# 🤖 CLAUDE.md - Observability Stack

**Module:** monitoring/  
**Purpose:** Comprehensive monitoring, observability, and alerting system  
**Architecture:** Prometheus + Grafana + structured logging with correlation tracking  
**Last Updated:** 2025-08-17

---

## 📊 **Monitoring System Overview**

Enterprise-grade observability stack featuring:
- **Prometheus Metrics**: Comprehensive metrics collection and storage
- **Grafana Dashboards**: Visual monitoring and alerting interfaces
- **Structured Logging**: JSON logging with correlation ID tracking
- **Health Monitoring**: Real-time system health validation
- **Alerting System**: Multi-channel alert routing and notification
- **Performance Tracking**: Application and infrastructure performance metrics

---

## 🏗️ **Observability Architecture**

### **Component Structure**
```
monitoring/
├── structured_logging.py         # 📊 JSON logging with correlation IDs
├── health_check.py              # 🏥 System health validation
├── graceful_shutdown.py         # 🔄 Graceful shutdown handling
├── prometheus.yml               # 📈 Prometheus configuration
├── grafana_dashboards.json      # 📊 Grafana dashboard definitions
└── alert_rules.yml              # 🚨 Alert rules and thresholds

config/monitoring/
├── README.md                    # 📚 Setup and configuration guide
├── prometheus.yml               # 📈 Production Prometheus config
├── alertmanager.yml             # 🚨 Alert routing configuration
├── alerts.yml                   # 🔔 Alert rule definitions
├── grafana_dashboards.json      # 📊 Production dashboards
├── logging_config.yaml          # 📝 Logging configuration
└── docker-compose.monitoring.yml # 🐳 Container orchestration
```

### **Monitoring Stack Components**

1. **Prometheus**: Metrics collection, storage, and querying
2. **Grafana**: Visualization, dashboards, and alerting
3. **Alertmanager**: Alert routing, grouping, and notification
4. **Node Exporter**: System-level metrics collection
5. **Structured Logging**: Application-level observability
6. **Health Checks**: Real-time system validation

---

## 📊 **Structured Logging System**

### **StructuredLogger** (`structured_logging.py`)

**Purpose**: Comprehensive JSON logging with correlation ID tracking

#### **Core Features**
- **Correlation ID Tracking**: Trace requests across multi-user sessions
- **Structured JSON Output**: Machine-readable log format
- **Context Management**: Request context propagation
- **Performance Metrics**: Built-in timing and performance tracking
- **Security Event Logging**: Security-focused event tracking
- **Integration Ready**: Seamless integration with monitoring systems

#### **Usage Examples**

##### **Basic Structured Logging**
```python
from monitoring.structured_logging import StructuredLogger, correlation_context

# Initialize logger
logger = StructuredLogger("tdd_application")

# Basic logging with correlation
with correlation_context("user_123", "web_request"):
    logger.info("User login successful", {
        "user_id": "user_123",
        "login_method": "oauth",
        "session_duration": 1800
    })
    
    logger.error("Database connection failed", {
        "database": "framework.db",
        "retry_count": 3,
        "error_code": "CONNECTION_TIMEOUT"
    })
```

##### **Performance Tracking**
```python
# Automatic performance measurement
@logger.performance_tracked
def process_epic_data(epic_id):
    # Function automatically logged with execution time
    return epic_processor.process(epic_id)

# Manual performance tracking
with logger.performance_context("database_query"):
    results = db.execute_complex_query()
    # Logs: query_duration_ms, records_processed, cache_hit_ratio
```

##### **Security Event Logging**
```python
# Security-focused logging
logger.security_event("authentication_failure", {
    "user_ip": "192.168.1.100",
    "attempted_username": "admin",
    "failure_reason": "invalid_credentials",
    "attempt_count": 3
})

logger.security_event("csrf_token_validation", {
    "form_id": "client_create",
    "token_valid": True,
    "user_id": "user_123"
})
```

##### **Multi-User Correlation**
```python
# Request correlation across services
def process_user_request(user_id, request_id):
    with correlation_context(user_id, request_id):
        # All logs within this context include correlation IDs
        logger.info("Processing user request")
        
        # Call other services
        epic_service.create_epic(epic_data)  # Logs include correlation
        project_service.assign_project(project_id)  # Logs include correlation
        
        logger.info("Request processing completed")
```

#### **Log Output Format**
```json
{
  "timestamp": "2025-08-17T10:30:00.123Z",
  "level": "INFO",
  "logger": "tdd_application",
  "message": "User login successful",
  "correlation_id": "req_abc123def456",
  "user_id": "user_123",
  "session_id": "sess_789xyz",
  "request_id": "web_request",
  "data": {
    "user_id": "user_123",
    "login_method": "oauth",
    "session_duration": 1800
  },
  "performance": {
    "duration_ms": 45.2,
    "memory_usage_mb": 12.5
  },
  "context": {
    "thread_id": "MainThread",
    "process_id": 1234,
    "environment": "production"
  }
}
```

#### **Advanced Features**

##### **Context Propagation**
```python
# Automatic context inheritance
class EpicService:
    def __init__(self):
        self.logger = StructuredLogger("epic_service")
    
    def create_epic(self, epic_data):
        # Inherits correlation context from parent request
        self.logger.info("Creating new epic", {
            "epic_name": epic_data["name"],
            "task_count": len(epic_data["tasks"])
        })
        
        # Context propagates to database operations
        with self.logger.performance_context("epic_creation"):
            epic_id = self.db.create_epic(epic_data)
            
        return epic_id
```

##### **Alert Integration**
```python
# Automatic alert triggering
logger.alert("database_connection_failure", {
    "severity": "critical",
    "database": "framework.db",
    "retry_attempts": 5,
    "last_success": "2025-08-17T09:45:00Z"
}, alert_channels=["slack", "email"])

# Performance-based alerts
with logger.performance_context("api_response", alert_threshold_ms=1000):
    # Automatically alerts if operation takes > 1000ms
    slow_operation()
```

##### **Sampling and Rate Limiting**
```python
# High-volume log sampling
logger = StructuredLogger("high_traffic", sample_rate=0.1)  # Log 10% of events

# Rate-limited logging for noisy operations
@logger.rate_limited(max_logs_per_minute=10)
def noisy_operation():
    logger.debug("Frequent operation completed")
```

---

## 🏥 **Health Monitoring System**

### **HealthCheck** (`health_check.py`)

**Purpose**: Real-time system health validation and monitoring

#### **Health Check Categories**
- **Database Health**: Connection, performance, integrity
- **Application Health**: Service availability, memory usage, response times
- **Integration Health**: External service connectivity, API availability
- **Security Health**: Authentication system, rate limiting, security policies

#### **Usage Examples**

##### **Basic Health Checks**
```python
from monitoring.health_check import HealthMonitor

# Initialize health monitor
health = HealthMonitor()

# Run all health checks
health_status = health.run_all_checks()

print(f"Overall Status: {health_status['overall_status']}")
print(f"Healthy Services: {health_status['healthy_count']}")
print(f"Critical Issues: {health_status['critical_count']}")
```

##### **Kubernetes Integration**
```python
# Kubernetes liveness probe
@app.route('/health/live')
def liveness_probe():
    return health.get_liveness_status()

# Kubernetes readiness probe  
@app.route('/health/ready')
def readiness_probe():
    return health.get_readiness_status()

# Detailed health status
@app.route('/health')
def health_status():
    return health.get_detailed_status()
```

##### **Custom Health Checks**
```python
# Add custom health check
@health.register_check("epic_sync_status")
def check_epic_sync():
    """Check bidirectional sync health."""
    try:
        last_sync = get_last_sync_time()
        if (datetime.now() - last_sync).hours > 1:
            return {
                "status": "warning",
                "message": "Epic sync stale",
                "last_sync": last_sync.isoformat()
            }
        return {"status": "healthy", "message": "Sync current"}
    except Exception as e:
        return {
            "status": "critical", 
            "message": f"Sync check failed: {e}"
        }
```

#### **Health Check Output**
```json
{
  "overall_status": "healthy",
  "timestamp": "2025-08-17T10:30:00Z",
  "checks": {
    "database_connection": {
      "status": "healthy",
      "response_time_ms": 2.5,
      "message": "Database responsive"
    },
    "memory_usage": {
      "status": "warning", 
      "usage_percent": 78.5,
      "message": "Memory usage elevated"
    },
    "epic_sync_status": {
      "status": "healthy",
      "last_sync": "2025-08-17T10:25:00Z",
      "message": "Sync current"
    }
  },
  "summary": {
    "healthy": 2,
    "warning": 1,
    "critical": 0,
    "total": 3
  }
}
```

---

## 📈 **Prometheus Metrics System**

### **Metrics Configuration** (`prometheus.yml`)

**Purpose**: Comprehensive metrics collection and storage

#### **Scrape Targets**
```yaml
scrape_configs:
  # Streamlit application metrics
  - job_name: 'streamlit-app'
    static_configs:
      - targets: ['localhost:8501']
    metrics_path: '/health/metrics'
    scrape_interval: 10s

  # Database performance metrics
  - job_name: 'database-metrics'
    static_configs:
      - targets: ['localhost:8502']
    metrics_path: '/db/metrics'
    scrape_interval: 30s

  # System metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
    scrape_interval: 15s
```

#### **Custom Metrics Implementation**
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define custom metrics
epic_creation_total = Counter(
    'tdd_epic_creations_total',
    'Total number of epics created',
    ['user_id', 'project_type']
)

response_time_histogram = Histogram(
    'tdd_response_time_seconds',
    'Response time distribution',
    ['endpoint', 'method']
)

active_users_gauge = Gauge(
    'tdd_active_users',
    'Number of currently active users'
)

# Use metrics in application
@response_time_histogram.time()
def process_epic_creation(user_id, epic_data):
    # Automatically measures response time
    epic_id = create_epic(epic_data)
    
    # Increment counter
    epic_creation_total.labels(
        user_id=user_id,
        project_type=epic_data['type']
    ).inc()
    
    return epic_id

# Start metrics server
start_http_server(8502)  # Metrics available at :8502/metrics
```

#### **Application Metrics Categories**

##### **Business Metrics**
- `tdd_epics_created_total`: Total epics created
- `tdd_tasks_completed_total`: Total tasks completed  
- `tdd_focus_sessions_total`: Total focus sessions
- `tdd_user_productivity_score`: User productivity metrics

##### **Performance Metrics**
- `tdd_response_time_seconds`: API response times
- `tdd_database_query_duration_seconds`: Database query performance
- `tdd_cache_hit_ratio`: Cache effectiveness
- `tdd_sync_duration_seconds`: Bidirectional sync performance

##### **System Metrics**
- `tdd_memory_usage_bytes`: Application memory usage
- `tdd_active_connections`: Database connection count
- `tdd_error_rate`: Application error rate
- `tdd_concurrent_users`: Active user sessions

##### **Security Metrics**
- `tdd_auth_attempts_total`: Authentication attempts
- `tdd_csrf_violations_total`: CSRF token violations
- `tdd_rate_limit_hits_total`: Rate limiting activations
- `tdd_security_events_total`: Security-related events

---

## 📊 **Grafana Dashboard System**

### **Dashboard Configuration** (`grafana_dashboards.json`)

**Purpose**: Visual monitoring and alerting interfaces

#### **Dashboard Categories**

##### **Application Overview Dashboard**
```json
{
  "dashboard": {
    "title": "TDD Framework - Application Overview",
    "panels": [
      {
        "title": "Active Users",
        "type": "stat",
        "targets": [{"expr": "tdd_active_users"}]
      },
      {
        "title": "Epic Creation Rate",
        "type": "graph", 
        "targets": [{"expr": "rate(tdd_epic_creations_total[5m])"}]
      },
      {
        "title": "Response Time P95",
        "type": "graph",
        "targets": [{"expr": "histogram_quantile(0.95, tdd_response_time_seconds)"}]
      }
    ]
  }
}
```

##### **Performance Dashboard**
- **Response Time Distribution**: P50, P95, P99 percentiles
- **Database Performance**: Query times, connection pool usage
- **Cache Performance**: Hit rates, memory usage, eviction rates
- **Resource Utilization**: CPU, memory, disk I/O metrics

##### **Business Metrics Dashboard**
- **User Productivity**: Focus session duration, task completion rates
- **Epic Progress**: Creation rates, completion times, goal achievement
- **TDD Cycle Metrics**: Red-Green-Refactor cycle times and success rates
- **System Adoption**: User engagement, feature usage, retention metrics

##### **Security Dashboard**
- **Authentication Metrics**: Login success/failure rates, session durations
- **Security Events**: CSRF violations, rate limiting, suspicious activity
- **Audit Trail**: User actions, data access, configuration changes
- **Compliance Metrics**: Security policy adherence, vulnerability status

#### **Alert Rules Integration**
```yaml
# Grafana alert rules
alerts:
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, tdd_response_time_seconds) > 1.0
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ $value }}s"

  - alert: DatabaseConnectionFailure
    expr: tdd_database_connections_failed_total > 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database connection failures detected"
```

---

## 🚨 **Alerting System**

### **Alert Rules** (`alert_rules.yml`)

**Purpose**: Comprehensive alerting for system health and performance

#### **Alert Categories**

##### **Critical Alerts**
```yaml
groups:
  - name: critical_alerts
    rules:
      - alert: DatabaseDown
        expr: up{job="database-metrics"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"
          description: "Database has been down for more than 1 minute"

      - alert: HighErrorRate
        expr: rate(tdd_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/second"
```

##### **Warning Alerts**
```yaml
  - name: warning_alerts  
    rules:
      - alert: HighMemoryUsage
        expr: tdd_memory_usage_bytes / 1024 / 1024 / 1024 > 2.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}GB"

      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, tdd_response_time_seconds) > 0.5
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "Slow response times"
```

#### **Alertmanager Configuration** (`alertmanager.yml`)
```yaml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@tdd-framework.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    email_configs:
      - to: 'admin@tdd-framework.com'
        subject: 'TDD Framework Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}

  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: 'TDD Framework Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

---

## 🔄 **Graceful Shutdown System**

### **GracefulShutdown** (`graceful_shutdown.py`)

**Purpose**: Ensure clean application shutdown with proper resource cleanup

#### **Usage Examples**

##### **Basic Shutdown Handler**
```python
from monitoring.graceful_shutdown import GracefulShutdown

# Initialize shutdown handler
shutdown = GracefulShutdown()

# Register cleanup functions
@shutdown.register_cleanup
def cleanup_database_connections():
    """Close database connections gracefully."""
    db_pool.close_all_connections()
    logger.info("Database connections closed")

@shutdown.register_cleanup  
def save_user_sessions():
    """Save active user sessions."""
    session_manager.save_all_sessions()
    logger.info("User sessions saved")

# Start application with shutdown handling
try:
    start_application()
except KeyboardInterrupt:
    shutdown.initiate_shutdown()
```

##### **Streamlit Integration**
```python
# Streamlit app with graceful shutdown
import signal
from monitoring.graceful_shutdown import GracefulShutdown

shutdown_handler = GracefulShutdown()

def streamlit_cleanup():
    """Streamlit-specific cleanup."""
    st.cache_data.clear()
    session_cleanup()

shutdown_handler.register_cleanup(streamlit_cleanup)

# Register signal handlers
signal.signal(signal.SIGTERM, shutdown_handler.signal_handler)
signal.signal(signal.SIGINT, shutdown_handler.signal_handler)
```

##### **Container Orchestration**
```python
# Kubernetes-ready shutdown handling
@shutdown.register_cleanup(priority=1)  # High priority
def stop_accepting_requests():
    """Stop accepting new requests."""
    load_balancer.mark_unhealthy()
    time.sleep(5)  # Grace period for existing requests

@shutdown.register_cleanup(priority=2)  # Medium priority
def complete_active_requests():
    """Wait for active requests to complete."""
    while active_request_count() > 0:
        time.sleep(1)
        
@shutdown.register_cleanup(priority=3)  # Low priority
def cleanup_resources():
    """Final resource cleanup."""
    cache.flush()
    log_files.close()
```

---

## 🐳 **Container Orchestration**

### **Docker Compose Setup** (`docker-compose.monitoring.yml`)

**Purpose**: Complete monitoring stack deployment

#### **Service Configuration**
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts.yml:/etc/prometheus/alerts.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - ./grafana_dashboards.json:/var/lib/grafana/dashboards/
      - grafana-storage:/var/lib/grafana

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro

volumes:
  grafana-storage:
```

#### **Deployment Commands**
```bash
# Start monitoring stack
cd config/monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# View logs
docker-compose -f docker-compose.monitoring.yml logs -f

# Stop stack
docker-compose -f docker-compose.monitoring.yml down

# Update configuration
docker-compose -f docker-compose.monitoring.yml restart prometheus
```

---

## 🚀 **Integration Workflows**

### **Application Integration**

#### **Streamlit Integration**
```python
# In streamlit_app.py
from monitoring.structured_logging import StructuredLogger
from monitoring.health_check import HealthMonitor

# Initialize monitoring
logger = StructuredLogger("streamlit_app")
health = HealthMonitor()

# Add health endpoint
if "health" in st.experimental_get_query_params():
    st.json(health.get_detailed_status())
    st.stop()

# Log user interactions
@logger.performance_tracked
def render_page(page_name):
    with correlation_context(st.session_state.user_id, f"page_{page_name}"):
        logger.info(f"Rendering page: {page_name}")
        # Page rendering logic
```

#### **Service Layer Integration**
```python
# In service classes
class EpicService(BaseService):
    def __init__(self):
        super().__init__()
        self.logger = StructuredLogger("epic_service")
        
    def create_epic(self, epic_data):
        with self.logger.performance_context("epic_creation"):
            # Service logic with automatic logging
            result = super().create_epic(epic_data)
            
            # Business metric
            epic_creation_total.labels(
                user_id=self.current_user_id,
                project_type=epic_data['type']
            ).inc()
            
            return result
```

### **Development Workflow**

#### **Local Development**
```bash
# Start monitoring stack
cd config/monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Start application with monitoring
export MONITORING_ENABLED=true
streamlit run streamlit_extension/streamlit_app.py

# Access monitoring interfaces
# Grafana: http://localhost:3000 (admin/admin123)
# Prometheus: http://localhost:9090
```

#### **Testing with Monitoring**
```python
# Test with monitoring
import pytest
from monitoring.structured_logging import StructuredLogger

@pytest.fixture
def monitored_test():
    logger = StructuredLogger("test_suite")
    with logger.performance_context("test_execution"):
        yield logger

def test_epic_creation(monitored_test):
    """Test epic creation with monitoring."""
    logger = monitored_test
    
    logger.info("Starting epic creation test")
    result = epic_service.create_epic(test_data)
    logger.info("Epic creation test completed", {"epic_id": result.id})
    
    assert result.success
```

### **Production Deployment**

#### **Kubernetes Deployment**
```yaml
# kubernetes/monitoring.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tdd-app
spec:
  template:
    spec:
      containers:
      - name: tdd-app
        image: tdd-framework:latest
        ports:
        - containerPort: 8501
        - containerPort: 8502  # Metrics endpoint
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8501
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8501
          initialDelaySeconds: 5
```

#### **Production Monitoring Checklist**
- [ ] Prometheus scraping application metrics
- [ ] Grafana dashboards configured and accessible
- [ ] Alert rules tested and notifications working
- [ ] Log aggregation system receiving structured logs
- [ ] Health checks responding correctly
- [ ] Graceful shutdown tested
- [ ] Resource limits and monitoring thresholds set

---

## 📋 **Monitoring Best Practices**

### **Metrics Design**
- **Use Counter for Events**: Login attempts, API calls, errors
- **Use Gauge for State**: Active users, memory usage, queue size
- **Use Histogram for Timing**: Response times, request durations
- **Label Judiciously**: Avoid high cardinality labels

### **Alerting Strategy** 
- **Alert on Symptoms**: User-facing issues, not technical details
- **Avoid Alert Fatigue**: Set appropriate thresholds and time windows
- **Escalation Paths**: Define clear escalation procedures
- **Runbooks**: Document response procedures for each alert

### **Logging Strategy**
- **Structured Format**: Use JSON for machine readability
- **Correlation IDs**: Track requests across services
- **Appropriate Levels**: DEBUG for development, INFO for business events
- **Security Awareness**: Sanitize sensitive data in logs

### **Dashboard Design**
- **Business Metrics First**: Focus on user-impacting metrics
- **Layered Detail**: Overview → detailed → diagnostic
- **Time Context**: Appropriate time ranges for different metrics
- **Actionable Alerts**: Connect metrics to specific actions

---

## 🔗 **See Also - Related Documentation**

**Main Project Documentation:**
- **📜 [Root CLAUDE.md](../CLAUDE.md)** - System overview, performance metrics, health status
- **📊 [Project README](../README.md)** - Quick start, system requirements, basic monitoring

**System Integration:**
- **📱 [Streamlit Extension](../streamlit_extension/CLAUDE.md)** - Application monitoring, performance tracking
- **⏱️ [Duration System](../duration_system/CLAUDE.md)** - Security monitoring, performance optimization
- **🧪 [Testing](../tests/CLAUDE.md)** - Performance testing, system validation

**Operations & Configuration:**
- **⚙️ [Config](../config/CLAUDE.md)** - Monitoring configuration, environment settings
- **🔧 [Scripts](../scripts/CLAUDE.md)** - Health check scripts, performance benchmarks
- **🔄 [Migration](../migration/CLAUDE.md)** - Migration monitoring, data integrity tracking

---

*This comprehensive monitoring system provides enterprise-grade observability with real-time health monitoring, performance tracking, and proactive alerting for production-ready deployment.*