"""Core rate limiting engine supporting multiple strategies."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, cast

from .algorithms import (
    FixedWindowRateLimiter,
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
)
from .policies import ENDPOINT_LIMITS, USER_TIER_LIMITS
from .storage import MemoryRateLimitStorage
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


@dataclass
class RateLimitResult:
    allowed: bool
    reason: Optional[str] = None


class RateLimiter:
    # Delegation to RateLimiterValidation
    def __init__(self):
        self._ratelimitervalidation = RateLimiterValidation()
    # Delegation to RateLimiterNetworking
    def __init__(self):
        self._ratelimiternetworking = RateLimiterNetworking()
    # Delegation to RateLimiterUiinteraction
    def __init__(self):
        self._ratelimiteruiinteraction = RateLimiterUiinteraction()
    # Delegation to RateLimiterFormatting
    def __init__(self):
        self._ratelimiterformatting = RateLimiterFormatting()
    # Delegation to RateLimiterConfiguration
    def __init__(self):
        self._ratelimiterconfiguration = RateLimiterConfiguration()
    # Delegation to RateLimiterCalculation
    def __init__(self):
        self._ratelimitercalculation = RateLimiterCalculation()
    # Delegation to RateLimiterErrorhandling
    def __init__(self):
        self._ratelimitererrorhandling = RateLimiterErrorhandling()
    """High level rate limiter handling IP, user and endpoint limits."""

    def __init__(self, ttl_seconds: int = 900, storage: object | None = None) -> None:
        self.storage = storage or MemoryRateLimitStorage()
        # key -> (last_seen_ts, limiter_instance)
        self.limiters: Dict[str, Tuple[float, object]] = {}
        self.ttl_seconds = ttl_seconds

    def _get(self, key: str) -> Optional[object]:
        item = self.limiters.get(key)
        if not item:
            return None
        last_seen, limiter = item
        now = time.time()
        if now - last_seen > self.ttl_seconds:
            self.limiters.pop(key, None)
            return None
        self.limiters[key] = (now, limiter)
        return limiter

    def _set(self, key: str, limiter: object) -> object:
        self.limiters[key] = (time.time(), limiter)
        return limiter

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
        limiter = self._get(key)
        if limiter is None:
            limiter = TokenBucketRateLimiter(
                capacity=rpm,
                refill_rate=rpm / 60,
                storage=self.storage,
                key=key,
            )
            self._set(key, limiter)
        return cast(TokenBucketRateLimiter, limiter).is_allowed()

    def check_ip_rate_limit(self, ip: str) -> bool:
        key = f"ip:{ip}"
        limiter = self._get(key)
        if limiter is None:
            limiter = SlidingWindowRateLimiter(
                window_size=60,
                max_requests=100,
                storage=self.storage,
                key=key,
            )
            self._set(key, limiter)
        return cast(SlidingWindowRateLimiter, limiter).is_allowed()

    def check_endpoint_rate_limit(self, endpoint: str) -> bool:
        config = self._match_endpoint(endpoint)
        if not config:
            return True
        count, period = self._parse_rate(config["rate_limit"])
        alg = config.get("algorithm", "sliding_window")
        key = f"endpoint:{endpoint}"
        limiter = self._get(key)
        if limiter is None:
            if alg == "token_bucket":
                refill_rate = count / period
                burst = config.get("burst_capacity", count)
                limiter = TokenBucketRateLimiter(
                    capacity=burst,
                    refill_rate=refill_rate,
                    refill_period=1,
                    storage=self.storage,
                    key=key,
                )
            elif alg == "fixed_window":
                limiter = FixedWindowRateLimiter(
                    window_size=period,
                    max_requests=count,
                    storage=self.storage,
                    key=key,
                )
            else:
                limiter = SlidingWindowRateLimiter(
                    window_size=period,
                    max_requests=count,
                    storage=self.storage,
                    key=key,
                )
            self._set(key, limiter)
        if alg == "token_bucket":
            return cast(TokenBucketRateLimiter, limiter).is_allowed()
        elif alg == "fixed_window":
            return cast(FixedWindowRateLimiter, limiter).is_allowed()
        else:
            return cast(SlidingWindowRateLimiter, limiter).is_allowed()

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

    # ------------------------------------------------------------------
    # Headers snapshot util
    # ------------------------------------------------------------------
    def _snapshot_token_bucket(self, key: str, capacity: int, refill_rate: float, refill_period: float) -> tuple[int, int, int]:
        state = self.storage.get_bucket_state(key)
        tokens = float(state.get("tokens", capacity))
        remaining = int(tokens) if tokens >= 0 else 0
        if tokens >= 1:
            reset = 0
        else:
            need = max(0.0, 1.0 - tokens)
            seconds = int((need / refill_rate) * refill_period) if refill_rate > 0 else 0
            reset = max(0, seconds)
        return capacity, remaining, reset

    def _snapshot_sliding_window(self, key: str, window_size: int, max_requests: int) -> tuple[int, int, int]:
        now = time.time()
        cutoff = now - window_size
        try:
            count = self.storage.get_window_count(key, cutoff)
        except AttributeError:
            self.storage.prune(key, cutoff)
            count = 0
        remaining = max(0, max_requests - int(count))
        reset = int(window_size - (now - cutoff))
        return max_requests, remaining, max(0, reset)

    def _snapshot_fixed_window(self, key: str, window_size: int, max_requests: int) -> tuple[int, int, int]:
        now = time.time()
        current_window = int(now) // window_size
        st = self.storage.get_counter_state(key)
        window_start = st.get("window_start")
        counter = int(st.get("counter", 0))
        if window_start is None or window_start != current_window:
            remaining = max_requests
            reset = window_size - (int(now) % window_size)
        else:
            remaining = max(0, max_requests - counter)
            reset = window_size - (int(now) % window_size)
        return max_requests, remaining, max(0, int(reset))

    def _pick_strictest(self, choices: Dict[str, tuple[int, int, int]], prefer: Optional[str]) -> tuple[str, tuple[int, int, int]]:
        if prefer and prefer in choices:
            return prefer, choices[prefer]
        best_key = None
        best_val = None
        for k, v in choices.items():
            if best_val is None:
                best_key, best_val = k, v
                continue
            if v[1] < best_val[1] or (v[1] == best_val[1] and v[2] < best_val[2]):
                best_key, best_val = k, v
        return (best_key or "endpoint"), (best_val or (0, 0, 0))

    def build_rate_limit_headers(
        self,
        *,
        ip: Optional[str],
        user_id: Optional[str],
        tier: str,
        endpoint: str,
        prefer: Optional[str] = None,
    ) -> Dict[str, str]:
        choices: Dict[str, tuple[int, int, int]] = {}

        cfg = self._match_endpoint(endpoint)
        if cfg:
            count, period = self._parse_rate(cfg["rate_limit"])
            alg = cfg.get("algorithm", "sliding_window")
            key = f"endpoint:{endpoint}"
            if alg == "token_bucket":
                refill_rate = count / period
                burst = cfg.get("burst_capacity", count)
                choices["endpoint"] = self._snapshot_token_bucket(key, burst, refill_rate, 1.0)
            elif alg == "fixed_window":
                choices["endpoint"] = self._snapshot_fixed_window(key, period, count)
            else:
                choices["endpoint"] = self._snapshot_sliding_window(key, period, count)

        if user_id:
            limits = USER_TIER_LIMITS.get(tier, USER_TIER_LIMITS["free"])
            rpm = limits.get("requests_per_minute", -1)
            if rpm >= 0:
                key = f"user:{user_id}"
                choices["user"] = self._snapshot_token_bucket(key, rpm, rpm / 60.0, 1.0)

        if ip:
            key = f"ip:{ip}"
            choices["ip"] = self._snapshot_sliding_window(key, 60, 100)

        if not choices:
            return {}
        _k, (limit, remaining, reset) = self._pick_strictest(choices, prefer)
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset),
        }