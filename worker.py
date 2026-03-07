# ruff: noqa
import os
import sys
import json
import logging
import asyncio

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.structured_logging import configure_structured_logging
from app.core.cache import get_cache_manager
from app.core.events import dispatcher
from app.core.event_handlers import register_all_handlers
from app.db.database import AsyncSessionLocal
<<<<<<< HEAD
from app.services.core.cleanup_service import CleanupService
from app.services.core.email_worker import EmailWorkerService
=======
from app.services.core.cleanup_service import cleanup_all
from app.services.core.email_worker import run_email_worker
>>>>>>> origin/main

configure_structured_logging("INFO")
logger = logging.getLogger("worker")

_CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60  # 24 hours

async def _periodic_cleanup() -> None:
    """Background task: runs cleanup_all every 24 hours."""
    while True:
        await asyncio.sleep(_CLEANUP_INTERVAL_SECONDS)
        async with AsyncSessionLocal() as db:
            try:
<<<<<<< HEAD
                summary = await CleanupService(db).cleanup_all()
=======
                summary = await cleanup_all(db)
>>>>>>> origin/main
                logger.info("Periodic cleanup completed: %s", summary)
            except Exception:
                logger.exception("Periodic cleanup failed")

async def process_queue():
    """Main background loop to process the event queue."""
    logger.info("Initializing event handlers...")
    register_all_handlers()
    
    cache = get_cache_manager()
    if not hasattr(cache.backend, "client") or not cache.backend.client:
        logger.error("Worker requires an active Redis backend. Exiting.")
        sys.exit(1)
        
    redis_client = cache.backend.client
    queue_key = "app:event_queue"
    
    logger.info(f"Worker is starting and listening to Redis queue '{queue_key}'...")
    
    while True:
        try:
            # Block until an event is available or timeout after 5 seconds
<<<<<<< HEAD
            result = await redis_client.brpop(queue_key, timeout=5)
            if not result:
                continue
                
            # redis-py returns a tuple (key, value)
=======
            result = redis_client.brpop(queue_key, timeout=5)
            if not result:
                continue
                
>>>>>>> origin/main
            _, data_bytes = result
            
            try:
                event_data = json.loads(data_bytes)
                event_type = event_data.get("event_type")
                payload = event_data.get("payload")
                
                if not event_type:
                    logger.warning(f"Malformed event received: {event_data}")
                    continue
                    
                logger.info(f"Processing event: {event_type}")
                # Dispatch the event internally to registered async handlers
                await dispatcher._run_handlers(event_type, payload)
                
            except json.JSONDecodeError as decode_err:
                logger.error(f"Failed to parse event JSON data: {decode_err}")
            except Exception as e:
                logger.error(f"Error processing event payload: {e}")
                
        except Exception as queue_err:
            logger.error(f"Redis queue connection error: {queue_err}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

async def main():
    logger.info("Starting background worker with multiple tasks...")
    # Run the various tasks concurrently using gather
<<<<<<< HEAD
    email_service = EmailWorkerService(None) # type: ignore — loop creates its own sessions
    await asyncio.gather(
        process_queue(),
        email_service.run_email_worker(interval_seconds=10),
=======
    await asyncio.gather(
        process_queue(),
        run_email_worker(interval_seconds=10),
>>>>>>> origin/main
        _periodic_cleanup()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker shutting down gracefully...")
