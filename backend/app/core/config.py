"""Typed application settings.

Values come from environment variables and/or a local `.env` file, so secrets (the
Google Gemini API key) and machine-specific paths (the ChromaDB directory) never end up
in version control. See `.env.example` for the supported keys.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Job Pulse backend."""

    model_config = SettingsConfigDict(
        # `env_file` paths are resolved relative to the process working directory, i.e.
        # `backend/` when the documented `uv run ...` commands are used.
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Unknown keys in `.env` are ignored, so later stages can add variables before
        # this class knows about them.
        extra="ignore",
    )

    # --- API metadata ---------------------------------------------------------------
    service_name: str = "jobpulse-backend"
    environment: str = "development"

    # --- CORS -----------------------------------------------------------------------
    # The Next.js frontend (Stage 8) runs on :3000 and calls this API from the browser.
    # List values must be provided as JSON in the environment, e.g.
    # CORS_ORIGINS=["http://localhost:3000","https://jobpulse.example"].
    cors_origins: list[str] = ["http://localhost:3000"]

    # --- Placeholders for later stages ----------------------------------------------
    # Deliberately commented out (not dead code) so Stage 4/6 only need to uncomment and
    # fill values instead of restructuring configuration:
    # gemini_api_key: str | None = None            # Stage 6 - Google Gemini API key
    # embedding_model_name: str = "BAAI/bge-m3"    # Stage 4 - same model for index + query
    # chroma_persist_dir: str = "../data/chroma"   # Stage 4 - persistent ChromaDB directory


@lru_cache
def get_settings() -> Settings:
    """Return process-wide settings, parsed once per process.

    Cached so it can be used as a FastAPI dependency without re-reading the environment
    on every request. Tests that need custom values can call ``get_settings.cache_clear()``.
    """
    return Settings()
