"""Create materialized views for metrics

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create materialized view for daily lead funnel overview
    op.execute("""
        CREATE MATERIALIZED VIEW mv_daily_lead_funnel AS
        SELECT
            DATE(created_at) as date,
            COUNT(*) FILTER (WHERE stage = 'new') as leads_new,
            COUNT(*) FILTER (WHERE stage = 'contacted') as leads_contacted,
            COUNT(*) FILTER (WHERE stage = 'qualified') as leads_qualified,
            COUNT(*) FILTER (WHERE stage = 'booked') as leads_booked,
            COUNT(*) FILTER (WHERE stage = 'confirmed') as leads_confirmed,
            COUNT(*) FILTER (WHERE stage = 'showed') as leads_showed,
            COUNT(*) FILTER (WHERE stage = 'no_show') as leads_no_show,
            COUNT(*) FILTER (WHERE stage = 'converted') as leads_converted,
            COUNT(*) FILTER (WHERE stage = 'lost') as leads_lost,
            COUNT(*) FILTER (WHERE classification = 'hot') as hot_leads,
            COUNT(*) FILTER (WHERE classification = 'warm') as warm_leads,
            COUNT(*) FILTER (WHERE classification = 'cold') as cold_leads,
            COUNT(*) FILTER (WHERE source = 'organic') as source_organic,
            COUNT(*) FILTER (WHERE source = 'paid_ads') as source_paid_ads,
            COUNT(*) FILTER (WHERE source = 'social_media') as source_social_media,
            COUNT(*) FILTER (WHERE source = 'referral') as source_referral,
            COUNT(*) FILTER (WHERE source = 'direct') as source_direct,
            COUNT(*) FILTER (WHERE source = 'other') as source_other
        FROM leads
        WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC;
    """)

    # Create index on the materialized view
    op.execute("CREATE UNIQUE INDEX idx_mv_daily_lead_funnel_date ON mv_daily_lead_funnel (date);")

    # Create materialized view for call performance
    op.execute("""
        CREATE MATERIALIZED VIEW mv_daily_call_metrics AS
        SELECT
            DATE(created_at) as date,
            COUNT(*) as calls_total,
            COUNT(*) FILTER (WHERE status = 'initiated') as calls_initiated,
            COUNT(*) FILTER (WHERE status = 'answered') as calls_answered,
            COUNT(*) FILTER (WHERE status = 'completed') as calls_completed,
            COUNT(*) FILTER (WHERE status = 'failed') as calls_failed,
            COUNT(*) FILTER (WHERE status = 'no_answer') as calls_no_answer,
            COUNT(*) FILTER (WHERE status = 'busy') as calls_busy,
            COALESCE(AVG(duration_seconds) FILTER (WHERE duration_seconds > 0), 0)::INTEGER as avg_duration,
            COALESCE(AVG(talk_time_seconds) FILTER (WHERE talk_time_seconds > 0), 0)::INTEGER as avg_talk_time,
            COALESCE(SUM(cost_cents), 0) as total_cost_cents,
            COUNT(DISTINCT lead_id) as unique_leads_called,
            COUNT(*) FILTER (WHERE outcome = 'appointment_booked') as appointments_booked_via_call,
            COUNT(*) FILTER (WHERE outcome = 'interested') as interested_outcomes,
            COUNT(*) FILTER (WHERE outcome = 'not_interested') as not_interested_outcomes,
            CASE
                WHEN COUNT(*) FILTER (WHERE status = 'initiated') > 0
                THEN ROUND(COUNT(*) FILTER (WHERE status = 'answered')::DECIMAL / COUNT(*) FILTER (WHERE status = 'initiated'), 4)
                ELSE 0
            END as answer_rate
        FROM calls
        WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC;
    """)

    # Create index on call metrics view
    op.execute("CREATE UNIQUE INDEX idx_mv_daily_call_metrics_date ON mv_daily_call_metrics (date);")

    # Create materialized view for WhatsApp metrics
    op.execute("""
        CREATE MATERIALIZED VIEW mv_daily_whatsapp_metrics AS
        SELECT
            DATE(created_at) as date,
            COUNT(*) FILTER (WHERE direction = 'outbound') as messages_sent,
            COUNT(*) FILTER (WHERE direction = 'inbound') as messages_received,
            COUNT(*) FILTER (WHERE status = 'delivered') as messages_delivered,
            COUNT(*) FILTER (WHERE status = 'read') as messages_read,
            COUNT(*) FILTER (WHERE status = 'failed') as messages_failed,
            COUNT(*) FILTER (WHERE channel = 'whatsapp') as whatsapp_messages,
            COUNT(DISTINCT lead_id) as unique_conversations,
            COUNT(*) FILTER (WHERE template_name IS NOT NULL) as template_messages,
            COUNT(*) FILTER (WHERE template_name IS NULL AND direction = 'outbound') as freeform_messages,
            CASE
                WHEN COUNT(*) FILTER (WHERE direction = 'outbound') > 0
                THEN ROUND(COUNT(*) FILTER (WHERE status = 'delivered')::DECIMAL / COUNT(*) FILTER (WHERE direction = 'outbound'), 4)
                ELSE 0
            END as delivery_rate,
            CASE
                WHEN COUNT(*) FILTER (WHERE status = 'delivered') > 0
                THEN ROUND(COUNT(*) FILTER (WHERE status = 'read')::DECIMAL / COUNT(*) FILTER (WHERE status = 'delivered'), 4)
                ELSE 0
            END as read_rate
        FROM messages
        WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC;
    """)

    # Create index on WhatsApp metrics view
    op.execute("CREATE UNIQUE INDEX idx_mv_daily_whatsapp_metrics_date ON mv_daily_whatsapp_metrics (date);")

    # Create materialized view for appointment no-show analysis
    op.execute("""
        CREATE MATERIALIZED VIEW mv_daily_appointment_metrics AS
        SELECT
            DATE(scheduled_date) as date,
            COUNT(*) as appointments_total,
            COUNT(*) FILTER (WHERE status = 'scheduled') as appointments_scheduled,
            COUNT(*) FILTER (WHERE status = 'confirmed') as appointments_confirmed,
            COUNT(*) FILTER (WHERE status = 'completed') as appointments_completed,
            COUNT(*) FILTER (WHERE status = 'no_show') as appointments_no_show,
            COUNT(*) FILTER (WHERE status = 'cancelled') as appointments_cancelled,
            COUNT(DISTINCT professional_id) as unique_professionals,
            COUNT(DISTINCT clinic_id) as unique_clinics,
            COUNT(*) FILTER (WHERE reminder_sent_24h = true) as reminded_24h,
            COUNT(*) FILTER (WHERE reminder_sent_3h = true) as reminded_3h,
            COUNT(*) FILTER (WHERE appointment_type = 'consultation') as consultations,
            COUNT(*) FILTER (WHERE appointment_type = 'follow_up') as follow_ups,
            COUNT(*) FILTER (WHERE appointment_type = 'procedure') as procedures,
            CASE
                WHEN COUNT(*) FILTER (WHERE status IN ('confirmed', 'completed', 'no_show')) > 0
                THEN ROUND(COUNT(*) FILTER (WHERE status = 'no_show')::DECIMAL / COUNT(*) FILTER (WHERE status IN ('confirmed', 'completed', 'no_show')), 4)
                ELSE 0
            END as no_show_rate,
            CASE
                WHEN COUNT(*) > 0
                THEN ROUND(COUNT(*) FILTER (WHERE status = 'cancelled')::DECIMAL / COUNT(*), 4)
                ELSE 0
            END as cancellation_rate
        FROM appointments
        WHERE scheduled_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY DATE(scheduled_date)
        ORDER BY date DESC;
    """)

    # Create index on appointment metrics view
    op.execute("CREATE UNIQUE INDEX idx_mv_daily_appointment_metrics_date ON mv_daily_appointment_metrics (date);")

    # Create materialized view for real-time dashboard summary
    op.execute("""
        CREATE MATERIALIZED VIEW mv_realtime_summary AS
        SELECT
            'today'::text as period,
            CURRENT_DATE as date,

            -- Lead metrics (today)
            (SELECT COUNT(*) FROM leads WHERE DATE(created_at) = CURRENT_DATE) as leads_today,
            (SELECT COUNT(*) FROM leads WHERE DATE(created_at) = CURRENT_DATE AND classification = 'hot') as hot_leads_today,
            (SELECT COUNT(*) FROM leads WHERE DATE(last_contacted_at) = CURRENT_DATE) as leads_contacted_today,

            -- Call metrics (today)
            (SELECT COUNT(*) FROM calls WHERE DATE(created_at) = CURRENT_DATE) as calls_today,
            (SELECT COUNT(*) FROM calls WHERE DATE(created_at) = CURRENT_DATE AND status = 'answered') as calls_answered_today,
            (SELECT COALESCE(SUM(duration_seconds), 0) FROM calls WHERE DATE(created_at) = CURRENT_DATE) as total_talk_time_today,

            -- Message metrics (today)
            (SELECT COUNT(*) FROM messages WHERE DATE(created_at) = CURRENT_DATE AND direction = 'outbound') as messages_sent_today,
            (SELECT COUNT(*) FROM messages WHERE DATE(created_at) = CURRENT_DATE AND status = 'delivered') as messages_delivered_today,

            -- Appointment metrics (today)
            (SELECT COUNT(*) FROM appointments WHERE DATE(scheduled_date) = CURRENT_DATE) as appointments_today,
            (SELECT COUNT(*) FROM appointments WHERE DATE(scheduled_date) = CURRENT_DATE AND status = 'confirmed') as appointments_confirmed_today,
            (SELECT COUNT(*) FROM appointments WHERE DATE(scheduled_date) = CURRENT_DATE AND status = 'no_show') as no_shows_today,

            -- Active metrics
            (SELECT COUNT(*) FROM leads WHERE is_active = true) as active_leads,
            (SELECT COUNT(*) FROM appointments WHERE status = 'confirmed' AND scheduled_date > NOW()) as upcoming_appointments,
            (SELECT COUNT(*) FROM messages WHERE direction = 'inbound' AND read_at IS NULL) as unread_messages,

            CURRENT_TIMESTAMP as last_updated;
    """)

    # Create a function to refresh all materialized views
    op.execute("""
        CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW mv_daily_lead_funnel;
            REFRESH MATERIALIZED VIEW mv_daily_call_metrics;
            REFRESH MATERIALIZED VIEW mv_daily_whatsapp_metrics;
            REFRESH MATERIALIZED VIEW mv_daily_appointment_metrics;
            REFRESH MATERIALIZED VIEW mv_realtime_summary;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    # Drop the refresh function
    op.execute("DROP FUNCTION IF EXISTS refresh_all_materialized_views();")

    # Drop all materialized views
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_realtime_summary;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_daily_appointment_metrics;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_daily_whatsapp_metrics;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_daily_call_metrics;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_daily_lead_funnel;")