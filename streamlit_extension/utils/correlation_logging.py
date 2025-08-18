"""
Correlation ID Logging System
Provides request tracking and structured logging for multi-user environments
"""

import uuid
import time
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional, Union
from contextlib import contextmanager
from functools import wraps
import threading

# Safe imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None


class CorrelationIDManager:
    """Manages correlation IDs for request tracking"""

    def __init__(self) -> None:
        self._correlation_storage = {}

    def generate_correlation_id(self, prefix: str = "req") -> str:
        """Generate a new correlation ID"""
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    def get_current_correlation_id(self) -> Optional[str]:
        """Get current correlation ID from context"""
        if STREAMLIT_AVAILABLE and st and hasattr(st, "session_state"):
            return st.session_state.get("correlation_id")
        return self._correlation_storage.get(threading.get_ident())

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID in current context"""
        if STREAMLIT_AVAILABLE and st and hasattr(st, "session_state"):
            st.session_state["correlation_id"] = correlation_id
        else:
            self._correlation_storage[threading.get_ident()] = correlation_id

    def ensure_correlation_id(self) -> str:
        """Ensure correlation ID exists, create if needed"""
        correlation_id = self.get_current_correlation_id()
        if not correlation_id:
            correlation_id = self.generate_correlation_id()
            self.set_correlation_id(correlation_id)
        return correlation_id


class StructuredLogger:
    """Structured logging with correlation ID support"""

    def __init__(self, name: str) -> None:
        self.logger = logging.getLogger(name)
        self.correlation_manager = CorrelationIDManager()

        # Configure JSON formatter if not already configured
        if not self.logger.handlers:
            self._setup_json_logging()

    def _setup_json_logging(self) -> None:
        """Setup JSON-based logging format"""
        from .log_formatter import JSONFormatter

        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        # Evita handlers duplicados em hot-reload
        if not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _get_session_info(self) -> Dict[str, Any]:
        """Extract session information"""
        session_info: Dict[str, Any] = {}

        if STREAMLIT_AVAILABLE and st and hasattr(st, "session_state"):
            session_info["session_id"] = st.session_state.get("session_id", "unknown")
            session_info["user_id"] = st.session_state.get("user_id", "anonymous")

            # Extract IP if available
            try:
                if hasattr(st, "experimental_get_query_params"):
                    session_info["query_params"] = st.experimental_get_query_params()
            except Exception:
                pass

        return session_info

    def log_operation(
        self,
        operation: str,
        level: str = "INFO",
        message: str = "",
        duration_ms: Optional[float] = None,
        success: bool = True,
        error: Optional[Exception] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an operation with correlation context"""

        correlation_id = self.correlation_manager.ensure_correlation_id()
        session_info = self._get_session_info()

        # Monta extras para o formatter estruturar (sem serializar duas vezes)
        extras: Dict[str, Any] = {
            "correlation_id": correlation_id,
            "operation": operation,
            "success": success,
            "metadata": metadata or {},
            **session_info,
        }

        if duration_ms is not None:
            extras["duration_ms"] = round(duration_ms, 2)

        # Deixa exceção para exc_info (o formatter cuidará)
        log_level = getattr(logging, level.upper(), logging.INFO)
        if error is not None:
            self.logger.log(log_level, message or operation, extra=extras, exc_info=error)
        else:
            self.logger.log(log_level, message or operation, extra=extras)

    def info(self, operation: str, message: str, **kwargs: Any) -> None:
        """Log info level operation"""
        self.log_operation(operation, "INFO", message, **kwargs)

    def error(
        self, operation: str, message: str, error: Exception | None = None, **kwargs: Any
    ) -> None:
        """Log error level operation"""
        self.log_operation(operation, "ERROR", message, error=error, success=False, **kwargs)

    def warning(self, operation: str, message: str, **kwargs: Any) -> None:
        """Log warning level operation"""
        self.log_operation(operation, "WARNING", message, **kwargs)

    @contextmanager
    def track_operation(
        self, operation: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """Context manager to track operation duration and success"""
        start_time = time.time()
        correlation_id = self.correlation_manager.ensure_correlation_id()

        self.info(
            f"{operation}_start",
            f"Starting operation: {operation}",
            metadata=metadata or {},
        )

        try:
            yield correlation_id
            duration_ms = (time.time() - start_time) * 1000
            self.info(
                f"{operation}_complete",
                f"Operation completed successfully: {operation}",
                duration_ms=duration_ms,
                metadata=metadata,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.error(
                f"{operation}_failed",
                f"Operation failed: {operation}",
                error=e,
                duration_ms=duration_ms,
                metadata=metadata,
            )
            raise


def with_correlation_logging(operation: str, metadata_func=None):
    """Decorator to add correlation logging to functions"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = StructuredLogger(func.__module__)

            metadata: Dict[str, Any] = {}
            if metadata_func:
                try:
                    metadata = metadata_func(*args, **kwargs)
                except Exception:
                    pass

            with logger.track_operation(operation, metadata):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Global logger instance
correlation_logger = StructuredLogger(__name__)