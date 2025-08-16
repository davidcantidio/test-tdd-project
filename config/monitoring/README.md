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
