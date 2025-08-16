"""Collection of rate limiting algorithm implementations."""

from __future__ import annotations

import time
from collections import deque
from typing import Deque


class TokenBucketRateLimiter:
    """Simple token bucket implementation."""

    def __init__(self, capacity: int, refill_rate: float, refill_period: float = 1.0) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_period = refill_period
        self.tokens = float(capacity)
        self.last_refill = time.time()

    def _refill_tokens(self) -> None:
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = (elapsed / self.refill_period) * self.refill_rate
        if tokens_to_add > 0:
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now

    def is_allowed(self, tokens_requested: int = 1) -> bool:
        """Return True if the requested number of tokens is available."""
        self._refill_tokens()
        if self.tokens >= tokens_requested:
            self.tokens -= tokens_requested
            return True
        return False


class SlidingWindowRateLimiter:
    """Sliding window implementation tracking individual request timestamps."""

    def __init__(self, window_size: int, max_requests: int) -> None:
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests: Deque[float] = deque()

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


class FixedWindowRateLimiter:
    """Fixed window counter implementation."""

    def __init__(self, window_size: int, max_requests: int) -> None:
        self.window_size = window_size
        self.max_requests = max_requests
        self.window_start = int(time.time())
        self.counter = 0

    def is_allowed(self, timestamp: float | None = None) -> bool:
        if timestamp is None:
            timestamp = time.time()
        current_window = int(timestamp) // self.window_size
        if current_window != self.window_start:
            self.window_start = current_window
            self.counter = 0
        if self.counter < self.max_requests:
            self.counter += 1
            return True
        return False