# 🤖 CLAUDE.md - Duration System Module

**Module:** duration_system/  
**Purpose:** Enterprise duration calculation and security utilities  
**Architecture:** Standalone modules for duration handling, security, and data protection  
**Last Updated:** 2025-08-16

---

## ⏱️ **Module Overview**

Comprehensive duration and security system featuring:
- **Duration Engine**: Calculation and formatting with business calendar support
- **Security Stack**: JSON validation, cache protection, transaction safety
- **Data Protection**: GDPR compliance, secure serialization, sanitization
- **Performance**: Interrupt-safe caching, optimized queries, circuit breakers

---

## 🏗️ **Module Architecture**

### **Core Components**
```
duration_system/
├── duration_calculator.py    # ⏱️ Core duration calculations
├── duration_formatter.py     # 📝 Human-readable formatting
├── business_calendar.py      # 📅 Business days + holidays
├── json_handler.py          # 📊 JSON field operations
├── json_security.py         # 🛡️ JSON validation & sanitization
├── cache_fix.py             # 🔄 Interrupt-safe LRU cache
├── database_transactions.py # 📊 Transaction safety
├── secure_serialization.py  # 🔒 Safe pickle alternatives
└── [security modules...]     # 🔐 Additional security utilities
```

### **System Categories**

1. **Duration Core**: Calculation, formatting, business logic
2. **Security Stack**: Input validation, cache protection, transaction safety
3. **Data Protection**: GDPR, encryption, secure serialization
4. **Performance**: Caching, optimization, circuit breakers

---

## ⏱️ **Duration Engine**

### **DurationCalculator** (`duration_calculator.py`)

**Purpose**: Core duration calculations with business day support

```python
from duration_system.duration_calculator import DurationCalculator

# Initialize calculator
calculator = DurationCalculator()

# Calculate duration between dates
duration_days = calculator.calculate_duration(
    start_date="2025-08-16",
    end_date="2025-08-20",
    include_weekends=True
)

# Business day calculations
business_days = calculator.calculate_business_duration(
    start_date="2025-08-16",
    end_date="2025-08-20",
    exclude_holidays=True
)

# Validate date consistency
is_valid = calculator.validate_date_range(start_date, end_date)
```

**Key Features:**
- Calendar vs business day calculations
- Holiday exclusion with Brazilian calendar
- Date consistency validation
- Performance optimized with caching

### **DurationFormatter** (`duration_formatter.py`)

**Purpose**: Human-readable duration formatting

```python
from duration_system.duration_formatter import DurationFormatter

formatter = DurationFormatter()

# Format durations
formatter.format(1)      # "1 dia"
formatter.format(7)      # "1 semana"
formatter.format(10)     # "1.5 semanas"
formatter.format(30)     # "1 mês"

# Parse duration strings
days = formatter.parse("1.5 dias")      # 1.5
days = formatter.parse("2 semanas")     # 14
```

**Features:**
- Multilingual support (Portuguese/English)
- Fractional duration support
- Bidirectional parsing (string ↔ number)
- Consistent formatting rules

### **BusinessCalendar** (`business_calendar.py`)

**Purpose**: Business day calculations with holiday support

```python
from duration_system.business_calendar import BusinessCalendar

calendar = BusinessCalendar()

# Check if date is business day
is_business = calendar.is_business_day("2025-08-16")

# Get business days in range
business_days = calendar.get_business_days_in_range(
    start_date="2025-08-01",
    end_date="2025-08-31"
)

# Add business days to date
target_date = calendar.add_business_days("2025-08-16", 5)
```

**Features:**
- Brazilian national holidays (2024-2026)
- Regional holiday configuration
- Weekend exclusion
- Performance caching for holidays

---

## 📊 **JSON & Data Handling**

### **JSONHandler** (`json_handler.py`)

**Purpose**: Safe JSON field operations with validation

```python
from duration_system.json_handler import JSONHandler

handler = JSONHandler()

# Serialize with validation
json_string = handler.serialize({
    "goals": ["Complete feature", "Write tests"],
    "definition_of_done": ["Code reviewed", "Tests passing"]
})

# Deserialize with security checks
data = handler.deserialize(json_string, expected_schema={
    "goals": list,
    "definition_of_done": list
})

# Validate JSON structure
is_valid, errors = handler.validate_structure(data, schema)
```

**Security Features:**
- Schema validation
- Type checking
- Size limits (prevents DoS)
- Circular reference detection

### **JSONSecurity** (`json_security.py`)

**Purpose**: Comprehensive JSON security validation

```python
from duration_system.json_security import JSONSecurity

security = JSONSecurity()

# Validate against attacks
is_safe, threats = security.validate_json_security(json_data)

# Sanitize dangerous content
clean_data = security.sanitize_json_content(user_input)

# Check for injection patterns
has_injection = security.detect_injection_patterns(json_string)
```

**Protection Against:**
- XSS (Script injection)
- SQL injection patterns
- Path traversal attacks
- Prototype pollution
- DoS via deep nesting/large payloads
- Binary data injection

---

## 🔐 **Security Stack**

### **CacheFix** (`cache_fix.py`)

**Purpose**: Interrupt-safe LRU cache with signal handling

```python
from duration_system.cache_fix import InterruptSafeCache

# Create interrupt-safe cache
cache = InterruptSafeCache(maxsize=1000)

@cache.cached_method
def expensive_operation(param):
    return complex_calculation(param)

# Manual cache operations
cache.put("key", value)
result = cache.get("key")
cache.clear()
```

**Features:**
- KeyboardInterrupt safety
- Thread-safe operations
- Graceful shutdown handling
- Automatic cleanup on interruption

### **DatabaseTransactions** (`database_transactions.py`)

**Purpose**: Enterprise transaction safety with connection pooling

```python
from duration_system.database_transactions import (
    TransactionalDatabaseManager,
    DatabaseConnectionPool
)

# Connection pool setup
pool = DatabaseConnectionPool(
    database_path="framework.db",
    max_connections=10,
    timeout=30
)

# Transactional operations
tx_manager = TransactionalDatabaseManager(pool)

with tx_manager.transaction() as tx:
    tx.execute("INSERT INTO clients (...) VALUES (?)", (data,))
    tx.execute("UPDATE projects SET ... WHERE id = ?", (id,))
    # Automatic commit on success, rollback on exception
```

**Features:**
- ACID transaction compliance
- Connection pooling with limits
- Deadlock detection and retry
- Isolation level control (DEFERRED, IMMEDIATE, EXCLUSIVE)
- WAL mode for concurrency

### **SecureSerialization** (`secure_serialization.py`)

**Purpose**: Safe alternatives to pickle with security restrictions

```python
from duration_system.secure_serialization import SecureUnpickler

# Safe unpickling with restrictions
unpickler = SecureUnpickler()
data = unpickler.safe_loads(pickle_data)

# JSON-based serialization (recommended)
json_data = unpickler.serialize_to_json(python_object)
python_object = unpickler.deserialize_from_json(json_data)
```

**Security Features:**
- Restricted pickle operations (blocks dangerous calls)
- File signature verification
- Size limits and timeout protection
- JSON-first approach (safer alternative)

---

## 🛡️ **Data Protection**

### **GDPR Compliance** (`gdpr_compliance.py`)

**Purpose**: Data protection and privacy compliance

```python
from duration_system.gdpr_compliance import GDPRCompliance

gdpr = GDPRCompliance()

# Data retention management
gdpr.setup_data_retention(
    retention_period_days=30,
    cleanup_schedule="daily"
)

# Personal data anonymization
anonymized_data = gdpr.anonymize_personal_data(user_data)

# Consent tracking
gdpr.record_consent(user_id, consent_type, granted=True)
```

**Compliance Features:**
- Automated data retention
- Personal data anonymization
- Consent tracking and management
- Data breach logging
- Right to erasure implementation

### **Log Sanitization** (`log_sanitization.py`)

**Purpose**: Secure logging without sensitive data exposure

```python
from duration_system.log_sanitization import LogSanitizer

sanitizer = LogSanitizer()

# Sanitize log entries
safe_message = sanitizer.sanitize_log_message(
    "User john@example.com failed login attempt"
)
# Result: "User [EMAIL] failed login attempt"

# Configure sensitive patterns
sanitizer.add_sensitive_pattern(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]')
```

**Features:**
- Email address masking
- Password/token removal
- Database path sanitization
- Custom pattern configuration

---

## ⚡ **Performance & Optimization**

### **Circuit Breakers** (`circuit_breaker.py`)

**Purpose**: Service protection against cascading failures

```python
from duration_system.circuit_breaker import CircuitBreaker

# Create circuit breaker
breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=DatabaseError
)

@breaker
def database_operation():
    return db.execute_complex_query()

# Manual control
breaker.open()      # Force circuit open
breaker.close()     # Force circuit closed
```

**Features:**
- Automatic failure detection
- Configurable thresholds and timeouts
- Multiple states (CLOSED, OPEN, HALF_OPEN)
- Metrics collection for monitoring

### **Query Builders** (`query_builders.py`)

**Purpose**: SQL injection prevention with parameterized queries

```python
from duration_system.query_builders import QueryBuilder

builder = QueryBuilder()

# Safe query construction
query = builder.select("clients") \
              .where("status", "=", "active") \
              .where("tier", "IN", ["premium", "enterprise"]) \
              .limit(50) \
              .build()

# Parameterized execution
results = builder.execute(query)
```

**Security Features:**
- 100% parameter binding (no f-strings)
- SQL injection prevention
- Query validation and sanitization
- Performance optimization with prepared statements

---

## 🔧 **Integration Patterns**

### **With Streamlit Extension**
```python
# In streamlit pages
from duration_system.duration_formatter import DurationFormatter
from duration_system.json_security import JSONSecurity

# Format durations for display
formatter = DurationFormatter()
display_duration = formatter.format(epic_duration_days)

# Validate user JSON input
security = JSONSecurity()
is_safe, threats = security.validate_json_security(user_json)
```

### **With Database Operations**
```python
# Transaction-safe database operations
from duration_system.database_transactions import TransactionalDatabaseManager

tx_manager = TransactionalDatabaseManager(db_path)
with tx_manager.transaction() as tx:
    # Multiple operations in single transaction
    client_id = tx.insert_client(client_data)
    project_id = tx.insert_project(project_data, client_id)
```

### **With Caching Systems**
```python
# Interrupt-safe caching
from duration_system.cache_fix import InterruptSafeCache

cache = InterruptSafeCache(maxsize=500)

@cache.cached_method
def calculate_epic_progress(epic_id):
    # Expensive calculation with caching
    return complex_progress_calculation(epic_id)
```

---

## 📊 **Module Metrics**

**Core Functionality:**
- **Duration Calculator**: 376 lines, 56 tests, 94.76% coverage
- **Duration Formatter**: 351 lines, 71 tests, 96.47% coverage
- **JSON Handler**: 443 lines, 48 tests, 83.43% coverage

**Security Implementation:**
- **91 Security Tests** covering all attack vectors
- **240+ Attack Patterns** detected by validation
- **Zero Critical Vulnerabilities** in all modules
- **Enterprise Grade** security compliance

**Performance Features:**
- **Interrupt-Safe Caching** with signal handling
- **Connection Pooling** with deadlock prevention
- **Circuit Breakers** for service protection
- **Query Optimization** with parameter binding

**Data Protection:**
- **GDPR Compliance** with automated retention
- **Secure Serialization** without pickle risks
- **Log Sanitization** preventing data leaks
- **JSON Security** with comprehensive validation

---

## 🚀 **Development Guidelines**

### **Security First**
- Always use parameter binding for SQL queries
- Validate all JSON input with `JSONSecurity`
- Use `SecureUnpickler` instead of raw pickle
- Implement proper error handling without information leakage

### **Performance Optimization**
- Use `InterruptSafeCache` for expensive operations
- Implement circuit breakers for external dependencies
- Use connection pooling for database operations
- Monitor cache hit rates and adjust sizes accordingly

### **Integration Standards**
- Follow established patterns for cross-module integration
- Use consistent error handling patterns
- Implement proper logging with sanitization
- Document all public APIs with usage examples

---

## 🔗 **See Also - Related Documentation**

**For Testing & Validation:**
- **🧪 Testing Framework**: [../tests/CLAUDE.md](../tests/CLAUDE.md) - Security testing, performance validation, comprehensive test coverage
- **🔧 Analysis Scripts**: [../scripts/CLAUDE.md](../scripts/CLAUDE.md) - Security audits, performance benchmarks, maintenance tools

**For Integration & Operations:**
- **📱 Streamlit Application**: [../streamlit_extension/CLAUDE.md](../streamlit_extension/CLAUDE.md) - Application architecture, service integration
- **🔄 Data Migration**: [../migration/CLAUDE.md](../migration/CLAUDE.md) - Bidirectional sync, schema evolution, data transformation
- **📊 Monitoring**: [../monitoring/CLAUDE.md](../monitoring/CLAUDE.md) - Structured logging, performance tracking, health monitoring
- **⚙️ Configuration**: [../config/CLAUDE.md](../config/CLAUDE.md) - Environment setup, security configuration, deployment

---

*This module provides enterprise-grade duration handling and security utilities with comprehensive protection against common vulnerabilities and performance optimizations.*