"""Correlation ID management and request lifecycle tracking."""

from __future__ import annotations

import threading
import time
import uuid
from typing import Dict, List, Optional, Tuple


class CorrelationManager:
    """Manage correlation IDs using thread-local storage."""

    def __init__(self) -> None:
        self.correlation_context = threading.local()

    def generate_correlation_id(self) -> str:
        """Generate unique correlation ID."""
        return f"{uuid.uuid4().hex[:8]}-{int(time.time())}"

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for current thread."""
        self.correlation_context.id = correlation_id

    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID."""
        return getattr(self.correlation_context, "id", None)

    def get_or_create(self) -> str:
        """Return existing correlation ID or create a new one."""
        cid = self.get_correlation_id()
        if cid is None:
            cid = self.generate_correlation_id()
            self.set_correlation_id(cid)
        return cid

    def clear_correlation_id(self) -> None:
        """Clear correlation ID from current thread."""
        if hasattr(self.correlation_context, "id"):
            del self.correlation_context.id


class RequestLifecycleTracker:
    """Track request lifecycle events for debugging and analytics."""

    def __init__(self) -> None:
        self.events: List[Tuple[str, str, Dict]] = []

    def track_request_start(self, correlation_id: str, context: Dict) -> None:
        """Record the start of a request."""
        self.events.append(("start", correlation_id, context))

    def track_request_end(self, correlation_id: str, status: str) -> None:
        """Record the end of a request."""
        self.events.append(("end", correlation_id, {"status": status}))