"""Application configuration loaded via Pydantic settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env")

    # API Keys
    OPENAI_API_KEY: str = Field(...)

    # Application
    BASE_URL: str = Field(...)
    DATA_DIR: Path = Field(default=Path("/data"))

    # Logging
    BS_ASSISTANT_LOG_LEVEL: str = Field(default="info")
    BS_ASSISTANT_LOG_DIR: Path | None = Field(default=None)
    LOG_PSEUDONYM_SECRET: str = Field(...)

    # LLM Configuration
    DEFAULT_MODEL: str = Field(default="gpt-4o")
    SIMPLE_QUERY_MODEL: str = Field(default="gpt-4o-mini")
    TEMPERATURE: float = Field(default=0.7)
    MAX_TOKENS: int = Field(default=2000)

    # RAG Configuration
    VECTOR_STORE_PATH: Path = Field(default=Path("data/chroma"))
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2")
    MAX_RETRIEVAL_RESULTS: int = Field(default=10)
    SIMILARITY_THRESHOLD: float = Field(default=0.7)

    # Verse Limits
    RETRIEVE_SCRIPTURE_VERSE_LIMIT: int = Field(default=120)
    TRANSLATE_SCRIPTURE_VERSE_LIMIT: int = Field(default=120)
    TRANSLATION_HELPS_VERSE_LIMIT: int = Field(default=5)

    # Response Configuration
    MAX_RESPONSE_TEXT_LENGTH: int = Field(default=50000)

    # Conversation History
    CONVERSATION_STORE: Literal["memory", "tinydb"] = Field(default="memory")
    CONVERSATION_HISTORY_MAX_MESSAGES: int = Field(default=10)
    CONVERSATION_HISTORY_PATH: Path = Field(default=Path("data/conversations.json"))

    # Admin/Health
    ADMIN_API_TOKEN: str | None = Field(default=None)
    HEALTHCHECK_API_TOKEN: str | None = Field(default=None)
    ENABLE_ADMIN_AUTH: bool = Field(default=True)

    # Cost Tracking
    COST_TRACKING_ENABLED: bool = Field(default=True)
    OPENAI_PRICING_JSON: str = Field(
        default=(
            "{"
            '"gpt-4o": {"input_per_million": 2.5, "output_per_million": 10.0}, '
            '"gpt-4o-mini": {"input_per_million": 0.15, "output_per_million": 0.6}'
            "}"
        )
    )


settings = Settings()  # type: ignore[call-arg]

# Set environment variables for downstream usage
os.environ.setdefault("OPENAI_API_KEY", settings.OPENAI_API_KEY)


__all__ = ["Settings", "settings"]
