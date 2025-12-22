"""
Worker main entry point.
Starts RabbitMQ consumer for extraction jobs and scheduler for proactive caching.
"""
import signal
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.infrastructure.messaging.rabbitmq_service import get_rabbitmq_service
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from workers.tasks.extraction_task import handle_extraction_message
from workers.tasks.proactive_cache_task import run_proactive_caching_job, get_all_user_ids

# Setup logging
setup_logging(level="INFO", json_format=True)
logger = get_logger(__name__)


def start_extraction_worker() -> None:
    """Start RabbitMQ consumer for extraction jobs."""
    logger.info("Starting extraction worker...")
    
    rabbitmq = None
    try:
        rabbitmq = get_rabbitmq_service()
        
        # Try to connect (will raise if fails)
        if not rabbitmq._connected:
            connected = rabbitmq.connect(raise_on_error=True)
            if not connected:
                raise Exception("Failed to connect to RabbitMQ")
        
        # Start consuming messages
        rabbitmq.consume(
            callback=handle_extraction_message,
            queue=settings.RABBITMQ_QUEUE_NAME,
            auto_ack=False,
        )
    except KeyboardInterrupt:
        logger.info("Extraction worker stopped by user")
        if rabbitmq:
            try:
                rabbitmq.stop_consuming()
                rabbitmq.disconnect()
            except:
                pass
    except Exception as e:
        logger.error(f"Extraction worker error: {e}")
        logger.error("Make sure RabbitMQ is running and accessible")
        raise


def start_proactive_caching_scheduler() -> None:
    """Start scheduler for proactive caching jobs."""
    logger.info("Starting proactive caching scheduler...")
    
    scheduler = BlockingScheduler()
    
    # Schedule proactive caching job
    scheduler.add_job(
        func=lambda: asyncio.run(
            run_proactive_caching_job(get_all_user_ids())
        ),
        trigger=IntervalTrigger(
            seconds=settings.PROACTIVE_CACHE_INTERVAL_SECONDS
        ),
        id="proactive_cache_job",
        name="Proactive User Favorite Cache Update",
        replace_existing=True,
    )
    
    try:
        logger.info(
            f"Proactive caching scheduler started. "
            f"Interval: {settings.PROACTIVE_CACHE_INTERVAL_SECONDS}s"
        )
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Proactive caching scheduler stopped")
        scheduler.shutdown()


def signal_handler(sig, frame) -> None:
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    import asyncio
    
    # Start both workers
    # In production, these would run in separate processes/containers
    import threading
    
    # Start extraction worker in main thread
    extraction_thread = threading.Thread(target=start_extraction_worker, daemon=True)
    extraction_thread.start()
    
    # Start proactive caching scheduler in main thread
    start_proactive_caching_scheduler()

