"""Pydantic models for API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=10000)
    user_id: str = Field(..., min_length=1)
    session_id: str | None = None
    language: str = Field(default="en")
    translation_id: str | None = None


class RetrievedResource(BaseModel):
    """A resource retrieved via RAG."""

    type: str
    content: str
    reference: str | None = None
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str
    session_id: str
    retrieved_resources: list[RetrievedResource] = Field(default_factory=list)
    model_used: str | None = None
    tokens_used: int | None = None
    cost_usd: float | None = None


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: Literal["healthy", "unhealthy"]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "2.0.0"


__all__ = [
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "RetrievedResource",
    "HealthResponse",
]
