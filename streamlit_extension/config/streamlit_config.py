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
            print(f"⚠️ Warning: streamlit_port {self.streamlit_port} outside recommended range (1024-65535)")
        
        # Validate session durations
        if self.focus_session_duration < 5 or self.focus_session_duration > 120:
            print(f"⚠️ Warning: focus_session_duration {self.focus_session_duration} outside recommended range (5-120 minutes)")
        
        # Validate timezone
        if PYTZ_AVAILABLE and self.timezone:
            try:
                pytz.timezone(self.timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                print(f"⚠️ Warning: Unknown timezone '{self.timezone}', falling back to UTC")
                self.timezone = "UTC"
        
        # Check GitHub configuration completeness
        github_fields = [self.github_token, self.github_repo_owner, self.github_repo_name]
        if any(github_fields) and not all(github_fields):
            print("⚠️ Warning: Incomplete GitHub configuration. Set all: GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME")
    
    def is_github_configured(self) -> bool:
        """Check if GitHub integration is properly configured."""
        return all([self.github_token, self.github_repo_owner, self.github_repo_name])
    
    def get_database_path(self) -> Path:
        """Get the main database file path."""
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", ""))
        return Path("framework.db")  # fallback
    
    def get_timer_database_path(self) -> Path:
        """Get the timer database file path."""
        if self.timer_database_url.startswith("sqlite:///"):
            return Path(self.timer_database_url.replace("sqlite:///", ""))
        return Path("task_timer.db")  # fallback
    
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
            "client": {
                "showSidebarNavigation": True,
                "toolbarMode": "auto"
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
                print(f"⚠️ Unknown timezone '{self.timezone}', using UTC")
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


def load_config(env_file: Optional[str] = None) -> StreamlitConfig:
    """
    Load configuration from environment variables and .env file.
    
    Args:
        env_file: Path to .env file (defaults to .env in current directory)
    
    Returns:
        StreamlitConfig: Loaded and validated configuration
    """
    # Load .env file if available
    if DOTENV_AVAILABLE:
        if env_file:
            load_dotenv(env_file)
        else:
            # Try multiple .env file locations
            env_locations = [
                Path(".env"),
                Path("streamlit_extension/.env"),
                Path("config/.env")
            ]
            
            for env_path in env_locations:
                if env_path.exists():
                    load_dotenv(env_path)
                    break
    else:
        if env_file or any(Path(p).exists() for p in [".env", "streamlit_extension/.env"]):
            print("⚠️ Warning: .env file found but python-dotenv not installed. Install with: pip install python-dotenv")
    
    # Helper function to get environment variable with type conversion
    def get_env(key: str, default: Any, convert_type: type = str) -> Any:
        value = os.getenv(key)
        if value is None:
            return default
        
        try:
            if convert_type == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            elif convert_type == int:
                return int(value)
            elif convert_type == float:
                return float(value)
            else:
                return value
        except ValueError:
            print(f"⚠️ Warning: Invalid value for {key}: '{value}', using default: {default}")
            return default
    
    # Load all configuration values
    config = StreamlitConfig(
        # GitHub
        github_token=get_env("GITHUB_TOKEN", None),
        github_repo_owner=get_env("GITHUB_REPO_OWNER", None),
        github_repo_name=get_env("GITHUB_REPO_NAME", None),
        github_api_calls_per_hour=get_env("GITHUB_API_CALLS_PER_HOUR", 4000, int),
        rate_limit_buffer=get_env("RATE_LIMIT_BUFFER", 500, int),
        
        # Streamlit
        streamlit_theme=get_env("STREAMLIT_THEME", "dark"),
        streamlit_port=get_env("STREAMLIT_PORT", 8501, int),
        streamlit_host=get_env("STREAMLIT_HOST", "localhost"),
        streamlit_auto_rerun=get_env("STREAMLIT_AUTO_RERUN", True, bool),
        streamlit_max_upload_size=get_env("STREAMLIT_MAX_UPLOAD_SIZE", 200, int),
        
        # Database
        database_url=get_env("DATABASE_URL", "sqlite:///./framework.db"),
        timer_database_url=get_env("TIMER_DATABASE_URL", "sqlite:///./task_timer.db"),
        db_pool_size=get_env("DB_POOL_SIZE", 10, int),
        db_max_overflow=get_env("DB_MAX_OVERFLOW", 20, int),
        
        # TDAH
        focus_session_duration=get_env("FOCUS_SESSION_DURATION", 25, int),
        short_break_duration=get_env("SHORT_BREAK_DURATION", 5, int),
        long_break_duration=get_env("LONG_BREAK_DURATION", 15, int),
        sessions_until_long_break=get_env("SESSIONS_UNTIL_LONG_BREAK", 4, int),
        timezone=get_env("TIMEZONE", "America/Fortaleza"),
        enable_focus_tracking=get_env("ENABLE_FOCUS_TRACKING", True, bool),
        enable_sound_alerts=get_env("ENABLE_SOUND_ALERTS", False, bool),
        enable_notifications=get_env("ENABLE_NOTIFICATIONS", True, bool),
        
        # Gamification
        enable_gamification=get_env("ENABLE_GAMIFICATION", True, bool),
        points_per_completed_task=get_env("POINTS_PER_COMPLETED_TASK", 10, int),
        points_per_tdd_cycle=get_env("POINTS_PER_TDD_CYCLE", 5, int),
        streak_bonus_multiplier=get_env("STREAK_BONUS_MULTIPLIER", 1.5, float),
        
        # Analytics
        analytics_retention_days=get_env("ANALYTICS_RETENTION_DAYS", 90, int),
        enable_performance_metrics=get_env("ENABLE_PERFORMANCE_METRICS", True, bool),
        cache_ttl_seconds=get_env("CACHE_TTL_SECONDS", 900, int),
        
        # Security
        session_timeout=get_env("SESSION_TIMEOUT", 480, int),
        
        # Development
        debug_mode=get_env("DEBUG_MODE", False, bool),
        enable_profiler=get_env("ENABLE_PROFILER", False, bool),
        log_level=get_env("LOG_LEVEL", "INFO"),
        testing_mode=get_env("TESTING_MODE", False, bool),
        test_database_url=get_env("TEST_DATABASE_URL", "sqlite:///./test_framework.db")
    )
    
    # Check for missing dependencies
    missing_deps = []
    if not DOTENV_AVAILABLE:
        missing_deps.append("python-dotenv")
    if not PYTZ_AVAILABLE:
        missing_deps.append("pytz")
    
    config.missing_dependencies = missing_deps
    config.config_loaded_at = str(Path.cwd())
    
    return config


def create_streamlit_config_file(config: StreamlitConfig, output_path: str = ".streamlit/config.toml"):
    """
    Create Streamlit config.toml file from configuration.
    
    Args:
        config: StreamlitConfig instance
        output_path: Path to save config.toml file
    """
    # Create .streamlit directory if it doesn't exist
    config_path = Path(output_path)
    config_path.parent.mkdir(exist_ok=True)
    
    # Get streamlit configuration
    streamlit_config = config.get_streamlit_config_dict()
    
    # Convert to TOML format
    toml_content = "[server]\n"
    for key, value in streamlit_config["server"].items():
        if isinstance(value, str):
            toml_content += f'{key} = "{value}"\n'
        else:
            toml_content += f'{key} = {str(value).lower()}\n'
    
    toml_content += "\n[theme]\n"
    for key, value in streamlit_config["theme"].items():
        toml_content += f'{key} = "{value}"\n'
    
    toml_content += "\n[client]\n"
    for key, value in streamlit_config["client"].items():
        if isinstance(value, bool):
            toml_content += f'{key} = {str(value).lower()}\n'
        else:
            toml_content += f'{key} = "{value}"\n'
    
    toml_content += "\n[runner]\n"
    for key, value in streamlit_config["runner"].items():
        toml_content += f'{key} = {str(value).lower()}\n'
    
    # Write to file
    with open(config_path, 'w') as f:
        f.write(toml_content)
    
    print(f"📁 Streamlit config saved to: {output_path}")


# Global configuration instance (lazy loaded)
_config: Optional[StreamlitConfig] = None

def get_config() -> StreamlitConfig:
    """Get global configuration instance (lazy loaded)."""
    global _config
    if _config is None:
        _config = load_config()
    return _config

def reload_config(env_file: Optional[str] = None) -> StreamlitConfig:
    """Reload configuration from environment."""
    global _config
    _config = load_config(env_file)
    return _config


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