"""
Organize Project via Master Orchestrator

Uses the MasterAutonomousOrchestrator to coordinate:
1. CompleteCleanupSystem (Clean root, organize tests)
2. OrganizationSystem (Fill templates, remove unused)

This ensures the entire autonomous system is aware of the changes.
"""

import asyncio
import sys
from pathlib import Path

# Add AUTONOMOUS_SYSTEM_COMPLETE to path
sys.path.insert(0, str(Path.cwd() / "AUTONOMOUS_SYSTEM_COMPLETE"))

from master_orchestrator import get_master_orchestrator

async def organize_all():
    print("🌟 STARTING AUTONOMOUS ORGANIZATION")
    print("="*70)
    
    # Initialize Master Orchestrator
    orchestrator = get_master_orchestrator()
    
    print("\n1️⃣  Running Complete Cleanup...")
    # Direct instantiation for guaranteed execution if orchestrator import fails
    try:
        if hasattr(orchestrator, 'cleanup') and orchestrator.cleanup:
            orchestrator.cleanup.run_complete_cleanup()
        else:
            from complete_cleanup import CompleteCleanupSystem
            cleanup = CompleteCleanupSystem(Path.cwd())
            cleanup.run_complete_cleanup()
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        
    print("\n2️⃣  Running Organization System...")
    try:
        if hasattr(orchestrator, 'organizer') and orchestrator.organizer:
            orchestrator.organizer.run_complete_cleanup()
        else:
            from organization_system import OrganizationSystem
            organizer = OrganizationSystem(Path.cwd())
            organizer.run_complete_cleanup()
    except Exception as e:
        print(f"❌ Organization failed: {e}")
        
    print("\n✅ ORGANIZATION COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(organize_all())
