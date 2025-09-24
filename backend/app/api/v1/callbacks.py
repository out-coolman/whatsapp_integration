"""
VAPI callback endpoints for receiving call status updates and transcripts.
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Request, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.api.dependencies import (
    get_client_ip,
    verify_webhook_signature,
    webhook_rate_limiter,
    check_rate_limit
)
from app.models.lead import Lead
from app.models.call import Call, CallStatus, CallOutcome, CallDirection
from app.models.event import Event, EventType
from app.models.log import Log, LogLevel
from app.core.logging import audit_logger
from app.jobs.scheduler import enqueue_orchestration_job

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models for VAPI callback payloads
class VAPIFunctionCall(BaseModel):
    """VAPI function call data."""
    name: str = Field(..., description="Function name")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Function parameters")
    result: Optional[Dict[str, Any]] = Field(None, description="Function result")


class VAPITranscript(BaseModel):
    """VAPI call transcript data."""
    text: str = Field(..., description="Full transcript text")
    summary: Optional[str] = Field(None, description="AI-generated summary")
    sentiment: Optional[str] = Field(None, description="Detected sentiment (positive/negative/neutral)")
    intent: Optional[str] = Field(None, description="Detected intent")
    confidence: Optional[float] = Field(None, description="Confidence score 0-1")


class VAPICallData(BaseModel):
    """VAPI call event data."""
    call_id: str = Field(..., description="VAPI call ID")
    status: str = Field(..., description="Call status")
    phone_number: Optional[str] = Field(None, description="Lead's phone number")
    duration: Optional[int] = Field(None, description="Call duration in seconds")
    started_at: Optional[datetime] = Field(None, description="Call start time")
    ended_at: Optional[datetime] = Field(None, description="Call end time")
    answered_at: Optional[datetime] = Field(None, description="Call answer time")
    cost: Optional[float] = Field(None, description="Call cost in dollars")
    recording_url: Optional[str] = Field(None, description="Recording URL")
    transcript: Optional[VAPITranscript] = Field(None, description="Call transcript")
    function_calls: Optional[List[VAPIFunctionCall]] = Field(default_factory=list, description="Function calls made during call")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    error_message: Optional[str] = Field(None, description="Error message if call failed")
    twilio_call_sid: Optional[str] = Field(None, description="Twilio call SID")


class VAPIWebhookPayload(BaseModel):
    """Main VAPI webhook payload structure."""
    event_type: str = Field(..., description="Type of event (call-started, call-ended, etc.)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: VAPICallData = Field(..., description="Call data")
    assistant_id: Optional[str] = Field(None, description="VAPI assistant ID")


@router.post("/callbacks/vapi")
async def vapi_callback(
    payload: VAPIWebhookPayload,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(lambda r: check_rate_limit(r, webhook_rate_limiter))
):
    """
    Receive callbacks from VAPI for call status updates and transcripts.

    Supported event types:
    - call-started: Call has been initiated
    - call-ringing: Call is ringing
    - call-answered: Call was answered by the lead
    - call-ended: Call has completed
    - call-failed: Call failed for some reason
    - transcript-updated: New transcript data available
    - function-called: AI assistant called a function
    """
    client_ip = get_client_ip(request)
    correlation_id = str(uuid.uuid4())

    # Log callback receipt
    audit_logger.log_event(
        event_type="vapi_callback_received",
        details={
            "event_type": payload.event_type,
            "call_id": payload.data.call_id,
            "status": payload.data.status
        }
    )

    try:
        # Verify webhook signature (if configured)
        if settings.VAPI_API_KEY:
            is_valid = await verify_webhook_signature(
                request, "vapi", settings.VAPI_API_KEY
            )
            if not is_valid:
                logger.warning(f"Invalid VAPI webhook signature from {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )

        # Find the call record
        call = db.query(Call).filter_by(vapi_call_id=payload.data.call_id).first()

        if not call:
            # If call doesn't exist, try to find by phone number and create it
            if payload.data.phone_number:
                lead = db.query(Lead).filter_by(phone=payload.data.phone_number).first()
                if lead:
                    call = create_call_from_vapi_data(payload.data, lead.id, db)
                else:
                    logger.warning(f"No lead found for phone number {payload.data.phone_number}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Call record not found and no matching lead"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Call record not found"
                )

        # Update call based on event type
        updated_call = await update_call_from_vapi_event(call, payload, db)

        # Create event for orchestration
        event_type_mapping = {
            "call-started": EventType.CALL_INITIATED,
            "call-answered": EventType.CALL_ANSWERED,
            "call-ended": EventType.CALL_COMPLETED,
            "call-failed": EventType.CALL_FAILED,
        }

        if payload.event_type in event_type_mapping:
            event = Event.create_lead_event(
                event_type=event_type_mapping[payload.event_type],
                lead_id=updated_call.lead_id,
                payload={
                    "call_id": updated_call.id,
                    "vapi_call_id": payload.data.call_id,
                    "status": payload.data.status,
                    "duration": payload.data.duration,
                    "outcome": updated_call.outcome.value if updated_call.outcome else None
                },
                correlation_id=correlation_id
            )

            # Add orchestration actions based on call outcome
            if payload.event_type == "call-ended" and updated_call.outcome:
                if updated_call.outcome == CallOutcome.APPOINTMENT_BOOKED:
                    event.add_triggered_action("process_appointment_booking", {
                        "lead_id": updated_call.lead_id,
                        "call_id": updated_call.id
                    })
                elif updated_call.outcome == CallOutcome.CALLBACK_REQUESTED:
                    event.add_triggered_action("schedule_callback", {
                        "lead_id": updated_call.lead_id,
                        "call_id": updated_call.id
                    })
                elif updated_call.outcome == CallOutcome.NOT_INTERESTED:
                    event.add_triggered_action("update_lead_classification", {
                        "lead_id": updated_call.lead_id,
                        "classification": "cold"
                    })

            db.add(event)

            # Enqueue background jobs
            background_tasks.add_task(
                enqueue_orchestration_job,
                event_id=event.id,
                correlation_id=correlation_id
            )

        # Log successful processing
        log_entry = Log.create_api_call_log(
            source="vapi_callback",
            endpoint="/callbacks/vapi",
            method="POST",
            status_code=200,
            details={
                "event_type": payload.event_type,
                "call_id": updated_call.id,
                "vapi_call_id": payload.data.call_id,
                "correlation_id": correlation_id
            }
        )
        log_entry.ip_address = client_ip
        log_entry.correlation_id = correlation_id
        log_entry.call_id = updated_call.id
        log_entry.lead_id = updated_call.lead_id
        db.add(log_entry)

        db.commit()

        return {
            "status": "success",
            "message": "Callback processed successfully",
            "call_id": updated_call.id,
            "correlation_id": correlation_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing VAPI callback: {e}", exc_info=True)

        # Log the error
        error_log = Log.create_error_log(
            source="vapi_callback",
            message=f"Failed to process callback: {str(e)}",
            details={
                "event_type": payload.event_type,
                "call_id": payload.data.call_id,
                "error": str(e)
            }
        )
        error_log.ip_address = client_ip
        error_log.correlation_id = correlation_id
        db.add(error_log)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process callback"
        )


def create_call_from_vapi_data(vapi_data: VAPICallData, lead_id: str, db: Session) -> Call:
    """Create a new call record from VAPI data."""
    call = Call(
        vapi_call_id=vapi_data.call_id,
        twilio_call_sid=vapi_data.twilio_call_sid,
        lead_id=lead_id,
        direction=CallDirection.OUTBOUND,  # Assuming all VAPI calls are outbound
        from_number=settings.TWILIO_PHONE_NUMBER,
        to_number=vapi_data.phone_number,
        status=CallStatus.QUEUED
    )

    if vapi_data.started_at:
        call.initiated_at = vapi_data.started_at

    db.add(call)
    db.commit()
    return call


async def update_call_from_vapi_event(
    call: Call,
    payload: VAPIWebhookPayload,
    db: Session
) -> Call:
    """Update call record based on VAPI event."""
    vapi_data = payload.data

    # Update basic call information
    if vapi_data.twilio_call_sid and not call.twilio_call_sid:
        call.twilio_call_sid = vapi_data.twilio_call_sid

    if vapi_data.started_at and not call.initiated_at:
        call.initiated_at = vapi_data.started_at

    if vapi_data.ended_at and not call.completed_at:
        call.completed_at = vapi_data.ended_at

    if vapi_data.answered_at and not call.answered_at:
        call.answered_at = vapi_data.answered_at

    if vapi_data.duration is not None:
        call.duration_seconds = vapi_data.duration

    if vapi_data.cost is not None:
        call.cost_cents = int(vapi_data.cost * 100)

    if vapi_data.recording_url:
        call.recording_url = vapi_data.recording_url

    if payload.assistant_id:
        call.vapi_assistant_id = payload.assistant_id

    # Update status based on event type
    if payload.event_type == "call-started":
        call.initiate(vapi_data.call_id, vapi_data.twilio_call_sid)
    elif payload.event_type == "call-ringing":
        call.mark_ringing()
    elif payload.event_type == "call-answered":
        call.mark_answered()
    elif payload.event_type == "call-ended":
        # Determine outcome from transcript or metadata
        outcome = determine_call_outcome(vapi_data)
        call.mark_completed(outcome, vapi_data.duration)
    elif payload.event_type == "call-failed":
        call.mark_failed(error_message=vapi_data.error_message)

    # Update transcript if provided
    if vapi_data.transcript:
        call.update_transcript(
            vapi_data.transcript.text,
            vapi_data.transcript.summary
        )

        if vapi_data.transcript.sentiment:
            call.ai_sentiment = vapi_data.transcript.sentiment

        if vapi_data.transcript.intent:
            call.ai_intent = vapi_data.transcript.intent

    # Update function calls
    if vapi_data.function_calls:
        for func_call in vapi_data.function_calls:
            call.add_function_call(
                func_call.name,
                func_call.parameters,
                func_call.result
            )

    # Update metadata
    if vapi_data.metadata:
        if not call.metadata:
            call.metadata = {}
        call.metadata.update(vapi_data.metadata)

    db.commit()
    return call


def determine_call_outcome(vapi_data: VAPICallData) -> Optional[CallOutcome]:
    """
    Determine call outcome based on transcript, function calls, and metadata.
    This uses AI analysis and function calls to classify the call result.
    """
    # Check function calls for explicit outcomes
    if vapi_data.function_calls:
        for func_call in vapi_data.function_calls:
            if func_call.name == "book_appointment" and func_call.result:
                return CallOutcome.APPOINTMENT_BOOKED
            elif func_call.name == "schedule_callback" and func_call.result:
                return CallOutcome.CALLBACK_REQUESTED

    # Check transcript analysis
    if vapi_data.transcript:
        transcript_lower = vapi_data.transcript.text.lower()

        # Look for appointment booking keywords
        appointment_keywords = [
            "book appointment", "schedule appointment", "yes, book it",
            "when can I come in", "what times are available"
        ]
        if any(keyword in transcript_lower for keyword in appointment_keywords):
            return CallOutcome.APPOINTMENT_BOOKED

        # Look for callback requests
        callback_keywords = [
            "call me back", "call later", "better time", "not now"
        ]
        if any(keyword in transcript_lower for keyword in callback_keywords):
            return CallOutcome.CALLBACK_REQUESTED

        # Look for interest indicators
        interest_keywords = [
            "interested", "tell me more", "sounds good", "yes"
        ]
        not_interested_keywords = [
            "not interested", "no thank you", "remove me", "don't call"
        ]

        if any(keyword in transcript_lower for keyword in not_interested_keywords):
            return CallOutcome.NOT_INTERESTED
        elif any(keyword in transcript_lower for keyword in interest_keywords):
            return CallOutcome.INTERESTED

        # Check sentiment
        if vapi_data.transcript.sentiment == "negative":
            return CallOutcome.NOT_INTERESTED
        elif vapi_data.transcript.sentiment == "positive":
            return CallOutcome.INTERESTED

    # Check duration - very short calls might be no answer or hang up
    if vapi_data.duration and vapi_data.duration < 10:
        return CallOutcome.NO_ANSWER

    # Default to successful if call completed normally
    return CallOutcome.SUCCESSFUL


@router.get("/callbacks/vapi/test")
async def test_vapi_callback():
    """Test endpoint to verify VAPI callback connectivity."""
    return {
        "status": "ok",
        "message": "VAPI callback endpoint is operational",
        "timestamp": datetime.utcnow().isoformat()
    }