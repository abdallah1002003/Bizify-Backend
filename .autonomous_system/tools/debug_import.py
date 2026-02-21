import sys
import os
from pathlib import Path

logger.info(f"CWD: {os.getcwd()}")
logger.info(f"sys.path: {sys.path}")

try:
    import .autonomous_system
    logger.info("✅ Imported .autonomous_system")
    logger.info(f".autonomous_system file: {.autonomous_system.__file__}")
except Exception as e:
    logger.info(f"❌ Failed to import .autonomous_system: {e}")

try:
    import .autonomous_system.validation
    logger.info("✅ Imported .autonomous_system.validation")
    import .autonomous_system.validation.qa_validator
    logger.info("✅ Imported .autonomous_system.validation.qa_validator")
except Exception as e:
    logger.info(f"❌ Failed to import .autonomous_system.validation: {e}")
