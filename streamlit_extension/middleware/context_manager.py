"""User context preservation utilities."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .correlation import CorrelationManager, RequestLifecycleTracker


@dataclass
class UserContext:
    """Dataclass representing user-related context information."""

    user_id: Optional[str]
    session_id: str
    request_id: str
    correlation_id: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    permissions: List[str]
    preferences: Dict[str, Any]
    performance_budget: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat(),
            "permissions": self.permissions,
            "preferences": self.preferences,
            "performance_budget": self.performance_budget,
        }

    def sanitize_for_logging(self) -> Dict[str, Any]:
        data = self.to_dict()
        data.pop("preferences", None)
        return data


class ContextManager:
    """Handle building and retrieving :class:`UserContext` objects."""

    def __init__(self, correlation_manager: Optional[CorrelationManager] = None) -> None:
        self.correlation_manager = correlation_manager or CorrelationManager()
        self.local = threading.local()

    def build_context(self, request_data: Dict[str, Any]) -> UserContext:
        correlation_id = self.correlation_manager.get_or_create()
        context = UserContext(
            user_id=request_data.get("user_id"),
            session_id=request_data.get("session_id", str(uuid.uuid4())),
            request_id=request_data.get("request_id", str(uuid.uuid4())),
            correlation_id=correlation_id,
            ip_address=request_data.get("ip_address", "0.0.0.0"),
            user_agent=request_data.get("user_agent", "unknown"),
            timestamp=datetime.now(),
            permissions=request_data.get("permissions", []),
            preferences=request_data.get("preferences", {}),
            performance_budget=request_data.get("performance_budget", {}),
        )
        self.local.context = context
        return context

    def get_context(self) -> Optional[UserContext]:
        return getattr(self.local, "context", None)

    def clear_context(self) -> None:
        if hasattr(self.local, "context"):
            del self.local.context
        # Also clear correlation ID for new requests
        self.correlation_manager.clear_correlation_id()


class ContextMiddleware:
    """Simple middleware to manage user context and correlation IDs."""

    def __init__(
        self,
        context_manager: Optional[ContextManager] = None,
        lifecycle_tracker: Optional[RequestLifecycleTracker] = None,
    ) -> None:
        self.context_manager = context_manager or ContextManager()
        self.lifecycle_tracker = lifecycle_tracker or RequestLifecycleTracker()

    def process_request(self, request: Dict[str, Any]) -> UserContext:
        context = self.context_manager.build_context(request)
        self.lifecycle_tracker.track_request_start(context.correlation_id, context.to_dict())
        return context

    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        context = self.context_manager.get_context()
        if context:
            headers = response.setdefault("headers", {})
            headers["X-Correlation-ID"] = context.correlation_id
            self.lifecycle_tracker.track_request_end(
                context.correlation_id, response.get("status", "ok")
            )
            self.context_manager.clear_context()
        return response