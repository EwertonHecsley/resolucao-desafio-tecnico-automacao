"""Configuração da aplicação usando Pydantic Settings."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # Project
    PROJECT_NAME: str = "IA Classifier API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # Health Check
    HEALTH_CHECK_ENABLED: bool = True

    # AI Provider
    AI_PROVIDER: Literal["openai", "google", "anthropic"] = "openai"
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
