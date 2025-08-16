"""Core rate limiting engine supporting multiple strategies."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

from .algorithms import (
    FixedWindowRateLimiter,
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
)
from .policies import ENDPOINT_LIMITS, USER_TIER_LIMITS
from .storage import MemoryRateLimitStorage


@dataclass
class RateLimitResult:
    allowed: bool
    reason: Optional[str] = None


class RateLimiter:
    """High level rate limiter handling IP, user and endpoint limits."""

    def __init__(self) -> None:
        self.storage = MemoryRateLimitStorage()
        self.limiters: Dict[str, object] = {}

    # ------------------------------------------------------------------
    # Helper parsing utilities
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_rate(rate: str) -> tuple[int, int]:
        """Return (count, period_in_seconds) from a rate string."""
        count_part, _, rest = rate.partition(" per ")
        count = int(count_part.strip())
        amount_str, unit = rest.strip().split()
        amount = int(amount_str)
        unit = unit.lower()
        if unit.startswith("second"):
            period = amount
        elif unit.startswith("minute"):
            period = amount * 60
        elif unit.startswith("hour"):
            period = amount * 3600
        else:
            period = amount * 86400
        return count, period

    @staticmethod
    def _match_endpoint(endpoint: str) -> Optional[Dict[str, str]]:
        if endpoint in ENDPOINT_LIMITS:
            return ENDPOINT_LIMITS[endpoint]
        for pattern, config in ENDPOINT_LIMITS.items():
            if pattern.endswith("*") and endpoint.startswith(pattern[:-1]):
                return config
        return None

    # ------------------------------------------------------------------
    # Rate limit checks
    # ------------------------------------------------------------------
    def check_user_rate_limit(self, user_id: str, tier: str) -> bool:
        limits = USER_TIER_LIMITS.get(tier, USER_TIER_LIMITS["free"])
        rpm = limits.get("requests_per_minute", -1)
        if rpm < 0:
            return True
        key = f"user:{user_id}"
        limiter = self.limiters.get(key)
        if limiter is None:
            limiter = TokenBucketRateLimiter(capacity=rpm, refill_rate=rpm / 60)
            self.limiters[key] = limiter
        return limiter.is_allowed()

    def check_ip_rate_limit(self, ip: str) -> bool:
        key = f"ip:{ip}"
        limiter = self.limiters.get(key)
        if limiter is None:
            limiter = SlidingWindowRateLimiter(window_size=60, max_requests=100)
            self.limiters[key] = limiter
        return limiter.is_allowed()

    def check_endpoint_rate_limit(self, endpoint: str) -> bool:
        config = self._match_endpoint(endpoint)
        if not config:
            return True
        count, period = self._parse_rate(config["rate_limit"])
        alg = config.get("algorithm", "sliding_window")
        key = f"endpoint:{endpoint}"
        limiter = self.limiters.get(key)
        if limiter is None:
            if alg == "token_bucket":
                refill_rate = count / period
                burst = config.get("burst_capacity", count)
                limiter = TokenBucketRateLimiter(capacity=burst, refill_rate=refill_rate, refill_period=1)
            elif alg == "fixed_window":
                limiter = FixedWindowRateLimiter(window_size=period, max_requests=count)
            else:
                limiter = SlidingWindowRateLimiter(window_size=period, max_requests=count)
            self.limiters[key] = limiter
        return limiter.is_allowed()

    # ------------------------------------------------------------------
    def is_allowed(
        self,
        ip: Optional[str] = None,
        user_id: Optional[str] = None,
        tier: str = "free",
        endpoint: str = "/",
    ) -> RateLimitResult:
        """Return a RateLimitResult for the given request details."""
        if ip and not self.check_ip_rate_limit(ip):
            return RateLimitResult(False, "ip")
        if user_id and not self.check_user_rate_limit(user_id, tier):
            return RateLimitResult(False, "user")
        if endpoint and not self.check_endpoint_rate_limit(endpoint):
            return RateLimitResult(False, "endpoint")
        return RateLimitResult(True)