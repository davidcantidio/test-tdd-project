"""Storage backends for rate limiting state."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict


class MemoryRateLimitStorage:
    """In-memory storage suitable for tests and single process usage."""

    def __init__(self) -> None:
        self.data: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()

    def get_bucket_state(self, key: str) -> Dict[str, Any]:
        with self.lock:
            return self.data.get(key, {"tokens": 0.0, "last_refill": time.time()})

    def update_bucket_state(self, key: str, tokens: float, last_refill: float) -> None:
        with self.lock:
            self.data[key] = {"tokens": tokens, "last_refill": last_refill}

    def increment(self, key: str, timestamp: float) -> int:
        """Increment sliding window counter and return current count."""
        with self.lock:
            window = self.data.setdefault(key, {"timestamps": []})["timestamps"]
            window.append(timestamp)
            return len(window)

    def prune(self, key: str, cutoff: float) -> None:
        with self.lock:
            window = self.data.setdefault(key, {"timestamps": []})["timestamps"]
            while window and window[0] <= cutoff:
                window.pop(0)