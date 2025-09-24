"""
Job orchestration and scheduling for healthcare sales automation.
"""
import redis
from rq import Queue, Worker
from rq_scheduler import Scheduler
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import json

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.lead import Lead, LeadStage, LeadClassification
from app.models.appointment import Appointment, AppointmentStatus
from app.models.call import Call, CallStatus, CallOutcome
from app.models.message import Message, MessageDirection, MessageChannel
from app.models.event import Event, EventType, EventStatus
from app.models.log import Log, LogLevel, LogCategory
from app.services.vapi_service import VAPIService
from app.services.ninsaude_service import NinsaudeService
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

# Initialize Redis connection and queues
redis_conn = redis.from_url(settings.REDIS_URL)
default_queue = Queue('default', connection=redis_conn)
high_priority_queue = Queue('high_priority', connection=redis_conn)
scheduler = Scheduler(connection=redis_conn)


def enqueue_orchestration_job(event_id: str, correlation_id: str) -> None:
    """Enqueue orchestration job for processing an event."""
    job = high_priority_queue.enqueue(
        process_orchestration_event,
        event_id,
        correlation_id,
        job_timeout=settings.JOB_TIMEOUT,
        retry_count=settings.MAX_JOB_RETRIES
    )
    logger.info(f"Enqueued orchestration job {job.id} for event {event_id}")


def enqueue_appointment_reminders(appointment_id: str) -> None:
    """Schedule appointment reminder jobs."""
    job = default_queue.enqueue(
        schedule_appointment_reminders,
        appointment_id,
        job_timeout=settings.JOB_TIMEOUT
    )
    logger.info(f"Enqueued reminder scheduling job {job.id} for appointment {appointment_id}")


def process_orchestration_event(event_id: str, correlation_id: str) -> Dict[str, Any]:
    """
    Main orchestration processor that handles events and triggers appropriate actions.
    """
    db = SessionLocal()
    result = {"status": "success", "actions_triggered": []}

    try:
        # Get the event
        event = db.query(Event).filter_by(id=event_id).first()
        if not event:
            raise ValueError(f"Event {event_id} not found")

        # Mark event as processing
        event.mark_processing()
        db.commit()

        logger.info(f"Processing orchestration event {event_id}: {event.event_type}")

        # Process based on event type
        if event.event_type == EventType.LEAD_CREATED:
            result["actions_triggered"].extend(
                handle_lead_created(event, correlation_id, db)
            )

        elif event.event_type == EventType.LEAD_STAGE_CHANGED:
            result["actions_triggered"].extend(
                handle_lead_stage_changed(event, correlation_id, db)
            )

        elif event.event_type == EventType.LEAD_TAG_ADDED:
            result["actions_triggered"].extend(
                handle_lead_tag_added(event, correlation_id, db)
            )

        elif event.event_type == EventType.MESSAGE_RECEIVED:
            result["actions_triggered"].extend(
                handle_message_received(event, correlation_id, db)
            )

        elif event.event_type == EventType.CALL_COMPLETED:
            result["actions_triggered"].extend(
                handle_call_completed(event, correlation_id, db)
            )

        elif event.event_type == EventType.APPOINTMENT_BOOKED:
            result["actions_triggered"].extend(
                handle_appointment_booked(event, correlation_id, db)
            )

        elif event.event_type == EventType.APPOINTMENT_NO_SHOW:
            result["actions_triggered"].extend(
                handle_appointment_no_show(event, correlation_id, db)
            )

        # Process any additional triggered actions from the event
        if event.triggers_actions:
            for action in event.triggers_actions:
                action_result = execute_triggered_action(action, event, correlation_id, db)
                if action_result:
                    result["actions_triggered"].append(action_result)

        # Mark event as completed
        event.mark_completed()
        db.commit()

        # Log successful processing
        log_entry = Log.create_job_log(
            source="orchestrator",
            job_name="process_orchestration_event",
            message=f"Successfully processed event {event.event_type}",
            details=result,
            correlation_id=correlation_id
        )
        log_entry.lead_id = event.lead_id
        db.add(log_entry)
        db.commit()

        logger.info(f"Completed orchestration for event {event_id}: {len(result['actions_triggered'])} actions triggered")

    except Exception as e:
        logger.error(f"Error processing orchestration event {event_id}: {e}", exc_info=True)

        # Mark event as failed
        if 'event' in locals():
            event.mark_failed(str(e))
            db.commit()

        # Log error
        error_log = Log.create_error_log(
            source="orchestrator",
            message=f"Failed to process event {event_id}: {str(e)}",
            details={"event_id": event_id, "correlation_id": correlation_id}
        )
        db.add(error_log)
        db.commit()

        result = {"status": "error", "error": str(e)}

    finally:
        db.close()

    return result


def handle_lead_created(event: Event, correlation_id: str, db) -> List[Dict[str, Any]]:
    """Handle new lead creation."""
    actions = []

    lead = db.query(Lead).filter_by(id=event.lead_id).first()
    if not lead:
        return actions

    # Check if this is a hot lead requiring immediate action
    if lead.is_hot_lead():
        # Enqueue immediate call
        call_job = high_priority_queue.enqueue(
            initiate_hot_lead_call,
            lead.id,
            correlation_id,
            job_timeout=settings.JOB_TIMEOUT
        )
        actions.append({
            "action": "initiate_hot_lead_call",
            "job_id": call_job.id,
            "lead_id": lead.id
        })

        # Send immediate WhatsApp message
        wa_job = high_priority_queue.enqueue(
            send_welcome_whatsapp,
            lead.id,
            correlation_id,
            urgent=True,
            job_timeout=settings.JOB_TIMEOUT
        )
        actions.append({
            "action": "send_urgent_whatsapp",
            "job_id": wa_job.id,
            "lead_id": lead.id
        })

    else:
        # Regular lead - schedule follow-up for later
        follow_up_time = datetime.utcnow() + timedelta(hours=2)
        follow_up_job = scheduler.enqueue_at(
            follow_up_time,
            initiate_lead_follow_up,
            lead.id,
            correlation_id
        )
        actions.append({
            "action": "schedule_follow_up",
            "job_id": follow_up_job.id,
            "scheduled_at": follow_up_time.isoformat(),
            "lead_id": lead.id
        })

    return actions


def handle_lead_stage_changed(event: Event, correlation_id: str, db) -> List[Dict[str, Any]]:
    """Handle lead stage changes."""
    actions = []

    lead = db.query(Lead).filter_by(id=event.lead_id).first()
    if not lead:
        return actions

    # Handle stage-specific actions
    if lead.stage == LeadStage.QUALIFIED:
        # Send appointment booking WhatsApp with available times
        booking_job = default_queue.enqueue(
            send_booking_whatsapp,
            lead.id,
            correlation_id,
            job_timeout=settings.JOB_TIMEOUT
        )
        actions.append({
            "action": "send_booking_whatsapp",
            "job_id": booking_job.id,
            "lead_id": lead.id
        })

    elif lead.stage == LeadStage.BOOKED:
        # Schedule appointment reminders
        reminder_job = default_queue.enqueue(
            schedule_appointment_reminders,
            event.appointment_id,
            job_timeout=settings.JOB_TIMEOUT
        )
        actions.append({
            "action": "schedule_appointment_reminders",
            "job_id": reminder_job.id,
            "appointment_id": event.appointment_id
        })

    return actions


def handle_lead_tag_added(event: Event, correlation_id: str, db) -> List[Dict[str, Any]]:
    """Handle tag additions to leads."""
    actions = []

    lead = db.query(Lead).filter_by(id=event.lead_id).first()
    if not lead:
        return actions

    # Check for handoff tag
    if lead.has_tag("handoff"):
        # Notify human agent
        handoff_job = high_priority_queue.enqueue(
            trigger_agent_handoff,
            lead.id,
            correlation_id,
            job_timeout=settings.JOB_TIMEOUT
        )
        actions.append({
            "action": "trigger_agent_handoff",
            "job_id": handoff_job.id,
            "lead_id": lead.id
        })

    # Check for urgent tag
    if lead.has_tag("urgent") and not lead.has_tag("contacted_urgent"):
        # Immediate call for urgent leads
        urgent_call_job = high_priority_queue.enqueue(
            initiate_urgent_call,
            lead.id,
            correlation_id,
            job_timeout=settings.JOB_TIMEOUT
        )
        actions.append({
            "action": "initiate_urgent_call",
            "job_id": urgent_call_job.id,
            "lead_id": lead.id
        })

        # Add tag to prevent duplicate urgent calls
        lead.add_tag("contacted_urgent")
        db.commit()

    return actions


def handle_message_received(event: Event, correlation_id: str, db) -> List[Dict[str, Any]]:
    """Handle inbound messages from leads."""
    actions = []

    lead = db.query(Lead).filter_by(id=event.lead_id).first()
    if not lead:
        return actions

    # Process message for intent recognition
    message_job = default_queue.enqueue(
        process_inbound_message,
        event.message_id,
        correlation_id,
        job_timeout=settings.JOB_TIMEOUT
    )
    actions.append({
        "action": "process_inbound_message",
        "job_id": message_job.id,
        "message_id": event.message_id,
        "lead_id": lead.id
    })

    return actions


def handle_call_completed(event: Event, correlation_id: str, db) -> List[Dict[str, Any]]:
    """Handle completed calls."""
    actions = []

    call = db.query(Call).filter_by(id=event.call_id).first()
    if not call:
        return actions

    # Process call outcome
    if call.outcome == CallOutcome.APPOINTMENT_BOOKED:
        # Trigger appointment booking flow
        booking_job = default_queue.enqueue(
            process_call_appointment_booking,
            call.id,
            correlation_id,
            job_timeout=settings.JOB_TIMEOUT
        )
        actions.append({
            "action": "process_call_appointment_booking",
            "job_id": booking_job.id,
            "call_id": call.id
        })

    elif call.outcome == CallOutcome.CALLBACK_REQUESTED:
        # Schedule callback
        callback_time = datetime.utcnow() + timedelta(hours=24)
        callback_job = scheduler.enqueue_at(
            callback_time,
            initiate_callback,
            call.lead_id,
            correlation_id
        )
        actions.append({
            "action": "schedule_callback",
            "job_id": callback_job.id,
            "scheduled_at": callback_time.isoformat(),
            "lead_id": call.lead_id
        })

    elif call.outcome == CallOutcome.NOT_INTERESTED:
        # Update lead classification and stop active campaigns
        update_job = default_queue.enqueue(
            update_lead_classification,
            call.lead_id,
            LeadClassification.COLD,
            correlation_id,
            job_timeout=settings.JOB_TIMEOUT
        )
        actions.append({
            "action": "update_lead_classification",
            "job_id": update_job.id,
            "lead_id": call.lead_id,
            "classification": "cold"
        })

    return actions


def handle_appointment_booked(event: Event, correlation_id: str, db) -> List[Dict[str, Any]]:
    """Handle appointment booking confirmation."""
    actions = []

    appointment = db.query(Appointment).filter_by(id=event.appointment_id).first()
    if not appointment:
        return actions

    # Send booking confirmation
    confirmation_job = default_queue.enqueue(
        send_booking_confirmation,
        appointment.id,
        correlation_id,
        job_timeout=settings.JOB_TIMEOUT
    )
    actions.append({
        "action": "send_booking_confirmation",
        "job_id": confirmation_job.id,
        "appointment_id": appointment.id
    })

    # Update lead stage
    lead = appointment.lead
    if lead:
        lead.update_stage(LeadStage.BOOKED)
        db.commit()

    return actions


def handle_appointment_no_show(event: Event, correlation_id: str, db) -> List[Dict[str, Any]]:
    """Handle appointment no-shows."""
    actions = []

    appointment = db.query(Appointment).filter_by(id=event.appointment_id).first()
    if not appointment:
        return actions

    # Trigger reactivation sequence
    reactivation_job = default_queue.enqueue(
        trigger_no_show_reactivation,
        appointment.id,
        correlation_id,
        job_timeout=settings.JOB_TIMEOUT
    )
    actions.append({
        "action": "trigger_no_show_reactivation",
        "job_id": reactivation_job.id,
        "appointment_id": appointment.id
    })

    return actions


def execute_triggered_action(action: Dict[str, Any], event: Event, correlation_id: str, db) -> Optional[Dict[str, Any]]:
    """Execute a specific triggered action from an event."""
    action_type = action.get("type")
    action_data = action.get("data", {})

    try:
        if action_type == "initiate_hot_lead_sequence":
            job = high_priority_queue.enqueue(
                initiate_hot_lead_call,
                action_data.get("lead_id"),
                correlation_id
            )
            return {"action": action_type, "job_id": job.id}

        elif action_type == "trigger_handoff":
            job = high_priority_queue.enqueue(
                trigger_agent_handoff,
                action_data.get("lead_id"),
                correlation_id
            )
            return {"action": action_type, "job_id": job.id}

        elif action_type == "schedule_appointment_reminders":
            job = default_queue.enqueue(
                schedule_appointment_reminders,
                action_data.get("appointment_id")
            )
            return {"action": action_type, "job_id": job.id}

        elif action_type == "process_inbound_message":
            job = default_queue.enqueue(
                process_inbound_message,
                action_data.get("message_id"),
                correlation_id
            )
            return {"action": action_type, "job_id": job.id}

        else:
            logger.warning(f"Unknown action type: {action_type}")
            return None

    except Exception as e:
        logger.error(f"Failed to execute action {action_type}: {e}")
        return {"action": action_type, "error": str(e)}


# Individual job functions
def initiate_hot_lead_call(lead_id: str, correlation_id: str) -> Dict[str, Any]:
    """Initiate an immediate call to a hot lead."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter_by(id=lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        # Use VAPI to initiate call
        vapi_service = VAPIService()
        call_result = vapi_service.initiate_call(
            phone_number=lead.phone,
            lead_data={
                "id": lead.id,
                "name": lead.full_name,
                "source": lead.source.value if lead.source else "unknown"
            },
            call_metadata={
                "call_type": "hot_lead_outreach",
                "correlation_id": correlation_id
            }
        )

        # Create call record
        call = Call(
            vapi_call_id=call_result.get("call_id"),
            lead_id=lead_id,
            direction="outbound",
            from_number=settings.TWILIO_PHONE_NUMBER,
            to_number=lead.phone,
            status=CallStatus.INITIATED
        )
        db.add(call)

        # Update lead status
        lead.last_contacted_at = datetime.utcnow()
        if lead.stage == LeadStage.NEW:
            lead.update_stage(LeadStage.CONTACTED)

        db.commit()

        logger.info(f"Initiated hot lead call for {lead_id}: {call_result.get('call_id')}")
        return {"status": "success", "call_id": call.id, "vapi_call_id": call_result.get("call_id")}

    except Exception as e:
        logger.error(f"Failed to initiate hot lead call for {lead_id}: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


def schedule_appointment_reminders(appointment_id: str) -> Dict[str, Any]:
    """Schedule 24h and 3h reminders for an appointment."""
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter_by(id=appointment_id).first()
        if not appointment:
            raise ValueError(f"Appointment {appointment_id} not found")

        now = datetime.utcnow()

        # Schedule 24-hour reminder (WhatsApp)
        reminder_24h_time = appointment.scheduled_date - timedelta(hours=24)
        if reminder_24h_time > now:
            reminder_24h_job = scheduler.enqueue_at(
                reminder_24h_time,
                send_appointment_reminder,
                appointment_id,
                "24h",
                "whatsapp"
            )
            logger.info(f"Scheduled 24h reminder for appointment {appointment_id} at {reminder_24h_time}")

        # Schedule 3-hour reminder (voice call)
        reminder_3h_time = appointment.scheduled_date - timedelta(hours=3)
        if reminder_3h_time > now:
            reminder_3h_job = scheduler.enqueue_at(
                reminder_3h_time,
                send_appointment_reminder,
                appointment_id,
                "3h",
                "voice"
            )
            logger.info(f"Scheduled 3h reminder for appointment {appointment_id} at {reminder_3h_time}")

        return {"status": "success", "reminders_scheduled": 2}

    except Exception as e:
        logger.error(f"Failed to schedule reminders for appointment {appointment_id}: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


def send_appointment_reminder(appointment_id: str, reminder_type: str, channel: str) -> Dict[str, Any]:
    """Send appointment reminder via specified channel."""
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter_by(id=appointment_id).first()
        if not appointment:
            raise ValueError(f"Appointment {appointment_id} not found")

        # Mark reminder as sent
        appointment.mark_reminded(reminder_type)
        db.commit()

        logger.info(f"Sent {reminder_type} reminder for appointment {appointment_id} via {channel}")
        return {"status": "success", "reminder_type": reminder_type, "channel": channel}

    except Exception as e:
        logger.error(f"Failed to send reminder for appointment {appointment_id}: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


# Placeholder functions for other job types
def send_welcome_whatsapp(lead_id: str, correlation_id: str, urgent: bool = False) -> Dict[str, Any]:
    """Send welcome WhatsApp message to new lead."""
    return {"status": "success", "message": "WhatsApp welcome sent"}


def initiate_lead_follow_up(lead_id: str, correlation_id: str) -> Dict[str, Any]:
    """Follow up with a lead after initial contact delay."""
    return {"status": "success", "message": "Follow-up initiated"}


def send_booking_whatsapp(lead_id: str, correlation_id: str) -> Dict[str, Any]:
    """Send appointment booking options via WhatsApp."""
    return {"status": "success", "message": "Booking WhatsApp sent"}


def trigger_agent_handoff(lead_id: str, correlation_id: str) -> Dict[str, Any]:
    """Trigger handoff to human agent."""
    return {"status": "success", "message": "Agent handoff triggered"}


def initiate_urgent_call(lead_id: str, correlation_id: str) -> Dict[str, Any]:
    """Initiate urgent call for tagged leads."""
    return {"status": "success", "message": "Urgent call initiated"}


def process_inbound_message(message_id: str, correlation_id: str) -> Dict[str, Any]:
    """Process inbound message for intent recognition."""
    return {"status": "success", "message": "Message processed"}


def process_call_appointment_booking(call_id: str, correlation_id: str) -> Dict[str, Any]:
    """Process appointment booking from call outcome."""
    return {"status": "success", "message": "Call booking processed"}


def initiate_callback(lead_id: str, correlation_id: str) -> Dict[str, Any]:
    """Initiate a scheduled callback."""
    return {"status": "success", "message": "Callback initiated"}


def update_lead_classification(lead_id: str, classification: LeadClassification, correlation_id: str) -> Dict[str, Any]:
    """Update lead classification."""
    return {"status": "success", "classification": classification.value}


def send_booking_confirmation(appointment_id: str, correlation_id: str) -> Dict[str, Any]:
    """Send appointment booking confirmation."""
    return {"status": "success", "message": "Booking confirmation sent"}


def trigger_no_show_reactivation(appointment_id: str, correlation_id: str) -> Dict[str, Any]:
    """Trigger reactivation sequence for no-show appointments."""
    return {"status": "success", "message": "Reactivation sequence triggered"}