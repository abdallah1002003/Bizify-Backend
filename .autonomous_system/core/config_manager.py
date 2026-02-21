"""
Configuration Management for Autonomous System
Centralized configuration with validation using Pydantic.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator
import json
import os

class PatternLearningConfig(BaseModel):
    """Configuration for pattern learning system."""
    
    max_patterns: int = Field(default=100000, ge=1000, description="Maximum patterns to store")
    cache_size: int = Field(default=128, ge=16, description="LRU cache size")
    deduplication_enabled: bool = Field(default=True, description="Enable pattern deduplication")
    auto_save_interval: int = Field(default=60, ge=10, description="Auto-save interval in seconds")
    backup_enabled: bool = Field(default=True, description="Enable automatic backups")

class EvolutionConfig(BaseModel):
    """Configuration for evolution system."""
    
    enabled: bool = Field(default=True, description="Enable evolution system")
    max_iterations: int = Field(default=3, ge=1, le=10, description="Max evolution iterations per file")
    add_docstrings: bool = Field(default=True, description="Add missing docstrings")
    add_type_hints: bool = Field(default=True, description="Add missing type hints")
    refactor_enabled: bool = Field(default=False, description="Enable code refactoring")
    safety_checks: bool = Field(default=True, description="Enable safety checks before evolution")

class SwarmConfig(BaseModel):
    """Configuration for swarm operations."""
    
    enabled: bool = Field(default=True, description="Enable swarm mode")
    max_workers: int = Field(default=4, ge=1, le=16, description="Maximum concurrent workers")
    heartbeat_interval: int = Field(default=30, ge=5, description="Heartbeat interval in seconds")
    directive_timeout: int = Field(default=300, ge=60, description="Directive timeout in seconds")

class MonitoringConfig(BaseModel):
    """Configuration for monitoring and metrics."""
    
    enabled: bool = Field(default=True, description="Enable monitoring")
    metrics_port: int = Field(default=9090, ge=1024, le=65535, description="Metrics server port")
    log_level: str = Field(default="INFO", description="Logging level")
    structured_logging: bool = Field(default=True, description="Use JSON structured logging")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

class SecurityConfig(BaseModel):
    """Configuration for security settings."""
    
    enable_code_signing: bool = Field(default=False, description="Enable code signing")
    max_file_size_mb: int = Field(default=10, ge=1, le=100, description="Max file size to process")
    allowed_extensions: List[str] = Field(
        default=[".py", ".js", ".ts", ".java", ".go"],
        description="Allowed file extensions"
    )
    sandbox_enabled: bool = Field(default=True, description="Enable sandbox for code execution")

class AutonomousSystemConfig(BaseModel):
    """Main configuration for autonomous system."""
    
    project_root: Path = Field(default=Path.cwd(), description="Project root directory")
    environment: str = Field(default="development", description="Environment (development/production)")
    
    pattern_learning: PatternLearningConfig = Field(default_factory=PatternLearningConfig)
    evolution: EvolutionConfig = Field(default_factory=EvolutionConfig)
    swarm: SwarmConfig = Field(default_factory=SwarmConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f"environment must be one of {valid_envs}")
        return v
    
    class Config:
        arbitrary_types_allowed = True

class ConfigManager:
    """
    Manages configuration loading, validation, and updates.
    Supports environment-specific configs and runtime updates.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(".autonomous_system/config/config.json")
        self.config: AutonomousSystemConfig = self._load_config()
    
    def _load_config(self) -> AutonomousSystemConfig:
        """Load configuration from file or environment."""
        # Try to load from file
        if self.config_path.exists():
            try:
                config_data = json.loads(self.config_path.read_text())
                return AutonomousSystemConfig(**config_data)
            except Exception as e:
                print(f"⚠️ Failed to load config from {self.config_path}: {e}")
        
        # Load from environment variables
        config_data = self._load_from_env()
        
        # Use defaults if no config found
        return AutonomousSystemConfig(**config_data)
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config_data: Dict[str, Any] = {}
        
        # Pattern learning
        if os.getenv("AS_MAX_PATTERNS"):
            config_data.setdefault("pattern_learning", {})["max_patterns"] = int(os.getenv("AS_MAX_PATTERNS"))
        
        # Evolution
        if os.getenv("AS_EVOLUTION_ENABLED"):
            config_data.setdefault("evolution", {})["enabled"] = os.getenv("AS_EVOLUTION_ENABLED").lower() == "true"
        
        # Swarm
        if os.getenv("AS_MAX_WORKERS"):
            config_data.setdefault("swarm", {})["max_workers"] = int(os.getenv("AS_MAX_WORKERS"))
        
        # Monitoring
        if os.getenv("AS_LOG_LEVEL"):
            config_data.setdefault("monitoring", {})["log_level"] = os.getenv("AS_LOG_LEVEL")
        
        # Environment
        if os.getenv("AS_ENVIRONMENT"):
            config_data["environment"] = os.getenv("AS_ENVIRONMENT")
        
        return config_data
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = self.config.dict()
        # Convert Path to string for JSON serialization
        config_dict["project_root"] = str(config_dict["project_root"])
        
        self.config_path.write_text(json.dumps(config_dict, indent=2))
        print(f"✅ Configuration saved to {self.config_path}")
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        config_dict = self.config.dict()
        config_dict.update(updates)
        self.config = AutonomousSystemConfig(**config_dict)
        print("✅ Configuration updated")
    
    def get_config(self) -> AutonomousSystemConfig:
        """Get current configuration."""
        return self.config
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()
        print("🔄 Configuration reloaded")
