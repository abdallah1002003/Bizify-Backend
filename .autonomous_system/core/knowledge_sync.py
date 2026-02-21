"""
Distributed Knowledge Synchronization
Handles conflict resolution and version control for patterns.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import time
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum

class ConflictStrategy(Enum):
    """Strategies for resolving conflicts."""
    LATEST_WINS = "latest_wins"
    HIGHEST_CONFIDENCE = "highest_confidence"
    MERGE = "merge"
    MANUAL = "manual"

@dataclass
class PatternVersion:
    """Version information for a pattern."""
    pattern_id: str
    version: int
    timestamp: float
    checksum: str
    data: Dict[str, Any]
    source: str  # Worker/node that created this version

class KnowledgeSyncManager:
    """
    Manages distributed knowledge synchronization with conflict resolution.
    Supports version control and pattern merging.
    """
    
    def __init__(self, project_root: Path, node_id: str = "main"):
        self.project_root = project_root
        self.node_id = node_id
        self.sync_dir = project_root / "autonomous_reports" / "sync"
        self.sync_dir.mkdir(parents=True, exist_ok=True)
        
        self.version_history: Dict[str, List[PatternVersion]] = {}
        self.conflict_strategy = ConflictStrategy.LATEST_WINS
    
    def create_version(self, pattern: Dict[str, Any], source: Optional[str] = None) -> PatternVersion:
        """Create a new version of a pattern."""
        pattern_id = pattern.get("id", "unknown")
        
        # Get current version number
        current_versions = self.version_history.get(pattern_id, [])
        version_num = len(current_versions) + 1
        
        # Calculate checksum
        pattern_str = json.dumps(pattern, sort_keys=True)
        checksum = hashlib.sha256(pattern_str.encode()).hexdigest()
        
        version = PatternVersion(
            pattern_id=pattern_id,
            version=version_num,
            timestamp=time.time(),
            checksum=checksum,
            data=pattern,
            source=source or self.node_id
        )
        
        # Store version
        if pattern_id not in self.version_history:
            self.version_history[pattern_id] = []
        self.version_history[pattern_id].append(version)
        
        return version
    
    def detect_conflict(self, pattern_id: str, incoming_version: PatternVersion) -> bool:
        """Detect if there's a conflict with incoming version."""
        if pattern_id not in self.version_history:
            return False
        
        local_versions = self.version_history[pattern_id]
        if not local_versions:
            return False
        
        latest_local = local_versions[-1]
        
        # Conflict if checksums differ and timestamps are close
        if (latest_local.checksum != incoming_version.checksum and
            abs(latest_local.timestamp - incoming_version.timestamp) < 60):
            return True
        
        return False
    
    def resolve_conflict(
        self,
        pattern_id: str,
        local_version: PatternVersion,
        remote_version: PatternVersion,
        strategy: Optional[ConflictStrategy] = None
    ) -> PatternVersion:
        """Resolve conflict between two versions."""
        strategy = strategy or self.conflict_strategy
        
        if strategy == ConflictStrategy.LATEST_WINS:
            return local_version if local_version.timestamp > remote_version.timestamp else remote_version
        
        elif strategy == ConflictStrategy.HIGHEST_CONFIDENCE:
            local_confidence = local_version.data.get("confidence_score", 0)
            remote_confidence = remote_version.data.get("confidence_score", 0)
            return local_version if local_confidence > remote_confidence else remote_version
        
        elif strategy == ConflictStrategy.MERGE:
            return self._merge_versions(local_version, remote_version)
        
        else:  # MANUAL
            # Store both for manual resolution
            return local_version
    
    def _merge_versions(self, v1: PatternVersion, v2: PatternVersion) -> PatternVersion:
        """Merge two pattern versions."""
        merged_data = v1.data.copy()
        
        # Merge details if both have them
        if "details" in v1.data and "details" in v2.data:
            if isinstance(v1.data["details"], dict) and isinstance(v2.data["details"], dict):
                merged_data["details"] = {**v1.data["details"], **v2.data["details"]}
            elif isinstance(v1.data["details"], str) and isinstance(v2.data["details"], str):
                merged_data["details"] = f"{v1.data['details']} | {v2.data['details']}"
        
        # Take higher confidence
        merged_data["confidence_score"] = max(
            v1.data.get("confidence_score", 0),
            v2.data.get("confidence_score", 0)
        )
        
        # Create new version
        return PatternVersion(
            pattern_id=v1.pattern_id,
            version=max(v1.version, v2.version) + 1,
            timestamp=time.time(),
            checksum=hashlib.sha256(json.dumps(merged_data, sort_keys=True).encode()).hexdigest(),
            data=merged_data,
            source=f"{v1.source}+{v2.source}"
        )
    
    def sync_patterns(self, incoming_patterns: List[Dict[str, Any]], source: str) -> Dict[str, Any]:
        """
        Synchronize incoming patterns with local knowledge.
        Returns sync results with conflicts and resolutions.
        """
        results = {
            "synced": 0,
            "conflicts": 0,
            "resolved": 0,
            "failed": 0,
            "conflict_details": []
        }
        
        for pattern in incoming_patterns:
            pattern_id = pattern.get("id", "unknown")
            
            # Create version for incoming pattern
            incoming_version = PatternVersion(
                pattern_id=pattern_id,
                version=0,  # Will be updated
                timestamp=time.time(),
                checksum=hashlib.sha256(json.dumps(pattern, sort_keys=True).encode()).hexdigest(),
                data=pattern,
                source=source
            )
            
            # Check for conflicts
            if self.detect_conflict(pattern_id, incoming_version):
                results["conflicts"] += 1
                
                local_version = self.version_history[pattern_id][-1]
                resolved = self.resolve_conflict(pattern_id, local_version, incoming_version)
                
                self.version_history[pattern_id].append(resolved)
                results["resolved"] += 1
                results["conflict_details"].append({
                    "pattern_id": pattern_id,
                    "strategy": self.conflict_strategy.value,
                    "winner": resolved.source
                })
            else:
                # No conflict, just add
                self.create_version(pattern, source)
                results["synced"] += 1
        
        return results
    
    def export_knowledge(self, output_path: Path) -> None:
        """Export all knowledge with version history."""
        export_data = {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "version_history": {
                pattern_id: [asdict(v) for v in versions]
                for pattern_id, versions in self.version_history.items()
            }
        }
        
        output_path.write_text(json.dumps(export_data, indent=2))
        print(f"✅ Knowledge exported to {output_path}")
    
    def import_knowledge(self, input_path: Path) -> Dict[str, Any]:
        """Import knowledge from another node."""
        data = json.loads(input_path.read_text())
        source_node = data.get("node_id", "unknown")
        
        # Convert to patterns
        patterns = []
        for pattern_id, versions in data.get("version_history", {}).items():
            if versions:
                # Take latest version
                latest = versions[-1]
                patterns.append(latest["data"])
        
        # Sync patterns
        return self.sync_patterns(patterns, source_node)
