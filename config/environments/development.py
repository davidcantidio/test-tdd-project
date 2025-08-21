"""Development environment configuration."""

DATABASE_CONFIG = {
    "framework_db_path": "dev_framework.db",
    "timer_db_path": "dev_task_timer.db",
    "connection_pool_size": 5,
    "query_timeout": 30
}

REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": None,
    "max_connections": 10
}

SECURITY_CONFIG = {
    "enable_csrf": True,
    "enable_rate_limiting": True,
    "rate_limit_strict": False,
    "session_timeout": 3600,
    "enable_debug_mode": True
}

LOGGING_CONFIG = {
    "level": "DEBUG",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "enable_file_logging": True,
    "log_file": "logs/dev_app.log"
}