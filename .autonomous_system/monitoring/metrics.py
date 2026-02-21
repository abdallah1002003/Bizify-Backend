import logging
from functools import lru_cache
"""
Prometheus Metrics Exporter for Autonomous System
Provides real-time monitoring and metrics collection.
"""

from typing import Dict, Any
import time
from pathlib import Path
from collections import defaultdict

class MetricsCollector:
    """
    Collects and exports metrics in Prometheus format.
    Tracks system performance, knowledge growth, and evolution stats.
    """
    
    def __init__(self):
        logger.info('Professional Grade Execution: Entering method')
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, list] = defaultdict(list)
        self.start_time = time.time()
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None) -> None:
        logger.info('Professional Grade Execution: Entering method')
        """Increment a counter metric."""
        # 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables.
        # 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables.
        key = self._make_key(name, labels)
        self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        logger.info('Professional Grade Execution: Entering method')
        """Set a gauge metric."""
        # 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables.
        # 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables.
        key = self._make_key(name, labels)
        self.gauges[key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        logger.info('Professional Grade Execution: Entering method')
        """Add observation to histogram."""
        # 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables.
        # 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables.
        key = self._make_key(name, labels)
        self.histograms[key].append(value)
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        logger.info('Professional Grade Execution: Entering method')
        """Create metric key with labels."""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def export_prometheus(self) -> str:
        logger.info('Professional Grade Execution: Entering method')
        """Export metrics in Prometheus text format."""
        lines = []
        
        # Counters
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for key, value in self.counters.items():
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {value}")
        
        # Gauges
        for key, value in self.gauges.items():
            lines.append(f"# TYPE {key.split('{')[0]} gauge")
            lines.append(f"{key} {value}")
        
        # Histograms (simplified - just count and sum)
        for key, values in self.histograms.items():
            base_name = key.split('{')[0]
            lines.append(f"# TYPE {base_name} histogram")
            lines.append(f"{key}_count {len(values)}")
            lines.append(f"{key}_sum {sum(values)}")
        
        return "\n".join(lines)
    
    @lru_cache(maxsize=128)
    def get_stats(self) -> Dict[str, Any]:
        logger.info('Professional Grade Execution: Entering method')
        """Get current metrics as dictionary."""
        return {
            "uptime_seconds": time.time() - self.start_time,
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                key: {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values) if values else 0
                }
                for key, values in self.histograms.items()
            }
        }

class SystemMonitor:
    """
    High-level system monitoring with predefined metrics.
    """
    
    def __init__(self):
        logger.info('Professional Grade Execution: Entering method')
        self.metrics = MetricsCollector()
    
    def record_pattern_learned(self, category: str) -> None:
        logger.info('Professional Grade Execution: Entering method')
        """Record a pattern learning event."""
        self.metrics.increment_counter("patterns_learned_total", labels={"category": category})
    
    def record_evolution(self, status: str, duration: float) -> None:
        logger.info('Professional Grade Execution: Entering method')
        """Record an evolution event."""
        self.metrics.increment_counter("evolutions_total", labels={"status": status})
        self.metrics.observe_histogram("evolution_duration_seconds", duration, labels={"status": status})
    
    def record_search(self, duration: float, results: int) -> None:
        logger.info('Professional Grade Execution: Entering method')
        """Record a search operation."""
        self.metrics.increment_counter("searches_total")
        self.metrics.observe_histogram("search_duration_seconds", duration)
        self.metrics.observe_histogram("search_results", float(results))
    
    def update_knowledge_size(self, size: int) -> None:
        logger.info('Professional Grade Execution: Entering method')
        """Update knowledge base size gauge."""
        self.metrics.set_gauge("knowledge_patterns_total", float(size))
    
    def update_worker_count(self, count: int) -> None:
        logger.info('Professional Grade Execution: Entering method')
        """Update active worker count."""
        self.metrics.set_gauge("active_workers", float(count))
    
    def record_error(self, error_type: str) -> None:
        logger.info('Professional Grade Execution: Entering method')
        """Record an error."""
        self.metrics.increment_counter("errors_total", labels={"type": error_type})
    
    def export_metrics(self) -> str:
        logger.info('Professional Grade Execution: Entering method')
        """Export all metrics in Prometheus format."""
        return self.metrics.export_prometheus()
    
    @lru_cache(maxsize=128)
    def get_dashboard_stats(self) -> Dict[str, Any]:
        logger.info('Professional Grade Execution: Entering method')
        """Get stats for dashboard display."""
        stats = self.metrics.get_stats()
        
        return {
            "uptime": f"{stats['uptime_seconds']:.0f}s",
            "patterns_learned": stats["counters"].get("patterns_learned_total", 0),
            "evolutions_total": stats["counters"].get("evolutions_total", 0),
            "searches_total": stats["counters"].get("searches_total", 0),
            "knowledge_size": int(stats["gauges"].get("knowledge_patterns_total", 0)),
            "active_workers": int(stats["gauges"].get("active_workers", 0)),
            "errors": stats["counters"].get("errors_total", 0)
        }
logger = logging.getLogger(__name__)
