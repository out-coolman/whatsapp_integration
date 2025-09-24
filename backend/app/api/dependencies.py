"""
Common API dependencies and utilities.
"""
from typing import Optional, Generator
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.security import require_api_key, verify_api_key
from app.core.logging import audit_logger
from app.models.log import Log, LogLevel, LogCategory

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


def log_api_request(
    request: Request,
    db: Session = Depends(get_db),
    user_id: Optional[str] = None
) -> None:
    """Log API request for audit purposes."""
    try:
        # Create API call log entry
        log_entry = Log.create_api_call_log(
            source="api",
            endpoint=str(request.url.path),
            method=request.method,
            status_code=200,  # Will be updated by middleware if needed
            details={
                "query_params": dict(request.query_params),
                "headers": {
                    k: v for k, v in request.headers.items()
                    if k.lower() not in ["authorization", "x-api-key"]
                }
            }
        )

        log_entry.user_id = user_id
        log_entry.ip_address = get_client_ip(request)
        log_entry.user_agent = request.headers.get("User-Agent")

        db.add(log_entry)
        db.commit()

        # Audit log for security-sensitive endpoints
        if any(path in str(request.url.path) for path in ["/webhooks/", "/metrics/", "/export/"]):
            audit_logger.log_event(
                event_type="api_access",
                details={
                    "endpoint": str(request.url.path),
                    "method": request.method,
                    "ip": get_client_ip(request)
                },
                user_id=user_id
            )

    except Exception as e:
        logger.error(f"Failed to log API request: {e}")


async def verify_webhook_signature(
    request: Request,
    source: str,
    secret_key: Optional[str] = None
) -> bool:
    """
    Verify webhook signature for security.
    Implementation depends on the webhook source (Helena, VAPI, etc.).
    """
    if not secret_key:
        logger.warning(f"No secret key configured for {source} webhook verification")
        return True  # Allow in development, should be False in production

    # Get signature from headers
    signature = request.headers.get("X-Signature") or request.headers.get("X-Hub-Signature-256")

    if not signature:
        logger.warning(f"No signature provided for {source} webhook")
        return False

    # TODO: Implement actual signature verification based on webhook source
    # This is a placeholder - each webhook provider has different signature schemes
    return True


class RateLimiter:
    """Simple in-memory rate limiter for API endpoints."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limit."""
        import time

        now = time.time()
        window_start = now - self.window_seconds

        # Clean old entries
        self.requests = {
            key: timestamps for key, timestamps in self.requests.items()
            if any(ts > window_start for ts in timestamps)
        }

        # Get recent requests for this identifier
        if identifier not in self.requests:
            self.requests[identifier] = []

        recent_requests = [ts for ts in self.requests[identifier] if ts > window_start]

        if len(recent_requests) >= self.max_requests:
            return False

        # Add current request
        recent_requests.append(now)
        self.requests[identifier] = recent_requests
        return True


# Global rate limiter instances
webhook_rate_limiter = RateLimiter(max_requests=1000, window_seconds=60)  # More lenient for webhooks
api_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


def check_rate_limit(request: Request, limiter: RateLimiter = api_rate_limiter):
    """Dependency to check rate limits."""
    client_ip = get_client_ip(request)

    if not limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )


def require_api_key_dependency(request: Request):
    """Dependency wrapper for API key requirement."""
    return require_api_key(request)


def optional_api_key(request: Request) -> bool:
    """Optional API key verification for endpoints that can work without auth."""
    return verify_api_key(request)


# Common query parameters
class CommonQueryParams:
    """Common query parameters for API endpoints."""

    def __init__(
        self,
        page: int = 1,
        limit: int = 100,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ):
        self.page = max(1, page)
        self.limit = min(1000, max(1, limit))  # Cap at 1000 items per page
        self.order_by = order_by
        self.order_direction = order_direction.lower()

        if self.order_direction not in ["asc", "desc"]:
            self.order_direction = "desc"

    @property
    def offset(self) -> int:
        """Calculate offset for pagination."""
        return (self.page - 1) * self.limit