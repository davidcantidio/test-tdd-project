"""Convenience wrapper exposing a singleton rate limiter."""

from __future__ import annotations

from streamlit_extension.middleware.rate_limiting.core import RateLimiter
from streamlit_extension.utils.dos_protection import DoSProtectionSystem

_rate_limiter = RateLimiter()
_dos = DoSProtectionSystem()


def is_request_allowed(ip: str | None, user_id: str | None, tier: str, endpoint: str) -> bool:
    """Check whether a request should be processed."""
    if _dos.detect_attack(ip):
        return False
    return _rate_limiter.is_allowed(ip=ip, user_id=user_id, tier=tier, endpoint=endpoint).allowed