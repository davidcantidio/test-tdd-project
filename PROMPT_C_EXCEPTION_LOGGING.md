# ⚠️ PROMPT C - EXCEPTION HANDLER + STRUCTURED LOGGING

**TASK**: Implementar sistema global de exception handling + structured logging  
**ARQUIVOS**: `streamlit_extension/utils/exceptions.py`, `streamlit_extension/utils/logging_config.py` (ISOLADO)  
**PRIORITY**: P0 - CRITICAL (bloqueador de produção no report.md)  
**CONTEXT**: "No global exception handler" + "Structured logging missing" + "Error logs may reveal sensitive info"

---

## 📋 **ARQUIVOS A CRIAR/EXPANDIR:**

### 1. `streamlit_extension/utils/exceptions.py`
```python
"""Global exception handling system for Streamlit application."""

from __future__ import annotations
import traceback
import sys
from typing import Optional, Dict, Any, Callable, Type
from functools import wraps
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import streamlit as st

from .logging_config import get_logger, LogLevel


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    SECURITY = "security"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_API = "external_api"
    SYSTEM = "system"
    USER_INPUT = "user_input"


@dataclass
class ErrorContext:
    """Error context information."""
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    function_name: Optional[str] = None
    module_name: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class ApplicationError:
    """Structured application error."""
    error_id: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: datetime
    context: ErrorContext
    exception: Optional[Exception] = None
    stack_trace: Optional[str] = None
    user_message: Optional[str] = None
    suggested_action: Optional[str] = None


class DatabaseError(Exception):
    """Database-related errors."""
    def __init__(self, message: str, query: Optional[str] = None, params: Optional[tuple] = None):
        super().__init__(message)
        self.query = query
        self.params = params
        self.category = ErrorCategory.DATABASE


class ValidationError(Exception):
    """Validation-related errors."""
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(message)
        self.field = field
        self.value = value
        self.category = ErrorCategory.VALIDATION


class SecurityError(Exception):
    """Security-related errors."""
    def __init__(self, message: str, threat_type: Optional[str] = None, source_ip: Optional[str] = None):
        super().__init__(message)
        self.threat_type = threat_type
        self.source_ip = source_ip
        self.category = ErrorCategory.SECURITY


class BusinessLogicError(Exception):
    """Business logic errors."""
    def __init__(self, message: str, operation: Optional[str] = None, entity: Optional[str] = None):
        super().__init__(message)
        self.operation = operation
        self.entity = entity
        self.category = ErrorCategory.BUSINESS_LOGIC


class GlobalExceptionHandler:
    """Global exception handler with logging and user-friendly error pages."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._error_counter = 0
        self._error_handlers: Dict[Type[Exception], Callable] = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default exception handlers."""
        self._error_handlers = {
            DatabaseError: self._handle_database_error,
            ValidationError: self._handle_validation_error,
            SecurityError: self._handle_security_error,
            BusinessLogicError: self._handle_business_logic_error,
            PermissionError: self._handle_permission_error,
            FileNotFoundError: self._handle_file_not_found_error,
            ConnectionError: self._handle_connection_error,
            TimeoutError: self._handle_timeout_error,
            ValueError: self._handle_value_error,
            KeyError: self._handle_key_error,
            AttributeError: self._handle_attribute_error,
            Exception: self._handle_generic_error
        }
    
    def generate_error_id(self) -> str:
        """Generate unique error ID."""
        self._error_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"ERR_{timestamp}_{self._error_counter:04d}"
    
    def get_error_context(self) -> ErrorContext:
        """Get current error context from Streamlit session."""
        return ErrorContext(
            user_id=st.session_state.get("current_user", {}).get("id"),
            session_id=st.session_state.get("session_id"),
            request_id=st.session_state.get("request_id"),
            additional_data={
                "page": getattr(st, "current_page", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def sanitize_error_message(self, message: str) -> str:
        """Sanitize error message to remove sensitive information."""
        # Remove potential file paths
        import re
        message = re.sub(r'/[a-zA-Z0-9_./]+', '[PATH_REDACTED]', message)
        
        # Remove potential database connection strings
        message = re.sub(r'sqlite:///[^\s]+', '[DB_PATH_REDACTED]', message)
        
        # Remove potential email addresses in errors
        message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', message)
        
        # Remove potential passwords or tokens
        message = re.sub(r'(password|token|secret|key)[\s=:]+[^\s]+', r'\1=[REDACTED]', message, flags=re.IGNORECASE)
        
        return message
    
    def create_application_error(self, exception: Exception, context: ErrorContext, 
                               severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> ApplicationError:
        """Create structured application error."""
        error_id = self.generate_error_id()
        
        # Determine category based on exception type
        category = getattr(exception, 'category', ErrorCategory.SYSTEM)
        
        # Get stack trace
        stack_trace = traceback.format_exc() if exception else None
        
        # Sanitize error message
        sanitized_message = self.sanitize_error_message(str(exception))
        
        # Generate user-friendly message
        user_message = self._generate_user_message(exception, category)
        
        # Generate suggested action
        suggested_action = self._generate_suggested_action(exception, category)
        
        return ApplicationError(
            error_id=error_id,
            message=sanitized_message,
            severity=severity,
            category=category,
            timestamp=datetime.now(),
            context=context,
            exception=exception,
            stack_trace=stack_trace,
            user_message=user_message,
            suggested_action=suggested_action
        )
    
    def _generate_user_message(self, exception: Exception, category: ErrorCategory) -> str:
        """Generate user-friendly error message."""
        user_messages = {
            ErrorCategory.DATABASE: "Database operation failed. Please try again.",
            ErrorCategory.AUTHENTICATION: "Authentication error. Please log in again.",
            ErrorCategory.VALIDATION: "Input validation failed. Please check your data.",
            ErrorCategory.SECURITY: "Security error detected. Access denied.",
            ErrorCategory.BUSINESS_LOGIC: "Operation could not be completed due to business rules.",
            ErrorCategory.EXTERNAL_API: "External service unavailable. Please try again later.",
            ErrorCategory.SYSTEM: "System error occurred. Please contact support.",
            ErrorCategory.USER_INPUT: "Invalid input provided. Please correct and try again."
        }
        
        return user_messages.get(category, "An unexpected error occurred. Please try again.")
    
    def _generate_suggested_action(self, exception: Exception, category: ErrorCategory) -> str:
        """Generate suggested action for error resolution."""
        actions = {
            ErrorCategory.DATABASE: "Check your connection and try again",
            ErrorCategory.AUTHENTICATION: "Please log in again",
            ErrorCategory.VALIDATION: "Correct the highlighted fields and resubmit",
            ErrorCategory.SECURITY: "Contact system administrator",
            ErrorCategory.BUSINESS_LOGIC: "Review the operation requirements",
            ErrorCategory.EXTERNAL_API: "Wait a moment and try again",
            ErrorCategory.SYSTEM: "Contact technical support",
            ErrorCategory.USER_INPUT: "Review your input and try again"
        }
        
        return actions.get(category, "Try again or contact support")
    
    def handle_exception(self, exception: Exception, context: Optional[ErrorContext] = None) -> ApplicationError:
        """Handle exception with logging and user notification."""
        if context is None:
            context = self.get_error_context()
        
        # Determine severity
        severity = self._determine_severity(exception)
        
        # Create application error
        app_error = self.create_application_error(exception, context, severity)
        
        # Log the error
        self._log_error(app_error)
        
        # Handle UI display
        self._display_error(app_error)
        
        return app_error
    
    def _determine_severity(self, exception: Exception) -> ErrorSeverity:
        """Determine error severity based on exception type."""
        critical_exceptions = (SecurityError, DatabaseError)
        high_exceptions = (PermissionError, ConnectionError)
        medium_exceptions = (ValidationError, BusinessLogicError, ValueError)
        
        if isinstance(exception, critical_exceptions):
            return ErrorSeverity.CRITICAL
        elif isinstance(exception, high_exceptions):
            return ErrorSeverity.HIGH
        elif isinstance(exception, medium_exceptions):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _log_error(self, app_error: ApplicationError):
        """Log error with appropriate level."""
        log_data = {
            "error_id": app_error.error_id,
            "category": app_error.category.value,
            "severity": app_error.severity.value,
            "user_id": app_error.context.user_id,
            "session_id": app_error.context.session_id,
            "function": app_error.context.function_name,
            "module": app_error.context.module_name
        }
        
        if app_error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Critical error: {app_error.message}", extra=log_data)
        elif app_error.severity == ErrorSeverity.HIGH:
            self.logger.error(f"High severity error: {app_error.message}", extra=log_data)
        elif app_error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"Medium severity error: {app_error.message}", extra=log_data)
        else:
            self.logger.info(f"Low severity error: {app_error.message}", extra=log_data)
        
        # Log stack trace for debugging (only in debug mode)
        if app_error.stack_trace and self.logger.isEnabledFor(LogLevel.DEBUG.value):
            self.logger.debug(f"Stack trace for {app_error.error_id}: {app_error.stack_trace}")
    
    def _display_error(self, app_error: ApplicationError):
        """Display error in Streamlit UI."""
        if app_error.severity == ErrorSeverity.CRITICAL:
            st.error(f"🚨 Critical Error: {app_error.user_message}")
            st.error(f"Error ID: {app_error.error_id}")
            st.stop()
        elif app_error.severity == ErrorSeverity.HIGH:
            st.error(f"❌ Error: {app_error.user_message}")
            if app_error.suggested_action:
                st.info(f"💡 Suggestion: {app_error.suggested_action}")
        elif app_error.severity == ErrorSeverity.MEDIUM:
            st.warning(f"⚠️ Warning: {app_error.user_message}")
            if app_error.suggested_action:
                st.info(f"💡 Suggestion: {app_error.suggested_action}")
        else:
            st.info(f"ℹ️ Notice: {app_error.user_message}")
    
    # Specific error handlers
    def _handle_database_error(self, error: DatabaseError, context: ErrorContext) -> ApplicationError:
        """Handle database-specific errors."""
        return self.create_application_error(error, context, ErrorSeverity.CRITICAL)
    
    def _handle_validation_error(self, error: ValidationError, context: ErrorContext) -> ApplicationError:
        """Handle validation errors."""
        return self.create_application_error(error, context, ErrorSeverity.MEDIUM)
    
    def _handle_security_error(self, error: SecurityError, context: ErrorContext) -> ApplicationError:
        """Handle security errors."""
        return self.create_application_error(error, context, ErrorSeverity.CRITICAL)
    
    def _handle_business_logic_error(self, error: BusinessLogicError, context: ErrorContext) -> ApplicationError:
        """Handle business logic errors."""
        return self.create_application_error(error, context, ErrorSeverity.MEDIUM)
    
    def _handle_permission_error(self, error: PermissionError, context: ErrorContext) -> ApplicationError:
        """Handle permission errors."""
        return self.create_application_error(error, context, ErrorSeverity.HIGH)
    
    def _handle_file_not_found_error(self, error: FileNotFoundError, context: ErrorContext) -> ApplicationError:
        """Handle file not found errors."""
        return self.create_application_error(error, context, ErrorSeverity.MEDIUM)
    
    def _handle_connection_error(self, error: ConnectionError, context: ErrorContext) -> ApplicationError:
        """Handle connection errors."""
        return self.create_application_error(error, context, ErrorSeverity.HIGH)
    
    def _handle_timeout_error(self, error: TimeoutError, context: ErrorContext) -> ApplicationError:
        """Handle timeout errors."""
        return self.create_application_error(error, context, ErrorSeverity.HIGH)
    
    def _handle_value_error(self, error: ValueError, context: ErrorContext) -> ApplicationError:
        """Handle value errors."""
        return self.create_application_error(error, context, ErrorSeverity.MEDIUM)
    
    def _handle_key_error(self, error: KeyError, context: ErrorContext) -> ApplicationError:
        """Handle key errors."""
        return self.create_application_error(error, context, ErrorSeverity.MEDIUM)
    
    def _handle_attribute_error(self, error: AttributeError, context: ErrorContext) -> ApplicationError:
        """Handle attribute errors."""
        return self.create_application_error(error, context, ErrorSeverity.MEDIUM)
    
    def _handle_generic_error(self, error: Exception, context: ErrorContext) -> ApplicationError:
        """Handle generic errors."""
        return self.create_application_error(error, context, ErrorSeverity.MEDIUM)


# Global exception handler instance
_global_exception_handler: Optional[GlobalExceptionHandler] = None


def get_exception_handler() -> GlobalExceptionHandler:
    """Get global exception handler instance."""
    global _global_exception_handler
    if _global_exception_handler is None:
        _global_exception_handler = GlobalExceptionHandler()
    return _global_exception_handler


def handle_exception(exception: Exception, context: Optional[ErrorContext] = None) -> ApplicationError:
    """Handle exception using global handler."""
    handler = get_exception_handler()
    return handler.handle_exception(exception, context)


def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """Execute function with exception handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_exception(e)
        return None


def exception_handler(func: Callable):
    """Decorator for automatic exception handling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = ErrorContext(
                function_name=func.__name__,
                module_name=func.__module__
            )
            handle_exception(e, context)
            return None
    return wrapper


def streamlit_exception_handler(func: Callable):
    """Exception handler specifically for Streamlit functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = ErrorContext(
                function_name=func.__name__,
                module_name=func.__module__,
                user_id=st.session_state.get("current_user", {}).get("id"),
                session_id=st.session_state.get("session_id")
            )
            app_error = handle_exception(e, context)
            
            # For critical errors, stop execution
            if app_error.severity == ErrorSeverity.CRITICAL:
                st.stop()
            
            return None
    return wrapper


def setup_global_exception_handling():
    """Setup global exception handling for the application."""
    def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        """Handle unhandled exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow keyboard interrupts to pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Handle other exceptions
        context = ErrorContext(
            function_name="global",
            module_name="__main__"
        )
        handle_exception(exc_value, context)
    
    # Set global exception handler
    sys.excepthook = handle_unhandled_exception
```

### 2. `streamlit_extension/utils/logging_config.py`
```python
"""Structured logging configuration for the application."""

from __future__ import annotations
import logging
import logging.handlers
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from pathlib import Path
import streamlit as st


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormat(Enum):
    """Logging formats."""
    JSON = "json"
    TEXT = "text"
    STRUCTURED = "structured"


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def __init__(self, format_type: LogFormat = LogFormat.JSON):
        super().__init__()
        self.format_type = format_type
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured data."""
        # Basic log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'message', 'exc_info', 'exc_text',
                          'stack_info'):
                extra_fields[key] = value
        
        if extra_fields:
            log_data["extra"] = extra_fields
        
        # Add Streamlit session context if available
        try:
            if hasattr(st, 'session_state') and st.session_state:
                session_context = {
                    "user_id": st.session_state.get("current_user", {}).get("id"),
                    "session_id": st.session_state.get("session_id"),
                    "page": getattr(st, "current_page", "unknown")
                }
                log_data["session"] = {k: v for k, v in session_context.items() if v is not None}
        except Exception:
            # Ignore session state errors during logging
            pass
        
        # Format based on type
        if self.format_type == LogFormat.JSON:
            return json.dumps(log_data, default=str, ensure_ascii=False)
        elif self.format_type == LogFormat.STRUCTURED:
            return self._format_structured(log_data)
        else:
            return self._format_text(log_data)
    
    def _format_structured(self, log_data: Dict[str, Any]) -> str:
        """Format as structured text."""
        parts = [
            f"[{log_data['timestamp']}]",
            f"[{log_data['level']}]",
            f"[{log_data['logger']}]",
            log_data['message']
        ]
        
        if 'session' in log_data:
            session = log_data['session']
            if session.get('user_id'):
                parts.append(f"user={session['user_id']}")
            if session.get('session_id'):
                parts.append(f"session={session['session_id'][:8]}...")
        
        if 'extra' in log_data:
            for key, value in log_data['extra'].items():
                parts.append(f"{key}={value}")
        
        result = " ".join(parts)
        
        if 'exception' in log_data:
            result += f"\nException: {log_data['exception']['type']}: {log_data['exception']['message']}"
        
        return result
    
    def _format_text(self, log_data: Dict[str, Any]) -> str:
        """Format as simple text."""
        timestamp = log_data['timestamp'][:19]  # Remove microseconds
        return f"{timestamp} [{log_data['level']}] {log_data['logger']}: {log_data['message']}"


class LoggingConfig:
    """Centralized logging configuration."""
    
    def __init__(self, 
                 level: LogLevel = LogLevel.INFO,
                 format_type: LogFormat = LogFormat.STRUCTURED,
                 log_file: Optional[str] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 console_output: bool = True):
        
        self.level = level
        self.format_type = format_type
        self.log_file = log_file
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.console_output = console_output
        self._loggers: Dict[str, logging.Logger] = {}
        
        # Setup root logger
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Setup root logger configuration."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.level.value)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Create formatter
        formatter = StructuredFormatter(self.format_type)
        
        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.level.value)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # File handler
        if self.log_file:
            self._setup_file_handler(root_logger, formatter)
        
        # Prevent duplicate logs
        root_logger.propagate = False
    
    def _setup_file_handler(self, logger: logging.Logger, formatter: StructuredFormatter):
        """Setup rotating file handler."""
        # Ensure log directory exists
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        file_handler.setLevel(self.level.value)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get logger for specific module."""
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(self.level.value)
        
        # Don't add handlers to child loggers (they inherit from root)
        logger.propagate = True
        
        self._loggers[name] = logger
        return logger
    
    def set_level(self, level: LogLevel):
        """Change logging level dynamically."""
        self.level = level
        root_logger = logging.getLogger()
        root_logger.setLevel(level.value)
        
        for handler in root_logger.handlers:
            handler.setLevel(level.value)
        
        for logger in self._loggers.values():
            logger.setLevel(level.value)
    
    def add_custom_handler(self, handler: logging.Handler):
        """Add custom logging handler."""
        formatter = StructuredFormatter(self.format_type)
        handler.setFormatter(formatter)
        handler.setLevel(self.level.value)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
    
    def create_correlation_id(self) -> str:
        """Create correlation ID for request tracking."""
        import uuid
        return str(uuid.uuid4())
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID in session state."""
        if hasattr(st, 'session_state'):
            st.session_state.correlation_id = correlation_id
    
    def get_correlation_id(self) -> Optional[str]:
        """Get correlation ID from session state."""
        if hasattr(st, 'session_state'):
            return st.session_state.get('correlation_id')
        return None


# Global logging configuration
_logging_config: Optional[LoggingConfig] = None


def setup_logging(level: LogLevel = LogLevel.INFO,
                 format_type: LogFormat = LogFormat.STRUCTURED,
                 log_file: Optional[str] = None,
                 console_output: bool = True) -> LoggingConfig:
    """Setup global logging configuration."""
    global _logging_config
    
    # Default log file location
    if log_file is None:
        log_file = "logs/app.log"
    
    _logging_config = LoggingConfig(
        level=level,
        format_type=format_type,
        log_file=log_file,
        console_output=console_output
    )
    
    return _logging_config


def get_logging_config() -> LoggingConfig:
    """Get global logging configuration."""
    global _logging_config
    if _logging_config is None:
        _logging_config = setup_logging()
    return _logging_config


def get_logger(name: str) -> logging.Logger:
    """Get logger for specific module."""
    config = get_logging_config()
    return config.get_logger(name)


def log_function_call(func_name: str, args: tuple = (), kwargs: Dict[str, Any] = None):
    """Log function call with parameters."""
    logger = get_logger("function_calls")
    
    # Sanitize arguments for logging
    safe_args = []
    for arg in args:
        if isinstance(arg, str) and len(arg) > 100:
            safe_args.append(f"{arg[:97]}...")
        else:
            safe_args.append(repr(arg))
    
    safe_kwargs = {}
    if kwargs:
        for key, value in kwargs.items():
            if isinstance(value, str) and len(value) > 100:
                safe_kwargs[key] = f"{value[:97]}..."
            else:
                safe_kwargs[key] = repr(value)
    
    logger.debug(f"Function call: {func_name}", extra={
        "function": func_name,
        "args": safe_args,
        "kwargs": safe_kwargs
    })


def log_performance(func_name: str, duration: float, additional_data: Dict[str, Any] = None):
    """Log performance metrics."""
    logger = get_logger("performance")
    
    log_data = {
        "function": func_name,
        "duration_ms": round(duration * 1000, 2)
    }
    
    if additional_data:
        log_data.update(additional_data)
    
    logger.info(f"Performance: {func_name} took {duration:.3f}s", extra=log_data)


def log_user_action(action: str, user_id: Optional[int] = None, additional_data: Dict[str, Any] = None):
    """Log user actions for audit trail."""
    logger = get_logger("user_actions")
    
    log_data = {
        "action": action,
        "user_id": user_id or st.session_state.get("current_user", {}).get("id")
    }
    
    if additional_data:
        log_data.update(additional_data)
    
    logger.info(f"User action: {action}", extra=log_data)


def log_security_event(event_type: str, severity: str, details: Dict[str, Any] = None):
    """Log security events."""
    logger = get_logger("security")
    
    log_data = {
        "event_type": event_type,
        "severity": severity
    }
    
    if details:
        log_data.update(details)
    
    logger.warning(f"Security event: {event_type}", extra=log_data)
```

### 3. Update `streamlit_extension/utils/__init__.py`:
```python
"""Utilities package with enhanced exception handling and logging."""

from .exceptions import (
    GlobalExceptionHandler, 
    ApplicationError, 
    DatabaseError, 
    ValidationError, 
    SecurityError,
    BusinessLogicError,
    ErrorSeverity,
    ErrorCategory,
    exception_handler,
    streamlit_exception_handler,
    safe_execute,
    handle_exception,
    setup_global_exception_handling
)

from .logging_config import (
    LoggingConfig,
    LogLevel,
    LogFormat,
    setup_logging,
    get_logger,
    log_function_call,
    log_performance,
    log_user_action,
    log_security_event
)

# Import existing utilities
from .database import DatabaseManager
from .cache import CacheManager

__all__ = [
    # Exception handling
    "GlobalExceptionHandler",
    "ApplicationError", 
    "DatabaseError",
    "ValidationError",
    "SecurityError",
    "BusinessLogicError",
    "ErrorSeverity",
    "ErrorCategory",
    "exception_handler",
    "streamlit_exception_handler",
    "safe_execute",
    "handle_exception",
    "setup_global_exception_handling",
    
    # Logging
    "LoggingConfig",
    "LogLevel", 
    "LogFormat",
    "setup_logging",
    "get_logger",
    "log_function_call",
    "log_performance",
    "log_user_action",
    "log_security_event",
    
    # Existing utilities
    "DatabaseManager",
    "CacheManager"
]
```

---

## 🔧 **INTEGRATION INSTRUCTIONS:**

### A. Update main `streamlit_app.py`:
```python
# Add to imports at top
from streamlit_extension.utils import setup_logging, setup_global_exception_handling, LogLevel
from streamlit_extension.utils import streamlit_exception_handler, get_logger

# Setup logging and exception handling at startup
def main():
    # Setup logging
    setup_logging(
        level=LogLevel.INFO,
        log_file="logs/app.log",
        console_output=True
    )
    
    # Setup global exception handling
    setup_global_exception_handling()
    
    # Get logger for main app
    logger = get_logger(__name__)
    logger.info("Application started")
    
    # Rest of existing main() function...
```

### B. Update existing functions with exception handling:
```python
# Add to all major functions
@streamlit_exception_handler
def render_clients_page():
    logger = get_logger(__name__)
    logger.info("Rendering clients page")
    
    # Existing function content...
```

### C. Update database operations with structured errors:
```python
# In database.py
from streamlit_extension.utils import DatabaseError, log_performance, get_logger

def create_client(self, client_data):
    logger = get_logger(__name__)
    start_time = time.time()
    
    try:
        # Database operation
        result = self.conn.execute(query, params)
        
        # Log performance
        log_performance("create_client", time.time() - start_time, {
            "rows_affected": result.rowcount
        })
        
        return result
    except Exception as e:
        raise DatabaseError(f"Failed to create client: {str(e)}", query=query, params=params)
```

---

## ✅ **VERIFICATION CHECKLIST:**

- [ ] Exception handling files created in `streamlit_extension/utils/`
- [ ] Global exception handler catching all errors
- [ ] Structured logging configuration active
- [ ] Error messages sanitized (no sensitive data)
- [ ] User-friendly error pages displaying
- [ ] Performance logging operational
- [ ] Security event logging working
- [ ] Correlation IDs for request tracking
- [ ] Log rotation and file management
- [ ] Integration with existing utilities

---

## 🎯 **SUCCESS CRITERIA:**

1. **P0 Critical Issue RESOLVED**: "No global exception handler; errors bubble to UI with raw messages"
2. **Structured Logging**: Comprehensive logging with correlation IDs and performance metrics
3. **Security Enhancement**: Sensitive data redaction in error messages
4. **User Experience**: User-friendly error pages with suggested actions
5. **Production Ready**: Enterprise-grade error handling and logging

**RESULTADO ESPERADO**: Sistema robusto de exception handling + structured logging eliminando erros em produção e habilitando monitoramento enterprise-grade com sanitização de dados sensíveis.