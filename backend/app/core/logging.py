"""
Centralized logging configuration for TaskPilot.

Sets up structured, readable log output for local development and production.
API keys and secrets are NEVER logged.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional


# ---------------------------------------------------------------------------
# Log format
# ---------------------------------------------------------------------------
_DEV_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_PROD_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    *,
    env: str = "development",
    log_file: Optional[str] = None,
) -> None:
    """
    Configure root logger and suppress noisy third-party loggers.

    Args:
        level:    Logging level (e.g. logging.DEBUG, logging.INFO).
        env:      Application environment string. 'production' uses a more
                  compact format without colors.
        log_file: Optional path to write logs to a file in addition to stdout.
    """
    fmt = _DEV_FORMAT if env != "production" else _PROD_FORMAT

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]

    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=_DATE_FORMAT,
        handlers=handlers,
        force=True,  # Override any existing root logger configuration.
    )

    # ------------------------------------------------------------------
    # Silence overly verbose third-party loggers.
    # ------------------------------------------------------------------
    _quiet_loggers = [
        "httpx",
        "httpcore",
        "uvicorn.access",
        "multipart",
    ]
    for name in _quiet_loggers:
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.

    Usage::

        from app.core.logging import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)
