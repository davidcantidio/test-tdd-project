# PROMPT 6: Environment Configuration System

## 🎯 OBJETIVO
Implementar configurações separadas dev/staging/prod para resolver item do report.md: "Separate environment configs for dev/staging/prod."

## 📁 ARQUIVOS ALVO (SEM INTERSEÇÃO)
- `config/environments/` (DIRETÓRIO NOVO)
- `config/environments/development.py` (NOVO)
- `config/environments/staging.py` (NOVO)
- `config/environments/production.py` (NOVO)
- `streamlit_extension/config/env_manager.py` (NOVO)
- `tests/test_environment_config.py` (NOVO)

## 🚀 DELIVERABLES

### 1. Environment Configuration Files

#### `config/environments/development.py`
```python
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
```

#### `config/environments/staging.py`
```python
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
```

#### `config/environments/production.py`
```python
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
```

### 2. Environment Manager (`streamlit_extension/config/env_manager.py`)

```python
"""
🌍 Environment Configuration Manager

Manages dev/staging/prod configurations with:
- Environment variable substitution
- Configuration validation
- Hot reloading capabilities
- Environment detection
- Secrets management integration
"""

class EnvironmentManager:
    """Manages environment-specific configurations."""
    
    def __init__(self, environment=None):
        """Initialize with auto-detection or explicit environment."""
        
    def load_config(self):
        """Load configuration for current environment."""
        
    def get_database_config(self):
        """Get database configuration with env var substitution."""
        
    def get_redis_config(self):
        """Get Redis configuration with env var substitution."""
        
    def get_security_config(self):
        """Get security configuration."""
        
    def substitute_env_vars(self, config_dict):
        """Substitute ${VAR} patterns with environment variables."""
        
    def validate_config(self):
        """Validate configuration completeness and format."""
        
    def reload_config(self):
        """Hot reload configuration from files."""
```

### 3. Test Suite (`tests/test_environment_config.py`)

```python
"""Test environment configuration system."""

class TestEnvironmentManager:
    def test_environment_detection(self):
        """Test automatic environment detection."""
        
    def test_config_loading(self):
        """Test configuration loading for each environment."""
        
    def test_env_var_substitution(self):
        """Test environment variable substitution."""
        
    def test_config_validation(self):
        """Test configuration validation."""
        
    def test_hot_reload(self):
        """Test configuration hot reloading."""
```

## 🔧 REQUISITOS TÉCNICOS

1. **Environment Detection**: Auto-detect via ENV vars ou parâmetros
2. **Variable Substitution**: ${VAR} replacement com env vars
3. **Validation**: Verificar configs obrigatórios
4. **Hot Reload**: Recarregar configs sem restart
5. **Security**: Não expor secrets em logs
6. **Compatibility**: Integrar com config existente

## 📊 SUCCESS CRITERIA

- [ ] Configurações separadas para dev/staging/prod
- [ ] Environment variable substitution funcional
- [ ] Auto-detection de ambiente
- [ ] Validation robusta de configurações
- [ ] Hot reload capabilities
- [ ] Integração com sistemas existentes