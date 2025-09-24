"""
Event model for business event tracking and orchestration.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

from app.core.database import Base


class EventType(str, Enum):
    """Types of business events in the system."""
    # Lead events
    LEAD_CREATED = "lead_created"
    LEAD_UPDATED = "lead_updated"
    LEAD_STAGE_CHANGED = "lead_stage_changed"
    LEAD_TAG_ADDED = "lead_tag_added"
    LEAD_TAG_REMOVED = "lead_tag_removed"

    # Message events
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_READ = "message_read"
    MESSAGE_FAILED = "message_failed"

    # Call events
    CALL_INITIATED = "call_initiated"
    CALL_ANSWERED = "call_answered"
    CALL_COMPLETED = "call_completed"
    CALL_FAILED = "call_failed"

    # Appointment events
    APPOINTMENT_BOOKED = "appointment_booked"
    APPOINTMENT_CONFIRMED = "appointment_confirmed"
    APPOINTMENT_REMINDED = "appointment_reminded"
    APPOINTMENT_COMPLETED = "appointment_completed"
    APPOINTMENT_NO_SHOW = "appointment_no_show"
    APPOINTMENT_CANCELLED = "appointment_cancelled"

    # Orchestration events
    HOT_LEAD_DETECTED = "hot_lead_detected"
    HANDOFF_TRIGGERED = "handoff_triggered"
    REACTIVATION_TRIGGERED = "reactivation_triggered"

    # System events
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    WEBHOOK_RECEIVED = "webhook_received"
    API_CALL_MADE = "api_call_made"


class EventStatus(str, Enum):
    """Status of event processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Event(Base):
    """
    Event model for tracking all business events and orchestration triggers.
    This serves as the central event log for the entire system.
    """
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Event classification
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    status = Column(SQLEnum(EventStatus), default=EventStatus.PENDING, index=True)
    source = Column(String(100), nullable=False, index=True)  # Where the event originated

    # Event data
    payload = Column(JSON, nullable=False)  # Event-specific data
    event_metadata = Column(JSON, default=dict)   # Additional context

    # Relationships
    lead_id = Column(String, ForeignKey("leads.id"), index=True)
    lead = relationship("Lead", back_populates="events")

    # Related entity IDs for filtering and querying
    appointment_id = Column(String, index=True)
    call_id = Column(String, index=True)
    message_id = Column(String, index=True)

    # Processing tracking
    processed_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)

    # Orchestration
    triggers_actions = Column(JSON, default=list)  # Actions this event should trigger
    correlation_id = Column(String(100), index=True)  # For tracking related events

    # Deduplication
    idempotency_key = Column(String(255), unique=True, index=True)

    # Timestamps
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Create indexes for common queries
    __table_args__ = (
        Index('idx_events_type_status', 'event_type', 'status'),
        Index('idx_events_lead_occurred', 'lead_id', 'occurred_at'),
        Index('idx_events_source_occurred', 'source', 'occurred_at'),
        Index('idx_events_correlation_occurred', 'correlation_id', 'occurred_at'),
    )

    def __repr__(self):
        return f"<Event(id={self.id}, type={self.event_type}, status={self.status}, lead_id={self.lead_id})>"

    @classmethod
    def create_from_webhook(cls, event_type: EventType, source: str, payload: dict,
                           lead_id: str = None, idempotency_key: str = None,
                           occurred_at: datetime = None) -> 'Event':
        """Create an event from a webhook payload."""
        return cls(
            event_type=event_type,
            source=source,
            payload=payload,
            lead_id=lead_id,
            idempotency_key=idempotency_key,
            occurred_at=occurred_at or datetime.utcnow()
        )

    @classmethod
    def create_lead_event(cls, event_type: EventType, lead_id: str, payload: dict,
                         source: str = "system", correlation_id: str = None) -> 'Event':
        """Create a lead-related event."""
        return cls(
            event_type=event_type,
            source=source,
            payload=payload,
            lead_id=lead_id,
            correlation_id=correlation_id,
            occurred_at=datetime.utcnow()
        )

    @classmethod
    def create_orchestration_event(cls, event_type: EventType, lead_id: str,
                                  triggers_actions: list, payload: dict = None,
                                  correlation_id: str = None) -> 'Event':
        """Create an orchestration event that triggers actions."""
        return cls(
            event_type=event_type,
            source="orchestrator",
            payload=payload or {},
            lead_id=lead_id,
            triggers_actions=triggers_actions,
            correlation_id=correlation_id,
            occurred_at=datetime.utcnow()
        )

    def mark_processing(self) -> None:
        """Mark event as being processed."""
        self.status = EventStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_completed(self) -> None:
        """Mark event as successfully processed."""
        self.status = EventStatus.COMPLETED
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """Mark event as failed with error message."""
        self.status = EventStatus.FAILED
        self.failed_at = datetime.utcnow()
        self.error_message = error_message
        self.retry_count += 1
        self.updated_at = datetime.utcnow()

    def mark_skipped(self, reason: str = None) -> None:
        """Mark event as skipped."""
        self.status = EventStatus.SKIPPED
        self.processed_at = datetime.utcnow()
        if reason:
            self.event_metadata["skip_reason"] = reason
        self.updated_at = datetime.utcnow()

    def should_retry(self, max_retries: int = 3) -> bool:
        """Check if event should be retried."""
        return (
            self.status == EventStatus.FAILED and
            self.retry_count < max_retries
        )

    def add_triggered_action(self, action_type: str, action_data: dict = None) -> None:
        """Add an action that this event should trigger."""
        if not self.triggers_actions:
            self.triggers_actions = []

        action = {
            "type": action_type,
            "data": action_data or {},
            "added_at": datetime.utcnow().isoformat()
        }
        self.triggers_actions.append(action)

    def get_masked_payload(self) -> dict:
        """Get payload with PII masked for logging."""
        import json
        from app.core.security import mask_pii

        payload_str = json.dumps(self.payload, default=str)
        masked_payload_str = mask_pii(payload_str)

        try:
            return json.loads(masked_payload_str)
        except json.JSONDecodeError:
            return {"masked": True, "original_keys": list(self.payload.keys())}

    @property
    def age_seconds(self) -> int:
        """Get age of event in seconds."""
        return int((datetime.utcnow() - self.occurred_at).total_seconds())

    @property
    def is_stale(self, max_age_hours: int = 24) -> bool:
        """Check if event is stale (older than max_age_hours)."""
        max_age_seconds = max_age_hours * 3600
        return self.age_seconds > max_age_seconds