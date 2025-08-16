# PROMPT 7: Health Check & Graceful Shutdown System

## 🎯 OBJETIVO
Implementar health check endpoint e graceful shutdown para resolver itens do report.md: "Implement health-check endpoint for orchestration tools" e "Ensure graceful shutdown handling for open connections."

## 📁 ARQUIVOS ALVO (SEM INTERSEÇÃO)
- `streamlit_extension/utils/health_check.py` (NOVO)
- `streamlit_extension/pages/health.py` (NOVO)
- `streamlit_extension/utils/shutdown_handler.py` (NOVO)
- `tests/test_health_system.py` (NOVO)

## 🚀 DELIVERABLES

### 1. Health Check System (`streamlit_extension/utils/health_check.py`)

```python
"""
🏥 Health Check System - Production Monitoring

Comprehensive health monitoring for:
- Database connectivity
- Redis cache availability
- File system access
- Memory usage
- Application components
- Integration with orchestration tools (Kubernetes, Docker)
"""

class HealthStatus:
    """Health status constants."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

class ComponentHealth:
    """Individual component health information."""
    def __init__(self, name, status, message="", response_time=None, metadata=None):
        self.name = name
        self.status = status
        self.message = message
        self.response_time = response_time
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

class HealthChecker:
    """Comprehensive health checking system."""
    
    def __init__(self):
        """Initialize health checker with all components."""
        
    def check_database_health(self):
        """Check database connectivity and performance."""
        
    def check_redis_health(self):
        """Check Redis cache availability."""
        
    def check_filesystem_health(self):
        """Check file system access and disk space."""
        
    def check_memory_health(self):
        """Check memory usage and availability."""
        
    def check_application_health(self):
        """Check application-specific components."""
        
    def get_overall_health(self):
        """Get comprehensive health status."""
        
    def get_health_endpoint_response(self):
        """Get standardized health endpoint response."""
        
    def register_custom_check(self, name, check_function):
        """Register custom health check."""
```

### 2. Health Endpoint Page (`streamlit_extension/pages/health.py`)

```python
"""
🏥 Health Check Endpoint Page

Provides:
- REST-like health endpoint for orchestration
- Detailed health dashboard for administrators
- Real-time component monitoring
- Health history and trends
"""

def render_health_endpoint():
    """Render health check endpoint for monitoring tools."""
    
def render_health_dashboard():
    """Render detailed health dashboard for administrators."""
    
def get_health_json():
    """Return JSON health status for API consumption."""
```

### 3. Graceful Shutdown Handler (`streamlit_extension/utils/shutdown_handler.py`)

```python
"""
🔄 Graceful Shutdown Handler

Manages clean application shutdown:
- Database connection cleanup
- Redis connection closure
- Active session completion
- Resource cleanup
- Signal handling (SIGTERM, SIGINT)
"""

class ShutdownHandler:
    """Manages graceful application shutdown."""
    
    def __init__(self):
        """Initialize shutdown handler."""
        
    def register_cleanup_function(self, name, cleanup_func):
        """Register cleanup function for shutdown."""
        
    def cleanup_database_connections(self):
        """Clean up all database connections."""
        
    def cleanup_redis_connections(self):
        """Clean up Redis connections."""
        
    def cleanup_active_sessions(self):
        """Complete or save active user sessions."""
        
    def cleanup_temporary_files(self):
        """Clean up temporary files and caches."""
        
    def perform_graceful_shutdown(self):
        """Execute complete graceful shutdown sequence."""
        
    def install_signal_handlers(self):
        """Install signal handlers for clean shutdown."""
```

### 4. Test Suite (`tests/test_health_system.py`)

```python
"""Test health check and shutdown systems."""

class TestHealthChecker:
    def test_database_health_check(self):
        """Test database health checking."""
        
    def test_redis_health_check(self):
        """Test Redis health checking."""
        
    def test_overall_health_status(self):
        """Test overall health status calculation."""
        
    def test_health_endpoint_response(self):
        """Test health endpoint JSON response format."""

class TestShutdownHandler:
    def test_cleanup_registration(self):
        """Test cleanup function registration."""
        
    def test_graceful_shutdown_sequence(self):
        """Test complete shutdown sequence."""
        
    def test_signal_handling(self):
        """Test signal handler installation."""
```

## 🔧 REQUISITOS TÉCNICOS

1. **Health Checks**: Database, Redis, filesystem, memory
2. **Response Format**: Padronizado para orquestração (Kubernetes)
3. **Performance**: Health checks < 500ms
4. **Graceful Shutdown**: Cleanup completo de recursos
5. **Signal Handling**: SIGTERM, SIGINT support
6. **Logging**: Eventos de health e shutdown

## 📊 SUCCESS CRITERIA

- [ ] Health endpoint funcional para orquestração
- [ ] Checks abrangentes de todos os componentes
- [ ] Graceful shutdown com cleanup completo
- [ ] Signal handlers instalados
- [ ] Dashboard de health para administradores
- [ ] Performance < 500ms para health checks