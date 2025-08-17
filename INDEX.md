# 📋 TDD Framework - Component Index

> **Complete inventory of all project components, tools, and utilities**

**Quick Navigation:** [Architecture](#architecture) | [Tools](#tools) | [Tests](#tests) | [Documentation](#documentation) | [Databases](#databases)

---

## 🏗️ **Architecture**

### **🎯 Core Modules**

| Module | Location | Purpose | Documentation | Key Files |
|--------|----------|---------|---------------|-----------|
| **📱 Streamlit App** | `streamlit_extension/` | Enterprise web application | [CLAUDE.md](streamlit_extension/CLAUDE.md) | `streamlit_app.py` |
| **⏱️ Duration System** | `duration_system/` | Time calculations & security | [CLAUDE.md](duration_system/CLAUDE.md) | `duration_calculator.py` |
| **🧪 Testing Framework** | `tests/` | 525+ comprehensive tests | [CLAUDE.md](tests/CLAUDE.md) | `conftest.py` |
| **🔄 Migration System** | `migration/` | Bidirectional sync & schema evolution | [CLAUDE.md](migration/CLAUDE.md) | `bidirectional_sync.py` |
| **🔧 Utility Scripts** | `scripts/` | 80+ maintenance & analysis tools | [CLAUDE.md](scripts/CLAUDE.md) | `maintenance/`, `analysis/` |
| **📊 Monitoring Stack** | `monitoring/` | Observability & alerting | [CLAUDE.md](monitoring/CLAUDE.md) | `prometheus.yml`, `structured_logging.py` |
| **⚙️ Configuration** | `config/` | Multi-environment architecture | [CLAUDE.md](config/CLAUDE.md) | `environment.py` |

### **📁 Streamlit Application Structure**

```
streamlit_extension/
├── 🔐 auth/              # Authentication system
│   ├── auth_manager.py   # User management (SHA-256)
│   ├── middleware.py     # @require_auth() decorators
│   └── session_handler.py # Session management
├── 📄 pages/             # Multi-page application  
│   ├── clients.py        # Client management (CSRF protected)
│   ├── projects.py       # Project management
│   ├── analytics.py      # TDD analytics dashboard
│   └── timer.py          # TDAH focus timer
├── 🏢 services/          # Business logic layer
│   ├── client_service.py # Client CRUD operations
│   ├── project_service.py # Project management
│   └── service_container.py # Dependency injection
├── 🧩 components/        # Reusable UI components
│   ├── form_components.py # DRY form patterns
│   └── dashboard_widgets.py # Metrics widgets
├── 🔧 utils/             # Core utilities
│   ├── database.py       # DatabaseManager
│   ├── security.py       # CSRF/XSS protection
│   └── validators.py     # Input validation
└── 🌐 endpoints/         # Health monitoring
    └── health.py         # Kubernetes-ready probes
```

### **⏱️ Duration System Structure**

```
duration_system/
├── 📊 Core Engines
│   ├── duration_calculator.py  # Time calculations
│   ├── duration_formatter.py   # Human-readable formatting
│   └── business_calendar.py    # Brazilian holidays
├── 🔐 Security Stack
│   ├── json_security.py       # JSON validation (240+ patterns)
│   ├── cache_fix.py           # Interrupt-safe caching
│   └── database_transactions.py # Transaction safety
├── 🛡️ Data Protection
│   ├── gdpr_compliance.py     # Data protection
│   ├── secure_serialization.py # Safe pickle alternatives
│   └── log_sanitization.py    # Secure logging
└── ⚡ Performance
    ├── circuit_breaker.py     # Service protection
    └── query_builders.py      # SQL injection prevention
```

---

## 🔧 **Tools & Utilities**

### **🏠 Root-Level Tools**

| Tool | Purpose | Usage | Notes |
|------|---------|-------|-------|
| `cleanup_cache.py` | Clear cache artifacts | `python cleanup_cache.py` | Safe cleanup |
| `validate_gitignore.py` | Verify ignore patterns | `python validate_gitignore.py` | Repository health |
| `comprehensive_integrity_test.py` | Production certification | `python comprehensive_integrity_test.py` | Full system validation |

### **⚙️ Configuration Tools**

| File | Purpose | Environment | Usage |
|------|---------|-------------|-------|
| `config/environment.py` | Multi-env configuration | All | `python config/environment.py` |
| `config/environments/development.yaml` | Dev settings | Development | Auto-loaded |
| `config/environments/production.yaml` | Prod settings | Production | Requires secrets |
| `config/feature_flags.py` | Feature toggles | All | Runtime configuration |

### **🗂️ Scripts Directory**

#### **🔧 Maintenance Scripts** (`scripts/maintenance/`)
- **`database_maintenance.py`** - Database health, backup, optimization
  ```bash
  python scripts/maintenance/database_maintenance.py health
  python scripts/maintenance/database_maintenance.py backup
  ```
- **`benchmark_database.py`** - Performance benchmarking
- **`simple_benchmark.py`** - Quick performance checks

#### **🔄 Migration Scripts** (`scripts/migration/`)
- **`migrate_real_json_data.py`** - Epic data migration
- **`assign_epics_to_client_project.py`** - Hierarchy assignment
- **`migration_utility.py`** - Generic migration helpers

#### **📊 Analysis Scripts** (`scripts/analysis/`)
- **`analysis_type_hints.py`** - Type coverage analysis
- **`audit_gap_analysis.py`** - Compliance checking
- **`map_epic_task_hierarchy.py`** - Data relationship mapping

#### **🧪 Testing Scripts** (`scripts/testing/`)
- **`comprehensive_integrity_test.py`** - Full system validation
- **`test_database_integrity.py`** - Database consistency checks
- **`validate_sync_results.py`** - Data synchronization validation

#### **🔧 Setup Scripts** (`scripts/setup/`)
- **`create_framework_db.py`** - Initialize database schema
- **`create_realistic_data.py`** - Generate test data

---

## 🧪 **Testing Infrastructure**

### **📊 Test Categories**

| Category | Location | Count | Purpose |
|----------|----------|-------|---------|
| **Unit Tests** | `tests/test_*.py` | 300+ | Individual component testing |
| **Integration Tests** | `tests/integration/` | 150+ | System interaction testing |
| **Security Tests** | `tests/test_*security*.py` | 110+ | Attack protection validation |
| **Performance Tests** | `tests/performance/` | 50+ | Load, stress, endurance testing |

### **🔐 Security Test Suite**

```bash
# Core security tests
tests/test_security_comprehensive.py    # Complete security validation
tests/test_csrf_protection.py          # CSRF attack prevention  
tests/test_xss_protection.py           # XSS attack prevention
tests/test_attack_scenarios.py         # Real attack simulation
tests/test_json_security.py            # JSON input validation
tests/test_database_transactions.py    # SQL injection prevention
```

### **⚡ Performance Test Suite**

```bash
# Performance validation
tests/performance/test_stress_suite.py      # System stress testing
tests/performance/test_breakpoint_testing.py # Failure point testing  
tests/load_testing/test_load_concurrent.py   # Concurrent user simulation
tests/load_testing/test_load_endurance.py    # Long-running stability
```

### **🔧 Test Utilities**

| Utility | Purpose | Usage |
|---------|---------|-------|
| `tests/conftest.py` | Test configuration | Auto-loaded by pytest |
| `tests/security_scenarios/` | Attack payloads | Security test data |
| `pytest.ini` | Test settings | pytest configuration |

---

## 📚 **Documentation**

### **📋 Core Documentation**

| Document | Purpose | Target Audience |
|----------|---------|-----------------|
| **[STATUS.md](STATUS.md)** | System health dashboard | Operations, monitoring |
| **[NAVIGATION.md](NAVIGATION.md)** | Navigation guide | New developers, AI assistants |
| **[INDEX.md](INDEX.md)** | Component inventory | Finding specific tools |
| **[README.md](README.md)** | Project overview | First-time users |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Problem solutions | Bug fixing, debugging |

### **🔧 Technical Documentation**

| Location | Focus | Content |
|----------|-------|---------|
| `streamlit_extension/CLAUDE.md` | App architecture | Enterprise app patterns, authentication, security |
| `duration_system/CLAUDE.md` | Core utilities | Duration engine, security stack, data protection |
| `tests/CLAUDE.md` | Testing framework | 525+ tests, test patterns, validation strategies |
| `migration/CLAUDE.md` | Data migration | Bidirectional sync, schema evolution, ETL |
| `scripts/CLAUDE.md` | Utility scripts | 80+ tools for maintenance, analysis, testing |
| `monitoring/CLAUDE.md` | Observability | Prometheus, Grafana, structured logging |
| `config/CLAUDE.md` | Configuration | Multi-environment, feature flags, secrets |
| `CLAUDE.md` | Project coordination | AI guidelines, development phases |
| `docs/api/` | API documentation | Service interfaces, database schemas |
| `docs/architecture/` | System design | Overall architecture, performance |

### **📁 Documentation Structure**

```
docs/
├── 🏗️ architecture/          # System design
│   ├── overview.md           # High-level architecture
│   ├── security.md           # Security architecture  
│   └── performance.md        # Performance considerations
├── 🛠️ development/          # Developer guides
│   ├── SETUP_GUIDE.md       # Environment setup
│   ├── contributing.md       # Contribution guidelines
│   └── testing.md           # Testing strategies
├── 📚 user guides/          # User documentation
│   ├── CUSTOMIZATION.md     # Framework customization
│   └── USAGE_GUIDE.md       # Feature usage guides
└── 📁 archive/              # Historical documentation
    └── plano.md             # Complete implementation history
```

---

## 🗄️ **Databases**

### **📊 Active Databases**

| Database | Purpose | Size | Records | Status |
|----------|---------|------|---------|--------|
| **framework.db** | Main application data | ~2MB | 1→1→12→206 hierarchy | ✅ Active |
| **task_timer.db** | Timer sessions | ~49KB | 34 examples | ✅ Active |
| **performance_cache.db** | Performance metrics | ~100KB | Benchmarks | ✅ Active |
| **demo_feature_flags.db** | Feature flags demo | ~10KB | Config flags | 🔧 Demo |

### **🔄 Database Tools**

```bash
# Health checking
python scripts/maintenance/database_maintenance.py health

# Backup and restore
python scripts/maintenance/database_maintenance.py backup
python scripts/maintenance/database_maintenance.py restore

# Schema validation
python scripts/testing/test_database_integrity.py

# Performance benchmarking
python scripts/maintenance/benchmark_database.py
```

### **📋 Schema Files**

| File | Purpose | Status |
|------|---------|--------|
| `framework_schema_final.sql` | Core database schema | ✅ Current |
| `migration/migrations/*.sql` | Schema migrations | ✅ Applied |
| `migrations/*.sql` | Additional migrations | ✅ Applied |

---

## 🎯 **Quick Access Commands**

### **🚀 Application**

```bash
# Start application  
streamlit run streamlit_extension/streamlit_app.py

# Development mode
export TDD_ENVIRONMENT=development
streamlit run streamlit_extension/streamlit_app.py

# Production mode (requires secrets)
export TDD_ENVIRONMENT=production
export GOOGLE_CLIENT_ID="your_id"
export GOOGLE_CLIENT_SECRET="your_secret"
streamlit run streamlit_extension/streamlit_app.py
```

### **🧪 Testing**

```bash
# Full test suite
python -m pytest tests/ --cov --tb=short

# Quick smoke test
python -m pytest tests/test_duration_calculator.py -v

# Security validation
python -m pytest tests/test_*security*.py -v

# Performance tests
python -m pytest tests/performance/ --stress -v
```

### **🔧 Maintenance**

```bash
# System health check
python comprehensive_integrity_test.py

# Database maintenance
python scripts/maintenance/database_maintenance.py health

# Cache cleanup  
python cleanup_cache.py

# Environment validation
python config/environment.py
```

### **📊 Monitoring**

```bash
# Live metrics (if health endpoint active)
curl http://localhost:8501/health

# Database performance
python scripts/maintenance/benchmark_database.py

# Test coverage report
python -m pytest tests/ --cov --cov-report=html
```

---

## 🔍 **Debugging**

### **🚨 Common Debug Commands**

```bash
# Database issues
python scripts/testing/test_database_integrity.py
python scripts/maintenance/database_maintenance.py health

# Connection problems  
python scripts/testing/test_connection_pool_debug.py
python scripts/testing/test_simple_sync.py

# Performance issues
python scripts/maintenance/benchmark_database.py
python scripts/testing/performance_demo.py

# Security validation
python -m pytest tests/test_security_comprehensive.py -v
python duration_system/json_security.py

# Environment problems
python config/environment.py
python setup/validate_environment.py
```

### **📋 Log Locations**

| Log Type | Location | Purpose |
|----------|----------|---------|
| **Application** | `logs/application.log` | General app activity |
| **Errors** | `logs/errors.log` | Error tracking |
| **Performance** | `logs/performance.log` | Performance metrics |
| **Security** | `logs/security.log` | Security events |
| **Demo Logs** | `demo_logs/` | Demo system activities |

---

## 📦 **Dependencies**

### **🐍 Python Dependencies**

| Package | Purpose | Version | Status |
|---------|---------|---------|--------|
| **streamlit** | Web framework | Latest | ✅ Required |
| **plotly** | Data visualization | Latest | ✅ Required |
| **pandas** | Data processing | Latest | ✅ Required |
| **sqlalchemy** | Database ORM | Latest | ✅ Required |
| **pytest** | Testing framework | Latest | ✅ Dev only |

### **⚙️ Configuration Files**

| File | Purpose | Environment |
|------|---------|-------------|
| `pyproject.toml` | Python dependencies | All |
| `poetry.lock` | Dependency lockfile | All |
| `pytest.ini` | Test configuration | Development |
| `config/python/pyproject_poetry.toml` | Poetry template | Template |

---

## 🎯 **Finding What You Need**

### **🔍 Search Strategies**

1. **By Purpose**:
   - **Authentication** → `streamlit_extension/auth/`
   - **Security** → `duration_system/*_security.py`
   - **Performance** → `tests/performance/`
   - **Configuration** → `config/`

2. **By File Type**:
   - **Python modules** → `find . -name "*.py" | grep [keyword]`
   - **Configuration** → `find . -name "*.yaml" -o -name "*.toml"`
   - **Documentation** → `find . -name "*.md"`
   - **Tests** → `find tests/ -name "test_*.py"`

3. **By Component**:
   - Use this INDEX.md for organized navigation
   - Check [STATUS.md](STATUS.md) for component health
   - Review module CLAUDEs for technical details

---

**🎯 Everything you need to navigate the TDD Framework efficiently**  
**🚀 Next: Check [STATUS.md](STATUS.md) for current system health**  
**🧭 Lost? See [NAVIGATION.md](NAVIGATION.md) for guidance**