# Healthcare Sales Orchestration Platform

A comprehensive FastAPI backend for automating healthcare sales processes through intelligent orchestration of leads, calls, messaging, and appointments.

## 🏥 Product Overview

This platform serves as the backbone for healthcare clinics to automate their sales funnel through:

- **Lead Management**: Centralized lead tracking from multiple sources
- **AI Voice Calls**: Automated outbound calls via VAPI + Twilio
- **WhatsApp Integration**: Automated messaging through Helena CRM
- **Appointment Scheduling**: Seamless integration with Ninsaúde healthcare API
- **Analytics Dashboard**: Real-time metrics and performance tracking
- **Compliance**: HIPAA-compliant logging and PII masking

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Environment Setup

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd whatsapp_integration
cp .env.example .env
```

2. **Configure environment variables in `.env`:**
```bash
# Database
DATABASE_URL=postgresql://postgres:password@db:5432/healthcare_orchestration

# Redis
REDIS_URL=redis://redis:6379/0

# API Security
API_KEY=your-secure-api-key-here
SECRET_KEY=your-secret-key-here

# Helena CRM
HELENA_API_KEY=your-helena-api-key
HELENA_BASE_URL=https://api.helena.com/v1
HELENA_WEBHOOK_SECRET=your-webhook-secret

# VAPI (Voice AI)
VAPI_API_KEY=your-vapi-api-key
VAPI_BASE_URL=https://api.vapi.ai
VAPI_PHONE_NUMBER_ID=your-phone-number-id

# Twilio
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+556312345678

# Ninsaúde
NINSAUDE_API_KEY=your-ninsaude-api-key
NINSAUDE_BASE_URL=https://api.ninsaude.com/v1
NINSAUDE_CLINIC_ID=your-clinic-id
```

3. **Start the services:**
```bash
docker-compose up -d
```

4. **Run database migrations:**
```bash
docker-compose exec web alembic upgrade head
```

5. **Verify installation:**
```bash
curl http://localhost:8000/health
```

## 📋 Services Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Helena CRM    │───▶│   FastAPI Web   │◀───│   VAPI + Twilio │
│   (Webhooks)    │    │   Application   │    │   (Voice Calls) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ninsaúde API  │◀───│   PostgreSQL    │───▶│   RQ Workers    │
│   (Scheduling)  │    │   Database      │    │   (Background)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                      ┌─────────────────┐
                      │ Redis + RQ      │
                      │ Scheduler       │
                      └─────────────────┘
```

### Service Components

- **Web Application**: FastAPI server handling API requests and webhooks
- **Database**: PostgreSQL with comprehensive data models and materialized views
- **Redis**: Caching and job queue management
- **RQ Workers**: Background job processing for orchestration
- **RQ Scheduler**: Automated scheduling for reminders and aggregations

## 🔌 API Endpoints

### Webhooks
- `POST /api/v1/webhooks/helena` - Receive Helena CRM events
- `GET /api/v1/webhooks/helena/test` - Test webhook connectivity

### Callbacks
- `POST /api/v1/callbacks/vapi` - Receive VAPI call updates
- `GET /api/v1/callbacks/vapi/test` - Test callback connectivity

### Scheduling
- `GET /api/v1/availability` - Get professional availability
- `POST /api/v1/schedule` - Book appointments
- `GET /api/v1/appointments` - List appointments
- `GET /api/v1/appointments/{id}` - Get specific appointment
- `PUT /api/v1/appointments/{id}` - Update appointment

### Metrics & Analytics
- `GET /api/v1/metrics/overview` - Funnel and real-time metrics
- `GET /api/v1/metrics/telephony` - Call performance metrics
- `GET /api/v1/metrics/whatsapp` - Messaging metrics
- `GET /api/v1/metrics/no_shows` - No-show analysis
- `GET /api/v1/export/metrics.csv` - Export metrics to CSV

### Monitoring
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed service health
- `GET /metrics/prometheus` - Prometheus metrics

## 🔐 Authentication

All API endpoints (except webhooks and health checks) require API key authentication:

```bash
curl -H "X-API-KEY: your-secure-api-key-here" \
     http://localhost:8000/api/v1/metrics/overview
```

## 📊 Business Logic Flow

### 1. Lead Creation & Hot Lead Detection
```
Helena Webhook (lead_created) → Lead Model → Hot Lead Check → Immediate Call + WhatsApp
```

### 2. Call Orchestration
```
VAPI Call Initiated → Call Status Updates → Outcome Analysis → Follow-up Actions
```

### 3. Appointment Flow
```
Booking Request → Ninsaúde Integration → Confirmation → Automated Reminders (24h + 3h)
```

### 4. No-Show Management
```
No-Show Detection → Lead Reclassification → Reactivation Sequence
```

## 📈 Metrics & KPIs

### Lead Funnel Metrics
- **Conversion Rates**: New → Contacted → Qualified → Booked → Showed
- **Source Performance**: Organic, Paid Ads, Social Media, Referrals
- **Lead Classification**: Hot, Warm, Cold lead performance

### Telephony Metrics
- **Call Performance**: Answer rate, completion rate, average handle time
- **Cost Analysis**: Total cost, cost per call, cost per conversion
- **Outcome Tracking**: Appointments booked, callbacks requested, not interested

### WhatsApp Metrics
- **Delivery Performance**: Delivery rate, read rate, response rate
- **Engagement**: First response time, conversation volume
- **Campaign Effectiveness**: Template vs. freeform message performance

### No-Show Analysis
- **Risk Prediction**: Professional and clinic-level no-show rates
- **Reminder Effectiveness**: 24h vs. 3h reminder success rates
- **Revenue Impact**: Cost of no-shows, reschedule rates

## 🔧 Development

### Running Tests
```bash
# Run all tests
docker-compose exec web pytest

# Run with coverage
docker-compose exec web pytest --cov=app

# Run specific test module
docker-compose exec web pytest app/tests/test_helena_webhook.py
```

### Database Migrations
```bash
# Create new migration
docker-compose exec web alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec web alembic upgrade head

# Rollback migration
docker-compose exec web alembic downgrade -1
```

### Background Jobs
```bash
# Monitor RQ jobs
docker-compose exec web rq worker high_priority default

# Check job status
docker-compose exec web rq info

# Schedule one-time job
docker-compose exec web python -c "
from app.jobs.scheduler import default_queue
from app.jobs.aggregate_metrics import aggregate_all_metrics
job = default_queue.enqueue(aggregate_all_metrics)
print(f'Job {job.id} enqueued')
"
```

## 📊 Monitoring & Observability

### Prometheus Metrics
Access metrics at `http://localhost:9090` (Prometheus) and `http://localhost:3000` (Grafana).

Key metrics:
- `http_requests_total` - HTTP request counts by endpoint and status
- `http_request_duration_seconds` - Request duration histogram
- Custom business metrics via `/metrics/prometheus`

### Log Analysis
- Structured JSON logging with correlation IDs
- PII masking for HIPAA compliance
- Comprehensive audit trail for all business events

### Health Monitoring
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health with service status
curl http://localhost:8000/health/detailed
```

## 🔒 Security & Compliance

### PII Protection
- Automatic masking of phone numbers, emails, and sensitive data in logs
- Configurable via `MASK_PII_IN_LOGS` environment variable

### API Security
- API key authentication for all protected endpoints
- Rate limiting (1000 req/min for webhooks, 100 req/min for API)
- CORS configuration for production domains

### HIPAA Compliance
- Encrypted data transmission (HTTPS required in production)
- Audit logging for all patient data access
- Secure credential management via environment variables

## 🚀 Production Deployment

### Docker Compose Production
```bash
# Use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Enable HTTPS (configure reverse proxy)
# Set secure environment variables
# Configure monitoring and alerting
```

### Environment Variables for Production
```bash
# Security
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=<generate-secure-key>
API_KEY=<generate-secure-api-key>

# Database (use managed PostgreSQL)
DATABASE_URL=postgresql://user:pass@prod-db:5432/healthcare_orchestration

# Redis (use managed Redis)
REDIS_URL=redis://prod-redis:6379/0

# Enable security features
MASK_PII_IN_LOGS=true
```

### Monitoring Setup
1. **Prometheus**: Scrapes metrics from `/metrics/prometheus`
2. **Grafana**: Visualizes metrics with pre-built dashboards
3. **Alerting**: Configure alerts for critical metrics (no-show rates, API errors)

## 🤝 Contributing

### Code Style
- Black code formatting
- PEP 8 compliance
- Type hints for all functions
- Comprehensive docstrings

### Pull Request Process
1. Create feature branch from `main`
2. Implement changes with tests
3. Run full test suite
4. Update documentation
5. Create pull request with detailed description

## 📞 Support

For technical support or questions:
- Create GitHub issue for bugs
- Contact team for API credentials and integration support
- Review logs in `/api/v1/logs` for troubleshooting

## 📄 License

This project is proprietary software for healthcare sales orchestration. All rights reserved.

---

**Built with ❤️ for healthcare professionals** 🏥