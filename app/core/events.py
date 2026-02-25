# type: ignore
import logging
import asyncio
import json
from uuid import UUID
from typing import Any, Callable, Dict, List, Coroutine

from config.settings import settings
from app.core.cache import get_cache_manager

logger = logging.getLogger(__name__)

# Type definition for event handlers
EventHandler = Callable[[str, Any], Coroutine[Any, Any, None]]

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON Encoder to handle UUIDs and Datetimes in event payloads."""
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return super().default(obj)

class EventDispatcher:
    """A simple internal event dispatcher for decoupling services.
    
    Supports pushing events to a Redis queue for background worker processing,
    with an automatic fallback to synchronous execution for tests.
    """

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self.queue_key = "app:event_queue"

    def subscribe(self, event_type: str, handler: EventHandler):
        """Subscribe a handler to an event type. Prevents duplicate subscriptions."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug(f"Subscribed handler {getattr(handler, '__name__', str(handler))} to event {event_type}")

    def clear_all_handlers(self):
        """Clear all registered handlers. Useful for test cleanup."""
        self._handlers = {}
        logger.debug("Cleared all event handlers")

    async def emit(self, event_type: str, payload: Any):
        """Emit an event to the background queue, or straight to handlers if testing."""
        logger.info(f"Emitting event: {event_type}")
        
        if settings.APP_ENV == "test":
            await self._run_handlers(event_type, payload)
            return

        cache = get_cache_manager()
        # Enqueue to Redis
        if hasattr(cache.backend, "client") and cache.backend.client:
            try:
                event_data = {
                    "event_type": event_type,
                    "payload": payload
                }
                encoded = json.dumps(event_data, cls=CustomJSONEncoder)
                cache.backend.client.lpush(self.queue_key, encoded)
                return
            except Exception as e:
                logger.error(f"Failed to push event {event_type} to Redis queue: {e}. Falling back to inline execution.")
        
        # Fallback to immediate execution if Redis is unavailable or we hit an error
        await self._run_handlers(event_type, payload)

    async def _run_handlers(self, event_type: str, payload: Any):
        """Run handlers immediately (used by test environment and worker)."""
        if event_type not in self._handlers:
            return

        tasks = []
        for handler in self._handlers.get(event_type, []):
            tasks.append(handler(event_type, payload))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

# Global singleton for application-wide event dispatching
dispatcher = EventDispatcher()
