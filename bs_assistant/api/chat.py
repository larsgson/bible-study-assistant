"""Chat endpoint for Bible Study Assistant."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from bs_assistant.models import ChatRequest, ChatResponse
from bs_assistant.services.chat_service import chat_service

router = APIRouter()

# Backward compatibility router for old /api/chat endpoint
compat_router = APIRouter(prefix="/api")


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.

    Process a user message and return a conversational response with
    RAG-retrieved resources and cost tracking.

    Args:
        request: Chat request with user message and metadata

    Returns:
        Chat response with generated text and metadata
    """
    try:
        response = chat_service.process_message(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}",
        )


@router.post("/clear")
async def clear_history(
    user_id: str,
    session_id: str | None = None,
) -> dict:
    """
    Clear conversation history for a user/session.

    Args:
        user_id: User identifier
        session_id: Optional session identifier

    Returns:
        Success message
    """
    try:
        from bs_assistant.services.conversation_service import conversation_service

        conversation_service.clear_history(user_id, session_id)
        return {"status": "success", "message": "Conversation history cleared"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing history: {str(e)}",
        )


@router.get("/sessions/{user_id}")
async def list_sessions(user_id: str) -> dict:
    """
    List all sessions for a user.

    Args:
        user_id: User identifier

    Returns:
        List of session IDs and summaries
    """
    try:
        from bs_assistant.services.conversation_service import conversation_service

        sessions = conversation_service.list_sessions(user_id)
        summaries = {}

        for session_id in sessions:
            sid = session_id if session_id != "default" else None
            summary = conversation_service.get_session_summary(user_id, sid)
            summaries[session_id] = summary

        return {"user_id": user_id, "sessions": summaries}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing sessions: {str(e)}",
        )


@router.get("/history/{user_id}")
async def get_history(
    user_id: str,
    session_id: str | None = None,
    limit: int = 10,
) -> dict:
    """
    Get conversation history for a user/session.

    Args:
        user_id: User identifier
        session_id: Optional session identifier
        limit: Maximum number of messages to return

    Returns:
        Conversation history
    """
    try:
        from bs_assistant.services.conversation_service import conversation_service

        history = conversation_service.get_history(user_id, session_id, limit)
        return {
            "user_id": user_id,
            "session_id": session_id,
            "history": history,
            "count": len(history),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting history: {str(e)}",
        )


# Backward compatibility endpoints (v1 used /api/chat instead of /chat)
@compat_router.post("/chat", response_model=ChatResponse)
async def chat_compat(request: ChatRequest) -> ChatResponse:
    """
    Backward compatible chat endpoint for v1 API.

    Old v1 endpoint was: POST /api/chat
    New v2 endpoint is: POST /chat

    This provides backward compatibility.
    """
    return await chat(request)
