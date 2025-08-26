# 🤖 CLAUDE.md - Testing Framework

**Module:** tests/  
**Purpose:** Streamlined test suite with 650+ focused tests across production categories  
**Architecture:** Multi-layered testing strategy (unit, integration, performance, security, load)  
**Last Updated:** 2025-08-25 - Test Suite Cleanup Complete

---

## 🧪 **Testing Framework Overview**

Enterprise-grade testing system featuring:
- **650+ Production Tests** - Streamlined and focused on active functionality
- **Multi-Category Testing**: Unit, integration, performance, security, load testing
- **Comprehensive Coverage**: 98%+ average code coverage maintained
- **CI/CD Integration**: Automated testing pipeline with pytest
- **Production Certification**: Full system validation before deployment
- **Clean Architecture**: Obsolete development artifacts eliminated (Aug 2025)

---

## 🏗️ **Test Architecture**

### **Directory Structure (Domain-Organized)**
```
tests/
├── conftest.py                 # 🔧 Test configuration and fixtures
├── cache_performance/          # 🚀 Cache, Rate Limiting & Performance
├── security/                   # 🔒 Security, GDPR & Compliance
├── database/                   # 🗄️ Database, Transactions & Migrations
├── product_vision/             # 🎯 Product Vision, Wizard & AI
├── ui_navigation/              # 🖥️ UI Components & Navigation
├── api_endpoints/              # 🌐 API, Endpoints & JSON Handlers
├── business_logic/             # 💼 Business Logic & Domain Rules
├── infrastructure/             # 🔧 Infrastructure & System Config
├── integration/                # 🔄 Cross-System Integration Tests
├── unit/                       # 🧪 Unit Tests
├── performance/                # ⚡ Performance & Stress Tests
├── load_testing/               # 📊 Load & Concurrent User Tests
├── migration/                  # 🔀 Data Migration Tests (Active)
├── models/                     # 📊 ORM and Data Model Tests
├── repos/                      # 🗂️ Repository Pattern Tests
└── scripts/                    # 📝 System Validation Scripts
```

### **⚡ Recent Cleanup (August 2025)**
**Eliminated Obsolete Categories:**
- `optimization/` - Intelligent audit system development artifacts (REMOVED)
- `test_agno_tools/` - Agno integration development tests (REMOVED)
- Obsolete integration tests for completed migration phases (CLEANED)

### **Test Categories**

1. **Unit Tests**: Individual component testing (40+ files)
2. **Integration Tests**: Cross-module functionality testing
3. **Performance Tests**: Speed and efficiency validation
4. **Security Tests**: Vulnerability and attack scenario testing
5. **Load Tests**: Multi-user and stress testing

---

## 🧪 **Unit Testing Framework**

### **Core Component Tests**

#### **Duration System Tests**
```bash
# Duration calculation tests
tests/test_duration_calculator.py     # Core calculations (56 tests)
tests/test_duration_formatter.py      # Formatting logic (71 tests)
tests/test_business_calendar.py       # Business day calculations (32 tests)
tests/test_json_handler.py           # JSON operations (48 tests)

# Run duration system tests
pytest tests/test_duration_*.py -v
```

#### **Security Tests**
```bash
# Security validation tests
tests/test_json_security.py          # JSON attack prevention
tests/test_csrf_protection.py        # CSRF token validation
tests/test_xss_protection.py         # XSS sanitization
tests/test_security_comprehensive.py  # Complete security audit

# Run all security tests
pytest tests/test_*security*.py tests/test_csrf*.py tests/test_xss*.py -v
```

#### **Database Tests**
```bash
# Database functionality tests
tests/test_database_transactions.py   # Transaction safety
tests/test_database_cascade.py        # Foreign key enforcement
tests/test_connection_pool.py         # Connection pool management
tests/test_database_manager_*.py      # DatabaseManager functionality

# Run database tests
pytest tests/test_database*.py tests/test_connection*.py -v
```

#### **Cache & Performance Tests**
```bash
# Cache system tests
tests/test_cache_interrupt_fix.py     # Interrupt safety (19 tests)
tests/test_cache_lru_fix.py          # LRU cache optimization
tests/test_cache_security.py         # Cache security validation
tests/test_redis_cache.py            # Redis integration

# Run cache tests
pytest tests/test_cache*.py tests/test_redis*.py -v
```

### **Configuration & Infrastructure Tests**
```bash
# System configuration tests
tests/test_environment_config.py      # Multi-environment setup
tests/test_constants_system.py       # Constants and enums

# Component & UI tests
tests/test_form_components_*.py      # Form component testing
tests/test_kanban_functionality.py   # Kanban board testing
tests/test_dashboard_headless.py     # Dashboard testing

# Rate limiting tests
tests/test_rate_limit_headers.py     # HTTP headers validation
tests/test_rate_limit_storage_backends.py # Storage backend tests
```

---

## 🔄 **Integration Testing**

### **Cross-System Integration** (`integration/`)

#### **Cache System Integration**
```python
# tests/integration/test_cache_system.py
# Tests interaction between different caching layers
pytest tests/integration/test_cache_system.py -v
```

#### **End-to-End Workflows**
```python
# tests/integration/test_e2e_workflows.py
# Complete user journey testing
pytest tests/integration/test_e2e_workflows.py -v
```

#### **UI Component Integration**
```python
# tests/integration/test_ui_components.py
# Component interaction and data flow
pytest tests/integration/test_ui_components.py -v
```

### **Cross-Module Testing**
```python
# tests/integration/test_cross_system.py
# Tests integration between:
# - streamlit_extension + duration_system
# - Database + Cache layers
# - Authentication + Security layers
pytest tests/integration/test_cross_system.py -v
```

### **Performance Integration**
```python
# tests/integration/test_performance_integration.py
# End-to-end performance validation
pytest tests/integration/test_performance_integration.py -v
```

---

## ⚡ **Performance Testing**

### **Stress Testing** (`performance/`)

#### **System Stress Suite**
```python
# tests/performance/test_stress_suite.py
# Comprehensive system stress testing
pytest tests/performance/test_stress_suite.py --stress -v

# Key features:
# - Database connection pool stress
# - Memory usage under load
# - Concurrent operation testing
# - Resource limit validation
```


#### **Breakpoint Testing**
```python
# tests/performance/test_breakpoint_testing.py
# System limit and threshold testing
pytest tests/performance/test_breakpoint_testing.py -v

# Validates:
# - Maximum concurrent users
# - Memory usage limits
# - Database connection limits
# - Cache size thresholds
```

---

## 📊 **Load Testing Framework**

### **Load Testing Structure** (`load_testing/`)

#### **Concurrent User Testing**
```python
# tests/load_testing/test_load_concurrent.py
# Multi-user concurrent access testing
pytest tests/load_testing/test_load_concurrent.py -v

# Simulates:
# - 10-100 concurrent users
# - Simultaneous database operations
# - Authentication load
# - Session management under load
```

#### **CRUD Operations Load**
```python
# tests/load_testing/test_load_crud.py
# High-volume CRUD operation testing
pytest tests/load_testing/test_load_crud.py -v

# Tests:
# - Client/Project creation load
# - Bulk epic/task operations
# - Database write performance
# - Transaction throughput
```

#### **Endurance Testing**
```python
# tests/load_testing/test_load_endurance.py
# Long-duration stability testing
pytest tests/load_testing/test_load_endurance.py -v

# Validates:
# - 24-hour stability
# - Memory leak detection
# - Connection pool stability
# - Cache performance over time
```

#### **Stress Testing**
```python
# tests/load_testing/test_load_stress.py
# System breaking point testing
pytest tests/load_testing/test_load_stress.py -v

# Identifies:
# - Maximum user capacity
# - Resource exhaustion points
# - Graceful degradation
# - Recovery procedures
```

### **Load Test Scenarios** (`load_testing/scenarios/`)
```python
# Predefined load test scenarios:
# - Normal usage patterns
# - Peak load simulation  
# - Burst traffic handling
# - Sustained high load
```

---

## 🛡️ **Security Testing**

### **Security Test Categories**

#### **Attack Scenario Testing**
```python
# tests/test_attack_scenarios.py
# Comprehensive attack simulation
pytest tests/test_attack_scenarios.py -v

# Covers:
# - SQL injection attempts
# - XSS attack vectors
# - CSRF bypass attempts
# - Path traversal attacks
# - DoS attack simulation
```

#### **CSRF Protection Testing**
```python
# tests/test_csrf_protection.py
# CSRF token validation testing
pytest tests/test_csrf_protection.py -v

# Validates:
# - Token generation
# - Token validation
# - Token expiration
# - Replay attack prevention
```

#### **XSS Protection Testing**
```python
# tests/test_xss_protection.py
# XSS sanitization testing
pytest tests/test_xss_protection.py -v

# Tests:
# - Script tag filtering
# - Event handler sanitization
# - URL validation
# - Content encoding
```

#### **Comprehensive Security Audit**
```python
# tests/test_security_comprehensive.py
# Complete security validation
pytest tests/test_security_comprehensive.py -v

# Includes:
# - Authentication security
# - Authorization checks
# - Input validation
# - Output encoding
# - Session security
```

### **Security Test Scenarios** (`security_scenarios/`)

#### **CSRF Attack Scenarios**
```python
# security_scenarios/csrf_scenarios.py
# CSRF attack patterns and payloads
# Used by security tests for validation
```

#### **XSS Attack Payloads**
```python
# security_scenarios/xss_payloads.py
# Comprehensive XSS payload collection
# Tests against modern XSS vectors
```

---

## 🔧 **Test Configuration & Fixtures**

### **Pytest Configuration** (`conftest.py`)

#### **Test Fixtures**
```python
# Core test fixtures available across all tests:

@pytest.fixture(scope="session")
def test_data_dir():
    # Temporary directory for test data

@pytest.fixture(scope="function") 
def temp_db():
    # Temporary SQLite database with test schema

@pytest.fixture
def sample_epic_data():
    # Sample epic data for testing

@pytest.fixture
def sample_task_data():
    # Sample task data for testing

@pytest.fixture
def mock_database_manager():
    # Mock DatabaseManager with test data

@pytest.fixture
def mock_streamlit():
    # Mock Streamlit components for UI testing

@pytest.fixture
def analytics_test_data():
    # Comprehensive analytics test data
```

#### **Test Data Factory**
```python
# TestDataFactory for creating test objects:
TestDataFactory.create_epic(id=1, name="Test Epic")
TestDataFactory.create_task(id=1, epic_id=1, title="Test Task")
TestDataFactory.create_timer_session(id=1, focus_rating=8)
```

### **Pytest Markers**
```python
# Custom test markers for organization:
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests  
@pytest.mark.ui            # UI component tests
@pytest.mark.cache         # Cache system tests
@pytest.mark.slow          # Slow-running tests
@pytest.mark.requires_streamlit  # Streamlit-dependent tests
```

---

## 🚀 **Test Execution Workflows**

### **Development Testing**

#### **Quick Smoke Tests** (< 30 seconds)
```bash
# Basic import and configuration tests
python -c "import streamlit_extension; print('✅ Import OK')"
python -c "import duration_system; print('✅ Duration System OK')"
```

#### **Component Tests** (< 2 minutes)
```bash
# Test specific components
pytest tests/test_duration_*.py -v
pytest tests/test_database_*.py -v
pytest tests/test_security_*.py -v
```

#### **Security Validation** (< 5 minutes)
```bash
# Complete security test suite
pytest tests/test_*security*.py tests/test_csrf*.py tests/test_xss*.py -v
```

#### **Full Unit Test Suite** (< 8 minutes)
```bash
# All unit tests with coverage
pytest tests/ --ignore=tests/integration --ignore=tests/performance --ignore=tests/load_testing --cov --tb=short
```

### **Integration Testing**

#### **Cross-System Integration** (< 10 minutes)
```bash
# Integration test suite
pytest tests/integration/ -v
```

#### **Performance Validation** (< 15 minutes)
```bash
# Performance test suite
pytest tests/performance/ -v
```

#### **Load Testing** (< 30 minutes)
```bash
# Load test suite (extended duration)
pytest tests/load_testing/ -v --timeout=1800
```

### **Production Certification**

#### **Complete Test Suite** (< 20 minutes)
```bash
# Full test suite with coverage
pytest tests/ --cov=streamlit_extension --cov=duration_system --cov-report=html --tb=short
```

#### **System Validation** (< 15 minutes)
```bash
# Production certification
python comprehensive_integrity_test.py
```

#### **Stress Testing** (Variable duration)
```bash
# Stress test with custom parameters
pytest tests/performance/test_stress_suite.py --stress --duration=1800 -v
```

---

## 📊 **Test Metrics & Coverage**

### **Coverage Targets**
- **Unit Tests**: 95%+ coverage per module
- **Integration Tests**: 90%+ cross-module coverage
- **Security Tests**: 100% attack vector coverage
- **Performance Tests**: Key operation coverage

### **Test Categories Breakdown** *(Post-Cleanup Aug 2025)*
- **Unit Tests**: 650+ focused tests across active modules
- **Duration System Tests**: 175+ tests (98%+ coverage) - MAINTAINED
- **Security Tests**: 80+ tests (including rate limiting) - MAINTAINED
- **Database Tests**: 85+ tests (96% coverage) - MAINTAINED
- **UI Component Tests**: 60+ tests (92% coverage) - MAINTAINED
- **Integration Tests**: 25+ core integration tests - STREAMLINED
- **Performance Tests**: 10+ tests (key operations) - MAINTAINED
- **Load Tests**: 15+ tests (scalability validation) - MAINTAINED
- **Cache Performance**: 47+ tests verified passing - MAINTAINED

### **🧹 Eliminated Obsolete Tests** *(Aug 2025 Cleanup)*
- **Intelligent Audit System Tests**: ~150+ development artifacts removed
  - `optimization/` directory with god code test files
  - `test_agno_tools/` directory with development utilities
  - Integration tests for completed audit phases
- **Migration Development Tests**: Obsolete validation tests removed
  - Phase-specific migration validation artifacts  
  - Completed system integration tests
- **Duplicate Test Files**: Empty/minimal duplicates eliminated
  - Consolidated product vision controller tests
  - Removed placeholder test stubs

### **Quality Gates**
```bash
# Automated quality checks:
pytest tests/ --cov --cov-fail-under=95     # Coverage threshold
pytest tests/ --tb=short | grep "failed"    # No failures
pytest tests/test_*security*.py --tb=short  # Security validation
```

---

## 🔍 **Test Development Guidelines**

### **Writing New Tests**

#### **Unit Test Pattern**
```python
# tests/test_new_feature.py
import pytest
from unittest.mock import Mock, patch

class TestNewFeature:
    """Test suite for new feature."""
    
    def test_basic_functionality(self, temp_db):
        """Test basic feature functionality."""
        # Arrange
        test_data = {"key": "value"}
        
        # Act
        result = new_feature.process(test_data)
        
        # Assert
        assert result is not None
        assert result["status"] == "success"
    
    def test_error_handling(self):
        """Test feature error handling."""
        with pytest.raises(ValueError):
            new_feature.process(invalid_data)
    
    @pytest.mark.slow
    def test_performance(self):
        """Test feature performance."""
        import time
        start = time.time()
        new_feature.process(large_dataset)
        duration = time.time() - start
        assert duration < 1.0  # Performance threshold
```

#### **Integration Test Pattern**
```python
# tests/integration/test_new_integration.py
import pytest

class TestNewIntegration:
    """Integration tests for new feature."""
    
    def test_cross_module_integration(self, mock_database_manager):
        """Test integration between modules."""
        # Test complete workflow
        result = workflow.execute_complete_process()
        assert result["success"] == True
    
    def test_ui_integration(self, mock_streamlit):
        """Test UI component integration."""
        # Test UI components work together
        page.render_complete_interface()
        mock_streamlit.markdown.assert_called()
```

#### **Security Test Pattern**
```python
# tests/test_new_security.py
import pytest
from security_scenarios.attack_payloads import XSS_PAYLOADS

class TestNewSecurity:
    """Security tests for new feature."""
    
    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_protection(self, payload):
        """Test XSS protection against various payloads."""
        result = new_feature.sanitize_input(payload)
        assert "<script>" not in result
        assert "javascript:" not in result
    
    def test_csrf_protection(self):
        """Test CSRF protection."""
        token = security.generate_csrf_token("form_id")
        assert security.validate_csrf_token("form_id", token)
        assert not security.validate_csrf_token("form_id", "invalid")
```

### **Test Organization Standards**

#### **File Naming Convention**
- `test_*.py` - Unit tests for specific modules
- `test_*_integration.py` - Integration tests
- `test_*_security.py` - Security-focused tests
- `test_*_performance.py` - Performance tests

#### **Test Class Organization**
```python
class TestFeatureName:
    """Test suite for FeatureName."""
    
    def test_basic_functionality(self):
        """Test basic feature operation."""
        pass
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        pass
    
    def test_error_handling(self):
        """Test error conditions and exceptions."""
        pass
    
    def test_integration(self):
        """Test integration with other components."""
        pass
    
    @pytest.mark.slow
    def test_performance(self):
        """Test performance characteristics."""
        pass
```

### **Test Data Management**

#### **Using Test Fixtures**
```python
def test_with_database(temp_db, sample_epic_data):
    """Test using database fixtures."""
    # temp_db provides clean database
    # sample_epic_data provides test data
    pass

def test_with_factory(test_data_factory):
    """Test using data factory."""
    epic = test_data_factory.create_epic(name="Custom Epic")
    task = test_data_factory.create_task(epic_id=epic["id"])
```

#### **Mock Configuration**
```python
def test_with_mocks(mock_database_manager, mock_streamlit):
    """Test with pre-configured mocks."""
    # Mocks are pre-configured in conftest.py
    # Use directly without additional setup
    pass
```

---

## 🚨 **Troubleshooting Tests**

### **Common Test Issues**

#### **Database Lock Issues**
```bash
# Clean up database locks
rm -f *.db-wal *.db-shm
pytest tests/test_database_*.py -v
```

#### **Test Timeout Issues**
```bash
# Run with extended timeout
pytest tests/performance/ --timeout=300 -v
```

#### **Memory Issues in Load Tests**
```bash
# Run load tests with memory monitoring
pytest tests/load_testing/ -v --maxfail=1
```

#### **Streamlit Import Issues**
```bash
# Run tests without Streamlit dependency
pytest tests/ -m "not requires_streamlit" -v
```

### **Test Debugging**

#### **Verbose Output**
```bash
# Maximum verbosity
pytest tests/test_specific.py -vvv --tb=long

# Show local variables in traceback
pytest tests/test_specific.py --tb=auto --showlocals
```

#### **Test Coverage Analysis**
```bash
# Detailed coverage report
pytest tests/ --cov --cov-report=html --cov-report=term-missing
# View: htmlcov/index.html
```

#### **Performance Debugging**
```bash
# Profile test execution
pytest tests/ --profile --profile-svg
```

---

## 🔗 **Integration with Development Workflow**

### **TDD Workflow Integration**
```bash
# 1. Write failing test
pytest tests/test_new_feature.py::TestNewFeature::test_new_functionality -v

# 2. Implement feature (minimal)
# 3. Run test until green
pytest tests/test_new_feature.py::TestNewFeature::test_new_functionality -v

# 4. Refactor while keeping tests green
pytest tests/test_new_feature.py -v
```

### **Pre-Commit Testing**
```bash
# Quick validation before commit
pytest tests/ --maxfail=5 --tb=short

# Security validation
pytest tests/test_*security*.py -v

# Performance regression check
pytest tests/performance/test_query_optimization.py -v
```

### **CI/CD Integration**
```bash
# Pipeline stages:
# 1. Unit tests (< 5 min)
pytest tests/ --ignore=tests/integration --ignore=tests/performance

# 2. Integration tests (< 10 min) 
pytest tests/integration/ -v

# 3. Security tests (< 5 min)
pytest tests/test_*security*.py -v

# 4. Performance validation (< 15 min)
pytest tests/performance/ -v

# 5. Production certification (< 20 min)
python comprehensive_integrity_test.py
```

---

## 📋 **Testing Checklist**

### **Before Deployment**
- [ ] All unit tests passing (1,300+ tests)
- [ ] Integration tests passing (cross-module functionality)
- [ ] Security tests passing (vulnerability protection)
- [ ] Performance tests within thresholds
- [ ] Load tests validate capacity
- [ ] Coverage above 95% threshold
- [ ] Production certification complete

### **Feature Development**
- [ ] Unit tests written (TDD approach)
- [ ] Integration tests for cross-module features
- [ ] Security tests for user input handling
- [ ] Performance tests for critical paths
- [ ] Error handling tests
- [ ] Documentation updated

### **Bug Fixes**
- [ ] Reproduction test written
- [ ] Fix implemented and tested
- [ ] Regression tests added
- [ ] Related functionality verified
- [ ] Security implications reviewed

---

## 🔗 **See Also - Related Documentation**

**Main Project Documentation:**
- **📜 [Root CLAUDE.md](../CLAUDE.md)** - Complete system overview, quick start, architecture
- **📊 [Project README](../README.md)** - Features, installation, testing commands

**Module Testing Integration:**
- **📱 [Streamlit Extension](../streamlit_extension/CLAUDE.md)** - UI component testing, authentication tests
- **⏱️ [Duration System](../duration_system/CLAUDE.md)** - Security testing, performance validation
- **🔧 [Scripts](../scripts/CLAUDE.md)** - Analysis tools, maintenance scripts, system validation

**Operations & Quality:**
- **⚙️ [Config](../config/CLAUDE.md)** - Environment setup, testing configurations
- **📊 [Monitoring](../monitoring/CLAUDE.md)** - Performance tracking, health monitoring
- **🔄 [Migration](../migration/CLAUDE.md)** - Data migration testing, schema validation

---

*This testing framework ensures enterprise-grade quality with comprehensive coverage across all system components, providing confidence for production deployment and ongoing development.*