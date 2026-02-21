"""
Type Definitions for Autonomous System
Provides TypedDict definitions for complex data structures.
"""

from typing import TypedDict, Optional, Dict, Any, List, Literal

class PatternContext(TypedDict, total=False):
    """Context information for a pattern."""
    category: str
    topic: Optional[str]
    source: Optional[str]
    type: str
    module: Optional[str]
    file: Optional[str]

class Pattern(TypedDict):
    """Structured pattern data."""
    id: str
    timestamp: str
    context: PatternContext
    details: str
    outcome: Literal["success", "failure"]
    confidence_score: float

class PatternCache(TypedDict):
    """Pattern cache structure."""
    success_patterns: List[Pattern]
    failure_patterns: List[Pattern]
    self_optimization_count: int

class WorkerInfo(TypedDict):
    """Worker registration information."""
    pid: int
    last_heartbeat: float
    current_focus: str

class DirectiveInfo(TypedDict):
    """Directive structure for swarm tasks."""
    task: str
    details: List[str]
    priority: Literal["high", "medium", "low"]
    timestamp: str

class EvolutionResult(TypedDict):
    """Result of evolution operation."""
    status: Literal["modified", "stable", "failed", "skipped"]
    reason: Optional[str]
    type: Optional[str]
    count: Optional[int]
    error: Optional[str]

class KnowledgeStats(TypedDict):
    """Knowledge base statistics."""
    total_patterns: int
    success_patterns: int
    failure_patterns: int
    self_optimizations: int
    last_updated: str

class SystemStatus(TypedDict):
    """System status information."""
    module: str
    timestamp: str
    status: Literal["active", "inactive", "error"]
    initialized: bool
    error_count: int
    configuration: Dict[str, Any]
