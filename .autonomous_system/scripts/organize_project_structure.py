#!/usr/bin/env python3
"""
Project Organizer - The Final Cleanup
Organizes the root directory into a standard professional structure.
"""
import os
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("ProjectOrganizer")

ROOT_DIR = Path.cwd()
APP_DIR = ROOT_DIR / "app"
SCRIPTS_DIR = ROOT_DIR / "scripts"
TESTS_DIR = ROOT_DIR / "tests"
DOCS_DIR = ROOT_DIR / "docs"
CONFIG_DIR = ROOT_DIR / "config"

# Define destination rules
# Pattern: Destination
RULES = {
    "run_*.py": SCRIPTS_DIR,
    "setup_*.py": SCRIPTS_DIR,
    "test_*.py": TESTS_DIR,
    "*_test.py": TESTS_DIR,
    "*.md": DOCS_DIR,
    "*.txt": DOCS_DIR,
    "*.ini": CONFIG_DIR,
    "*.toml": CONFIG_DIR,
    "*.yaml": CONFIG_DIR,
    "*.json": CONFIG_DIR,
    ".env*": CONFIG_DIR,
}

# Exemptions (Files to keep in root)
EXEMPT = [
    "main.py",
    "requirements.txt",
    "Dockerfile",
    ".gitignore",
    "organize_project_structure.py", # Self-exemption
    "README.md" # Usually good to keep README in root
]

def create_structure():
    """Creates necessary directories."""
    for d in [APP_DIR, SCRIPTS_DIR, TESTS_DIR, DOCS_DIR, CONFIG_DIR]:
        d.mkdir(exist_ok=True)
        logger.info(f"✅ Ensure directory exists: {d.name}/")
        
    # App structure
    (APP_DIR / "api").mkdir(exist_ok=True)
    (APP_DIR / "core").mkdir(exist_ok=True)
    (APP_DIR / "db").mkdir(exist_ok=True)
    (APP_DIR / "services").mkdir(exist_ok=True)

def move_file(file: Path, dest_dir: Path):
    """Safely moves a file."""
    if file.name in EXEMPT:
        return
        
    try:
        dest = dest_dir / file.name
        if dest.exists():
            # Handle collision
            timestamp = int(os.path.getmtime(file))
            dest = dest_dir / f"{file.stem}_{timestamp}{file.suffix}"
            
        shutil.move(str(file), str(dest))
        logger.info(f"🚚 Moved {file.name} -> {dest_dir.name}/")
    except Exception as e:
        logger.error(f"❌ Failed to move {file.name}: {e}")

def organize_root():
    """Scans and organizes root directory."""
    logger.info("🧹 Starting Project Organization...")
    
    # 1. Process Rules
    for pattern, dest in RULES.items():
        for file in ROOT_DIR.glob(pattern):
            if file.is_file() and not file.name.startswith("."): # Skip hidden files (except .env)
                move_file(file, dest)
            elif file.is_file() and pattern.startswith("."): # Specific handling for hidden config files
                move_file(file, dest)

    # 2. Smart Python File Sorting
    # Move loose python files (that aren't scripts/tests/main) to app/ or scripts/
    for file in ROOT_DIR.glob("*.py"):
        if file.name in EXEMPT or file.name in ["manage.py", "wsgi.py"]:
            continue
            
        # Heuristics
        content = file.read_text()
        if "FastAPI" in content or "APIRouter" in content:
            move_file(file, APP_DIR / "api")
        elif "BaseModel" in content:
            move_file(file, APP_DIR / "db") # Likely a schema/model
        elif "sqlalchemy" in content:
            move_file(file, APP_DIR / "db")
        else:
            # Default to scripts if unsure
            move_file(file, SCRIPTS_DIR)

    logger.info("✨ Organization Complete!")

if __name__ == "__main__":
    create_structure()
    organize_root()
