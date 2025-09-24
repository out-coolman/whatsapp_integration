"""
Aggregate models and materialized views for metrics and reporting.
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Date, Boolean, Index, text
from sqlalchemy.sql import func
from datetime import datetime, date
import uuid

from app.core.database import Base


class LeadFunnelMetrics(Base):
    """
    Aggregated metrics for lead funnel analysis.
    Updated periodically by aggregation jobs.
    """
    __tablename__ = "lead_funnel_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Time dimensions
    date = Column(Date, nullable=False, index=True)
    hour = Column(Integer, index=True)  # 0-23 for hourly breakdowns

    # Funnel metrics
    leads_new = Column(Integer, default=0)
    leads_contacted = Column(Integer, default=0)
    leads_qualified = Column(Integer, default=0)
    leads_booked = Column(Integer, default=0)
    leads_confirmed = Column(Integer, default=0)
    leads_showed = Column(Integer, default=0)
    leads_no_show = Column(Integer, default=0)
    leads_converted = Column(Integer, default=0)
    leads_lost = Column(Integer, default=0)

    # Conversion rates (calculated fields)
    contact_rate = Column(Numeric(5, 4), default=0)  # contacted/new
    qualification_rate = Column(Numeric(5, 4), default=0)  # qualified/contacted
    booking_rate = Column(Numeric(5, 4), default=0)  # booked/qualified
    show_rate = Column(Numeric(5, 4), default=0)  # showed/confirmed
    conversion_rate = Column(Numeric(5, 4), default=0)  # converted/new

    # Source breakdown
    source_organic = Column(Integer, default=0)
    source_paid_ads = Column(Integer, default=0)
    source_social_media = Column(Integer, default=0)
    source_referral = Column(Integer, default=0)
    source_direct = Column(Integer, default=0)
    source_other = Column(Integer, default=0)

    # Lead classification
    hot_leads = Column(Integer, default=0)
    warm_leads = Column(Integer, default=0)
    cold_leads = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_funnel_date_hour', 'date', 'hour'),
    )


class TelephonyMetrics(Base):
    """
    Aggregated metrics for telephony/call analysis.
    """
    __tablename__ = "telephony_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Time dimensions
    date = Column(Date, nullable=False, index=True)
    hour = Column(Integer, index=True)

    # Call volume metrics
    calls_initiated = Column(Integer, default=0)
    calls_answered = Column(Integer, default=0)
    calls_completed = Column(Integer, default=0)
    calls_failed = Column(Integer, default=0)
    calls_no_answer = Column(Integer, default=0)
    calls_busy = Column(Integer, default=0)

    # Call performance metrics
    answer_rate = Column(Numeric(5, 4), default=0)  # answered/initiated
    completion_rate = Column(Numeric(5, 4), default=0)  # completed/answered

    # Duration metrics (in seconds)
    total_talk_time = Column(Integer, default=0)
    total_ring_time = Column(Integer, default=0)
    total_queue_time = Column(Integer, default=0)
    avg_handle_time = Column(Integer, default=0)  # average total call time
    avg_talk_time = Column(Integer, default=0)

    # Outcome metrics
    outcome_successful = Column(Integer, default=0)
    outcome_no_answer = Column(Integer, default=0)
    outcome_voicemail = Column(Integer, default=0)
    outcome_interested = Column(Integer, default=0)
    outcome_not_interested = Column(Integer, default=0)
    outcome_callback_requested = Column(Integer, default=0)
    outcome_appointment_booked = Column(Integer, default=0)
    outcome_technical_issue = Column(Integer, default=0)

    # Cost metrics (in cents)
    total_cost_cents = Column(Integer, default=0)
    avg_cost_per_call_cents = Column(Integer, default=0)

    # Agent performance
    unique_leads_called = Column(Integer, default=0)
    repeat_calls = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_telephony_date_hour', 'date', 'hour'),
    )


class WhatsAppMetrics(Base):
    """
    Aggregated metrics for WhatsApp messaging analysis.
    """
    __tablename__ = "whatsapp_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Time dimensions
    date = Column(Date, nullable=False, index=True)
    hour = Column(Integer, index=True)

    # Message volume metrics
    messages_sent = Column(Integer, default=0)
    messages_delivered = Column(Integer, default=0)
    messages_read = Column(Integer, default=0)
    messages_failed = Column(Integer, default=0)
    messages_received = Column(Integer, default=0)

    # Delivery metrics
    delivery_rate = Column(Numeric(5, 4), default=0)  # delivered/sent
    read_rate = Column(Numeric(5, 4), default=0)  # read/delivered
    response_rate = Column(Numeric(5, 4), default=0)  # received/sent

    # Timing metrics (in minutes)
    avg_first_response_time = Column(Integer, default=0)
    avg_delivery_time = Column(Integer, default=0)

    # Message types
    template_messages = Column(Integer, default=0)
    freeform_messages = Column(Integer, default=0)
    media_messages = Column(Integer, default=0)

    # Engagement metrics
    unique_conversations = Column(Integer, default=0)
    active_conversations = Column(Integer, default=0)
    unread_messages = Column(Integer, default=0)

    # Campaign metrics
    reminder_messages = Column(Integer, default=0)
    promotional_messages = Column(Integer, default=0)
    support_messages = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_whatsapp_date_hour', 'date', 'hour'),
    )


class NoShowMetrics(Base):
    """
    Aggregated metrics for no-show analysis and forecasting.
    """
    __tablename__ = "no_show_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Time dimensions
    date = Column(Date, nullable=False, index=True)

    # Appointment metrics
    appointments_scheduled = Column(Integer, default=0)
    appointments_confirmed = Column(Integer, default=0)
    appointments_completed = Column(Integer, default=0)
    appointments_no_show = Column(Integer, default=0)
    appointments_cancelled = Column(Integer, default=0)

    # No-show rates
    no_show_rate = Column(Numeric(5, 4), default=0)  # no_shows/confirmed
    cancellation_rate = Column(Numeric(5, 4), default=0)  # cancelled/scheduled

    # Breakdown by professional/clinic
    professional_id = Column(String(100), index=True)
    professional_name = Column(String(200))
    clinic_id = Column(String(100), index=True)
    clinic_name = Column(String(200))
    specialty = Column(String(100), index=True)

    # Breakdown by appointment type
    consultation_no_shows = Column(Integer, default=0)
    follow_up_no_shows = Column(Integer, default=0)
    procedure_no_shows = Column(Integer, default=0)

    # Risk factors
    first_time_patients = Column(Integer, default=0)
    first_time_no_shows = Column(Integer, default=0)
    repeat_patients = Column(Integer, default=0)
    repeat_no_shows = Column(Integer, default=0)

    # Reminder effectiveness
    reminded_24h = Column(Integer, default=0)
    reminded_24h_showed = Column(Integer, default=0)
    reminded_3h = Column(Integer, default=0)
    reminded_3h_showed = Column(Integer, default=0)
    not_reminded = Column(Integer, default=0)
    not_reminded_showed = Column(Integer, default=0)

    # Forecasting metrics (calculated by ML models)
    predicted_no_shows = Column(Integer, default=0)
    risk_score = Column(Numeric(3, 2), default=0)  # 0.00 to 1.00

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_no_show_date_professional', 'date', 'professional_id'),
        Index('idx_no_show_date_clinic', 'date', 'clinic_id'),
        Index('idx_no_show_date_specialty', 'date', 'specialty'),
    )


class MetricsCheckpoint(Base):
    """
    Checkpoint table for tracking metrics aggregation progress.
    """
    __tablename__ = "metrics_checkpoints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Checkpoint identification
    metric_type = Column(String(100), nullable=False, unique=True, index=True)
    last_processed_timestamp = Column(DateTime(timezone=True), nullable=False)

    # Aggregation metadata
    total_records_processed = Column(Integer, default=0)
    last_batch_size = Column(Integer, default=0)
    processing_duration_seconds = Column(Integer, default=0)

    # Error tracking
    last_error = Column(String(500))
    error_count = Column(Integer, default=0)
    last_successful_run = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @classmethod
    def get_or_create_checkpoint(cls, session, metric_type: str, default_timestamp: datetime = None):
        """Get existing checkpoint or create new one."""
        checkpoint = session.query(cls).filter_by(metric_type=metric_type).first()

        if not checkpoint:
            checkpoint = cls(
                metric_type=metric_type,
                last_processed_timestamp=default_timestamp or datetime.utcnow()
            )
            session.add(checkpoint)
            session.commit()

        return checkpoint

    def update_progress(self, new_timestamp: datetime, records_processed: int,
                       duration_seconds: int, session) -> None:
        """Update checkpoint with new progress."""
        self.last_processed_timestamp = new_timestamp
        self.total_records_processed += records_processed
        self.last_batch_size = records_processed
        self.processing_duration_seconds = duration_seconds
        self.last_successful_run = datetime.utcnow()
        self.error_count = 0  # Reset error count on success
        self.last_error = None
        session.commit()

    def record_error(self, error_message: str, session) -> None:
        """Record an error in the checkpoint."""
        self.last_error = error_message[:500]  # Truncate long errors
        self.error_count += 1
        session.commit()