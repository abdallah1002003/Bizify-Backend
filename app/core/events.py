import logging
import asyncio
from typing import Any, Callable, Dict, List, Coroutine

logger = logging.getLogger(__name__)

# Type definition for event handlers
EventHandler = Callable[[str, Any], Coroutine[Any, Any, None]]

class EventDispatcher:
    """A simple internal event dispatcher for decoupling services."""

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}

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
        """Emit an event to all subscribed handlers."""
        if event_type not in self._handlers:
            return

        logger.info(f"Emitting event: {event_type}")
        
        # In a real-world scenario, you might want to run these concurrently or in background tasks
        tasks = []
        for handler in self._handlers.get(event_type, []):
            tasks.append(handler(event_type, payload))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

# Global singleton for application-wide event dispatching
dispatcher = EventDispatcher()
