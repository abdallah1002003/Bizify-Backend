# ruff: noqa
import os
import sys
import json
import logging
import asyncio

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.structured_logging import setup_logging
from app.core.cache import get_cache_manager
from app.core.events import dispatcher
from app.core.event_handlers import register_all_handlers

setup_logging("worker")
logger = logging.getLogger("worker")

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
            result = redis_client.brpop(queue_key, timeout=5)
            if not result:
                continue
                
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

if __name__ == "__main__":
    try:
        asyncio.run(process_queue())
    except KeyboardInterrupt:
        logger.info("Worker shutting down gracefully...")
