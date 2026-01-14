"""Health check endpoint for Bible Study Assistant."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse

from bs_assistant import __version__
from bs_assistant.config import settings
from bs_assistant.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    authorization: str | None = Header(None),
) -> HealthResponse:
    """
    Health check endpoint.

    Returns the health status of the service.
    Optionally requires authentication token.
    """
    # Check authentication if enabled
    if settings.ENABLE_ADMIN_AUTH and settings.HEALTHCHECK_API_TOKEN:
        if not authorization or authorization != f"Bearer {settings.HEALTHCHECK_API_TOKEN}":
            raise HTTPException(status_code=401, detail="Unauthorized")

    # Perform health checks
    status = "healthy"
    checks = {}

    # Check vector store
    try:
        from bs_assistant.core.rag import vector_store

        collections = vector_store.list_collections()
        checks["vector_store"] = {"status": "ok", "collections": len(collections)}
    except Exception as e:
        status = "unhealthy"
        checks["vector_store"] = {"status": "error", "error": str(e)}

    # Check Bible data
    try:
        from bs_assistant.services.bible_service import bible_service

        languages = bible_service.list_available_languages()
        checks["bible_data"] = {"status": "ok", "languages": len(languages)}
    except Exception as e:
        status = "unhealthy"
        checks["bible_data"] = {"status": "error", "error": str(e)}

    # Check LLM client
    try:
        from bs_assistant.core.llm import llm_client

        # Simple token count test
        token_count = llm_client.count_tokens("test", "gpt-4o")
        checks["llm_client"] = {"status": "ok", "test_token_count": token_count}
    except Exception as e:
        status = "unhealthy"
        checks["llm_client"] = {"status": "error", "error": str(e)}

    response = HealthResponse(
        status=status,  # type: ignore[arg-type]
        timestamp=datetime.utcnow(),
        version=__version__,
    )

    # Add checks to response if in debug mode
    if settings.BS_ASSISTANT_LOG_LEVEL == "debug":
        return JSONResponse(
            status_code=200 if status == "healthy" else 503,
            content={
                **response.model_dump(),
                "checks": checks,
            },
        )

    return response


@router.get("/ready")
async def readiness_check() -> dict:
    """
    Readiness check endpoint for Kubernetes/Docker.

    Returns 200 if service is ready to accept traffic.
    """
    try:
        # Quick checks for readiness
        from bs_assistant.core.rag import vector_store

        vector_store.list_collections()
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check() -> dict:
    """
    Liveness check endpoint for Kubernetes/Docker.

    Returns 200 if service is alive.
    """
    return {"status": "alive"}
