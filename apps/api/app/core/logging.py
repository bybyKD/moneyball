"""Structured logging (spec §37).

Every agent/analytic execution will emit structured JSON logs. This module
provides a JSON formatter and a small emit helper used across the API.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


class JsonFormatter(logging.Formatter):
    """Compact JSON log formatter for machine-readable observability."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        extra = getattr(record, "ctx", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.handlers.clear()
    root.addHandler(handler)
    # keep uvicorn access logs human-friendly
    logging.getLogger("uvicorn.access").setLevel("WARNING")


def emit(logger_name: str, message: str, **context: Any) -> None:
    """Emit a structured log line with arbitrary JSON-safe context."""
    logger = logging.getLogger(logger_name)
    logger.info(message, extra={"ctx": context})
