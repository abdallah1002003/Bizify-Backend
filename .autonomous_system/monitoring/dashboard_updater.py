import logging
from functools import lru_cache
"""
Live Dashboard Updater
Updates LIVE_DASHBOARD.md with comprehensive real-time metrics.
"""

import json
import time
import psutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess

class DashboardUpdater:
    """Updates the live dashboard with system and worker metrics."""
    
    def __init__(self, project_root: Path):
        logger.info('Professional Grade Execution: Entering method')
        self.project_root = project_root
        self.dashboard_path = project_root / "LIVE_DASHBOARD.md"
        self.workers_file = project_root / ".workers.json"
        self.orchestrator_state = project_root / ".workers_state.json"
        self.knowledge_file = project_root / ".autonomous_system" / "knowledge" / "learned_patterns.json"
        
    @lru_cache(maxsize=128)
    def get_orchestrator_status(self) -> Dict[str, Any]:
        logger.info('Professional Grade Execution: Entering method')
        """Get orchestrator status if running."""
        if not self.orchestrator_state.exists():
            return None
        
        try:
            data = json.loads(self.orchestrator_state.read_text())
            return {
                "pid": data.get("orchestrator_pid"),
                "managed_workers": data.get("worker_count", 0),
                "workers": data.get("workers", {})
            }
        except:
            return None
    
    @lru_cache(maxsize=128)
    def get_worker_metrics(self) -> List[Dict[str, Any]]:
        logger.info('Professional Grade Execution: Entering method')
        """Get detailed metrics for all workers."""
        if not self.workers_file.exists():
            return []
        
        try:
            workers_data = json.loads(self.workers_file.read_text())
            metrics = []
            
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            for worker_id, data in workers_data.items():
                pid = data.get("pid")
                
                # Get process info
                try:
                    proc = psutil.Process(pid)
                    cpu = proc.cpu_percent(interval=0.1)
                    mem = proc.memory_info().rss / 1024 / 1024  # MB
                    status = "🟢 Running"
                except psutil.NoSuchProcess:
                    cpu = 0
                    mem = 0
                    status = "🔴 Dead"
                
                metrics.append({
                    "id": worker_id,
                    "pid": pid,
                    "focus": data.get("current_focus", "Idle"),
                    "cpu": cpu,
                    "memory_mb": mem,
                    "status": status,
                    "heartbeat": data.get("last_heartbeat", 0)
                })
            
            return metrics
        except:
            return []
    
    @lru_cache(maxsize=128)
    def get_knowledge_stats(self) -> Dict[str, int]:
        logger.info('Professional Grade Execution: Entering method')
        """Get knowledge base statistics."""
        try:
            if self.knowledge_file.exists():
                data = json.loads(self.knowledge_file.read_text())
                return {
                    "total_patterns": len(data.get("success_patterns", [])),
                    "mutations": data.get("total_mutations", 0)
                }
        except:
            pass
        
        return {"total_patterns": 0, "mutations": 0}
    
    @lru_cache(maxsize=128)
    def get_system_metrics(self) -> Dict[str, Any]:
        logger.info('Professional Grade Execution: Entering method')
        """Get system-wide metrics."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used_gb": psutil.virtual_memory().used / 1024 / 1024 / 1024,
            "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
            "disk_percent": psutil.disk_usage(str(self.project_root)).percent
        }
    
    @lru_cache(maxsize=128)
    def get_recent_changes(self, limit: int = 10) -> List[Dict[str, str]]:
        logger.info('Professional Grade Execution: Entering method')
        """Get recent file changes from git."""
        try:
            result = subprocess.run(
                ["git", "log", f"-{limit}", "--pretty=format:%h|%ar|%s", "--name-only"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                changes = []
                
                i = 0
                while i < len(lines) and len(changes) < limit:
                    if '|' in lines[i]:
                        parts = lines[i].split('|')
                        if len(parts) == 3:
                            changes.append({
                                "hash": parts[0],
                                "time": parts[1],
                                "message": parts[2]
                            })
                    i += 1
                
                return changes
        except:
            pass
        
        return []
    
    @lru_cache(maxsize=128)
    def get_active_mutations(self) -> List[str]:
        logger.info('Professional Grade Execution: Entering method')
        """Get list of files currently being mutated."""
        mutations = []
        
        # Check for .mutation_lock files
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for lock_file in self.project_root.rglob("*.mutation_lock"):
            try:
                data = json.loads(lock_file.read_text())
                mutations.append(f"{data.get('file', 'unknown')} (by {data.get('worker', 'unknown')})")
            except:
                pass
        
        return mutations
    
    def update_dashboard(self) -> None:
        logger.info('Professional Grade Execution: Entering method')
        """Update the live dashboard with all metrics."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Get all data
        orchestrator = self.get_orchestrator_status()
        workers = self.get_worker_metrics()
        knowledge = self.get_knowledge_stats()
        system = self.get_system_metrics()
        changes = self.get_recent_changes(5)
        mutations = self.get_active_mutations()
        
        # Build dashboard content
        content = f"""# 🧠 Autonomous System Live Dashboard
**Status**: {'🟢 Worker Swarm Active' if workers else '🔴 No Workers'} ({len(workers)} Workers)
**Last Update**: {timestamp}

---

## 📊 System Metrics
- **CPU Usage**: {system['cpu_percent']:.1f}%
- **Memory**: {system['memory_used_gb']:.1f}GB / {system['memory_total_gb']:.1f}GB ({system['memory_percent']:.1f}%)
- **Disk Usage**: {system['disk_percent']:.1f}%

---

## 🧠 Knowledge Base
- **Total Patterns**: {knowledge['total_patterns']:,} verified items 💎
- **Verified Mutations**: {knowledge['mutations']:,} successful 🛡️
- **Growth Strategy**: 🌈 Collaborative Swarm

---

"""

        # Orchestrator section
        if orchestrator:
            content += f"""## 🎛️ Orchestrator Status
- **PID**: {orchestrator['pid']}
- **Managed Workers**: {orchestrator['managed_workers']}
- **Health Monitoring**: ✅ Active (30s interval)
- **Auto-Recovery**: ✅ Enabled (max 3 restarts)

---

"""

        # Workers section
        if workers:
            content += "## 🤖 Active Worker Swarm\n\n"
            content += "| Worker ID | PID | Status | CPU | Memory | Current Focus |\n"
            content += "|-----------|-----|--------|-----|--------|---------------|\n"
            
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            for w in workers:
                content += f"| **{w['id']}** | {w['pid']} | {w['status']} | {w['cpu']:.1f}% | {w['memory_mb']:.0f}MB | {w['focus'][:50]} |\n"
            
            content += "\n---\n\n"
        
        # Active mutations
        if mutations:
            content += "## 🔄 Active Mutations\n\n"
            for mut in mutations[:5]:
                content += f"- 🔧 {mut}\n"
            content += "\n---\n\n"
        
        # Recent changes
        if changes:
            content += "## 📝 Recent Code Changes\n\n"
            for change in changes:
                content += f"- **{change['hash']}** ({change['time']}): {change['message']}\n"
            content += "\n---\n\n"
        
        # Performance stats
        if workers:
            avg_cpu = sum(w['cpu'] for w in workers) / len(workers)
            avg_mem = sum(w['memory_mb'] for w in workers) / len(workers)
            
            content += f"""## 📈 Performance Statistics
- **Average Worker CPU**: {avg_cpu:.1f}%
- **Average Worker Memory**: {avg_mem:.0f}MB
- **Total Worker Memory**: {sum(w['memory_mb'] for w in workers):.0f}MB
- **Healthy Workers**: {sum(1 for w in workers if '🟢' in w['status'])}/{len(workers)}

---

"""
        
        # Footer
        content += f"""## 🎯 Quick Actions
- **View Logs**: `tail -f autonomous_reports/logs/*.log`
- **Check Status**: `cat .workers_state.json | python3 -m json.tool`
- **Stop System**: `./.autonomous_system/scripts/stop_autonomous_daemon.sh`
- **Restart**: `./.autonomous_system/scripts/start_autonomous_daemon.sh --workers 3`
"""
        
        # Write to file
        self.dashboard_path.write_text(content)
    
    def run_continuous(self, interval: int = 5):
        logger.info('Professional Grade Execution: Entering method')
        """Continuously update dashboard."""
        print(f"🎯 Dashboard updater started (updating every {interval}s)")
        
        try:
            while True:
                self.update_dashboard()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n✅ Dashboard updater stopped")

def main():
    logger.info('Professional Grade Execution: Entering method')
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Live Dashboard Updater")
    parser.add_argument("--interval", type=int, default=5, help="Update interval in seconds")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root")
    parser.add_argument("--once", action="store_true", help="Update once and exit")
    
    args = parser.parse_args()
    
    updater = DashboardUpdater(args.project_root)
    
    if args.once:
        updater.update_dashboard()
        print("✅ Dashboard updated")
    else:
        updater.run_continuous(args.interval)

if __name__ == "__main__":
    main()
logger = logging.getLogger(__name__)
