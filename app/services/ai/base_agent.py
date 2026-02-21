import logging
import abc
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.services.core.evolution_service import get_service as get_evolution_service

logger = logging.getLogger(__name__)

class BaseAgent(abc.ABC):
    """
    Elite Standard: Abstract Base Class for Supreme Agents.
    Provides standardized hooks for context injection, telemetry, and bridge communication.
    """
    
    def __init__(self, agent_id: UUID, name: str):
        self.agent_id = agent_id
        self.name = name
        self.evolution_service = get_evolution_service()
        logger.info(f"🤖 Agent {self.name} ({self.agent_id}) localized.")

    @abc.abstractmethod
    async def run(self, db: Session, target_id: UUID, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution loop for the agent.
        Must be implemented by all Supreme Agents.
        """
        pass

    def log_telemetry(self, action: str, outcome: str, details: Dict[str, Any]):
        """Standardized telemetry dispatch."""
        self.evolution_service.record_evolution_event(
            action=f"AGENT_{self.name}_{action}",
            outcome=outcome,
            details=details
        )
        logger.debug(f"📊 Telemetry logged for {self.name}: {action}")

    def consult_patterns(self, intent: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Direct access to the 133k+ autonomous patterns."""
        return self.evolution_service.consult_master_patterns(intent, context)

    def _safe_execute(self, func: callable, *args, **kwargs):
        """Internal safety wrapper for fragile AI operations."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"🚨 Agent {self.name} Internal Failure: {str(e)}")
            self.log_telemetry("EXECUTION_ERROR", "FAILED", {"error": str(e)})
            return None
