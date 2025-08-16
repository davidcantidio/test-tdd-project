"""
📊 Monitoring Integration System

Complete integration system for structured logging, Prometheus metrics, and Grafana dashboards.
This module provides easy-to-use decorators and utilities for monitoring throughout the TDD Framework.

Features:
- Function performance monitoring decorators
- Database operation tracking
- User action logging
- Security event automation
- Prometheus metrics integration
- Streamlit performance tracking
- Error tracking and alerting
"""

import functools
import time
import traceback
import inspect
from typing import Callable, Dict, Any, Optional, List, Union
from contextlib import contextmanager
import threading
import psutil
import gc

from .structured_logger import (
    get_logger, 
    StructuredLogger, 
    LogLevel, 
    EventType,
    log_user_session,
    log_database_transaction,
    log_performance_metrics
)


class MonitoringDecorators:
    """Collection of monitoring decorators for easy integration."""
    
    @staticmethod
    def monitor_performance(component: str = None, operation: str = None,
                          log_args: bool = False, log_result: bool = False):
        """
        Decorator for monitoring function performance.
        
        Args:
            component: Component name (defaults to module name)
            operation: Operation name (defaults to function name)
            log_args: Whether to log function arguments
            log_result: Whether to log function result
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                logger = get_logger()
                
                # Get component and operation names
                comp_name = component or func.__module__.split('.')[-1]
                op_name = operation or func.__name__
                
                # Prepare extra data
                extra_data = {}
                if log_args:
                    extra_data["args"] = str(args)[:500]  # Limit size
                    extra_data["kwargs"] = {k: str(v)[:100] for k, v in kwargs.items()}
                
                # Monitor performance
                start_time = time.perf_counter()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Calculate performance metrics
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    memory_delta = end_memory - start_memory
                    
                    # Log result if requested
                    if log_result and result is not None:
                        extra_data["result_type"] = type(result).__name__
                        if hasattr(result, '__len__'):
                            extra_data["result_length"] = len(result)
                    
                    # Log performance event
                    logger.performance_event(
                        component=comp_name,
                        operation=op_name,
                        message=f"Function {op_name} completed successfully",
                        operation_duration_ms=duration_ms,
                        memory_usage_mb=memory_delta,
                        extra_data=extra_data
                    )
                    
                    return result
                    
                except Exception as e:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    
                    logger.error(
                        component=comp_name,
                        operation=op_name,
                        message=f"Function {op_name} failed",
                        exception=e,
                        extra_data={
                            **extra_data,
                            "duration_ms": duration_ms,
                            "error_type": type(e).__name__
                        }
                    )
                    raise
            
            return wrapper
        return decorator
    
    @staticmethod
    def monitor_database_operation(table: str = None, operation_type: str = None):
        """
        Decorator for monitoring database operations.
        
        Args:
            table: Database table name
            operation_type: Type of operation (create, read, update, delete)
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                logger = get_logger()
                
                # Determine table and operation
                table_name = table or "unknown"
                op_type = operation_type or func.__name__
                
                start_time = time.perf_counter()
                
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    
                    # Determine rows affected
                    rows_affected = None
                    if isinstance(result, (list, tuple)):
                        rows_affected = len(result)
                    elif isinstance(result, dict) and 'total' in result:
                        rows_affected = result['total']
                    elif isinstance(result, int):
                        rows_affected = 1 if result > 0 else 0
                    
                    logger.database_operation(
                        operation=op_type,
                        table=table_name,
                        duration_ms=duration_ms,
                        rows_affected=rows_affected
                    )
                    
                    return result
                    
                except Exception as e:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    
                    logger.error(
                        component="database",
                        operation=op_type,
                        message=f"Database operation failed on {table_name}",
                        exception=e,
                        extra_data={
                            "table": table_name,
                            "duration_ms": duration_ms
                        }
                    )
                    raise
            
            return wrapper
        return decorator
    
    @staticmethod
    def monitor_user_action(action_type: str = None, resource_type: str = None):
        """
        Decorator for monitoring user actions.
        
        Args:
            action_type: Type of action (create, update, delete, view)
            resource_type: Type of resource (client, project, epic, task)
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                logger = get_logger()
                context = logger.get_context()
                
                # Get user information from context
                user_id = context.get('user_id', 'anonymous')
                session_id = context.get('session_id')
                
                action = action_type or func.__name__
                resource = resource_type or "unknown"
                
                start_time = time.perf_counter()
                
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    
                    # Determine success
                    success = True
                    if isinstance(result, dict) and 'error' in result:
                        success = False
                    elif result is None or result is False:
                        success = False
                    
                    logger.user_action(
                        user_id=user_id,
                        action=action,
                        resource=resource,
                        success=success,
                        session_id=session_id,
                        duration_ms=duration_ms
                    )
                    
                    return result
                    
                except Exception as e:
                    logger.user_action(
                        user_id=user_id,
                        action=action,
                        resource=resource,
                        success=False,
                        session_id=session_id,
                        error=str(e)
                    )
                    raise
            
            return wrapper
        return decorator
    
    @staticmethod
    def monitor_security_event(event_category: str, severity: str = "medium"):
        """
        Decorator for monitoring security-sensitive operations.
        
        Args:
            event_category: Category of security event
            severity: Event severity (low, medium, high, critical)
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                logger = get_logger()
                context = logger.get_context()
                
                # Get security context
                ip_address = context.get('ip_address')
                user_id = context.get('user_id')
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Log successful security operation
                    logger.security_event(
                        component="security",
                        operation=func.__name__,
                        message=f"Security operation {func.__name__} completed",
                        event_category=event_category,
                        severity="low",  # Success = low severity
                        threat_detected=False,
                        blocked=False,
                        source_ip=ip_address
                    )
                    
                    return result
                    
                except Exception as e:
                    # Log security failure
                    logger.security_event(
                        component="security",
                        operation=func.__name__,
                        message=f"Security operation {func.__name__} failed: {str(e)}",
                        event_category=event_category,
                        severity=severity,
                        threat_detected=True,
                        blocked=True,
                        source_ip=ip_address
                    )
                    raise
            
            return wrapper
        return decorator


class StreamlitMonitoring:
    """Specialized monitoring for Streamlit applications."""
    
    def __init__(self):
        self.logger = get_logger()
        self.page_load_times = {}
        self.user_interactions = []
    
    def track_page_load(self, page_name: str):
        """Track page load time."""
        start_time = time.perf_counter()
        self.page_load_times[page_name] = start_time
        
        @contextmanager
        def page_timer():
            try:
                yield
            finally:
                load_time_ms = (time.perf_counter() - start_time) * 1000
                self.logger.performance_event(
                    component="streamlit",
                    operation="page_load",
                    message=f"Page {page_name} loaded",
                    operation_duration_ms=load_time_ms,
                    extra_data={"page_name": page_name}
                )
        
        return page_timer()
    
    def track_user_interaction(self, interaction_type: str, element: str, 
                             user_id: str = None):
        """Track user interaction with Streamlit elements."""
        interaction_data = {
            "timestamp": time.time(),
            "type": interaction_type,
            "element": element,
            "user_id": user_id or "anonymous"
        }
        
        self.user_interactions.append(interaction_data)
        
        self.logger.user_action(
            user_id=user_id or "anonymous",
            action=interaction_type,
            resource=element,
            success=True
        )
    
    def track_form_submission(self, form_name: str, success: bool, 
                            validation_errors: List[str] = None):
        """Track form submission events."""
        extra_data = {"form_name": form_name}
        if validation_errors:
            extra_data["validation_errors"] = validation_errors
        
        self.logger.user_action(
            user_id=self.logger.get_context().get('user_id', 'anonymous'),
            action="form_submission",
            resource=form_name,
            success=success,
            **extra_data
        )
    
    def get_user_interaction_stats(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get user interaction statistics."""
        cutoff_time = time.time() - (time_window_minutes * 60)
        recent_interactions = [
            i for i in self.user_interactions 
            if i["timestamp"] > cutoff_time
        ]
        
        stats = {
            "total_interactions": len(recent_interactions),
            "unique_users": len(set(i["user_id"] for i in recent_interactions)),
            "interaction_types": {},
            "elements": {}
        }
        
        for interaction in recent_interactions:
            # Count by type
            itype = interaction["type"]
            stats["interaction_types"][itype] = stats["interaction_types"].get(itype, 0) + 1
            
            # Count by element
            element = interaction["element"]
            stats["elements"][element] = stats["elements"].get(element, 0) + 1
        
        return stats


class SystemMetricsCollector:
    """Collect and log system performance metrics."""
    
    def __init__(self, collection_interval: int = 60):
        self.logger = get_logger()
        self.collection_interval = collection_interval
        self.collecting = False
        self.collector_thread = None
    
    def start_collection(self):
        """Start automatic metrics collection."""
        if self.collecting:
            return
        
        self.collecting = True
        self.collector_thread = threading.Thread(
            target=self._collection_loop,
            daemon=True
        )
        self.collector_thread.start()
        
        self.logger.info(
            component="monitoring",
            operation="start_metrics_collection",
            message=f"Started system metrics collection (interval: {self.collection_interval}s)"
        )
    
    def stop_collection(self):
        """Stop automatic metrics collection."""
        self.collecting = False
        if self.collector_thread:
            self.collector_thread.join(timeout=5)
        
        self.logger.info(
            component="monitoring",
            operation="stop_metrics_collection",
            message="Stopped system metrics collection"
        )
    
    def _collection_loop(self):
        """Main metrics collection loop."""
        while self.collecting:
            try:
                self.collect_and_log_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                self.logger.error(
                    component="monitoring",
                    operation="metrics_collection",
                    message="Error during metrics collection",
                    exception=e
                )
                time.sleep(self.collection_interval)
    
    def collect_and_log_metrics(self):
        """Collect current system metrics and log them."""
        try:
            # Get system metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            # Get process metrics
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Get thread count
            thread_count = threading.active_count()
            
            # Log performance metrics
            log_performance_metrics(
                memory_mb=process_memory,
                cpu_percent=cpu_percent,
                active_connections=0,  # Would be updated by database manager
                cache_hit_ratio=0.0    # Would be updated by cache system
            )
            
            # Log detailed system metrics
            self.logger.performance_event(
                component="system",
                operation="metrics_collection",
                message="System metrics collected",
                operation_duration_ms=0,
                memory_usage_mb=process_memory,
                cpu_usage_percent=cpu_percent,
                extra_data={
                    "system_memory_percent": memory.percent,
                    "system_memory_available_gb": memory.available / 1024 / 1024 / 1024,
                    "disk_usage_percent": disk.percent,
                    "disk_free_gb": disk.free / 1024 / 1024 / 1024,
                    "thread_count": thread_count
                }
            )
            
        except Exception as e:
            self.logger.error(
                component="monitoring",
                operation="collect_metrics",
                message="Failed to collect system metrics",
                exception=e
            )


class ErrorTracker:
    """Track and analyze application errors."""
    
    def __init__(self):
        self.logger = get_logger()
        self.error_counts = {}
        self.error_patterns = {}
    
    def track_error(self, error: Exception, context: Dict[str, Any] = None):
        """Track an application error with context."""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Update error counts
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Extract error pattern
        error_pattern = self._extract_error_pattern(error_message)
        if error_pattern:
            self.error_patterns[error_pattern] = self.error_patterns.get(error_pattern, 0) + 1
        
        # Log error with context
        extra_data = {
            "error_type": error_type,
            "error_count": self.error_counts[error_type],
            "stack_trace": traceback.format_exc()
        }
        
        if context:
            extra_data["context"] = context
        
        self.logger.error(
            component="error_tracker",
            operation="track_error",
            message=f"Application error tracked: {error_type}",
            exception=error,
            extra_data=extra_data
        )
    
    def _extract_error_pattern(self, error_message: str) -> str:
        """Extract pattern from error message for grouping."""
        # Remove specific values (numbers, IDs, timestamps)
        import re
        pattern = re.sub(r'\d+', '[NUMBER]', error_message)
        pattern = re.sub(r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b', '[UUID]', pattern)
        pattern = re.sub(r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\b', '[TIMESTAMP]', pattern)
        return pattern[:200]  # Limit length
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of tracked errors."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_types": self.error_counts.copy(),
            "top_patterns": dict(sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)[:10])
        }


# Global instances
_streamlit_monitoring = None
_metrics_collector = None
_error_tracker = None


def get_streamlit_monitoring() -> StreamlitMonitoring:
    """Get global Streamlit monitoring instance."""
    global _streamlit_monitoring
    if _streamlit_monitoring is None:
        _streamlit_monitoring = StreamlitMonitoring()
    return _streamlit_monitoring


def get_metrics_collector() -> SystemMetricsCollector:
    """Get global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = SystemMetricsCollector()
    return _metrics_collector


def get_error_tracker() -> ErrorTracker:
    """Get global error tracker instance."""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    return _error_tracker


def setup_monitoring(log_dir: str = "logs", metrics_port: int = 8000,
                    enable_metrics_collection: bool = True,
                    metrics_interval: int = 60):
    """
    Setup complete monitoring system.
    
    Args:
        log_dir: Directory for log files
        metrics_port: Port for Prometheus metrics server
        enable_metrics_collection: Whether to start automatic metrics collection
        metrics_interval: Metrics collection interval in seconds
    """
    # Setup structured logging
    from .structured_logger import setup_logging
    logger = setup_logging(log_dir, metrics_port)
    
    # Setup metrics collection
    if enable_metrics_collection:
        collector = get_metrics_collector()
        collector.collection_interval = metrics_interval
        collector.start_collection()
    
    # Log setup completion
    logger.info(
        component="monitoring",
        operation="setup_complete",
        message="Monitoring system setup completed",
        extra_data={
            "log_dir": log_dir,
            "metrics_port": metrics_port,
            "metrics_collection_enabled": enable_metrics_collection,
            "metrics_interval": metrics_interval
        }
    )
    
    return logger


# Export decorators for easy access
monitor_performance = MonitoringDecorators.monitor_performance
monitor_database = MonitoringDecorators.monitor_database_operation
monitor_user_action = MonitoringDecorators.monitor_user_action
monitor_security = MonitoringDecorators.monitor_security_event


# Context managers for easy integration
@contextmanager
def monitoring_context(user_id: str = None, session_id: str = None, 
                      ip_address: str = None, correlation_id: str = None):
    """Context manager for setting monitoring context."""
    logger = get_logger()
    
    context_data = {}
    if user_id:
        context_data['user_id'] = user_id
    if session_id:
        context_data['session_id'] = session_id
    if ip_address:
        context_data['ip_address'] = ip_address
    if correlation_id:
        context_data['correlation_id'] = correlation_id
    
    with logger.log_context(**context_data):
        yield logger


if __name__ == "__main__":
    # Example usage and testing
    
    # Setup monitoring
    logger = setup_monitoring("demo_logs", 8000, True, 30)
    
    # Example decorated function
    @monitor_performance("demo", "test_function", log_args=True)
    def example_function(x: int, y: str = "test") -> Dict[str, Any]:
        time.sleep(0.1)  # Simulate work
        return {"result": x * 2, "message": y}
    
    # Example database operation
    @monitor_database("users", "create")
    def create_user(name: str) -> int:
        time.sleep(0.05)  # Simulate database work
        return 123  # User ID
    
    # Example user action
    @monitor_user_action("create", "client")
    def create_client_action(client_data: Dict[str, Any]) -> bool:
        time.sleep(0.02)
        return True
    
    # Test with monitoring context
    with monitoring_context(user_id="demo_user", session_id="demo_session"):
        result = example_function(5, "hello")
        user_id = create_user("John Doe")
        success = create_client_action({"name": "ACME Corp"})
    
    # Test error tracking
    error_tracker = get_error_tracker()
    try:
        raise ValueError("Example error for testing")
    except ValueError as e:
        error_tracker.track_error(e, {"context": "demo"})
    
    # Test Streamlit monitoring
    streamlit_monitor = get_streamlit_monitoring()
    streamlit_monitor.track_user_interaction("button_click", "create_client_btn", "demo_user")
    
    print("Monitoring integration demo completed!")
    print("Check demo_logs/ directory for structured logs")
    print("Prometheus metrics available at http://localhost:8000")