"""
RQ Worker for processing background jobs.
"""
import sys
import os
import logging
from rq import Worker, Connection
import redis

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.config import settings
from app.core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Redis connection
redis_conn = redis.from_url(settings.REDIS_URL)

def main():
    """Main worker entry point."""
    logger.info("Starting RQ worker...")

    # Configure worker
    worker = Worker(
        ['high_priority', 'default'],  # Listen to high priority first, then default
        connection=redis_conn,
        name=f"healthcare-worker-{os.getpid()}"
    )

    # Start worker
    try:
        with Connection(redis_conn):
            worker.work()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
    finally:
        logger.info("Worker shutting down")


if __name__ == '__main__':
    main()