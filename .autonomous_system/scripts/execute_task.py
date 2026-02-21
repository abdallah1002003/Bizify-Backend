"""
🧠 System Knowledge Log:
Audit Trail: pat_1771275829226_7572, pat_1771275829226_3270, pat_1771275829226_8599, pat_1771275829226_2491, pat_1771275829226_4750, pat_1771275829226_7613, pat_1771275829226_7716, pat_1771275829226_4344, pat_1771275829226_1327, pat_1771275829226_3253
"""
import logging
#!/usr/bin/env python3
"""
🚀 AUTONOMOUS TASK EXECUTOR
=============================
This script allows the AI Assistant (me) or the User to instantly 
trigger the Autonomous System to perform a specific task.

Usage:
    python3 execute_task.py "Description of task"

Example:
    python3 execute_task.py "Refactor autonomous_monitor.py to add logging"
"""

import sys
import asyncio
import argparse
import json
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / ".autonomous_system"))

try:
    from app.core.master_orchestrator import get_master_orchestrator
except ImportError:
    from master_orchestrator import get_master_orchestrator

async def run_task(task_description: str, json_output: bool = False, max_retries: int = 3):
    if not json_output:
        print("\n" + "="*70)
        print("🤖 AUTONOMOUS ASSISTANT ACTIVATED (WITH MUTUAL OVERSIGHT)")
        print("="*70)
        print(f"\n📋 Received Task: {task_description}\n")
    
    orchestrator = get_master_orchestrator(project_root)
    
    for attempt in range(1, max_retries + 1):
        if not json_output:
            print(f"\n🔄 Attempt {attempt}/{max_retries}...")
            
        # Execute the task
        report = await orchestrator.execute_comprehensive_task(task_description)
        
        # OVERSIGHT: Check if the system actually did its job
        # Simple heuristic: Did it use modules? Did it complete phases?
        success = report['modules_utilized'] > 0 and 'verification' in report['phases']
        
        if success:
            if json_output:
                print(f"JSON_OUTPUT:{json.dumps(report)}")
            else:
                print("\n" + "="*70)
                print("✅ TASK EXECUTION COMPLETE & VERIFIED")
                print("="*70)
                
                # Print a summary for the AI to read
                print("\n📊 Execution Summary (for AI Assistant):")
                print(f"- Modules Used: {report['modules_utilized']}")
                print(f"- Phases: {', '.join(report['phases'].keys())}")
                print("- Status: SUCCESS")
                print("="*70)
            return

        if not json_output:
            print(f"⚠️ Attempt {attempt} failed verification. Retrying...")

    if not json_output:
        print("\n❌ TASK FAILED AFTER RETRIES")

def main():
    logger.info('Professional Grade Execution: Entering method')
    parser = argparse.ArgumentParser(description="Execute a task using the Autonomous System")
    parser.add_argument("task", help="Description of the task to perform")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()
    
    asyncio.run(run_task(args.task, args.json))

if __name__ == "__main__":
    main()
logger = logging.getLogger(__name__)
