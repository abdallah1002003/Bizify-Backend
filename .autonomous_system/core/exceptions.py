import logging
"""
Centralized Exception Hierarchy for Autonomous System
Provides structured error handling with context preservation.
"""

from typing import Optional, Dict, Any

class AutonomousSystemError(Exception):
    """Base exception for all autonomous system errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        logger.info('Professional Grade Execution: Entering method')
        self.message = message
        self.context = context or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        logger.info('Professional Grade Execution: Entering method')
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (Context: {context_str})"
        return self.message

# Pattern Learning Exceptions
class PatternLearningError(AutonomousSystemError):
    """Base exception for pattern learning operations."""
    pass

class PatternSyncError(PatternLearningError):
    """Raised when pattern synchronization fails."""
    pass

class PatternValidationError(PatternLearningError):
    """Raised when pattern validation fails."""
    pass

class PatternStorageError(PatternLearningError):
    """Raised when pattern storage/retrieval fails."""
    pass

# Evolution Exceptions
class EvolutionError(AutonomousSystemError):
    """Base exception for evolution operations."""
    pass

class CodeAnalysisError(EvolutionError):
    """Raised when code analysis fails."""
    pass

class CodeTransformationError(EvolutionError):
    """Raised when code transformation fails."""
    pass

class SyntaxValidationError(EvolutionError):
    """Raised when generated code has syntax errors."""
    pass

# Worker/Swarm Exceptions
class SwarmError(AutonomousSystemError):
    """Base exception for swarm operations."""
    pass

class WorkerRegistrationError(SwarmError):
    """Raised when worker registration fails."""
    pass

class DirectiveProcessingError(SwarmError):
    """Raised when directive processing fails."""
    pass

class HeartbeatError(SwarmError):
    """Raised when worker heartbeat fails."""
    pass

# I/O Exceptions
class FileOperationError(AutonomousSystemError):
    """Base exception for file operations."""
    pass

class FileReadError(FileOperationError):
    """Raised when file reading fails."""
    pass

class FileWriteError(FileOperationError):
    """Raised when file writing fails."""
    pass

class FileLockError(FileOperationError):
    """Raised when file locking fails."""
    pass

# Web Research Exceptions
class WebResearchError(AutonomousSystemError):
    """Base exception for web research operations."""
    pass

class SearchError(WebResearchError):
    """Raised when web search fails."""
    pass

class DataExtractionError(WebResearchError):
    """Raised when data extraction from web fails."""
    pass

# Configuration Exceptions
class ConfigurationError(AutonomousSystemError):
    """Base exception for configuration issues."""
    pass

class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid."""
    pass

class MissingConfigError(ConfigurationError):
    """Raised when required configuration is missing."""
    pass
logger = logging.getLogger(__name__)
