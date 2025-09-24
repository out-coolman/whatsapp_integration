"""
Scheduling API endpoints for Ninsaúde integration and appointment management.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from datetime import datetime, date, time
import logging

from app.core.database import get_db
from app.api.dependencies import (
    CommonQueryParams,
    log_api_request
)
from app.api.v1.auth import get_current_active_user
from app.models.lead import Lead
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.event import Event, EventType
from app.models.log import Log, LogLevel
from app.models.user import User
from app.services.ninsaude_service import NinsaudeService
from app.core.logging import audit_logger
# from app.jobs.scheduler import enqueue_appointment_reminders  # Temporarily disabled

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models for scheduling requests
class TimeSlot(BaseModel):
    """Available time slot."""
    start_time: datetime = Field(..., description="Slot start time")
    end_time: datetime = Field(..., description="Slot end time")
    available: bool = Field(..., description="Whether slot is available")
    professional_id: str = Field(..., description="Professional ID")
    professional_name: Optional[str] = Field(None, description="Professional name")
    specialty: Optional[str] = Field(None, description="Professional specialty")
    clinic_id: Optional[str] = Field(None, description="Clinic ID")
    clinic_name: Optional[str] = Field(None, description="Clinic name")
    estimated_cost: Optional[float] = Field(None, description="Estimated appointment cost")


class BookingRequest(BaseModel):
    """Request to book an appointment."""
    lead_id: str = Field(..., description="Lead ID")
    professional_id: str = Field(..., description="Professional ID")
    scheduled_date: datetime = Field(..., description="Appointment date and time")
    duration_minutes: Optional[int] = Field(30, description="Appointment duration")
    appointment_type: Optional[AppointmentType] = Field(AppointmentType.CONSULTATION, description="Appointment type")
    notes: Optional[str] = Field(None, description="Additional notes")

    @validator('scheduled_date')
    def validate_future_date(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('Appointment must be scheduled in the future')
        return v


class AppointmentUpdate(BaseModel):
    """Request to update an appointment."""
    status: Optional[AppointmentStatus] = Field(None, description="New appointment status")
    scheduled_date: Optional[datetime] = Field(None, description="New appointment date/time")
    notes: Optional[str] = Field(None, description="Updated notes")
    cancellation_reason: Optional[str] = Field(None, description="Reason for cancellation")


class AppointmentResponse(BaseModel):
    """Appointment response model."""
    id: str
    ninsaude_id: Optional[str]
    lead_id: str
    scheduled_date: datetime
    duration_minutes: int
    appointment_type: AppointmentType
    status: AppointmentStatus
    professional_id: str
    professional_name: Optional[str]
    clinic_id: str
    clinic_name: Optional[str]
    specialty: Optional[str]
    estimated_cost: Optional[float]
    notes: Optional[str]
    created_at: datetime


@router.get("/availability")
async def get_availability(
    professional_id: str = Query(..., description="Professional ID"),
    date: date = Query(..., description="Date to check availability"),
    appointment_type: Optional[str] = Query("consultation", description="Type of appointment"),
    duration_minutes: Optional[int] = Query(30, description="Appointment duration in minutes"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[TimeSlot]:
    """
    Get available time slots for a professional on a specific date.
    Integrates with Ninsaúde API to fetch real-time availability.
    """
    # Check permission
    if not current_user.has_permission("view_appointments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view availability"
        )

    try:
        # Log API request
        if request:
            log_api_request(request, db)

        # Initialize Ninsaúde service
        ninsaude_service = NinsaudeService()

        # Get availability from Ninsaúde
        availability_data = await ninsaude_service.get_availability(
            professional_id=professional_id,
            date=date,
            appointment_type=appointment_type,
            duration_minutes=duration_minutes
        )

        # Convert to our response format
        time_slots = []
        for slot_data in availability_data.get("available_slots", []):
            time_slot = TimeSlot(
                start_time=datetime.fromisoformat(slot_data["start_time"]),
                end_time=datetime.fromisoformat(slot_data["end_time"]),
                available=slot_data.get("available", True),
                professional_id=slot_data["professional_id"],
                professional_name=slot_data.get("professional_name"),
                specialty=slot_data.get("specialty"),
                clinic_id=slot_data.get("clinic_id"),
                clinic_name=slot_data.get("clinic_name"),
                estimated_cost=slot_data.get("estimated_cost")
            )
            time_slots.append(time_slot)

        # Log successful query
        log_entry = Log.create_api_call_log(
            source="scheduling_api",
            endpoint="/availability",
            method="GET",
            status_code=200,
            details={
                "professional_id": professional_id,
                "date": date.isoformat(),
                "slots_found": len(time_slots)
            }
        )
        db.add(log_entry)
        db.commit()

        return time_slots

    except Exception as e:
        logger.error(f"Error fetching availability: {e}", exc_info=True)

        # Log error
        error_log = Log.create_error_log(
            source="scheduling_api",
            message=f"Failed to fetch availability: {str(e)}",
            details={
                "professional_id": professional_id,
                "date": date.isoformat()
            }
        )
        db.add(error_log)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch availability"
        )


@router.post("/schedule")
async def book_appointment(
    booking: BookingRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> AppointmentResponse:
    """
    Book a new appointment for a lead.
    Creates appointment in both our system and Ninsaúde.
    """
    # Check permission
    if not current_user.has_permission("create_appointments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to book appointments"
        )

    try:
        # Verify lead exists
        lead = db.query(Lead).filter_by(id=booking.lead_id).first()
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )

        # Check for existing appointments at the same time
        existing_appointment = db.query(Appointment).filter(
            Appointment.scheduled_date == booking.scheduled_date,
            Appointment.professional_id == booking.professional_id,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
        ).first()

        if existing_appointment:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Time slot already booked"
            )

        # Initialize Ninsaúde service
        ninsaude_service = NinsaudeService()

        # Book appointment in Ninsaúde
        ninsaude_response = await ninsaude_service.book_appointment(
            professional_id=booking.professional_id,
            patient_data={
                "name": lead.full_name,
                "phone": lead.phone,
                "email": lead.email
            },
            scheduled_date=booking.scheduled_date,
            duration_minutes=booking.duration_minutes,
            appointment_type=booking.appointment_type.value,
            notes=booking.notes
        )

        # Create appointment record
        appointment = Appointment(
            ninsaude_id=ninsaude_response.get("appointment_id"),
            lead_id=booking.lead_id,
            scheduled_date=booking.scheduled_date,
            duration_minutes=booking.duration_minutes,
            appointment_type=booking.appointment_type,
            status=AppointmentStatus.SCHEDULED,
            professional_id=booking.professional_id,
            professional_name=ninsaude_response.get("professional_name"),
            clinic_id=ninsaude_response.get("clinic_id"),
            clinic_name=ninsaude_response.get("clinic_name"),
            specialty=ninsaude_response.get("specialty"),
            address=ninsaude_response.get("address"),
            phone=ninsaude_response.get("clinic_phone"),
            estimated_cost=ninsaude_response.get("estimated_cost"),
            notes=booking.notes
        )

        db.add(appointment)
        db.flush()  # Get the ID

        # Create event for appointment booking
        event = Event.create_lead_event(
            event_type=EventType.APPOINTMENT_BOOKED,
            lead_id=booking.lead_id,
            payload={
                "appointment_id": appointment.id,
                "ninsaude_id": appointment.ninsaude_id,
                "scheduled_date": booking.scheduled_date.isoformat(),
                "professional_id": booking.professional_id,
                "clinic_id": appointment.clinic_id
            }
        )
        event.appointment_id = appointment.id

        # Add orchestration actions
        event.add_triggered_action("send_booking_confirmation", {
            "appointment_id": appointment.id,
            "lead_id": booking.lead_id
        })
        event.add_triggered_action("schedule_reminders", {
            "appointment_id": appointment.id
        })

        db.add(event)

        # Log booking
        audit_logger.log_appointment_booked(booking.lead_id, appointment.id)

        log_entry = Log.create_business_log(
            source="scheduling_api",
            action="appointment_booked",
            message=f"Appointment booked for lead {booking.lead_id}",
            lead_id=booking.lead_id,
            appointment_id=appointment.id,
            details={
                "professional_id": booking.professional_id,
                "scheduled_date": booking.scheduled_date.isoformat(),
                "ninsaude_id": appointment.ninsaude_id
            }
        )
        db.add(log_entry)

        db.commit()

        # Schedule reminder jobs - temporarily disabled
        # background_tasks.add_task(
        #     enqueue_appointment_reminders,
        #     appointment_id=appointment.id
        # )

        return AppointmentResponse(
            id=appointment.id,
            ninsaude_id=appointment.ninsaude_id,
            lead_id=appointment.lead_id,
            scheduled_date=appointment.scheduled_date,
            duration_minutes=appointment.duration_minutes,
            appointment_type=appointment.appointment_type,
            status=appointment.status,
            professional_id=appointment.professional_id,
            professional_name=appointment.professional_name,
            clinic_id=appointment.clinic_id,
            clinic_name=appointment.clinic_name,
            specialty=appointment.specialty,
            estimated_cost=float(appointment.estimated_cost) if appointment.estimated_cost else None,
            notes=appointment.notes,
            created_at=appointment.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error booking appointment: {e}", exc_info=True)

        # Log error
        error_log = Log.create_error_log(
            source="scheduling_api",
            message=f"Failed to book appointment: {str(e)}",
            details={
                "lead_id": booking.lead_id,
                "professional_id": booking.professional_id,
                "scheduled_date": booking.scheduled_date.isoformat()
            },
            lead_id=booking.lead_id
        )
        db.add(error_log)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to book appointment"
        )


@router.get("/appointments")
async def list_appointments(
    lead_id: Optional[str] = None,
    professional_id: Optional[str] = None,
    clinic_id: Optional[str] = None,
    status: Optional[AppointmentStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    common: CommonQueryParams = Depends(),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    List appointments with filtering and pagination.
    """
    # Check permission
    if not current_user.has_permission("view_appointments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view appointments"
        )

    try:
        # Build query
        query = db.query(Appointment)

        if lead_id:
            query = query.filter(Appointment.lead_id == lead_id)
        if professional_id:
            query = query.filter(Appointment.professional_id == professional_id)
        if clinic_id:
            query = query.filter(Appointment.clinic_id == clinic_id)
        if status:
            query = query.filter(Appointment.status == status)
        if date_from:
            query = query.filter(Appointment.scheduled_date >= datetime.combine(date_from, time.min))
        if date_to:
            query = query.filter(Appointment.scheduled_date <= datetime.combine(date_to, time.max))

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        appointments = query.order_by(
            getattr(Appointment, common.order_by).desc() if common.order_direction == "desc"
            else getattr(Appointment, common.order_by)
        ).offset(common.offset).limit(common.limit).all()

        # Convert to response format
        appointment_responses = []
        for appointment in appointments:
            appointment_responses.append(AppointmentResponse(
                id=appointment.id,
                ninsaude_id=appointment.ninsaude_id,
                lead_id=appointment.lead_id,
                scheduled_date=appointment.scheduled_date,
                duration_minutes=appointment.duration_minutes,
                appointment_type=appointment.appointment_type,
                status=appointment.status,
                professional_id=appointment.professional_id,
                professional_name=appointment.professional_name,
                clinic_id=appointment.clinic_id,
                clinic_name=appointment.clinic_name,
                specialty=appointment.specialty,
                estimated_cost=float(appointment.estimated_cost) if appointment.estimated_cost else None,
                notes=appointment.notes,
                created_at=appointment.created_at
            ))

        return {
            "appointments": appointment_responses,
            "pagination": {
                "page": common.page,
                "limit": common.limit,
                "total": total,
                "pages": (total + common.limit - 1) // common.limit
            }
        }

    except Exception as e:
        logger.error(f"Error listing appointments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list appointments"
        )


@router.get("/appointments/{appointment_id}")
async def get_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> AppointmentResponse:
    """Get a specific appointment by ID."""
    # Check permission
    if not current_user.has_permission("view_appointments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view appointments"
        )

    appointment = db.query(Appointment).filter_by(id=appointment_id).first()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    return AppointmentResponse(
        id=appointment.id,
        ninsaude_id=appointment.ninsaude_id,
        lead_id=appointment.lead_id,
        scheduled_date=appointment.scheduled_date,
        duration_minutes=appointment.duration_minutes,
        appointment_type=appointment.appointment_type,
        status=appointment.status,
        professional_id=appointment.professional_id,
        professional_name=appointment.professional_name,
        clinic_id=appointment.clinic_id,
        clinic_name=appointment.clinic_name,
        specialty=appointment.specialty,
        estimated_cost=float(appointment.estimated_cost) if appointment.estimated_cost else None,
        notes=appointment.notes,
        created_at=appointment.created_at
    )


@router.put("/appointments/{appointment_id}")
async def update_appointment(
    appointment_id: str,
    update: AppointmentUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> AppointmentResponse:
    """Update an appointment."""
    # Check permission
    if not current_user.has_permission("edit_appointments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update appointments"
        )

    appointment = db.query(Appointment).filter_by(id=appointment_id).first()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    try:
        # Initialize Ninsaúde service for external updates
        ninsaude_service = NinsaudeService()

        # Update status
        if update.status:
            old_status = appointment.status
            if update.status == AppointmentStatus.CONFIRMED:
                appointment.confirm()
                # Sync with Ninsaúde
                await ninsaude_service.confirm_appointment(appointment.ninsaude_id)
            elif update.status == AppointmentStatus.COMPLETED:
                appointment.mark_completed()
                await ninsaude_service.complete_appointment(appointment.ninsaude_id)
            elif update.status == AppointmentStatus.NO_SHOW:
                appointment.mark_no_show()
                await ninsaude_service.mark_no_show(appointment.ninsaude_id)
            elif update.status == AppointmentStatus.CANCELLED:
                appointment.cancel(update.cancellation_reason)
                await ninsaude_service.cancel_appointment(appointment.ninsaude_id, update.cancellation_reason)

            # Create event for status change
            if old_status != update.status:
                event_type_mapping = {
                    AppointmentStatus.CONFIRMED: EventType.APPOINTMENT_CONFIRMED,
                    AppointmentStatus.COMPLETED: EventType.APPOINTMENT_COMPLETED,
                    AppointmentStatus.NO_SHOW: EventType.APPOINTMENT_NO_SHOW,
                    AppointmentStatus.CANCELLED: EventType.APPOINTMENT_CANCELLED
                }

                if update.status in event_type_mapping:
                    event = Event.create_lead_event(
                        event_type=event_type_mapping[update.status],
                        lead_id=appointment.lead_id,
                        payload={
                            "appointment_id": appointment.id,
                            "old_status": old_status.value,
                            "new_status": update.status.value,
                            "reason": update.cancellation_reason
                        }
                    )
                    event.appointment_id = appointment.id

                    # Add orchestration actions
                    if update.status == AppointmentStatus.NO_SHOW:
                        event.add_triggered_action("handle_no_show", {
                            "appointment_id": appointment.id,
                            "lead_id": appointment.lead_id
                        })

                    db.add(event)

        # Update scheduled date (reschedule)
        if update.scheduled_date and update.scheduled_date != appointment.scheduled_date:
            old_date = appointment.scheduled_date
            appointment.reschedule(update.scheduled_date)

            # Sync with Ninsaúde
            await ninsaude_service.reschedule_appointment(
                appointment.ninsaude_id,
                update.scheduled_date
            )

            # Reschedule reminders - temporarily disabled
            # background_tasks.add_task(
            #     enqueue_appointment_reminders,
            #     appointment_id=appointment.id
            # )

        # Update notes
        if update.notes is not None:
            appointment.notes = update.notes

        db.commit()

        return AppointmentResponse(
            id=appointment.id,
            ninsaude_id=appointment.ninsaude_id,
            lead_id=appointment.lead_id,
            scheduled_date=appointment.scheduled_date,
            duration_minutes=appointment.duration_minutes,
            appointment_type=appointment.appointment_type,
            status=appointment.status,
            professional_id=appointment.professional_id,
            professional_name=appointment.professional_name,
            clinic_id=appointment.clinic_id,
            clinic_name=appointment.clinic_name,
            specialty=appointment.specialty,
            estimated_cost=float(appointment.estimated_cost) if appointment.estimated_cost else None,
            notes=appointment.notes,
            created_at=appointment.created_at
        )

    except Exception as e:
        logger.error(f"Error updating appointment: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update appointment"
        )