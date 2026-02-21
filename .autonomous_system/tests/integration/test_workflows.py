import logging
"""
Integration Tests for Autonomous System
Tests end-to-end workflows and component interactions.
"""

import pytest
import time
from pathlib import Path
from evolution.pattern_learning import PatternLearningSystem
from evolution.self_evolution import SelfEvolutionSystem

@pytest.fixture
def temp_workspace(tmp_path):
    logger.info('Professional Grade Execution: Entering method')
    """Create a temporary workspace for integration testing."""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    return workspace

@pytest.fixture
def integrated_system(temp_workspace):
    logger.info('Professional Grade Execution: Entering method')
    """Create integrated system components."""
    return {
        "pattern_system": PatternLearningSystem(temp_workspace),
        "evolution_system": SelfEvolutionSystem(temp_workspace)
    }

class TestEndToEndWorkflows:
    """Integration tests for complete workflows."""
    
    def test_learn_and_search_workflow(self, integrated_system):
        logger.info('Professional Grade Execution: Entering method')
        """Test complete learn → search workflow."""
        pattern_system = integrated_system["pattern_system"]
        
        # Learn multiple patterns
        patterns = [
            {
                "context": {"category": "python", "type": "best_practice"},
                "details": "Always use type hints for function parameters"
            },
            {
                "context": {"category": "python", "type": "best_practice"},
                "details": "Use context managers for file operations"
            },
            {
                "context": {"category": "security", "type": "warning"},
                "details": "Never hardcode API keys in source code"
            }
        ]
        
        pattern_system.mass_learn(patterns)
        
        # Search for learned patterns
        results = pattern_system.search_patterns("type hints", limit=5)
        
        assert len(results) > 0
        assert any("type hints" in str(r.get("details", "")).lower() for r in results)
        
        # Verify stats
        stats = pattern_system.get_knowledge_stats()
        assert stats["total_patterns"] >= 3
    
    def test_evolution_with_pattern_learning(self, integrated_system, temp_workspace):
        logger.info('Professional Grade Execution: Entering method')
        """Test evolution system learning from its own improvements."""
        pattern_system = integrated_system["pattern_system"]
        evolution_system = integrated_system["evolution_system"]
        
        # Create a file to evolve
        test_file = temp_workspace / "evolve_me.py"
        test_file.write_text("""
def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total
""")
        
        # Evolve the file
        result = evolution_system.evolve(test_file)
        
        # Record the evolution as a pattern
        if result["status"] == "modified":
            pattern_system.learn_pattern(
                context={"category": "evolution", "type": "code_improvement"},
                outcome="success",
                details={
                    "file": str(test_file),
                    "improvement_type": result.get("type"),
                    "count": result.get("count")
                }
            )
            
            # Verify pattern was learned
            evolution_patterns = pattern_system.search_patterns("evolution", limit=10)
            assert len(evolution_patterns) > 0
    
    def test_persistence_across_instances(self, temp_workspace):
        logger.info('Professional Grade Execution: Entering method')
        """Test that data persists across system restarts."""
        # First instance
        system1 = PatternLearningSystem(temp_workspace)
        system1.learn_pattern(
            {"category": "persistence_test"},
            "success",
            {"message": "This should persist"}
        )
        
        # Force save
        system1._save_patterns()
        
        # Second instance (simulates restart)
        system2 = PatternLearningSystem(temp_workspace)
        
        # Search for the pattern
        results = system2.search_patterns("persist", limit=5)
        
        assert len(results) > 0
        assert any("persist" in str(r.get("details", "")).lower() for r in results)
    
    def test_concurrent_pattern_learning(self, temp_workspace):
        logger.info('Professional Grade Execution: Entering method')
        """Test concurrent learning from multiple sources."""
        import threading
        
        system = PatternLearningSystem(temp_workspace)
        
        def learn_batch(category, count):
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            logger.info('Professional Grade Execution: Entering method')
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            for i in range(count):
                system.learn_pattern(
                    {"category": category},
                    "success",
                    {"message": f"{category} pattern {i}"}
                )
        
        # Run concurrent learning
        threads = [
            threading.Thread(target=learn_batch, args=("python", 10)),
            threading.Thread(target=learn_batch, args=("security", 10)),
            threading.Thread(target=learn_batch, args=("performance", 10))
        ]
        
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Verify all patterns were learned
        stats = system.get_knowledge_stats()
        assert stats["total_patterns"] >= 30
    
    def test_error_recovery_workflow(self, temp_workspace):
        logger.info('Professional Grade Execution: Entering method')
        """Test system recovery from errors."""
        system = PatternLearningSystem(temp_workspace)
        
        # Learn some patterns
        system.learn_pattern(
            {"category": "test"},
            "success",
            {"message": "Before error"}
        )
        
        # Simulate corruption by writing invalid JSON
        system.patterns_file.write_text("{ invalid json }")
        
        # Create new instance - should recover
        recovered_system = PatternLearningSystem(temp_workspace)
        
        # Should have recovered with empty cache
        assert isinstance(recovered_system._cache, dict)
        
        # Should be able to learn new patterns
        recovered_system.learn_pattern(
            {"category": "test"},
            "success",
            {"message": "After recovery"}
        )
        
        stats = recovered_system.get_knowledge_stats()
        assert stats["total_patterns"] > 0
    
    def test_large_scale_pattern_search(self, temp_workspace):
        logger.info('Professional Grade Execution: Entering method')
        """Test search performance with large pattern set."""
        system = PatternLearningSystem(temp_workspace)
        
        # Add many patterns
        patterns = [
            {
                "context": {"category": f"category_{i % 10}"},
                "details": f"Pattern about topic {i % 20} with keywords {i % 5}"
            }
            for i in range(1000)
        ]
        
        start_time = time.time()
        system.mass_learn(patterns)
        learn_time = time.time() - start_time
        
        # Search should be fast even with 1000+ patterns
        start_time = time.time()
        results = system.search_patterns("topic keywords", limit=10)
        search_time = time.time() - start_time
        
        assert len(results) > 0
        assert search_time < 1.0  # Should complete in under 1 second
        
        print(f"Learn time: {learn_time:.3f}s, Search time: {search_time:.3f}s")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
logger = logging.getLogger(__name__)
