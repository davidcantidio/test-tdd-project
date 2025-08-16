"""Tests for environment configuration, secrets and feature flags."""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch

import pytest

from streamlit_extension.config.environment import EnvironmentManager, Environment
from streamlit_extension.config.secrets_manager import (
    SecretsManager,
    SecretType,
    VaultIntegration,
)
from streamlit_extension.config.feature_flags import FeatureFlagManager, FeatureFlag


# ---------------------------------------------------------------------------
# Environment configuration tests
# ---------------------------------------------------------------------------

def test_load_development_config():
    manager = EnvironmentManager(Environment.DEVELOPMENT)
    config = manager.load_environment_config()
    assert config["debug"] is True
    assert config["database"]["url"] == "sqlite:///framework_dev.db"


def test_load_production_config():
    with patch.dict(os.environ, {"DATABASE_URL": "postgres://prod/db"}):
        manager = EnvironmentManager(Environment.PRODUCTION)
        config = manager.load_environment_config()
        assert config["database"]["url"] == "postgres://prod/db"
        assert config["security"]["csrf_protection"] is True


def test_environment_detection():
    with patch.dict(os.environ, {"APP_ENV": "testing"}, clear=True):
        manager = EnvironmentManager()
        assert manager.environment == Environment.TESTING


def test_config_validation():
    manager = EnvironmentManager(Environment.DEVELOPMENT)
    config = manager.load_environment_config()
    assert manager.validate_config(config) is True
    del config["database"]["url"]
    with pytest.raises(ValueError):
        manager.validate_config(config)


def test_merge_configs():
    manager = EnvironmentManager(Environment.DEVELOPMENT)
    base = {"a": 1, "b": {"c": 2}}
    override = {"b": {"d": 3}, "e": 4}
    merged = manager.merge_configs(base, override)
    assert merged == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}


# ---------------------------------------------------------------------------
# Secrets management tests
# ---------------------------------------------------------------------------

def test_load_secrets_from_env():
    env = {secret.value: f"value_{i}" for i, secret in enumerate(SecretType)}
    with patch.dict(os.environ, env, clear=True):
        manager = SecretsManager()
        loaded = manager.load_from_env_vars()
        assert len(loaded) == len(SecretType)


def test_secrets_validation():
    manager = SecretsManager()
    manager._secrets = {SecretType.DATABASE_URL: "url"}
    with pytest.raises(ValueError):
        manager.validate_secrets()
    manager.load_from_vault()
    assert manager.validate_secrets() is True


def test_secrets_caching():
    vault = VaultIntegration()
    manager = SecretsManager(vault)
    manager.load_from_vault()
    assert vault.get_cached(SecretType.DATABASE_URL) == "vault-db-url"


def test_secrets_rotation():
    manager = SecretsManager()
    manager.load_from_vault()
    rotated = manager.rotate_secrets()
    for secret in SecretType:
        assert manager.get_secret(secret) == rotated[secret]


def test_get_secret():
    manager = SecretsManager()
    with patch.dict(os.environ, {SecretType.API_KEYS.value: "key"}):
        manager.load_from_env_vars()
    assert manager.get_secret(SecretType.API_KEYS) == "key"


# ---------------------------------------------------------------------------
# Feature flag tests
# ---------------------------------------------------------------------------

def test_feature_flag_enabled():
    with patch.dict(os.environ, {"FF_NEW_CLIENT_FORM": "1"}):
        manager = FeatureFlagManager()
        assert manager.is_enabled(FeatureFlag.NEW_CLIENT_FORM)


def test_feature_flag_disabled():
    manager = FeatureFlagManager()
    assert manager.is_enabled(FeatureFlag.BETA_FEATURES) is False


def test_feature_flag_override():
    manager = FeatureFlagManager()
    manager.override_flag(FeatureFlag.BETA_FEATURES, True)
    assert manager.is_enabled(FeatureFlag.BETA_FEATURES)


def test_feature_flag_refresh():
    manager = FeatureFlagManager()
    with patch.dict(os.environ, {"FF_ADVANCED_ANALYTICS": "true"}):
        manager.refresh_flags()
    assert manager.is_enabled(FeatureFlag.ADVANCED_ANALYTICS)


def test_feature_flag_get_value():
    manager = FeatureFlagManager()
    assert manager.get_flag_value(FeatureFlag.MAINTENANCE_MODE) is False

