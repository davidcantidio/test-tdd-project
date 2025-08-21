#!/usr/bin/env python3
"""
📊 Structured Logging with Correlation IDs

Addresses report.md requirement: "Set up structured logging and monitoring"
and "Introduce comprehensive logging with correlation IDs for multi-user tracing"

This module provides:
- Structured JSON logging
- Correlation ID tracking across requests
- Context management for request tracing
- Performance metrics logging
- Security event logging
- Integration with monitoring systems
"""

import os
import sys
import json
import time
import uuid
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass, asdict, field

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config.environment import get_config, is_production
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    get_config = None
    is_production = lambda: False

try:
    from duration_system.log_sanitization import sanitize_log_message
    LOG_SANITIZATION_AVAILABLE = True
except ImportError:
    LOG_SANITIZATION_AVAILABLE = False
    sanitize_log_message = lambda msg, level: msg


# Thread-local storage for correlation context
_correlation_context = threading.local()


@dataclass
class CorrelationContext:
    """Correlation context for request tracing."""
    correlation_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    operation: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class StructuredLogFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def __init__(self, include_correlation: bool = True, include_performance: bool = True):
        super().__init__()
        self.include_correlation = include_correlation
        self.include_performance = include_performance
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation context if available
        if self.include_correlation:
            correlation = get_correlation_context()
            if correlation:
                log_entry["correlation"] = correlation.to_dict()
        
        # Add performance metrics if available
        if self.include_performance and hasattr(record, 'performance'):
            log_entry["performance"] = record.performance
        
        # Add custom fields from record
        for attr in ['user_id', 'operation', 'error_code', 'request_size', 'response_size']:
            if hasattr(record, attr):
                log_entry[attr] = getattr(record, attr)
        
        # Add exception information
        if record.exc_info:
            import traceback
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry["extra_fields"] = record.extra_fields
        
        # Sanitize sensitive data if available
        if LOG_SANITIZATION_AVAILABLE:
            log_entry["message"] = sanitize_log_message(log_entry["message"], record.levelname)
        
        return json.dumps(log_entry, ensure_ascii=False)


class CorrelationIDFilter(logging.Filter):
    """Filter to add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation context to log record."""
        correlation = get_correlation_context()
        if correlation:
            record.correlation_id = correlation.correlation_id
            record.user_id = correlation.user_id
            record.session_id = correlation.session_id
            record.operation = correlation.operation
        
        return True


class PerformanceLoggerMixin:
    """Mixin to add performance logging capabilities."""
    
    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """Log performance metrics."""
        performance_data = {
            "operation": operation,
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs
        }
        
        # Use structured logger if available
        logger = getattr(self, 'logger', logging.getLogger(__name__))
        
        # Create log record with performance data
        record = logger.makeRecord(
            logger.name, logging.INFO, "", 0,
            f"Performance: {operation} completed in {duration_ms:.2f}ms",
            (), None
        )
        record.performance = performance_data
        
        logger.handle(record)
    
    @contextmanager
    def performance_timer(self, operation: str, **kwargs):
        """Context manager for timing operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000
            self.log_performance(operation, duration, **kwargs)


class SecurityEventLogger:
    """Logger for security-related events."""
    
    def __init__(self, logger_name: str = "security"):
        self.logger = get_structured_logger(logger_name)
    
    def log_authentication_attempt(self, user_id: str, success: bool, method: str = "oauth", **kwargs):
        """Log authentication attempt."""
        self.logger.info(
            f"Authentication {'succeeded' if success else 'failed'} for user {user_id}",
            extra={
                'extra_fields': {
                    'event_type': 'authentication',
                    'user_id': user_id,
                    'success': success,
                    'method': method,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    **kwargs
                }
            }
        )
    
    def log_authorization_failure(self, user_id: str, resource: str, action: str, **kwargs):
        """Log authorization failure."""
        self.logger.warning(
            f"Authorization denied: user {user_id} attempted {action} on {resource}",
            extra={
                'extra_fields': {
                    'event_type': 'authorization_failure',
                    'user_id': user_id,
                    'resource': resource,
                    'action': action,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    **kwargs
                }
            }
        )
    
    def log_security_violation(self, violation_type: str, details: Dict[str, Any], severity: str = "medium"):
        """Log security violation."""
        level = {
            "low": logging.INFO,
            "medium": logging.WARNING,
            "high": logging.ERROR,
            "critical": logging.CRITICAL
        }.get(severity, logging.WARNING)
        
        self.logger.log(
            level,
            f"Security violation detected: {violation_type}",
            extra={
                'extra_fields': {
                    'event_type': 'security_violation',
                    'violation_type': violation_type,
                    'severity': severity,
                    'details': details,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
        )
    
    def log_rate_limit_exceeded(self, identifier: str, limit_type: str, **kwargs):
        """Log rate limit exceeded."""
        self.logger.warning(
            f"Rate limit exceeded: {identifier} for {limit_type}",
            extra={
                'extra_fields': {
                    'event_type': 'rate_limit_exceeded',
                    'identifier': identifier,
                    'limit_type': limit_type,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    **kwargs
                }
            }
        )


def generate_correlation_id() -> str:
    """Generate a unique correlation ID."""
    return str(uuid.uuid4())


def get_correlation_context() -> Optional[CorrelationContext]:
    """Get current correlation context."""
    return getattr(_correlation_context, 'current', None)


def set_correlation_context(context: CorrelationContext):
    """Set correlation context."""
    _correlation_context.current = context


def clear_correlation_context():
    """Clear correlation context."""
    _correlation_context.current = None


@contextmanager
def correlation_context(correlation_id: Optional[str] = None, **kwargs):
    """Context manager for correlation tracking."""
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    
    # Create new context
    context = CorrelationContext(
        correlation_id=correlation_id,
        **kwargs
    )
    
    # Store previous context
    previous_context = get_correlation_context()
    
    try:
        set_correlation_context(context)
        yield context
    finally:
        # Restore previous context
        if previous_context:
            set_correlation_context(previous_context)
        else:
            clear_correlation_context()


def update_correlation_context(**kwargs):
    """Update current correlation context."""
    context = get_correlation_context()
    if context:
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)
            else:
                context.metadata[key] = value


def get_structured_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get a structured logger with correlation ID support."""
    logger = logging.getLogger(name)
    
    # Configure logger if not already configured
    if not logger.handlers:
        setup_structured_logging(logger, level)
    
    return logger


def setup_structured_logging(logger: Optional[logging.Logger] = None, level: Optional[str] = None):
    """Setup structured logging configuration."""
    if logger is None:
        logger = logging.getLogger()
    
    # Determine log level
    if level is None:
        if CONFIG_AVAILABLE:
            try:
                config = get_config()
                level = config.security.log_level
            except Exception:
                level = "INFO"
        else:
            level = "INFO"
    
    # Set log level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create handler
    if CONFIG_AVAILABLE:
        try:
            config = get_config()
            if config.monitoring.log_file_path:
                handler = logging.FileHandler(config.monitoring.log_file_path)
            else:
                handler = logging.StreamHandler()
        except Exception:
            handler = logging.StreamHandler()
    else:
        handler = logging.StreamHandler()
    
    # Setup formatter
    if CONFIG_AVAILABLE:
        try:
            config = get_config()
            use_json = config.monitoring.log_format == "json"
        except Exception:
            use_json = is_production()
    else:
        use_json = False
    
    if use_json:
        formatter = StructuredLogFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
            defaults={'correlation_id': 'no-correlation'}
        )
    
    handler.setFormatter(formatter)
    
    # Add correlation ID filter
    correlation_filter = CorrelationIDFilter()
    handler.addFilter(correlation_filter)
    
    logger.addHandler(handler)
    
    return logger


def log_request_start(operation: str, **kwargs) -> str:
    """Log request start and return correlation ID."""
    correlation_id = generate_correlation_id()
    
    with correlation_context(
        correlation_id=correlation_id,
        operation=operation,
        **kwargs
    ):
        logger = get_structured_logger("request")
        logger.info(f"Request started: {operation}", extra={
            'extra_fields': {
                'event_type': 'request_start',
                'operation': operation,
                **kwargs
            }
        })
    
    return correlation_id


def log_request_end(correlation_id: str, success: bool = True, **kwargs):
    """Log request completion."""
    with correlation_context(correlation_id=correlation_id):
        logger = get_structured_logger("request")
        
        context = get_correlation_context()
        duration = None
        if context:
            duration = (time.time() - context.start_time) * 1000
        
        logger.info(
            f"Request {'completed' if success else 'failed'}: {context.operation if context else 'unknown'}",
            extra={
                'extra_fields': {
                    'event_type': 'request_end',
                    'success': success,
                    'duration_ms': round(duration, 2) if duration else None,
                    **kwargs
                }
            }
        )


class DatabaseLogger(PerformanceLoggerMixin):
    """Logger for database operations."""
    
    def __init__(self):
        self.logger = get_structured_logger("database")
    
    def log_query(self, query_type: str, table: str, duration_ms: float, rows_affected: int = 0):
        """Log database query."""
        self.logger.info(
            f"Database {query_type} on {table}: {rows_affected} rows in {duration_ms:.2f}ms",
            extra={
                'extra_fields': {
                    'event_type': 'database_query',
                    'query_type': query_type,
                    'table': table,
                    'duration_ms': round(duration_ms, 2),
                    'rows_affected': rows_affected
                }
            }
        )
    
    def log_connection_event(self, event_type: str, details: Dict[str, Any]):
        """Log database connection events."""
        self.logger.info(
            f"Database connection {event_type}",
            extra={
                'extra_fields': {
                    'event_type': f'database_{event_type}',
                    'details': details
                }
            }
        )


class ApplicationLogger(PerformanceLoggerMixin):
    """Logger for general application events."""
    
    def __init__(self):
        self.logger = get_structured_logger("application")
    
    def log_user_action(self, action: str, user_id: str, details: Dict[str, Any] = None):
        """Log user action."""
        self.logger.info(
            f"User action: {action} by {user_id}",
            extra={
                'extra_fields': {
                    'event_type': 'user_action',
                    'action': action,
                    'user_id': user_id,
                    'details': details or {}
                }
            }
        )
    
    def log_system_event(self, event_type: str, message: str, details: Dict[str, Any] = None):
        """Log system event."""
        self.logger.info(
            f"System event: {message}",
            extra={
                'extra_fields': {
                    'event_type': f'system_{event_type}',
                    'details': details or {}
                }
            }
        )
    
    def log_error(self, error: Exception, context: str = "", **kwargs):
        """Log application error with context."""
        self.logger.error(
            f"Application error in {context}: {error}",
            exc_info=True,
            extra={
                'extra_fields': {
                    'event_type': 'application_error',
                    'error_type': type(error).__name__,
                    'context': context,
                    **kwargs
                }
            }
        )


# Global logger instances
security_logger = SecurityEventLogger()
database_logger = DatabaseLogger()
application_logger = ApplicationLogger()


def setup_monitoring_integration():
    """Setup integration with monitoring systems."""
    if not CONFIG_AVAILABLE:
        return
    
    try:
        config = get_config()
        
        # Setup file logging for production
        if config.environment == "production" and not config.monitoring.log_file_path:
            log_dir = Path("/app/logs")
            log_dir.mkdir(exist_ok=True)
            config.monitoring.log_file_path = str(log_dir / "tdd_framework.log")
        
        # Setup root logger
        setup_structured_logging()
        
        logging.info("Structured logging initialized", extra={
            'extra_fields': {
                'event_type': 'logging_initialized',
                'environment': config.environment,
                'log_format': config.monitoring.log_format,
                'correlation_enabled': config.monitoring.enable_correlation_ids
            }
        })
        
    except Exception as e:
        logging.error(f"Failed to setup monitoring integration: {e}")


# Decorators for easy integration
def with_correlation(operation: str = None):
    """Decorator to add correlation tracking to functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            
            # Check if we're already in a correlation context
            existing_context = get_correlation_context()
            if existing_context:
                # Update operation if not set
                if not existing_context.operation:
                    update_correlation_context(operation=op_name)
                return func(*args, **kwargs)
            
            # Create new correlation context
            with correlation_context(operation=op_name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_performance(operation: str = None):
    """Decorator to log function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                
                logger = get_structured_logger("performance")
                logger.info(f"Performance: {op_name} completed in {duration:.2f}ms", extra={
                    'extra_fields': {
                        'event_type': 'performance',
                        'operation': op_name,
                        'duration_ms': round(duration, 2),
                        'success': True
                    }
                })
                
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                
                logger = get_structured_logger("performance")
                logger.error(f"Performance: {op_name} failed after {duration:.2f}ms", extra={
                    'extra_fields': {
                        'event_type': 'performance',
                        'operation': op_name,
                        'duration_ms': round(duration, 2),
                        'success': False,
                        'error': str(e)
                    }
                })
                raise
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test structured logging
    print("📊 Testing Structured Logging System")
    print("=" * 50)
    
    # Setup logging
    setup_structured_logging()
    
    # Test basic logging
    logger = get_structured_logger("test")
    
    with correlation_context(operation="test_operation", user_id="test_user"):
        logger.info("Test structured log message")
        logger.warning("Test warning with correlation")
        
        # Test performance logging
        with application_logger.performance_timer("test_timer"):
            time.sleep(0.1)
        
        # Test security logging
        security_logger.log_authentication_attempt("test_user", True)
        
        # Test database logging
        database_logger.log_query("SELECT", "framework_epics", 15.5, 10)
    
    print("✅ Structured logging system test completed")