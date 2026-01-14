"""Main FastAPI application for Bible Study Assistant."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from bs_assistant import __version__
from bs_assistant.api import chat, health
from bs_assistant.config import settings

# Static files directory
STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Handles startup and shutdown logic.
    """
    # Startup
    print(f"Starting Bible Study Assistant v{__version__}")
    print(f"Data directory: {settings.DATA_DIR}")
    print(f"Vector store: {settings.VECTOR_STORE_PATH}")

    yield

    # Shutdown
    print("Shutting down Bible Study Assistant")


# Create FastAPI application
app = FastAPI(
    title="Bible Study Assistant",
    description="RAG-based conversational assistant for Bible translation",
    version=__version__,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
            if settings.BS_ASSISTANT_LOG_LEVEL == "debug"
            else "An error occurred",
        },
    )


# Include routers
app.include_router(health.router, prefix="", tags=["health"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

# Backward compatibility for v1 API (used /api/chat)
app.include_router(chat.compat_router, tags=["chat-compat"])

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Root endpoint - serve the web interface
@app.get("/", response_class=FileResponse)
async def root():
    """Serve the web chat interface."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    # Fallback to API info
    return JSONResponse(
        {
            "name": "Bible Study Assistant",
            "version": __version__,
            "status": "running",
            "endpoints": {"health": "/health", "chat": "/chat", "chat_v1_compat": "/api/chat"},
        }
    )


# API info endpoint
@app.get("/api")
async def api_info() -> dict:
    """API endpoint information."""
    return {
        "name": "Bible Study Assistant",
        "version": __version__,
        "status": "running",
        "endpoints": {"health": "/health", "chat": "/chat", "chat_v1_compat": "/api/chat"},
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "bs_assistant.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
