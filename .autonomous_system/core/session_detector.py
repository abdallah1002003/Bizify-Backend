"""
Session Detector - Detects if Antigravity is actively working
"""
import logging
from pathlib import Path
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class AntigravitySessionDetector:
    """Detects if an Antigravity collaborative session is active."""
    
    def __init__(self, project_root: Path):
        """
        Initialize the session detector.
        
        Args:
            project_root: Root directory of the project
        """
        logger.info('Professional Grade Execution: Entering method')
        self.project_root = Path(project_root)
        self.session_file = self.project_root / ".antigravity_session_active"
        self.session_timeout = 300  # 5 minutes in seconds
    
    def is_antigravity_active(self) -> bool:
        """
        Check if Antigravity session is currently active.
        
        Returns:
            True if an active session exists, False otherwise
        """
        logger.info('Professional Grade Execution: Entering method')
        
        if not self.session_file.exists():
            logger.debug("No session file found")
            return False
        
        # Check if session file is recent (not stale)
        try:
            file_age = time.time() - self.session_file.stat().st_mtime
            if file_age > self.session_timeout:
                logger.warning(f"⚠️ Stale session file detected (age: {file_age:.0f}s), removing...")
                self.session_file.unlink()
                return False
            
            logger.debug(f"✅ Active session detected (age: {file_age:.0f}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error checking session file: {e}")
            return False
    
    def mark_session_active(self):
        """
        Mark that Antigravity session is active.
        Creates or updates the session marker file.
        """
        logger.info('Professional Grade Execution: Entering method')
        try:
            self.session_file.write_text(f"{time.time()}")
            logger.info("✅ Antigravity session marked as active")
        except Exception as e:
            logger.error(f"Failed to mark session: {e}")
    
    def mark_session_inactive(self):
        """
        Mark that Antigravity session ended.
        Removes the session marker file.
        """
        logger.info('Professional Grade Execution: Entering method')
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                logger.info("✅ Antigravity session marked as inactive")
            else:
                logger.debug("No session file to remove")
        except Exception as e:
            logger.error(f"Failed to remove session marker: {e}")
    
    def refresh_session(self):
        """
        Refresh session timestamp to keep it alive.
        Should be called periodically during active sessions.
        """
        logger.info('Professional Grade Execution: Entering method')
        if self.session_file.exists():
            self.mark_session_active()
            logger.debug("Session timestamp refreshed")
        else:
            logger.warning("Cannot refresh - no active session")

# CLI for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python session_detector.py [check|start|stop|refresh]")
        sys.exit(1)
    
    detector = AntigravitySessionDetector(Path.cwd())
    command = sys.argv[1]
    
    if command == "check":
        active = detector.is_antigravity_active()
        print(f"Antigravity session active: {active}")
    elif command == "start":
        detector.mark_session_active()
        print("Session started")
    elif command == "stop":
        detector.mark_session_inactive()
        print("Session stopped")
    elif command == "refresh":
        detector.refresh_session()
        print("Session refreshed")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
