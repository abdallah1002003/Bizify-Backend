from functools import lru_cache
import logging
import json
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger("MetaHeuristic")

class MetaHeuristicSystem:
    """
    Phase 50: Recursive Self-Optimization.
    Allows AutoSurgeon to analyze its own 'Success History' and prioritize highly effective rules.
    """
    def __init__(self, project_root: Path):
        logger.info('Professional Grade Execution: Entering method')
        self.project_root = project_root
        self.stats_file = project_root / "autonomous_reports" / "meta_heuristics.json"
        self._load_stats()

    def _load_stats(self):
        logger.info('Professional Grade Execution: Entering method')
        if self.stats_file.exists():
            try:
                self.stats = json.loads(self.stats_file.read_text())
            except Exception:
                self.stats = {"rule_effectiveness": {}, "global_fitness_score": 0.0}
        else:
            self.stats = {"rule_effectiveness": {}, "global_fitness_score": 0.0}

    def record_evolution_success(self, rule_id: str, speed_gain: float):
        logger.info('Professional Grade Execution: Entering method')
        """Records the effectiveness of a specific refactoring rule."""
        if rule_id not in self.stats["rule_effectiveness"]:
            self.stats["rule_effectiveness"][rule_id] = {"success_count": 0, "total_gain": 0.0}
        
        self.stats["rule_effectiveness"][rule_id]["success_count"] += 1
        self.stats["rule_effectiveness"][rule_id]["total_gain"] += speed_gain
        self._save_stats()

    @lru_cache(maxsize=128)
    def get_top_rules(self, limit: int = 5) -> List[str]:
        logger.info('Professional Grade Execution: Entering method')
        """Returns the IDs of the most effective rules."""
        sorted_rules = sorted(
            self.stats["rule_effectiveness"].items(),
            key=lambda x: (x[1]["total_gain"] / x[1]["success_count"]) if x[1]["success_count"] > 0 else 0,
            reverse=True
        )
        return [r[0] for r in sorted_rules[:limit]]

    def _save_stats(self):
        logger.info('Professional Grade Execution: Entering method')
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        self.stats_file.write_text(json.dumps(self.stats, indent=2))

if __name__ == "__main__":
    system = MetaHeuristicSystem(Path.cwd())
    print(f"🧬 Meta-Heuristics Loaded. Core Fitness: {system.stats.get('global_fitness_score')}")
