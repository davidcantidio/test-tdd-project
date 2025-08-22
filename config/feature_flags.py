#!/usr/bin/env python3
"""
Feature Flags System
Control feature rollout and A/B testing.
"""

import os
import yaml
import logging
import hashlib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps

import streamlit as st

logger = logging.getLogger(__name__)


class FeatureFlagType(Enum):
    """Types of feature flags."""

    BOOLEAN = "boolean"  # Simple on/off
    PERCENTAGE = "percentage"  # Rollout percentage
    USER_LIST = "user_list"  # Specific users
    ROLE_BASED = "role_based"  # Based on user roles
    TIME_BASED = "time_based"  # Time-window activation
    VARIANT = "variant"  # A/B testing variants
    CONDITIONAL = "conditional"  # Complex conditions


@dataclass
class FeatureFlag:
    """Feature flag definition."""

    name: str
    description: str
    flag_type: FeatureFlagType
    enabled: bool = False
    percentage: float = 0.0
    allowed_users: List[str] = field(default_factory=list)
    allowed_roles: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    variants: Dict[str, Any] = field(default_factory=dict)
    conditions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_enabled_for_user(
        self,
        user_id: str,
        user_role: str | None = None,
        user_attributes: Dict | None = None,
    ) -> bool:
        """Check if feature is enabled for specific user."""
        if not self.enabled:
            return False

        if self.flag_type == FeatureFlagType.BOOLEAN:
            return True

        if self.flag_type == FeatureFlagType.PERCENTAGE:
            # SECURITY FIX: Use SHA-256 instead of MD5
            hash_value = int(
                hashlib.sha256(f"{self.name}:{user_id}".encode()).hexdigest(), 16
            )
            return (hash_value % 100) < (self.percentage * 100)

        if self.flag_type == FeatureFlagType.USER_LIST:
            return user_id in self.allowed_users

        if self.flag_type == FeatureFlagType.ROLE_BASED:
            return user_role in self.allowed_roles if user_role else False

        if self.flag_type == FeatureFlagType.TIME_BASED:
            now = datetime.now()
            if self.start_time and now < self.start_time:
                return False
            if self.end_time and now > self.end_time:
                return False
            return True

        if self.flag_type == FeatureFlagType.CONDITIONAL:
            return self._evaluate_conditions(user_id, user_role, user_attributes)

        return False

    def get_variant(self, user_id: str) -> Optional[str]:
        """Get A/B test variant for user."""
        if self.flag_type != FeatureFlagType.VARIANT:
            return None

        if not self.variants:
            return None

        # SECURITY FIX: Use SHA-256 instead of MD5
        hash_value = int(
            hashlib.sha256(f"{self.name}:variant:{user_id}".encode()).hexdigest(), 16
        )
        bucket = hash_value % 100

        cumulative = 0
        for variant_name, variant_config in self.variants.items():
            weight = variant_config.get("weight", 0)
            cumulative += weight
            if bucket < cumulative:
                return variant_name

        return None

    def _evaluate_conditions(
        self, user_id: str, user_role: str, user_attributes: Dict
    ) -> bool:
        """Evaluate complex conditions."""
        if not user_attributes:
            return False

        for key, expected_value in self.conditions.items():
            actual_value = user_attributes.get(key)

            if actual_value is None:
                return False

            if isinstance(expected_value, dict):
                operator = expected_value.get("operator", "==")
                value = expected_value.get("value")

                if operator == ">":
                    if not (actual_value > value):
                        return False
                elif operator == ">=":
                    if not (actual_value >= value):
                        return False
                elif operator == "<":
                    if not (actual_value < value):
                        return False
                elif operator == "<=":
                    if not (actual_value <= value):
                        return False
                elif operator == "in":
                    if actual_value not in value:
                        return False
                elif operator == "not_in":
                    if actual_value in value:
                        return False
                else:
                    if actual_value != value:
                        return False
            else:
                if actual_value != expected_value:
                    return False

        return True


class FeatureFlagManager:
    """Manage feature flags across the application."""

    def __init__(self, config_path: str = "config/feature_flags.yaml", environment: str | None = None):
        self.config_path = config_path
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.flags: Dict[str, FeatureFlag] = {}
        self.analytics: List[Dict] = []
        self.load_configuration()

    def load_configuration(self) -> None:
        """Load feature flags from configuration file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                # SECURITY FIX: Use safe_load to prevent YAML injection
                config = yaml.safe_load(f)

            # Validate YAML structure
            if not isinstance(config, dict):
                raise ValueError("Invalid YAML structure: root must be a dictionary")

            env_flags = config.get(self.environment, {})
            default_flags = config.get("default", {})
            
            # Validate environment sections
            if not isinstance(env_flags, dict):
                logger.warning(f"Invalid environment section: {self.environment}")
                env_flags = {}
            if not isinstance(default_flags, dict):
                logger.warning("Invalid default section")
                default_flags = {}
                
            all_flags = {**default_flags, **env_flags}

            for flag_name, flag_config in all_flags.items():
                if not isinstance(flag_config, dict):
                    logger.warning(f"Invalid flag config for {flag_name}")
                    continue
                    
                self.flags[flag_name] = FeatureFlag(
                    name=flag_name,
                    description=flag_config.get("description", ""),
                    flag_type=FeatureFlagType(flag_config.get("type", "boolean")),
                    enabled=flag_config.get("enabled", False),
                    percentage=flag_config.get("percentage", 0.0),
                    allowed_users=flag_config.get("allowed_users", []),
                    allowed_roles=flag_config.get("allowed_roles", []),
                    start_time=self._parse_datetime(flag_config.get("start_time")),
                    end_time=self._parse_datetime(flag_config.get("end_time")),
                    variants=flag_config.get("variants", {}),
                    conditions=flag_config.get("conditions", {}),
                    metadata=flag_config.get("metadata", {}),
                )

            logger.info(
                "Loaded %d feature flags for %s", len(self.flags), self.environment
            )
        except FileNotFoundError:
            logger.warning("Feature flags config not found: %s", self.config_path)
            self._load_defaults()
        except yaml.YAMLError as e:
            logger.error("YAML parsing error in feature flags: %s", e)
            self._load_defaults()
        except Exception as exc:
            logger.error("Error loading feature flags: %s", exc)
            self._load_defaults()

    def _parse_datetime(self, dt_string: Optional[str]) -> Optional[datetime]:
        if not dt_string:
            return None
        try:
            return datetime.fromisoformat(dt_string)
        except Exception:
            return None

    def _load_defaults(self) -> None:
        self.flags = {
            "new_analytics_dashboard": FeatureFlag(
                name="new_analytics_dashboard",
                description="New analytics dashboard with advanced metrics",
                flag_type=FeatureFlagType.PERCENTAGE,
                enabled=True,
                percentage=0.1,
            ),
            "enhanced_security": FeatureFlag(
                name="enhanced_security",
                description="Enhanced security features",
                flag_type=FeatureFlagType.BOOLEAN,
                enabled=True,
            ),
            "beta_features": FeatureFlag(
                name="beta_features",
                description="Beta features for testing",
                flag_type=FeatureFlagType.ROLE_BASED,
                enabled=True,
                allowed_roles=["admin", "beta_tester"],
            ),
        }

    def is_enabled(
        self,
        flag_name: str,
        user_id: str | None = None,
        user_role: str | None = None,
        user_attributes: Dict | None = None,
    ) -> bool:
        if flag_name not in self.flags:
            logger.warning("Unknown feature flag: %s", flag_name)
            return False

        flag = self.flags[flag_name]
        self._track_flag_check(flag_name, user_id)

        if not user_id:
            return flag.enabled and flag.flag_type == FeatureFlagType.BOOLEAN

        return flag.is_enabled_for_user(user_id, user_role, user_attributes)

    def get_variant(self, flag_name: str, user_id: str) -> Optional[str]:
        if flag_name not in self.flags:
            return None

        flag = self.flags[flag_name]
        variant = flag.get_variant(user_id)
        self._track_variant_assignment(flag_name, user_id, variant)
        return variant

    def _track_flag_check(self, flag_name: str, user_id: Optional[str]) -> None:
        self.analytics.append(
            {
                "timestamp": datetime.now(),
                "flag_name": flag_name,
                "user_id": user_id,
                "event": "flag_checked",
            }
        )

    def _track_variant_assignment(
        self, flag_name: str, user_id: str, variant: Optional[str]
    ) -> None:
        self.analytics.append(
            {
                "timestamp": datetime.now(),
                "flag_name": flag_name,
                "user_id": user_id,
                "variant": variant,
                "event": "variant_assigned",
            }
        )

    def get_all_flags(
        self,
        user_id: str | None = None,
        user_role: str | None = None,
        user_attributes: Dict | None = None,
    ) -> Dict[str, bool]:
        result: Dict[str, bool] = {}
        for flag_name in self.flags:
            result[flag_name] = self.is_enabled(
                flag_name, user_id, user_role, user_attributes
            )
        return result

    def get_analytics(self, flag_name: Optional[str] = None) -> List[Dict]:
        if flag_name:
            return [a for a in self.analytics if a["flag_name"] == flag_name]
        return self.analytics


def feature_flag(flag_name: str, default: bool = False) -> Callable:
    """Decorator to control feature availability."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = st.session_state.get("user_id")
            user_role = st.session_state.get("user_role")
            user_attributes = st.session_state.get("user_attributes", {})

            if feature_flags.is_enabled(flag_name, user_id, user_role, user_attributes):
                return func(*args, **kwargs)
            if default:
                logger.info(
                    "Feature %s disabled, using default behavior", flag_name
                )
                return None
            st.warning("This feature is currently not available.")
            return None

        return wrapper

    return decorator


def variant_test(flag_name: str) -> Callable:
    """Decorator for A/B testing."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = st.session_state.get("user_id")
            variant = feature_flags.get_variant(flag_name, user_id)
            return func(*args, variant=variant, **kwargs)

        return wrapper

    return decorator


def render_feature_flags_admin() -> None:
    """Admin interface for managing feature flags."""

    st.title("🎛️ Feature Flags Management")

    if st.session_state.get("user_role") != "admin":
        st.error("Admin access required")
        return

    st.subheader("Current Feature Flags")

    for flag_name, flag in feature_flags.flags.items():
        with st.expander(f"{flag_name} - {flag.description}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Type:** {flag.flag_type.value}")
                st.write(f"**Enabled:** {flag.enabled}")

            with col2:
                if flag.flag_type == FeatureFlagType.PERCENTAGE:
                    new_percentage = st.slider(
                        "Rollout Percentage",
                        0.0,
                        1.0,
                        flag.percentage,
                        key=f"percentage_{flag_name}",
                    )
                    if new_percentage != flag.percentage:
                        flag.percentage = new_percentage
                        st.success("Updated")

            with col3:
                if st.button(f"Toggle {flag_name}", key=f"toggle_{flag_name}"):
                    flag.enabled = not flag.enabled
                    st.rerun()

    st.subheader("📊 Feature Flag Analytics")
    analytics_data = feature_flags.get_analytics()

    if analytics_data:
        import pandas as pd

        df = pd.DataFrame(analytics_data)
        st.dataframe(df)


feature_flags: FeatureFlagManager


def init_feature_flags() -> FeatureFlagManager:
    """Initialize feature flags manager."""
    global feature_flags
    feature_flags = FeatureFlagManager()
    return feature_flags