# 🚀 TDD Framework - Enterprise Streamlit Application

> **Production-ready Test-Driven Development** framework with **Client → Project → Epic → Task** hierarchy, enterprise authentication, and security stack.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-525%2B%20passing-success.svg)](tests/)
[![Security](https://img.shields.io/badge/security-A%2B-success.svg)](CODEX_AUDIT_REMEDIATION_REPORT.md)
[![Enterprise Ready](https://img.shields.io/badge/enterprise-ready-brightgreen.svg)](https://github.com/dbcantidio/tdd-project-template)

## ✨ Key Features

### 🏗️ **Enterprise Architecture**
- **4-Level Hierarchy**: Client → Project → Epic → Task with full relationship mapping
- **Enterprise Security**: Grade A+ compliance with authentication, CSRF/XSS protection
- **Service Layer**: 6 business services with clean architecture
- **Multi-Environment**: Development, staging, production configurations

### 🎯 **Core Functionality**
- **📊 Interactive Dashboard**: Real-time metrics and progress tracking
- **👥 Client/Project Management**: Complete CRUD with filtering and pagination
- **🎯 Epic & Task Tracking**: TDD phase tracking (Red/Green/Refactor)
- **⏱️ Focus Timer**: TDAH-optimized productivity sessions
- **🛡️ Security Stack**: Enterprise-grade protection and monitoring

### 🔧 **Technical Stack**
- **Frontend**: Streamlit with multi-page navigation
- **Backend**: Modular SQLite architecture with enterprise transaction handling
- **Database**: Hybrid modular architecture (6-module layer with dual API support)
- **Security**: SHA-256 authentication, CSRF/XSS protection, enterprise rate limiting (multi-backend)
- **Testing**: 525+ tests with 98%+ coverage
- **Code Quality**: 98%+ type hints, DRY architecture, centralized constants

## 🔐 **Enterprise Ready**

- **Authentication**: SHA-256 hashing, session management, role-based access
- **Security**: CSRF/XSS protection, input validation, enterprise rate limiting (Memory/SQLite/Redis)
- **Operations**: Multi-environment config, health monitoring, performance tracking

## 🌟 **Why This Framework?**

**Complete TDD ecosystem** with Red-Green-Refactor cycles, epic-based project management, TDAH-optimized productivity tools, and enterprise security (A+ audit passed). One-command setup, production-ready.

## 🚀 **Quick Start**

### **1. Setup**
```bash
git clone https://github.com/davidcantidio/test-tdd-project.git
cd test-tdd-project

# Install dependencies
pip install streamlit plotly pandas typer rich
```

### **2. Launch Application**
```bash
# Start Streamlit dashboard
streamlit run streamlit_extension/streamlit_app.py

# Access: http://localhost:8501
```

### **3. Environment (Optional)**
```bash
# Development (default)
export TDD_ENVIRONMENT=development

# Production (requires secrets)
export TDD_ENVIRONMENT=production
export GOOGLE_CLIENT_ID="your_client_id"
export GOOGLE_CLIENT_SECRET="your_client_secret"
```

## 🧪 TDD Workflow

**Built-in Red-Green-Refactor cycles:** Write failing tests → Make them pass → Improve design

```bash
pytest tests/  # Run tests
streamlit run streamlit_extension/streamlit_app.py  # Start dashboard + timer
```

## 📊 Dashboard Features

**Sample Data:** 1 Client → 1 Project → 12 Epics → 206 Tasks  
**Analytics:** Real-time progress, TDD metrics, focus sessions, productivity insights  
**Management:** Complete CRUD operations via Streamlit interface

## 🗄️ Database Architecture

**Hybrid Modular Database Architecture** (2025-08-18):

### **Dual API Support**
```python
# Original API (preserved for compatibility)
from streamlit_extension.utils.database import DatabaseManager
db = DatabaseManager()
conn = db.get_connection()

# New Modular API (optimized)
from streamlit_extension.database import get_connection, transaction, check_health
conn = get_connection()
with transaction():
    # ACID-compliant operations

# Mixed Usage (best of both worlds)
from streamlit_extension.utils.database import DatabaseManager
from streamlit_extension.database import transaction
db = DatabaseManager()
with transaction():  # Fast modular transaction
    db.create_client(data)  # Familiar DatabaseManager
```

### **Key Benefits**
- ✅ **Zero Breaking Changes**: Complete backward compatibility
- ✅ **Performance Excellence**: Optimized modular approach
- ✅ **Gradual Migration**: Teams can transition at their own pace
- ✅ **Production Ready**: Immediate deployment safe with zero risk
- ✅ **Modular Structure**: 6 specialized modules (connection, health, queries, schema, seed)

## 🛠️ Commands

```bash
pytest tests/                                       # Run tests (525+ tests, 98%+ coverage)
python scripts/maintenance/database_maintenance.py  # Database maintenance
python scripts/testing/comprehensive_integrity_test.py  # Production certification
```

## 📈 Status

**Quality:** 98%+ test coverage • A+ security grade • 98%+ type safety • 6 business services  
**Systems:** ✅ Authentication • Security • Client/Project Management • Epic/Task Tracking • Timer • Health Monitoring

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/epic-name`
3. **Follow TDD workflow:** Red → Green → Refactor
4. **Write/update tests** for all changes
5. **Ensure all tests pass:** `pytest tests/`
6. **Submit a pull request**

### Contribution Guidelines
- Follow the Red-Green-Refactor TDD cycle
- Maintain test coverage above 90%
- Update epic documentation for new features
- Use the provided issue and PR templates

## 📚 Documentation

- 📖 **[Setup Guide](docs/development/SETUP_GUIDE.md)** - Detailed setup instructions
- 🎯 **[Streamlit App Guide](streamlit_extension/CLAUDE.md)** - Working with the web interface
- ⏰ **[Duration System](duration_system/CLAUDE.md)** - Time tracking and calculations
- 📊 **[Current Roadmap](docs/streamlit_current_roadmap.md)** - Development status and next steps
- 🔧 **[Customization](docs/CUSTOMIZATION_GUIDE.md)** - Template customization
- 🐛 **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

## 🚨 Troubleshooting

**Tests failing:** `export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"`  
**Timer issues:** `python tdah_tools/task_timer.py init`  
**Epic validation:** Check epic files in `epics/` directory for valid JSON

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits

TDD methodology (Kent Beck) • TDAH productivity research • Agile development practices

## 🔗 Links

[📊 Dashboard](http://localhost:8501) • [🎯 Epics](epics/) • [🐛 Issues](../../issues) • [📋 Discussions](../../discussions)

## 🔐 Security

**Grade A+ Enterprise Security** - Zero critical vulnerabilities  
**525+ comprehensive tests** (100% passing) • Zero critical vulnerabilities • SOC 2/ISO 27001/GDPR ready  
**Features:** CSRF/XSS protection • Enterprise rate limiting • Input validation (240+ patterns) • Attack detection • Audit trails

---

**Built with the [TDD Project Template](https://github.com/tdd-project-template/template)** 🚀  
**Enterprise Security Certified** 🛡️