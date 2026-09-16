"""FastAPI application entry point for the Job Pulse backend.

Run locally (from the `backend/` directory):

    uv run fastapi dev app/main.py     # auto-reload + Swagger UI on /docs
    # or
    uv run uvicorn app.main:app --reload
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes.health import router as health_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage process-wide resources for the application's lifetime.

    Stage 0 intentionally starts and stops nothing. Later stages will warm up the
    expensive, process-wide objects here instead of per request:
      * Stage 4 - the sentence-transformers embedding model and the ChromaDB client
      * Stage 6 - the Google Gemini client
    """
    # --- startup ---
    yield
    # --- shutdown ---


def create_app() -> FastAPI:
    """Build the FastAPI application.

    Uses the factory form so tests (and later CI) can build isolated instances via
    `create_app()` instead of importing a partially configured module-level app.
    """
    settings = get_settings()

    application = FastAPI(
        title="Job Pulse API",
        description=(
            "Analyze a resume against real Iranian job postings using RAG: retrieval "
            "from ChromaDB plus skill-gap generation with Google Gemini."
        ),
        version=__version__,
        lifespan=lifespan,
    )

    # The Next.js frontend (Stage 8) is served from a different origin, so CORS origins
    # come from settings instead of being hard-coded.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Feature routers. Stage 7 adds `analyze_router` (`POST /analyze`) alongside this one.
    application.include_router(health_router)

    return application


# Module-level instance referenced by `uvicorn app.main:app` / `fastapi dev app/main.py`.
app = create_app()
