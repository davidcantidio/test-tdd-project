"""Very small DoS protection helper used by the middleware tests."""

from __future__ import annotations

import time
from typing import Dict
from collections import deque
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


class SimpleSlidingWindow:
    """Simple sliding window rate limiter for DoS protection."""
    
    def __init__(self, window_size: int, max_requests: int) -> None:
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = deque()
    
    def is_allowed(self, timestamp: float | None = None) -> bool:
        if timestamp is None:
            timestamp = time.time()
        cutoff = timestamp - self.window_size
        while self.requests and self.requests[0] <= cutoff:
            self.requests.popleft()
        if len(self.requests) < self.max_requests:
            self.requests.append(timestamp)
            return True
        return False


class DoSProtectionSystem:
    """Detects suspicious request rates from individual IPs."""

    def __init__(self, threshold: int = 100, window: int = 60) -> None:
        self.threshold = threshold
        self.window = window
        self.limiters: Dict[str, SimpleSlidingWindow] = {}

    def record_request(self, ip: str | None, timestamp: float | None = None) -> bool:
        """Record a request and return True if under threshold."""
        if ip is None:
            return True
        limiter = self.limiters.get(ip)
        if limiter is None:
            limiter = SimpleSlidingWindow(self.window, self.threshold)
            self.limiters[ip] = limiter
        return limiter.is_allowed(timestamp)

    def detect_attack(self, ip: str | None) -> bool:
        """Return True if the request rate for the IP is suspicious."""
        return not self.record_request(ip)