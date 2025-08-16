"""Rate limiting policy definitions."""

USER_TIER_LIMITS = {
    "free": {
        "requests_per_minute": 60,
    },
    "premium": {
        "requests_per_minute": 300,
    },
    "enterprise": {
        "requests_per_minute": 1000,
    },
    "admin": {
        "requests_per_minute": -1,
    },
}

ENDPOINT_LIMITS = {
    "/api/auth/login": {"rate_limit": "5 per 5 minutes", "algorithm": "sliding_window"},
    "/api/client/create": {"rate_limit": "10 per minute", "algorithm": "token_bucket", "burst_capacity": 3},
    "/api/search": {"rate_limit": "100 per minute", "algorithm": "sliding_window"},
    "/api/bulk/*": {"rate_limit": "1 per 10 seconds", "algorithm": "fixed_window"},
}