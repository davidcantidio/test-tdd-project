"""
🔧 Streamlit Configuration Management

Manages all configuration settings for the Streamlit extension with:
- Environment variable loading
- Type-safe configuration
- Validation and defaults
- Runtime configuration updates
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import json

# Graceful imports
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    load_dotenv = None

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    pytz = None

from datetime import datetime
import logging


@dataclass
class StreamlitConfig:
    """Type-safe configuration for Streamlit extension."""
    
    # GitHub Integration
    github_token: Optional[str] = None
    github_repo_owner: Optional[str] = None  
    github_repo_name: Optional[str] = None
    github_api_calls_per_hour: int = 4000
    rate_limit_buffer: int = 500
    
    # Streamlit Settings
    streamlit_theme: str = "dark"
    streamlit_port: int = 8501
    streamlit_host: str = "localhost"
    streamlit_auto_rerun: bool = True
    streamlit_max_upload_size: int = 200
    
    # Database Configuration
    database_url: str = "sqlite:///./framework.db"
    timer_database_url: str = "sqlite:///./task_timer.db"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    
    # TDAH Configuration
    focus_session_duration: int = 25
    short_break_duration: int = 5
    long_break_duration: int = 15
    sessions_until_long_break: int = 4
    timezone: str = "America/Fortaleza"
    enable_focus_tracking: bool = True
    enable_sound_alerts: bool = False
    enable_notifications: bool = True
    
    # Gamification
    enable_gamification: bool = True
    points_per_completed_task: int = 10
    points_per_tdd_cycle: int = 5
    streak_bonus_multiplier: float = 1.5
    
    # Analytics
    analytics_retention_days: int = 90
    enable_performance_metrics: bool = True
    cache_ttl_seconds: int = 900
    
    # Security
    session_timeout: int = 480
    
    # Development
    debug_mode: bool = False
    enable_profiler: bool = False
    log_level: str = "INFO"
    testing_mode: bool = False
    test_database_url: str = "sqlite:///./test_framework.db"
    
    # Runtime settings (not from env)
    config_loaded_at: Optional[str] = field(default=None)
    missing_dependencies: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate_config()
    
    def validate_config(self):
        """Validate configuration values."""
        # Validate port range
        if not (1024 <= self.streamlit_port <= 65535):
            logging.info(f"⚠️ Warning: streamlit_port {self.streamlit_port} outside recommended range (1024-65535)")
        
        # Validate session durations
        if self.focus_session_duration < 5 or self.focus_session_duration > 120:
            logging.info(f"⚠️ Warning: focus_session_duration {self.focus_session_duration} outside recommended range (5-120 minutes)")
        
        # Validate timezone
        if PYTZ_AVAILABLE and self.timezone:
            try:
                pytz.timezone(self.timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                logging.info(f"⚠️ Warning: Unknown timezone '{self.timezone}', falling back to UTC")
                self.timezone = "UTC"
        
        # Check GitHub configuration completeness
        github_fields = [self.github_token, self.github_repo_owner, self.github_repo_name]
        if any(github_fields) and not all(github_fields):
            logging.info("⚠️ Warning: Incomplete GitHub configuration. Set all: GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME")
    
    def is_github_configured(self) -> bool:
        """Check if GitHub integration is properly configured."""
        return all([self.github_token, self.github_repo_owner, self.github_repo_name])
    
    def get_database_path(self) -> Path:
        """Get the main database file path, resolved relative to project root."""
        if self.database_url.startswith("sqlite:///"):
            db_path = Path(self.database_url.replace("sqlite:///", ""))
        else:
            db_path = Path("framework.db")  # fallback
        
        # If path is relative, resolve it relative to project root
        if not db_path.is_absolute():
            # Get project root by going up from streamlit_extension directory
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / db_path
        
        return db_path.resolve()
    
    def get_timer_database_path(self) -> Path:
        """Get the timer database file path, resolved relative to project root."""
        if self.timer_database_url.startswith("sqlite:///"):
            db_path = Path(self.timer_database_url.replace("sqlite:///", ""))
        else:
            db_path = Path("task_timer.db")  # fallback
        
        # If path is relative, resolve it relative to project root
        if not db_path.is_absolute():
            # Get project root by going up from streamlit_extension directory
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / db_path
        
        return db_path.resolve()
    
    def get_streamlit_config_dict(self) -> Dict[str, Any]:
        """Get Streamlit-specific configuration as dictionary."""
        return {
            "server": {
                "port": self.streamlit_port,
                "address": self.streamlit_host,
                "maxUploadSize": self.streamlit_max_upload_size,
                "enableCORS": False,
                "enableXsrfProtection": True
            },
            "theme": {
                "base": self.streamlit_theme,
                "primaryColor": "#FF6B6B" if self.streamlit_theme == "dark" else "#FF4B4B",
                "backgroundColor": "#0E1117" if self.streamlit_theme == "dark" else "#FFFFFF",
                "secondaryBackgroundColor": "#262730" if self.streamlit_theme == "dark" else "#F0F2F6",
                "textColor": "#FFFFFF" if self.streamlit_theme == "dark" else "#262730"
            },
            "runner": {
                "magicEnabled": True,
                "fastReruns": self.streamlit_auto_rerun
            }
        }
    
    def get_timezone_object(self):
        """Get pytz timezone object."""
        if PYTZ_AVAILABLE:
            try:
                return pytz.timezone(self.timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                logging.info(f"⚠️ Unknown timezone '{self.timezone}', using UTC")
                return pytz.UTC
        return None
    
    def format_datetime(self, dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime with user's timezone."""
        if not isinstance(dt, datetime):
            return str(dt)
        
        if PYTZ_AVAILABLE:
            tz = self.get_timezone_object()
            if tz:
                # If datetime is naive, assume UTC
                if dt.tzinfo is None:
                    dt = pytz.UTC.localize(dt)
                
                # Convert to user's timezone
                local_dt = dt.astimezone(tz)
                return local_dt.strftime(format_str)
        
        # Fallback to basic formatting
        return dt.strftime(format_str)
    
    def get_current_time(self) -> datetime:
        """Get current time in user's timezone."""
        now = datetime.now()
        
        if PYTZ_AVAILABLE:
            tz = self.get_timezone_object()
            if tz:
                return tz.localize(now)
        
        return now
    
    def format_time_ago(self, dt: datetime) -> str:
        """Format time as 'time ago' string with timezone awareness."""
        if not isinstance(dt, datetime):
            return "Unknown time"
        
        now = self.get_current_time()
        
        # Ensure both datetimes have timezone info for comparison
        if dt.tzinfo is None and PYTZ_AVAILABLE:
            dt = pytz.UTC.localize(dt)
        
        if now.tzinfo is None and dt.tzinfo is not None:
            if PYTZ_AVAILABLE:
                now = pytz.UTC.localize(now.replace(tzinfo=None))
        
        try:
            diff = now - dt
            seconds = int(diff.total_seconds())
            
            if seconds < 60:
                return "Just now"
            elif seconds < 3600:
                minutes = seconds // 60
                return f"{minutes}m ago"
            elif seconds < 86400:
                hours = seconds // 3600
                return f"{hours}h ago"
            else:
                days = seconds // 86400
                return f"{days}d ago"
                
        except TypeError:
            return "Unknown time"

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        config_dict = {}
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            # Don't include runtime fields in serialization
            if field_name not in ['missing_dependencies', 'config_loaded_at']:
                config_dict[field_name] = value
        return config_dict
    
    def save_to_file(self, file_path: str):
        """Save configuration to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'StreamlitConfig':
        """Load configuration from JSON file."""
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        return cls(**config_dict)
# Strategy Pattern for Configuration Loading

class ConfigSource:
    """Abstract base class for configuration sources."""
    
    def load(self) -> Dict[str, Any]:
        """Load configuration data from this source."""
        raise NotImplementedError


class DefaultConfigSource(ConfigSource):
    """Provides default configuration values."""
    
    def load(self) -> Dict[str, Any]:
        """Return default configuration values."""
        return {
            # GitHub
            "github_token": None,
            "github_repo_owner": None,
            "github_repo_name": None,
            "github_api_calls_per_hour": 4000,
            "rate_limit_buffer": 500,
            
            # Streamlit
            "streamlit_theme": "dark",
            "streamlit_port": 8501,
            "streamlit_host": "localhost",
            "streamlit_auto_rerun": True,
            "streamlit_max_upload_size": 200,
            
            # Database
            "database_url": "sqlite:///./framework.db",
            "timer_database_url": "sqlite:///./task_timer.db",
            "db_pool_size": 10,
            "db_max_overflow": 20,
            
            # TDAH
            "focus_session_duration": 25,
            "short_break_duration": 5,
            "long_break_duration": 15,
            "sessions_until_long_break": 4,
            "timezone": "America/Fortaleza",
            "enable_focus_tracking": True,
            "enable_sound_alerts": False,
            "enable_notifications": True,
            
            # Gamification
            "enable_gamification": True,
            "points_per_completed_task": 10,
            "points_per_tdd_cycle": 5,
            "streak_bonus_multiplier": 1.5,
            
            # Analytics
            "analytics_retention_days": 90,
            "enable_performance_metrics": True,
            "cache_ttl_seconds": 900,
            
            # Security
            "session_timeout": 480,
            
            # Development
            "debug_mode": False,
            "enable_profiler": False,
            "log_level": "INFO",
            "testing_mode": False,
            "test_database_url": "sqlite:///./test_framework.db"
        }


class EnvFileConfigSource(ConfigSource):
    """Loads configuration from .env files."""
    
    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file
    
    def load(self) -> Dict[str, Any]:
        """Load .env file if available."""
        if not DOTENV_AVAILABLE:
            self._warn_missing_dotenv()
            return {}
        
        self._load_env_file()
        return {}  # .env files populate os.environ, not return values
    
    def _load_env_file(self) -> None:
        """Load the appropriate .env file."""
        if self.env_file:
            load_dotenv(self.env_file)
        else:
            self._load_from_default_locations()
    
    def _load_from_default_locations(self) -> None:
        """Try loading .env from default locations."""
        env_locations = [
            Path(".env"),
            Path("streamlit_extension/.env"),
            Path("config/.env")
        ]
        
        for env_path in env_locations:
            if env_path.exists():
                load_dotenv(env_path)
                break
    
    def _warn_missing_dotenv(self) -> None:
        """Warn if .env files exist but dotenv is not available."""
        env_files_exist = (
            self.env_file or 
            any(Path(p).exists() for p in [".env", "streamlit_extension/.env"])
        )
        
        if env_files_exist:
            logging.info(
                "⚠️ Warning: .env file found but python-dotenv not installed. "
                "Install with: pip install python-dotenv"
            )


class EnvironmentVariableConfigSource(ConfigSource):
    """Loads configuration from environment variables."""
    
    TYPE_CONVERTERS = {
        bool: lambda x: x.lower() in ('true', '1', 'yes', 'on'),
        int: int,
        float: float,
        str: str
    }
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            # GitHub
            "github_token": self._get_env("GITHUB_TOKEN", None),
            "github_repo_owner": self._get_env("GITHUB_REPO_OWNER", None),
            "github_repo_name": self._get_env("GITHUB_REPO_NAME", None),
            "github_api_calls_per_hour": self._get_env("GITHUB_API_CALLS_PER_HOUR", 4000, int),
            "rate_limit_buffer": self._get_env("RATE_LIMIT_BUFFER", 500, int),
            
            # Streamlit
            "streamlit_theme": self._get_env("STREAMLIT_THEME", "dark"),
            "streamlit_port": self._get_env("STREAMLIT_PORT", 8501, int),
            "streamlit_host": self._get_env("STREAMLIT_HOST", "localhost"),
            "streamlit_auto_rerun": self._get_env("STREAMLIT_AUTO_RERUN", True, bool),
            "streamlit_max_upload_size": self._get_env("STREAMLIT_MAX_UPLOAD_SIZE", 200, int),
            
            # Database
            "database_url": self._get_env("DATABASE_URL", "sqlite:///./framework.db"),
            "timer_database_url": self._get_env("TIMER_DATABASE_URL", "sqlite:///./task_timer.db"),
            "db_pool_size": self._get_env("DB_POOL_SIZE", 10, int),
            "db_max_overflow": self._get_env("DB_MAX_OVERFLOW", 20, int),
            
            # TDAH
            "focus_session_duration": self._get_env("FOCUS_SESSION_DURATION", 25, int),
            "short_break_duration": self._get_env("SHORT_BREAK_DURATION", 5, int),
            "long_break_duration": self._get_env("LONG_BREAK_DURATION", 15, int),
            "sessions_until_long_break": self._get_env("SESSIONS_UNTIL_LONG_BREAK", 4, int),
            "timezone": self._get_env("TIMEZONE", "America/Fortaleza"),
            "enable_focus_tracking": self._get_env("ENABLE_FOCUS_TRACKING", True, bool),
            "enable_sound_alerts": self._get_env("ENABLE_SOUND_ALERTS", False, bool),
            "enable_notifications": self._get_env("ENABLE_NOTIFICATIONS", True, bool),
            
            # Gamification
            "enable_gamification": self._get_env("ENABLE_GAMIFICATION", True, bool),
            "points_per_completed_task": self._get_env("POINTS_PER_COMPLETED_TASK", 10, int),
            "points_per_tdd_cycle": self._get_env("POINTS_PER_TDD_CYCLE", 5, int),
            "streak_bonus_multiplier": self._get_env("STREAK_BONUS_MULTIPLIER", 1.5, float),
            
            # Analytics
            "analytics_retention_days": self._get_env("ANALYTICS_RETENTION_DAYS", 90, int),
            "enable_performance_metrics": self._get_env("ENABLE_PERFORMANCE_METRICS", True, bool),
            "cache_ttl_seconds": self._get_env("CACHE_TTL_SECONDS", 900, int),
            
            # Security
            "session_timeout": self._get_env("SESSION_TIMEOUT", 480, int),
            
            # Development
            "debug_mode": self._get_env("DEBUG_MODE", False, bool),
            "enable_profiler": self._get_env("ENABLE_PROFILER", False, bool),
            "log_level": self._get_env("LOG_LEVEL", "INFO"),
            "testing_mode": self._get_env("TESTING_MODE", False, bool),
            "test_database_url": self._get_env("TEST_DATABASE_URL", "sqlite:///./test_framework.db")
        }
    
    def _get_env(self, key: str, default: Any, convert_type: type = str) -> Any:
        """Get environment variable with type conversion."""
        value = os.getenv(key)
        if value is None:
            return default
        
        return self._convert_value(key, value, default, convert_type)
    
    def _convert_value(self, key: str, value: str, default: Any, convert_type: type) -> Any:
        """Convert string value to specified type."""
        try:
            converter = self.TYPE_CONVERTERS.get(convert_type, str)
            return converter(value)
        except ValueError:
            logging.info(f"⚠️ Warning: Invalid value for {key}: '{value}', using default: {default}")
            return default


class ConfigLoader:
    """Main configuration loader using Strategy pattern."""
    
    def __init__(self, sources: Optional[List[ConfigSource]] = None):
        self.sources = sources or []
    
    def load(self, env_file: Optional[str] = None) -> StreamlitConfig:
        """Load configuration from all sources."""
        # Setup default sources if none provided
        if not self.sources:
            self.sources = [
                DefaultConfigSource(),
                EnvFileConfigSource(env_file),
                EnvironmentVariableConfigSource()
            ]
        
        # Load and merge configuration from all sources
        config_data = self._merge_sources()
        
        # Create configuration object
        config = StreamlitConfig(**config_data)
        
        # Add metadata
        self._add_metadata(config)
        
        return config
    
    def _merge_sources(self) -> Dict[str, Any]:
        """Merge configuration from all sources (later sources override earlier ones)."""
        merged_config = {}
        
        for source in self.sources:
            source_data = source.load()
            # Only update with non-None values
            merged_config.update({k: v for k, v in source_data.items() if v is not None})
        
        return merged_config
    
    def _add_metadata(self, config: StreamlitConfig) -> None:
        """Add metadata to configuration."""
        missing_deps = self._check_missing_dependencies()
        config.missing_dependencies = missing_deps
        config.config_loaded_at = str(Path.cwd())
    
    def _check_missing_dependencies(self) -> List[str]:
        """Check for missing optional dependencies."""
        missing_deps = []
        if not DOTENV_AVAILABLE:
            missing_deps.append("python-dotenv")
        if not PYTZ_AVAILABLE:
            missing_deps.append("pytz")
        return missing_deps


def load_config(env_file: Optional[str] = None) -> StreamlitConfig:
    """
    Load configuration using Strategy pattern.
    
    Args:
        env_file: Path to .env file (defaults to searching common locations)
    
    Returns:
        StreamlitConfig: Loaded and validated configuration
    """
    loader = ConfigLoader()
    return loader.load(env_file)


_CONFIG_SINGLETON: Optional[StreamlitConfig] = None
def get_config(env_file: Optional[str] = None) -> StreamlitConfig:
    """Singleton de configuração com carregamento preguiçoso."""
    global _CONFIG_SINGLETON
    if _CONFIG_SINGLETON is None:
        _CONFIG_SINGLETON = load_config(env_file)
        _CONFIG_SINGLETON.config_loaded_at = datetime.utcnow().isoformat()
    return _CONFIG_SINGLETON
def create_streamlit_config_file(output_dir: Optional[Path] = None) -> Path:
    """
    Gera `.streamlit/config.toml` a partir de `get_streamlit_config_dict()`.
    Retorna o caminho do arquivo gerado.
    """
    cfg = get_config()
    data = cfg.get_streamlit_config_dict()

    toml_parts: List[str] = []
    for section, content in data.items():
        toml_parts.append(f"[{section}]")
        if isinstance(content, dict):
            for k, v in content.items():
                if isinstance(v, dict):
                    toml_parts.append(f"\n[{section}.{k}]")
                    for k2, v2 in v.items():
                        val = f"\"{v2}\"" if isinstance(v2, str) else str(v2).lower() if isinstance(v2, bool) else v2
                        toml_parts.append(f"{k2} = {val}")
                else:
                    val = f"\"{v}\"" if isinstance(v, str) else str(v).lower() if isinstance(v, bool) else v
                    toml_parts.append(f"{k} = {val}")
        toml_parts.append("")

    toml_content = "\n".join(toml_parts).strip() + "\n"

    out_dir = output_dir or (Path.cwd() / ".streamlit")
    out_dir.mkdir(exist_ok=True, parents=True)
    out_path = out_dir / "config.toml"
    out_path.write_text(toml_content, encoding="utf-8")
    return out_path
def reload_config(env_file: Optional[str] = None) -> StreamlitConfig:
    """Reload configuration from environment."""
    global _CONFIG_SINGLETON
    _CONFIG_SINGLETON = load_config(env_file)
    _CONFIG_SINGLETON.config_loaded_at = datetime.utcnow().isoformat()
    return _CONFIG_SINGLETON


# Utility functions for timezone handling
def format_datetime_user_tz(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime in user's timezone (convenience function)."""
    config = get_config()
    return config.format_datetime(dt, format_str)


def format_time_ago_user_tz(dt: datetime) -> str:
    """Format time ago in user's timezone (convenience function)."""
    config = get_config()
    return config.format_time_ago(dt)


def get_current_user_time() -> datetime:
    """Get current time in user's timezone (convenience function)."""
    config = get_config()
    return config.get_current_time()