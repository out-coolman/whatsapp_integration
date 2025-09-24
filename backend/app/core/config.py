"""
Core configuration and settings for the healthcare orchestration platform.
"""
import os
from typing import Optional
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/healthcare_orchestration"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # API Security
    API_KEY: str = "your-secure-api-key-here"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Helena CRM
    HELENA_API_KEY: Optional[str] = None
    HELENA_BASE_URL: str = "https://api.helena.com/v1"
    HELENA_WEBHOOK_SECRET: Optional[str] = None

    # VAPI (Voice AI)
    VAPI_API_KEY: Optional[str] = None
    VAPI_BASE_URL: str = "https://api.vapi.ai"
    VAPI_PHONE_NUMBER_ID: Optional[str] = None

    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: str = "+556312345678"  # Brazil +55, area code 63

    # Ninsaúde Scheduling API
    NINSAUDE_API_KEY: Optional[str] = None
    NINSAUDE_BASE_URL: str = "https://api.ninsaude.com/v1"
    NINSAUDE_CLINIC_ID: Optional[str] = None

    # WhatsApp (via Helena)
    WHATSAPP_API_KEY: Optional[str] = None
    WHATSAPP_BASE_URL: str = "https://api.helena.com/v1/whatsapp"

    # Application
    APP_NAME: str = "Healthcare Sales Orchestration"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Logging
    LOG_LEVEL: str = "INFO"
    MASK_PII_IN_LOGS: bool = True

    # Job Scheduler
    JOB_TIMEOUT: int = 300  # 5 minutes
    MAX_JOB_RETRIES: int = 3

    # Metrics
    METRICS_RETENTION_DAYS: int = 90
    AGGREGATION_INTERVAL_MINUTES: int = 5

    # Prometheus
    PROMETHEUS_MULTIPROC_DIR: Optional[str] = None

    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v

    @validator("REDIS_URL", pre=True)
    def validate_redis_url(cls, v):
        if not v:
            raise ValueError("REDIS_URL is required")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


class DevelopmentSettings(Settings):
    """Development environment settings."""
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "DEBUG"


class TestingSettings(Settings):
    """Testing environment settings."""
    DEBUG: bool = True
    ENVIRONMENT: str = "testing"
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/healthcare_orchestration_test"
    REDIS_URL: str = "redis://localhost:6379/1"


class ProductionSettings(Settings):
    """Production environment settings."""
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"


def get_settings() -> Settings:
    """Get settings based on environment."""
    env = os.getenv("ENVIRONMENT", "production").lower()

    if env == "development":
        return DevelopmentSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return ProductionSettings()


# Global settings instance
settings = get_settings()