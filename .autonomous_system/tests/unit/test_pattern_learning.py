import logging
"""
Unit Tests for PatternLearningSystem
Tests core functionality with mocking and fixtures.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from evolution.pattern_learning import PatternLearningSystem
from app.core.exceptions import PatternStorageError

@pytest.fixture
def temp_project_root(tmp_path):
    logger.info('Professional Grade Execution: Entering method')
    """Create a temporary project root for testing."""
    return tmp_path

@pytest.fixture
def pattern_system(temp_project_root):
    logger.info('Professional Grade Execution: Entering method')
    """Create a PatternLearningSystem instance for testing."""
    return PatternLearningSystem(temp_project_root)

class TestPatternLearningSystem:
    """Test suite for PatternLearningSystem."""
    
    def test_initialization(self, pattern_system, temp_project_root):
        logger.info('Professional Grade Execution: Entering method')
        """Test system initializes correctly."""
        assert pattern_system.project_root == temp_project_root
        assert pattern_system.knowledge_dir.exists()
        assert isinstance(pattern_system._cache, dict)
        assert "success_patterns" in pattern_system._cache
    
    def test_learn_pattern_success(self, pattern_system):
        logger.info('Professional Grade Execution: Entering method')
        """Test learning a new pattern."""
        context = {"category": "test", "type": "unit_test"}
        details = {"message": "Test pattern"}
        
        pattern_system.learn_pattern(context, "success", details)
        
        patterns = pattern_system._cache["success_patterns"]
        assert len(patterns) > 0
        assert patterns[-1]["outcome"] == "success"
        assert patterns[-1]["context"]["category"] == "test"
    
    def test_learn_pattern_deduplication(self, pattern_system):
        logger.info('Professional Grade Execution: Entering method')
        """Test that duplicate patterns are filtered."""
        context = {"category": "test"}
        details = {"message": "Duplicate test"}
        
        # Learn same pattern twice
        pattern_system.learn_pattern(context, "success", details)
        initial_count = len(pattern_system._cache["success_patterns"])
        
        pattern_system.learn_pattern(context, "success", details)
        final_count = len(pattern_system._cache["success_patterns"])
        
        # Should not add duplicate
        assert final_count == initial_count
    
    def test_mass_learn(self, pattern_system):
        logger.info('Professional Grade Execution: Entering method')
        """Test batch learning of patterns."""
        patterns = [
            {"context": {"category": f"test_{i}"}, "details": f"Pattern {i}"}
            for i in range(10)
        ]
        
        pattern_system.mass_learn(patterns)
        
        assert len(pattern_system._cache["success_patterns"]) >= 10
    
    def test_search_patterns(self, pattern_system):
        logger.info('Professional Grade Execution: Entering method')
        """Test pattern search functionality."""
        # Add test patterns
        pattern_system.learn_pattern(
            {"category": "python"},
            "success",
            {"message": "Use type hints for better code quality"}
        )
        pattern_system.learn_pattern(
            {"category": "python"},
            "success",
            {"message": "Implement error handling with try-except"}
        )
        
        # Search for patterns
        results = pattern_system.search_patterns("type hints", limit=5)
        
        assert len(results) > 0
        assert any("type hints" in str(r.get("details", "")).lower() for r in results)
    
    def test_get_knowledge_stats(self, pattern_system):
        logger.info('Professional Grade Execution: Entering method')
        """Test knowledge statistics retrieval."""
        # Add some patterns
        pattern_system.learn_pattern({"category": "test"}, "success", {"msg": "test1"})
        pattern_system.learn_pattern({"category": "test"}, "failure", {"msg": "test2"})
        
        stats = pattern_system.get_knowledge_stats()
        
        assert "total_patterns" in stats
        assert "success_patterns" in stats
        assert "failure_patterns" in stats
        assert stats["total_patterns"] > 0
    
    def test_save_and_load_patterns(self, pattern_system):
        logger.info('Professional Grade Execution: Entering method')
        """Test persistence of patterns."""
        # Add pattern
        pattern_system.learn_pattern(
            {"category": "persistence_test"},
            "success",
            {"message": "Test persistence"}
        )
        
        # Save
        pattern_system._save_patterns()
        
        # Create new instance (should load from disk)
        new_system = PatternLearningSystem(pattern_system.project_root)
        
        # Verify pattern was loaded
        patterns = new_system._cache["success_patterns"]
        assert any(p.get("context", {}).get("category") == "persistence_test" for p in patterns)
    
    def test_corrupted_file_recovery(self, temp_project_root):
        logger.info('Professional Grade Execution: Entering method')
        """Test recovery from corrupted patterns file."""
        # Create corrupted file
        patterns_file = temp_project_root / "autonomous_reports" / "knowledge" / "patterns.json"
        patterns_file.parent.mkdir(parents=True, exist_ok=True)
        patterns_file.write_text("{ invalid json }")
        
        # Should recover gracefully
        system = PatternLearningSystem(temp_project_root)
        
        assert isinstance(system._cache, dict)
        assert "success_patterns" in system._cache
        # Corrupted file should be backed up
        assert any(f.suffix == ".corrupted" for f in patterns_file.parent.iterdir())
    
    def test_thread_safety(self, pattern_system):
        logger.info('Professional Grade Execution: Entering method')
        """Test thread-safe operations."""
        import threading
        
        def add_patterns():
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            logger.info('Professional Grade Execution: Entering method')
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            for i in range(10):
                pattern_system.learn_pattern(
                    {"category": "thread_test"},
                    "success",
                    {"message": f"Thread pattern {i}"}
                )
        
        # Run multiple threads
        threads = [threading.Thread(target=add_patterns) for _ in range(3)]
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All patterns should be added without corruption
        patterns = pattern_system._cache["success_patterns"]
        thread_patterns = [p for p in patterns if p.get("context", {}).get("category") == "thread_test"]
        assert len(thread_patterns) > 0
    
    @patch('.autonomous_system.evolution.pattern_learning.logger')
    def test_error_logging(self, mock_logger, pattern_system):
        """Test that errors are properly logged."""
        # Force an error by making patterns_file read-only
        pattern_system.patterns_file.touch()
        pattern_system.patterns_file.chmod(0o444)
        
        try:
            pattern_system._save_patterns()
        except PatternStorageError:
            # Error should be logged
            assert mock_logger.error.called
        finally:
            # Cleanup
            pattern_system.patterns_file.chmod(0o644)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
logger = logging.getLogger(__name__)
