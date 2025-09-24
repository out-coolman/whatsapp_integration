"""
Metrics aggregation jobs for analytics and reporting.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from datetime import datetime, date, timedelta
import logging
from typing import Dict, Any

from app.core.database import SessionLocal
from app.models.aggregates import (
    LeadFunnelMetrics, TelephonyMetrics, WhatsAppMetrics,
    NoShowMetrics, MetricsCheckpoint
)
from app.models.lead import Lead
from app.models.call import Call
from app.models.message import Message
from app.models.appointment import Appointment

logger = logging.getLogger(__name__)


def aggregate_all_metrics() -> Dict[str, Any]:
    """Run all metrics aggregation jobs."""
    results = {}

    try:
        results["lead_funnel"] = aggregate_lead_funnel_metrics()
        results["telephony"] = aggregate_telephony_metrics()
        results["whatsapp"] = aggregate_whatsapp_metrics()
        results["no_shows"] = aggregate_no_show_metrics()
        results["refresh_views"] = refresh_materialized_views()

        logger.info(f"Completed all metrics aggregation: {results}")
        return {"status": "success", "results": results}

    except Exception as e:
        logger.error(f"Error in metrics aggregation: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def aggregate_lead_funnel_metrics(target_date: date = None) -> Dict[str, Any]:
    """Aggregate lead funnel metrics for a specific date."""
    db = SessionLocal()
    try:
        if not target_date:
            target_date = date.today() - timedelta(days=1)  # Previous day by default

        start_time = datetime.utcnow()

        # Get checkpoint
        checkpoint = MetricsCheckpoint.get_or_create_checkpoint(
            db, "lead_funnel", datetime.combine(target_date, datetime.min.time())
        )

        # Aggregate lead data for the date
        date_start = datetime.combine(target_date, datetime.min.time())
        date_end = datetime.combine(target_date, datetime.max.time())

        # Count leads by stage and source for the date
        lead_counts = db.query(
            func.count().label('total'),
            Lead.stage,
            Lead.source,
            Lead.classification
        ).filter(
            Lead.created_at.between(date_start, date_end)
        ).group_by(Lead.stage, Lead.source, Lead.classification).all()

        # Initialize metrics
        metrics_data = {
            'date': target_date,
            'leads_new': 0,
            'leads_contacted': 0,
            'leads_qualified': 0,
            'leads_booked': 0,
            'leads_confirmed': 0,
            'leads_showed': 0,
            'leads_no_show': 0,
            'leads_converted': 0,
            'leads_lost': 0,
            'source_organic': 0,
            'source_paid_ads': 0,
            'source_social_media': 0,
            'source_referral': 0,
            'source_direct': 0,
            'source_other': 0,
            'hot_leads': 0,
            'warm_leads': 0,
            'cold_leads': 0
        }

        # Process counts
        for count_data in lead_counts:
            total, stage, source, classification = count_data

            # Stage counts
            if stage:
                stage_key = f"leads_{stage}"
                if stage_key in metrics_data:
                    metrics_data[stage_key] += total

            # Source counts
            if source:
                source_key = f"source_{source}"
                if source_key in metrics_data:
                    metrics_data[source_key] += total

            # Classification counts
            if classification:
                class_key = f"{classification}_leads"
                if class_key in metrics_data:
                    metrics_data[class_key] += total

        # Calculate conversion rates
        if metrics_data['leads_new'] > 0:
            metrics_data['contact_rate'] = metrics_data['leads_contacted'] / metrics_data['leads_new']
        if metrics_data['leads_contacted'] > 0:
            metrics_data['qualification_rate'] = metrics_data['leads_qualified'] / metrics_data['leads_contacted']
        if metrics_data['leads_qualified'] > 0:
            metrics_data['booking_rate'] = metrics_data['leads_booked'] / metrics_data['leads_qualified']
        if metrics_data['leads_booked'] > 0:
            metrics_data['show_rate'] = metrics_data['leads_showed'] / metrics_data['leads_booked']
        if metrics_data['leads_new'] > 0:
            metrics_data['conversion_rate'] = metrics_data['leads_converted'] / metrics_data['leads_new']

        # Upsert metrics record
        existing_metrics = db.query(LeadFunnelMetrics).filter_by(
            date=target_date, hour=None
        ).first()

        if existing_metrics:
            for key, value in metrics_data.items():
                if hasattr(existing_metrics, key):
                    setattr(existing_metrics, key, value)
        else:
            existing_metrics = LeadFunnelMetrics(**metrics_data)
            db.add(existing_metrics)

        db.commit()

        # Update checkpoint
        duration = int((datetime.utcnow() - start_time).total_seconds())
        checkpoint.update_progress(
            datetime.combine(target_date + timedelta(days=1), datetime.min.time()),
            metrics_data['leads_new'],
            duration,
            db
        )

        logger.info(f"Aggregated lead funnel metrics for {target_date}: {metrics_data['leads_new']} leads")
        return {"status": "success", "date": target_date.isoformat(), "leads_processed": metrics_data['leads_new']}

    except Exception as e:
        logger.error(f"Error aggregating lead funnel metrics: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


def aggregate_telephony_metrics(target_date: date = None) -> Dict[str, Any]:
    """Aggregate telephony metrics for a specific date."""
    db = SessionLocal()
    try:
        if not target_date:
            target_date = date.today() - timedelta(days=1)

        start_time = datetime.utcnow()

        # Get checkpoint
        checkpoint = MetricsCheckpoint.get_or_create_checkpoint(
            db, "telephony", datetime.combine(target_date, datetime.min.time())
        )

        date_start = datetime.combine(target_date, datetime.min.time())
        date_end = datetime.combine(target_date, datetime.max.time())

        # Aggregate call data
        call_stats = db.query(
            func.count().label('total_calls'),
            func.count().filter(Call.status == 'initiated').label('calls_initiated'),
            func.count().filter(Call.status == 'answered').label('calls_answered'),
            func.count().filter(Call.status == 'completed').label('calls_completed'),
            func.count().filter(Call.status == 'failed').label('calls_failed'),
            func.count().filter(Call.status == 'no_answer').label('calls_no_answer'),
            func.count().filter(Call.status == 'busy').label('calls_busy'),
            func.sum(Call.duration_seconds).label('total_duration'),
            func.sum(Call.talk_time_seconds).label('total_talk_time'),
            func.sum(Call.ring_time_seconds).label('total_ring_time'),
            func.sum(Call.queue_time_seconds).label('total_queue_time'),
            func.sum(Call.cost_cents).label('total_cost_cents'),
            func.count(func.distinct(Call.lead_id)).label('unique_leads')
        ).filter(
            Call.created_at.between(date_start, date_end)
        ).first()

        # Calculate averages and rates
        calls_initiated = call_stats.calls_initiated or 0
        calls_answered = call_stats.calls_answered or 0

        metrics_data = {
            'date': target_date,
            'calls_initiated': calls_initiated,
            'calls_answered': calls_answered,
            'calls_completed': call_stats.calls_completed or 0,
            'calls_failed': call_stats.calls_failed or 0,
            'calls_no_answer': call_stats.calls_no_answer or 0,
            'calls_busy': call_stats.calls_busy or 0,
            'answer_rate': (calls_answered / calls_initiated) if calls_initiated > 0 else 0,
            'completion_rate': (call_stats.calls_completed / calls_answered) if calls_answered > 0 else 0,
            'total_talk_time': call_stats.total_talk_time or 0,
            'total_ring_time': call_stats.total_ring_time or 0,
            'total_queue_time': call_stats.total_queue_time or 0,
            'avg_handle_time': ((call_stats.total_talk_time or 0) + (call_stats.total_ring_time or 0) + (call_stats.total_queue_time or 0)) // max(calls_initiated, 1),
            'avg_talk_time': (call_stats.total_talk_time or 0) // max(calls_answered, 1),
            'total_cost_cents': call_stats.total_cost_cents or 0,
            'avg_cost_per_call_cents': (call_stats.total_cost_cents or 0) // max(calls_initiated, 1),
            'unique_leads_called': call_stats.unique_leads or 0,
            'repeat_calls': max(0, calls_initiated - (call_stats.unique_leads or 0))
        }

        # Upsert metrics record
        existing_metrics = db.query(TelephonyMetrics).filter_by(
            date=target_date, hour=None
        ).first()

        if existing_metrics:
            for key, value in metrics_data.items():
                if hasattr(existing_metrics, key):
                    setattr(existing_metrics, key, value)
        else:
            existing_metrics = TelephonyMetrics(**metrics_data)
            db.add(existing_metrics)

        db.commit()

        # Update checkpoint
        duration = int((datetime.utcnow() - start_time).total_seconds())
        checkpoint.update_progress(
            datetime.combine(target_date + timedelta(days=1), datetime.min.time()),
            calls_initiated,
            duration,
            db
        )

        logger.info(f"Aggregated telephony metrics for {target_date}: {calls_initiated} calls")
        return {"status": "success", "date": target_date.isoformat(), "calls_processed": calls_initiated}

    except Exception as e:
        logger.error(f"Error aggregating telephony metrics: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


def aggregate_whatsapp_metrics(target_date: date = None) -> Dict[str, Any]:
    """Aggregate WhatsApp messaging metrics for a specific date."""
    db = SessionLocal()
    try:
        if not target_date:
            target_date = date.today() - timedelta(days=1)

        start_time = datetime.utcnow()

        # Get checkpoint
        checkpoint = MetricsCheckpoint.get_or_create_checkpoint(
            db, "whatsapp", datetime.combine(target_date, datetime.min.time())
        )

        date_start = datetime.combine(target_date, datetime.min.time())
        date_end = datetime.combine(target_date, datetime.max.time())

        # Aggregate message data
        message_stats = db.query(
            func.count().filter(Message.direction == 'outbound').label('messages_sent'),
            func.count().filter(Message.direction == 'inbound').label('messages_received'),
            func.count().filter(Message.status == 'delivered').label('messages_delivered'),
            func.count().filter(Message.status == 'read').label('messages_read'),
            func.count().filter(Message.status == 'failed').label('messages_failed'),
            func.count().filter(Message.template_name.isnot(None)).label('template_messages'),
            func.count().filter(Message.template_name.is_(None)).label('freeform_messages'),
            func.count(func.distinct(Message.lead_id)).label('unique_conversations')
        ).filter(
            Message.created_at.between(date_start, date_end),
            Message.channel == 'whatsapp'
        ).first()

        messages_sent = message_stats.messages_sent or 0
        messages_delivered = message_stats.messages_delivered or 0

        metrics_data = {
            'date': target_date,
            'messages_sent': messages_sent,
            'messages_delivered': messages_delivered,
            'messages_read': message_stats.messages_read or 0,
            'messages_failed': message_stats.messages_failed or 0,
            'messages_received': message_stats.messages_received or 0,
            'delivery_rate': (messages_delivered / messages_sent) if messages_sent > 0 else 0,
            'read_rate': ((message_stats.messages_read or 0) / messages_delivered) if messages_delivered > 0 else 0,
            'response_rate': ((message_stats.messages_received or 0) / messages_sent) if messages_sent > 0 else 0,
            'template_messages': message_stats.template_messages or 0,
            'freeform_messages': message_stats.freeform_messages or 0,
            'unique_conversations': message_stats.unique_conversations or 0,
            'avg_first_response_time': 0,  # Would need more complex query
            'avg_delivery_time': 0  # Would need more complex query
        }

        # Upsert metrics record
        existing_metrics = db.query(WhatsAppMetrics).filter_by(
            date=target_date, hour=None
        ).first()

        if existing_metrics:
            for key, value in metrics_data.items():
                if hasattr(existing_metrics, key):
                    setattr(existing_metrics, key, value)
        else:
            existing_metrics = WhatsAppMetrics(**metrics_data)
            db.add(existing_metrics)

        db.commit()

        # Update checkpoint
        duration = int((datetime.utcnow() - start_time).total_seconds())
        checkpoint.update_progress(
            datetime.combine(target_date + timedelta(days=1), datetime.min.time()),
            messages_sent,
            duration,
            db
        )

        logger.info(f"Aggregated WhatsApp metrics for {target_date}: {messages_sent} messages")
        return {"status": "success", "date": target_date.isoformat(), "messages_processed": messages_sent}

    except Exception as e:
        logger.error(f"Error aggregating WhatsApp metrics: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


def aggregate_no_show_metrics(target_date: date = None) -> Dict[str, Any]:
    """Aggregate no-show metrics for a specific date."""
    db = SessionLocal()
    try:
        if not target_date:
            target_date = date.today() - timedelta(days=1)

        start_time = datetime.utcnow()

        # Get checkpoint
        checkpoint = MetricsCheckpoint.get_or_create_checkpoint(
            db, "no_shows", datetime.combine(target_date, datetime.min.time())
        )

        date_start = datetime.combine(target_date, datetime.min.time())
        date_end = datetime.combine(target_date, datetime.max.time())

        # Aggregate appointment data by professional
        professional_stats = db.query(
            Appointment.professional_id,
            Appointment.professional_name,
            Appointment.clinic_id,
            Appointment.clinic_name,
            Appointment.specialty,
            func.count().label('total_appointments'),
            func.count().filter(Appointment.status == 'scheduled').label('appointments_scheduled'),
            func.count().filter(Appointment.status == 'confirmed').label('appointments_confirmed'),
            func.count().filter(Appointment.status == 'completed').label('appointments_completed'),
            func.count().filter(Appointment.status == 'no_show').label('appointments_no_show'),
            func.count().filter(Appointment.status == 'cancelled').label('appointments_cancelled'),
            func.count().filter(Appointment.reminder_sent_24h == True).label('reminded_24h'),
            func.count().filter(Appointment.reminder_sent_3h == True).label('reminded_3h')
        ).filter(
            Appointment.scheduled_date.between(date_start, date_end)
        ).group_by(
            Appointment.professional_id,
            Appointment.professional_name,
            Appointment.clinic_id,
            Appointment.clinic_name,
            Appointment.specialty
        ).all()

        # Create metrics for each professional
        for stats in professional_stats:
            total = stats.total_appointments or 0
            no_shows = stats.appointments_no_show or 0

            metrics_data = {
                'date': target_date,
                'professional_id': stats.professional_id,
                'professional_name': stats.professional_name,
                'clinic_id': stats.clinic_id,
                'clinic_name': stats.clinic_name,
                'specialty': stats.specialty,
                'appointments_scheduled': stats.appointments_scheduled or 0,
                'appointments_confirmed': stats.appointments_confirmed or 0,
                'appointments_completed': stats.appointments_completed or 0,
                'appointments_no_show': no_shows,
                'appointments_cancelled': stats.appointments_cancelled or 0,
                'no_show_rate': (no_shows / total) if total > 0 else 0,
                'cancellation_rate': ((stats.appointments_cancelled or 0) / total) if total > 0 else 0,
                'reminded_24h': stats.reminded_24h or 0,
                'reminded_3h': stats.reminded_3h or 0,
                'risk_score': min(1.0, (no_shows / max(total, 1)) * 1.5)  # Simple risk calculation
            }

            # Upsert metrics record
            existing_metrics = db.query(NoShowMetrics).filter_by(
                date=target_date,
                professional_id=stats.professional_id
            ).first()

            if existing_metrics:
                for key, value in metrics_data.items():
                    if hasattr(existing_metrics, key):
                        setattr(existing_metrics, key, value)
            else:
                existing_metrics = NoShowMetrics(**metrics_data)
                db.add(existing_metrics)

        db.commit()

        # Update checkpoint
        duration = int((datetime.utcnow() - start_time).total_seconds())
        total_appointments = sum(stats.total_appointments or 0 for stats in professional_stats)
        checkpoint.update_progress(
            datetime.combine(target_date + timedelta(days=1), datetime.min.time()),
            total_appointments,
            duration,
            db
        )

        logger.info(f"Aggregated no-show metrics for {target_date}: {len(professional_stats)} professionals")
        return {"status": "success", "date": target_date.isoformat(), "professionals_processed": len(professional_stats)}

    except Exception as e:
        logger.error(f"Error aggregating no-show metrics: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


def refresh_materialized_views() -> Dict[str, Any]:
    """Refresh all materialized views."""
    db = SessionLocal()
    try:
        start_time = datetime.utcnow()

        # Refresh all materialized views using the stored function
        db.execute(text("SELECT refresh_all_materialized_views()"))
        db.commit()

        duration = int((datetime.utcnow() - start_time).total_seconds())

        logger.info(f"Refreshed all materialized views in {duration} seconds")
        return {"status": "success", "duration_seconds": duration}

    except Exception as e:
        logger.error(f"Error refreshing materialized views: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        db.close()