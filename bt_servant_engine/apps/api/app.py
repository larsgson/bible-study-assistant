"""FastAPI application factory and shared API state."""

from __future__ import annotations

import asyncio
import concurrent.futures
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request

from bt_servant_engine.apps.api.limiter import limiter
from bt_servant_engine.apps.api.middleware import CorrelationIdMiddleware
from bt_servant_engine.apps.api.routes import (
    admin_datastore,
    admin_logs,
    admin_status_messages,
    chat,
    health,
)
from bt_servant_engine.core.logging import get_logger
from bt_servant_engine.services import ServiceContainer, runtime
from bt_servant_engine.services.brain_orchestrator import create_brain

from .state import get_brain, set_brain

logger = get_logger(__name__)


def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors with better user messaging."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": "You have exceeded the rate limit of 10 requests per hour. Please try again later. This is a demo environment with strict rate limiting. Contact support for higher limits.",
            "message": "You have exceeded the rate limit of 10 requests per hour. Please try again later. This is a demo environment with strict rate limiting. Contact support for higher limits.",
            "limit": "10 per hour",
            "retry_after": "1 hour",
        },
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared resources at startup and clean up on shutdown."""
    logger.info("Initializing bt servant engine...")
    logger.info("Loading brain...")
    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=64)
    loop.set_default_executor(executor)
    # Ensure runtime registry is populated even for non-HTTP contexts (e.g., CLI tests)
    services = getattr(app.state, "services", None)
    if isinstance(services, ServiceContainer):
        runtime.set_services(services)
    set_brain(create_brain())
    logger.info("brain loaded.")
    try:
        yield
    finally:
        executor.shutdown(wait=False)


def create_app(services: ServiceContainer | None = None) -> FastAPI:
    """Build the FastAPI application with configured routers."""
    if services is None:
        raise RuntimeError("Service container must be provided when creating the app.")
    app = FastAPI(lifespan=lifespan)
    service_container = services
    app.state.services = service_container
    runtime.set_services(service_container)

    # Add rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(SlowAPIMiddleware)

    # Mount static files for web chat interface first
    static_dir = Path(__file__).parent.parent.parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info("Mounted static files from: %s", static_dir)

        # Add root redirect before other routers to override health.router root
        @app.get("/", include_in_schema=False)
        async def root():
            return RedirectResponse(url="/static/index.html")
    else:
        logger.warning("Static directory not found: %s", static_dir)

    # Include routers after static files and root override
    app.include_router(health.router)
    app.include_router(admin_logs.router)
    app.include_router(admin_status_messages.router)
    app.include_router(admin_datastore.router)
    app.include_router(chat.router)

    return app


__all__ = ["create_app", "get_brain", "set_brain", "lifespan"]
