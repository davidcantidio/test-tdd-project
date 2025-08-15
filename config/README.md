# 🌍 Environment Configuration System

This directory contains the environment-specific configuration system for the TDD Framework, addressing the report.md requirement for **"Separate environment configs for dev/staging/prod"** and **"Store secrets in vault or environment variables"**.

## 📁 File Structure

```
config/
├── environment.py      # Configuration loader and manager
├── development.toml    # Development environment settings
├── staging.toml        # Staging environment settings  
├── production.toml     # Production environment settings
├── .env.example        # Environment variables template
└── README.md          # This documentation
```

## 🚀 Quick Start

### 1. Set Environment

```bash
# For development (default)
export TDD_ENVIRONMENT=development

# For staging
export TDD_ENVIRONMENT=staging

# For production
export TDD_ENVIRONMENT=production
```

### 2. Configure Secrets

Copy the example environment file and set your secrets:

```bash
cp config/.env.example .env
# Edit .env with your actual values
```

### 3. Use in Code

```python
from config.environment import get_config, is_production

# Get full configuration
config = get_config()

# Check environment
if is_production():
    print("Running in production mode")

# Access specific configs
db_config = get_config().database
oauth_config = get_config().google_oauth
```

## 🔧 Configuration Hierarchy

The configuration system loads settings in this order (later overrides earlier):

1. **Base config file** (`{environment}.toml`)
2. **Environment variables** (secure secrets)
3. **Environment-specific overrides** (in code)

## 🌍 Environment Details

### Development
- **Purpose**: Local development
- **Authentication**: Optional (can be disabled)
- **Logging**: Debug level, console output
- **Database**: Local SQLite files
- **Caching**: Memory only, short TTL
- **Security**: Relaxed for development convenience

### Staging
- **Purpose**: Pre-production testing
- **Authentication**: Required
- **Logging**: Structured JSON, file output
- **Database**: Persistent volumes
- **Caching**: Redis optional
- **Security**: Production-like security

### Production
- **Purpose**: Live production deployment
- **Authentication**: Mandatory
- **Logging**: Warnings only, structured
- **Database**: Encrypted, backed up
- **Caching**: Redis required
- **Security**: Maximum security settings

## 🔐 Security Best Practices

### Environment Variables (SECURE)

All sensitive data should be stored in environment variables:

```bash
# Required for authentication
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"

# Database security
export DATABASE_ENCRYPTION_KEY="your-32-char-key"
export SESSION_SECRET_KEY="your-session-key"
```

### Secrets Management

For production deployments, use a secrets management service:

- **AWS**: AWS Secrets Manager
- **Google Cloud**: Secret Manager
- **Azure**: Key Vault
- **Kubernetes**: Secrets
- **Docker**: Docker Secrets

### File Permissions

Ensure config files have appropriate permissions:

```bash
chmod 600 .env                    # Only owner can read/write
chmod 644 config/*.toml          # Read-only for others
```

## 📊 Configuration Reference

### AppConfig Structure

```python
@dataclass
class AppConfig:
    environment: str
    debug: bool
    app_name: str
    host: str
    port: int
    
    google_oauth: GoogleOAuthConfig
    database: DatabaseConfig
    security: SecurityConfig
    performance: PerformanceConfig
    monitoring: MonitoringConfig
```

### Key Configuration Sections

#### Google OAuth
```python
config.google_oauth.client_id      # From GOOGLE_CLIENT_ID
config.google_oauth.client_secret  # From GOOGLE_CLIENT_SECRET
config.google_oauth.redirect_uri   # Environment-specific
```

#### Database
```python
config.database.framework_db_path  # Database file location
config.database.connection_timeout # Connection timeout
config.database.pool_size         # Connection pool size
```

#### Security
```python
config.security.require_auth      # Authentication required
config.security.csrf_token_expiry # CSRF token lifetime
config.security.enable_rate_limiting # Rate limiting
```

#### Performance
```python
config.performance.enable_redis   # Redis caching
config.performance.cache_ttl_seconds # Cache lifetime
config.performance.default_page_size # Pagination
```

#### Monitoring
```python
config.monitoring.enable_health_check # Health endpoint
config.monitoring.log_level           # Logging level
config.monitoring.enable_metrics      # Metrics collection
```

## 🧪 Testing Configuration

Test configuration loading:

```bash
# Test current environment
python config/environment.py

# Test specific environment
TDD_ENVIRONMENT=production python config/environment.py
```

## 🔄 Configuration Updates

### Adding New Settings

1. **Add to dataclass** in `environment.py`
2. **Update TOML files** with default values
3. **Add environment variable** support if needed
4. **Update validation** logic

### Environment-Specific Overrides

Add overrides in `_apply_environment_overrides()`:

```python
if self.environment == "production":
    config.new_setting = "production_value"
```

## 🚨 Production Deployment

### Required Environment Variables

For production, these environment variables are **MANDATORY**:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `DATABASE_ENCRYPTION_KEY`
- `SESSION_SECRET_KEY`

### Validation

The system validates configuration on startup:

- Required environment variables
- OAuth credentials (if auth enabled)
- Database file existence (production)
- Network connectivity (Redis)

### Error Handling

Configuration errors will prevent startup:

```
ValueError: Missing required environment variables for production: 
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
```

## 📈 Monitoring

### Health Checks

When enabled, provides health check endpoint:

```
GET /health
{
  "status": "healthy",
  "environment": "production",
  "version": "1.0.0",
  "timestamp": "2025-08-15T10:30:00Z"
}
```

### Metrics

When enabled, provides metrics endpoint:

```
GET /metrics
# Prometheus-compatible metrics
```

## 🔍 Troubleshooting

### Common Issues

**Config file not found**
```
WARNING: Config file not found: config/production.toml, using defaults
```
*Solution*: Ensure TOML file exists for environment

**Missing environment variables**
```
ValueError: Missing required environment variables for production
```
*Solution*: Set required environment variables

**Authentication failure**
```
ValueError: Google OAuth credentials required when authentication is enabled
```
*Solution*: Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET

### Debug Mode

Enable debug logging to troubleshoot:

```bash
export LOG_LEVEL=DEBUG
python your_app.py
```

## 📋 Migration from Legacy Config

To migrate from `.streamlit/secrets.toml`:

1. **Set environment**: `export TDD_ENVIRONMENT=development`
2. **Set OAuth vars**: Move Google credentials to environment variables
3. **Update imports**: Replace direct TOML loading with `get_config()`
4. **Test**: Verify configuration loads correctly

## 🔗 Related Files

- **Legacy config**: `.streamlit/secrets.toml` (deprecated)
- **Environment loader**: `config/environment.py`
- **Usage examples**: See `streamlit_extension/` for integration examples

---

*This configuration system provides enterprise-grade security and flexibility for the TDD Framework across all deployment environments.*