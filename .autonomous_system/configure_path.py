import sys
from pathlib import Path

# Add the hidden .autonomous_system to python path so it can be imported as a module
sys.path.insert(0, str(Path(__file__).resolve().parent / ".autonomous_system"))

logger.info("✅ System Path Configured for Hidden Autonomous System")
