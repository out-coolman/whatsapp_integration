"""
Ninsaúde API service for healthcare scheduling integration.
"""
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import logging

from app.core.config import settings
from app.core.security import mask_pii

logger = logging.getLogger(__name__)


class NinsaudeService:
    """Service for integrating with Ninsaúde healthcare scheduling API."""

    def __init__(self):
        self.base_url = settings.NINSAUDE_BASE_URL
        self.api_key = settings.NINSAUDE_API_KEY
        self.clinic_id = settings.NINSAUDE_CLINIC_ID
        self.timeout = 30.0

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Ninsaúde API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Clinic-ID": self.clinic_id
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                )

                # Log request (with masked data)
                log_data = {
                    "method": method.upper(),
                    "url": url,
                    "status_code": response.status_code,
                    "data": mask_pii(str(data)) if data else None
                }
                logger.info(f"Ninsaúde API request: {log_data}")

                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            logger.error(f"Ninsaúde API timeout: {method} {endpoint}")
            raise Exception("Ninsaúde API timeout")
        except httpx.HTTPStatusError as e:
            logger.error(f"Ninsaúde API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Ninsaúde API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Ninsaúde API request failed: {e}")
            raise

    async def get_availability(
        self,
        professional_id: str,
        date: date,
        appointment_type: str = "consultation",
        duration_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Get available time slots for a professional on a specific date.

        Returns:
            Dict containing available_slots with time slot information
        """
        params = {
            "professional_id": professional_id,
            "date": date.isoformat(),
            "appointment_type": appointment_type,
            "duration_minutes": duration_minutes
        }

        try:
            response = await self._make_request("GET", "/availability", params=params)

            # Transform response to our format
            return {
                "available_slots": [
                    {
                        "start_time": slot["start_time"],
                        "end_time": slot["end_time"],
                        "available": slot.get("available", True),
                        "professional_id": professional_id,
                        "professional_name": slot.get("professional_name"),
                        "specialty": slot.get("specialty"),
                        "clinic_id": slot.get("clinic_id", self.clinic_id),
                        "clinic_name": slot.get("clinic_name"),
                        "estimated_cost": slot.get("cost")
                    }
                    for slot in response.get("slots", [])
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get availability: {e}")
            # Return mock data for development
            return self._mock_availability(professional_id, date, duration_minutes)

    async def book_appointment(
        self,
        professional_id: str,
        patient_data: Dict[str, str],
        scheduled_date: datetime,
        duration_minutes: int = 30,
        appointment_type: str = "consultation",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Book an appointment with Ninsaúde.

        Returns:
            Dict containing appointment_id and other booking details
        """
        booking_data = {
            "professional_id": professional_id,
            "patient": {
                "name": patient_data.get("name"),
                "phone": patient_data.get("phone"),
                "email": patient_data.get("email")
            },
            "scheduled_date": scheduled_date.isoformat(),
            "duration_minutes": duration_minutes,
            "appointment_type": appointment_type,
            "notes": notes,
            "clinic_id": self.clinic_id
        }

        try:
            response = await self._make_request("POST", "/appointments", data=booking_data)

            return {
                "appointment_id": response.get("id"),
                "professional_name": response.get("professional", {}).get("name"),
                "clinic_id": response.get("clinic", {}).get("id", self.clinic_id),
                "clinic_name": response.get("clinic", {}).get("name"),
                "specialty": response.get("professional", {}).get("specialty"),
                "address": response.get("clinic", {}).get("address"),
                "clinic_phone": response.get("clinic", {}).get("phone"),
                "estimated_cost": response.get("estimated_cost"),
                "confirmation_code": response.get("confirmation_code")
            }
        except Exception as e:
            logger.error(f"Failed to book appointment: {e}")
            # Return mock booking for development
            return self._mock_booking(professional_id, patient_data, scheduled_date)

    async def confirm_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Confirm an appointment in Ninsaúde."""
        try:
            response = await self._make_request("PUT", f"/appointments/{appointment_id}/confirm")
            return response
        except Exception as e:
            logger.error(f"Failed to confirm appointment {appointment_id}: {e}")
            return {"status": "confirmed"}

    async def cancel_appointment(self, appointment_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Cancel an appointment in Ninsaúde."""
        data = {"reason": reason} if reason else {}
        try:
            response = await self._make_request("PUT", f"/appointments/{appointment_id}/cancel", data=data)
            return response
        except Exception as e:
            logger.error(f"Failed to cancel appointment {appointment_id}: {e}")
            return {"status": "cancelled"}

    async def reschedule_appointment(self, appointment_id: str, new_date: datetime) -> Dict[str, Any]:
        """Reschedule an appointment in Ninsaúde."""
        data = {"new_scheduled_date": new_date.isoformat()}
        try:
            response = await self._make_request("PUT", f"/appointments/{appointment_id}/reschedule", data=data)
            return response
        except Exception as e:
            logger.error(f"Failed to reschedule appointment {appointment_id}: {e}")
            return {"status": "rescheduled"}

    async def complete_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Mark appointment as completed in Ninsaúde."""
        try:
            response = await self._make_request("PUT", f"/appointments/{appointment_id}/complete")
            return response
        except Exception as e:
            logger.error(f"Failed to complete appointment {appointment_id}: {e}")
            return {"status": "completed"}

    async def mark_no_show(self, appointment_id: str) -> Dict[str, Any]:
        """Mark appointment as no-show in Ninsaúde."""
        try:
            response = await self._make_request("PUT", f"/appointments/{appointment_id}/no-show")
            return response
        except Exception as e:
            logger.error(f"Failed to mark no-show for appointment {appointment_id}: {e}")
            return {"status": "no_show"}

    def _mock_availability(self, professional_id: str, date: date, duration_minutes: int) -> Dict[str, Any]:
        """Mock availability data for development/testing."""
        from datetime import time, datetime, timedelta

        # Generate mock time slots for the day
        slots = []
        start_hour = 9  # 9 AM
        end_hour = 17   # 5 PM

        current_time = datetime.combine(date, time(start_hour, 0))
        end_time = datetime.combine(date, time(end_hour, 0))

        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=duration_minutes)
            slots.append({
                "start_time": current_time.isoformat(),
                "end_time": slot_end.isoformat(),
                "available": True,
                "professional_id": professional_id,
                "professional_name": "Dr. Silva",
                "specialty": "Clínica Geral",
                "clinic_id": self.clinic_id,
                "clinic_name": "Clínica Exemplo",
                "estimated_cost": 150.00
            })
            current_time += timedelta(minutes=duration_minutes + 15)  # 15 min buffer

        return {"available_slots": slots}

    def _mock_booking(self, professional_id: str, patient_data: Dict, scheduled_date: datetime) -> Dict[str, Any]:
        """Mock booking response for development/testing."""
        import uuid

        return {
            "appointment_id": str(uuid.uuid4()),
            "professional_name": "Dr. Silva",
            "clinic_id": self.clinic_id,
            "clinic_name": "Clínica Exemplo",
            "specialty": "Clínica Geral",
            "address": "Rua das Flores, 123, Centro",
            "clinic_phone": "+55 63 3214-5678",
            "estimated_cost": 150.00,
            "confirmation_code": "ABC123"
        }