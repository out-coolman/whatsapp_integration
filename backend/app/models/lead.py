"""
Lead model for healthcare sales orchestration.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

from app.core.database import Base


class LeadStage(str, Enum):
    """Lead stages in the sales funnel."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    BOOKED = "booked"
    CONFIRMED = "confirmed"
    SHOWED = "showed"
    NO_SHOW = "no_show"
    CONVERTED = "converted"
    LOST = "lost"


class LeadSource(str, Enum):
    """Lead source channels."""
    ORGANIC = "organic"
    PAID_ADS = "paid_ads"
    SOCIAL_MEDIA = "social_media"
    REFERRAL = "referral"
    DIRECT = "direct"
    OTHER = "other"


class LeadClassification(str, Enum):
    """Lead temperature/priority classification."""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class Lead(Base):
    """
    Lead model representing potential customers in the healthcare sales funnel.
    """
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    helena_id = Column(String, unique=True, nullable=False, index=True)

    # Contact information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    email = Column(String(255), index=True)
    phone = Column(String(20), nullable=False, index=True)

    # Lead classification
    stage = Column(SQLEnum(LeadStage), default=LeadStage.NEW, nullable=False, index=True)
    classification = Column(SQLEnum(LeadClassification), default=LeadClassification.WARM, index=True)
    source = Column(SQLEnum(LeadSource), default=LeadSource.OTHER, index=True)

    # Metadata
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    notes = Column(Text)

    # Tracking
    is_active = Column(Boolean, default=True, index=True)
    assigned_agent_id = Column(String(100))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_contacted_at = Column(DateTime(timezone=True))
    qualified_at = Column(DateTime(timezone=True))

    # Relationships
    messages = relationship("Message", back_populates="lead", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="lead", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="lead", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lead(id={self.id}, helena_id={self.helena_id}, stage={self.stage})>"

    @property
    def full_name(self) -> str:
        """Get full name of the lead."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def masked_phone(self) -> str:
        """Get masked phone number for logging."""
        if not self.phone:
            return "***"
        return f"***{self.phone[-4:]}" if len(self.phone) > 4 else "***"

    @property
    def masked_email(self) -> str:
        """Get masked email for logging."""
        if not self.email:
            return "***"
        parts = self.email.split("@")
        if len(parts) == 2:
            return f"***@{parts[1]}"
        return "***"

    def has_tag(self, tag: str) -> bool:
        """Check if lead has a specific tag."""
        return tag in (self.tags or [])

    def add_tag(self, tag: str) -> None:
        """Add a tag to the lead."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the lead."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)

    def update_stage(self, new_stage: LeadStage) -> None:
        """Update lead stage with timestamp tracking."""
        old_stage = self.stage
        self.stage = new_stage

        if new_stage == LeadStage.CONTACTED and not self.last_contacted_at:
            self.last_contacted_at = datetime.utcnow()
        elif new_stage == LeadStage.QUALIFIED and not self.qualified_at:
            self.qualified_at = datetime.utcnow()

    def is_hot_lead(self) -> bool:
        """Determine if this is a hot lead requiring immediate action."""
        return (
            self.classification == LeadClassification.HOT or
            self.has_tag("urgent") or
            self.has_tag("high_value") or
            (self.source == LeadSource.REFERRAL and self.stage == LeadStage.NEW)
        )