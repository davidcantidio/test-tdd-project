# ⚙️ CODEX PROMPT H: Environment Configuration System

## 🎯 **OBJETIVO**
Implementar sistema completo de configuração de ambientes conforme gap do report.md: "Separate environment configs for dev/staging/prod" e "Store secrets in vault or environment variables".

## 📁 **ARQUIVOS ALVO (ISOLADOS - SEM INTERSEÇÃO)**
```
streamlit_extension/config/environment.py          # Sistema de ambientes
streamlit_extension/config/secrets_manager.py      # Gerenciador de secrets
streamlit_extension/config/feature_flags.py        # Sistema de feature flags
config/environments/                               # Configurações por ambiente
config/environments/development.yaml               # Config de desenvolvimento
config/environments/staging.yaml                   # Config de staging  
config/environments/production.yaml                # Config de produção
config/environments/testing.yaml                   # Config de testes
tests/test_environment_config.py                   # Testes do sistema
```

## 📋 **ESPECIFICAÇÕES TÉCNICAS**

### **1. streamlit_extension/config/environment.py**
```python
# EnvironmentManager class:
# - load_environment_config()
# - get_current_environment()
# - validate_config()
# - merge_configs()

# Environment enum:
# - DEVELOPMENT
# - STAGING  
# - PRODUCTION
# - TESTING

# ConfigLoader class:
# - load_yaml_config()
# - validate_schema()
# - apply_environment_overrides()
```

### **2. streamlit_extension/config/secrets_manager.py**
```python
# SecretsManager class:
# - load_from_env_vars()
# - load_from_vault()
# - get_secret()
# - rotate_secrets()
# - validate_secrets()

# SecretType enum:
# - DATABASE_URL
# - API_KEYS
# - ENCRYPTION_KEYS
# - OAUTH_SECRETS

# VaultIntegration class:
# - connect_to_vault()
# - retrieve_secrets()
# - cache_secrets()
```

### **3. streamlit_extension/config/feature_flags.py**
```python
# FeatureFlagManager class:
# - is_enabled()
# - get_flag_value()
# - refresh_flags()
# - override_flag()

# FeatureFlag enum:
# - NEW_CLIENT_FORM
# - ADVANCED_ANALYTICS
# - BETA_FEATURES
# - MAINTENANCE_MODE
```

### **4. config/environments/development.yaml**
```yaml
# Configuração para desenvolvimento:
# - Database: local SQLite
# - Debug: true
# - Logging: DEBUG level
# - Cache: disabled
# - Rate limiting: disabled
```

### **5. config/environments/production.yaml**
```yaml
# Configuração para produção:
# - Database: production URL from env
# - Debug: false
# - Logging: INFO level
# - Cache: Redis
# - Rate limiting: strict
# - Health checks: enabled
```

## 🧪 **CASOS DE TESTE OBRIGATÓRIOS**

### **Environment Loading:**
```python
def test_load_development_config():
    # Carregamento de config de desenvolvimento
    
def test_load_production_config():
    # Carregamento de config de produção
    
def test_environment_detection():
    # Detecção automática de ambiente
    
def test_config_validation():
    # Validação de schema de configuração
```

### **Secrets Management:**
```python
def test_load_secrets_from_env():
    # Carregamento de secrets de env vars
    
def test_secrets_validation():
    # Validação de secrets obrigatórios
    
def test_secrets_caching():
    # Cache de secrets em memória
    
def test_secrets_rotation():
    # Rotação de secrets
```

### **Feature Flags:**
```python
def test_feature_flag_enabled():
    # Teste de feature flag habilitada
    
def test_feature_flag_disabled():
    # Teste de feature flag desabilitada
    
def test_feature_flag_override():
    # Override de feature flag
    
def test_feature_flag_refresh():
    # Refresh de feature flags
```

## 🔧 **CONFIGURAÇÕES ESPECÍFICAS**

### **Database Configuration:**
```yaml
database:
  development:
    url: "sqlite:///framework_dev.db"
    pool_size: 5
    echo: true
  production:
    url: "${DATABASE_URL}"
    pool_size: 20
    echo: false
    ssl_mode: require
```

### **Logging Configuration:**
```yaml
logging:
  development:
    level: DEBUG
    format: detailed
    console: true
  production:
    level: INFO
    format: json
    file: "/var/log/app.log"
```

### **Security Configuration:**
```yaml
security:
  development:
    csrf_protection: false
    rate_limiting: false
  production:
    csrf_protection: true
    rate_limiting: strict
    session_timeout: 3600
```

## 🎯 **CRITÉRIOS DE SUCESSO**
1. **4 ambientes** completamente configurados (dev/staging/prod/test)
2. **Secrets management** com env vars + vault support
3. **Feature flags system** funcional
4. **Config validation** com schema checking
5. **15+ testes** cobrindo todos os cenários
6. **Zero hard-coded** values em produção

## 🔗 **INTEGRAÇÃO**
```python
# Usage example:
env_manager = EnvironmentManager()
config = env_manager.load_environment_config()
secrets = SecretsManager().load_secrets()
flags = FeatureFlagManager()

if flags.is_enabled('NEW_CLIENT_FORM'):
    # Use new form
```

## 📊 **ESTRUTURA DE CONFIGURAÇÃO**
```
config/
├── environments/
│   ├── development.yaml    # Local dev settings
│   ├── staging.yaml        # Staging environment  
│   ├── production.yaml     # Production settings
│   └── testing.yaml        # Test environment
├── schemas/
│   └── config_schema.json  # Config validation schema
└── secrets/
    └── .env.template       # Template for env vars
```

---

**🎯 RESULTADO ESPERADO:** Sistema completo de configuração de ambientes que resolve gaps de "environment configs" e "secrets management" do report.md, preparando o sistema para deployment em múltiplos ambientes.