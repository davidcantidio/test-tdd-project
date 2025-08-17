# 🧭 TDD Framework - Navigation Guide

> **Quick orientation for developers and AI assistants**

**New here?** This guide gets you from zero to productive in **< 5 minutes**.

---

## 🚀 **Quick Start (30 seconds)**

```bash
# 1. Launch the application
streamlit run streamlit_extension/streamlit_app.py

# 2. Open browser
# http://localhost:8501

# 3. Login with default credentials (development mode)
# Create account or use existing session
```

**✅ Success indicators:**
- Login page appears  
- Authentication system active
- Dashboard loads with navigation sidebar

---

## 🎯 **I Want To...**

### **🔍 Understand the Project**
- **Project Overview**: [README.md](README.md) - What this framework does
- **System Status**: [STATUS.md](STATUS.md) - Current health and metrics
- **Component Index**: [INDEX.md](INDEX.md) - What's inside each directory

### **🏗️ Start Developing**
- **App Architecture**: [streamlit_extension/CLAUDE.md](streamlit_extension/CLAUDE.md) - Streamlit app patterns & security
- **Core Systems**: [duration_system/CLAUDE.md](duration_system/CLAUDE.md) - Utilities & security stack
- **Configuration**: [config/CLAUDE.md](config/CLAUDE.md) - Multi-environment configuration
- **Development Guide**: [docs/development/](docs/development/) - Setup and practices

### **🔧 System Operations**
- **Testing Framework**: [tests/CLAUDE.md](tests/CLAUDE.md) - 525+ tests across all categories
- **Data Migration**: [migration/CLAUDE.md](migration/CLAUDE.md) - Bidirectional sync & schema evolution
- **Utility Scripts**: [scripts/CLAUDE.md](scripts/CLAUDE.md) - 80+ maintenance & analysis tools
- **Monitoring Stack**: [monitoring/CLAUDE.md](monitoring/CLAUDE.md) - Observability & alerting

### **🐛 Fix Issues**
- **Common Problems**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Quick solutions
- **System Health**: [STATUS.md](STATUS.md) - Check component status
- **Debug Commands**: [INDEX.md#debugging](INDEX.md#debugging) - Diagnostic tools

### **🧪 Run Tests**
- **All Tests**: `python -m pytest tests/ -v`
- **Security Tests**: `python -m pytest tests/test_*security*.py -v`
- **Performance Tests**: `python -m pytest tests/performance/ -v`
- **Integration Tests**: `python -m pytest tests/integration/ -v`

### **📊 Check Status**
- **Live Dashboard**: [STATUS.md](STATUS.md) - Real-time metrics
- **System Health**: `python scripts/maintenance/database_maintenance.py health`
- **Test Results**: `python comprehensive_integrity_test.py`

---

## 🗺️ **Project Map**

### **📁 Essential Directories**

| Directory | Purpose | Documentation | Quick Access |
|-----------|---------|---------------|--------------|
| `streamlit_extension/` | 📱 Main application | [CLAUDE.md](streamlit_extension/CLAUDE.md) | Enterprise app patterns |
| `duration_system/` | ⏱️ Core utilities | [CLAUDE.md](duration_system/CLAUDE.md) | Security & calculations |
| `tests/` | 🧪 Test suite | [CLAUDE.md](tests/CLAUDE.md) | 525+ comprehensive tests |
| `migration/` | 🔄 Data migration | [CLAUDE.md](migration/CLAUDE.md) | Bidirectional sync system |
| `scripts/` | 🔧 Utility scripts | [CLAUDE.md](scripts/CLAUDE.md) | 80+ maintenance tools |
| `monitoring/` | 📊 Observability | [CLAUDE.md](monitoring/CLAUDE.md) | Metrics & alerting |
| `config/` | ⚙️ Configuration | [CLAUDE.md](config/CLAUDE.md) | Multi-environment setup |
| `docs/` | 📚 Documentation | [README.md](docs/README.md) | User guides & setup |

### **📋 Key Files**

| File | Purpose | When to use |
|------|---------|-------------|
| **[STATUS.md](STATUS.md)** | System dashboard | Check health & metrics |
| **[README.md](README.md)** | Project overview | Understand what this is |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Problem solutions | When things break |
| **[CLAUDE.md](CLAUDE.md)** | Technical coordination | AI assistant guidance |
| **[INDEX.md](INDEX.md)** | Component inventory | Find specific tools |

---

## 🛠️ **Development Workflows**

### **🆕 Adding New Features**

1. **Understand Architecture**:
   ```bash
   # Read module documentation
   cat streamlit_extension/CLAUDE.md
   cat duration_system/CLAUDE.md
   ```

2. **Choose Appropriate Module**:
   - **UI Features** → `streamlit_extension/pages/`
   - **Business Logic** → `streamlit_extension/services/`
   - **Data Processing** → `duration_system/`
   - **Configuration** → `config/`

3. **Follow Security Patterns**:
   - All pages need `@require_auth()` decorator
   - All forms need CSRF protection
   - All inputs need XSS sanitization
   - See [streamlit_extension/CLAUDE.md](streamlit_extension/CLAUDE.md#security)

4. **Write Tests First** (TDD):
   ```bash
   # Create test file
   touch tests/test_new_feature.py
   
   # Run tests (should fail initially)
   pytest tests/test_new_feature.py -v
   
   # Implement feature until tests pass
   ```

### **🔧 Fixing Bugs**

1. **Check System Status**:
   ```bash
   # Overall health
   python comprehensive_integrity_test.py
   
   # Specific component
   python scripts/maintenance/database_maintenance.py health
   ```

2. **Find Root Cause**:
   - Check [STATUS.md](STATUS.md) for known issues
   - Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common problems
   - Run relevant test suite

3. **Fix with Tests**:
   ```bash
   # Create reproduction test
   pytest tests/test_specific_issue.py -v
   
   # Fix issue
   # Verify fix
   pytest tests/test_specific_issue.py -v
   ```

### **🧪 Testing Strategy**

```bash
# Quick smoke test (< 30s)
python -c "import streamlit_extension; print('✅ Import OK')"

# Component tests (< 2 min)  
pytest tests/test_duration_*.py -v

# Security validation (< 5 min)
pytest tests/test_*security*.py -v

# Full test suite (< 10 min)
pytest tests/ --cov --tb=short

# Production certification (< 15 min)
python comprehensive_integrity_test.py
```

---

## 📊 **Monitoring & Operations**

### **🔍 Health Checks**

```bash
# System status dashboard
cat STATUS.md

# Database health
python scripts/maintenance/database_maintenance.py health

# Application health  
curl http://localhost:8501/health  # (if health endpoint is active)

# Test suite health
pytest tests/ --tb=line | grep "failed\|error"
```

### **🚨 Emergency Procedures**

```bash
# System not responding
pkill -f streamlit
streamlit run streamlit_extension/streamlit_app.py

# Database locked
rm -f *.db-wal *.db-shm
python scripts/maintenance/database_maintenance.py health

# Tests hanging
timeout 30 pytest tests/test_connection_pool.py

# Complete reset (keeps data)
rm -rf .streamlit/ 
streamlit cache clear
streamlit run streamlit_extension/streamlit_app.py
```

### **📈 Performance Monitoring**

```bash
# Database performance
python scripts/maintenance/benchmark_database.py

# Memory usage
python scripts/testing/performance_demo.py

# Load testing
pytest tests/performance/test_stress_suite.py --stress

# Connection pool status
python scripts/testing/test_connection_pool_debug.py
```

---

## 🎓 **Learning Path**

### **👨‍💻 For New Developers**

1. **Week 1 - Understanding**:
   - Read [README.md](README.md) and [STATUS.md](STATUS.md)
   - Launch application and explore UI
   - Run test suite and understand coverage

2. **Week 2 - Architecture**:
   - Study [streamlit_extension/CLAUDE.md](streamlit_extension/CLAUDE.md)
   - Understand service layer and security patterns
   - Review [duration_system/CLAUDE.md](duration_system/CLAUDE.md)

3. **Week 3 - Contributing**:
   - Fix a small bug using TDD workflow
   - Add a minor feature following security patterns
   - Write tests and documentation

### **🤖 For AI Assistants**

1. **Context Loading**:
   - Read [STATUS.md](STATUS.md) for current state
   - Check [CLAUDE.md](CLAUDE.md) for development guidelines
   - Review module-specific CLAUDEs for technical details:
     - [streamlit_extension/CLAUDE.md](streamlit_extension/CLAUDE.md) - App architecture & security
     - [duration_system/CLAUDE.md](duration_system/CLAUDE.md) - Core utilities & security
     - [tests/CLAUDE.md](tests/CLAUDE.md) - Testing framework & patterns
     - [migration/CLAUDE.md](migration/CLAUDE.md) - Data migration strategies
     - [scripts/CLAUDE.md](scripts/CLAUDE.md) - Utility tools & maintenance
     - [monitoring/CLAUDE.md](monitoring/CLAUDE.md) - Observability stack
     - [config/CLAUDE.md](config/CLAUDE.md) - Configuration architecture

2. **Problem Solving**:
   - Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for known solutions
   - Use [INDEX.md](INDEX.md) to locate relevant tools
   - Consult appropriate CLAUDE.md for module-specific patterns
   - Follow security patterns from security documentation

3. **Development**:
   - Use Codex for mechanical tasks (imports, patterns, refactoring)
   - Apply manual work for architecture and complex logic
   - Reference appropriate CLAUDE.md for development patterns
   - Always verify with comprehensive test suite (see [tests/CLAUDE.md](tests/CLAUDE.md))

---

## 🔗 **Quick Reference**

### **🚀 Essential Commands**
```bash
# Start development
streamlit run streamlit_extension/streamlit_app.py

# Run tests  
pytest tests/ -v

# Check health
python comprehensive_integrity_test.py

# Clean restart
rm -rf .streamlit/ && streamlit cache clear
```

### **📞 When You Need Help**

| Problem Type | Solution |
|--------------|----------|
| **Can't start app** | Check [TROUBLESHOOTING.md#application](TROUBLESHOOTING.md#application) |
| **Tests failing** | Check [tests/CLAUDE.md](tests/CLAUDE.md) for test patterns & troubleshooting |
| **Need architecture info** | Read appropriate CLAUDE.md: [app](streamlit_extension/CLAUDE.md), [core](duration_system/CLAUDE.md), [config](config/CLAUDE.md) |
| **Security questions** | Check [streamlit_extension/CLAUDE.md#security](streamlit_extension/CLAUDE.md#security) |
| **Migration issues** | See [migration/CLAUDE.md](migration/CLAUDE.md) for data sync & schema evolution |
| **Monitoring setup** | Follow [monitoring/CLAUDE.md](monitoring/CLAUDE.md) for observability stack |
| **Performance issues** | Use [scripts/CLAUDE.md](scripts/CLAUDE.md) diagnostic tools |

### **📋 Documentation Hierarchy**

1. **[STATUS.md](STATUS.md)** ← Start here for system overview
2. **[README.md](README.md)** ← Project introduction and setup  
3. **[NAVIGATION.md](NAVIGATION.md)** ← This guide (you are here)
4. **[INDEX.md](INDEX.md)** ← Component inventory and tools
5. **Module CLAUDEs** ← Technical implementation details
6. **[docs/](docs/)** ← Comprehensive user guides

---

**🎯 Goal: Zero confusion, maximum productivity**  
**🚀 Next: Check [STATUS.md](STATUS.md) for system health**  
**🔧 Need tools? See [INDEX.md](INDEX.md) for component inventory**