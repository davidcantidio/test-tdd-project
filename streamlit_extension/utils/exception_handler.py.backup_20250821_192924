"""
🛡️ Global Exception Handler for Streamlit Applications

Comprehensive exception handling system that prevents raw error messages from reaching the UI
and provides structured error logging with security considerations.

Features:
- Global exception catching for all Streamlit operations
- Sanitized error messages for users
- Comprehensive error logging for developers
- Security-aware error handling (no sensitive data leakage)
- Integration with existing security framework
- Production-ready error recovery
"""

import sys
import time
import traceback
import functools
import threading
from collections import deque
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple, Union
from datetime import datetime
from contextlib import contextmanager

# Add duration_system to path for security module
sys.path.append(str(Path(__file__).parent.parent.parent / "duration_system"))

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    
    # Mock streamlit for testing
    class MockStreamlit:
        def __getattr__(self, name):
            def mock_func(*args, **kwargs):
                return None
            return mock_func
    st = MockStreamlit()

try:
    from log_sanitization import create_secure_logger, sanitize_log_message, sanitize_exception
    LOG_SANITIZATION_AVAILABLE = True
except ImportError:
    LOG_SANITIZATION_AVAILABLE = False
    create_secure_logger = sanitize_log_message = sanitize_exception = None

try:
    from .security import security_manager, sanitize_display
    SECURITY_MANAGER_AVAILABLE = True
except ImportError:
    SECURITY_MANAGER_AVAILABLE = False
    security_manager = None
    sanitize_display = lambda x, **kwargs: str(x)


class ErrorSeverity:
    """Error severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM" 
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ErrorCategory:
    """Error categories for better classification."""
    DATABASE = "DATABASE"
    AUTHENTICATION = "AUTHENTICATION"
    VALIDATION = "VALIDATION"
    NETWORK = "NETWORK"
    FILE_SYSTEM = "FILE_SYSTEM"
    SECURITY = "SECURITY"
    USER_INPUT = "USER_INPUT"
    BUSINESS_LOGIC = "BUSINESS_LOGIC"
    SYSTEM = "SYSTEM"
    UNKNOWN = "UNKNOWN"


class StreamlitError:
    """Structured error information for Streamlit applications."""
    
    def __init__(self, 
                 exception: Exception,
                 severity: str = ErrorSeverity.MEDIUM,
                 category: str = ErrorCategory.UNKNOWN,
                 user_message: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None,
                 suggestions: Optional[List[str]] = None):
        self.exception = exception
        self.severity = severity
        self.category = category
        self.timestamp = datetime.now()
        self.user_message = user_message or self._generate_user_message()
        self.context = context or {}
        self.suggestions = suggestions or []
        self.error_id = self._generate_error_id()
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID for tracking."""
        import hashlib
        error_data = f"{self.timestamp.isoformat()}_{type(self.exception).__name__}_{str(self.exception)[:100]}"
        return hashlib.sha256(error_data.encode()).hexdigest()[:12]
    
    def _generate_user_message(self) -> str:
        """Generate user-friendly error message."""
        exception_type = type(self.exception).__name__
        
        # Map common exceptions to user-friendly messages
        user_messages = {
            "sqlite3.OperationalError": "Database temporarily unavailable. Please try again in a moment.",
            "sqlite3.DatabaseError": "Database error occurred. Please refresh the page.",
            "ConnectionError": "Network connection issue. Please check your internet connection.",
            "FileNotFoundError": "Required file not found. Please contact support.",
            "PermissionError": "Permission denied. Please contact an administrator.",
            "ValueError": "Invalid input provided. Please check your data and try again.",
            "KeyError": "Missing required information. Please complete all fields.",
            "ImportError": "System configuration issue. Please contact support.",
            "TimeoutError": "Operation timed out. Please try again.",
            "MemoryError": "System resources low. Please try again later.",
            "OSError": "System error occurred. Please try again or contact support."
        }
        
        # Check for specific exception types
        for exc_pattern, message in user_messages.items():
            if exc_pattern in str(type(self.exception)):
                return message
        
        # Fallback message
        return "An unexpected error occurred. Please try again or contact support if the problem persists."
    
    def get_safe_context(self) -> Dict[str, Any]:
        """Get sanitized context safe for logging."""
        safe_context = {}
        
        for key, value in self.context.items():
            if isinstance(value, str):
                # Sanitize string values with length limit
                sanitized = sanitize_display(value, max_length=200)
                # Ensure it doesn't exceed 200 characters
                safe_context[key] = sanitized[:200] if len(sanitized) > 200 else sanitized
            elif isinstance(value, (int, float, bool)):
                safe_context[key] = value
            elif isinstance(value, (list, tuple)) and len(value) < 10:
                # Small collections only
                safe_context[key] = [sanitize_display(str(item), max_length=50) for item in value]
            else:
                # For complex objects, just include type info
                safe_context[key] = f"<{type(value).__name__}>"
        
        return safe_context


class GlobalExceptionHandler:
    # Delegation to GlobalExceptionHandlerUiinteraction
    def __init__(self):
        self._globalexceptionhandleruiinteraction = GlobalExceptionHandlerUiinteraction()
    # Delegation to GlobalExceptionHandlerValidation
    def __init__(self):
        self._globalexceptionhandlervalidation = GlobalExceptionHandlerValidation()
    # Delegation to GlobalExceptionHandlerLogging
    def __init__(self):
        self._globalexceptionhandlerlogging = GlobalExceptionHandlerLogging()
    # Delegation to GlobalExceptionHandlerErrorhandling
    def __init__(self):
        self._globalexceptionhandlererrorhandling = GlobalExceptionHandlerErrorhandling()
    # Delegation to GlobalExceptionHandlerNetworking
    def __init__(self):
        self._globalexceptionhandlernetworking = GlobalExceptionHandlerNetworking()
    # Delegation to GlobalExceptionHandlerFormatting
    def __init__(self):
        self._globalexceptionhandlerformatting = GlobalExceptionHandlerFormatting()
    # Delegation to GlobalExceptionHandlerDataaccess
    def __init__(self):
        self._globalexceptionhandlerdataaccess = GlobalExceptionHandlerDataaccess()
    # Delegation to GlobalExceptionHandlerCalculation
    def __init__(self):
        self._globalexceptionhandlercalculation = GlobalExceptionHandlerCalculation()
    """Global exception handler for Streamlit applications."""
    
    def __init__(self):
        """Initialize the global exception handler."""
        # Initialize secure logging
        if LOG_SANITIZATION_AVAILABLE:
            self.logger = create_secure_logger('streamlit_exceptions')
        else:
            import logging
            self.logger = logging.getLogger('streamlit_exceptions')
            self.logger.setLevel(logging.ERROR)
            
            # Create console handler if none exists
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
        
        # Error statistics
        self.error_stats = {
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {},
            "recent_errors": deque(maxlen=100),
            "last_reset": time.time()
        }
        
        # Error recovery strategies
        self.recovery_strategies = {}
        self._setup_default_recovery_strategies()
        
        # Thread lock for stats
        self._stats_lock = threading.Lock()
        
    def _setup_default_recovery_strategies(self):
        """Setup default error recovery strategies."""
        self.recovery_strategies = {
            ErrorCategory.DATABASE: self._recover_database_error,
            ErrorCategory.AUTHENTICATION: self._recover_auth_error,
            ErrorCategory.VALIDATION: self._recover_validation_error,
            ErrorCategory.NETWORK: self._recover_network_error,
            ErrorCategory.FILE_SYSTEM: self._recover_filesystem_error,
            ErrorCategory.SECURITY: self._recover_security_error,
            ErrorCategory.USER_INPUT: self._recover_user_input_error,
            ErrorCategory.BUSINESS_LOGIC: self._recover_business_logic_error,
            ErrorCategory.SYSTEM: self._recover_system_error
        }
    
    def classify_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """
        Classify exception by category and severity.
        
        Args:
            exception: The exception to classify
            context: Optional context information
            
        Returns:
            Tuple of (category, severity)
        """
        exception_type = type(exception).__name__
        exception_str = str(exception).lower()
        
        # Security-related errors
        if any(keyword in exception_str for keyword in [
            'authentication', 'authorization', 'csrf', 'security', 'forbidden',
            'permission denied', 'access denied', 'unauthorized'
        ]):
            return ErrorCategory.SECURITY, ErrorSeverity.HIGH
        
        # Database errors
        if any(keyword in exception_type.lower() for keyword in [
            'database', 'sqlite', 'operational', 'integrity'
        ]):
            # Database locks are high severity
            if 'locked' in exception_str or 'busy' in exception_str:
                return ErrorCategory.DATABASE, ErrorSeverity.HIGH
            return ErrorCategory.DATABASE, ErrorSeverity.MEDIUM
        
        # Authentication errors
        if any(keyword in exception_str for keyword in [
            'login', 'oauth', 'token', 'credentials', 'authenticate'
        ]):
            return ErrorCategory.AUTHENTICATION, ErrorSeverity.MEDIUM
        
        # Validation errors
        if exception_type in ['ValueError', 'ValidationError', 'TypeError']:
            return ErrorCategory.VALIDATION, ErrorSeverity.LOW
        
        # Network errors
        if any(keyword in exception_type.lower() for keyword in [
            'connection', 'timeout', 'network', 'http', 'url'
        ]):
            return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM
        
        # File system errors
        if any(keyword in exception_type.lower() for keyword in [
            'file', 'directory', 'path', 'io', 'os'
        ]):
            return ErrorCategory.FILE_SYSTEM, ErrorSeverity.MEDIUM
        
        # Memory/system errors
        if exception_type in ['MemoryError', 'SystemError', 'OSError']:
            return ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL
        
        # Import errors
        if exception_type == 'ImportError':
            return ErrorCategory.SYSTEM, ErrorSeverity.HIGH
        
        # Default classification
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM
    
    def handle_exception(self,
                        exception: Exception,
                        context: Optional[Dict[str, Any]] = None,
                        show_user_message: bool = True,
                        attempt_recovery: bool = True) -> StreamlitError:
        """
        Handle an exception with comprehensive error processing.
        
        Args:
            exception: The exception to handle
            context: Optional context information
            show_user_message: Whether to show user-friendly message in UI
            attempt_recovery: Whether to attempt automatic recovery
            
        Returns:
            StreamlitError object with processed error information
        """
        try:
            # Classify the error
            category, severity = self.classify_exception(exception, context)
            
            # Create structured error
            error = StreamlitError(
                exception=exception,
                severity=severity,
                category=category,
                context=context or {}
            )
            
            # Update statistics
            self._update_error_stats(error)
            
            # Log the error
            self._log_error(error)
            
            # Show user message if requested
            if show_user_message and STREAMLIT_AVAILABLE:
                self._show_user_error(error)
            
            # Attempt recovery if requested
            if attempt_recovery:
                self._attempt_recovery(error)
            
            return error
            
        except Exception as e:
            # Fallback error handling to prevent recursive errors
            self.logger.error(f"Exception in exception handler: {e}")
            if STREAMLIT_AVAILABLE:
                st.error("🚨 A critical error occurred. Please refresh the page.")
            
            # Return minimal error object
            return StreamlitError(exception=exception)
    
    def _update_error_stats(self, error: StreamlitError):
        """Update error statistics."""
        with self._stats_lock:
            self.error_stats["total_errors"] += 1
            
            # Update category stats
            category_stats = self.error_stats["errors_by_category"]
            category_stats[error.category] = category_stats.get(error.category, 0) + 1
            
            # Update severity stats
            severity_stats = self.error_stats["errors_by_severity"]
            severity_stats[error.severity] = severity_stats.get(error.severity, 0) + 1
            
            # Add to recent errors (deque handles max size)
            recent: Deque[Dict[str, Any]] = self.error_stats["recent_errors"]
            recent.append({
                "error_id": error.error_id,
                "category": error.category,
                "severity": error.severity,
                "timestamp": error.timestamp.isoformat(),
                "message": str(error.exception)[:100]
            })
    
    def _log_error(self, error: StreamlitError):
        """Log error with appropriate level."""
        safe_context = error.get_safe_context()
        
        # Create log message
        log_data = {
            "error_id": error.error_id,
            "category": error.category,
            "severity": error.severity,
            "exception_type": type(error.exception).__name__,
            "message": str(error.exception)[:500],  # Truncate long messages
            "context": safe_context
        }
        
        # Log with appropriate level based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            if LOG_SANITIZATION_AVAILABLE:
                self.logger.critical(sanitize_log_message(f"Critical error: {log_data}", 'CRITICAL'))
            else:
                self.logger.critical(f"Critical error: {log_data}")
        elif error.severity == ErrorSeverity.HIGH:
            if LOG_SANITIZATION_AVAILABLE:
                self.logger.error(sanitize_log_message(f"High severity error: {log_data}", 'ERROR'))
            else:
                self.logger.error(f"High severity error: {log_data}")
        elif error.severity == ErrorSeverity.MEDIUM:
            if LOG_SANITIZATION_AVAILABLE:
                self.logger.warning(sanitize_log_message(f"Medium severity error: {log_data}", 'WARNING'))
            else:
                self.logger.warning(f"Medium severity error: {log_data}")
        else:  # LOW
            if LOG_SANITIZATION_AVAILABLE:
                self.logger.info(sanitize_log_message(f"Low severity error: {log_data}", 'INFO'))
            else:
                self.logger.info(f"Low severity error: {log_data}")
        
        # Also log full traceback for debugging (sanitized)
        if LOG_SANITIZATION_AVAILABLE:
            full_traceback = traceback.format_exc()
            try:
                sanitized_traceback = sanitize_exception(error.exception)
            except Exception:
                # Fallback if sanitize_exception fails
                sanitized_traceback = str(error.exception)[:500]
            self.logger.debug(f"Full traceback for {error.error_id}: {sanitized_traceback}")
        else:
            self.logger.debug(f"Full traceback for {error.error_id}: {traceback.format_exc()}")
    
    def _show_user_error(self, error: StreamlitError):
        """Show user-friendly error message in Streamlit UI."""
        if not STREAMLIT_AVAILABLE:
            return
        
        # Choose appropriate Streamlit method based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            st.error(f"🚨 {error.user_message}")
            st.error(f"Error ID: {error.error_id} (Please share this with support)")
        elif error.severity == ErrorSeverity.HIGH:
            st.error(f"❌ {error.user_message}")
            with st.expander("Error Details", expanded=False):
                st.code(f"Error ID: {error.error_id}")
                if error.suggestions:
                    st.markdown("**Suggestions:**")
                    for suggestion in error.suggestions:
                        st.markdown(f"• {suggestion}")
        elif error.severity == ErrorSeverity.MEDIUM:
            st.warning(f"⚠️ {error.user_message}")
            if error.suggestions:
                with st.expander("Suggestions", expanded=False):
                    for suggestion in error.suggestions:
                        st.markdown(f"• {suggestion}")
        else:  # LOW
            st.info(f"ℹ️ {error.user_message}")
    
    def _attempt_recovery(self, error: StreamlitError):
        """Attempt automatic error recovery."""
        recovery_func = self.recovery_strategies.get(error.category)
        if recovery_func:
            try:
                recovery_func(error)
            except Exception as e:
                self.logger.warning(f"Recovery failed for {error.error_id}: {e}")
    
    # Recovery strategy implementations
    def _recover_database_error(self, error: StreamlitError):
        """Attempt database error recovery."""
        if "locked" in str(error.exception).lower():
            # Database lock - suggest retry
            error.suggestions.append("The database is busy. Please wait a moment and try again.")
            error.suggestions.append("If the problem persists, try refreshing the page.")
        elif "no such table" in str(error.exception).lower():
            error.suggestions.append("Database schema may be outdated. Please contact support.")
        else:
            error.suggestions.append("Database connectivity issue. Please try again.")
    
    def _recover_auth_error(self, error: StreamlitError):
        """Attempt authentication error recovery."""
        error.suggestions.append("Please log out and log back in.")
        error.suggestions.append("Clear your browser cookies if the problem persists.")
    
    def _recover_validation_error(self, error: StreamlitError):
        """Attempt validation error recovery."""
        error.suggestions.append("Please check your input and try again.")
        error.suggestions.append("Ensure all required fields are filled correctly.")
    
    def _recover_network_error(self, error: StreamlitError):
        """Attempt network error recovery."""
        error.suggestions.append("Check your internet connection.")
        error.suggestions.append("Try refreshing the page.")
    
    def _recover_filesystem_error(self, error: StreamlitError):
        """Attempt file system error recovery."""
        error.suggestions.append("File system error occurred.")
        error.suggestions.append("Please contact support if this persists.")
    
    def _recover_security_error(self, error: StreamlitError):
        """Attempt security error recovery."""
        error.suggestions.append("Security check failed.")
        error.suggestions.append("Please refresh the page and try again.")
        error.suggestions.append("Contact support if you believe this is an error.")
    
    def _recover_user_input_error(self, error: StreamlitError):
        """Attempt user input error recovery."""
        error.suggestions.append("Please check your input format.")
        error.suggestions.append("Ensure all fields contain valid data.")
    
    def _recover_business_logic_error(self, error: StreamlitError):
        """Attempt business logic error recovery."""
        error.suggestions.append("Business rule validation failed.")
        error.suggestions.append("Please review your data and try again.")
    
    def _recover_system_error(self, error: StreamlitError):
        """Attempt system error recovery."""
        error.suggestions.append("System error occurred.")
        error.suggestions.append("Please try again or contact support.")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        with self._stats_lock:
            return self.error_stats.copy()
    
    def reset_error_stats(self):
        """Reset error statistics."""
        with self._stats_lock:
            self.error_stats = {
                "total_errors": 0,
                "errors_by_category": {},
                "errors_by_severity": {},
                "recent_errors": [],
                "last_reset": time.time()
            }
    
    def install_global_handler(self):
        """Install global exception handler for the current thread."""
        def handle_exception(exc_type, exc_value, exc_traceback):
            """Global exception handler function."""
            if issubclass(exc_type, KeyboardInterrupt):
                # Don't handle keyboard interrupts
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # Handle the exception
            self.handle_exception(exc_value, context={
                "exc_type": exc_type.__name__,
                "traceback_length": len(traceback.format_tb(exc_traceback))
            })
        
        # Install as global exception handler
        sys.excepthook = handle_exception


# Decorator for automatic exception handling
def handle_streamlit_exceptions(show_error: bool = True, attempt_recovery: bool = True):
    """
    Decorator for automatic exception handling in Streamlit functions.
    
    Args:
        show_error: Whether to show error message in UI
        attempt_recovery: Whether to attempt automatic recovery
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()) if kwargs else []
                }
                
                error = global_exception_handler.handle_exception(
                    e, context=context, 
                    show_user_message=show_error,
                    attempt_recovery=attempt_recovery
                )
                
                # Return None or appropriate default based on function
                return None
        
        return wrapper
    return decorator


@contextmanager
def streamlit_error_boundary(operation_name: str = "operation"):
    """
    Context manager for error boundary around Streamlit operations.
    
    Args:
        operation_name: Name of the operation for logging
    """
    try:
        yield
    except Exception as e:
        context = {
            "operation": operation_name,
            "timestamp": datetime.now().isoformat()
        }
        
        global_exception_handler.handle_exception(
            e, context=context,
            show_user_message=True,
            attempt_recovery=True
        )


def safe_streamlit_operation(func: Callable, 
                           *args, 
                           default_return: Any = None,
                           operation_name: Optional[str] = None,
                           **kwargs) -> Any:
    """
    Safely execute a Streamlit operation with error handling.
    
    Args:
        func: Function to execute
        *args: Arguments for the function
        default_return: Default return value on error
        operation_name: Name of operation for logging
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        context = {
            "function": func.__name__ if hasattr(func, '__name__') else str(func),
            "operation": operation_name or "safe_operation",
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys()) if kwargs else []
        }
        
        global_exception_handler.handle_exception(
            e, context=context,
            show_user_message=True,
            attempt_recovery=True
        )
        
        return default_return


# Global instance
global_exception_handler = GlobalExceptionHandler()


# Convenience functions
def handle_error(exception: Exception, 
                context: Optional[Dict[str, Any]] = None,
                show_user_message: bool = True) -> StreamlitError:
    """Handle an exception with the global handler."""
    return global_exception_handler.handle_exception(
        exception, context=context, show_user_message=show_user_message
    )


def install_global_exception_handler():
    """Install the global exception handler."""
    global_exception_handler.install_global_handler()


def get_error_statistics() -> Dict[str, Any]:
    """Get error statistics."""
    return global_exception_handler.get_error_stats()


def reset_error_statistics():
    """Reset error statistics."""
    global_exception_handler.reset_error_stats()


def show_error_dashboard():
    """Show error dashboard in Streamlit."""
    if not STREAMLIT_AVAILABLE:
        return
    
    stats = get_error_statistics()
    
    st.subheader("🛡️ Error Monitoring Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Errors",
            value=stats["total_errors"],
            delta=f"Since {datetime.fromtimestamp(stats['last_reset']).strftime('%H:%M')}"
        )
    
    with col2:
        if stats["errors_by_severity"]:
            critical_count = stats["errors_by_severity"].get(ErrorSeverity.CRITICAL, 0)
            high_count = stats["errors_by_severity"].get(ErrorSeverity.HIGH, 0)
            st.metric(
                label="High/Critical Errors",
                value=critical_count + high_count,
                delta="🚨" if critical_count > 0 else "⚠️" if high_count > 0 else "✅"
            )
        else:
            st.metric(label="High/Critical Errors", value=0, delta="✅")
    
    with col3:
        if stats["recent_errors"]:
            last_error_time = stats["recent_errors"][-1]["timestamp"]
            st.metric(
                label="Last Error",
                value=datetime.fromisoformat(last_error_time).strftime("%H:%M:%S")
            )
        else:
            st.metric(label="Last Error", value="None", delta="✅")
    
    # Error breakdown
    if stats["errors_by_category"]:
        st.subheader("Error Categories")
        categories_df = []
        for category, count in stats["errors_by_category"].items():
            categories_df.append({"Category": category, "Count": count})
        
        if categories_df:
            import pandas as pd
            df = pd.DataFrame(categories_df)
            st.dataframe(df, use_container_width=True)
    
    # Recent errors
    if stats["recent_errors"]:
        st.subheader("Recent Errors")
        for error in stats["recent_errors"][-5:]:  # Show last 5
            severity_icon = {
                ErrorSeverity.CRITICAL: "🚨",
                ErrorSeverity.HIGH: "❌", 
                ErrorSeverity.MEDIUM: "⚠️",
                ErrorSeverity.LOW: "ℹ️"
            }.get(error["severity"], "❓")
            
            with st.expander(f"{severity_icon} {error['category']} - {error['error_id'][:8]}", expanded=False):
                st.text(f"Time: {error['timestamp']}")
                st.text(f"Message: {error['message']}")
                st.text(f"Severity: {error['severity']}")
    
    # Reset button
    if st.button("🔄 Reset Error Statistics"):
        reset_error_statistics()
        st.success("Error statistics reset successfully")
        st.rerun()
__all__ = [
    "ErrorSeverity", "ErrorCategory", "StreamlitError", "GlobalExceptionHandler",
    "handle_streamlit_exceptions", "streamlit_error_boundary",
    "safe_streamlit_operation", "handle_error", "install_global_exception_handler",
    "get_error_statistics", "reset_error_statistics", "show_error_dashboard",
    "global_exception_handler",
]
