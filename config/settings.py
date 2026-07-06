"""Application settings with validation and type safety."""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings.

    All settings are loaded from environment variables or .env file.
    Validation ensures configuration correctness at startup.
    """

    # Application settings
    app_env: str = Field(default="development", description="Environment: development/staging/production")
    app_debug: bool = Field(default=False, description="Enable debug mode")

    # Google OAuth configuration
    google_client_secret_path: str = Field(
        default="client_secret.json",
        description="Path to Google OAuth client secrets file"
    )
    google_credentials_storage_path: str = Field(
        default="credentials.storage",
        description="Path to store OAuth credentials"
    )
    blogger_api_scopes: str = Field(
        default="https://www.googleapis.com/auth/blogger",
        description="OAuth scopes for Blogger API (comma-separated)"
    )

    # Blogger configuration
    blogger_blog_id: str = Field(
        description="Default Blogger Blog ID for operations"
    )

    def get_scopes(self) -> List[str]:
        """Parse scopes from comma-separated string."""
        return [s.strip() for s in self.blogger_api_scopes.split(",") if s.strip()]

    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Logging format: json or plain")
    log_file_path: Path = Field(
        default=Path("logs/blogger_automation.log"),
        description="Path to log file"
    )

    # AI Configuration (Phase 4)
    openrouter_api_key: Optional[str] = Field(
        default=None,
        description="OpenRouter API key for unified model access"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude models"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for GPT models"
    )
    ai_default_provider: str = Field(
        default="openrouter",
        description="Default AI provider: openrouter, anthropic, or openai"
    )
    ai_default_model: str = Field(
        default="poolside-xs-free",
        description="Default model for AI operations (using free OpenRouter model)"
    )
    ai_max_tokens: int = Field(
        default=4000,
        description="Maximum tokens for AI generation"
    )
    ai_temperature: float = Field(
        default=0.7,
        description="Temperature for AI generation (0.0-1.0)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got {v}")
        return v.upper()

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format is supported."""
        allowed = {"json", "plain"}
        if v.lower() not in allowed:
            raise ValueError(f"log_format must be one of {allowed}, got {v}")
        return v.lower()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses LRU cache to ensure settings are loaded only once per process.
    Call this instead of Settings() directly for performance.
    """
    return Settings()


# Convenience function for backward compatibility
def load_settings() -> Settings:
    """Load settings (alias for get_settings)."""
    return get_settings()