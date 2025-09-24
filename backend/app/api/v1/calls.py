"""
Calls and VAPI integration API endpoints.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.api.v1.auth import get_current_active_user
from app.models.call import Call, CallStatus, CallDirection, CallOutcome
from app.models.user import User
from app.models.lead import Lead
from pydantic import BaseModel, Field

router = APIRouter()


class CallResponse(BaseModel):
    """Call response model for API."""
    id: str
    vapi_call_id: Optional[str] = None
    twilio_call_sid: Optional[str] = None
    lead_id: str
    lead_name: Optional[str] = None
    lead_phone: Optional[str] = None
    direction: str
    status: str
    outcome: Optional[str] = None
    from_number: str
    to_number: str
    duration_seconds: int
    talk_time_seconds: int
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    transcript_summary: Optional[str] = None
    ai_sentiment: Optional[str] = None
    ai_intent: Optional[str] = None
    cost_cents: int
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    queued_at: datetime
    initiated_at: Optional[datetime] = None
    answered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_call(cls, call: Call) -> 'CallResponse':
        lead_name = None
        lead_phone = None
        if call.lead:
            lead_name = call.lead.full_name
            lead_phone = call.lead.phone

        return cls(
            id=call.id,
            vapi_call_id=call.vapi_call_id,
            twilio_call_sid=call.twilio_call_sid,
            lead_id=call.lead_id,
            lead_name=lead_name,
            lead_phone=lead_phone,
            direction=call.direction.value if call.direction else 'outbound',
            status=call.status.value if call.status else 'queued',
            outcome=call.outcome.value if call.outcome else None,
            from_number=call.from_number,
            to_number=call.to_number,
            duration_seconds=call.duration_seconds or 0,
            talk_time_seconds=call.talk_time_seconds or 0,
            recording_url=call.recording_url,
            transcript=call.transcript,
            transcript_summary=call.transcript_summary,
            ai_sentiment=call.ai_sentiment,
            ai_intent=call.ai_intent,
            cost_cents=call.cost_cents or 0,
            error_code=call.error_code,
            error_message=call.error_message,
            queued_at=call.queued_at,
            initiated_at=call.initiated_at,
            answered_at=call.answered_at,
            completed_at=call.completed_at,
            created_at=call.created_at,
            updated_at=call.updated_at
        )


class CallStatsResponse(BaseModel):
    """Call statistics response."""
    total_calls: int
    answered_calls: int
    completed_calls: int
    no_answer_calls: int
    busy_calls: int
    failed_calls: int
    escalated_calls: int
    average_duration: float
    total_cost_dollars: float
    answer_rate: float
    completion_rate: float


@router.get("/calls", response_model=List[CallResponse])
async def get_calls(
    status: Optional[str] = Query(None, description="Filter by call status"),
    direction: Optional[str] = Query(None, description="Filter by call direction"),
    lead_id: Optional[str] = Query(None, description="Filter by lead ID"),
    date_from: Optional[date] = Query(None, description="Start date filter"),
    date_to: Optional[date] = Query(None, description="End date filter"),
    search: Optional[str] = Query(None, description="Search by lead name or phone"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[CallResponse]:
    """Get all calls with optional filtering."""

    # Check permission
    if not current_user.has_permission("view_calls"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view calls"
        )

    query = db.query(Call).join(Lead, Call.lead_id == Lead.id)

    if status:
        try:
            query = query.filter(Call.status == CallStatus(status.lower()))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    if direction:
        try:
            query = query.filter(Call.direction == CallDirection(direction.lower()))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid direction: {direction}")

    if lead_id:
        query = query.filter(Call.lead_id == lead_id)

    if date_from:
        query = query.filter(Call.created_at >= date_from)

    if date_to:
        # Include the entire day
        end_date = datetime.combine(date_to, datetime.max.time())
        query = query.filter(Call.created_at <= end_date)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Lead.first_name.ilike(search_term)) |
            (Lead.last_name.ilike(search_term)) |
            (Lead.phone.ilike(search_term)) |
            (Call.from_number.ilike(search_term)) |
            (Call.to_number.ilike(search_term))
        )

    calls = query.order_by(desc(Call.created_at)).offset(offset).limit(limit).all()
    return [CallResponse.from_call(call) for call in calls]


@router.get("/calls/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CallResponse:
    """Get a specific call by ID."""

    # Check permission
    if not current_user.has_permission("view_calls"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view calls"
        )

    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    return CallResponse.from_call(call)


@router.get("/calls/stats", response_model=CallStatsResponse)
async def get_call_stats(
    date_from: Optional[date] = Query(None, description="Start date for stats"),
    date_to: Optional[date] = Query(None, description="End date for stats"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> CallStatsResponse:
    """Get call statistics."""

    # Check permission
    if not current_user.has_permission("view_calls"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view call statistics"
        )

    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    # Include the entire day for date_to
    end_date = datetime.combine(date_to, datetime.max.time())
    start_date = datetime.combine(date_from, datetime.min.time())

    calls = db.query(Call).filter(
        and_(Call.created_at >= start_date, Call.created_at <= end_date)
    ).all()

    total_calls = len(calls)
    answered_calls = len([c for c in calls if c.was_answered])
    completed_calls = len([c for c in calls if c.status == CallStatus.COMPLETED])
    no_answer_calls = len([c for c in calls if c.status == CallStatus.NO_ANSWER])
    busy_calls = len([c for c in calls if c.status == CallStatus.BUSY])
    failed_calls = len([c for c in calls if c.status == CallStatus.FAILED])

    # Count escalated calls (assuming these are calls with human handoff intent or outcome)
    escalated_calls = len([c for c in calls if c.ai_intent and 'handoff' in c.ai_intent.lower()])

    # Calculate averages and rates
    total_duration = sum(c.duration_seconds or 0 for c in calls)
    average_duration = total_duration / total_calls if total_calls > 0 else 0

    total_cost_dollars = sum(c.total_cost_dollars for c in calls)

    answer_rate = (answered_calls / total_calls * 100) if total_calls > 0 else 0
    completion_rate = (completed_calls / answered_calls * 100) if answered_calls > 0 else 0

    return CallStatsResponse(
        total_calls=total_calls,
        answered_calls=answered_calls,
        completed_calls=completed_calls,
        no_answer_calls=no_answer_calls,
        busy_calls=busy_calls,
        failed_calls=failed_calls,
        escalated_calls=escalated_calls,
        average_duration=round(average_duration, 2),
        total_cost_dollars=round(total_cost_dollars, 2),
        answer_rate=round(answer_rate, 2),
        completion_rate=round(completion_rate, 2)
    )


@router.get("/calls/{call_id}/recording")
async def get_call_recording(
    call_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get call recording URL."""

    # Check permission
    if not current_user.has_permission("view_calls"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view call recordings"
        )

    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    if not call.recording_url:
        raise HTTPException(status_code=404, detail="Recording not available")

    return {"recording_url": call.recording_url}


@router.get("/calls/{call_id}/transcript")
async def get_call_transcript(
    call_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get call transcript and summary."""

    # Check permission
    if not current_user.has_permission("view_calls"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view call transcripts"
        )

    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    return {
        "call_id": call.id,
        "transcript": call.transcript,
        "summary": call.transcript_summary,
        "ai_sentiment": call.ai_sentiment,
        "ai_intent": call.ai_intent,
        "vapi_function_calls": call.vapi_function_calls or []
    }