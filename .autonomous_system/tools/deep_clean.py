#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

# Import needed modules - handling potential missing modules gracefully
try:
    from evolution.self_refactor import AutoSurgeon
except ImportError:
    # If self_refactor isn't available, we'll proceed with basic cleaning
    AutoSurgeon = None

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def project_deep_clean():
    """Executes Phase 42 Super-Cleaner on all Python files."""
    logger.info("🧹 Starting Project-Wide Deep Clean (Phase 42)...")
    
    python_files = list(root.rglob("*.py"))
    clean_count = 0
    
    for file_path in python_files:
        if ".gemini" in str(file_path) or "venv" in str(file_path) or "__pycache__" in str(file_path):
            continue
            
        try:
            surgeon = AutoSurgeon(file_path)
            surgeon.beauty_pass()
            clean_count += 1
        except Exception as e:
            logger.info(f"❌ Error cleaning {file_path}: {e}")
            
    logger.info(f"✨ Deep Clean Complete! Sanitized {clean_count} files.")

if __name__ == "__main__":
    project_deep_clean()
