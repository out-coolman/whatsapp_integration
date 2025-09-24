"""
RQ Scheduler for managing scheduled jobs.
"""
import sys
import os
import logging
from rq_scheduler import Scheduler
from datetime import datetime, timedelta
import redis

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.config import settings
from app.core.logging import setup_logging
from app.jobs.aggregate_metrics import aggregate_all_metrics

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Redis connection
redis_conn = redis.from_url(settings.REDIS_URL)

def setup_recurring_jobs(scheduler: Scheduler):
    """Setup recurring jobs for the scheduler."""
    logger.info("Setting up recurring jobs...")

    # Clear any existing scheduled jobs (optional - be careful in production)
    # scheduler.cancel_all_jobs()

    # Schedule metrics aggregation - daily at 1 AM
    scheduler.cron(
        "0 1 * * *",  # Daily at 1 AM
        func=aggregate_all_metrics,
        timeout=1800,  # 30 minutes timeout
        id="daily_metrics_aggregation"
    )

    # Schedule materialized view refresh - every 4 hours
    from app.jobs.aggregate_metrics import refresh_materialized_views
    scheduler.cron(
        "0 */4 * * *",  # Every 4 hours
        func=refresh_materialized_views,
        timeout=300,  # 5 minutes timeout
        id="refresh_materialized_views"
    )

    # Schedule cleanup jobs - weekly on Sunday at 3 AM
    scheduler.cron(
        "0 3 * * 0",  # Weekly on Sunday at 3 AM
        func=cleanup_old_logs,
        timeout=3600,  # 1 hour timeout
        id="weekly_cleanup"
    )

    logger.info("Recurring jobs scheduled successfully")


def cleanup_old_logs():
    """Clean up old log entries and events."""
    from app.core.database import SessionLocal
    from app.models.log import Log
    from app.models.event import Event

    db = SessionLocal()
    try:
        # Delete logs older than retention period
        cutoff_date = datetime.utcnow() - timedelta(days=settings.METRICS_RETENTION_DAYS)

        # Clean up logs
        deleted_logs = db.query(Log).filter(
            Log.created_at < cutoff_date
        ).delete(synchronize_session=False)

        # Clean up completed events older than 30 days
        event_cutoff = datetime.utcnow() - timedelta(days=30)
        deleted_events = db.query(Event).filter(
            Event.created_at < event_cutoff,
            Event.status == 'completed'
        ).delete(synchronize_session=False)

        db.commit()

        logger.info(f"Cleanup completed: {deleted_logs} logs, {deleted_events} events deleted")
        return {"logs_deleted": deleted_logs, "events_deleted": deleted_events}

    except Exception as e:
        logger.error(f"Error in cleanup job: {e}", exc_info=True)
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


def main():
    """Main scheduler entry point."""
    logger.info("Starting RQ scheduler...")

    try:
        scheduler = Scheduler(connection=redis_conn)

        # Setup recurring jobs
        setup_recurring_jobs(scheduler)

        # Start scheduler
        logger.info("RQ Scheduler started successfully")
        scheduler.run()

    except KeyboardInterrupt:
        logger.info("Scheduler interrupted by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
    finally:
        logger.info("Scheduler shutting down")


if __name__ == '__main__':
    main()