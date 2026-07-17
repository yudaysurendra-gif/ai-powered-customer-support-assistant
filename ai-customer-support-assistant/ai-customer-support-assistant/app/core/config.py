"""
Application configuration loaded from environment variables / .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "AI Customer Support Assistant"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "insecure-dev-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite:///./data/support_assistant.db"

    # AI / NLP behavior
    INTENT_CONFIDENCE_THRESHOLD: float = 0.35
    ESCALATION_SENTIMENT_THRESHOLD: float = -0.4
    MAX_AUTO_REPLIES_PER_TICKET: int = 3

    # Optional external LLM fallback
    ENABLE_LLM_FALLBACK: bool = False
    LLM_API_KEY: str = ""
    LLM_API_URL: str = "https://api.anthropic.com/v1/messages"
    LLM_MODEL: str = "claude-sonnet-4-6"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
