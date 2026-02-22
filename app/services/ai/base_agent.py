import logging
import abc
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class BaseAgent(abc.ABC):
    """
    Abstract base class for AI agents.
    Provides standardized hooks for context injection and telemetry.
    """
    
    def __init__(self, agent_id: UUID, name: str):
        self.agent_id = agent_id
        self.name = name
        logger.info("Agent %s (%s) initialized.", self.name, self.agent_id)

    @abc.abstractmethod
    async def run(self, db: Session, target_id: UUID, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution loop for the agent.
        Must be implemented by agent subclasses.
        """
        pass

    def log_telemetry(self, action: str, outcome: str, details: Dict[str, Any]):
        """Standardized telemetry logging."""
        logger.info(
            "agent_telemetry agent=%s action=%s outcome=%s details=%s",
            self.name,
            action,
            outcome,
            details,
        )

    def consult_patterns(self, intent: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Backward-compatible helper for agent guidance.
        Returns a neutral in-process response.
        """
        _ = context
        return {"status": "neutral", "intent": intent, "insights": []}

    def _safe_execute(self, func: callable, *args, **kwargs):
        """Internal safety wrapper for fragile AI operations."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error("Agent %s internal failure: %s", self.name, str(e))
            self.log_telemetry("EXECUTION_ERROR", "FAILED", {"error": str(e)})
            return None
