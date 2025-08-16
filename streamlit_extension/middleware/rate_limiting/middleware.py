"""Simple middleware integrating rate limiting and DoS protection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .core import RateLimiter
from streamlit_extension.utils.dos_protection import DoSProtectionSystem


@dataclass
class MiddlewareResponse:
    allowed: bool
    status_code: int = 200
    message: str = ""


class RateLimitingMiddleware:
    """Process requests enforcing DoS protection and rate limits."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.rate_limiter = RateLimiter()
        self.dos = DoSProtectionSystem()

    def extract_request_info(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Extract minimal request information."""
        return {
            "ip": request.get("ip"),
            "user_id": request.get("user_id"),
            "tier": request.get("tier", "free"),
            "endpoint": request.get("endpoint", "/"),
        }

    def process_request(self, request: Dict[str, Any]) -> MiddlewareResponse:
        info = self.extract_request_info(request)
        if not self.dos.record_request(info["ip"]):
            return MiddlewareResponse(False, 429, "DoS attack detected")
        result = self.rate_limiter.is_allowed(
            ip=info["ip"],
            user_id=info["user_id"],
            tier=info["tier"],
            endpoint=info["endpoint"],
        )
        if not result.allowed:
            return MiddlewareResponse(False, 429, f"Rate limit exceeded ({result.reason})")
        return MiddlewareResponse(True)