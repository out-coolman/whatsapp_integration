"""
Twilio service for phone number management and basic telephony.
"""
import httpx
from typing import Dict, Any, Optional, List
import logging

from app.core.config import settings
from app.core.security import mask_pii

logger = logging.getLogger(__name__)


class TwilioService:
    """Service for Twilio telephony integration."""

    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.base_url = "https://api.twilio.com/2010-04-01"
        self.timeout = 30.0

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Twilio API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        auth = (self.account_sid, self.auth_token)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    data=data,  # Twilio uses form data, not JSON
                    params=params,
                    auth=auth
                )

                # Log request (with masked data)
                log_data = {
                    "method": method.upper(),
                    "url": url,
                    "status_code": response.status_code,
                    "data": mask_pii(str(data)) if data else None
                }
                logger.info(f"Twilio API request: {log_data}")

                response.raise_for_status()

                # Twilio returns XML, but we'll work with JSON when possible
                if response.headers.get("content-type", "").startswith("application/json"):
                    return response.json()
                else:
                    return {"status": "success", "content": response.text}

        except httpx.TimeoutException:
            logger.error(f"Twilio API timeout: {method} {endpoint}")
            raise Exception("Twilio API timeout")
        except httpx.HTTPStatusError as e:
            logger.error(f"Twilio API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Twilio API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Twilio API request failed: {e}")
            raise

    async def get_phone_numbers(self) -> List[Dict[str, Any]]:
        """Get list of Twilio phone numbers."""
        try:
            endpoint = f"/Accounts/{self.account_sid}/IncomingPhoneNumbers.json"
            response = await self._make_request("GET", endpoint)

            return [
                {
                    "sid": number.get("sid"),
                    "phone_number": number.get("phone_number"),
                    "friendly_name": number.get("friendly_name"),
                    "capabilities": number.get("capabilities", {}),
                    "status": "active"
                }
                for number in response.get("incoming_phone_numbers", [])
            ]
        except Exception as e:
            logger.error(f"Failed to get phone numbers: {e}")
            return self._mock_phone_numbers()

    async def provision_phone_number(
        self,
        area_code: str = "63",  # Default to Palmas, TO area code
        country_code: str = "BR"
    ) -> Dict[str, Any]:
        """Provision a new phone number in Brazil."""
        try:
            # First, search for available numbers
            search_endpoint = f"/Accounts/{self.account_sid}/AvailablePhoneNumbers/{country_code}/Local.json"
            search_params = {"AreaCode": area_code, "Limit": 10}

            available = await self._make_request("GET", search_endpoint, params=search_params)
            available_numbers = available.get("available_phone_numbers", [])

            if not available_numbers:
                raise Exception(f"No available numbers in area code {area_code}")

            # Purchase the first available number
            number_to_buy = available_numbers[0]["phone_number"]
            purchase_endpoint = f"/Accounts/{self.account_sid}/IncomingPhoneNumbers.json"
            purchase_data = {
                "PhoneNumber": number_to_buy,
                "FriendlyName": f"Healthcare Orchestration - {area_code}"
            }

            response = await self._make_request("POST", purchase_endpoint, data=purchase_data)

            return {
                "sid": response.get("sid"),
                "phone_number": response.get("phone_number"),
                "friendly_name": response.get("friendly_name"),
                "status": "provisioned"
            }

        except Exception as e:
            logger.error(f"Failed to provision phone number: {e}")
            return self._mock_provisioned_number(area_code)

    async def configure_phone_number(
        self,
        phone_number_sid: str,
        webhook_url: str,
        webhook_method: str = "POST"
    ) -> Dict[str, Any]:
        """Configure webhooks for a phone number."""
        try:
            endpoint = f"/Accounts/{self.account_sid}/IncomingPhoneNumbers/{phone_number_sid}.json"
            data = {
                "VoiceUrl": webhook_url,
                "VoiceMethod": webhook_method,
                "StatusCallback": f"{webhook_url}/status",
                "StatusCallbackMethod": webhook_method
            }

            response = await self._make_request("POST", endpoint, data=data)

            return {
                "sid": response.get("sid"),
                "phone_number": response.get("phone_number"),
                "voice_url": response.get("voice_url"),
                "status": "configured"
            }

        except Exception as e:
            logger.error(f"Failed to configure phone number {phone_number_sid}: {e}")
            return {"status": "error", "error": str(e)}

    async def get_call_details(self, call_sid: str) -> Dict[str, Any]:
        """Get details for a specific call."""
        try:
            endpoint = f"/Accounts/{self.account_sid}/Calls/{call_sid}.json"
            response = await self._make_request("GET", endpoint)

            return {
                "call_sid": response.get("sid"),
                "from_number": response.get("from"),
                "to_number": response.get("to"),
                "status": response.get("status"),
                "duration": response.get("duration"),
                "start_time": response.get("start_time"),
                "end_time": response.get("end_time"),
                "price": response.get("price"),
                "price_unit": response.get("price_unit"),
                "direction": response.get("direction")
            }

        except Exception as e:
            logger.error(f"Failed to get call details for {call_sid}: {e}")
            return {"error": str(e)}

    async def get_call_recordings(self, call_sid: str) -> List[Dict[str, Any]]:
        """Get recordings for a specific call."""
        try:
            endpoint = f"/Accounts/{self.account_sid}/Calls/{call_sid}/Recordings.json"
            response = await self._make_request("GET", endpoint)

            return [
                {
                    "recording_sid": recording.get("sid"),
                    "call_sid": recording.get("call_sid"),
                    "duration": recording.get("duration"),
                    "uri": recording.get("uri"),
                    "date_created": recording.get("date_created")
                }
                for recording in response.get("recordings", [])
            ]

        except Exception as e:
            logger.error(f"Failed to get recordings for call {call_sid}: {e}")
            return []

    async def get_account_usage(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get Twilio account usage statistics."""
        try:
            endpoint = f"/Accounts/{self.account_sid}/Usage/Records.json"
            params = {}
            if start_date:
                params["StartDate"] = start_date
            if end_date:
                params["EndDate"] = end_date

            response = await self._make_request("GET", endpoint, params=params)

            # Aggregate usage by category
            usage_summary = {
                "total_cost": 0.0,
                "calls": {"count": 0, "cost": 0.0, "minutes": 0},
                "sms": {"count": 0, "cost": 0.0},
                "recordings": {"count": 0, "cost": 0.0}
            }

            for record in response.get("usage_records", []):
                category = record.get("category", "").lower()
                cost = float(record.get("price", 0))
                usage = int(record.get("usage", 0))

                usage_summary["total_cost"] += cost

                if "call" in category:
                    usage_summary["calls"]["count"] += usage
                    usage_summary["calls"]["cost"] += cost
                    if "minutes" in category:
                        usage_summary["calls"]["minutes"] += usage
                elif "sms" in category:
                    usage_summary["sms"]["count"] += usage
                    usage_summary["sms"]["cost"] += cost
                elif "recording" in category:
                    usage_summary["recordings"]["count"] += usage
                    usage_summary["recordings"]["cost"] += cost

            return usage_summary

        except Exception as e:
            logger.error(f"Failed to get account usage: {e}")
            return {"error": str(e)}

    def _mock_phone_numbers(self) -> List[Dict[str, Any]]:
        """Mock phone numbers for development."""
        return [
            {
                "sid": "PN12345678901234567890123456789012",
                "phone_number": settings.TWILIO_PHONE_NUMBER,
                "friendly_name": "Healthcare Orchestration Main",
                "capabilities": {
                    "voice": True,
                    "sms": True,
                    "mms": False,
                    "fax": False
                },
                "status": "active"
            }
        ]

    def _mock_provisioned_number(self, area_code: str) -> Dict[str, Any]:
        """Mock provisioned number for development."""
        import uuid

        return {
            "sid": f"PN{uuid.uuid4().hex[:32]}",
            "phone_number": f"+55{area_code}91234567",
            "friendly_name": f"Healthcare Orchestration - {area_code}",
            "status": "provisioned"
        }