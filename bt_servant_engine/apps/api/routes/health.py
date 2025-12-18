"""Health and readiness routes."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from ..dependencies import require_healthcheck_token

router = APIRouter()


@router.get("/health")
async def health_check() -> JSONResponse:
    """Simple unauthenticated health check endpoint."""
    return JSONResponse({"status": "healthy"})


@router.get("/alive")
async def alive_check(_: None = Depends(require_healthcheck_token)) -> JSONResponse:
    """Authenticated health check endpoint for infrastructure probes."""
    return JSONResponse({"status": "ok", "message": "BT Servant is alive and healthy."})


__all__ = ["router"]
