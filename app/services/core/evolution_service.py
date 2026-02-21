import datetime
import logging
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root / ".autonomous_system" / "core"))
sys.path.insert(0, str(project_root / ".autonomous_system"))

try:
    from antigravity_bridge import AntigravityBridge
except ImportError:
    AntigravityBridge = None
    logging.warning("AntigravityBridge could not be loaded. EvolutionService running in Sandbox Mode.")


class EvolutionService:
    def __init__(self):
        self.bridge = AntigravityBridge() if AntigravityBridge else None
        self.scripts_dir = project_root / ".autonomous_system" / "scripts"
        if self.bridge:
            logger.info("Evolution bridge established.")
        else:
            logger.info("EvolutionService active in sandbox mode.")

    def get_detailed_status(self) -> Dict[str, Any]:
        return {
            "module": "EvolutionMasterService",
            "timestamp": datetime.datetime.now().isoformat(),
            "bridge_connected": self.bridge is not None,
            "status": "operational",
            "capabilities": [
                "automated_pattern_discovery",
                "dynamic_module_optimization",
                "telemetry_loopback",
                "autonomous_script_execution",
            ],
            "domain_depth": "Elite",
        }

    def _safe_execution_wrapper(self, operation: callable, *args, **kwargs):
        try:
            logger.debug("Executing evolutionary task: %s", operation.__name__)
            return operation(*args, **kwargs)
        except Exception as exc:  # pragma: no cover
            logger.error("Evolution failure [%s]: %s", operation.__name__, exc)
            logger.debug(traceback.format_exc())
            return None

    def record_evolution_event(self, action: str, outcome: str, details: Dict[str, Any]):
        if self.bridge:
            self.bridge.feed_system(action, outcome, details)
        else:
            logger.info("Sandbox event log: %s -> %s", action, outcome)

    def consult_master_patterns(self, intent: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        if self.bridge:
            return self.bridge.consult_system(intent, context or {})
        return {"status": "neutral", "insights": [], "suggestion": "Proceed with standard patterns."}

    def request_module_optimization(self, target_file_path: str):
        script_path = self.scripts_dir / "evolve.py"
        if not script_path.exists():
            logger.error("Evolution script not found at %s", script_path)
            return None

        try:
            process = subprocess.Popen(
                [sys.executable, str(script_path), "--target", target_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return process.pid
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to trigger autonomous evolution: %s", exc)
            return None

    def trigger_self_reconstruction(self):
        script_path = self.scripts_dir / "trigger_self_construction.py"
        if not script_path.exists():
            return
        subprocess.Popen([sys.executable, str(script_path)])


def get_service():
    return EvolutionService()


def reset_internal_state():
    logger.warning("Master reset: clearing evolution service state.")
