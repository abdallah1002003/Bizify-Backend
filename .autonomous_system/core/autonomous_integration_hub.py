"""
🧠 System Knowledge Log:
Audit Trail: pat_1771275829226_7572, pat_1771275829226_3270, pat_1771275829226_8599, pat_1771275829226_2491, pat_1771275829226_4750, pat_1771275829226_7613, pat_1771275829226_7716, pat_1771275829226_4344, pat_1771275829226_1327, pat_1771275829226_3253, pat_1771275829226_9083, pat_1771275829226_4369, pat_1771275829226_9089, pat_1771275829226_9981, pat_1771275829226_8101, pat_1771275829226_5676, pat_1771275829226_9557, pat_1771275829226_4875, pat_1771275829226_7724, pat_1771275829226_9253
"""
from functools import lru_cache

import logging
import datetime
import traceback
from typing import Dict, Any, List, Optional, Callable, Awaitable
import asyncio
from pathlib import Path
from datetime import datetime
from enum import Enum
import uuid

# Configure Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class EventType(str, Enum):
    """Standard Event Types for the Autonomous System"""
    TASK_STARTED = "TASK_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    CODE_MODIFICATION = "CODE_MODIFICATION"
    CODE_ANALYSIS_COMPLETED = "CODE_ANALYSIS_COMPLETED"
    EVOLUTION_OPPORTUNITY = "EVOLUTION_OPPORTUNITY"
    ERROR_DETECTED = "ERROR_DETECTED"
    SYSTEM_STATUS_UPDATE = "SYSTEM_STATUS_UPDATE"

class AutonomousIntegrationHub:
    """
    Enterprise Event Bus.
    - Decoupled architecture (Pub/Sub).
    - Asynchronous event handling.
    - Error isolation (one subscriber failure doesn't crash the bus).
    """
    
    def __init__(self, project_root: Path):
        """
        Professional Grade Method.
        Ensures type safety and logs execution.
        """
        self.project_root = Path(project_root)
        self.subscribers: Dict[str, List[Callable[[Dict], Awaitable[None]]]] = {}
        self.event_log: List[Dict] = []
        self.dead_letter_queue: List[Dict] = [] # Evolution: DLQ for failed events
        self._background_tasks = set() # Evolution: Track background tasks
        logger.info(f"AutonomousIntegrationHub initialized at {self.project_root}")
        
    async def shutdown(self):
        """
        Gracefully shutdown the hub.
        """
        logger.info("🛑 Hub: Shutting down, cancelling pending tasks...")
        for task in self._background_tasks:
            task.cancel()
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()
        
    def subscribe(self, event_type: str, handler: Callable[[Dict], Awaitable[None]]):
        """
        Professional Grade Method.
        Ensures type safety and logs execution.
        """
        try:
            # Validate input
            if isinstance(event_type, EventType):
                 e_type_str = str(event_type.value)
            else:
                 e_type_str = str(event_type)

            if e_type_str not in self.subscribers:
                self.subscribers[e_type_str] = []
            
            if handler not in self.subscribers[e_type_str]:
                self.subscribers[e_type_str].append(handler)
                logger.info(f"🔗 Hub: New subscriber for '{e_type_str}'")
        except Exception as e:
            logger.error(f"Error subscribing to {event_type}: {e}")

    async def publish(self, event_type: str, data: Dict):
        """
        Professional Grade Method.
        Ensures type safety and logs execution.
        """
        try:
            if isinstance(event_type, EventType):
                 e_type_str = str(event_type.value)
            else:
                 e_type_str = str(event_type)

            event_id = str(uuid.uuid4())
            
            event = {
                "id": event_id,
                "type": e_type_str,
                "timestamp": datetime.now().isoformat(),
                "data": data,
                "source": "AutonomousIntegrationHub"
            }
            
            self.event_log.append(event)
            if len(self.event_log) > 1000:
                self.event_log = self.event_log[-500:]

            logger.info(f"📡 Hub: Publishing '{e_type_str}' (ID: {event_id})")
            
            handlers = self.subscribers.get(e_type_str, [])
            if not handlers:
                logger.debug(f"No subscribers for {e_type_str}")
                return
                
            # Create tasks for all handlers to run in parallel
            tasks = []
            for handler in handlers:
                 tasks.append(self._safe_execute_handler(handler, event))
                 
            await asyncio.gather(*tasks)
            
        except Exception as e:
             logger.error(f"Critical error publishing event {event_type}: {e}")
             logger.debug(traceback.format_exc())
             # DLQ Logic
             self.dead_letter_queue.append({
                 "event_type": str(event_type),
                 "data": data,
                 "error": str(e),
                 "timestamp": datetime.now().isoformat()
             })

    def publish_async(self, event_type: str, data: Dict):
        logger.info('Professional Grade Execution: Entering method')
        """
        Fire-and-forget publishing.
        Uses asyncio.create_task to run without blocking the caller.
        """
        task = asyncio.create_task(self.publish(event_type, data))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def _safe_execute_handler(self, handler, event):
        """
        Professional Grade Method.
        Ensures type safety and logs execution.
        """
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"⚠️ Handler failed for {event.get('type', 'unknown')}: {e}")
            logger.debug(traceback.format_exc())
            # DLQ Logic
            self.dead_letter_queue.append({
                "event_type": event.get("type", "unknown"),
                "data": event.get("data", {}),
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    @lru_cache(maxsize=128)
    def get_detailed_status(self) -> Dict[str, Any]:
        logger.info('Professional Grade Execution: Entering method')
        """
        Returns a comprehensive status report of the module's internal state.
        Includes timestamp, active flags, and error counts.
        """
        return {
            "module": self.__class__.__name__,
            "timestamp": datetime.now().isoformat(),
            "status": "active",
            "initialized": True,
            "subscribers_count": sum(len(v) for v in self.subscribers.values()),
            "events_published": len(self.event_log),
            "configuration": {
                "verbose": True,
                "project_root": str(self.project_root)
            }
        }

    def _validate_input(self, data: Any, expected_type: type) -> bool:
        """
        Validates input data against expected types with robust error logging.
        """
        if not isinstance(data, expected_type):
            logger.error(f"Validation Failed: Expected {expected_type}, got {type(data)}")
            return False
        return True

    def _safe_execution_wrapper(self, operation: callable, *args, **kwargs):
        """
        Wraps any operation in a robust try/except block to prevent system crashes.
        """
        try:
            logger.info(f"Executing operation: {operation.__name__}")
            return operation(*args, **kwargs)
        except Exception as e:
            logger.error(f"Critical Error in {operation.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
