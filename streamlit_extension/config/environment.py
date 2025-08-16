from __future__ import annotations

"""Environment configuration system with validation and merging."""

import os
import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict

import yaml
from jsonschema import validate, ValidationError


class Environment(str, Enum):
    """Supported deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class ConfigLoader:
    """Loads and validates YAML configuration files."""

    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path("config/environments")

    def load_yaml_config(self, environment: Environment) -> Dict[str, Any]:
        """Load YAML configuration for the given environment."""
        file_path = self.base_path / f"{environment.value}.yaml"
        with file_path.open("r", encoding="utf-8") as fh:
            data: Dict[str, Any] = yaml.safe_load(fh) or {}
        return self.apply_environment_overrides(data)

    def validate_schema(self, config: Dict[str, Any], schema_path: Path | None = None) -> bool:
        """Validate configuration against JSON schema."""
        schema_path = schema_path or Path("config/schemas/config_schema.json")
        with schema_path.open("r", encoding="utf-8") as fh:
            schema = json.load(fh)
        validate(instance=config, schema=schema)
        return True

    def apply_environment_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides in ${VAR} format."""

        def resolve(value: Any) -> Any:
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var = value[2:-1]
                return os.getenv(var, "")
            if isinstance(value, dict):
                return {k: resolve(v) for k, v in value.items()}
            if isinstance(value, list):
                return [resolve(v) for v in value]
            return value

        return resolve(config)


class EnvironmentManager:
    """High level manager for environment configurations."""

    def __init__(self, environment: Environment | None = None) -> None:
        self.environment = environment or self.get_current_environment()
        self.loader = ConfigLoader()

    def get_current_environment(self) -> Environment:
        """Detect current environment from APP_ENV variable."""
        env = os.getenv("APP_ENV", Environment.DEVELOPMENT.value).lower()
        try:
            return Environment(env)
        except ValueError:
            return Environment.DEVELOPMENT

    def load_environment_config(self) -> Dict[str, Any]:
        """Load and validate configuration for current environment."""
        config = self.loader.load_yaml_config(self.environment)
        self.validate_config(config)
        return config

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure."""
        try:
            return self.loader.validate_schema(config)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc

    def merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two configuration dictionaries."""
        merged = dict(base)
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self.merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged

