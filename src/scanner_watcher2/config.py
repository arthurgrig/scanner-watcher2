"""
Configuration management for Scanner-Watcher2.
"""

from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator


class ProcessingConfig(BaseModel):
    """Configuration for document processing."""

    file_prefix: str = "SCAN-"
    pages_to_extract: int = Field(ge=1, le=10, default=3)
    retry_attempts: int = Field(ge=1, le=10, default=3)
    retry_delay_seconds: int = Field(ge=1, le=60, default=5)
    temp_directory: Path | None = None

    @field_validator("file_prefix")
    @classmethod
    def validate_file_prefix(cls, v: str) -> str:
        """Validate that file prefix is non-empty and contains valid filename characters."""
        if not v or not v.strip():
            raise ValueError("file_prefix cannot be empty")
        
        # Check for invalid Windows filename characters
        invalid_chars = '<>:"|?*\\/\0'
        for char in invalid_chars:
            if char in v:
                raise ValueError(
                    f"file_prefix contains invalid filename character: '{char}'"
                )
        
        return v.strip()


class AIConfig(BaseModel):
    """Configuration for AI service."""

    model: str = "gpt-4-vision-preview"
    max_tokens: int = 500
    temperature: float = 0.1
    timeout_seconds: int = 30


class LoggingConfig(BaseModel):
    """Configuration for logging system."""

    max_file_size_mb: int = 10
    backup_count: int = 5
    log_to_event_log: bool = True


class ServiceConfig(BaseModel):
    """Configuration for service orchestration."""

    health_check_interval_seconds: int = 60
    graceful_shutdown_timeout_seconds: int = 30


class Config(BaseModel):
    """Main application configuration."""

    version: str
    watch_directory: Path
    openai_api_key: str
    log_level: str = "INFO"
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    service: ServiceConfig = Field(default_factory=ServiceConfig)

    @field_validator("watch_directory")
    @classmethod
    def validate_watch_directory(cls, v: Path) -> Path:
        """Validate that watch directory path is absolute."""
        if not v.is_absolute():
            raise ValueError("watch_directory must be an absolute path")
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate that API key is not empty."""
        if not v or not v.strip():
            raise ValueError("openai_api_key cannot be empty")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(
                f"log_level must be one of {valid_levels}, got '{v}'"
            )
        return v.upper()
