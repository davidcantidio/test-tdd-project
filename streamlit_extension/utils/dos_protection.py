"""Very small DoS protection helper used by the middleware tests."""

from __future__ import annotations

import time
from typing import Dict

from streamlit_extension.middleware.rate_limiting.algorithms import SlidingWindowRateLimiter


class DoSProtectionSystem:
    """Detects suspicious request rates from individual IPs."""

    def __init__(self, threshold: int = 100, window: int = 60) -> None:
        self.threshold = threshold
        self.window = window
        self.limiters: Dict[str, SlidingWindowRateLimiter] = {}

    def record_request(self, ip: str | None, timestamp: float | None = None) -> bool:
        """Record a request and return True if under threshold."""
        if ip is None:
            return True
        limiter = self.limiters.get(ip)
        if limiter is None:
            limiter = SlidingWindowRateLimiter(self.window, self.threshold)
            self.limiters[ip] = limiter
        return limiter.is_allowed(timestamp)

    def detect_attack(self, ip: str | None) -> bool:
        """Return True if the request rate for the IP is suspicious."""
        return not self.record_request(ip)