"""Test environment configuration system."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from streamlit_extension.config.env_manager import EnvironmentManager


class TestEnvironmentManager:
    def test_environment_detection(self):
        """Test automatic environment detection."""
        with patch.dict(os.environ, {}, clear=True):
            manager = EnvironmentManager()
            assert manager.environment == "development"
        with patch.dict(os.environ, {"APP_ENV": "staging"}, clear=True):
            manager = EnvironmentManager()
            assert manager.environment == "staging"
        with patch.dict(os.environ, {"APP_ENV": "staging"}, clear=True):
            manager = EnvironmentManager(environment="production")
            assert manager.environment == "production"

    def test_config_loading(self):
        """Test configuration loading for each environment."""
        expected = {
            "development": "dev_framework.db",
            "staging": "staging_framework.db",
            "production": "${DB_PATH}/framework.db",
        }
        for env, path in expected.items():
            manager = EnvironmentManager(environment=env)
            assert manager.database_config["framework_db_path"] == path

    def test_env_var_substitution(self):
        """Test environment variable substitution."""
        vars = {
            "DB_PATH": "/data",
            "REDIS_PASSWORD": "secret",
            "REDIS_HOST": "prod-redis",
            "REDIS_PORT": "6380",
        }
        with patch.dict(os.environ, vars, clear=True):
            manager = EnvironmentManager(environment="production")
            db_config = manager.get_database_config()
            assert db_config["framework_db_path"] == "/data/framework.db"
            redis_config = manager.get_redis_config()
            assert redis_config["password"] == "secret"
            assert redis_config["host"] == "prod-redis"
            assert redis_config["port"] == "6380"

    def test_config_validation(self):
        """Test configuration validation."""
        manager = EnvironmentManager(environment="development")
        assert manager.validate_config() is True
        manager.database_config.pop("framework_db_path")
        with pytest.raises(ValueError):
            manager.validate_config()

    def test_hot_reload(self):
        """Test configuration hot reloading."""
        manager = EnvironmentManager(environment="development")
        assert manager.get_database_config()["framework_db_path"] == "dev_framework.db"
        manager.environment = "staging"
        manager.reload_config()
        assert manager.get_database_config()["framework_db_path"] == "staging_framework.db"
