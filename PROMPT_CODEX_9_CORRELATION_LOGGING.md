# 📝 PROMPT_CODEX_9: CORRELATION ID LOGGING SYSTEM

## 🎯 **TASK SPECIFICATION**
**TASK**: Implement comprehensive logging system with correlation IDs for multi-user tracing
**TARGET**: Item 99 - Comprehensive logging with correlation IDs for multi-user tracing
**PRIORITY**: HIGH (Production observability and debugging)
**EFFORT**: MEDIUM (2-3 horas)
**CONFIDENCE**: MEDIUM-HIGH (80% - Logging patterns are well-established)

---

## 📋 **DETAILED REQUIREMENTS**

### **SCOPE: New Logging Infrastructure (No Conflicts)**
- `streamlit_extension/utils/correlation_logging.py` (NEW)
- `streamlit_extension/utils/log_formatter.py` (NEW)
- Integration with existing pages (minimal changes)
- Log configuration setup

### **CORRELATION LOGGING FEATURES:**

#### **1. CORRELATION ID GENERATION**
```python
# Unique request tracking across all operations
- UUID-based correlation IDs
- Session-based correlation for Streamlit
- Request lifecycle tracking
- Multi-user differentiation
```

#### **2. STRUCTURED LOGGING**
```python
# JSON-based log entries with standard fields
{
    "timestamp": "2025-08-16T10:30:00Z",
    "correlation_id": "req_abc123def456",
    "session_id": "session_xyz789",
    "user_id": "user_123",
    "operation": "create_client",
    "level": "INFO",
    "message": "Client created successfully",
    "duration_ms": 45,
    "metadata": {
        "client_id": 123,
        "ip_address": "192.168.1.100"
    }
}
```

#### **3. OPERATION TRACKING**
```python
# Track complete operation lifecycle
- Operation start/end
- Performance metrics
- Success/failure status
- Error context preservation
```

---

## 🎯 **IMPLEMENTATION STRATEGY**

### **FILE 1: streamlit_extension/utils/correlation_logging.py**
```python
"""
Correlation ID Logging System
Provides request tracking and structured logging for multi-user environments
"""

import uuid
import time
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional, Union
from contextlib import contextmanager
from functools import wraps

# Safe imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

class CorrelationIDManager:
    """Manages correlation IDs for request tracking"""
    
    def __init__(self):
        self._correlation_storage = {}
        
    def generate_correlation_id(self, prefix: str = "req") -> str:
        """Generate a new correlation ID"""
        return f"{prefix}_{uuid.uuid4().hex[:12]}"
    
    def get_current_correlation_id(self) -> Optional[str]:
        """Get current correlation ID from context"""
        if STREAMLIT_AVAILABLE and st and hasattr(st, 'session_state'):
            return st.session_state.get('correlation_id')
        return None
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID in current context"""
        if STREAMLIT_AVAILABLE and st and hasattr(st, 'session_state'):
            st.session_state['correlation_id'] = correlation_id
    
    def ensure_correlation_id(self) -> str:
        """Ensure correlation ID exists, create if needed"""
        correlation_id = self.get_current_correlation_id()
        if not correlation_id:
            correlation_id = self.generate_correlation_id()
            self.set_correlation_id(correlation_id)
        return correlation_id

class StructuredLogger:
    """Structured logging with correlation ID support"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.correlation_manager = CorrelationIDManager()
        
        # Configure JSON formatter if not already configured
        if not self.logger.handlers:
            self._setup_json_logging()
    
    def _setup_json_logging(self):
        """Setup JSON-based logging format"""
        from .log_formatter import JSONFormatter
        
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _get_session_info(self) -> Dict[str, Any]:
        """Extract session information"""
        session_info = {}
        
        if STREAMLIT_AVAILABLE and st and hasattr(st, 'session_state'):
            session_info['session_id'] = st.session_state.get('session_id', 'unknown')
            session_info['user_id'] = st.session_state.get('user_id', 'anonymous')
            
            # Extract IP if available
            try:
                if hasattr(st, 'experimental_get_query_params'):
                    session_info['query_params'] = st.experimental_get_query_params()
            except:
                pass
        
        return session_info
    
    def log_operation(
        self,
        operation: str,
        level: str = "INFO",
        message: str = "",
        duration_ms: Optional[float] = None,
        success: bool = True,
        error: Optional[Exception] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an operation with correlation context"""
        
        correlation_id = self.correlation_manager.ensure_correlation_id()
        session_info = self._get_session_info()
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "correlation_id": correlation_id,
            "operation": operation,
            "level": level,
            "message": message,
            "success": success,
            **session_info
        }
        
        if duration_ms is not None:
            log_entry["duration_ms"] = round(duration_ms, 2)
        
        if error:
            log_entry["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": str(error) if hasattr(error, '__traceback__') else None
            }
        
        if metadata:
            log_entry["metadata"] = metadata
        
        # Log at appropriate level
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, json.dumps(log_entry))
    
    def info(self, operation: str, message: str, **kwargs):
        """Log info level operation"""
        self.log_operation(operation, "INFO", message, **kwargs)
    
    def error(self, operation: str, message: str, error: Exception = None, **kwargs):
        """Log error level operation"""
        self.log_operation(operation, "ERROR", message, error=error, success=False, **kwargs)
    
    def warning(self, operation: str, message: str, **kwargs):
        """Log warning level operation"""
        self.log_operation(operation, "WARNING", message, **kwargs)
    
    @contextmanager
    def track_operation(
        self,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Context manager to track operation duration and success"""
        start_time = time.time()
        correlation_id = self.correlation_manager.ensure_correlation_id()
        
        self.info(
            f"{operation}_start",
            f"Starting operation: {operation}",
            metadata={"correlation_id": correlation_id, **(metadata or {})}
        )
        
        try:
            yield correlation_id
            duration_ms = (time.time() - start_time) * 1000
            self.info(
                f"{operation}_complete",
                f"Operation completed successfully: {operation}",
                duration_ms=duration_ms,
                metadata=metadata
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.error(
                f"{operation}_failed",
                f"Operation failed: {operation}",
                error=e,
                duration_ms=duration_ms,
                metadata=metadata
            )
            raise

def with_correlation_logging(operation: str, metadata_func=None):
    """Decorator to add correlation logging to functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = StructuredLogger(func.__module__)
            
            # Extract metadata if function provided
            metadata = {}
            if metadata_func:
                try:
                    metadata = metadata_func(*args, **kwargs)
                except:
                    pass
            
            with logger.track_operation(operation, metadata):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Global logger instance
correlation_logger = StructuredLogger(__name__)
```

### **FILE 2: streamlit_extension/utils/log_formatter.py**
```python
"""
JSON Log Formatter for structured logging
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Start with basic log record
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage()
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'lineno', 
                          'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process',
                          'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)

class CorrelationFilter(logging.Filter):
    """Filter to add correlation ID to all log records"""
    
    def __init__(self):
        super().__init__()
        from .correlation_logging import CorrelationIDManager
        self.correlation_manager = CorrelationIDManager()
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record"""
        correlation_id = self.correlation_manager.get_current_correlation_id()
        if correlation_id:
            record.correlation_id = correlation_id
        return True
```

### **STEP 3: Integration with existing pages**

#### **clients.py integration:**
```python
# ADD TO TOP OF FILE:
from streamlit_extension.utils.correlation_logging import correlation_logger, with_correlation_logging

# MODIFY EXISTING FUNCTIONS:
@with_correlation_logging("create_client", lambda client_data: {"client_key": client_data.get("client_key")})
def create_client_with_logging(client_data):
    """Create client with correlation logging"""
    # Existing create_client logic here
    pass

# ADD OPERATION LOGGING:
def render_clients_page():
    """Render clients page with operation tracking"""
    with correlation_logger.track_operation("render_clients_page"):
        # Existing page rendering logic
        pass
```

#### **projects.py integration:**
```python
# Similar pattern for projects.py
@with_correlation_logging("create_project", lambda **kwargs: {"project_key": kwargs.get("project_key")})
def create_project_with_logging(**kwargs):
    pass
```

---

## 🔍 **VERIFICATION CRITERIA**

### **SUCCESS REQUIREMENTS:**
1. ✅ **Correlation IDs generated** for all operations
2. ✅ **JSON structured logging** implemented
3. ✅ **Operation tracking** with duration measurement
4. ✅ **Multi-user differentiation** via session/user IDs
5. ✅ **Error context preservation** in logs
6. ✅ **Performance monitoring** via duration tracking
7. ✅ **Integration complete** across main pages

### **LOG STRUCTURE VALIDATION:**
```json
{
    "timestamp": "2025-08-16T10:30:00Z",
    "correlation_id": "req_abc123def456",
    "session_id": "session_xyz789", 
    "user_id": "user_123",
    "operation": "create_client",
    "level": "INFO",
    "message": "Client created successfully",
    "duration_ms": 45.67,
    "success": true,
    "metadata": {
        "client_id": 123,
        "client_key": "new_client"
    }
}
```

---

## 📊 **EXPECTED RESULTS**

### **BEFORE IMPLEMENTATION:**
- Scattered logging without correlation
- No operation duration tracking
- Difficult to trace multi-user operations
- Basic string-based log messages

### **AFTER IMPLEMENTATION:**
- Structured JSON logs with correlation IDs
- Complete operation lifecycle tracking  
- Multi-user operation traceability
- Performance metrics in logs
- Error context preservation
- Production-ready observability

---

## ⚠️ **CRITICAL REQUIREMENTS**

1. **PERFORMANCE IMPACT** - Logging must not significantly impact performance
2. **SESSION SAFETY** - Handle Streamlit session state safely
3. **BACKWARDS COMPATIBILITY** - Don't break existing logging
4. **ERROR RESILIENCE** - Logging failures must not break operations
5. **PRIVACY COMPLIANCE** - Don't log sensitive user data

---

## 📈 **SUCCESS METRICS**

- ✅ **100% operation correlation** - All operations have correlation IDs
- ✅ **Structured logging format** - JSON-based log entries
- ✅ **Multi-user traceability** - Session and user differentiation
- ✅ **Performance monitoring** - Duration tracking for all operations
- ✅ **Error context** - Complete error information in logs
- ✅ **Production observability** - Debugging capability enhancement
- ✅ **Report.md Item 99** - RESOLVED

**PRIORITY**: High (production observability)
**DEPENDENCIES**: None (isolated utility implementation)
**RISK**: Medium (potential performance impact, session handling complexity)