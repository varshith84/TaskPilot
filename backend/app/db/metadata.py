"""
SQLite metadata repository for documents.

Uses Python's built-in sqlite3 — no heavy ORM needed for a single table.
All database access is isolated here; no SQL appears in API routes or services.

Schema:
    documents (
        document_id     TEXT PRIMARY KEY,
        filename        TEXT NOT NULL,          -- original user filename
        stored_filename TEXT NOT NULL,          -- collision-safe on-disk name
        file_type       TEXT NOT NULL,          -- 'pdf', 'txt', 'md', 'docx'
        file_size       INTEGER NOT NULL,       -- bytes
        pages           INTEGER,                -- NULL when not applicable
        chunks          INTEGER NOT NULL DEFAULT 0,
        status          TEXT NOT NULL DEFAULT 'processing',
        created_at      TEXT NOT NULL            -- ISO-8601 UTC
    )
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


def _db_path() -> Path:
    """Return the absolute path to the SQLite database file.

    Reads DATABASE_URL from settings; falls back to a sane default.
    Handles both ``sqlite:///./file.db`` and plain path strings.
    """
    from app.core.config import settings  # local import to avoid circular deps

    url: str = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        raw = url[len("sqlite:///"):]
        path = Path(raw)
        if not path.is_absolute():
            # Relative path → resolve relative to backend directory
            backend_dir = Path(__file__).resolve().parents[2]
            path = (backend_dir / path).resolve()
    else:
        path = Path(url).resolve()

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager yielding an auto-committed/rolled-back connection."""
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they do not already exist."""
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id     TEXT PRIMARY KEY,
                filename        TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                file_type       TEXT NOT NULL,
                file_size       INTEGER NOT NULL,
                pages           INTEGER,
                chunks          INTEGER NOT NULL DEFAULT 0,
                status          TEXT NOT NULL DEFAULT 'processing',
                created_at      TEXT NOT NULL
            )
        """)
    logger.debug("Database initialised at %s", _db_path())


# ---------------------------------------------------------------------------
# Document record as a plain dataclass-like dict helper
# ---------------------------------------------------------------------------


class DocumentRecord:
    """Thin wrapper around a sqlite3.Row for type-safe access."""

    def __init__(self, row: sqlite3.Row) -> None:
        self._row = row

    @property
    def document_id(self) -> str:
        return self._row["document_id"]

    @property
    def filename(self) -> str:
        return self._row["filename"]

    @property
    def stored_filename(self) -> str:
        return self._row["stored_filename"]

    @property
    def file_type(self) -> str:
        return self._row["file_type"]

    @property
    def file_size(self) -> int:
        return self._row["file_size"]

    @property
    def pages(self) -> Optional[int]:
        return self._row["pages"]

    @property
    def chunks(self) -> int:
        return self._row["chunks"]

    @property
    def status(self) -> str:
        return self._row["status"]

    @property
    def created_at(self) -> str:
        return self._row["created_at"]

    def to_dict(self) -> dict:
        return dict(self._row)


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------


def insert_document(
    document_id: str,
    filename: str,
    stored_filename: str,
    file_type: str,
    file_size: int,
    pages: Optional[int] = None,
    chunks: int = 0,
    status: str = "processing",
) -> None:
    """Insert a new document record."""
    created_at = datetime.now(timezone.utc).isoformat()
    with _db() as conn:
        conn.execute(
            """
            INSERT INTO documents
                (document_id, filename, stored_filename, file_type,
                 file_size, pages, chunks, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (document_id, filename, stored_filename, file_type,
             file_size, pages, chunks, status, created_at),
        )


def update_document_after_ingestion(
    document_id: str,
    chunks: int,
    pages: Optional[int] = None,
    status: str = "ready",
) -> None:
    """Update chunk count, page count and status after successful ingestion."""
    with _db() as conn:
        conn.execute(
            """
            UPDATE documents
            SET chunks = ?, pages = ?, status = ?
            WHERE document_id = ?
            """,
            (chunks, pages, status, document_id),
        )


def get_document(document_id: str) -> Optional[DocumentRecord]:
    """Return a single document or None."""
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE document_id = ?",
            (document_id,),
        ).fetchone()
    return DocumentRecord(row) if row else None


def list_documents() -> list[DocumentRecord]:
    """Return all documents ordered newest-first."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY created_at DESC"
        ).fetchall()
    return [DocumentRecord(r) for r in rows]


def delete_document(document_id: str) -> bool:
    """Delete a document record. Returns True if a row was deleted."""
    with _db() as conn:
        cursor = conn.execute(
            "DELETE FROM documents WHERE document_id = ?",
            (document_id,),
        )
    return cursor.rowcount > 0


def mark_document_failed(document_id: str, reason: str = "ingestion_failed") -> None:
    """Mark a document as failed so partial records are visible."""
    with _db() as conn:
        conn.execute(
            "UPDATE documents SET status = ? WHERE document_id = ?",
            (reason, document_id),
        )
