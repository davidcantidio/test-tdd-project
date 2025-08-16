# 🏥 CODEX PROMPT I: Health Check Endpoint & Monitoring

## 🎯 **OBJETIVO**
Implementar endpoint de health check conforme gap do report.md: "Implement health-check endpoint for orchestration tools" e "Set up structured logging and monitoring".

## 📁 **ARQUIVOS ALVO (ISOLADOS - SEM INTERSEÇÃO)**
```
streamlit_extension/endpoints/                     # Novo diretório
streamlit_extension/endpoints/__init__.py          # Package init
streamlit_extension/endpoints/health.py            # Health check endpoint
streamlit_extension/utils/monitoring.py            # Sistema de monitoramento
streamlit_extension/utils/structured_logging.py    # Logging estruturado
streamlit_extension/utils/graceful_shutdown.py     # Shutdown handler
tests/test_health_endpoint.py                      # Testes do endpoint
tests/test_monitoring.py                           # Testes de monitoramento
scripts/health_check.py                            # Script standalone
```

## 📋 **ESPECIFICAÇÕES TÉCNICAS**

### **1. streamlit_extension/endpoints/health.py**
```python
# HealthCheckEndpoint class:
# - basic_health()
# - detailed_health()
# - readiness_check()
# - liveness_check()

# HealthStatus enum:
# - HEALTHY
# - DEGRADED
# - UNHEALTHY
# - MAINTENANCE

# ComponentChecker class:
# - check_database()
# - check_cache()
# - check_external_apis()
# - check_disk_space()
# - check_memory_usage()
```

### **2. streamlit_extension/utils/monitoring.py**
```python
# SystemMonitor class:
# - collect_metrics()
# - check_performance()
# - generate_alerts()
# - export_metrics()

# MetricsCollector class:
# - cpu_usage()
# - memory_usage()
# - disk_usage()
# - connection_pool_stats()
# - response_time_metrics()

# AlertManager class:
# - define_thresholds()
# - check_alerts()
# - send_notifications()
```

### **3. streamlit_extension/utils/structured_logging.py**
```python
# StructuredLogger class:
# - log_with_correlation()
# - log_performance()
# - log_security_event()
# - log_business_event()

# LogFormat enum:
# - JSON
# - GELF
# - PLAIN_TEXT

# LogLevel enum:
# - DEBUG
# - INFO
# - WARNING
# - ERROR
# - CRITICAL
```

### **4. streamlit_extension/utils/graceful_shutdown.py**
```python
# GracefulShutdownHandler class:
# - register_signal_handlers()
# - shutdown_sequence()
# - cleanup_resources()
# - wait_for_completion()

# ShutdownPhase enum:
# - STOP_ACCEPTING_REQUESTS
# - DRAIN_CONNECTIONS
# - CLEANUP_RESOURCES
# - FINAL_SHUTDOWN
```

## 🧪 **CASOS DE TESTE OBRIGATÓRIOS**

### **Health Check Tests:**
```python
def test_basic_health_check():
    # Health check básico retorna 200
    
def test_detailed_health_check():
    # Health check detalhado com componentes
    
def test_readiness_check():
    # Readiness probe para Kubernetes
    
def test_liveness_check():
    # Liveness probe para Kubernetes
    
def test_health_check_with_database_down():
    # Health check quando database está down
    
def test_health_check_with_degraded_performance():
    # Health check com performance degradada
```

### **Monitoring Tests:**
```python
def test_metrics_collection():
    # Coleta de métricas do sistema
    
def test_performance_monitoring():
    # Monitoramento de performance
    
def test_alert_generation():
    # Geração de alertas
    
def test_metrics_export():
    # Export de métricas para Prometheus
```

### **Logging Tests:**
```python
def test_structured_logging():
    # Logging estruturado em JSON
    
def test_correlation_id_logging():
    # Logging com correlation IDs
    
def test_security_event_logging():
    # Logging de eventos de segurança
    
def test_performance_logging():
    # Logging de métricas de performance
```

## 🔧 **HEALTH CHECK ENDPOINTS**

### **Basic Health Check:**
```python
GET /health
Response:
{
    "status": "healthy",
    "timestamp": "2025-01-15T10:30:00Z",
    "uptime": "72:30:15",
    "version": "1.0.0"
}
```

### **Detailed Health Check:**
```python
GET /health/detailed
Response:
{
    "status": "healthy",
    "timestamp": "2025-01-15T10:30:00Z",
    "components": {
        "database": {
            "status": "healthy",
            "response_time": "2ms",
            "connections": {
                "active": 5,
                "idle": 3,
                "max": 20
            }
        },
        "cache": {
            "status": "healthy",
            "hit_rate": "95%",
            "memory_usage": "45%"
        },
        "system": {
            "cpu_usage": "25%",
            "memory_usage": "60%",
            "disk_usage": "40%"
        }
    }
}
```

### **Readiness Check:**
```python
GET /health/ready
Response: 200 OK if ready, 503 if not
{
    "ready": true,
    "dependencies": {
        "database": "connected",
        "cache": "available"
    }
}
```

### **Liveness Check:**
```python
GET /health/live
Response: 200 OK if alive, 503 if dead
{
    "alive": true,
    "last_heartbeat": "2025-01-15T10:30:00Z"
}
```

## 📊 **MONITORAMENTO E MÉTRICAS**

### **System Metrics:**
```python
# CPU, Memory, Disk usage
# Network I/O
# Process count
# File descriptor usage
```

### **Application Metrics:**
```python
# Request count and latency
# Error rates
# Database connection pool
# Cache hit/miss rates
# Active user sessions
```

### **Business Metrics:**
```python
# Client creation rate
# Project completion rate
# Task throughput
# User engagement metrics
```

## 🚨 **ALERTAS E THRESHOLDS**

### **Critical Alerts:**
```python
THRESHOLDS = {
    "cpu_usage": 85,
    "memory_usage": 90,
    "disk_usage": 85,
    "error_rate": 5,
    "response_time": 5000,  # 5 seconds
    "database_connections": 18  # 90% of max
}
```

### **Alert Actions:**
```python
# Log alert
# Send notification (email, Slack, PagerDuty)
# Auto-scale if configured
# Circuit breaker activation
```

## 🎯 **CRITÉRIOS DE SUCESSO**
1. **4 tipos** de health checks implementados (basic/detailed/ready/live)
2. **Structured logging** em formato JSON
3. **System monitoring** com métricas de sistema e aplicação
4. **Graceful shutdown** handling
5. **15+ testes** cobrindo todos os cenários
6. **Prometheus integration** para métricas
7. **Kubernetes probes** compatível

## 🔗 **INTEGRAÇÃO**
```python
# Kubernetes deployment:
livenessProbe:
  httpGet:
    path: /health/live
    port: 8501
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8501
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

**🎯 RESULTADO ESPERADO:** Sistema completo de health checks e monitoramento que resolve gaps de "health-check endpoint", "structured logging and monitoring" e "graceful shutdown handling" do report.md, preparando o sistema para deployment em produção com orchestration tools.