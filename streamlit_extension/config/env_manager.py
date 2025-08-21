"""
🌍 Environment Configuration Manager

Manages dev/staging/prod configurations with:
- Environment variable substitution
- Configuration validation
- Hot reloading capabilities
- Environment detection
- Secrets management integration
"""

from __future__ import annotations

import importlib
import os
import re
from copy import deepcopy


class EnvironmentManager:
    """Manages environment-specific configurations."""

    def __init__(self, environment: str | None = None) -> None:
        """Initialize with auto-detection or explicit environment."""
        self.environment = environment or os.getenv("APP_ENV", "development")
        self.config_module = None
        self.database_config: dict = {}
        self.redis_config: dict = {}
        self.security_config: dict = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration for current environment."""
        module_name = f"config.environments.{self.environment}"
        self.config_module = importlib.import_module(module_name)
        self.database_config = deepcopy(getattr(self.config_module, "DATABASE_CONFIG", {}))
        self.redis_config = deepcopy(getattr(self.config_module, "REDIS_CONFIG", {}))
        self.security_config = deepcopy(getattr(self.config_module, "SECURITY_CONFIG", {}))

    def get_database_config(self) -> dict:
        """Get database configuration with env var substitution."""
        return self.substitute_env_vars(deepcopy(self.database_config))

    def get_redis_config(self) -> dict:
        """Get Redis configuration with env var substitution."""
        return self.substitute_env_vars(deepcopy(self.redis_config))

    def get_security_config(self) -> dict:
        """Get security configuration."""
        return deepcopy(self.security_config)

    def substitute_env_vars(self, config_dict: dict) -> dict:
        """Substitute ${VAR} patterns with environment variables."""
        pattern = re.compile(r"\$\{([^}]+)\}")

        def _resolve(value):
            if isinstance(value, str):
                return pattern.sub(lambda m: os.getenv(m.group(1), ""), value)
            if isinstance(value, dict):
                return {k: _resolve(v) for k, v in value.items()}
            if isinstance(value, list):
                return [_resolve(v) for v in value]
            return value

        return _resolve(config_dict)

    def validate_config(self) -> bool:
        """Validate configuration completeness and format."""
        required = {
            "database": ["framework_db_path", "timer_db_path"],
            "redis": ["host", "port"],
            "security": ["enable_csrf", "enable_rate_limiting"],
        }
        for name, keys in required.items():
            cfg = getattr(self, f"{name}_config", {})
            for key in keys:
                if key not in cfg:
                    raise ValueError(f"Missing {name} config key: {key}")
        return True

    def reload_config(self) -> None:
        """Hot reload configuration from files."""
        module_name = f"config.environments.{self.environment}"
        if self.config_module and self.config_module.__name__ == module_name:
            self.config_module = importlib.reload(self.config_module)
        else:
            self.config_module = importlib.import_module(module_name)
        self.database_config = deepcopy(getattr(self.config_module, "DATABASE_CONFIG", {}))
        self.redis_config = deepcopy(getattr(self.config_module, "REDIS_CONFIG", {}))
        self.security_config = deepcopy(getattr(self.config_module, "SECURITY_CONFIG", {}))