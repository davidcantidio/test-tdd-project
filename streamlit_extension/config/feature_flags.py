from __future__ import annotations

"""Simple feature flag management."""

import os
from enum import Enum
from typing import Any, Dict


class FeatureFlag(str, Enum):
    NEW_CLIENT_FORM = "NEW_CLIENT_FORM"
    ADVANCED_ANALYTICS = "ADVANCED_ANALYTICS"
    BETA_FEATURES = "BETA_FEATURES"
    MAINTENANCE_MODE = "MAINTENANCE_MODE"


class FeatureFlagManager:
    """Manage feature flags with environment overrides."""

    def __init__(self) -> None:
        self.flags: Dict[FeatureFlag, bool] = {flag: False for flag in FeatureFlag}
        self.refresh_flags()

    def is_enabled(self, flag: FeatureFlag) -> bool:
        return bool(self.flags.get(flag, False))

    def get_flag_value(self, flag: FeatureFlag) -> Any:
        return self.flags.get(flag)

    def refresh_flags(self) -> Dict[FeatureFlag, bool]:
        for flag in FeatureFlag:
            env_var = f"FF_{flag.value}"
            if env_var in os.environ:
                value = os.environ[env_var]
                self.flags[flag] = value.lower() in {"1", "true", "yes", "on"}
        return self.flags

    def override_flag(self, flag: FeatureFlag, value: bool) -> None:
        self.flags[flag] = value

