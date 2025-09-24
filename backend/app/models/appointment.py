"""
Appointment model for healthcare scheduling.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from enum import Enum
import uuid

from app.core.database import Base


class AppointmentStatus(str, Enum):
    """Appointment status."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    REMINDED = "reminded"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class AppointmentType(str, Enum):
    """Type of healthcare appointment."""
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    PROCEDURE = "procedure"
    EMERGENCY = "emergency"
    PREVENTIVE = "preventive"


class Appointment(Base):
    """
    Appointment model for healthcare scheduling and tracking.
    """
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ninsaude_id = Column(String, unique=True, index=True)

    # Relationships
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False, index=True)
    lead = relationship("Lead", back_populates="appointments")

    # Appointment details
    scheduled_date = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, default=30)
    appointment_type = Column(SQLEnum(AppointmentType), default=AppointmentType.CONSULTATION)
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.SCHEDULED, index=True)

    # Healthcare provider details
    professional_id = Column(String(100), nullable=False)
    professional_name = Column(String(200))
    clinic_id = Column(String(100), nullable=False)
    clinic_name = Column(String(200))
    specialty = Column(String(100))

    # Location and contact
    address = Column(Text)
    room_number = Column(String(50))
    phone = Column(String(20))

    # Financial
    estimated_cost = Column(Numeric(10, 2))
    insurance_covered = Column(Boolean, default=False)

    # Reminders and notifications
    reminder_sent_24h = Column(Boolean, default=False)
    reminder_sent_3h = Column(Boolean, default=False)
    confirmation_sent = Column(Boolean, default=False)

    # Metadata
    notes = Column(Text)
    appointment_metadata = Column(JSON, default=dict)
    cancellation_reason = Column(String(500))

    # Timestamps
    confirmed_at = Column(DateTime(timezone=True))
    reminded_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    no_show_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Appointment(id={self.id}, lead_id={self.lead_id}, status={self.status}, date={self.scheduled_date})>"

    @property
    def end_time(self) -> datetime:
        """Calculate appointment end time."""
        return self.scheduled_date + timedelta(minutes=self.duration_minutes)

    @property
    def is_past_due(self) -> bool:
        """Check if appointment is past due."""
        return datetime.utcnow() > self.scheduled_date

    @property
    def time_until_appointment(self) -> timedelta:
        """Get time remaining until appointment."""
        return self.scheduled_date - datetime.utcnow()

    @property
    def needs_24h_reminder(self) -> bool:
        """Check if 24-hour reminder should be sent."""
        if self.reminder_sent_24h or self.status != AppointmentStatus.CONFIRMED:
            return False

        time_until = self.time_until_appointment
        return timedelta(hours=20) <= time_until <= timedelta(hours=28)

    @property
    def needs_3h_reminder(self) -> bool:
        """Check if 3-hour reminder should be sent."""
        if self.reminder_sent_3h or self.status != AppointmentStatus.CONFIRMED:
            return False

        time_until = self.time_until_appointment
        return timedelta(hours=2) <= time_until <= timedelta(hours=4)

    @property
    def should_check_no_show(self) -> bool:
        """Check if appointment should be marked as no-show."""
        if self.status not in [AppointmentStatus.CONFIRMED, AppointmentStatus.REMINDED]:
            return False

        # Check 15 minutes after scheduled time
        grace_period = timedelta(minutes=15)
        return datetime.utcnow() > (self.scheduled_date + grace_period)

    def confirm(self) -> None:
        """Confirm the appointment."""
        self.status = AppointmentStatus.CONFIRMED
        self.confirmed_at = datetime.utcnow()
        self.confirmation_sent = True

    def mark_reminded(self, reminder_type: str) -> None:
        """Mark that a reminder was sent."""
        self.status = AppointmentStatus.REMINDED
        self.reminded_at = datetime.utcnow()

        if reminder_type == "24h":
            self.reminder_sent_24h = True
        elif reminder_type == "3h":
            self.reminder_sent_3h = True

    def mark_completed(self) -> None:
        """Mark appointment as completed."""
        self.status = AppointmentStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_no_show(self) -> None:
        """Mark appointment as no-show."""
        self.status = AppointmentStatus.NO_SHOW
        self.no_show_at = datetime.utcnow()

    def cancel(self, reason: str = None) -> None:
        """Cancel the appointment."""
        self.status = AppointmentStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        if reason:
            self.cancellation_reason = reason

    def reschedule(self, new_date: datetime) -> None:
        """Reschedule the appointment."""
        self.status = AppointmentStatus.RESCHEDULED
        self.scheduled_date = new_date
        # Reset reminder flags
        self.reminder_sent_24h = False
        self.reminder_sent_3h = False
        self.confirmation_sent = False