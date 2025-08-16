"""Scenario definitions for load testing examples."""

SCENARIOS = {
    "normal_day": {
        "users": 5,
        "ramp_up": 1,
        "duration": 1,
        "think_time": 0.01,
        "actions": ["login", "browse", "logout"],
    }
}