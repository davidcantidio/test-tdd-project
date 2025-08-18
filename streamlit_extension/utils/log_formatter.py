"""
JSON Log Formatter for structured logging
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""

        # Start with basic log record
        log_entry = {
            "event": "log",
            "timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Normalize correlation id if passed via extra / filter
        corr_id = getattr(record, "correlation_id", None)
        if corr_id:
            log_entry["correlation_id"] = corr_id

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "message",  # avoid duplicating the message
                "sinfo",
                "exc_info", "exc_text", "stack_info",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                # commonly added by handlers/filters:
                "asctime",
            ]:
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class CorrelationFilter(logging.Filter):
    """Filter to add correlation ID to all log records"""

    def __init__(self) -> None:
        super().__init__()
        from .correlation_logging import CorrelationIDManager

        self.correlation_manager = CorrelationIDManager()

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record"""
        correlation_id = self.correlation_manager.get_current_correlation_id()
        if correlation_id:
            record.correlation_id = correlation_id
        return True
