"""
📊 Structured Logging System with Prometheus/Grafana Integration

Enterprise-grade logging system addressing report.md requirements:
- Structured JSON logging
- Correlation IDs for request tracing
- Performance metrics integration
- Prometheus metrics export
- Grafana dashboard compatibility
- Log aggregation and analysis
- Security event logging
- Error tracking and alerting

Features:
- Structured JSON format with metadata
- Performance timing integration
- Security event classification
- Correlation ID tracking
- Log level management
- Metrics collection for Prometheus
- Dashboard data preparation
- Log rotation and archival
"""

import logging
import logging.handlers
import json
import time
import uuid
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from pathlib import Path
import traceback
import os
import socket
from enum import Enum
import contextvars

request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)

# Prometheus metrics (optional dependency)
try:
    from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create mock classes for when prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def time(self): return MockTimer()
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
    
    def start_http_server(port): pass
    
    class MockTimer:
        def __enter__(self): return self
        def __exit__(self, *args): pass


class LogLevel(Enum):
    """Structured log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    """Event classification for structured logging."""
    APPLICATION = "application"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DATABASE = "database"
    API = "api"
    USER_ACTION = "user_action"
    SYSTEM = "system"
    ERROR = "error"


@dataclass
class LogContext:
    """Structured log context information."""
    correlation_id: str
    timestamp: str
    level: str
    event_type: str
    component: str
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class PerformanceData:
    """Performance metrics for logging."""
    operation_duration_ms: float
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    database_queries: Optional[int] = None
    cache_hits: Optional[int] = None
    cache_misses: Optional[int] = None


@dataclass
class SecurityData:
    """Security event data for logging."""
    event_category: str  # authentication, authorization, data_access, etc.
    severity: str  # low, medium, high, critical
    threat_detected: bool = False
    blocked: bool = False
    attack_type: Optional[str] = None
    source_ip: Optional[str] = None


class StructuredLogger:
    # Delegation to StructuredLoggerNetworking
    def __init__(self):
        self._structuredloggernetworking = StructuredLoggerNetworking()
    # Delegation to StructuredLoggerLogging
    def __init__(self):
        self._structuredloggerlogging = StructuredLoggerLogging()
    # Delegation to StructuredLoggerErrorhandling
    def __init__(self):
        self._structuredloggererrorhandling = StructuredLoggerErrorhandling()
    # Delegation to StructuredLoggerConfiguration
    def __init__(self):
        self._structuredloggerconfiguration = StructuredLoggerConfiguration()
    # Delegation to StructuredLoggerValidation
    def __init__(self):
        self._structuredloggervalidation = StructuredLoggerValidation()
    # Delegation to StructuredLoggerCaching
    def __init__(self):
        self._structuredloggercaching = StructuredLoggerCaching()
    # Delegation to StructuredLoggerFormatting
    def __init__(self):
        self._structuredloggerformatting = StructuredLoggerFormatting()
    # Delegation to StructuredLoggerDataaccess
    def __init__(self):
        self._structuredloggerdataaccess = StructuredLoggerDataaccess()
    # Delegation to StructuredLoggerSerialization
    def __init__(self):
        self._structuredloggerserialization = StructuredLoggerSerialization()
    # Delegation to StructuredLoggerUiinteraction
    def __init__(self):
        self._structuredloggeruiinteraction = StructuredLoggerUiinteraction()
    """Enterprise structured logging system."""
    
    def __init__(self, name: str = "tdd_framework", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # System information
        self.hostname = socket.gethostname()
        self.process_id = os.getpid()
        
        # Thread-local storage for context
        self._local = threading.local()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize Prometheus metrics
        self._setup_prometheus_metrics()
        
    def _setup_logging(self):
        """Setup structured logging configuration."""
        # Create custom formatter
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler for structured logs
        log_file = self.log_dir / "application.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(file_handler)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(console_handler)
        
        # Separate error log
        error_file = self.log_dir / "errors.log"
        error_handler = logging.FileHandler(error_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(error_handler)
        
        # Security events log
        security_file = self.log_dir / "security.log"
        self.security_handler = logging.FileHandler(security_file)
        self.security_handler.setFormatter(StructuredFormatter())
        
        # Performance metrics log
        performance_file = self.log_dir / "performance.log"
        self.performance_handler = logging.FileHandler(performance_file)
        self.performance_handler.setFormatter(StructuredFormatter())
    
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics for monitoring."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        # Application metrics
        self.request_count = Counter(
            'tdd_framework_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'tdd_framework_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )
        
        self.error_count = Counter(
            'tdd_framework_errors_total',
            'Total number of errors',
            ['component', 'error_type']
        )
        
        self.active_sessions = Gauge(
            'tdd_framework_active_sessions',
            'Number of active user sessions'
        )
        
        self.database_connections = Gauge(
            'tdd_framework_database_connections',
            'Number of active database connections'
        )
        
        self.cache_hit_ratio = Gauge(
            'tdd_framework_cache_hit_ratio',
            'Cache hit ratio'
        )
        
        # Security metrics
        self.security_events = Counter(
            'tdd_framework_security_events_total',
            'Total security events',
            ['event_type', 'severity']
        )
        
        self.authentication_attempts = Counter(
            'tdd_framework_auth_attempts_total',
            'Authentication attempts',
            ['status', 'method']
        )
        
        # Performance metrics
        self.memory_usage = Gauge(
            'tdd_framework_memory_usage_bytes',
            'Memory usage in bytes'
        )
        
        self.cpu_usage = Gauge(
            'tdd_framework_cpu_usage_percent',
            'CPU usage percentage'
        )
        
        # System info
        self.app_info = Info(
            'tdd_framework_info',
            'Application information'
        )
        self.app_info.info({
            'version': '2.4.0',
            'hostname': self.hostname,
            'process_id': str(self.process_id)
        })
    
    def set_context(self, **kwargs):
        """Set logging context for current thread."""
        if not hasattr(self._local, 'context'):
            self._local.context = {}
        self._local.context.update(kwargs)
    
    def get_context(self) -> Dict[str, Any]:
        """Get current logging context."""
        if not hasattr(self._local, 'context'):
            self._local.context = {}
        return self._local.context.copy()
    
    def clear_context(self):
        """Clear logging context for current thread."""
        if hasattr(self._local, 'context'):
            self._local.context.clear()
    
    @contextmanager
    def log_context(self, **kwargs):
        """Context manager for temporary logging context."""
        original_context = self.get_context()
        self.set_context(**kwargs)
        try:
            yield
        finally:
            self.clear_context()
            self.set_context(**original_context)
    
    def _create_log_entry(self, level: LogLevel, event_type: EventType, 
                         component: str, operation: str, message: str,
                         extra_data: Optional[Dict[str, Any]] = None,
                         performance_data: Optional[PerformanceData] = None,
                         security_data: Optional[SecurityData] = None,
                         exception: Optional[Exception] = None) -> Dict[str, Any]:
        """Create structured log entry."""
        
        # Get context
        context = self.get_context()
        correlation_id = context.get('correlation_id', str(uuid.uuid4()))
        
        # Create log context
        log_context = LogContext(
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level.value,
            event_type=event_type.value,
            component=component,
            operation=operation,
            user_id=context.get('user_id'),
            session_id=context.get('session_id'),
            request_id=context.get('request_id'),
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
        
        # Build log entry
        log_entry = {
            "context": asdict(log_context),
            "message": message,
            "hostname": self.hostname,
            "process_id": self.process_id,
            "thread_id": threading.get_ident()
        }
        
        # Add extra data
        if extra_data:
            log_entry["data"] = extra_data
        
        # Add performance data
        if performance_data:
            log_entry["performance"] = asdict(performance_data)
        
        # Add security data
        if security_data:
            log_entry["security"] = asdict(security_data)
        
        # Add exception details
        if exception:
            log_entry["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
                "traceback": traceback.format_exc()
            }
        
        return log_entry
    
    def log(self, level: LogLevel, event_type: EventType, component: str, 
            operation: str, message: str, **kwargs):
        """Generic structured logging method."""
        
        log_entry = self._create_log_entry(
            level, event_type, component, operation, message, **kwargs
        )
        
        # Log to appropriate handler
        if event_type == EventType.SECURITY and hasattr(self, 'security_handler'):
            security_logger = logging.getLogger(f"{self.name}.security")
            security_logger.addHandler(self.security_handler)
            security_logger.log(getattr(logging, level.value), json.dumps(log_entry))
        elif event_type == EventType.PERFORMANCE and hasattr(self, 'performance_handler'):
            perf_logger = logging.getLogger(f"{self.name}.performance")
            perf_logger.addHandler(self.performance_handler)
            perf_logger.log(getattr(logging, level.value), json.dumps(log_entry))
        else:
            self.logger.log(getattr(logging, level.value), json.dumps(log_entry))
        
        # Update Prometheus metrics
        self._update_prometheus_metrics(level, event_type, log_entry)
        
        return log_entry
    
    def _update_prometheus_metrics(self, level: LogLevel, event_type: EventType, log_entry: Dict[str, Any]):
        """Update Prometheus metrics based on log entry."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        # Error counting
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            component = log_entry["context"]["component"]
            self.error_count.labels(component=component, error_type=level.value).inc()
        
        # Security events
        if event_type == EventType.SECURITY and "security" in log_entry:
            security_data = log_entry["security"]
            self.security_events.labels(
                event_type=security_data.get("event_category", "unknown"),
                severity=security_data.get("severity", "unknown")
            ).inc()
        
        # Performance metrics
        if "performance" in log_entry:
            perf_data = log_entry["performance"]
            if "memory_usage_mb" in perf_data and perf_data["memory_usage_mb"]:
                self.memory_usage.set(perf_data["memory_usage_mb"] * 1024 * 1024)  # Convert to bytes
    
    # Convenience methods
    def debug(self, component: str, operation: str, message: str, **kwargs):
        """Log debug message."""
        return self.log(LogLevel.DEBUG, EventType.APPLICATION, component, operation, message, **kwargs)
    
    def info(self, component: str, operation: str, message: str, **kwargs):
        """Log info message."""
        return self.log(LogLevel.INFO, EventType.APPLICATION, component, operation, message, **kwargs)
    
    def warning(self, component: str, operation: str, message: str, **kwargs):
        """Log warning message."""
        return self.log(LogLevel.WARNING, EventType.APPLICATION, component, operation, message, **kwargs)
    
    def error(self, component: str, operation: str, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message."""
        return self.log(LogLevel.ERROR, EventType.ERROR, component, operation, message, exception=exception, **kwargs)
    
    def critical(self, component: str, operation: str, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message."""
        return self.log(LogLevel.CRITICAL, EventType.ERROR, component, operation, message, exception=exception, **kwargs)
    
    def security_event(self, component: str, operation: str, message: str, 
                      event_category: str, severity: str, **kwargs):
        """Log security event."""
        security_data = SecurityData(
            event_category=event_category,
            severity=severity,
            **{k: v for k, v in kwargs.items() if k in ['threat_detected', 'blocked', 'attack_type', 'source_ip']}
        )
        
        return self.log(
            LogLevel.WARNING if severity in ['low', 'medium'] else LogLevel.ERROR,
            EventType.SECURITY,
            component,
            operation,
            message,
            security_data=security_data
        )
    
    def performance_event(self, component: str, operation: str, message: str,
                         operation_duration_ms: float, **kwargs):
        """Log performance event."""
        # Separate performance data from extra data
        perf_fields = ['memory_usage_mb', 'cpu_usage_percent', 'database_queries', 'cache_hits', 'cache_misses']
        performance_kwargs = {k: v for k, v in kwargs.items() if k in perf_fields}
        extra_data = {k: v for k, v in kwargs.items() if k not in perf_fields}
        
        performance_data = PerformanceData(
            operation_duration_ms=operation_duration_ms,
            **performance_kwargs
        )
        
        return self.log(
            LogLevel.INFO,
            EventType.PERFORMANCE,
            component,
            operation,
            message,
            performance_data=performance_data,
            extra_data=extra_data if extra_data else None
        )
    
    @contextmanager
    def performance_timer(self, component: str, operation: str, message: str = None):
        """Context manager for timing operations."""
        start_time = time.perf_counter()
        
        # Prometheus timing
        if PROMETHEUS_AVAILABLE:
            timer = self.request_duration.labels(method=operation, endpoint=component).time()
            timer.__enter__()
        
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            if PROMETHEUS_AVAILABLE:
                timer.__exit__(None, None, None)
            
            self.performance_event(
                component=component,
                operation=operation,
                message=message or f"{operation} completed",
                operation_duration_ms=duration_ms
            )
    
    def database_operation(self, operation: str, table: str, duration_ms: float, 
                          rows_affected: Optional[int] = None):
        """Log database operation."""
        extra_data = {"table": table}
        if rows_affected is not None:
            extra_data["rows_affected"] = rows_affected
        
        return self.performance_event(
            component="database",
            operation=operation,
            message=f"Database {operation} on {table}",
            operation_duration_ms=duration_ms,
            database_queries=1,
            extra_data=extra_data
        )
    
    def api_request(self, method: str, endpoint: str, status_code: int, 
                   duration_ms: float, user_id: Optional[str] = None):
        """Log API request."""
        
        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            self.request_count.labels(method=method, endpoint=endpoint, status=status_code).inc()
        
        level = LogLevel.INFO if status_code < 400 else LogLevel.WARNING if status_code < 500 else LogLevel.ERROR
        
        extra_data = {
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "user_id": user_id
        }
        
        return self.performance_event(
            component="api",
            operation="request",
            message=f"{method} {endpoint} -> {status_code}",
            operation_duration_ms=duration_ms,
            extra_data=extra_data
        )
    
    def user_action(self, user_id: str, action: str, resource: str, 
                   success: bool = True, **kwargs):
        """Log user action."""
        level = LogLevel.INFO if success else LogLevel.WARNING
        
        extra_data = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "success": success,
            **kwargs
        }
        
        return self.log(
            level=level,
            event_type=EventType.USER_ACTION,
            component="user_interface",
            operation=action,
            message=f"User {user_id} {action} {resource}",
            extra_data=extra_data
        )
    
    def start_metrics_server(self, port: int = 8000):
        """Start Prometheus metrics HTTP server."""
        if PROMETHEUS_AVAILABLE:
            start_http_server(port)
            self.info(
                component="monitoring",
                operation="start_metrics_server",
                message=f"Prometheus metrics server started on port {port}",
                extra_data={"port": port}
            )
        else:
            self.warning(
                component="monitoring",
                operation="start_metrics_server", 
                message="Prometheus not available, metrics server not started"
            )


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logs."""
    
    def format(self, record):
        # If the message is already JSON (from structured logger), return as-is
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            try:
                json.loads(record.msg)
                return record.msg
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Otherwise format as structured log
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": request_id_ctx.get(),
        }
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


# Global logger instance
_logger_instance: Optional[StructuredLogger] = None


def get_logger(name: str = "tdd_framework") -> StructuredLogger:
    """Get global structured logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StructuredLogger(name)
    return _logger_instance


def setup_logging(log_dir: str = "logs", metrics_port: Optional[int] = None):
    """Setup global structured logging."""
    global _logger_instance
    _logger_instance = StructuredLogger("tdd_framework", log_dir)
    
    if metrics_port and PROMETHEUS_AVAILABLE:
        _logger_instance.start_metrics_server(metrics_port)
    
    return _logger_instance


# Context managers for common logging patterns
@contextmanager
def log_user_session(user_id: str, session_id: str, ip_address: str = None):
    """Context manager for user session logging."""
    logger = get_logger()
    correlation_id = str(uuid.uuid4())
    
    with logger.log_context(
        correlation_id=correlation_id,
        user_id=user_id,
        session_id=session_id,
        ip_address=ip_address
    ):
        logger.info(
            component="authentication",
            operation="session_start",
            message=f"User session started for {user_id}",
            extra_data={"session_id": session_id}
        )
        
        try:
            yield logger
        finally:
            logger.info(
                component="authentication",
                operation="session_end", 
                message=f"User session ended for {user_id}",
                extra_data={"session_id": session_id}
            )


@contextmanager
def log_database_transaction(operation: str, tables: List[str]):
    """Context manager for database transaction logging."""
    logger = get_logger()
    start_time = time.perf_counter()
    
    logger.info(
        component="database",
        operation="transaction_start",
        message=f"Database transaction started: {operation}",
        extra_data={"tables": tables, "operation": operation}
    )
    
    try:
        yield logger
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.performance_event(
            component="database",
            operation="transaction_complete",
            message=f"Database transaction completed: {operation}",
            operation_duration_ms=duration_ms,
            extra_data={"tables": tables, "success": True}
        )
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            component="database",
            operation="transaction_failed",
            message=f"Database transaction failed: {operation}",
            exception=e,
            extra_data={"tables": tables, "duration_ms": duration_ms}
        )
        raise


# Example usage and integration functions
def log_performance_metrics(memory_mb: float, cpu_percent: float, 
                           active_connections: int, cache_hit_ratio: float):
    """Log current performance metrics."""
    logger = get_logger()
    
    # Update Prometheus gauges
    if PROMETHEUS_AVAILABLE:
        logger.memory_usage.set(memory_mb * 1024 * 1024)
        logger.cpu_usage.set(cpu_percent)
        logger.database_connections.set(active_connections)
        logger.cache_hit_ratio.set(cache_hit_ratio)
    
    logger.performance_event(
        component="system",
        operation="metrics_collection",
        message="System performance metrics collected",
        operation_duration_ms=0,  # Instantaneous measurement
        memory_usage_mb=memory_mb,
        cpu_usage_percent=cpu_percent,
        extra_data={
            "active_connections": active_connections,
            "cache_hit_ratio": cache_hit_ratio
        }
    )


if __name__ == "__main__":
    # Example usage
    logger = setup_logging("demo_logs", metrics_port=8000)
    
    # Application logging
    logger.info("application", "startup", "TDD Framework starting up")
    
    # Performance logging with timer
    with logger.performance_timer("database", "project_query"):
        time.sleep(0.1)  # Simulate work
    
    # Security event
    logger.security_event(
        component="authentication",
        operation="login_attempt",
        message="Failed login attempt detected",
        event_category="authentication",
        severity="medium",
        threat_detected=True,
        source_ip="192.168.1.100"
    )
    
    # User action logging
    with log_user_session("user123", "session456", "192.168.1.50"):
        logger.user_action("user123", "create_project", "project_form", success=True)
    
    logging.info("Structured logging demo completed!")
    logging.info("Check demo_logs/ directory for log files")
    if PROMETHEUS_AVAILABLE:
        logging.info("Prometheus metrics available at http://localhost:8000")
