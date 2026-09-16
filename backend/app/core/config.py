    # AI / LLM (optional; the API boots without provider credentials)
    # Web search (optional; unavailable without a provider credential)
    # Database (document metadata and graph checkpoint paths)
    # RAG parameters
"""
Centralized application configuration using Pydantic Settings.

All environment variables are read from the environment or a .env file.
Sensitive values (API keys) are never logged.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Resolve the repository root so relative paths work regardless of cwd.
# backend/app/core/config.py  →  go up 3 levels  →  TaskPilot/
# ---------------------------------------------------------------------------
_BACKEND_DIR: Path = Path(__file__).resolve().parents[2]  # backend/
_REPO_ROOT: Path = _BACKEND_DIR.parent  # TaskPilot/


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_NAME: str = "TaskPilot"
    APP_ENV: str = Field(default="development", description="development | staging | production")
    APP_VERSION: str = "0.1.0"

    # ------------------------------------------------------------------
    # AI / LLM (optional — not required to boot in Phase 1)
    # ------------------------------------------------------------------
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key — not required for Phase 1")
    GEMINI_MODEL: str = Field(default="gemini-3.6-flash", description="Gemini model identifier")

    # ------------------------------------------------------------------
    # Web search (optional — not required to boot in Phase 1)
    # ------------------------------------------------------------------
    TAVILY_API_KEY: str = Field(default="", description="Tavily search API key — not required for Phase 1")

    # ------------------------------------------------------------------
    # Storage paths
    # ------------------------------------------------------------------
    VECTOR_STORE_PATH: Path = Field(
        default=_REPO_ROOT / "data" / "vector_store",
        description="Directory for persistent FAISS vector index",
    )
    UPLOAD_DIR: Path = Field(
        default=_REPO_ROOT / "data" / "uploads",
        description="Directory for uploaded user documents",
    )

    # ------------------------------------------------------------------
    # Database (future SQLite checkpoint store)
    # ------------------------------------------------------------------
    DATABASE_URL: str = Field(
        default="sqlite:///./taskpilot.db",
        description="SQLAlchemy-compatible database URL",
    )

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    FRONTEND_ORIGIN: str = Field(
        default="http://localhost:5173",
        description="Allowed CORS origin (Vite dev server)",
    )

    # ------------------------------------------------------------------
    # File upload limits
    # ------------------------------------------------------------------
    MAX_UPLOAD_SIZE_MB: int = Field(default=20, description="Maximum upload file size in megabytes")

    # ------------------------------------------------------------------
    # RAG parameters (used in future phases)
    # ------------------------------------------------------------------
    RAG_CHUNK_SIZE: int = Field(default=1000, description="Text chunk size for document splitting")
    RAG_CHUNK_OVERLAP: int = Field(default=200, description="Overlap between consecutive text chunks")
    RAG_TOP_K: int = Field(default=5, description="Number of top documents to retrieve from vector store")

    # ------------------------------------------------------------------
    # Computed / derived helpers
    # ------------------------------------------------------------------
    @property
    def allowed_origins(self) -> List[str]:
        """Return list of allowed CORS origins."""
        return [origin.strip() for origin in self.FRONTEND_ORIGIN.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        """Return max upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @field_validator("VECTOR_STORE_PATH", "UPLOAD_DIR", mode="before")
    @classmethod
    def _resolve_path(cls, v: object) -> Path:
        """Resolve any string path to an absolute Path."""
        return Path(str(v)).resolve()

    def ensure_data_directories(self) -> None:
        """Create required data directories if they do not already exist."""
        for directory in (self.UPLOAD_DIR, self.VECTOR_STORE_PATH):
            directory.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere.
# ---------------------------------------------------------------------------
settings = Settings()
