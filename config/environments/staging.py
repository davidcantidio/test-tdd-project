"""Staging environment configuration."""

DATABASE_CONFIG = {
    "framework_db_path": "staging_framework.db",
    "timer_db_path": "staging_task_timer.db", 
    "connection_pool_size": 10,
    "query_timeout": 15
}

REDIS_CONFIG = {
    "host": "staging-redis.internal",
    "port": 6379,
    "db": 1,
    "password": "${REDIS_PASSWORD}",
    "max_connections": 20
}

SECURITY_CONFIG = {
    "enable_csrf": True,
    "enable_rate_limiting": True,
    "rate_limit_strict": True,
    "session_timeout": 1800,
    "enable_debug_mode": False
}
