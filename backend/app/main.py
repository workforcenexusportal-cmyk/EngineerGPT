"""EngineerGPT FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RateLimitMiddleware, RequestContextMiddleware

configure_logging("INFO" if settings.environment != "development" else "DEBUG")
logger = get_logger("engineergpt.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "startup",
        extra={
            "extra_fields": {
                "environment": settings.environment,
                "ai_mock": settings.use_mock_ai,
            }
        },
    )
    yield
    logger.info("shutdown")


app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="AI Operating System for Manufacturing Engineers",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, limit=120, window_seconds=60)
app.add_middleware(RequestContextMiddleware)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.project_name, "version": "0.1.0"}
