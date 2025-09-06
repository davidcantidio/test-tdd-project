# 🤖 CLAUDE.md - Configuration Architecture

**Module:** config/  
**Purpose:** Enterprise configuration management with multi-environment support  
**Architecture:** Hierarchical configuration with environment-specific overrides  
**Last Updated:** 2025-08-17

---

## ⚙️ **Configuration System Overview**

Enterprise-grade configuration management featuring:
- **Multi-Environment Support**: Development, staging, production configurations
- **Secret Management**: Secure handling of sensitive configuration data
- **Feature Flags**: Runtime feature control and A/B testing capabilities
- **Configuration Validation**: Type checking and required parameter validation
- **Environment Detection**: Automatic environment detection and configuration loading
- **Integration Ready**: Seamless integration with Docker, Kubernetes, and CI/CD

---

## 🏗️ **Configuration Architecture**

### **Directory Structure**
```
config/
├── environment.py              # 🔧 Configuration loader and manager
├── feature_flags.py            # 🎛️ Feature flag system
├── development.toml            # 🛠️ Development environment settings
├── staging.toml               # 🧪 Staging environment settings
├── production.toml            # 🚀 Production environment settings
├── docker/                    # 🐳 Container configuration
│   ├── Dockerfile             # Application container definition
│   └── docker-compose.yml     # Multi-service orchestration
├── environments/              # 📁 Environment-specific configurations
│   ├── __init__.py            # Environment module initialization
│   ├── development.py         # Development configuration overrides
│   ├── staging.py            # Staging configuration overrides
│   ├── production.py         # Production configuration overrides
│   ├── development.yaml      # Development YAML config
│   ├── staging.yaml          # Staging YAML config
│   ├── production.yaml       # Production YAML config
│   └── testing.yaml          # Testing configuration
├── monitoring/               # 📊 Monitoring and observability configuration
│   ├── README.md            # Monitoring setup guide
│   ├── prometheus.yml       # Metrics collection configuration
│   ├── grafana_dashboards.json # Dashboard definitions
│   ├── alertmanager.yml     # Alert routing configuration
│   ├── alerts.yml          # Alert rule definitions
│   ├── logging_config.yaml # Structured logging configuration
│   └── docker-compose.monitoring.yml # Monitoring stack
├── schemas/                 # 📋 Configuration validation schemas
│   └── config_schema.json   # JSON schema for configuration validation
├── secrets/                 # 🔐 Secret management (environment-dependent)
├── vscode/                  # 🔧 VS Code configuration
│   ├── settings.json       # Editor settings
│   ├── launch.json         # Debug configurations
│   └── extensions.json     # Recommended extensions
├── python/                  # 🐍 Python-specific configuration
│   ├── pyproject.toml      # Project metadata and dependencies
│   ├── pyproject_poetry.toml # Poetry configuration
│   └── pytest.ini         # Testing configuration
└── README.md               # 📚 Comprehensive setup guide
```

### **Configuration Layers**

1. **Base Configuration**: Default values in TOML files
2. **Environment Overrides**: Environment-specific Python modules
3. **Environment Variables**: Secure secrets and runtime overrides
4. **Feature Flags**: Runtime feature control
5. **Validation Layer**: Type checking and required parameter validation

---

## 🔧 **Configuration Management System**

### **EnvironmentManager** (`environment.py`)

**Purpose**: Centralized configuration loading with environment-specific overrides

#### **Configuration Hierarchy**
```python
from config.environment import get_config, is_production, get_environment

# Configuration loading order (later overrides earlier):
# 1. Base TOML file (development.toml, staging.toml, production.toml)
# 2. Environment-specific Python module overrides
# 3. Environment variables (highest priority)
# 4. Feature flag overrides
# 5. Runtime configuration updates

# Get current configuration
config = get_config()

# Environment detection
current_env = get_environment()  # Returns: "development", "staging", "production"
is_dev = is_development()
is_staging = is_staging()
is_prod = is_production()
```

#### **Configuration Structure**
```python
@dataclass
class AppConfig:
    """Complete application configuration."""
    
    # Environment and application info
    environment: str
    debug: bool
    app_name: str
    version: str
    host: str
    port: int
    
    # Authentication and security
    google_oauth: GoogleOAuthConfig
    security: SecurityConfig
    
    # Database configuration
    database: DatabaseConfig
    
    # Performance and caching
    performance: PerformanceConfig
    
    # Monitoring and observability
    monitoring: MonitoringConfig
    
    # Feature flags
    features: FeatureFlags
    
    # External integrations
    integrations: IntegrationConfig
```

#### **Usage Examples**

##### **Basic Configuration Access**
```python
from config.environment import get_config

# Get complete configuration
config = get_config()

# Access nested configuration
oauth_client_id = config.google_oauth.client_id
db_path = config.database.framework_db_path
enable_redis = config.performance.enable_redis
log_level = config.monitoring.log_level
```

##### **Environment-Specific Logic**
```python
from config.environment import is_production, is_development

# Environment-specific behavior
if is_production():
    # Production-specific setup
    enable_ssl = True
    log_level = "WARNING"
    cache_ttl = 3600
elif is_development():
    # Development-specific setup
    enable_ssl = False
    log_level = "DEBUG"
    cache_ttl = 60
```

##### **Configuration Validation**
```python
# Automatic validation on load
try:
    config = get_config()
    print("✅ Configuration valid")
except ConfigurationError as e:
    print(f"❌ Configuration error: {e}")
    print(f"Missing: {e.missing_variables}")
    print(f"Invalid: {e.invalid_values}")
```

#### **Configuration Categories**

##### **GoogleOAuthConfig**
```python
@dataclass
class GoogleOAuthConfig:
    client_id: str          # From GOOGLE_CLIENT_ID env var
    client_secret: str      # From GOOGLE_CLIENT_SECRET env var
    redirect_uri: str       # Environment-specific
    enabled: bool = True    # Can be disabled in development
```

##### **SecurityConfig**
```python
@dataclass
class SecurityConfig:
    require_auth: bool = True
    csrf_token_expiry: int = 3600
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    session_timeout: int = 1800
    password_min_length: int = 8
```

##### **DatabaseConfig**
```python
@dataclass
class DatabaseConfig:
    framework_db_path: str = "framework.db"
    timer_db_path: str = "task_timer.db"
    connection_timeout: int = 30
    pool_size: int = 10
    enable_wal_mode: bool = True
    backup_enabled: bool = True
```

##### **PerformanceConfig**
```python
@dataclass
class PerformanceConfig:
    enable_redis: bool = False
    cache_ttl_seconds: int = 300
    max_memory_cache_mb: int = 100
    enable_compression: bool = True
    default_page_size: int = 50
```

##### **MonitoringConfig**
```python
@dataclass
class MonitoringConfig:
    enable_health_check: bool = True
    enable_metrics: bool = True
    log_level: str = "INFO"
    structured_logging: bool = True
    correlation_tracking: bool = True
    metrics_port: int = 8502
```

---

## 🎛️ **Feature Flag System**

### **FeatureFlags** (`feature_flags.py`)

**Purpose**: Runtime feature control and A/B testing capabilities

#### **Feature Flag Configuration**
```python
from config.feature_flags import FeatureFlags, is_feature_enabled

# Initialize feature flags
flags = FeatureFlags()

# Check feature status
if is_feature_enabled("new_dashboard_ui"):
    render_new_dashboard()
else:
    render_legacy_dashboard()

# Percentage-based rollout
if is_feature_enabled("beta_analytics", user_id="user_123"):
    # 10% of users see beta analytics
    render_beta_analytics()
else:
    render_standard_analytics()
```

#### **Feature Flag Types**

##### **Boolean Flags**
```yaml
# feature_flags.yaml
features:
  new_dashboard_ui:
    enabled: true
    description: "New dashboard user interface"
    
  enhanced_security:
    enabled: false
    description: "Enhanced security features"
    environments: ["staging", "production"]
```

##### **Percentage Rollouts**
```yaml
features:
  beta_analytics:
    type: "percentage"
    percentage: 10
    description: "Beta analytics features for 10% of users"
    
  experimental_caching:
    type: "percentage"
    percentage: 50
    environments: ["development", "staging"]
```

##### **User-Based Flags**
```yaml
features:
  admin_features:
    type: "user_list"
    users: ["admin@example.com", "manager@example.com"]
    description: "Administrative features"
    
  power_user_tools:
    type: "user_attribute"
    attribute: "user_tier"
    values: ["premium", "enterprise"]
```

#### **Dynamic Feature Control**
```python
# Runtime feature flag updates
flags.enable_feature("new_feature", environment="staging")
flags.set_percentage("beta_feature", 25)  # Increase to 25%
flags.add_user_to_feature("premium_feature", "user@example.com")

# Feature flag analytics
analytics = flags.get_feature_analytics()
print(f"Feature usage: {analytics['usage_stats']}")
print(f"A/B test results: {analytics['ab_test_results']}")
```

---

## 🌍 **Environment-Specific Configuration**

### **Development Environment** (`environments/development.py`)

**Purpose**: Development-optimized configuration with debugging features

```python
# Development overrides
def apply_development_overrides(config):
    """Apply development-specific configuration overrides."""
    
    # Disable authentication for easier development
    config.security.require_auth = False
    
    # Enable debug features
    config.debug = True
    config.monitoring.log_level = "DEBUG"
    
    # Faster cache expiration for testing
    config.performance.cache_ttl_seconds = 60
    
    # Local database paths
    config.database.framework_db_path = "dev_framework.db"
    config.database.timer_db_path = "dev_task_timer.db"
    
    # Enable all development features
    config.features.enable_all_dev_features()
    
    return config
```

### **Staging Environment** (`environments/staging.py`)

**Purpose**: Production-like environment for testing and validation

```python
# Staging overrides
def apply_staging_overrides(config):
    """Apply staging-specific configuration overrides."""
    
    # Production-like security
    config.security.require_auth = True
    config.security.enable_rate_limiting = True
    
    # Detailed logging for debugging
    config.monitoring.log_level = "INFO"
    config.monitoring.structured_logging = True
    
    # Staging-specific database
    config.database.framework_db_path = "staging_framework.db"
    
    # Enable staging feature flags
    config.features.enable_staging_features()
    
    # Extended monitoring
    config.monitoring.enable_health_check = True
    config.monitoring.enable_metrics = True
    
    return config
```

### **Production Environment** (`environments/production.py`)

**Purpose**: Production-optimized configuration with maximum security and performance

```python
# Production overrides
def apply_production_overrides(config):
    """Apply production-specific configuration overrides."""
    
    # Maximum security
    config.security.require_auth = True
    config.security.enable_rate_limiting = True
    config.security.session_timeout = 1800  # 30 minutes
    
    # Optimized performance
    config.performance.enable_redis = True
    config.performance.cache_ttl_seconds = 3600  # 1 hour
    config.performance.enable_compression = True
    
    # Production logging
    config.monitoring.log_level = "WARNING"
    config.monitoring.structured_logging = True
    config.monitoring.correlation_tracking = True
    
    # Production database settings
    config.database.enable_wal_mode = True
    config.database.backup_enabled = True
    
    # Feature flags for production
    config.features.enable_production_features_only()
    
    return config
```

---

## 🐳 **Container Configuration**

### **Docker Configuration** (`docker/`)

**Purpose**: Containerized deployment with environment-specific overrides

#### **Application Container** (`Dockerfile`)
```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV TDD_ENVIRONMENT=production
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501

# Install dependencies
COPY pyproject.toml /app/
WORKDIR /app
RUN pip install -e .

# Copy application
COPY . /app/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/health || exit 1

# Start application
CMD ["streamlit", "run", "streamlit_extension/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### **Multi-Service Orchestration** (`docker-compose.yml`)
```yaml
version: '3.8'

services:
  tdd-app:
    build: .
    ports:
      - "8501:8501"
      - "8502:8502"  # Metrics endpoint
    environment:
      - TDD_ENVIRONMENT=${TDD_ENVIRONMENT:-production}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      - redis
      - prometheus

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  redis-data:
```

### **Kubernetes Configuration**
```yaml
# kubernetes/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tdd-config
data:
  TDD_ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  
---
apiVersion: v1
kind: Secret
metadata:
  name: tdd-secrets
type: Opaque
data:
  GOOGLE_CLIENT_ID: <base64-encoded-client-id>
  GOOGLE_CLIENT_SECRET: <base64-encoded-client-secret>

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tdd-app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: tdd-app
        image: tdd-framework:latest
        envFrom:
        - configMapRef:
            name: tdd-config
        - secretRef:
            name: tdd-secrets
        ports:
        - containerPort: 8501
        - containerPort: 8502
```

---

## 📋 **Configuration Validation**

### **Schema Validation** (`schemas/config_schema.json`)

**Purpose**: JSON schema validation for configuration files

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "environment": {
      "type": "string",
      "enum": ["development", "staging", "production"]
    },
    "google_oauth": {
      "type": "object",
      "properties": {
        "client_id": {"type": "string", "minLength": 1},
        "client_secret": {"type": "string", "minLength": 1},
        "enabled": {"type": "boolean"}
      },
      "required": ["client_id", "client_secret"]
    },
    "database": {
      "type": "object",
      "properties": {
        "framework_db_path": {"type": "string"},
        "connection_timeout": {"type": "integer", "minimum": 1},
        "pool_size": {"type": "integer", "minimum": 1, "maximum": 100}
      }
    }
  },
  "required": ["environment"]
}
```

### **Runtime Validation**
```python
from config.environment import validate_configuration

# Validate configuration at startup
validation_result = validate_configuration()

if not validation_result.is_valid:
    for error in validation_result.errors:
        print(f"Configuration error: {error}")
    
    if validation_result.missing_required:
        print(f"Missing required: {validation_result.missing_required}")
    
    sys.exit(1)
```

---

## 🔧 **Development Tools Integration**

### **VS Code Configuration** (`vscode/`)

#### **Editor Settings** (`settings.json`)
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "*.db": false,
    "*.db-wal": true,
    "*.db-shm": true
  }
}
```

#### **Debug Configuration** (`launch.json`)
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Streamlit App",
      "type": "python",
      "request": "launch",
      "module": "streamlit",
      "args": ["run", "streamlit_extension/streamlit_app.py"],
      "env": {"TDD_ENVIRONMENT": "development"},
      "console": "integratedTerminal"
    },
    {
      "name": "Debug Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v"],
      "console": "integratedTerminal"
    }
  ]
}
```

### **Python Configuration** (`python/`)

#### **Project Metadata** (`pyproject.toml`)
```toml
[project]
name = "test-tdd-project"
version = "1.0.0"
description = "Enterprise TDD Framework with Streamlit"
authors = [{name = "TDD Team", email = "team@tdd-framework.com"}]

[project.dependencies]
streamlit = ">=1.28.0"
pandas = ">=2.0.0"
plotly = ">=5.15.0"
pydantic = ">=2.0.0"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "--verbose --cov=streamlit_extension --cov=duration_system"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
target-version = "py311"
```

---

## 🚀 **Configuration Best Practices**

### **Security Guidelines**
- **Never commit secrets**: Use environment variables for sensitive data
- **Validate inputs**: Use schema validation for all configuration
- **Principle of least privilege**: Minimize permissions in production
- **Audit configuration access**: Log configuration reads and updates

### **Performance Optimization**
- **Cache configuration**: Load configuration once at startup
- **Environment-specific tuning**: Optimize cache TTL and connection pools
- **Resource limits**: Set appropriate memory and connection limits
- **Monitoring integration**: Track configuration-related metrics

### **Operational Excellence**
- **Configuration as code**: Version control all configuration files
- **Environment parity**: Minimize differences between environments
- **Documentation**: Keep README.md updated with configuration changes
- **Testing**: Test configuration loading and validation

### **CI/CD Integration**
```yaml
# .github/workflows/config-validation.yml
name: Configuration Validation

on: [push, pull_request]

jobs:
  validate-config:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Validate configuration schemas
      run: |
        python -c "from config.environment import validate_configuration; assert validate_configuration().is_valid"
    - name: Test environment loading
      run: |
        export TDD_ENVIRONMENT=development
        python -c "from config.environment import get_config; config = get_config(); print(f'✅ Config loaded: {config.environment}')"
```

---

## 🔗 **Integration Patterns**

### **Streamlit Integration**
```python
# In streamlit_app.py
from config.environment import get_config, is_production

# Load configuration at startup
config = get_config()

# Environment-specific UI behavior
if is_production():
    st.set_page_config(page_title="TDD Framework", page_icon="🏢")
else:
    st.set_page_config(page_title="TDD Framework (DEV)", page_icon="🛠️")

# Configuration-driven features
if config.features.enable_analytics:
    render_analytics_dashboard()
```

### **Service Layer Integration**
```python
# In service classes
from config.environment import get_config

class DatabaseService:
    def __init__(self):
        self.config = get_config()
        self.db_path = self.config.database.framework_db_path
        self.pool_size = self.config.database.pool_size
        self.timeout = self.config.database.connection_timeout
```

### **Testing Integration**
```python
# In test files
import pytest
from config.environment import get_config, override_config

@pytest.fixture
def test_config():
    """Override configuration for testing."""
    with override_config({
        'database.framework_db_path': ':memory:',
        'security.require_auth': False,
        'performance.cache_ttl_seconds': 1
    }):
        yield get_config()

def test_with_config(test_config):
    """Test using overridden configuration."""
    assert test_config.database.framework_db_path == ':memory:'
    assert not test_config.security.require_auth
```

---

## 🔗 **See Also - Related Documentation**

**Main Project Documentation:**
- **📜 [Root CLAUDE.md](../CLAUDE.md)** - System overview, environment setup, quick start
- **📊 [Project README](../README.md)** - Installation, environment variables, configuration

**Integration Documentation:**
- **📱 [Streamlit Extension](../streamlit_extension/CLAUDE.md)** - Application configuration, security settings
- **⏱️ [Duration System](../duration_system/CLAUDE.md)** - Security configuration, data protection settings
- **🧪 [Testing](../tests/CLAUDE.md)** - Test configuration, environment-specific testing

**Operations & Deployment:**
- **📊 [Monitoring](../monitoring/CLAUDE.md)** - Observability configuration, logging settings
- **🔧 [Scripts](../scripts/CLAUDE.md)** - Environment setup scripts, configuration validation
- **🔄 [Migration](../migration/CLAUDE.md)** - Migration configuration, database settings

---

*This configuration architecture provides enterprise-grade configuration management with comprehensive environment support, security best practices, and seamless integration capabilities for production deployment.*