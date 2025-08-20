"""Collection of rate limiting algorithm implementations."""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Any
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


class TokenBucketRateLimiter:
    """Simple token bucket implementation."""

    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        refill_period: float = 1.0,
        storage: Any | None = None,
        key: str | None = None,
    ) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_period = refill_period
        self._storage = storage
        self._key = key
        self.tokens = float(capacity)
        self.last_refill = time.time()
        if self._storage and self._key:
            self._storage.update_bucket_state(self._key, tokens=self.tokens, last_refill=self.last_refill)

    def _refill_tokens(self) -> None:
        now = time.time()
        if self._storage and self._key:
            state = self._storage.get_bucket_state(self._key)
            last_refill = state.get("last_refill", now)
            tokens = float(state.get("tokens", self.capacity))
            elapsed = now - last_refill
            tokens_to_add = (elapsed / self.refill_period) * self.refill_rate
            if tokens_to_add > 0:
                tokens = min(self.capacity, tokens + tokens_to_add)
                self._storage.update_bucket_state(self._key, tokens=tokens, last_refill=now)
        else:
            elapsed = now - self.last_refill
            tokens_to_add = (elapsed / self.refill_period) * self.refill_rate
            if tokens_to_add > 0:
                self.tokens = min(self.capacity, self.tokens + tokens_to_add)
                self.last_refill = now

    def is_allowed(self, tokens_requested: int = 1) -> bool:
        """Return True if the requested number of tokens is available."""
        self._refill_tokens()
        if self._storage and self._key:
            state = self._storage.get_bucket_state(self._key)
            tokens = float(state.get("tokens", self.capacity))
            if tokens >= tokens_requested:
                tokens -= tokens_requested
                self._storage.update_bucket_state(
                    self._key, tokens=tokens, last_refill=state.get("last_refill", time.time())
                )
                return True
            return False
        else:
            if self.tokens >= tokens_requested:
                self.tokens -= tokens_requested
                return True
            return False


class SlidingWindowRateLimiter:
    """Sliding window implementation tracking individual request timestamps."""

    def __init__(
        self,
        window_size: int,
        max_requests: int,
        storage: Any | None = None,
        key: str | None = None,
    ) -> None:
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests: Deque[float] = deque()
        self._storage = storage
        self._key = key

    def is_allowed(self, timestamp: float | None = None) -> bool:
        if timestamp is None:
            timestamp = time.time()
        cutoff = timestamp - self.window_size
        if self._storage and self._key:
            self._storage.prune(self._key, cutoff)
            count = self._storage.increment(self._key, timestamp)
            return count <= self.max_requests
        while self.requests and self.requests[0] <= cutoff:
            self.requests.popleft()
        if len(self.requests) < self.max_requests:
            self.requests.append(timestamp)
            return True
        return False


class FixedWindowRateLimiter:
    """Fixed window counter implementation."""

    def __init__(
        self,
        window_size: int,
        max_requests: int,
        storage: Any | None = None,
        key: str | None = None,
    ) -> None:
        self.window_size = window_size
        self.max_requests = max_requests
        self.window_start = int(time.time()) // self.window_size
        self.counter = 0
        self._storage = storage
        self._key = key

    def is_allowed(self, timestamp: float | None = None) -> bool:
        if timestamp is None:
            timestamp = time.time()
        current_window = int(timestamp) // self.window_size
        if self._storage and self._key:
            state = self._storage.get_counter_state(self._key)
            window_start = state.get("window_start")
            counter = int(state.get("counter", 0))
            if window_start is None or window_start != current_window:
                window_start = current_window
                counter = 0
            if counter < self.max_requests:
                counter += 1
                self._storage.update_counter_state(
                    self._key, window_start=window_start, counter=counter
                )
                return True
            self._storage.update_counter_state(
                self._key, window_start=window_start, counter=counter
            )
            return False
        if current_window != self.window_start:
            self.window_start = current_window
            self.counter = 0
        if self.counter < self.max_requests:
            self.counter += 1
            return True
        return False

