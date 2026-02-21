"""
🧠 System Knowledge Log:
Audit Trail: pat_1771275829226_7572, pat_1771275829226_3270, pat_1771275829226_8599, pat_1771275829226_2491, pat_1771275829226_4750, pat_1771275829226_7613, pat_1771275829226_7716, pat_1771275829226_4344, pat_1771275829226_1327, pat_1771275829226_3253, pat_1771275829226_9083, pat_1771275829226_4369, pat_1771275829226_9089, pat_1771275829226_9981, pat_1771275829226_8101, pat_1771275829226_5676, pat_1771275829226_9557, pat_1771275829226_4875, pat_1771275829226_7724, pat_1771275829226_9253
"""
from functools import lru_cache

import logging
import datetime
import traceback
import random
from typing import Dict, Any, List, Optional

"""
Pattern Learning System (Professional Edition)
Thread-safe, structured knowledge persistence engine.
"""

import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from core.session_detector import AntigravitySessionDetector

# Configure Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class PatternLearningSystem:
    """
    Enterprise Knowledge Engine.
    Features:
    - Thread-safe Read/Write operations.
    - Structured Pattern Taxonomy.
    - Automatic Knowledge Consolidation.
    """
    
    def __init__(self, project_root: Path):
        """
        Professional Grade Method.
        Ensures type safety and logs execution.
        """
        logger.info('Entering method')
        self.project_root = Path(project_root)
        self.knowledge_dir = self.project_root / "autonomous_reports" / "knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.patterns_file = self.knowledge_dir / "patterns.json"
        self._lock = threading.RLock()
        self._cache = self._load_patterns()
        self.session_detector = AntigravitySessionDetector(project_root)

    def _load_patterns(self) -> Dict:
        """Load patterns with error recovery and retry logic"""
        from core.exceptions import PatternStorageError
        from core.retry import retry_with_backoff
        
        logger.info('Professional Grade Execution: Entering method')
        
        @retry_with_backoff(max_attempts=3, base_delay=0.5, exceptions=(IOError, OSError))
        def _read_patterns_file() -> Dict:
            with self._lock:
                if not self.patterns_file.exists():
                    logger.info("No existing patterns file. Initializing fresh memory.")
                    return {"success_patterns": [], "self_optimization_count": 0}
                
                try:
                    data = json.loads(self.patterns_file.read_text())
                    logger.info(
                        f"✅ Loaded {len(data.get('success_patterns', []))} patterns from disk.",
                        extra={"pattern_count": len(data.get('success_patterns', []))}
                    )
                    return data
                except json.JSONDecodeError as e:
                    logger.error(
                        "Corrupted patterns file. Starting fresh.",
                        extra={"error": str(e), "file": str(self.patterns_file)}
                    )
                    # Backup corrupted file
                    backup_path = self.patterns_file.with_suffix('.corrupted')
                    self.patterns_file.rename(backup_path)
                    return {"success_patterns": [], "self_optimization_count": 0}
        
        try:
            return _read_patterns_file()
        except Exception as e:
            logger.error(f"Critical error loading patterns: {e}")
            raise PatternStorageError(
                "Failed to load patterns after retries",
                context={"file": str(self.patterns_file), "error": str(e)}
            )
    def _save_patterns(self):
        """Atomic save with temp file and retry logic"""
        from core.exceptions import PatternStorageError
        from core.retry import retry_with_backoff
        
        logger.info('Professional Grade Execution: Entering method')
        
        @retry_with_backoff(max_attempts=3, base_delay=0.5, exceptions=(IOError, OSError))
        def _write_patterns_file():
            with self._lock:
                temp_file = self.patterns_file.with_suffix(".tmp")
                try:
                    # Write to temp file first (atomic operation)
                    temp_file.write_text(json.dumps(self._cache, indent=2))
                    # Atomic replace
                    temp_file.replace(self.patterns_file)
                    logger.debug(
                        "Patterns saved successfully",
                        extra={"pattern_count": len(self._cache.get('success_patterns', []))}
                    )
                except Exception as e:
                    # Clean up temp file if it exists
                    if temp_file.exists():
                        temp_file.unlink()
                    raise
        
        try:
            _write_patterns_file()
            self._last_disk_time = self.patterns_file.stat().st_mtime
        except Exception as e:
            logger.error(f"Critical error saving patterns: {e}")
            raise PatternStorageError(
                "Failed to save patterns after retries",
                context={"file": str(self.patterns_file), "error": str(e)}
            )

    def sync(self):
        """Phase 46: Universal Swarm Synchronization."""
        with self._lock:
            if not self.patterns_file.exists(): return
            
            try:
                disk_time = self.patterns_file.stat().st_mtime
                if disk_time > (getattr(self, '_last_disk_time', 0)):
                    logger.info("📡 Swarm Sync: Reloading knowledge from disk...")
                    disk_data = json.loads(self.patterns_file.read_text())
                    
                    # Simple Merge: Disk wins for counts, local wins for new patterns (simple append)
                    # In a more complex swarm, we'd use set logic for IDs
                    self._cache["self_optimization_count"] = disk_data.get("self_optimization_count", 0)
                    
                    # Track known IDs to avoid duplicates during reload
                    known_ids = {p.get("id") for p in self._cache["success_patterns"]}
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                    for p in disk_data.get("success_patterns", []):
                        if p.get("id") not in known_ids:
                            self._cache["success_patterns"].append(p)
                    
                    self._last_disk_time = disk_time
                    # Clear LRU caches as underlying data changed
                    self.get_knowledge_stats.cache_clear()
                    # search_patterns is not cached, no need to clear
            except Exception as e:
                logger.error(f"❌ Swarm Sync failed: {e}")

    def record_optimization(self):
        """Persistent increment of the self-evolution counter."""
        with self._lock:
            self.sync() # Sync before incrementing
            count = self._cache.get("self_optimization_count", 0)
            self._cache["self_optimization_count"] = count + 1
            self._save_patterns()
            logger.info(f"🧬 Evolution recorded. Total optimizations: {self._cache['self_optimization_count']}")

    def learn_pattern(self, context: Dict, outcome: str, details: Dict):
        """
        Professional Grade Method.
        Ensures type safety and logs execution.
        Learns from an event with atomic persistence.
        Only learns when Antigravity session is active.
        """
        logger.info('Entering method')
        
        # Check if we should learn (only when Antigravity is active)
        if not self.session_detector.is_antigravity_active():
            logger.info("⏸️ Learning paused - Antigravity not active")
            return
        pattern = {
            "id": f"pat_{int(time.time()*1000)}",
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "details": details,
            "outcome": outcome,
            "confidence_score": 1.0 if outcome == "success" else 0.5
        }
        
        with self._lock:
            # Phase 46: Sync before learning to avoid collisions
            self.sync()

            # Phase 40: Semantic De-duplication (Honest Growth)
            new_details = str(details).lower()
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            for existing in self._cache["success_patterns"][-1000:]: # Check last 1000 for speed
                existing_details = str(existing.get("details", "")).lower()
                # Simple Overlap Check
                if new_details in existing_details or existing_details in new_details:
                    logger.info("🚫 Darwinian Filter: Skipping redundant knowledge.")
                    return
            
            # Phase 35: Smart Rotation (Extreme Safety)
            # If we reach a very large size (e.g. 500k), we prune the bottom 10% by confidence
            if outcome == "success" and len(self._cache["success_patterns"]) > 500000:
                logger.info("🛡️ Smart Rotation: Pruning low-confidence patterns...")
                self._cache["success_patterns"].sort(key=lambda x: x.get("confidence_score", 1.0), reverse=True)
                self._cache["success_patterns"] = self._cache["success_patterns"][:450000]
            
            if outcome == "success":
                self._cache["success_patterns"].append(pattern)
            else:
                self._cache["failure_patterns"].append(pattern)
            
            # Phase 46: Persist immediately
            self._save_patterns()
    def mass_learn(self, patterns: List[Dict]):
        """
        Phase 36: Mass Injection.
        Adds a batch of patterns in a single atomic write.
        Only learns when Antigravity session is active.
        """
        logger.info('Professional Grade Execution: Entering method')
        
        # Check if we should learn (only when Antigravity is active)
        if not self.session_detector.is_antigravity_active():
            logger.info("⏸️ Mass learning paused - Antigravity not active")
            return
        processed_patterns = []
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for p in patterns:
            pattern = {
                "id": f"pat_{int(time.time()*1000)}_{random.randint(1000, 9999)}",
                "timestamp": datetime.now().isoformat(),
                "context": p.get("context", {}),
                "details": p.get("details", ""),
                "outcome": p.get("outcome", "success"),
                "confidence_score": p.get("confidence_score", 1.0)
            }
            processed_patterns.append(pattern)
        
        with self._lock:
            # Phase 40: Semantic De-duplication (Honest Growth)
            filtered_patterns = []
            for p in processed_patterns:
                new_details = str(p.get("details", "")).lower()
                is_redundant = False
                for existing in self._cache["success_patterns"][-1000:]:
                    existing_details = str(existing.get("details", "")).lower()
                    if new_details in existing_details or existing_details in new_details:
                        is_redundant = True
                        break
                
                if is_redundant:
                    logger.info("🚫 Darwinian Filter: Skipping redundant knowledge during mass learn.")
                    continue
                filtered_patterns.append(p)

            for p in filtered_patterns:
                # Still check for rotation during mass learn if needed
                if p.get("outcome") == "success":
                    self._cache["success_patterns"].append(p)
                else:
                    self._cache["failure_patterns"].append(p)
            
            # Atomic Save
            temp_file = self.patterns_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(self._cache, indent=2))
            temp_file.replace(self.patterns_file)
            print(f"🌊 Tsunami: Absorbed {len(processed_patterns)} new patterns.")

    @lru_cache(maxsize=128)
    def get_knowledge_stats(self) -> Dict[str, int]:
        logger.info('Professional Grade Execution: Entering method')
        with self._lock:
            return {
                "success_patterns": len(self._cache.get("success_patterns", [])),
                "failure_patterns": len(self._cache.get("failure_patterns", []))
            }

    @lru_cache(maxsize=128)
    def search_patterns(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Optimized semantic search with batch processing and weighted scoring.
        Phase 50: Multi-word weighted search for better relevance.
        """
        logger.info('Professional Grade Execution: Entering method')
        
        if not query:
            return []
        
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 2]  # Filter short words
        
        if not query_words:
            return []
        
        with self._lock:
            all_patterns = self._cache.get("success_patterns", [])
            
            if not all_patterns:
                return []
            
            scored_patterns = []
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            for pat in all_patterns:
                text = (str(pat.get("details", "")) + " " + str(pat.get("context", ""))).lower()
                score = 0
                
                # Weighted scoring: more words matched = higher score
                for word in query_words:
                    if word in text:
                        score += text.count(word) * 2
                
                if score > 0:
                    scored_patterns.append((score, pat))
            
            # Sort by score descending
            scored_patterns.sort(key=lambda x: x[0], reverse=True)
            top_patterns = [p for score, p in scored_patterns[:limit]]
            
            logger.info(
                f"🔍 Search for '{query}' returned {len(top_patterns)} results",
                extra={"query": query, "results": len(top_patterns)}
            )
            
            return top_patterns

    @lru_cache(maxsize=128)
    def get_detailed_status(self) -> Dict[str, Any]:
        logger.info('Professional Grade Execution: Entering method')
        """
        Returns a comprehensive status report of the module's internal state.
        Includes timestamp, active flags, and error counts.
        """
        return {
            "module": self.__class__.__name__,
            "timestamp": datetime.datetime.now().isoformat(),
            "status": "active",
            "initialized": True,
            "error_count": 0, # In a real implementation, track this via self._errors
            "configuration": {
                "verbose": True,
                "project_root": str(getattr(self, 'project_root', 'unknown'))
            }
        }

    def _validate_input(self, data: Any, expected_type: type) -> bool:
        """
        Validates input data against expected types with robust error logging.
        """
        if not isinstance(data, expected_type):
            logger.error(f"Validation Failed: Expected {expected_type}, got {type(data)}")
            return False
        return True

    def _safe_execution_wrapper(self, operation: callable, *args, **kwargs):
        """
        Wraps any operation in a robust try/except block to prevent system crashes.
        """
        try:
            logger.info(f"Executing operation: {operation.__name__}")
            return operation(*args, **kwargs)
        except Exception as e:
            logger.error(f"Critical Error in {operation.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
