"""Comprehensive tests for the lightweight rate limiting system."""

from __future__ import annotations

import time

from streamlit_extension.middleware.rate_limiting.algorithms import (
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
)
from streamlit_extension.middleware.rate_limiting.core import RateLimiter


# ---------------------------------------------------------------------------
# Algorithm tests
# ---------------------------------------------------------------------------

def test_token_bucket_algorithm():
    limiter = TokenBucketRateLimiter(capacity=2, refill_rate=1, refill_period=1)
    assert limiter.is_allowed()
    assert limiter.is_allowed()
    assert not limiter.is_allowed()
    time.sleep(1.1)
    assert limiter.is_allowed()


def test_sliding_window_algorithm():
    limiter = SlidingWindowRateLimiter(window_size=3, max_requests=2)
    assert limiter.is_allowed(timestamp=1000)
    assert limiter.is_allowed(timestamp=1001)
    assert not limiter.is_allowed(timestamp=1002)
    assert limiter.is_allowed(timestamp=1004)


# ---------------------------------------------------------------------------
# Policy enforcement
# ---------------------------------------------------------------------------

def test_user_tier_enforcement():
    rl = RateLimiter()
    for _ in range(60):
        assert rl.is_allowed(user_id="u1", tier="free").allowed
    assert not rl.is_allowed(user_id="u1", tier="free").allowed


def test_endpoint_specific_limits():
    rl = RateLimiter()
    endpoint = "/api/auth/login"
    for _ in range(5):
        assert rl.is_allowed(endpoint=endpoint).allowed
    assert not rl.is_allowed(endpoint=endpoint).allowed


# ---------------------------------------------------------------------------
# Burst and progressive penalties
# ---------------------------------------------------------------------------

class ProgressiveRateLimiter:
    """Simple progressive penalty helper."""

    def __init__(self) -> None:
        self.violations = {}
        self.delays = [1, 5, 15]

    def record_violation(self, ident: str) -> None:
        self.violations[ident] = self.violations.get(ident, 0) + 1

    def get_delay(self, ident: str) -> int:
        count = self.violations.get(ident, 0)
        if count == 0:
            return 0
        idx = min(count - 1, len(self.delays) - 1)
        return self.delays[idx]


def test_progressive_penalties():
    prl = ProgressiveRateLimiter()
    prl.record_violation("a")
    assert prl.get_delay("a") == 1
    prl.record_violation("a")
    assert prl.get_delay("a") == 5
    prl.record_violation("a")
    assert prl.get_delay("a") == 15