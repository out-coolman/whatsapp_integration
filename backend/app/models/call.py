"""
Call model for voice communication tracking via VAPI and Twilio.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

from app.core.database import Base


class CallStatus(str, Enum):
    """Call status throughout the lifecycle."""
    QUEUED = "queued"
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    CANCELLED = "cancelled"


class CallDirection(str, Enum):
    """Call direction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallOutcome(str, Enum):
    """Call outcome classification."""
    SUCCESSFUL = "successful"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    VOICEMAIL = "voicemail"
    WRONG_NUMBER = "wrong_number"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    CALLBACK_REQUESTED = "callback_requested"
    APPOINTMENT_BOOKED = "appointment_booked"
    TECHNICAL_ISSUE = "technical_issue"


class Call(Base):
    """
    Call model for tracking voice communications with leads.
    """
    __tablename__ = "calls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vapi_call_id = Column(String, unique=True, index=True)
    twilio_call_sid = Column(String, unique=True, index=True)

    # Relationships
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False, index=True)
    lead = relationship("Lead", back_populates="calls")

    # Call details
    direction = Column(SQLEnum(CallDirection), nullable=False, index=True)
    status = Column(SQLEnum(CallStatus), default=CallStatus.QUEUED, index=True)
    outcome = Column(SQLEnum(CallOutcome), index=True)

    # Phone numbers
    from_number = Column(String(20), nullable=False)
    to_number = Column(String(20), nullable=False)

    # Call metrics
    duration_seconds = Column(Integer, default=0)
    queue_time_seconds = Column(Integer, default=0)
    ring_time_seconds = Column(Integer, default=0)
    talk_time_seconds = Column(Integer, default=0)

    # Audio and transcription
    recording_url = Column(String(500))
    transcript = Column(Text)
    transcript_summary = Column(Text)

    # AI/VAPI specific
    vapi_assistant_id = Column(String(100))
    vapi_function_calls = Column(JSON, default=list)
    ai_sentiment = Column(String(50))  # positive, negative, neutral
    ai_intent = Column(String(100))   # appointment_booking, information_request, etc.

    # Cost tracking
    cost_cents = Column(Integer, default=0)
    cost_per_minute_cents = Column(Integer, default=0)

    # Error tracking
    error_code = Column(String(50))
    error_message = Column(Text)

    # Metadata
    call_metadata = Column(JSON, default=dict)
    user_agent = Column(String(500))

    # Timestamps
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    initiated_at = Column(DateTime(timezone=True))
    ringing_at = Column(DateTime(timezone=True))
    answered_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Call(id={self.id}, lead_id={self.lead_id}, status={self.status}, duration={self.duration_seconds}s)>"

    @property
    def masked_from_number(self) -> str:
        """Get masked from number for logging."""
        if not self.from_number:
            return "***"
        return f"***{self.from_number[-4:]}" if len(self.from_number) > 4 else "***"

    @property
    def masked_to_number(self) -> str:
        """Get masked to number for logging."""
        if not self.to_number:
            return "***"
        return f"***{self.to_number[-4:]}" if len(self.to_number) > 4 else "***"

    @property
    def is_completed(self) -> bool:
        """Check if call is completed (successfully or not)."""
        return self.status in [
            CallStatus.COMPLETED,
            CallStatus.FAILED,
            CallStatus.BUSY,
            CallStatus.NO_ANSWER,
            CallStatus.CANCELLED
        ]

    @property
    def was_answered(self) -> bool:
        """Check if call was answered."""
        return self.status in [CallStatus.ANSWERED, CallStatus.COMPLETED] and self.answered_at is not None

    @property
    def total_cost_dollars(self) -> float:
        """Get total cost in dollars."""
        return self.cost_cents / 100.0 if self.cost_cents else 0.0

    @property
    def average_handle_time(self) -> int:
        """Get average handle time (queue + ring + talk time)."""
        return (self.queue_time_seconds or 0) + (self.ring_time_seconds or 0) + (self.talk_time_seconds or 0)

    def initiate(self, vapi_call_id: str = None, twilio_call_sid: str = None) -> None:
        """Mark call as initiated."""
        self.status = CallStatus.INITIATED
        self.initiated_at = datetime.utcnow()
        if vapi_call_id:
            self.vapi_call_id = vapi_call_id
        if twilio_call_sid:
            self.twilio_call_sid = twilio_call_sid

    def mark_ringing(self) -> None:
        """Mark call as ringing."""
        self.status = CallStatus.RINGING
        self.ringing_at = datetime.utcnow()
        if self.initiated_at:
            self.queue_time_seconds = int((self.ringing_at - self.initiated_at).total_seconds())

    def mark_answered(self) -> None:
        """Mark call as answered."""
        self.status = CallStatus.ANSWERED
        self.answered_at = datetime.utcnow()
        if self.ringing_at:
            self.ring_time_seconds = int((self.answered_at - self.ringing_at).total_seconds())

    def mark_completed(self, outcome: CallOutcome = None, duration_seconds: int = None) -> None:
        """Mark call as completed."""
        self.status = CallStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if outcome:
            self.outcome = outcome
        if duration_seconds is not None:
            self.duration_seconds = duration_seconds
            # Calculate talk time if we have answered time
            if self.answered_at:
                self.talk_time_seconds = duration_seconds

    def mark_failed(self, error_code: str = None, error_message: str = None) -> None:
        """Mark call as failed."""
        self.status = CallStatus.FAILED
        self.failed_at = datetime.utcnow()
        if error_code:
            self.error_code = error_code
        if error_message:
            self.error_message = error_message

    def update_transcript(self, transcript: str, summary: str = None) -> None:
        """Update call transcript and summary."""
        self.transcript = transcript
        if summary:
            self.transcript_summary = summary

    def add_function_call(self, function_name: str, parameters: dict, result: dict = None) -> None:
        """Add a VAPI function call to the call record."""
        if not self.vapi_function_calls:
            self.vapi_function_calls = []

        function_call = {
            "function_name": function_name,
            "parameters": parameters,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.vapi_function_calls.append(function_call)

    def calculate_cost(self, rate_per_minute_cents: int) -> None:
        """Calculate call cost based on duration and rate."""
        if self.duration_seconds and rate_per_minute_cents:
            minutes = self.duration_seconds / 60.0
            self.cost_cents = int(minutes * rate_per_minute_cents)
            self.cost_per_minute_cents = rate_per_minute_cents