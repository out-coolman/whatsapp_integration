"""Initial schema with all core tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE leadstage AS ENUM ('new', 'contacted', 'qualified', 'booked', 'confirmed', 'showed', 'no_show', 'converted', 'lost')")
    op.execute("CREATE TYPE leadsource AS ENUM ('organic', 'paid_ads', 'social_media', 'referral', 'direct', 'other')")
    op.execute("CREATE TYPE leadclassification AS ENUM ('hot', 'warm', 'cold')")
    op.execute("CREATE TYPE messagedirection AS ENUM ('inbound', 'outbound')")
    op.execute("CREATE TYPE messagestatus AS ENUM ('queued', 'sent', 'delivered', 'read', 'failed')")
    op.execute("CREATE TYPE messagechannel AS ENUM ('whatsapp', 'sms', 'email', 'voice')")
    op.execute("CREATE TYPE appointmentstatus AS ENUM ('scheduled', 'confirmed', 'reminded', 'completed', 'no_show', 'cancelled', 'rescheduled')")
    op.execute("CREATE TYPE appointmenttype AS ENUM ('consultation', 'follow_up', 'procedure', 'emergency', 'preventive')")
    op.execute("CREATE TYPE callstatus AS ENUM ('queued', 'initiated', 'ringing', 'answered', 'completed', 'failed', 'busy', 'no_answer', 'cancelled')")
    op.execute("CREATE TYPE calldirection AS ENUM ('inbound', 'outbound')")
    op.execute("CREATE TYPE calloutcome AS ENUM ('successful', 'no_answer', 'busy', 'voicemail', 'wrong_number', 'interested', 'not_interested', 'callback_requested', 'appointment_booked', 'technical_issue')")
    op.execute("CREATE TYPE loglevel AS ENUM ('debug', 'info', 'warning', 'error', 'critical')")
    op.execute("CREATE TYPE logcategory AS ENUM ('webhook', 'api_call', 'job', 'system', 'security', 'business', 'integration')")
    op.execute("CREATE TYPE eventtype AS ENUM ('lead_created', 'lead_updated', 'lead_stage_changed', 'lead_tag_added', 'lead_tag_removed', 'message_received', 'message_sent', 'message_delivered', 'message_read', 'message_failed', 'call_initiated', 'call_answered', 'call_completed', 'call_failed', 'appointment_booked', 'appointment_confirmed', 'appointment_reminded', 'appointment_completed', 'appointment_no_show', 'appointment_cancelled', 'hot_lead_detected', 'handoff_triggered', 'reactivation_triggered', 'job_started', 'job_completed', 'job_failed', 'webhook_received', 'api_call_made')")
    op.execute("CREATE TYPE eventstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'skipped')")

    # Create leads table
    op.create_table('leads',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('helena_id', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('stage', postgresql.ENUM(name='leadstage'), nullable=False),
        sa.Column('classification', postgresql.ENUM(name='leadclassification'), nullable=True),
        sa.Column('source', postgresql.ENUM(name='leadsource'), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('custom_fields', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('assigned_agent_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_contacted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('qualified_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leads_helena_id'), 'leads', ['helena_id'], unique=True)
    op.create_index(op.f('ix_leads_email'), 'leads', ['email'], unique=False)
    op.create_index(op.f('ix_leads_phone'), 'leads', ['phone'], unique=False)
    op.create_index(op.f('ix_leads_stage'), 'leads', ['stage'], unique=False)
    op.create_index(op.f('ix_leads_classification'), 'leads', ['classification'], unique=False)
    op.create_index(op.f('ix_leads_source'), 'leads', ['source'], unique=False)
    op.create_index(op.f('ix_leads_is_active'), 'leads', ['is_active'], unique=False)

    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('helena_message_id', sa.String(), nullable=True),
        sa.Column('lead_id', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('channel', postgresql.ENUM(name='messagechannel'), nullable=False),
        sa.Column('direction', postgresql.ENUM(name='messagedirection'), nullable=False),
        sa.Column('status', postgresql.ENUM(name='messagestatus'), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('template_name', sa.String(length=100), nullable=True),
        sa.Column('template_params', sa.JSON(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_helena_message_id'), 'messages', ['helena_message_id'], unique=True)
    op.create_index(op.f('ix_messages_lead_id'), 'messages', ['lead_id'], unique=False)
    op.create_index(op.f('ix_messages_channel'), 'messages', ['channel'], unique=False)
    op.create_index(op.f('ix_messages_direction'), 'messages', ['direction'], unique=False)
    op.create_index(op.f('ix_messages_status'), 'messages', ['status'], unique=False)

    # Create appointments table
    op.create_table('appointments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('ninsaude_id', sa.String(), nullable=True),
        sa.Column('lead_id', sa.String(), nullable=False),
        sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('appointment_type', postgresql.ENUM(name='appointmenttype'), nullable=True),
        sa.Column('status', postgresql.ENUM(name='appointmentstatus'), nullable=True),
        sa.Column('professional_id', sa.String(length=100), nullable=False),
        sa.Column('professional_name', sa.String(length=200), nullable=True),
        sa.Column('clinic_id', sa.String(length=100), nullable=False),
        sa.Column('clinic_name', sa.String(length=200), nullable=True),
        sa.Column('specialty', sa.String(length=100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('room_number', sa.String(length=50), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('estimated_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('insurance_covered', sa.Boolean(), nullable=True),
        sa.Column('reminder_sent_24h', sa.Boolean(), nullable=True),
        sa.Column('reminder_sent_3h', sa.Boolean(), nullable=True),
        sa.Column('confirmation_sent', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('cancellation_reason', sa.String(length=500), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reminded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('no_show_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointments_ninsaude_id'), 'appointments', ['ninsaude_id'], unique=True)
    op.create_index(op.f('ix_appointments_lead_id'), 'appointments', ['lead_id'], unique=False)
    op.create_index(op.f('ix_appointments_scheduled_date'), 'appointments', ['scheduled_date'], unique=False)
    op.create_index(op.f('ix_appointments_status'), 'appointments', ['status'], unique=False)

    # Create calls table
    op.create_table('calls',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('vapi_call_id', sa.String(), nullable=True),
        sa.Column('twilio_call_sid', sa.String(), nullable=True),
        sa.Column('lead_id', sa.String(), nullable=False),
        sa.Column('direction', postgresql.ENUM(name='calldirection'), nullable=False),
        sa.Column('status', postgresql.ENUM(name='callstatus'), nullable=True),
        sa.Column('outcome', postgresql.ENUM(name='calloutcome'), nullable=True),
        sa.Column('from_number', sa.String(length=20), nullable=False),
        sa.Column('to_number', sa.String(length=20), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('queue_time_seconds', sa.Integer(), nullable=True),
        sa.Column('ring_time_seconds', sa.Integer(), nullable=True),
        sa.Column('talk_time_seconds', sa.Integer(), nullable=True),
        sa.Column('recording_url', sa.String(length=500), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('transcript_summary', sa.Text(), nullable=True),
        sa.Column('vapi_assistant_id', sa.String(length=100), nullable=True),
        sa.Column('vapi_function_calls', sa.JSON(), nullable=True),
        sa.Column('ai_sentiment', sa.String(length=50), nullable=True),
        sa.Column('ai_intent', sa.String(length=100), nullable=True),
        sa.Column('cost_cents', sa.Integer(), nullable=True),
        sa.Column('cost_per_minute_cents', sa.Integer(), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('queued_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('initiated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ringing_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calls_vapi_call_id'), 'calls', ['vapi_call_id'], unique=True)
    op.create_index(op.f('ix_calls_twilio_call_sid'), 'calls', ['twilio_call_sid'], unique=True)
    op.create_index(op.f('ix_calls_lead_id'), 'calls', ['lead_id'], unique=False)
    op.create_index(op.f('ix_calls_direction'), 'calls', ['direction'], unique=False)
    op.create_index(op.f('ix_calls_status'), 'calls', ['status'], unique=False)
    op.create_index(op.f('ix_calls_outcome'), 'calls', ['outcome'], unique=False)

    # Create events table
    op.create_table('events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('event_type', postgresql.ENUM(name='eventtype'), nullable=False),
        sa.Column('status', postgresql.ENUM(name='eventstatus'), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('lead_id', sa.String(), nullable=True),
        sa.Column('appointment_id', sa.String(), nullable=True),
        sa.Column('call_id', sa.String(), nullable=True),
        sa.Column('message_id', sa.String(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('triggers_actions', sa.JSON(), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_event_type'), 'events', ['event_type'], unique=False)
    op.create_index(op.f('ix_events_status'), 'events', ['status'], unique=False)
    op.create_index(op.f('ix_events_source'), 'events', ['source'], unique=False)
    op.create_index(op.f('ix_events_lead_id'), 'events', ['lead_id'], unique=False)
    op.create_index(op.f('ix_events_appointment_id'), 'events', ['appointment_id'], unique=False)
    op.create_index(op.f('ix_events_call_id'), 'events', ['call_id'], unique=False)
    op.create_index(op.f('ix_events_message_id'), 'events', ['message_id'], unique=False)
    op.create_index(op.f('ix_events_correlation_id'), 'events', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_events_idempotency_key'), 'events', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_events_occurred_at'), 'events', ['occurred_at'], unique=False)
    op.create_index('idx_events_type_status', 'events', ['event_type', 'status'], unique=False)
    op.create_index('idx_events_lead_occurred', 'events', ['lead_id', 'occurred_at'], unique=False)
    op.create_index('idx_events_source_occurred', 'events', ['source', 'occurred_at'], unique=False)
    op.create_index('idx_events_correlation_occurred', 'events', ['correlation_id', 'occurred_at'], unique=False)

    # Create logs table
    op.create_table('logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('level', postgresql.ENUM(name='loglevel'), nullable=False),
        sa.Column('category', postgresql.ENUM(name='logcategory'), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=True),
        sa.Column('lead_id', sa.String(), nullable=True),
        sa.Column('appointment_id', sa.String(), nullable=True),
        sa.Column('call_id', sa.String(), nullable=True),
        sa.Column('message_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('memory_usage_mb', sa.Integer(), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_logs_level'), 'logs', ['level'], unique=False)
    op.create_index(op.f('ix_logs_category'), 'logs', ['category'], unique=False)
    op.create_index(op.f('ix_logs_source'), 'logs', ['source'], unique=False)
    op.create_index(op.f('ix_logs_request_id'), 'logs', ['request_id'], unique=False)
    op.create_index(op.f('ix_logs_correlation_id'), 'logs', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_logs_lead_id'), 'logs', ['lead_id'], unique=False)
    op.create_index(op.f('ix_logs_appointment_id'), 'logs', ['appointment_id'], unique=False)
    op.create_index(op.f('ix_logs_call_id'), 'logs', ['call_id'], unique=False)
    op.create_index(op.f('ix_logs_message_id'), 'logs', ['message_id'], unique=False)
    op.create_index(op.f('ix_logs_user_id'), 'logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_logs_created_at'), 'logs', ['created_at'], unique=False)
    op.create_index('idx_logs_level_category', 'logs', ['level', 'category'], unique=False)
    op.create_index('idx_logs_source_created', 'logs', ['source', 'created_at'], unique=False)
    op.create_index('idx_logs_lead_created', 'logs', ['lead_id', 'created_at'], unique=False)
    op.create_index('idx_logs_correlation_created', 'logs', ['correlation_id', 'created_at'], unique=False)


def downgrade() -> None:
    # Drop all indexes and tables
    op.drop_table('logs')
    op.drop_table('events')
    op.drop_table('calls')
    op.drop_table('appointments')
    op.drop_table('messages')
    op.drop_table('leads')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS eventstatus")
    op.execute("DROP TYPE IF EXISTS eventtype")
    op.execute("DROP TYPE IF EXISTS logcategory")
    op.execute("DROP TYPE IF EXISTS loglevel")
    op.execute("DROP TYPE IF EXISTS calloutcome")
    op.execute("DROP TYPE IF EXISTS calldirection")
    op.execute("DROP TYPE IF EXISTS callstatus")
    op.execute("DROP TYPE IF EXISTS appointmenttype")
    op.execute("DROP TYPE IF EXISTS appointmentstatus")
    op.execute("DROP TYPE IF EXISTS messagechannel")
    op.execute("DROP TYPE IF EXISTS messagestatus")
    op.execute("DROP TYPE IF EXISTS messagedirection")
    op.execute("DROP TYPE IF EXISTS leadclassification")
    op.execute("DROP TYPE IF EXISTS leadsource")
    op.execute("DROP TYPE IF EXISTS leadstage")