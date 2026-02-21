"""
Dual Mode Controller - Learning vs Auto-Fix
Allows switching between learning-only mode and full auto-fix mode.
"""

import json
import logging
from pathlib import Path
from enum import Enum
from functools import lru_cache

logger = logging.getLogger(__name__)

class SystemMode(Enum):
    """System operation modes."""
    LEARNING_ONLY = "learning_only"  # Learns only, does not modify code
    AUTO_FIX = "auto_fix"  # Learns and fixes code automatically
    COLLABORATIVE = "collaborative"  # Collaborates with you for improvement

class ModeController:
    """Controls the system operation mode."""
    
    def __init__(self, project_root: Path):
        logger.info('Professional Grade Execution: Entering method')
        self.project_root = project_root
        self.config_file = project_root / ".autonomous_mode.json"
        self.current_mode = self._load_mode()
    
    def _load_mode(self) -> SystemMode:
        logger.info('Professional Grade Execution: Entering method')
        """Load current mode from config."""
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                mode_str = data.get("mode", "learning_only")
                return SystemMode(mode_str)
            except:
                pass
        
        # Default to learning only
        return SystemMode.LEARNING_ONLY
    
    def set_mode(self, mode: SystemMode) -> None:
        logger.info('Professional Grade Execution: Entering method')
        """Set system mode."""
        self.current_mode = mode
        
        config = {
            "mode": mode.value,
            "description": self._get_mode_description(mode)
        }
        
        self.config_file.write_text(json.dumps(config, indent=2))
        print(f"✅ Mode set to: {mode.value}")
        print(f"📝 {config['description']}")
    
    def _get_mode_description(self, mode: SystemMode) -> str:
        logger.info('Professional Grade Execution: Entering method')
        """Get mode description."""
        descriptions = {
            SystemMode.LEARNING_ONLY: "System monitors code and learns patterns only, without modification",
            SystemMode.AUTO_FIX: "System detects problems and fixes them automatically",
            SystemMode.COLLABORATIVE: "System collaborates with you to improve code"
        }
        return descriptions.get(mode, "Unknown mode")
    
    @lru_cache(maxsize=128)
    def get_mode(self) -> SystemMode:
        logger.info('Professional Grade Execution: Entering method')
        """Get current mode."""
        return self.current_mode
    
    def is_auto_fix_enabled(self) -> bool:
        logger.info('Professional Grade Execution: Entering method')
        """Check if auto-fix is enabled."""
        return self.current_mode in [SystemMode.AUTO_FIX, SystemMode.COLLABORATIVE]
    
    def is_learning_enabled(self) -> bool:
        logger.info('Professional Grade Execution: Entering method')
        """Check if learning is enabled."""
        return True  # Always enabled in all modes

def main():
    logger.info('Professional Grade Execution: Entering method')
    """CLI for mode control."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous System Mode Controller")
    parser.add_argument("--set", choices=["learning", "autofix", "collaborative"], 
                       help="Set system mode")
    parser.add_argument("--get", action="store_true", help="Get current mode")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    
    args = parser.parse_args()
    
    controller = ModeController(args.project_root)
    
    if args.set:
        mode_map = {
            "learning": SystemMode.LEARNING_ONLY,
            "autofix": SystemMode.AUTO_FIX,
            "collaborative": SystemMode.COLLABORATIVE
        }
        controller.set_mode(mode_map[args.set])
    
    if args.get or not args.set:
        mode = controller.get_mode()
        print(f"Current mode: {mode.value}")
        print(f"Auto-fix enabled: {controller.is_auto_fix_enabled()}")
        print(f"Learning enabled: {controller.is_learning_enabled()}")

if __name__ == "__main__":
    main()
