"""
Database configuration and session management.
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Database engine configuration
if "sqlite" in settings.DATABASE_URL:
    # SQLite for testing
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
    )
else:
    # PostgreSQL for production
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=0,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# Metadata for materialized views
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


def drop_tables():
    """Drop all tables (for testing)."""
    Base.metadata.drop_all(bind=engine)
    logger.info("Database tables dropped")


def seed_admin_user():
    """Seed the database with an admin user."""
    from app.models.user import User, UserRole, UserStatus
    from app.core.security import get_password_hash

    db = SessionLocal()
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.email == "admin@gmail.com").first()
        if existing_admin:
            logger.info("Admin user already exists")
            return

        # Create admin user
        admin_user = User(
            email="admin@gmail.com",
            username="admin",
            first_name="Admin",
            last_name="User",
            hashed_password=get_password_hash("@Hireme2025"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        logger.info(f"Admin user created successfully with ID: {admin_user.id}")

    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()