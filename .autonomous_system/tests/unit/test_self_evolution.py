import logging
"""
Unit Tests for SelfEvolutionSystem
Tests autonomous code improvement capabilities.
"""

import pytest
import ast
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from evolution.self_evolution import SelfEvolutionSystem
from app.core.exceptions import EvolutionError

@pytest.fixture
def temp_project_root(tmp_path):
    logger.info('Professional Grade Execution: Entering method')
    """Create a temporary project root for testing."""
    return tmp_path

@pytest.fixture
def evolution_system(temp_project_root):
    logger.info('Professional Grade Execution: Entering method')
    """Create a SelfEvolutionSystem instance for testing."""
    return SelfEvolutionSystem(temp_project_root)

@pytest.fixture
def sample_python_file(tmp_path):
    logger.info('Professional Grade Execution: Entering method')
    """Create a sample Python file for testing."""
    test_file = tmp_path / "test_module.py"
    test_file.write_text("""
def function_without_docstring(x, y):
    return x + y

def function_with_docstring(a, b):
    '''This function has a docstring.'''
    return a * b

class TestClass:
    def method_without_docstring(self):
        pass
""")
    return test_file

class TestSelfEvolutionSystem:
    """Test suite for SelfEvolutionSystem."""
    
    def test_initialization(self, evolution_system, temp_project_root):
        logger.info('Professional Grade Execution: Entering method')
        """Test system initializes correctly."""
        assert evolution_system.project_root == temp_project_root
        assert hasattr(evolution_system, 'analyzer')
        assert hasattr(evolution_system, 'executor')
    
    def test_evolve_nonexistent_file(self, evolution_system, tmp_path):
        logger.info('Professional Grade Execution: Entering method')
        """Test evolution of non-existent file."""
        fake_file = tmp_path / "nonexistent.py"
        result = evolution_system.evolve(fake_file)
        
        assert result["status"] == "skipped"
        assert result["reason"] == "file_not_found"
    
    def test_add_docstrings(self, evolution_system, sample_python_file):
        logger.info('Professional Grade Execution: Entering method')
        """Test adding docstrings to functions without them."""
        result = evolution_system.evolve(sample_python_file)
        
        # Should have added docstrings
        if result["status"] == "modified":
            assert result["type"] == "added_docstrings"
            assert result["count"] > 0
            
            # Verify file was modified
            content = sample_python_file.read_text()
            assert "TODO: Add docstring" in content
    
    def test_syntax_validation(self, evolution_system):
        logger.info('Professional Grade Execution: Entering method')
        """Test syntax validation of generated code."""
        valid_code = "def foo():\n    pass"
        invalid_code = "def foo(\n    pass"
        
        assert evolution_system._verify_syntax(valid_code) is True
        assert evolution_system._verify_syntax(invalid_code) is False
    
    def test_no_modification_when_complete(self, evolution_system, tmp_path):
        logger.info('Professional Grade Execution: Entering method')
        """Test that complete files are not modified."""
        complete_file = tmp_path / "complete.py"
        complete_file.write_text("""
def well_documented_function(x):
    '''This function is well documented.'''
    return x * 2
""")
        
        result = evolution_system.evolve(complete_file)
        
        assert result["status"] in ["stable", "modified"]
        if result["status"] == "stable":
            assert "no_obvious_improvements" in result.get("reason", "")
    
    def test_preserves_existing_code(self, evolution_system, sample_python_file):
        logger.info('Professional Grade Execution: Entering method')
        """Test that evolution preserves existing code logic."""
        original_content = sample_python_file.read_text()
        
        evolution_system.evolve(sample_python_file)
        
        modified_content = sample_python_file.read_text()
        
        # Original function names should still be present
        assert "function_without_docstring" in modified_content
        assert "function_with_docstring" in modified_content
        assert "TestClass" in modified_content
    
    def test_handles_syntax_errors_gracefully(self, evolution_system, tmp_path):
        logger.info('Professional Grade Execution: Entering method')
        """Test graceful handling of files with syntax errors."""
        bad_file = tmp_path / "bad_syntax.py"
        bad_file.write_text("def broken(\n    this is not valid python")
        
        result = evolution_system.evolve(bad_file)
        
        assert result["status"] == "failed"
        assert "error" in result
    
    def test_get_detailed_status(self, evolution_system):
        logger.info('Professional Grade Execution: Entering method')
        """Test status reporting."""
        status = evolution_system.get_detailed_status()
        
        assert "module" in status
        assert "timestamp" in status
        assert "status" in status
        assert status["status"] == "active"
        assert status["initialized"] is True
    
    @patch('.autonomous_system.evolution.self_evolution.logger')
    def test_logging(self, mock_logger, evolution_system, sample_python_file):
        """Test that operations are properly logged."""
        evolution_system.evolve(sample_python_file)
        
        # Should have logged the evolution attempt
        assert mock_logger.info.called
    
    def test_multiple_functions_in_file(self, evolution_system, tmp_path):
        logger.info('Professional Grade Execution: Entering method')
        """Test handling files with multiple functions."""
        multi_file = tmp_path / "multi.py"
        multi_file.write_text("""
def func1():
    pass

def func2():
    pass

def func3():
    pass
""")
        
        result = evolution_system.evolve(multi_file)
        
        if result["status"] == "modified":
            # Should have added docstrings to all 3 functions
            assert result["count"] == 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
logger = logging.getLogger(__name__)
