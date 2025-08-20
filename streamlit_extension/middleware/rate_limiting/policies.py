"""Rate limiting policy definitions."""

from typing import TypedDict, Literal
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


UNLIMITED = -1


class TierLimits(TypedDict, total=False):
    requests_per_minute: int


Algorithm = Literal["token_bucket", "fixed_window", "sliding_window"]


class EndpointPolicy(TypedDict, total=False):
    rate_limit: str
    algorithm: Algorithm
    burst_capacity: int


USER_TIER_LIMITS: dict[str, TierLimits] = {
    "free": {"requests_per_minute": 60},
    "premium": {"requests_per_minute": 300},
    "enterprise": {"requests_per_minute": 1000},
    "admin": {"requests_per_minute": UNLIMITED},
}


ENDPOINT_LIMITS: dict[str, EndpointPolicy] = {
    "/api/auth/login": {"rate_limit": "5 per 5 minutes", "algorithm": "sliding_window"},
    "/api/client/create": {"rate_limit": "10 per minute", "algorithm": "token_bucket", "burst_capacity": 3},
    "/api/search": {"rate_limit": "100 per minute", "algorithm": "sliding_window"},
    "/api/bulk/*": {"rate_limit": "1 per 10 seconds", "algorithm": "fixed_window"},
}

