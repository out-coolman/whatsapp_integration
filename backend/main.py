"""
Healthcare Sales Orchestration Platform
FastAPI main application entry point.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.core.config import settings
from app.core.database import create_tables, seed_admin_user
from app.core.logging import setup_logging
from app.api.v1 import helena, callbacks, metrics, leads, calls, auth, schedule
from app.models.log import Log, LogLevel, LogCategory

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Create database tables if they don't exist
    try:
        create_tables()
        logger.info("Database tables verified/created")

        # Seed admin user
        seed_admin_user()
        logger.info("Admin user seeding completed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Initialize services and connections
    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Healthcare Sales Orchestration Platform for Clinics",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://*.yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else ["yourdomain.com", "*.yourdomain.com"]
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all HTTP requests and track metrics."""
    start_time = time.time()

    # Process request
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        logger.error(f"Request failed: {e}", exc_info=True)
        status_code = 500
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    # Calculate duration
    duration = time.time() - start_time

    # Update Prometheus metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=status_code
    ).inc()
    REQUEST_DURATION.observe(duration)

    # Log request (exclude health checks and metrics to reduce noise)
    if not request.url.path.startswith(("/health", "/metrics")):
        logger.info(
            f"{request.method} {request.url.path} - "
            f"{status_code} - {duration:.3f}s"
        )

    return response


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to responses."""
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time()
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "status_code": 500,
            "timestamp": time.time()
        }
    )


# Include API routers
app.include_router(
    helena.router,
    prefix="/api/v1",
    tags=["Helena CRM Webhooks"]
)

app.include_router(
    callbacks.router,
    prefix="/api/v1",
    tags=["VAPI Callbacks"]
)

app.include_router(
    schedule.router,
    prefix="/api/v1",
    tags=["Scheduling & Appointments"]
)

app.include_router(
    metrics.router,
    prefix="/api/v1",
    tags=["Metrics & Analytics"]
)

app.include_router(
    leads.router,
    prefix="/api/v1",
    tags=["Leads & CRM"]
)

app.include_router(
    calls.router,
    prefix="/api/v1",
    tags=["Calls & VAPI"]
)

app.include_router(
    auth.router,
    prefix="/api/v1",
    tags=["Authentication"]
)


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with service status."""
    from app.core.database import engine
    from app.core.redis_client import redis_client

    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {}
    }

    # Check database connection
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Redis connection
    try:
        redis_client.redis.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check external services (optional, don't fail health check)
    health_status["services"]["helena"] = "unknown"
    health_status["services"]["vapi"] = "unknown"
    health_status["services"]["ninsaude"] = "unknown"

    return health_status


@app.get("/metrics/prometheus")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    from fastapi.responses import Response

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Healthcare Sales Orchestration Platform",
        "docs_url": "/docs" if settings.DEBUG else None,
        "health_url": "/health",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time()
    }


# API information endpoint
@app.get("/api/v1")
async def api_info():
    """API version information."""
    return {
        "version": "v1",
        "description": "Healthcare Sales Orchestration API",
        "endpoints": {
            "webhooks": {
                "helena": "/api/v1/webhooks/helena",
                "test": "/api/v1/webhooks/helena/test"
            },
            "callbacks": {
                "vapi": "/api/v1/callbacks/vapi",
                "test": "/api/v1/callbacks/vapi/test"
            },
            "scheduling": {
                "availability": "/api/v1/availability",
                "book": "/api/v1/schedule",
                "appointments": "/api/v1/appointments"
            },
            "metrics": {
                "overview": "/api/v1/metrics/overview",
                "telephony": "/api/v1/metrics/telephony",
                "whatsapp": "/api/v1/metrics/whatsapp",
                "no_shows": "/api/v1/metrics/no_shows",
                "logs": "/api/v1/logs",
                "export": "/api/v1/export/metrics.csv"
            }
        },
        "authentication": "JWT Bearer token required",
        "rate_limits": {
            "webhooks": "1000 requests/minute",
            "api": "100 requests/minute"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )