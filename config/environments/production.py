"""Production environment configuration."""

DATABASE_CONFIG = {
    "framework_db_path": "${DB_PATH}/framework.db",
    "timer_db_path": "${DB_PATH}/task_timer.db",
    "connection_pool_size": 20,
    "query_timeout": 10,
    "enable_backup": True,
    "backup_schedule": "0 2 * * *"  # Daily at 2 AM
}

REDIS_CONFIG = {
    "host": "${REDIS_HOST}",
    "port": "${REDIS_PORT}",
    "db": 0,
    "password": "${REDIS_PASSWORD}",
    "max_connections": 50,
    "connection_pool_timeout": 5,
    "ssl": True
}

SECURITY_CONFIG = {
    "enable_csrf": True,
    "enable_rate_limiting": True,
    "rate_limit_strict": True,
    "session_timeout": 900,
    "enable_debug_mode": False,
    "force_https": True,
    "enable_audit_logging": True
}