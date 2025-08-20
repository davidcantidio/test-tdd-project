"""Simple middleware integrating rate limiting and DoS protection."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, Optional

from .core import RateLimiter
from streamlit_extension.utils.dos_protection import DoSProtectionSystem
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


@dataclass
class MiddlewareResponse:
    allowed: bool
    status_code: int = 200
    message: str = ""
    headers: Dict[str, str] = field(default_factory=dict)


class RateLimitingMiddleware:
    """Process requests enforcing DoS protection and rate limits."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.rate_limiter = RateLimiter(
            ttl_seconds=self.config.get("ttl_seconds", 900),
            storage=self.config.get("rate_limit_storage"),
        )
        self.dos = DoSProtectionSystem()

    def extract_request_info(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Extract minimal request information."""
        return {
            "ip": request.get("ip"),
            "user_id": request.get("user_id"),
            "tier": request.get("tier", "free"),
            "endpoint": request.get("endpoint", "/"),
        }

    def _build_headers(self, info: Dict[str, Any], reason_hint: Optional[str]) -> Dict[str, str]:
        try:
            return self.rate_limiter.build_rate_limit_headers(
                ip=info["ip"],
                user_id=info["user_id"],
                tier=info["tier"],
                endpoint=info["endpoint"],
                prefer=reason_hint,
            )
        except Exception:
            return {}

    def process_request(self, request: Dict[str, Any]) -> MiddlewareResponse:
        info = self.extract_request_info(request)
        if not self.dos.record_request(info["ip"]):
            self.logger.warning(
                "dos_block",
                extra={"ip": info["ip"], "endpoint": info["endpoint"], "user_id": info["user_id"], "tier": info["tier"]},
            )
            return MiddlewareResponse(False, 429, "DoS attack detected", headers={})
        result = self.rate_limiter.is_allowed(
            ip=info["ip"],
            user_id=info["user_id"],
            tier=info["tier"],
            endpoint=info["endpoint"],
        )
        if not result.allowed:
            self.logger.info(
                "rate_limit_block",
                extra={
                    "ip": info["ip"],
                    "endpoint": info["endpoint"],
                    "user_id": info["user_id"],
                    "tier": info["tier"],
                    "reason": result.reason,
                },
            )
            headers = self._build_headers(info, result.reason)
            return MiddlewareResponse(False, 429, f"Rate limit exceeded ({result.reason})", headers=headers)
        headers = self._build_headers(info, None)
        return MiddlewareResponse(True, headers=headers)

