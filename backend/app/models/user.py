"""
User model for authentication and authorization.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Enum as SQLEnum, Text, JSON, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from enum import Enum
import uuid

from app.core.database import Base
from app.core.security import get_password_hash, verify_password


class UserRole(str, Enum):
    """User roles for authorization."""
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(Base):
    """
    User model for authentication and authorization.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)

    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))

    # Authentication
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.AGENT, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)

    # Settings and preferences
    preferences = Column(JSON, default=dict)
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")

    # Security
    last_login_at = Column(DateTime(timezone=True))
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))

    # Metadata
    notes = Column(Text)
    avatar_url = Column(String(500))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN

    @property
    def is_manager(self) -> bool:
        """Check if user is manager or admin."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]

    @property
    def is_locked(self) -> bool:
        """Check if account is temporarily locked."""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until

    def set_password(self, password: str) -> None:
        """Set user password (hashed)."""
        self.hashed_password = get_password_hash(password)
        self.password_changed_at = datetime.utcnow()

    def check_password(self, password: str) -> bool:
        """Verify password against hash."""
        return verify_password(password, self.hashed_password)

    def record_login_attempt(self, success: bool = True) -> None:
        """Record login attempt."""
        if success:
            self.login_attempts = 0
            self.last_login_at = datetime.utcnow()
            self.last_active_at = datetime.utcnow()
            self.locked_until = None
        else:
            self.login_attempts += 1
            # Lock account after 5 failed attempts for 30 minutes
            if self.login_attempts >= 5:
                self.locked_until = datetime.utcnow() + timedelta(minutes=30)

    def update_last_active(self) -> None:
        """Update last active timestamp."""
        self.last_active_at = datetime.utcnow()

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        # Admin has all permissions
        if self.role == UserRole.ADMIN:
            return True

        # Manager permissions
        if self.role == UserRole.MANAGER:
            manager_permissions = [
                "view_dashboard", "view_leads", "edit_leads", "view_calls",
                "view_metrics", "export_data", "manage_agents"
            ]
            return permission in manager_permissions

        # Agent permissions
        if self.role == UserRole.AGENT:
            agent_permissions = [
                "view_dashboard", "view_leads", "edit_leads", "view_calls"
            ]
            return permission in agent_permissions

        # Viewer permissions
        if self.role == UserRole.VIEWER:
            viewer_permissions = [
                "view_dashboard", "view_leads", "view_calls"
            ]
            return permission in viewer_permissions

        return False

    def get_settings(self, key: str, default=None):
        """Get user preference/setting."""
        if not self.preferences:
            return default
        return self.preferences.get(key, default)

    def set_setting(self, key: str, value) -> None:
        """Set user preference/setting."""
        if not self.preferences:
            self.preferences = {}
        self.preferences[key] = value

    @classmethod
    def create_admin_user(cls, email: str, password: str, first_name: str, last_name: str) -> "User":
        """Create admin user."""
        user = cls(
            email=email,
            username=email,  # Use email as username for simplicity
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )
        user.set_password(password)
        return user

    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding sensitive data)."""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role.value if self.role else None,
            "status": self.status.value if self.status else None,
            "timezone": self.timezone,
            "language": self.language,
            "avatar_url": self.avatar_url,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
        }