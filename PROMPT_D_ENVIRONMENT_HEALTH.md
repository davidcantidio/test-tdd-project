# 🏥 PROMPT D - ENVIRONMENT CONFIGURATION + HEALTH CHECKS

**TASK**: Implementar sistema de configuração por ambiente + health check endpoints  
**ARQUIVOS**: `config/`, `streamlit_extension/health.py` (ISOLADO - sem interseção com outros prompts)  
**PRIORITY**: P1 - IMPORTANT (production deployment requirements no report.md)  
**CONTEXT**: "Separate environment configs for dev/staging/prod" + "health-check endpoint for orchestration tools"

---

## 📋 **ARQUIVOS A CRIAR:**

### 1. `config/__init__.py`
```python
"""Configuration package for environment management."""

from .environment import EnvironmentConfig, get_config, ConfigType
from .database_config import DatabaseConfig
from .security_config import SecurityConfig
from .logging_config import LoggingConfigEnv
from .app_config import AppConfig

__all__ = [
    "EnvironmentConfig",
    "get_config",
    "ConfigType",
    "DatabaseConfig", 
    "SecurityConfig",
    "LoggingConfigEnv",
    "AppConfig"
]
```

### 2. `config/environment.py`
```python
"""Environment configuration management."""

from __future__ import annotations
import os
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, Union
from pathlib import Path
import yaml
import json


class ConfigType(Enum):
    """Configuration types/environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class EnvironmentConfig:
    """Environment configuration container."""
    env_type: ConfigType
    debug: bool
    database_url: str
    secret_key: str
    log_level: str
    log_file: Optional[str]
    
    # Security settings
    csrf_secret_key: str
    session_timeout_hours: int
    max_login_attempts: int
    
    # Performance settings
    cache_size: int
    connection_pool_size: int
    query_timeout_seconds: int
    
    # Feature flags
    features: Dict[str, bool]
    
    # External services
    external_services: Dict[str, Dict[str, Any]]
    
    # Health check settings
    health_check_enabled: bool
    health_check_path: str
    health_check_port: Optional[int]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], env_type: ConfigType) -> EnvironmentConfig:
        """Create config from dictionary."""
        return cls(
            env_type=env_type,
            debug=data.get("debug", False),
            database_url=data.get("database_url", "sqlite:///framework.db"),
            secret_key=data.get("secret_key", "dev-secret-key"),
            log_level=data.get("log_level", "INFO"),
            log_file=data.get("log_file"),
            
            # Security
            csrf_secret_key=data.get("csrf_secret_key", "csrf-secret-key"),
            session_timeout_hours=data.get("session_timeout_hours", 24),
            max_login_attempts=data.get("max_login_attempts", 5),
            
            # Performance
            cache_size=data.get("cache_size", 128),
            connection_pool_size=data.get("connection_pool_size", 10),
            query_timeout_seconds=data.get("query_timeout_seconds", 30),
            
            # Features
            features=data.get("features", {}),
            
            # External services
            external_services=data.get("external_services", {}),
            
            # Health checks
            health_check_enabled=data.get("health_check_enabled", True),
            health_check_path=data.get("health_check_path", "/health"),
            health_check_port=data.get("health_check_port")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "env_type": self.env_type.value,
            "debug": self.debug,
            "database_url": self.database_url,
            "secret_key": self.secret_key,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "csrf_secret_key": self.csrf_secret_key,
            "session_timeout_hours": self.session_timeout_hours,
            "max_login_attempts": self.max_login_attempts,
            "cache_size": self.cache_size,
            "connection_pool_size": self.connection_pool_size,
            "query_timeout_seconds": self.query_timeout_seconds,
            "features": self.features,
            "external_services": self.external_services,
            "health_check_enabled": self.health_check_enabled,
            "health_check_path": self.health_check_path,
            "health_check_port": self.health_check_port
        }
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env_type == ConfigType.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env_type == ConfigType.PRODUCTION
    
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.env_type == ConfigType.TESTING
    
    def get_feature_flag(self, feature_name: str, default: bool = False) -> bool:
        """Get feature flag value."""
        return self.features.get(feature_name, default)
    
    def get_external_service_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get external service configuration."""
        return self.external_services.get(service_name)


class ConfigManager:
    """Configuration manager for loading and managing environment configs."""
    
    def __init__(self, config_dir: Union[str, Path] = "config"):
        self.config_dir = Path(config_dir)
        self._configs: Dict[ConfigType, EnvironmentConfig] = {}
        self._current_config: Optional[EnvironmentConfig] = None
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all environment configurations."""
        environments_dir = self.config_dir / "environments"
        
        if not environments_dir.exists():
            environments_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_configs()
        
        for env_type in ConfigType:
            config_file = environments_dir / f"{env_type.value}.yaml"
            if config_file.exists():
                self._configs[env_type] = self._load_config_file(config_file, env_type)
    
    def _load_config_file(self, config_file: Path, env_type: ConfigType) -> EnvironmentConfig:
        """Load configuration from YAML file."""
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Substitute environment variables
        data = self._substitute_env_vars(data)
        
        return EnvironmentConfig.from_dict(data, env_type)
    
    def _substitute_env_vars(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute environment variables in configuration."""
        def substitute_value(value):
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                parts = env_var.split(":", 1)
                var_name = parts[0]
                default_value = parts[1] if len(parts) > 1 else ""
                return os.getenv(var_name, default_value)
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(item) for item in value]
            else:
                return value
        
        return substitute_value(data)
    
    def _create_default_configs(self):
        """Create default configuration files."""
        environments_dir = self.config_dir / "environments"
        
        # Development config
        dev_config = {
            "debug": True,
            "database_url": "sqlite:///framework_dev.db",
            "secret_key": "${SECRET_KEY:dev-secret-key}",
            "log_level": "DEBUG",
            "log_file": "logs/app_dev.log",
            "csrf_secret_key": "${CSRF_SECRET_KEY:dev-csrf-key}",
            "session_timeout_hours": 24,
            "max_login_attempts": 10,
            "cache_size": 64,
            "connection_pool_size": 5,
            "query_timeout_seconds": 30,
            "features": {
                "debug_toolbar": True,
                "detailed_errors": True,
                "performance_metrics": True
            },
            "external_services": {},
            "health_check_enabled": True,
            "health_check_path": "/health",
            "health_check_port": None
        }
        
        # Testing config
        test_config = {
            "debug": True,
            "database_url": "sqlite:///:memory:",
            "secret_key": "test-secret-key",
            "log_level": "WARNING",
            "log_file": None,
            "csrf_secret_key": "test-csrf-key",
            "session_timeout_hours": 1,
            "max_login_attempts": 3,
            "cache_size": 32,
            "connection_pool_size": 2,
            "query_timeout_seconds": 10,
            "features": {
                "debug_toolbar": False,
                "detailed_errors": True,
                "performance_metrics": False
            },
            "external_services": {},
            "health_check_enabled": False,
            "health_check_path": "/health",
            "health_check_port": None
        }
        
        # Staging config
        staging_config = {
            "debug": False,
            "database_url": "${DATABASE_URL:sqlite:///framework_staging.db}",
            "secret_key": "${SECRET_KEY}",
            "log_level": "INFO",
            "log_file": "logs/app_staging.log",
            "csrf_secret_key": "${CSRF_SECRET_KEY}",
            "session_timeout_hours": 12,
            "max_login_attempts": 5,
            "cache_size": 128,
            "connection_pool_size": 8,
            "query_timeout_seconds": 20,
            "features": {
                "debug_toolbar": False,
                "detailed_errors": False,
                "performance_metrics": True
            },
            "external_services": {},
            "health_check_enabled": True,
            "health_check_path": "/health",
            "health_check_port": 8080
        }
        
        # Production config
        prod_config = {
            "debug": False,
            "database_url": "${DATABASE_URL}",
            "secret_key": "${SECRET_KEY}",
            "log_level": "WARNING",
            "log_file": "logs/app_production.log",
            "csrf_secret_key": "${CSRF_SECRET_KEY}",
            "session_timeout_hours": 8,
            "max_login_attempts": 3,
            "cache_size": 256,
            "connection_pool_size": 15,
            "query_timeout_seconds": 15,
            "features": {
                "debug_toolbar": False,
                "detailed_errors": False,
                "performance_metrics": True
            },
            "external_services": {},
            "health_check_enabled": True,
            "health_check_path": "/health",
            "health_check_port": 8080
        }
        
        configs = {
            "development": dev_config,
            "testing": test_config,
            "staging": staging_config,
            "production": prod_config
        }
        
        for env_name, config in configs.items():
            config_file = environments_dir / f"{env_name}.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def get_config(self, env_type: Optional[ConfigType] = None) -> EnvironmentConfig:
        """Get configuration for specified environment."""
        if env_type is None:
            env_type = self.detect_environment()
        
        if env_type not in self._configs:
            raise ValueError(f"Configuration not found for environment: {env_type.value}")
        
        return self._configs[env_type]
    
    def detect_environment(self) -> ConfigType:
        """Detect current environment from environment variables."""
        env_name = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
        
        env_mapping = {
            "dev": ConfigType.DEVELOPMENT,
            "development": ConfigType.DEVELOPMENT,
            "test": ConfigType.TESTING,
            "testing": ConfigType.TESTING,
            "stage": ConfigType.STAGING,
            "staging": ConfigType.STAGING,
            "prod": ConfigType.PRODUCTION,
            "production": ConfigType.PRODUCTION
        }
        
        return env_mapping.get(env_name, ConfigType.DEVELOPMENT)
    
    def set_current_config(self, env_type: ConfigType):
        """Set current active configuration."""
        self._current_config = self.get_config(env_type)
    
    def get_current_config(self) -> EnvironmentConfig:
        """Get current active configuration."""
        if self._current_config is None:
            self._current_config = self.get_config()
        return self._current_config
    
    def validate_config(self, env_type: ConfigType) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        try:
            config = self.get_config(env_type)
            
            # Validate required fields
            if not config.secret_key or config.secret_key == "dev-secret-key":
                if config.is_production():
                    errors.append("SECRET_KEY must be set for production")
            
            if not config.csrf_secret_key or config.csrf_secret_key == "dev-csrf-key":
                if config.is_production():
                    errors.append("CSRF_SECRET_KEY must be set for production")
            
            # Validate database URL
            if not config.database_url:
                errors.append("Database URL is required")
            
            # Validate log settings
            if config.log_file and not Path(config.log_file).parent.exists():
                try:
                    Path(config.log_file).parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create log directory: {e}")
            
            # Validate performance settings
            if config.connection_pool_size <= 0:
                errors.append("Connection pool size must be positive")
            
            if config.query_timeout_seconds <= 0:
                errors.append("Query timeout must be positive")
        
        except Exception as e:
            errors.append(f"Configuration validation error: {e}")
        
        return errors


# Global config manager
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config(env_type: Optional[ConfigType] = None) -> EnvironmentConfig:
    """Get configuration for environment."""
    return get_config_manager().get_config(env_type)


def get_current_config() -> EnvironmentConfig:
    """Get current active configuration."""
    return get_config_manager().get_current_config()


def validate_environment() -> list[str]:
    """Validate current environment configuration."""
    manager = get_config_manager()
    env_type = manager.detect_environment()
    return manager.validate_config(env_type)
```

### 3. `config/schemas/config_schema.yaml`
```yaml
# Configuration schema for validation
type: object
required:
  - debug
  - database_url
  - secret_key
  - log_level

properties:
  debug:
    type: boolean
    description: Enable debug mode
  
  database_url:
    type: string
    description: Database connection URL
    pattern: "^(sqlite|postgresql|mysql)://"
  
  secret_key:
    type: string
    minLength: 16
    description: Application secret key
  
  log_level:
    type: string
    enum: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    description: Logging level
  
  log_file:
    type: string
    description: Log file path (optional)
  
  csrf_secret_key:
    type: string
    minLength: 16
    description: CSRF protection secret key
  
  session_timeout_hours:
    type: integer
    minimum: 1
    maximum: 168
    description: Session timeout in hours
  
  max_login_attempts:
    type: integer
    minimum: 1
    maximum: 20
    description: Maximum login attempts before lockout
  
  cache_size:
    type: integer
    minimum: 16
    maximum: 1024
    description: Cache size in MB
  
  connection_pool_size:
    type: integer
    minimum: 1
    maximum: 50
    description: Database connection pool size
  
  query_timeout_seconds:
    type: integer
    minimum: 5
    maximum: 300
    description: Database query timeout in seconds
  
  features:
    type: object
    description: Feature flags
    additionalProperties:
      type: boolean
  
  external_services:
    type: object
    description: External service configurations
    additionalProperties: true
  
  health_check_enabled:
    type: boolean
    description: Enable health check endpoint
  
  health_check_path:
    type: string
    pattern: "^/.*"
    description: Health check endpoint path
  
  health_check_port:
    type: integer
    minimum: 1024
    maximum: 65535
    description: Health check port (optional)
```

### 4. `streamlit_extension/health.py`
```python
"""Health check endpoints and monitoring."""

from __future__ import annotations
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import streamlit as st
import psutil
from pathlib import Path

from config import get_current_config


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check result."""
    name: str
    status: HealthStatus
    message: str
    response_time_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    last_checked: Optional[datetime] = None


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: HealthStatus
    timestamp: datetime
    checks: List[HealthCheck]
    summary: Dict[str, Any]
    uptime_seconds: float


class HealthMonitor:
    """Health monitoring system."""
    
    def __init__(self):
        self.config = get_current_config()
        self._start_time = time.time()
    
    def check_database_health(self) -> HealthCheck:
        """Check database connectivity and performance."""
        start_time = time.time()
        
        try:
            # Test connection
            with sqlite3.connect(self.config.database_url.replace("sqlite:///", ""), timeout=5) as conn:
                # Test basic query
                cursor = conn.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result[0] != 1:
                    return HealthCheck(
                        name="database",
                        status=HealthStatus.CRITICAL,
                        message="Database query returned unexpected result",
                        response_time_ms=(time.time() - start_time) * 1000
                    )
                
                # Test table existence
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='framework_epics'
                """)
                
                if not cursor.fetchone():
                    return HealthCheck(
                        name="database",
                        status=HealthStatus.WARNING,
                        message="Framework tables not found",
                        response_time_ms=(time.time() - start_time) * 1000
                    )
                
                # Test data integrity
                cursor = conn.execute("SELECT COUNT(*) FROM framework_epics")
                epic_count = cursor.fetchone()[0]
                
                response_time = (time.time() - start_time) * 1000
                
                return HealthCheck(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful",
                    response_time_ms=response_time,
                    details={
                        "epic_count": epic_count,
                        "database_path": self.config.database_url
                    }
                )
                
        except sqlite3.OperationalError as e:
            return HealthCheck(
                name="database",
                status=HealthStatus.CRITICAL,
                message=f"Database connection failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return HealthCheck(
                name="database",
                status=HealthStatus.CRITICAL,
                message=f"Database health check failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def check_memory_health(self) -> HealthCheck:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            available_gb = memory.available / (1024**3)
            
            if memory_percent > 90:
                status = HealthStatus.CRITICAL
                message = f"Critical memory usage: {memory_percent:.1f}%"
            elif memory_percent > 80:
                status = HealthStatus.WARNING
                message = f"High memory usage: {memory_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {memory_percent:.1f}%"
            
            return HealthCheck(
                name="memory",
                status=status,
                message=message,
                details={
                    "memory_percent": memory_percent,
                    "available_gb": round(available_gb, 2),
                    "total_gb": round(memory.total / (1024**3), 2)
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="memory",
                status=HealthStatus.UNKNOWN,
                message=f"Memory check failed: {str(e)}"
            )
    
    def check_disk_health(self) -> HealthCheck:
        """Check disk space."""
        try:
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            free_gb = disk.free / (1024**3)
            
            if disk_percent > 90:
                status = HealthStatus.CRITICAL
                message = f"Critical disk usage: {disk_percent:.1f}%"
            elif disk_percent > 80:
                status = HealthStatus.WARNING
                message = f"High disk usage: {disk_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {disk_percent:.1f}%"
            
            return HealthCheck(
                name="disk",
                status=status,
                message=message,
                details={
                    "disk_percent": round(disk_percent, 1),
                    "free_gb": round(free_gb, 2),
                    "total_gb": round(disk.total / (1024**3), 2)
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="disk",
                status=HealthStatus.UNKNOWN,
                message=f"Disk check failed: {str(e)}"
            )
    
    def check_log_health(self) -> HealthCheck:
        """Check logging system health."""
        try:
            if not self.config.log_file:
                return HealthCheck(
                    name="logging",
                    status=HealthStatus.HEALTHY,
                    message="Console logging only (no file logging configured)"
                )
            
            log_path = Path(self.config.log_file)
            
            if not log_path.exists():
                return HealthCheck(
                    name="logging",
                    status=HealthStatus.WARNING,
                    message="Log file does not exist yet"
                )
            
            # Check log file size
            log_size_mb = log_path.stat().st_size / (1024**2)
            
            # Check if log directory is writable
            log_dir = log_path.parent
            if not os.access(log_dir, os.W_OK):
                return HealthCheck(
                    name="logging",
                    status=HealthStatus.CRITICAL,
                    message="Log directory is not writable"
                )
            
            # Check recent log activity
            mod_time = datetime.fromtimestamp(log_path.stat().st_mtime)
            time_since_update = datetime.now() - mod_time
            
            if time_since_update > timedelta(hours=1):
                status = HealthStatus.WARNING
                message = f"Log file last updated {time_since_update} ago"
            else:
                status = HealthStatus.HEALTHY
                message = "Logging system operational"
            
            return HealthCheck(
                name="logging",
                status=status,
                message=message,
                details={
                    "log_file": str(log_path),
                    "log_size_mb": round(log_size_mb, 2),
                    "last_modified": mod_time.isoformat()
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="logging",
                status=HealthStatus.WARNING,
                message=f"Log check failed: {str(e)}"
            )
    
    def check_configuration_health(self) -> HealthCheck:
        """Check configuration validity."""
        try:
            from config import validate_environment
            
            errors = validate_environment()
            
            if errors:
                return HealthCheck(
                    name="configuration",
                    status=HealthStatus.CRITICAL,
                    message=f"Configuration errors: {'; '.join(errors)}",
                    details={"errors": errors}
                )
            
            return HealthCheck(
                name="configuration",
                status=HealthStatus.HEALTHY,
                message="Configuration is valid",
                details={
                    "environment": self.config.env_type.value,
                    "debug": self.config.debug
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="configuration",
                status=HealthStatus.CRITICAL,
                message=f"Configuration check failed: {str(e)}"
            )
    
    def perform_health_check(self) -> SystemHealth:
        """Perform comprehensive health check."""
        checks = [
            self.check_database_health(),
            self.check_memory_health(),
            self.check_disk_health(),
            self.check_log_health(),
            self.check_configuration_health()
        ]
        
        # Set check timestamps
        for check in checks:
            check.last_checked = datetime.now()
        
        # Determine overall status
        statuses = [check.status for check in checks]
        
        if HealthStatus.CRITICAL in statuses:
            overall_status = HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            overall_status = HealthStatus.WARNING
        elif HealthStatus.UNKNOWN in statuses:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Create summary
        summary = {
            "healthy_checks": len([c for c in checks if c.status == HealthStatus.HEALTHY]),
            "warning_checks": len([c for c in checks if c.status == HealthStatus.WARNING]),
            "critical_checks": len([c for c in checks if c.status == HealthStatus.CRITICAL]),
            "total_checks": len(checks),
            "environment": self.config.env_type.value
        }
        
        return SystemHealth(
            status=overall_status,
            timestamp=datetime.now(),
            checks=checks,
            summary=summary,
            uptime_seconds=time.time() - self._start_time
        )
    
    def get_health_json(self) -> Dict[str, Any]:
        """Get health status as JSON-serializable dictionary."""
        health = self.perform_health_check()
        
        return {
            "status": health.status.value,
            "timestamp": health.timestamp.isoformat(),
            "uptime_seconds": health.uptime_seconds,
            "summary": health.summary,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms,
                    "details": check.details,
                    "last_checked": check.last_checked.isoformat() if check.last_checked else None
                }
                for check in health.checks
            ]
        }


def render_health_page():
    """Render health status page in Streamlit."""
    st.title("🏥 System Health Monitor")
    
    monitor = HealthMonitor()
    health = monitor.perform_health_check()
    
    # Overall status
    status_colors = {
        HealthStatus.HEALTHY: "🟢",
        HealthStatus.WARNING: "🟡", 
        HealthStatus.CRITICAL: "🔴",
        HealthStatus.UNKNOWN: "⚪"
    }
    
    st.header(f"{status_colors[health.status]} Overall Status: {health.status.value.title()}")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Healthy Checks", health.summary["healthy_checks"])
    
    with col2:
        st.metric("Warning Checks", health.summary["warning_checks"])
    
    with col3:
        st.metric("Critical Checks", health.summary["critical_checks"])
    
    with col4:
        uptime_hours = health.uptime_seconds / 3600
        st.metric("Uptime (hours)", f"{uptime_hours:.1f}")
    
    # Individual checks
    st.header("📋 Individual Health Checks")
    
    for check in health.checks:
        with st.expander(f"{status_colors[check.status]} {check.name.title()} - {check.status.value.title()}"):
            st.write(f"**Message:** {check.message}")
            
            if check.response_time_ms:
                st.write(f"**Response Time:** {check.response_time_ms:.2f}ms")
            
            if check.last_checked:
                st.write(f"**Last Checked:** {check.last_checked.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if check.details:
                st.write("**Details:**")
                st.json(check.details)
    
    # Environment info
    st.header("🔧 Environment Information")
    
    env_info = {
        "Environment": health.summary["environment"],
        "Debug Mode": monitor.config.debug,
        "Database URL": monitor.config.database_url,
        "Log Level": monitor.config.log_level,
        "Session Timeout": f"{monitor.config.session_timeout_hours} hours",
        "Connection Pool Size": monitor.config.connection_pool_size
    }
    
    for key, value in env_info.items():
        st.write(f"**{key}:** {value}")
    
    # Refresh button
    if st.button("🔄 Refresh Health Status"):
        st.rerun()
    
    # Raw JSON export
    if st.checkbox("Show Raw JSON"):
        st.json(monitor.get_health_json())


# Global health monitor
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


def get_health_status() -> Dict[str, Any]:
    """Get current health status as dictionary."""
    monitor = get_health_monitor()
    return monitor.get_health_json()
```

### 5. `config/secrets/.env.example`
```bash
# Example environment variables file
# Copy to .env and fill in actual values

# Environment
ENVIRONMENT=development

# Security
SECRET_KEY=your-secret-key-here-minimum-32-characters
CSRF_SECRET_KEY=your-csrf-secret-key-here-minimum-32-chars

# Database
DATABASE_URL=sqlite:///framework.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Performance
CACHE_SIZE=128
CONNECTION_POOL_SIZE=10
QUERY_TIMEOUT_SECONDS=30

# Features
ENABLE_DEBUG_TOOLBAR=false
ENABLE_PERFORMANCE_METRICS=true

# Health Checks
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_PORT=8080
```

### 6. `.env.production.example`
```bash
# Production environment variables
ENVIRONMENT=production

# Security (REQUIRED IN PRODUCTION)
SECRET_KEY=
CSRF_SECRET_KEY=

# Database
DATABASE_URL=

# Logging
LOG_LEVEL=WARNING
LOG_FILE=logs/app_production.log

# Performance
CACHE_SIZE=256
CONNECTION_POOL_SIZE=15
QUERY_TIMEOUT_SECONDS=15

# Health Checks
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_PORT=8080

# Features
ENABLE_DEBUG_TOOLBAR=false
ENABLE_PERFORMANCE_METRICS=true
```

---

## 🔧 **INTEGRATION INSTRUCTIONS:**

### A. Update main `streamlit_app.py`:
```python
# Add to imports
from config import get_current_config, validate_environment
from streamlit_extension.health import get_health_status

# Setup configuration at startup
def main():
    # Load and validate configuration
    config = get_current_config()
    
    # Validate environment
    validation_errors = validate_environment()
    if validation_errors:
        st.error(f"Configuration errors: {'; '.join(validation_errors)}")
        st.stop()
    
    # Set up application with config
    setup_logging(level=LogLevel[config.log_level])
    
    # Rest of existing main() function...
```

### B. Add health check page to navigation:
```python
# In navigation system
pages = {
    "Health": "streamlit_extension.health.render_health_page",
    # ... existing pages
}
```

### C. Environment detection in deployment:
```bash
# Set environment variable before running
export ENVIRONMENT=production
export SECRET_KEY=your-production-secret
export DATABASE_URL=your-production-db

streamlit run streamlit_app.py
```

---

## ✅ **VERIFICATION CHECKLIST:**

- [ ] Configuration files created in `config/`
- [ ] Environment-specific YAML configs (dev/test/stage/prod)
- [ ] Environment variable substitution working
- [ ] Health check endpoint operational
- [ ] System monitoring (memory, disk, database)
- [ ] Configuration validation functional
- [ ] Secret key management secure
- [ ] Feature flags system active
- [ ] Logging configuration per environment
- [ ] Production deployment ready

---

## 🎯 **SUCCESS CRITERIA:**

1. **P1 Issue RESOLVED**: "Separate environment configs for dev/staging/prod"
2. **P1 Issue RESOLVED**: "health-check endpoint for orchestration tools"
3. **Environment Management**: Proper separation of configs with secret management
4. **Production Readiness**: Health monitoring for Kubernetes/Docker deployments
5. **Configuration Security**: No hardcoded secrets, proper environment variable usage

**RESULTADO ESPERADO**: Sistema de configuração enterprise-grade com separação de ambientes, health checks para orquestração, e gestão segura de secrets preparado para deployment em produção.