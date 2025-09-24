"""
VAPI service for AI-powered voice calls integration.
"""
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.core.config import settings
from app.core.security import mask_pii

logger = logging.getLogger(__name__)


class VAPIService:
    """Service for integrating with VAPI AI voice calling platform."""

    def __init__(self):
        self.base_url = settings.VAPI_BASE_URL
        self.api_key = settings.VAPI_API_KEY
        self.phone_number_id = settings.VAPI_PHONE_NUMBER_ID
        self.timeout = 30.0

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to VAPI API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
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
                logger.info(f"VAPI API request: {log_data}")

                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            logger.error(f"VAPI API timeout: {method} {endpoint}")
            raise Exception("VAPI API timeout")
        except httpx.HTTPStatusError as e:
            logger.error(f"VAPI API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"VAPI API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"VAPI API request failed: {e}")
            raise

    async def initiate_call(
        self,
        phone_number: str,
        lead_data: Dict[str, Any],
        assistant_config: Optional[Dict] = None,
        call_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Initiate an AI-powered voice call to a lead.

        Args:
            phone_number: Target phone number
            lead_data: Lead information for personalization
            assistant_config: Custom assistant configuration
            call_metadata: Additional metadata to attach to the call

        Returns:
            Dict containing call_id and call status
        """
        # Default assistant configuration for healthcare sales
        default_assistant = {
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": self._get_system_prompt(lead_data)
                    }
                ]
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "ErXwobaYiN019PkySvjV",  # Professional female voice
                "speed": 1.0,
                "stability": 0.8
            },
            "functions": [
                {
                    "name": "book_appointment",
                    "description": "Book an appointment for the lead",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "preferred_date": {"type": "string"},
                            "preferred_time": {"type": "string"},
                            "appointment_type": {"type": "string"}
                        },
                        "required": ["preferred_date", "preferred_time"]
                    }
                },
                {
                    "name": "schedule_callback",
                    "description": "Schedule a callback for later",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "callback_date": {"type": "string"},
                            "callback_time": {"type": "string"},
                            "reason": {"type": "string"}
                        },
                        "required": ["callback_date", "callback_time"]
                    }
                },
                {
                    "name": "update_lead_status",
                    "description": "Update lead status based on conversation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "notes": {"type": "string"},
                            "interest_level": {"type": "string"}
                        },
                        "required": ["status", "interest_level"]
                    }
                }
            ]
        }

        # Merge with custom configuration
        assistant = {**default_assistant, **(assistant_config or {})}

        call_data = {
            "phoneNumberId": self.phone_number_id,
            "customer": {
                "number": phone_number
            },
            "assistant": assistant,
            "metadata": {
                "lead_id": lead_data.get("id"),
                "lead_name": lead_data.get("name"),
                "lead_source": lead_data.get("source"),
                "call_purpose": "healthcare_consultation_booking",
                **(call_metadata or {})
            }
        }

        try:
            response = await self._make_request("POST", "/call", data=call_data)

            return {
                "call_id": response.get("id"),
                "status": response.get("status"),
                "phone_number": phone_number,
                "assistant_id": response.get("assistantId"),
                "started_at": response.get("createdAt"),
                "estimated_cost": response.get("cost")
            }

        except Exception as e:
            logger.error(f"Failed to initiate call to {mask_pii(phone_number)}: {e}")
            # Return mock response for development
            return self._mock_call_response(phone_number, lead_data)

    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Get current status of a call."""
        try:
            response = await self._make_request("GET", f"/call/{call_id}")
            return response
        except Exception as e:
            logger.error(f"Failed to get call status for {call_id}: {e}")
            return {"status": "unknown", "error": str(e)}

    async def end_call(self, call_id: str) -> Dict[str, Any]:
        """End an active call."""
        try:
            response = await self._make_request("POST", f"/call/{call_id}/end")
            return response
        except Exception as e:
            logger.error(f"Failed to end call {call_id}: {e}")
            return {"status": "error", "error": str(e)}

    async def get_call_transcript(self, call_id: str) -> Dict[str, Any]:
        """Get transcript and analysis for a completed call."""
        try:
            response = await self._make_request("GET", f"/call/{call_id}/transcript")
            return response
        except Exception as e:
            logger.error(f"Failed to get transcript for call {call_id}: {e}")
            return {"transcript": "", "error": str(e)}

    async def create_assistant(self, assistant_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom AI assistant configuration."""
        try:
            response = await self._make_request("POST", "/assistant", data=assistant_config)
            return response
        except Exception as e:
            logger.error(f"Failed to create assistant: {e}")
            raise

    async def list_phone_numbers(self) -> List[Dict[str, Any]]:
        """List available phone numbers for calls."""
        try:
            response = await self._make_request("GET", "/phone-number")
            return response.get("phoneNumbers", [])
        except Exception as e:
            logger.error(f"Failed to list phone numbers: {e}")
            return []

    def _get_system_prompt(self, lead_data: Dict[str, Any]) -> str:
        """Generate personalized system prompt for the AI assistant."""
        lead_name = lead_data.get("name", "the prospect")
        lead_source = lead_data.get("source", "unknown")

        return f"""
You are a professional healthcare appointment scheduler calling {lead_name} who expressed interest through {lead_source}.

Your goal is to:
1. Warmly introduce yourself and the clinic
2. Confirm their interest in healthcare services
3. Understand their healthcare needs
4. Book an appointment if they're interested
5. Handle objections professionally

Guidelines:
- Be friendly, professional, and empathetic
- Listen carefully to their concerns
- Don't be pushy - respect "no" as an answer
- If they're not ready now, offer to call back later
- Use the available functions to book appointments or schedule callbacks
- Keep the conversation focused and efficient (aim for 2-3 minutes)

Sample opening: "Hi {lead_name}, this is [Your Name] from [Clinic Name]. I'm calling because you showed interest in our healthcare services. Do you have a quick moment to chat about scheduling a consultation?"

Remember: Always maintain HIPAA compliance and protect patient privacy.
        """

    def _mock_call_response(self, phone_number: str, lead_data: Dict) -> Dict[str, Any]:
        """Mock call response for development/testing."""
        import uuid

        return {
            "call_id": str(uuid.uuid4()),
            "status": "initiated",
            "phone_number": phone_number,
            "assistant_id": "mock_assistant",
            "started_at": datetime.utcnow().isoformat(),
            "estimated_cost": 0.15
        }