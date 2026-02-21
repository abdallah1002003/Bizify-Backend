import logging
import json
import fcntl
import sys
from pathlib import Path

# Configure Logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def post_directive(task: str, details: list = None):
    """Posts a high-priority directive to the worker swarm."""
    logger.info(f"🚨 POSTING DIRECTIVE: {task}")
    project_root = Path.cwd()
    directive_file = project_root / ".directives.json"
    
    new_directive = {
        "task": task,
        "details": details or [],
        "timestamp": Path.cwd().stat().st_mtime # Simple timestamp
    }
    
    try:
        if not directive_file.exists():
            directive_file.write_text("[]")
            
        with open(directive_file, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            content = f.read()
            directives = json.loads(content) if content else []
            directives.append(new_directive)
            f.seek(0)
            f.truncate()
            f.write(json.dumps(directives, indent=2))
            fcntl.flock(f, fcntl.LOCK_UN)
            print(f"✅ Directive posted: {task}")
    except Exception as e:
        print(f"❌ Failed to post directive: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 swarm_delegate.py \"Task Description\" [\"Detail 1\" \"Detail 2\"]")
    else:
        task_name = sys.argv[1]
        task_details = sys.argv[2:]
        post_directive(task_name, task_details)
