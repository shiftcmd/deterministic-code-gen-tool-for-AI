"""
Configuration management for the Python Debug Tool.

This module handles loading and validation of environment variables
and application settings.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    # PostgreSQL
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/python_debug_tool",
        description="PostgreSQL database URL",
    )
    database_host: str = Field(default="localhost", description="Database host")
    database_port: int = Field(default=5432, description="Database port")
    database_name: str = Field(default="python_debug_tool", description="Database name")
    database_user: str = Field(default="user", description="Database user")
    database_password: str = Field(default="password", description="Database password")

    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="password", description="Neo4j password")
    neo4j_database: str = Field(default="neo4j", description="Neo4j database name")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")

    # Chroma DB
    chroma_host: str = Field(default="localhost", description="Chroma DB host")
    chroma_port: int = Field(default=8001, description="Chroma DB port")
    chroma_persist_directory: str = Field(
        default="./chroma_data", description="Chroma DB persistence directory"
    )


class AISettings(BaseSettings):
    """AI/ML service configuration settings."""

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4", description="Default OpenAI model")
    openai_max_tokens: int = Field(default=4000, description="Max tokens for OpenAI")

    # Anthropic
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API key"
    )
    anthropic_model: str = Field(
        default="claude-3-sonnet-20240229", description="Default Anthropic model"
    )

    # Perplexity
    perplexity_api_key: Optional[str] = Field(
        default=None, description="Perplexity API key"
    )
    perplexity_model: str = Field(
        default="sonar-pro", description="Default Perplexity model"
    )


class AppSettings(BaseSettings):
    """Main application settings."""

    # Environment
    environment: str = Field(
        default="development", description="Application environment"
    )
    debug: bool = Field(default=True, description="Debug mode")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8080, description="API port")
    api_reload: bool = Field(default=True, description="API auto-reload")

    # Security
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="Secret key for JWT tokens",
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration time in minutes"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format")
    log_file: str = Field(default="logs/app.log", description="Log file path")

    # CORS
    allowed_origins: list[str] = Field(
        default=["*"],  # Allow all origins
        description="Allowed CORS origins",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class Settings(BaseSettings):
    """Combined application settings."""

    app: AppSettings = AppSettings()
    database: DatabaseSettings = DatabaseSettings()
    ai: AISettings = AISettings()

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app.environment.lower() == "production"

    def get_database_url(self) -> str:
        """Get the complete database URL."""
        return self.database.database_url

    def get_neo4j_config(self) -> dict:
        """Get Neo4j connection configuration."""
        return {
            "uri": self.database.neo4j_uri,
            "auth": (self.database.neo4j_user, self.database.neo4j_password),
            "database": self.database.neo4j_database,
        }

    def get_redis_config(self) -> dict:
        """Get Redis connection configuration."""
        return {
            "host": self.database.redis_host,
            "port": self.database.redis_port,
            "db": self.database.redis_db,
        }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def ensure_directories() -> None:
    """Ensure required directories exist."""
    project_root = get_project_root()

    # Create logs directory
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Create chroma data directory
    chroma_dir = Path(settings.database.chroma_persist_directory)
    if not chroma_dir.is_absolute():
        chroma_dir = project_root / chroma_dir
    chroma_dir.mkdir(exist_ok=True)

    # Create analysis results directory
    results_dir = project_root / "analysis_results"
    results_dir.mkdir(exist_ok=True)


# Ensure directories exist on import
ensure_directories()
