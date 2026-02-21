from functools import lru_cache
"""
Worker Health Monitor
Tracks resource usage, performance metrics, and health status.
"""

import psutil
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class HealthMetrics:
    """Health metrics for a worker."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    num_threads: int
    num_fds: int  # File descriptors
    tasks_completed: int
    errors_count: int

class WorkerHealthMonitor:
    """
    Monitors worker health and performance metrics.
    Provides alerts for unhealthy workers.
    """
    
    def __init__(self, project_root: Path, history_size: int = 100):
        logger.info('Professional Grade Execution: Entering method')
        self.project_root = project_root
        self.history_size = history_size
        
        # Metrics history per worker
        self.metrics_history: Dict[int, deque] = {}  # pid -> deque of HealthMetrics
        
        # Thresholds
        self.cpu_threshold = 90.0  # %
        self.memory_threshold = 80.0  # %
        self.error_rate_threshold = 0.1  # 10% error rate
    
    def collect_metrics(self, pid: int) -> Optional[HealthMetrics]:
        """Collect current metrics for a worker process."""
        try:
            proc = psutil.Process(pid)
            
            metrics = HealthMetrics(
                timestamp=time.time(),
                cpu_percent=proc.cpu_percent(interval=0.1),
                memory_mb=proc.memory_info().rss / 1024 / 1024,
                memory_percent=proc.memory_percent(),
                num_threads=proc.num_threads(),
                num_fds=proc.num_fds() if hasattr(proc, 'num_fds') else 0,
                tasks_completed=0,  # Will be updated from worker data
                errors_count=0  # Will be updated from logs
            )
            
            # Store in history
            if pid not in self.metrics_history:
                self.metrics_history[pid] = deque(maxlen=self.history_size)
            
            self.metrics_history[pid].append(metrics)
            
            return metrics
            
        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} no longer exists")
            return None
        except Exception as e:
            logger.error(f"Error collecting metrics for {pid}: {e}")
            return None
    
    def check_health(self, pid: int) -> Dict[str, Any]:
        logger.info('Professional Grade Execution: Entering method')
        """
        Check health of a worker and return status.
        Returns dict with 'healthy' bool and 'issues' list.
        """
        if pid not in self.metrics_history or not self.metrics_history[pid]:
            return {"healthy": False, "issues": ["No metrics available"]}
        
        latest = self.metrics_history[pid][-1]
        issues = []
        
        # Check CPU usage
        if latest.cpu_percent > self.cpu_threshold:
            issues.append(f"High CPU usage: {latest.cpu_percent:.1f}%")
        
        # Check memory usage
        if latest.memory_percent > self.memory_threshold:
            issues.append(f"High memory usage: {latest.memory_percent:.1f}%")
        
        # Check for memory leaks (increasing trend)
        if len(self.metrics_history[pid]) >= 10:
            recent_memory = [m.memory_mb for m in list(self.metrics_history[pid])[-10:]]
            if self._is_increasing_trend(recent_memory):
                issues.append("Possible memory leak detected")
        
        # Check file descriptor count
        if latest.num_fds > 100:
            issues.append(f"High file descriptor count: {latest.num_fds}")
        
        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "metrics": asdict(latest)
        }
    
    def _is_increasing_trend(self, values: List[float]) -> bool:
        logger.info('Professional Grade Execution: Entering method')
        """Check if values show an increasing trend."""
        if len(values) < 3:
            return False
        
        # Simple linear regression check
        increases = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
        return increases / (len(values) - 1) > 0.7  # 70% increasing
    
    @lru_cache(maxsize=128)
    def get_statistics(self, pid: int) -> Dict[str, Any]:
        logger.info('Professional Grade Execution: Entering method')
        """Get statistical summary of worker metrics."""
        if pid not in self.metrics_history or not self.metrics_history[pid]:
            return {}
        
        history = list(self.metrics_history[pid])
        
        cpu_values = [m.cpu_percent for m in history]
        memory_values = [m.memory_mb for m in history]
        
        return {
            "samples": len(history),
            "cpu": {
                "current": cpu_values[-1],
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory": {
                "current_mb": memory_values[-1],
                "avg_mb": sum(memory_values) / len(memory_values),
                "max_mb": max(memory_values),
                "min_mb": min(memory_values)
            },
            "uptime_seconds": history[-1].timestamp - history[0].timestamp
        }
    
    def export_metrics(self, output_path: Path) -> None:
        """Export all metrics to JSON file."""
        export_data = {
            "timestamp": time.time(),
            "workers": {}
        }
        
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for pid, history in self.metrics_history.items():
            export_data["workers"][str(pid)] = {
                "metrics": [asdict(m) for m in history],
                "statistics": self.get_statistics(pid),
                "health": self.check_health(pid)
            }
        
        output_path.write_text(json.dumps(export_data, indent=2))
        logger.info(f"✅ Metrics exported to {output_path}")
