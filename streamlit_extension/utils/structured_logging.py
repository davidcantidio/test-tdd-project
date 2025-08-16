"""Small structured logging helper.

This module implements a tiny structured logger capable of producing JSON
formatted log records.  It is deliberately simplified but provides the
hooks required for tests: correlation identifiers, performance metrics
and dedicated security/business event helpers.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict


class LogFormat(str, Enum):
    JSON = "json"
    GELF = "gelf"
    PLAIN_TEXT = "plain_text"


class LogLevel(int, Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - trivial
        data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in ("correlation_id", "performance", "security", "business"):
            if hasattr(record, field):
                data[field] = getattr(record, field)
        return json.dumps(data)


@dataclass
class StructuredLogger:
    """Wrapper around :mod:`logging` providing helper methods."""

    name: str = "app"
    level: LogLevel = LogLevel.INFO
    fmt: LogFormat = LogFormat.JSON

    def __post_init__(self) -> None:
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.level.value)
        handler = logging.StreamHandler()
        formatter: logging.Formatter
        if self.fmt is LogFormat.JSON:
            formatter = _JSONFormatter()
        else:  # pragma: no cover - not used in tests
            formatter = logging.Formatter("%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        self.logger.handlers = [handler]

    # ------------------------------------------------------------------
    def log_with_correlation(self, level: LogLevel, message: str, correlation_id: str) -> None:
        extra = {"correlation_id": correlation_id}
        self.logger.log(level.value, message, extra=extra)

    def log_performance(self, message: str, **metrics: Any) -> None:
        extra = {"performance": metrics}
        self.logger.info(message, extra=extra)

    def log_security_event(self, message: str, **details: Any) -> None:
        extra = {"security": details}
        self.logger.warning(message, extra=extra)

    def log_business_event(self, message: str, **details: Any) -> None:
        extra = {"business": details}
        self.logger.info(message, extra=extra)


__all__ = [
    "StructuredLogger",
    "LogFormat",
    "LogLevel",
]
