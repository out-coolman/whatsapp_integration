"""
Message model for WhatsApp and other communication channels.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
import uuid

from app.core.database import Base


class MessageDirection(str, Enum):
    """Direction of the message."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(str, Enum):
    """Message delivery status."""
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class MessageChannel(str, Enum):
    """Communication channel."""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"


class Message(Base):
    """
    Message model for tracking all communications with leads.
    """
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    helena_message_id = Column(String, unique=True, index=True)

    # Relationships
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False, index=True)
    lead = relationship("Lead", back_populates="messages")

    # Message content
    content = Column(Text, nullable=False)
    channel = Column(SQLEnum(MessageChannel), nullable=False, index=True)
    direction = Column(SQLEnum(MessageDirection), nullable=False, index=True)

    # Delivery tracking
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.QUEUED, index=True)
    external_id = Column(String(255))  # Provider message ID
    error_message = Column(Text)

    # Metadata
    message_metadata = Column(JSON, default=dict)
    template_name = Column(String(100))  # For template messages
    template_params = Column(JSON)

    # Timestamps
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Message(id={self.id}, lead_id={self.lead_id}, channel={self.channel}, direction={self.direction})>"

    @property
    def masked_content(self) -> str:
        """Get masked content for logging."""
        if len(self.content) <= 50:
            return "***MESSAGE***"
        return f"***MESSAGE*** (length: {len(self.content)})"

    def is_delivered(self) -> bool:
        """Check if message was successfully delivered."""
        return self.status in [MessageStatus.DELIVERED, MessageStatus.READ]

    def is_failed(self) -> bool:
        """Check if message delivery failed."""
        return self.status == MessageStatus.FAILED

    def mark_sent(self, external_id: str = None) -> None:
        """Mark message as sent."""
        self.status = MessageStatus.SENT
        self.sent_at = func.now()
        if external_id:
            self.external_id = external_id

    def mark_delivered(self) -> None:
        """Mark message as delivered."""
        self.status = MessageStatus.DELIVERED
        self.delivered_at = func.now()

    def mark_read(self) -> None:
        """Mark message as read."""
        self.status = MessageStatus.READ
        self.read_at = func.now()

    def mark_failed(self, error_message: str) -> None:
        """Mark message as failed."""
        self.status = MessageStatus.FAILED
        self.failed_at = func.now()
        self.error_message = error_message