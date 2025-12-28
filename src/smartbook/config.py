"""
Application configuration using Pydantic Settings.
"""

import json
from typing import Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Smartbook"
    debug: bool = False
    version: str = "0.1.0"

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/smartbook"
    database_echo: bool = False

    # Security
    secret_key: str = "change-this-to-a-random-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    magic_link_token_bytes: int = 32

    # CORS
    cors_origins: Union[list[str], str] = ["http://localhost:3000", "http://localhost:3001"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from JSON string or return list as-is."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If it's a single origin, wrap it in a list
                return [v]
        return v

    # ROS1000 (will be configured per tenant)
    ros1000_wsdl_url: str = "https://www.flussituristici.servizirl.it/..."

    # Notifications
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@smartbook.app"


# Global settings instance
settings = Settings()
