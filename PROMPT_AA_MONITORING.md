# 🤖 PROMPT AA: MONITORING & OBSERVABILITY STACK

## 🎯 OBJECTIVE
Create a complete monitoring and observability stack for the test-tdd-project with Prometheus, Grafana, and structured logging configuration as required by report.md.

## 📁 FILES TO CREATE

### 1. config/monitoring/prometheus.yml
```yaml
# Prometheus configuration for TDD Project monitoring
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    project: 'test-tdd-project'
    environment: '${ENVIRONMENT:-development}'

rule_files:
  - "alerts.yml"

scrape_configs:
  # Streamlit application metrics
  - job_name: 'streamlit-app'
    static_configs:
      - targets: ['localhost:8501']
    metrics_path: '/health/metrics'
    scrape_interval: 10s

  # Database metrics
  - job_name: 'sqlite-exporter'
    static_configs:
      - targets: ['localhost:9100']
    scrape_interval: 30s

  # System metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  # Application metrics
  - job_name: 'app-metrics'
    static_configs:
      - targets: ['localhost:8502']
    metrics_path: '/metrics'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 2. config/monitoring/alerts.yml
```yaml
# Alert rules for TDD Project
groups:
  - name: database_alerts
    rules:
      - alert: DatabaseConnectionFailure
        expr: database_connections_failed_total > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failures detected"
          description: "{{ $labels.instance }} has {{ $value }} failed connections"

      - alert: SlowQueries
        expr: database_query_duration_seconds > 1
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Slow database queries detected"

  - name: application_alerts
    rules:
      - alert: HighErrorRate
        expr: error_rate > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate in application"

      - alert: MemoryUsageHigh
        expr: memory_usage_percent > 90
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"

  - name: performance_alerts
    rules:
      - alert: ResponseTimeHigh
        expr: response_time_seconds > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response times detected"
```

### 3. config/monitoring/grafana_dashboards.json
```json
{
  "dashboard": {
    "id": null,
    "title": "Test TDD Project - Main Dashboard",
    "tags": ["streamlit", "tdd", "monitoring"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Application Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"streamlit-app\"}",
            "legendFormat": "Streamlit Status"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "database_connections_active",
            "legendFormat": "Active Connections"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Response Times",
        "type": "graph",
        "targets": [
          {
            "expr": "http_request_duration_seconds",
            "legendFormat": "{{ handler }}"
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"4..|5..\"}[5m])",
            "legendFormat": "Error Rate"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
      },
      {
        "id": 5,
        "title": "TDD Metrics",
        "type": "table",
        "targets": [
          {
            "expr": "tdd_phase_duration_seconds",
            "legendFormat": "{{ phase }}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

### 4. config/monitoring/docker-compose.monitoring.yml
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: tdd-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts.yml:/etc/prometheus/alerts.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:latest
    container_name: tdd-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana_dashboards.json:/etc/grafana/provisioning/dashboards/dashboard.json
    depends_on:
      - prometheus

  node-exporter:
    image: prom/node-exporter:latest
    container_name: tdd-node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'

  alertmanager:
    image: prom/alertmanager:latest
    container_name: tdd-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml

volumes:
  prometheus_data:
  grafana_data:
```

### 5. config/monitoring/alertmanager.yml
```yaml
# Alertmanager configuration
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@test-tdd-project.local'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/webhook'
        send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
```

### 6. config/monitoring/logging_config.yaml
```yaml
# Structured logging configuration
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  json:
    class: pythonjsonlogger.jsonlogger.JsonFormatter
    format: '%(asctime)s %(name)s %(levelname)s %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: json
    filename: logs/application.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

  prometheus:
    class: prometheus_client.logging.PrometheusHandler
    level: WARNING

loggers:
  streamlit_extension:
    level: DEBUG
    handlers: [console, file, prometheus]
    propagate: false
  
  duration_system:
    level: DEBUG
    handlers: [console, file]
    propagate: false

root:
  level: WARNING
  handlers: [console, file]
```

### 7. config/monitoring/README.md
```markdown
# Monitoring & Observability Stack

## Components
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Node Exporter**: System metrics
- **Alertmanager**: Alert routing and notification

## Setup Instructions

1. Start monitoring stack:
   ```bash
   cd config/monitoring
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

2. Access dashboards:
   - Grafana: http://localhost:3000 (admin/admin123)
   - Prometheus: http://localhost:9090
   - Alertmanager: http://localhost:9093

3. Configure application metrics endpoint in health.py

## Metrics Exposed
- Application health status
- Database connection metrics
- Response times and error rates
- TDD phase completion metrics
- System resource usage

## Alerts Configured
- Database connection failures
- High response times
- Memory usage warnings
- Error rate monitoring
```

## 🔧 IMPLEMENTATION REQUIREMENTS

1. Create `config/monitoring/` directory
2. Generate all configuration files with proper YAML/JSON syntax
3. Ensure Docker Compose compatibility
4. Include comprehensive metrics for TDD project
5. Set up alerts for critical system events
6. Create ready-to-use Grafana dashboard
7. Include detailed setup documentation

## ✅ VERIFICATION CHECKLIST

- [ ] All configuration files created in correct directory
- [ ] Prometheus configuration validates
- [ ] Grafana dashboard JSON is valid
- [ ] Docker Compose file syntax correct
- [ ] Alert rules cover database, application, and performance
- [ ] Logging configuration supports structured logging
- [ ] README.md provides clear setup instructions

## 🎯 CONTEXT
This addresses report.md requirement: "Set up structured logging and monitoring (e.g., Prometheus/Grafana)" in the Production Deployment Checklist.

The monitoring stack should integrate with existing health endpoints and provide enterprise-grade observability for the TDD project.