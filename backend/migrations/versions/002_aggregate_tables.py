"""Create aggregate tables for metrics

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create lead_funnel_metrics table
    op.create_table('lead_funnel_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hour', sa.Integer(), nullable=True),
        sa.Column('leads_new', sa.Integer(), nullable=True),
        sa.Column('leads_contacted', sa.Integer(), nullable=True),
        sa.Column('leads_qualified', sa.Integer(), nullable=True),
        sa.Column('leads_booked', sa.Integer(), nullable=True),
        sa.Column('leads_confirmed', sa.Integer(), nullable=True),
        sa.Column('leads_showed', sa.Integer(), nullable=True),
        sa.Column('leads_no_show', sa.Integer(), nullable=True),
        sa.Column('leads_converted', sa.Integer(), nullable=True),
        sa.Column('leads_lost', sa.Integer(), nullable=True),
        sa.Column('contact_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('qualification_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('booking_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('show_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('conversion_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('source_organic', sa.Integer(), nullable=True),
        sa.Column('source_paid_ads', sa.Integer(), nullable=True),
        sa.Column('source_social_media', sa.Integer(), nullable=True),
        sa.Column('source_referral', sa.Integer(), nullable=True),
        sa.Column('source_direct', sa.Integer(), nullable=True),
        sa.Column('source_other', sa.Integer(), nullable=True),
        sa.Column('hot_leads', sa.Integer(), nullable=True),
        sa.Column('warm_leads', sa.Integer(), nullable=True),
        sa.Column('cold_leads', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lead_funnel_metrics_date'), 'lead_funnel_metrics', ['date'], unique=False)
    op.create_index(op.f('ix_lead_funnel_metrics_hour'), 'lead_funnel_metrics', ['hour'], unique=False)
    op.create_index('idx_funnel_date_hour', 'lead_funnel_metrics', ['date', 'hour'], unique=False)

    # Create telephony_metrics table
    op.create_table('telephony_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hour', sa.Integer(), nullable=True),
        sa.Column('calls_initiated', sa.Integer(), nullable=True),
        sa.Column('calls_answered', sa.Integer(), nullable=True),
        sa.Column('calls_completed', sa.Integer(), nullable=True),
        sa.Column('calls_failed', sa.Integer(), nullable=True),
        sa.Column('calls_no_answer', sa.Integer(), nullable=True),
        sa.Column('calls_busy', sa.Integer(), nullable=True),
        sa.Column('answer_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('completion_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('total_talk_time', sa.Integer(), nullable=True),
        sa.Column('total_ring_time', sa.Integer(), nullable=True),
        sa.Column('total_queue_time', sa.Integer(), nullable=True),
        sa.Column('avg_handle_time', sa.Integer(), nullable=True),
        sa.Column('avg_talk_time', sa.Integer(), nullable=True),
        sa.Column('outcome_successful', sa.Integer(), nullable=True),
        sa.Column('outcome_no_answer', sa.Integer(), nullable=True),
        sa.Column('outcome_voicemail', sa.Integer(), nullable=True),
        sa.Column('outcome_interested', sa.Integer(), nullable=True),
        sa.Column('outcome_not_interested', sa.Integer(), nullable=True),
        sa.Column('outcome_callback_requested', sa.Integer(), nullable=True),
        sa.Column('outcome_appointment_booked', sa.Integer(), nullable=True),
        sa.Column('outcome_technical_issue', sa.Integer(), nullable=True),
        sa.Column('total_cost_cents', sa.Integer(), nullable=True),
        sa.Column('avg_cost_per_call_cents', sa.Integer(), nullable=True),
        sa.Column('unique_leads_called', sa.Integer(), nullable=True),
        sa.Column('repeat_calls', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_telephony_metrics_date'), 'telephony_metrics', ['date'], unique=False)
    op.create_index(op.f('ix_telephony_metrics_hour'), 'telephony_metrics', ['hour'], unique=False)
    op.create_index('idx_telephony_date_hour', 'telephony_metrics', ['date', 'hour'], unique=False)

    # Create whatsapp_metrics table
    op.create_table('whatsapp_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hour', sa.Integer(), nullable=True),
        sa.Column('messages_sent', sa.Integer(), nullable=True),
        sa.Column('messages_delivered', sa.Integer(), nullable=True),
        sa.Column('messages_read', sa.Integer(), nullable=True),
        sa.Column('messages_failed', sa.Integer(), nullable=True),
        sa.Column('messages_received', sa.Integer(), nullable=True),
        sa.Column('delivery_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('read_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('response_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('avg_first_response_time', sa.Integer(), nullable=True),
        sa.Column('avg_delivery_time', sa.Integer(), nullable=True),
        sa.Column('template_messages', sa.Integer(), nullable=True),
        sa.Column('freeform_messages', sa.Integer(), nullable=True),
        sa.Column('media_messages', sa.Integer(), nullable=True),
        sa.Column('unique_conversations', sa.Integer(), nullable=True),
        sa.Column('active_conversations', sa.Integer(), nullable=True),
        sa.Column('unread_messages', sa.Integer(), nullable=True),
        sa.Column('reminder_messages', sa.Integer(), nullable=True),
        sa.Column('promotional_messages', sa.Integer(), nullable=True),
        sa.Column('support_messages', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whatsapp_metrics_date'), 'whatsapp_metrics', ['date'], unique=False)
    op.create_index(op.f('ix_whatsapp_metrics_hour'), 'whatsapp_metrics', ['hour'], unique=False)
    op.create_index('idx_whatsapp_date_hour', 'whatsapp_metrics', ['date', 'hour'], unique=False)

    # Create no_show_metrics table
    op.create_table('no_show_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('appointments_scheduled', sa.Integer(), nullable=True),
        sa.Column('appointments_confirmed', sa.Integer(), nullable=True),
        sa.Column('appointments_completed', sa.Integer(), nullable=True),
        sa.Column('appointments_no_show', sa.Integer(), nullable=True),
        sa.Column('appointments_cancelled', sa.Integer(), nullable=True),
        sa.Column('no_show_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('cancellation_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('professional_id', sa.String(length=100), nullable=True),
        sa.Column('professional_name', sa.String(length=200), nullable=True),
        sa.Column('clinic_id', sa.String(length=100), nullable=True),
        sa.Column('clinic_name', sa.String(length=200), nullable=True),
        sa.Column('specialty', sa.String(length=100), nullable=True),
        sa.Column('consultation_no_shows', sa.Integer(), nullable=True),
        sa.Column('follow_up_no_shows', sa.Integer(), nullable=True),
        sa.Column('procedure_no_shows', sa.Integer(), nullable=True),
        sa.Column('first_time_patients', sa.Integer(), nullable=True),
        sa.Column('first_time_no_shows', sa.Integer(), nullable=True),
        sa.Column('repeat_patients', sa.Integer(), nullable=True),
        sa.Column('repeat_no_shows', sa.Integer(), nullable=True),
        sa.Column('reminded_24h', sa.Integer(), nullable=True),
        sa.Column('reminded_24h_showed', sa.Integer(), nullable=True),
        sa.Column('reminded_3h', sa.Integer(), nullable=True),
        sa.Column('reminded_3h_showed', sa.Integer(), nullable=True),
        sa.Column('not_reminded', sa.Integer(), nullable=True),
        sa.Column('not_reminded_showed', sa.Integer(), nullable=True),
        sa.Column('predicted_no_shows', sa.Integer(), nullable=True),
        sa.Column('risk_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_no_show_metrics_date'), 'no_show_metrics', ['date'], unique=False)
    op.create_index(op.f('ix_no_show_metrics_professional_id'), 'no_show_metrics', ['professional_id'], unique=False)
    op.create_index(op.f('ix_no_show_metrics_clinic_id'), 'no_show_metrics', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_no_show_metrics_specialty'), 'no_show_metrics', ['specialty'], unique=False)
    op.create_index('idx_no_show_date_professional', 'no_show_metrics', ['date', 'professional_id'], unique=False)
    op.create_index('idx_no_show_date_clinic', 'no_show_metrics', ['date', 'clinic_id'], unique=False)
    op.create_index('idx_no_show_date_specialty', 'no_show_metrics', ['date', 'specialty'], unique=False)

    # Create metrics_checkpoints table
    op.create_table('metrics_checkpoints',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('metric_type', sa.String(length=100), nullable=False),
        sa.Column('last_processed_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_records_processed', sa.Integer(), nullable=True),
        sa.Column('last_batch_size', sa.Integer(), nullable=True),
        sa.Column('processing_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('last_error', sa.String(length=500), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=True),
        sa.Column('last_successful_run', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metrics_checkpoints_metric_type'), 'metrics_checkpoints', ['metric_type'], unique=True)


def downgrade() -> None:
    # Drop all aggregate tables
    op.drop_table('metrics_checkpoints')
    op.drop_table('no_show_metrics')
    op.drop_table('whatsapp_metrics')
    op.drop_table('telephony_metrics')
    op.drop_table('lead_funnel_metrics')