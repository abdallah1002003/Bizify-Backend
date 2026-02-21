"""
🧠 System Knowledge Log:
Audit Trail: pat_1771275829226_7572, pat_1771275829226_3270, pat_1771275829226_8599, pat_1771275829226_2491, pat_1771275829226_4750, pat_1771275829226_7613, pat_1771275829226_7716, pat_1771275829226_4344, pat_1771275829226_1327, pat_1771275829226_3253
"""
#!/usr/bin/env python3
"""
🚀 RUN FULL AUTONOMOUS SYSTEM
Runs everything: Monitoring + Meta-Evolution + Learning

This combines:
- Autonomous Monitor (detects incomplete work)
- Meta-Evolution (self-improvement)
- Real-time Learning (saves everything)
"""

import asyncio
import time
import sys
import argparse
from pathlib import Path

# Add project root and .autonomous_system to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
autonomous_system_root = project_root / ".autonomous_system"
sys.path.insert(0, str(autonomous_system_root))
sys.path.insert(0, str(project_root))

try:
    from core.autonomous_monitor import AutonomousMonitor
    from evolution.meta_evolution_system import MetaEvolutionSystem
except ImportError:
    # Fallback for different directory structures if needed
    print("⚠️  Could not import directly, trying alternative path structure...")
    sys.path.append(str(autonomous_system_root))
    from core.autonomous_monitor import AutonomousMonitor
    from evolution.meta_evolution_system import MetaEvolutionSystem

async def run_full_autonomous_system(continuous=False, interval=60):
    """
    Run complete autonomous system!
    """
    print("\n" + "=" * 70)
    print("🚀 FULL AUTONOMOUS SYSTEM - STARTING")
    print("=" * 70)
    print()
    print("🤖 Systems Loading:")
    print("  1. ✅ Autonomous Monitor - Detects incomplete work")
    print("  2. ✅ Meta-Evolution - Self-improvement")
    print("  3. ✅ Real-time Learning - Knowledge logging")
    print()
    print("=" * 70)
    print()
    
    project_root = Path.cwd()
    
    # Initialize systems
    monitor = AutonomousMonitor(project_root)
    evolution = MetaEvolutionSystem(project_root)
    
    print("🌟 All systems initialized!")
    print()

    while True:
        # Phase 1: Meta-Evolution (Self-Improvement)
        print("=" * 70)
        print("🌟 PHASE 1: META-EVOLUTION (Self-Improvement)")
        print("=" * 70)
        print()
        
        try:
            analysis = evolution.evolution_cycle()
            
            print(f"\n✅ Meta-Evolution Complete!")
            if hasattr(evolution, 'state'):
                 print(f"   Efficiency: {evolution.state.get('current_efficiency', 0):.1f}%")
                 print(f"   Requests sent: {evolution.state.get('improvements_requested', 0)}")
        except Exception as e:
            print(f"❌ Error in Meta-Evolution: {e}")
        print()
        
        time.sleep(2)
        
        # Phase 2: Autonomous Monitoring (Code Quality)
        print("=" * 70)
        print("🔄 PHASE 2: AUTONOMOUS MONITORING (Code Quality)")
        print("=" * 70)
        print()
        
        print("Running monitoring cycle...")
        print()
        
        try:
            # Run a single monitoring cycle, or appropriate number
            monitor.monitor_loop(max_cycles=1, wait_seconds=5) 
            
            print(f"   Task Requests Sent: {monitor.state.get('requests_sent', 0)}")
            print(f"   Status: {monitor.state.get('status', 'unknown')}")
        except Exception as e:
            print(f"❌ Error in Autonomous Monitor: {e}")
        
        print()
        
        # Final Summary for this loop iteration
        print("=" * 70)
        print("🎉 CYCLE COMPLETE!")
        print("=" * 70)
        print()
        
        if not continuous:
            break
            
        print(f"waiting {interval} seconds before next cycle...")
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Full Autonomous System")
    parser.add_argument("--continuous", action="store_true", help="Run continuously in a loop")
    parser.add_argument("--interval", type=int, default=300, help="Interval between cycles in seconds")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    
    args = parser.parse_args()

    print("\n🤖 FULL AUTONOMOUS SYSTEM")
    print()
    
    if not args.force:
        # Confirm, but default to yes if non-interactive env or args provided
        # actually, let's keep it simple: if --force not provided, ask. 
        # But for the user request "make it start working", we will use --force in the shell script.
        pass
        # We removed the input for now to ensure automation, or assume args are used.
        # If run manually without args, it will just run once.
    
    # Run!
    try:
        asyncio.run(run_full_autonomous_system(continuous=args.continuous, interval=args.interval))
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
