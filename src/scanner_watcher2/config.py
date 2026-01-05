"""
Configuration management for Scanner-Watcher2.
"""

from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator


class ProcessingConfig(BaseModel):
    """Configuration for document processing."""

    file_prefixes: list[str] = Field(default_factory=lambda: ["SCAN-"])
    pages_to_extract: int = Field(ge=1, le=10, default=3)
    retry_attempts: int = Field(ge=1, le=10, default=3)
    retry_delay_seconds: int = Field(ge=1, le=60, default=5)
    temp_directory: Path | None = None

    @field_validator("file_prefixes")
    @classmethod
    def validate_file_prefixes(cls, v: list[str]) -> list[str]:
        """Validate that all prefixes are non-empty and contain valid filename characters."""
        if not v:
            raise ValueError("file_prefixes cannot be empty")
        
        validated = []
        invalid_chars = '<>:"|?*\\/\0'
        
        for prefix in v:
            if not prefix or not prefix.strip():
                raise ValueError("file_prefix cannot be empty")
            
            for char in invalid_chars:
                if char in prefix:
                    raise ValueError(
                        f"file_prefix contains invalid filename character: '{char}'"
                    )
            
            validated.append(prefix.strip())
        
        return validated
    
    @model_validator(mode="before")
    @classmethod
    def convert_legacy_prefix(cls, data: dict) -> dict:
        """Convert legacy single file_prefix to file_prefixes array."""
        if isinstance(data, dict):
            if "file_prefix" in data and "file_prefixes" not in data:
                data["file_prefixes"] = [data.pop("file_prefix")]
        return data


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
    watch_directories: list[Path] = Field(min_length=1)
    openai_api_key: str
    log_level: str = "INFO"
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    service: ServiceConfig = Field(default_factory=ServiceConfig)

    @field_validator("watch_directories")
    @classmethod
    def validate_watch_directories(cls, v: list[Path]) -> list[Path]:
        """Validate that all watch directory paths are absolute."""
        if not v:
            raise ValueError("watch_directories cannot be empty")
        
        validated = []
        for path in v:
            if not path.is_absolute():
                raise ValueError(f"watch_directory must be an absolute path: {path}")
            validated.append(path)
        
        return validated
    
    @model_validator(mode="before")
    @classmethod
    def convert_legacy_directory(cls, data: dict) -> dict:
        """Convert legacy single watch_directory to watch_directories array."""
        if isinstance(data, dict):
            if "watch_directory" in data and "watch_directories" not in data:
                data["watch_directories"] = [data.pop("watch_directory")]
        return data

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
