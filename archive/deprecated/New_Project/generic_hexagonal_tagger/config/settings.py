"""
Configuration settings for the Generic Hexagonal Architecture Tagging System.

This module defines the configuration schema and provides centralized access
to all system settings, including AI services, Neo4j, logging, and analysis parameters.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class LogLevel(str, Enum):
    """Available logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AIProvider(str, Enum):
    """Supported AI service providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class Neo4jConfig(BaseModel):
    """Neo4j database configuration."""

    uri: str = Field(
        default="bolt://localhost:7687", description="Neo4j connection URI"
    )
    username: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(default="password", description="Neo4j password")
    database: str = Field(default="neo4j", description="Neo4j database name")
    max_connection_lifetime: int = Field(
        default=3600, description="Max connection lifetime in seconds"
    )
    max_connection_pool_size: int = Field(
        default=50, description="Max connection pool size"
    )
    connection_timeout: int = Field(
        default=30, description="Connection timeout in seconds"
    )

    class Config:
        env_prefix = "NEO4J_"


class AIConfig(BaseModel):
    """AI service configuration."""

    provider: AIProvider = Field(
        default=AIProvider.OPENAI, description="AI service provider"
    )
    api_key: Optional[str] = Field(default=None, description="API key for AI service")
    model: str = Field(default="gpt-4o-mini", description="Model to use for analysis")
    max_tokens: int = Field(default=4000, description="Maximum tokens per request")
    temperature: float = Field(
        default=0.1, ge=0.0, le=2.0, description="Temperature for AI responses"
    )
    timeout: int = Field(default=60, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    batch_size: int = Field(default=10, description="Batch size for bulk processing")

    # Model-specific settings
    openai_base_url: Optional[str] = Field(
        default=None, description="Custom OpenAI base URL"
    )
    anthropic_base_url: Optional[str] = Field(
        default=None, description="Custom Anthropic base URL"
    )

    class Config:
        env_prefix = "AI_"

    @validator("api_key")
    def validate_api_key(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> Optional[str]:
        """Validate API key based on provider."""
        provider = values.get("provider")
        if provider in [AIProvider.OPENAI, AIProvider.ANTHROPIC] and not v:
            # Try to get from environment
            env_key = f"{provider.value.upper()}_API_KEY"
            v = os.getenv(env_key)
            if not v:
                raise ValueError(f"API key required for provider {provider}")
        return v


class AnalysisConfig(BaseModel):
    """Configuration for code analysis parameters."""

    # File filtering
    include_patterns: List[str] = Field(
        default=["*.py", "*.js", "*.ts", "*.java", "*.cs", "*.cpp", "*.c", "*.h"],
        description="File patterns to include in analysis",
    )
    exclude_patterns: List[str] = Field(
        default=[
            "*.pyc",
            "*.pyo",
            "__pycache__",
            ".git",
            ".svn",
            "node_modules",
            "*.min.js",
        ],
        description="File patterns to exclude from analysis",
    )
    exclude_directories: List[str] = Field(
        default=[
            ".git",
            ".svn",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
        ],
        description="Directories to exclude from analysis",
    )

    # Analysis parameters
    max_file_size: int = Field(
        default=1024 * 1024, description="Maximum file size to analyze (bytes)"
    )
    min_confidence_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum confidence for tag assignment"
    )
    enable_ai_tagging: bool = Field(
        default=True, description="Enable AI-assisted tagging"
    )
    enable_static_analysis: bool = Field(
        default=True, description="Enable static code analysis"
    )
    enable_pattern_detection: bool = Field(
        default=True, description="Enable design pattern detection"
    )

    # Performance settings
    parallel_processing: bool = Field(
        default=True, description="Enable parallel processing"
    )
    max_workers: int = Field(default=4, description="Maximum number of worker threads")
    batch_processing: bool = Field(
        default=True, description="Enable batch processing for AI requests"
    )
    cache_results: bool = Field(default=True, description="Cache analysis results")

    # Validation settings
    enable_validation: bool = Field(
        default=True, description="Enable result validation"
    )
    cross_validation: bool = Field(
        default=True,
        description="Enable cross-validation between AI and static analysis",
    )
    human_in_loop: bool = Field(
        default=False, description="Enable human-in-the-loop validation"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        description="Log message format",
    )
    file_path: Optional[str] = Field(default=None, description="Log file path")
    max_file_size: str = Field(default="10 MB", description="Maximum log file size")
    backup_count: int = Field(default=5, description="Number of backup log files")
    enable_console: bool = Field(default=True, description="Enable console logging")
    enable_file: bool = Field(default=False, description="Enable file logging")

    class Config:
        env_prefix = "LOG_"


class CacheConfig(BaseModel):
    """Caching configuration."""

    enabled: bool = Field(default=True, description="Enable caching")
    backend: str = Field(
        default="memory", description="Cache backend (memory, redis, file)"
    )
    ttl: int = Field(default=3600, description="Time to live in seconds")
    max_size: int = Field(default=1000, description="Maximum cache size")

    # File cache settings
    cache_dir: str = Field(
        default=".cache", description="Cache directory for file backend"
    )

    # Redis settings (if using Redis backend)
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")

    class Config:
        env_prefix = "CACHE_"


class TaggingSystemSettings(BaseSettings):
    """
    Main configuration class for the Generic Hexagonal Architecture Tagging System.

    This class aggregates all configuration sections and provides environment variable
    support with proper validation and defaults.
    """

    # Basic settings
    project_name: str = Field(
        default="Generic Hexagonal Tagger", description="Project name"
    )
    version: str = Field(default="0.1.0", description="Project version")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Configuration sections
    neo4j: Neo4jConfig = Field(
        default_factory=Neo4jConfig, description="Neo4j configuration"
    )
    ai: AIConfig = Field(
        default_factory=AIConfig, description="AI service configuration"
    )
    analysis: AnalysisConfig = Field(
        default_factory=AnalysisConfig, description="Analysis configuration"
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="Logging configuration"
    )
    cache: CacheConfig = Field(
        default_factory=CacheConfig, description="Cache configuration"
    )

    # Plugin settings
    plugin_directories: List[str] = Field(
        default_factory=list, description="Plugin directories"
    )
    enabled_plugins: List[str] = Field(
        default_factory=list, description="Enabled plugins"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("logging")
    def setup_logging_defaults(
        cls, v: LoggingConfig, values: Dict[str, Any]
    ) -> LoggingConfig:
        """Set up logging defaults based on debug mode."""
        debug = values.get("debug", False)
        if debug and v.level == LogLevel.INFO:
            v.level = LogLevel.DEBUG
        return v

    def get_cache_dir(self) -> Path:
        """Get the cache directory path."""
        cache_dir = Path(self.cache.cache_dir)
        if not cache_dir.is_absolute():
            cache_dir = Path.cwd() / cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def get_log_file_path(self) -> Optional[Path]:
        """Get the log file path if file logging is enabled."""
        if not self.logging.enable_file or not self.logging.file_path:
            return None

        log_path = Path(self.logging.file_path)
        if not log_path.is_absolute():
            log_path = Path.cwd() / log_path

        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path

    def is_file_included(self, file_path: str) -> bool:
        """Check if a file should be included in analysis."""
        from fnmatch import fnmatch

        file_name = Path(file_path).name

        # Check exclude patterns first
        for pattern in self.analysis.exclude_patterns:
            if fnmatch(file_name, pattern):
                return False

        # Check if any parent directory is excluded
        path_parts = Path(file_path).parts
        for exclude_dir in self.analysis.exclude_directories:
            if exclude_dir in path_parts:
                return False

        # Check include patterns
        for pattern in self.analysis.include_patterns:
            if fnmatch(file_name, pattern):
                return True

        return False

    def should_use_ai_tagging(self) -> bool:
        """Check if AI tagging should be used."""
        return (
            self.analysis.enable_ai_tagging
            and self.ai.api_key is not None
            and self.ai.provider in [AIProvider.OPENAI, AIProvider.ANTHROPIC]
        )

    def get_effective_max_workers(self) -> int:
        """Get the effective number of worker threads."""
        if not self.analysis.parallel_processing:
            return 1

        import multiprocessing

        cpu_count = multiprocessing.cpu_count()
        return min(self.analysis.max_workers, cpu_count)


# Global settings instance
_settings: Optional[TaggingSystemSettings] = None


def get_settings() -> TaggingSystemSettings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = TaggingSystemSettings()
    return _settings


def reload_settings() -> TaggingSystemSettings:
    """Reload settings from environment and configuration files."""
    global _settings
    _settings = TaggingSystemSettings()
    return _settings
