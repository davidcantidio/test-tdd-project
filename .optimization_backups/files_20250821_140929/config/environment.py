#!/usr/bin/env python3
"""
🌍 Environment Configuration Manager

Addresses report.md requirement: "Separate environment configs for dev/staging/prod"
and "Store secrets in vault or environment variables (no hard-coded paths)"

This module provides:
- Environment-specific configuration loading
- Secure secret management via environment variables
- Configuration validation and type checking
- Support for dev/staging/prod environments
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import tomllib

logger = logging.getLogger(__name__)


@dataclass
class GoogleOAuthConfig:
    """Google OAuth 2.0 configuration."""
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = "http://localhost:8501"
    scopes: List[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ])


@dataclass
class DatabaseConfig:
    """Database configuration."""
    framework_db_path: str = "framework.db"
    timer_db_path: str = "task_timer.db"
    connection_timeout: int = 20
    pool_size: int = 5
    max_overflow: int = 10
    
    # Performance settings
    enable_wal_mode: bool = True
    cache_size: int = -2000  # 2MB cache
    temp_store: str = "memory"


@dataclass
class SecurityConfig:
    """Security configuration."""
    require_auth: bool = True
    csrf_token_expiry: int = 3600  # 1 hour
    session_timeout_minutes: int = 480  # 8 hours
    cookie_name: str = "tdd_framework_session"
    
    # Rate limiting
    enable_rate_limiting: bool = True
    enable_dos_protection: bool = True
    
    # Logging
    enable_log_sanitization: bool = True
    log_level: str = "INFO"


@dataclass
class PerformanceConfig:
    """Performance and caching configuration."""
    enable_database_cache: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    enable_redis: bool = False
    redis_url: Optional[str] = None
    
    # Pagination defaults
    default_page_size: int = 50
    max_page_size: int = 1000
    
    # Streamlit optimization
    enable_streamlit_cache: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    enable_health_check: bool = True
    health_check_port: int = 8080
    enable_metrics: bool = False
    metrics_port: int = 9090
    
    # Logging
    log_format: str = "json"
    enable_correlation_ids: bool = True
    log_file_path: Optional[str] = None


@dataclass
class AppConfig:
    """Main application configuration."""
    # Environment info
    environment: str = "development"
    debug: bool = True
    app_name: str = "TDD Framework"
    version: str = "1.0.0"
    
    # Server settings
    host: str = "localhost"
    port: int = 8501
    
    # Sub-configurations
    google_oauth: GoogleOAuthConfig = field(default_factory=GoogleOAuthConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)


class EnvironmentConfigLoader:
    """Loads environment-specific configuration with security best practices."""
    
    REQUIRED_ENV_VARS = {
        "production": [
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET", 
        ],
        "staging": [],  # More permissive for staging
        "development": []  # More permissive for dev
    }
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent
        self.environment = os.getenv("TDD_ENVIRONMENT", "development").lower()
        logger.info(f"Loading configuration for environment: {self.environment}")
    
    def load_config(self) -> AppConfig:
        """Load complete configuration for current environment."""
        
        # Load base configuration
        config = self._load_base_config()
        
        # Override with environment-specific settings
        config = self._apply_environment_overrides(config)
        
        # Load secrets from environment variables (secure)
        config = self._load_secrets_from_env(config)
        
        # Validate configuration
        self._validate_config(config)
        
        logger.info(f"Configuration loaded successfully for {self.environment}")
        return config
    
    def _load_base_config(self) -> AppConfig:
        """Load base configuration from file."""
        config_file = self.config_dir / f"{self.environment}.toml"
        
        if config_file.exists():
            logger.info(f"Loading config from: {config_file}")
            with open(config_file, "rb") as f:
                config_data = tomllib.load(f)
            return self._dict_to_config(config_data)
        else:
            logger.warning(f"Config file not found: {config_file}, using defaults")
            return AppConfig(environment=self.environment)
    
    def _apply_environment_overrides(self, config: AppConfig) -> AppConfig:
        """Apply environment-specific overrides."""
        config.environment = self.environment
        
        if self.environment == "production":
            config.debug = False
            config.security.require_auth = True
            config.security.log_level = "WARNING"
            config.monitoring.enable_health_check = True
            config.monitoring.enable_metrics = True
            config.performance.enable_redis = True
            
        elif self.environment == "staging":
            config.debug = False
            config.security.require_auth = True
            config.security.log_level = "INFO"
            config.monitoring.enable_health_check = True
            config.performance.enable_redis = False
            
        elif self.environment == "development":
            config.debug = True
            config.security.require_auth = False  # Optional for dev
            config.security.log_level = "DEBUG"
            config.monitoring.enable_health_check = False
            config.performance.enable_redis = False
        
        return config
    
    def _load_secrets_from_env(self, config: AppConfig) -> AppConfig:
        """Load sensitive data from environment variables (SECURE)."""
        
        # Google OAuth (from environment variables)
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        
        if google_client_id and google_client_secret:
            config.google_oauth.client_id = google_client_id
            config.google_oauth.client_secret = google_client_secret
            logger.info("Loaded Google OAuth credentials from environment")
        else:
            logger.warning("Google OAuth credentials not found in environment variables")
        
        # Database paths from environment
        if db_path := os.getenv("FRAMEWORK_DB_PATH"):
            config.database.framework_db_path = db_path
        
        if timer_db_path := os.getenv("TIMER_DB_PATH"):
            config.database.timer_db_path = timer_db_path
        
        # Redis configuration
        if redis_url := os.getenv("REDIS_URL"):
            config.performance.redis_url = redis_url
            config.performance.enable_redis = True
        
        # Security settings
        if session_timeout := os.getenv("SESSION_TIMEOUT_MINUTES"):
            config.security.session_timeout_minutes = int(session_timeout)
        
        # Server settings
        if port := os.getenv("PORT"):
            config.port = int(port)
        
        if host := os.getenv("HOST"):
            config.host = host
        
        # Monitoring
        if log_level := os.getenv("LOG_LEVEL"):
            config.security.log_level = log_level.upper()
        
        return config
    
    def _validate_config(self, config: AppConfig) -> None:
        """Validate configuration for current environment."""
        required_vars = self.REQUIRED_ENV_VARS.get(self.environment, [])
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables for {self.environment}: "
                f"{', '.join(missing_vars)}"
            )
        
        # Validate OAuth config for auth-required environments (except development)
        if config.security.require_auth and self.environment != "development":
            if not config.google_oauth.client_id or not config.google_oauth.client_secret:
                logger.warning(
                    "Google OAuth credentials missing - authentication may not work properly"
                )
        
        # Validate database paths
        if config.environment not in ["test", "development"] and config.environment.startswith("test"):
            db_path = Path(config.database.framework_db_path)
            if not db_path.exists() and config.environment == "production":
                logger.warning(f"Database file not found: {db_path}")
        
        logger.info("Configuration validation passed")
    
    def _dict_to_config(self, config_data: Dict[str, Any]) -> AppConfig:
        """Convert dictionary to AppConfig object."""
        # This is a simplified implementation
        # In a real scenario, you might use a library like pydantic
        config = AppConfig()
        
        # Map basic app settings
        if "app" in config_data:
            app_data = config_data["app"]
            config.app_name = app_data.get("name", config.app_name)
            config.debug = app_data.get("debug", config.debug)
            config.environment = app_data.get("environment", config.environment)
        
        # Map database settings
        if "database" in config_data:
            db_data = config_data["database"]
            config.database.framework_db_path = db_data.get("framework_db_path", config.database.framework_db_path)
            config.database.timer_db_path = db_data.get("timer_db_path", config.database.timer_db_path)
            config.database.connection_timeout = db_data.get("connection_timeout", config.database.connection_timeout)
        
        # Map security settings
        if "security" in config_data:
            sec_data = config_data["security"]
            config.security.require_auth = sec_data.get("require_auth", config.security.require_auth)
            config.security.session_timeout_minutes = sec_data.get("session_timeout_minutes", config.security.session_timeout_minutes)
        
        return config


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        loader = EnvironmentConfigLoader()
        _config = loader.load_config()
    return _config


def reload_config() -> AppConfig:
    """Reload configuration (useful for testing)."""
    global _config
    _config = None
    return get_config()


# Convenience functions for common config access
def is_production() -> bool:
    """Check if running in production environment."""
    return get_config().environment == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return get_config().environment == "development"


def is_staging() -> bool:
    """Check if running in staging environment."""
    return get_config().environment == "staging"


def get_database_config() -> DatabaseConfig:
    """Get database configuration."""
    return get_config().database


def get_security_config() -> SecurityConfig:
    """Get security configuration."""
    return get_config().security


def get_google_oauth_config() -> GoogleOAuthConfig:
    """Get Google OAuth configuration."""
    return get_config().google_oauth


if __name__ == "__main__":
    # Test configuration loading
    print("🌍 Testing Environment Configuration")
    print("=" * 50)
    
    try:
        config = get_config()
        print(f"Environment: {config.environment}")
        print(f"Debug mode: {config.debug}")
        print(f"App name: {config.app_name}")
        print(f"Auth required: {config.security.require_auth}")
        print(f"Database path: {config.database.framework_db_path}")
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration error: {e}")