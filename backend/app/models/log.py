"""
Log model for audit trail and debugging.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, JSON, Index
from sqlalchemy.sql import func
from enum import Enum
import uuid

from app.core.database import Base


class LogLevel(str, Enum):
    """Log levels for categorizing log entries."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(str, Enum):
    """Categories for different types of logs."""
    WEBHOOK = "webhook"
    API_CALL = "api_call"
    JOB = "job"
    SYSTEM = "system"
    SECURITY = "security"
    BUSINESS = "business"
    INTEGRATION = "integration"


class Log(Base):
    """
    Log model for comprehensive audit trail and debugging.
    All system events, API calls, and business operations are logged here.
    """
    __tablename__ = "logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Classification
    level = Column(SQLEnum(LogLevel), nullable=False, index=True)
    category = Column(SQLEnum(LogCategory), nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)  # service/module name

    # Message and context
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict)  # Additional structured data

    # Request/Response tracking
    request_id = Column(String(100), index=True)  # For tracing requests across services
    correlation_id = Column(String(100), index=True)  # For business process correlation

    # Entity relationships
    lead_id = Column(String, index=True)
    appointment_id = Column(String, index=True)
    call_id = Column(String, index=True)
    message_id = Column(String, index=True)

    # User context
    user_id = Column(String(100), index=True)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)

    # Performance metrics
    duration_ms = Column(Integer)  # For timing operations
    memory_usage_mb = Column(Integer)

    # Error tracking
    error_code = Column(String(50))
    stack_trace = Column(Text)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Create indexes for common queries
    __table_args__ = (
        Index('idx_logs_level_category', 'level', 'category'),
        Index('idx_logs_source_created', 'source', 'created_at'),
        Index('idx_logs_lead_created', 'lead_id', 'created_at'),
        Index('idx_logs_correlation_created', 'correlation_id', 'created_at'),
    )

    def __repr__(self):
        return f"<Log(id={self.id}, level={self.level}, category={self.category}, source={self.source})>"

    @classmethod
    def create_webhook_log(cls, source: str, message: str, details: dict = None,
                          level: LogLevel = LogLevel.INFO, lead_id: str = None) -> 'Log':
        """Create a webhook-specific log entry."""
        return cls(
            level=level,
            category=LogCategory.WEBHOOK,
            source=source,
            message=message,
            details=details or {},
            lead_id=lead_id
        )

    @classmethod
    def create_api_call_log(cls, source: str, endpoint: str, method: str,
                           status_code: int, duration_ms: int = None,
                           details: dict = None, level: LogLevel = LogLevel.INFO) -> 'Log':
        """Create an API call log entry."""
        message = f"{method} {endpoint} -> {status_code}"
        log_details = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            **(details or {})
        }

        return cls(
            level=level,
            category=LogCategory.API_CALL,
            source=source,
            message=message,
            details=log_details,
            duration_ms=duration_ms
        )

    @classmethod
    def create_job_log(cls, source: str, job_name: str, message: str,
                      details: dict = None, level: LogLevel = LogLevel.INFO,
                      correlation_id: str = None) -> 'Log':
        """Create a job execution log entry."""
        log_details = {
            "job_name": job_name,
            **(details or {})
        }

        return cls(
            level=level,
            category=LogCategory.JOB,
            source=source,
            message=message,
            details=log_details,
            correlation_id=correlation_id
        )

    @classmethod
    def create_business_log(cls, source: str, action: str, message: str,
                           lead_id: str = None, appointment_id: str = None,
                           call_id: str = None, details: dict = None,
                           level: LogLevel = LogLevel.INFO) -> 'Log':
        """Create a business event log entry."""
        log_details = {
            "action": action,
            **(details or {})
        }

        return cls(
            level=level,
            category=LogCategory.BUSINESS,
            source=source,
            message=message,
            details=log_details,
            lead_id=lead_id,
            appointment_id=appointment_id,
            call_id=call_id
        )

    @classmethod
    def create_error_log(cls, source: str, message: str, error_code: str = None,
                        stack_trace: str = None, details: dict = None,
                        lead_id: str = None) -> 'Log':
        """Create an error log entry."""
        return cls(
            level=LogLevel.ERROR,
            category=LogCategory.SYSTEM,
            source=source,
            message=message,
            details=details or {},
            error_code=error_code,
            stack_trace=stack_trace,
            lead_id=lead_id
        )

    @classmethod
    def create_security_log(cls, source: str, message: str, user_id: str = None,
                           ip_address: str = None, user_agent: str = None,
                           details: dict = None, level: LogLevel = LogLevel.WARNING) -> 'Log':
        """Create a security-related log entry."""
        return cls(
            level=level,
            category=LogCategory.SECURITY,
            source=source,
            message=message,
            details=details or {},
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def mask_sensitive_data(self) -> None:
        """Mask sensitive data in log details for compliance."""
        if not self.details:
            return

        sensitive_fields = [
            'phone', 'email', 'phone_number', 'email_address',
            'cpf', 'credit_card', 'password', 'token', 'api_key'
        ]

        for field in sensitive_fields:
            if field in self.details:
                self.details[field] = "***MASKED***"

        # Mask phone numbers in message
        import re
        if self.message:
            self.message = re.sub(r'\+?[\d\s\-\(\)]{8,}', '***PHONE***', self.message)