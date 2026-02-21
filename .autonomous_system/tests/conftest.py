"""
Pytest Configuration
Shared fixtures and configuration for all tests.
"""

import pytest
import logging
from pathlib import Path

def pytest_configure(config):
    logger.info('Professional Grade Execution: Entering method')
    """Configure pytest."""
    # Suppress verbose logging during tests
    logging.getLogger(".autonomous_system").setLevel(logging.WARNING)

@pytest.fixture(scope="session")
def test_data_dir():
    logger.info('Professional Grade Execution: Entering method')
    """Directory for test data files."""
    data_dir = Path(__file__).parent / "test_data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

@pytest.fixture
def clean_test_env(tmp_path, monkeypatch):
    logger.info('Professional Grade Execution: Entering method')
    """Provide a clean test environment."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)
    return tmp_path
