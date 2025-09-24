"""
Helena CRM webhook endpoints for receiving lead updates and events.
"""
from typing import Dict, Any, Optional
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
    log_api_request,
    verify_webhook_signature,
    webhook_rate_limiter,
    check_rate_limit
)
from app.models.lead import Lead, LeadStage, LeadSource, LeadClassification
from app.models.message import Message, MessageDirection, MessageChannel, MessageStatus
from app.models.event import Event, EventType, EventStatus
from app.models.log import Log, LogLevel, LogCategory
from app.core.logging import audit_logger
from app.jobs.scheduler import enqueue_orchestration_job

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models for webhook payloads
class HelenaLeadData(BaseModel):
    """Helena lead data structure."""
    helena_id: str = Field(..., description="Helena CRM lead ID")
    first_name: str = Field(..., max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: str = Field(..., max_length=20)
    stage: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[list] = Field(default_factory=list)
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict)
    notes: Optional[str] = None
    assigned_agent_id: Optional[str] = None


class HelenaMessageData(BaseModel):
    """Helena message data structure."""
    helena_message_id: str = Field(..., description="Helena message ID")
    helena_lead_id: str = Field(..., description="Helena lead ID")
    content: str = Field(..., description="Message content")
    direction: str = Field(..., description="inbound or outbound")
    channel: str = Field(default="whatsapp", description="Communication channel")
    status: Optional[str] = Field(default="sent", description="Message status")
    timestamp: Optional[datetime] = None


class HelenaWebhookPayload(BaseModel):
    """Main Helena webhook payload structure."""
    event_type: str = Field(..., description="Type of event (lead_created, message_received, etc.)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(..., description="Event-specific data")
    helena_lead_id: Optional[str] = Field(None, description="Associated lead ID")
    idempotency_key: Optional[str] = Field(None, description="Unique event identifier")


@router.post("/webhooks/helena")
async def helena_webhook(
    payload: HelenaWebhookPayload,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(lambda r: check_rate_limit(r, webhook_rate_limiter))
):
    """
    Receive webhooks from Helena CRM for lead updates, messages, and other events.

    Supported event types:
    - lead_created: New lead was created
    - lead_updated: Lead information was updated
    - lead_stage_changed: Lead moved to different stage
    - lead_tag_added: Tag was added to lead
    - message_received: Inbound message from lead
    - message_sent: Outbound message to lead
    - message_delivered: Message delivery confirmation
    - message_read: Message read receipt
    """
    client_ip = get_client_ip(request)
    correlation_id = str(uuid.uuid4())

    # Log webhook receipt
    audit_logger.log_webhook_received("helena", payload.event_type, payload.helena_lead_id)

    try:
        # Verify webhook signature (if configured)
        if settings.HELENA_WEBHOOK_SECRET:
            is_valid = await verify_webhook_signature(
                request, "helena", settings.HELENA_WEBHOOK_SECRET
            )
            if not is_valid:
                logger.warning(f"Invalid Helena webhook signature from {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )

        # Create idempotency key if not provided
        if not payload.idempotency_key:
            payload.idempotency_key = f"helena_{payload.event_type}_{payload.helena_lead_id}_{int(payload.timestamp.timestamp())}"

        # Check for duplicate events
        existing_event = db.query(Event).filter_by(
            idempotency_key=payload.idempotency_key
        ).first()

        if existing_event:
            logger.info(f"Duplicate Helena webhook ignored: {payload.idempotency_key}")
            return {
                "status": "success",
                "message": "Event already processed",
                "event_id": existing_event.id
            }

        # Process the webhook based on event type
        event = await process_helena_event(payload, db, correlation_id)

        # Enqueue background jobs for orchestration
        background_tasks.add_task(
            enqueue_orchestration_job,
            event_id=event.id,
            correlation_id=correlation_id
        )

        # Log successful processing
        log_entry = Log.create_webhook_log(
            source="helena",
            message=f"Successfully processed {payload.event_type}",
            details={
                "event_type": payload.event_type,
                "helena_lead_id": payload.helena_lead_id,
                "correlation_id": correlation_id
            },
            level=LogLevel.INFO,
            lead_id=event.lead_id
        )
        log_entry.ip_address = client_ip
        log_entry.correlation_id = correlation_id
        db.add(log_entry)
        db.commit()

        return {
            "status": "success",
            "message": "Webhook processed successfully",
            "event_id": event.id,
            "correlation_id": correlation_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Helena webhook: {e}", exc_info=True)

        # Log the error
        error_log = Log.create_error_log(
            source="helena_webhook",
            message=f"Failed to process webhook: {str(e)}",
            details={
                "event_type": payload.event_type,
                "helena_lead_id": payload.helena_lead_id,
                "error": str(e)
            }
        )
        error_log.ip_address = client_ip
        error_log.correlation_id = correlation_id
        db.add(error_log)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


async def process_helena_event(
    payload: HelenaWebhookPayload,
    db: Session,
    correlation_id: str
) -> Event:
    """Process Helena webhook event based on type."""

    lead = None
    event_mapping = {
        "lead_created": EventType.LEAD_CREATED,
        "lead_updated": EventType.LEAD_UPDATED,
        "lead_stage_changed": EventType.LEAD_STAGE_CHANGED,
        "lead_tag_added": EventType.LEAD_TAG_ADDED,
        "message_received": EventType.MESSAGE_RECEIVED,
        "message_sent": EventType.MESSAGE_SENT,
        "message_delivered": EventType.MESSAGE_DELIVERED,
        "message_read": EventType.MESSAGE_READ,
    }

    event_type = event_mapping.get(payload.event_type)
    if not event_type:
        raise ValueError(f"Unsupported Helena event type: {payload.event_type}")

    # Handle lead events
    if payload.event_type in ["lead_created", "lead_updated", "lead_stage_changed", "lead_tag_added"]:
        lead = await handle_lead_event(payload, db)

    # Handle message events
    elif payload.event_type in ["message_received", "message_sent", "message_delivered", "message_read"]:
        lead = await handle_message_event(payload, db)

    # Create event record
    event = Event.create_from_webhook(
        event_type=event_type,
        source="helena",
        payload=payload.data,
        lead_id=lead.id if lead else None,
        idempotency_key=payload.idempotency_key,
        occurred_at=payload.timestamp
    )
    event.correlation_id = correlation_id

    # Determine orchestration actions based on event type and lead state
    if lead and event_type == EventType.LEAD_CREATED and lead.is_hot_lead():
        event.add_triggered_action("initiate_hot_lead_sequence", {"lead_id": lead.id})

    elif lead and event_type == EventType.LEAD_TAG_ADDED and lead.has_tag("handoff"):
        event.add_triggered_action("trigger_handoff", {"lead_id": lead.id})

    elif lead and event_type == EventType.LEAD_STAGE_CHANGED and lead.stage == LeadStage.BOOKED:
        event.add_triggered_action("schedule_appointment_reminders", {"lead_id": lead.id})

    elif event_type == EventType.MESSAGE_RECEIVED:
        event.add_triggered_action("process_inbound_message", {"lead_id": lead.id if lead else None})

    db.add(event)
    db.commit()

    return event


async def handle_lead_event(payload: HelenaWebhookPayload, db: Session) -> Lead:
    """Handle lead-related webhook events."""
    try:
        lead_data = HelenaLeadData(**payload.data)
    except Exception as e:
        raise ValueError(f"Invalid lead data: {e}")

    # Find or create lead
    lead = db.query(Lead).filter_by(helena_id=lead_data.helena_id).first()

    if payload.event_type == "lead_created" or not lead:
        if not lead:
            lead = Lead(
                helena_id=lead_data.helena_id,
                first_name=lead_data.first_name,
                last_name=lead_data.last_name,
                email=lead_data.email,
                phone=lead_data.phone,
                tags=lead_data.tags or [],
                custom_fields=lead_data.custom_fields or {},
                notes=lead_data.notes,
                assigned_agent_id=lead_data.assigned_agent_id
            )

            # Set stage and classification
            if lead_data.stage:
                try:
                    lead.stage = LeadStage(lead_data.stage.lower())
                except ValueError:
                    lead.stage = LeadStage.NEW

            if lead_data.source:
                try:
                    lead.source = LeadSource(lead_data.source.lower())
                except ValueError:
                    lead.source = LeadSource.OTHER

            # Determine classification based on tags and source
            if any(tag.lower() in ["urgent", "hot", "high_value"] for tag in (lead_data.tags or [])):
                lead.classification = LeadClassification.HOT
            elif lead_data.source and lead_data.source.lower() == "referral":
                lead.classification = LeadClassification.WARM
            else:
                lead.classification = LeadClassification.WARM

            db.add(lead)

    else:
        # Update existing lead
        if lead_data.first_name:
            lead.first_name = lead_data.first_name
        if lead_data.last_name:
            lead.last_name = lead_data.last_name
        if lead_data.email:
            lead.email = lead_data.email
        if lead_data.phone:
            lead.phone = lead_data.phone
        if lead_data.notes:
            lead.notes = lead_data.notes
        if lead_data.assigned_agent_id:
            lead.assigned_agent_id = lead_data.assigned_agent_id

        # Handle stage changes
        if payload.event_type == "lead_stage_changed" and lead_data.stage:
            try:
                new_stage = LeadStage(lead_data.stage.lower())
                lead.update_stage(new_stage)
            except ValueError:
                logger.warning(f"Invalid stage value: {lead_data.stage}")

        # Handle tag changes
        if payload.event_type == "lead_tag_added" and lead_data.tags:
            for tag in lead_data.tags:
                lead.add_tag(tag)

        # Update custom fields
        if lead_data.custom_fields:
            if not lead.custom_fields:
                lead.custom_fields = {}
            lead.custom_fields.update(lead_data.custom_fields)

    db.commit()
    return lead


async def handle_message_event(payload: HelenaWebhookPayload, db: Session) -> Optional[Lead]:
    """Handle message-related webhook events."""
    try:
        message_data = HelenaMessageData(**payload.data)
    except Exception as e:
        raise ValueError(f"Invalid message data: {e}")

    # Find lead
    lead = db.query(Lead).filter_by(helena_id=message_data.helena_lead_id).first()
    if not lead:
        logger.warning(f"Lead not found for message: {message_data.helena_lead_id}")
        return None

    # Find or create message
    message = db.query(Message).filter_by(
        helena_message_id=message_data.helena_message_id
    ).first()

    if not message and payload.event_type in ["message_received", "message_sent"]:
        # Create new message
        message = Message(
            helena_message_id=message_data.helena_message_id,
            lead_id=lead.id,
            content=message_data.content,
            direction=MessageDirection(message_data.direction.lower()),
            channel=MessageChannel(message_data.channel.lower())
        )

        if message_data.status:
            try:
                message.status = MessageStatus(message_data.status.lower())
            except ValueError:
                message.status = MessageStatus.SENT

        db.add(message)

    elif message:
        # Update existing message status
        if payload.event_type == "message_delivered":
            message.mark_delivered()
        elif payload.event_type == "message_read":
            message.mark_read()

    # Update lead's last contacted timestamp for outbound messages
    if message and message.direction == MessageDirection.OUTBOUND:
        lead.last_contacted_at = datetime.utcnow()

    db.commit()
    return lead


@router.get("/webhooks/helena/test")
async def test_helena_webhook():
    """Test endpoint to verify Helena webhook connectivity."""
    return {
        "status": "ok",
        "message": "Helena webhook endpoint is operational",
        "timestamp": datetime.utcnow().isoformat()
    }