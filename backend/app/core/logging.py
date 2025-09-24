"""
Logging configuration with PII masking support.
"""
import logging
import sys
from typing import Dict, Any
import json

from .config import settings
from .security import mask_pii


class PIIMaskingFormatter(logging.Formatter):
    """Custom formatter that masks PII in log messages."""

    def format(self, record):
        # Format the log record normally first
        formatted = super().format(record)

        # Mask PII if enabled
        if settings.MASK_PII_IN_LOGS:
            formatted = mask_pii(formatted)

        return formatted


def setup_logging():
    """Configure application logging."""
    # Root logger configuration
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Apply PII masking formatter to all handlers
    formatter = PIIMaskingFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)

    # Set specific logger levels
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)


class AuditLogger:
    """Structured audit logger for compliance and monitoring."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(f"audit.{name}")

    def log_event(self, event_type: str, details: Dict[str, Any], user_id: str = None):
        """Log an audit event with structured data."""
        audit_data = {
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
            "timestamp": None  # Will be added by log formatter
        }

        # Mask PII in audit data if enabled
        if settings.MASK_PII_IN_LOGS:
            audit_data_str = json.dumps(audit_data, default=str)
            audit_data_str = mask_pii(audit_data_str)
            self.logger.info(f"AUDIT: {audit_data_str}")
        else:
            self.logger.info(f"AUDIT: {json.dumps(audit_data, default=str)}")

    def log_webhook_received(self, source: str, event_type: str, lead_id: str = None):
        """Log webhook receipt."""
        self.log_event("webhook_received", {
            "source": source,
            "event_type": event_type,
            "lead_id": lead_id
        })

    def log_call_initiated(self, lead_id: str, phone_number: str):
        """Log call initiation."""
        self.log_event("call_initiated", {
            "lead_id": lead_id,
            "phone_number": mask_pii(phone_number) if settings.MASK_PII_IN_LOGS else phone_number
        })

    def log_appointment_booked(self, lead_id: str, appointment_id: str):
        """Log appointment booking."""
        self.log_event("appointment_booked", {
            "lead_id": lead_id,
            "appointment_id": appointment_id
        })

    def log_metric_export(self, export_type: str, record_count: int, user_id: str = None):
        """Log metrics export."""
        self.log_event("metric_export", {
            "export_type": export_type,
            "record_count": record_count
        }, user_id)


# Global audit logger instance
audit_logger = AuditLogger("main")