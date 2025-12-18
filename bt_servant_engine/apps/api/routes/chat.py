"""Web chat API route for bible study assistant."""

from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from bt_servant_engine.adapters.web_messaging import WebMessagingAdapter
from bt_servant_engine.apps.api.dependencies import get_service_container
from bt_servant_engine.apps.api.message_processor import process_message
from bt_servant_engine.core.logging import get_logger
from bt_servant_engine.core.models import UserMessage
from bt_servant_engine.services import ServiceContainer

logger = get_logger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Request model for web chat messages."""

    message: str = Field(..., description="The user's message text", min_length=1)
    user_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique user identifier for session continuity",
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session identifier for grouping conversations",
    )


class ChatMessageResponse(BaseModel):
    """Individual response message from the assistant."""

    content: str = Field(..., description="The response message content")
    type: str = Field(default="text", description="Message type (text, voice, etc.)")


class ChatResponse(BaseModel):
    """Response model for web chat."""

    user_id: str = Field(..., description="The user identifier")
    message_id: str = Field(..., description="Unique message identifier")
    responses: list[ChatMessageResponse] = Field(
        default_factory=list,
        description="List of response messages from the assistant",
    )
    processing_time_seconds: float = Field(..., description="Time taken to process the request")
    session_id: str | None = Field(default=None, description="Session identifier if provided")


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_endpoint(
    request: ChatRequest,
    services: ServiceContainer = Depends(get_service_container),
) -> ChatResponse:
    """Process a chat message and return assistant responses.

    This endpoint accepts a text message from a web chat interface and processes
    it through the bible study assistant's RAG engine and intent routing system.
    The same brain/orchestration logic used for WhatsApp is reused here.

    Args:
        request: The chat request containing the user's message
        services: Injected service container with adapters

    Returns:
        ChatResponse with the assistant's reply messages

    Raises:
        HTTPException: If processing fails
    """
    start_time = time.time()
    message_id = str(uuid.uuid4())

    logger.info(
        "Web chat request received: user_id=%s, message_id=%s, session=%s",
        request.user_id,
        message_id,
        request.session_id,
    )

    web_adapter = WebMessagingAdapter()
    web_services = ServiceContainer(
        chroma=services.chroma,
        user_state=services.user_state,
        messaging=web_adapter,
        intent_router=services.intent_router,
    )

    user_message = UserMessage(
        user_id=request.user_id,
        text=request.message,
        message_id=message_id,
        message_type="text",
        timestamp=int(start_time),
        media_id="",
    )

    try:
        await process_message(
            user_message,
            web_services,
            correlation_id=message_id,
            client_ip=None,
        )

        responses = [
            ChatMessageResponse(content=r.content, type=r.message_type)
            for r in web_adapter.get_responses()
        ]

        processing_time = time.time() - start_time

        logger.info(
            "Web chat response sent: user_id=%s, message_id=%s, responses=%d, time=%.2fs",
            request.user_id,
            message_id,
            len(responses),
            processing_time,
        )

        return ChatResponse(
            user_id=request.user_id,
            message_id=message_id,
            responses=responses,
            processing_time_seconds=round(processing_time, 3),
            session_id=request.session_id,
        )

    except Exception as exc:
        logger.error(
            "Web chat processing failed: user_id=%s, message_id=%s, error=%s",
            request.user_id,
            message_id,
            str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message",
        ) from exc


__all__ = ["router"]
