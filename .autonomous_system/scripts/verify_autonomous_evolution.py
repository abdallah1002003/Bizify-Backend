"""
🧠 System Knowledge Log:
Audit Trail: pat_1771275829226_7572, pat_1771275829226_3270, pat_1771275829226_8599, pat_1771275829226_2491, pat_1771275829226_4750, pat_1771275829226_7613, pat_1771275829226_7716, pat_1771275829226_4344, pat_1771275829226_1327, pat_1771275829226_3253
"""
import asyncio
import sys
from pathlib import Path

# Add project root and .autonomous_system to path
# Add project root and .autonomous_system to path
# Adjust for script location (p7/.autonomous_system/scripts/ -> p7/)
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / ".autonomous_system"))

from master_orchestrator import MasterAutonomousOrchestrator
from autonomous_integration_hub import EventType

async def verify_system():
    # 1. Setup Test Subject
    test_subject = project_root / ".autonomous_system/tests/test_subject_v1.py"
    test_subject.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a file missing docstrings
    test_subject.write_text("""
def calculate_sum(a, b):
    return a + b

class MathOperations:
    def multiply(self, a, b):
        return a * b
""")
    
    print(f"📄 Created test subject: {test_subject}")
    print("   [Initial Content]:")
    print(test_subject.read_text())
    
    # 2. Run Orchestrator
    orchestrator = MasterAutonomousOrchestrator(project_root)
    
    # Manually trigger evolution on this file for the test
    # (Since the full orchestrator runs on everything, we want to focus)
    if hasattr(orchestrator, 'self_evolution') and orchestrator.self_evolution:
        print("\n🧬 Triggering Self-Evolution...")
        result = orchestrator.self_evolution.evolve(test_subject)
        print(f"   Result: {result}")
        
    # 3. Verify Changes
    print("\n🔍 Verifying Changes...")
    new_content = test_subject.read_text()
    print("   [New Content]:")
    print(new_content)
    
    if '"""' in new_content and "TODO: Add docstring" in new_content:
        print("\n✅ SUCCESS: Docstrings were added!")
    else:
        print("\n❌ FAILURE: Docstrings were NOT added.")

if __name__ == "__main__":
    asyncio.run(verify_system())
