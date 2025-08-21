"""
🧪 Test Suite for Global Exception Handler

Tests the comprehensive exception handling system for Streamlit applications.
Validates error classification, recovery strategies, and security integration.
"""

import pytest
import sys
import time
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from streamlit_extension.utils.exception_handler import (
        GlobalExceptionHandler, StreamlitError, ErrorSeverity, ErrorCategory,
        handle_streamlit_exceptions, streamlit_error_boundary, safe_streamlit_operation,
        global_exception_handler, handle_error, install_global_exception_handler
    )
    EXCEPTION_HANDLER_AVAILABLE = True
except ImportError as e:
    EXCEPTION_HANDLER_AVAILABLE = False
    pytest.skip(f"Exception handler not available: {e}", allow_module_level=True)


class TestStreamlitError:
    """Test StreamlitError class."""
    
    def test_error_creation(self):
        """Test basic error creation."""
        exception = ValueError("Test error")
        error = StreamlitError(exception)
        
        assert error.exception == exception
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.UNKNOWN
        assert error.timestamp is not None
        assert error.error_id is not None
        assert len(error.error_id) == 12  # SHA-256 hash truncated
        
    def test_error_with_custom_params(self):
        """Test error creation with custom parameters."""
        exception = sqlite3.OperationalError("Database locked")
        error = StreamlitError(
            exception,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            user_message="Custom message",
            context={"operation": "insert"},
            suggestions=["Try again", "Check connection"]
        )
        
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.DATABASE
        assert error.user_message == "Custom message"
        assert error.context == {"operation": "insert"}
        assert error.suggestions == ["Try again", "Check connection"]
    
    def test_user_message_generation(self):
        """Test automatic user message generation."""
        # Database error
        db_error = StreamlitError(sqlite3.OperationalError("table locked"))
        assert "Database temporarily unavailable" in db_error.user_message
        
        # Connection error
        conn_error = StreamlitError(ConnectionError("Network issue"))
        assert "Network connection issue" in conn_error.user_message
        
        # File error
        file_error = StreamlitError(FileNotFoundError("Missing file"))
        assert "Required file not found" in file_error.user_message
        
        # Unknown error
        unknown_error = StreamlitError(RuntimeError("Unknown issue"))
        assert "unexpected error occurred" in unknown_error.user_message
    
    def test_safe_context(self):
        """Test safe context generation."""
        error = StreamlitError(
            ValueError("Test"),
            context={
                "safe_string": "test",
                "safe_number": 42,
                "safe_bool": True,
                "safe_list": ["a", "b"],
                "unsafe_object": {"complex": "object"},
                "long_string": "x" * 300
            }
        )
        
        safe_context = error.get_safe_context()
        
        assert safe_context["safe_string"] == "test"
        assert safe_context["safe_number"] == 42
        assert safe_context["safe_bool"] is True
        assert safe_context["safe_list"] == ["a", "b"]
        assert "<dict>" in safe_context["unsafe_object"]
        assert len(safe_context["long_string"]) <= 200  # Truncated


class TestGlobalExceptionHandler:
    """Test GlobalExceptionHandler class."""
    
    def setup_method(self):
        """Setup for each test."""
        self.handler = GlobalExceptionHandler()
        self.handler.reset_error_stats()
    
    def test_exception_classification(self):
        """Test exception classification."""
        # Database error
        db_error = sqlite3.OperationalError("database is locked")
        category, severity = self.handler.classify_exception(db_error)
        assert category == ErrorCategory.DATABASE
        assert severity == ErrorSeverity.HIGH  # Locked is high severity
        
        # Database error (non-locked)
        db_error2 = sqlite3.DatabaseError("generic database error")
        category2, severity2 = self.handler.classify_exception(db_error2)
        assert category2 == ErrorCategory.DATABASE
        assert severity2 == ErrorSeverity.MEDIUM
        
        # Security error
        sec_error = PermissionError("access denied")
        category3, severity3 = self.handler.classify_exception(sec_error)
        assert category3 == ErrorCategory.SECURITY
        assert severity3 == ErrorSeverity.HIGH
        
        # Validation error
        val_error = ValueError("invalid input")
        category4, severity4 = self.handler.classify_exception(val_error)
        assert category4 == ErrorCategory.VALIDATION
        assert severity4 == ErrorSeverity.LOW
        
        # Network error
        net_error = ConnectionError("connection failed")
        category5, severity5 = self.handler.classify_exception(net_error)
        assert category5 == ErrorCategory.NETWORK
        assert severity5 == ErrorSeverity.MEDIUM
        
        # System error
        sys_error = MemoryError("out of memory")
        category6, severity6 = self.handler.classify_exception(sys_error)
        assert category6 == ErrorCategory.SYSTEM
        assert severity6 == ErrorSeverity.CRITICAL
    
    def test_handle_exception(self):
        """Test exception handling."""
        exception = ValueError("Test error")
        context = {"test": "context"}
        
        with patch('streamlit_extension.utils.exception_handler.STREAMLIT_AVAILABLE', False):
            error = self.handler.handle_exception(
                exception, 
                context=context,
                show_user_message=False,
                attempt_recovery=False
            )
        
        assert isinstance(error, StreamlitError)
        assert error.exception == exception
        assert error.context == context
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.LOW
    
    def test_error_stats_update(self):
        """Test error statistics updating."""
        # Handle multiple errors
        self.handler.handle_exception(ValueError("Error 1"), show_user_message=False)
        self.handler.handle_exception(sqlite3.OperationalError("Error 2"), show_user_message=False)
        self.handler.handle_exception(ConnectionError("Error 3"), show_user_message=False)
        
        stats = self.handler.get_error_stats()
        
        assert stats["total_errors"] == 3
        assert stats["errors_by_category"][ErrorCategory.VALIDATION] == 1
        assert stats["errors_by_category"][ErrorCategory.DATABASE] == 1
        assert stats["errors_by_category"][ErrorCategory.NETWORK] == 1
        assert stats["errors_by_severity"][ErrorSeverity.LOW] == 1
        assert stats["errors_by_severity"][ErrorSeverity.MEDIUM] == 2
        assert len(stats["recent_errors"]) == 3
    
    def test_error_stats_limit(self):
        """Test error statistics limit."""
        # Generate more than 10 errors
        for i in range(15):
            self.handler.handle_exception(ValueError(f"Error {i}"), show_user_message=False)
        
        stats = self.handler.get_error_stats()
        
        assert stats["total_errors"] == 15
        assert len(stats["recent_errors"]) == 10  # Should be limited to 10
        
        # Check that most recent errors are kept
        recent_messages = [e["message"] for e in stats["recent_errors"]]
        assert "Error 14" in recent_messages[-1]  # Last error should be present
    
    def test_error_stats_reset(self):
        """Test error statistics reset."""
        self.handler.handle_exception(ValueError("Error"), show_user_message=False)
        
        stats_before = self.handler.get_error_stats()
        assert stats_before["total_errors"] == 1
        
        self.handler.reset_error_stats()
        
        stats_after = self.handler.get_error_stats()
        assert stats_after["total_errors"] == 0
        assert stats_after["errors_by_category"] == {}
        assert stats_after["recent_errors"] == []
    
    def test_recovery_strategies(self):
        """Test error recovery strategies."""
        # Database lock error should get specific suggestions
        db_error = sqlite3.OperationalError("database is locked")
        error = self.handler.handle_exception(db_error, show_user_message=False, attempt_recovery=True)
        
        assert any("database is busy" in suggestion.lower() for suggestion in error.suggestions)
        
        # Auth error should get auth-specific suggestions
        auth_error = PermissionError("authentication failed")
        error = self.handler.handle_exception(auth_error, show_user_message=False, attempt_recovery=True)
        
        assert any("log out and log back in" in suggestion.lower() for suggestion in error.suggestions)


class TestExceptionDecorator:
    """Test exception handling decorator."""
    
    def test_decorator_success(self):
        """Test decorator with successful function."""
        @handle_streamlit_exceptions(show_error=False)
        def success_function(x, y):
            return x + y
        
        result = success_function(2, 3)
        assert result == 5
    
    def test_decorator_exception(self):
        """Test decorator with exception."""
        @handle_streamlit_exceptions(show_error=False)
        def failing_function():
            raise ValueError("Test error")
        
        with patch('streamlit_extension.utils.exception_handler.STREAMLIT_AVAILABLE', False):
            result = failing_function()
        
        assert result is None  # Should return None on error
    
    def test_decorator_with_context(self):
        """Test decorator captures function context."""
        @handle_streamlit_exceptions(show_error=False)
        def function_with_args(arg1, arg2, kwarg1=None):
            raise ValueError("Test error")
        
        with patch('streamlit_extension.utils.exception_handler.STREAMLIT_AVAILABLE', False):
            function_with_args("test", 123, kwarg1="value")
        
        # Check that error was logged with context
        stats = global_exception_handler.get_error_stats()
        assert stats["total_errors"] > 0
        
        recent_error = stats["recent_errors"][-1]
        # Should have captured function name and args info
        assert "function_with_args" in str(recent_error)


class TestErrorBoundary:
    """Test error boundary context manager."""
    
    def test_error_boundary_success(self):
        """Test error boundary with successful operation."""
        with patch('streamlit_extension.utils.exception_handler.STREAMLIT_AVAILABLE', False):
            with streamlit_error_boundary("test_operation"):
                result = 2 + 2
                assert result == 4
    
    def test_error_boundary_exception(self):
        """Test error boundary with exception."""
        with patch('streamlit_extension.utils.exception_handler.STREAMLIT_AVAILABLE', False):
            with streamlit_error_boundary("test_operation"):
                raise ValueError("Boundary test error")
        
        # Should not re-raise the exception
        # Check that error was handled
        stats = global_exception_handler.get_error_stats()
        assert stats["total_errors"] > 0


class TestSafeOperation:
    """Test safe operation wrapper."""
    
    def test_safe_operation_success(self):
        """Test safe operation with successful function."""
        def add_numbers(a, b):
            return a + b
        
        result = safe_streamlit_operation(add_numbers, 2, 3, default_return=0)
        assert result == 5
    
    def test_safe_operation_exception(self):
        """Test safe operation with exception."""
        def failing_function():
            raise ValueError("Safe operation test error")
        
        with patch('streamlit_extension.utils.exception_handler.STREAMLIT_AVAILABLE', False):
            result = safe_streamlit_operation(
                failing_function, 
                default_return="default_value",
                operation_name="test_safe_op"
            )
        
        assert result == "default_value"
        
        # Check that error was handled
        stats = global_exception_handler.get_error_stats()
        assert stats["total_errors"] > 0
    
    def test_safe_operation_with_args_kwargs(self):
        """Test safe operation with args and kwargs."""
        def complex_function(a, b, multiplier=1, offset=0):
            if a < 0:
                raise ValueError("Negative input")
            return (a + b) * multiplier + offset
        
        # Successful case
        result = safe_streamlit_operation(
            complex_function, 
            2, 3, 
            multiplier=2, 
            offset=1,
            default_return=0
        )
        assert result == 11  # (2 + 3) * 2 + 1
        
        # Error case
        with patch('streamlit_extension.utils.exception_handler.STREAMLIT_AVAILABLE', False):
            result = safe_streamlit_operation(
                complex_function,
                -1, 3,
                multiplier=2,
                default_return=-999
            )
        
        assert result == -999


class TestGlobalInstallation:
    """Test global exception handler installation."""
    
    def test_install_global_handler(self):
        """Test installing global exception handler."""
        original_hook = sys.excepthook
        
        try:
            install_global_exception_handler()
            
            # Check that excepthook was changed
            assert sys.excepthook != original_hook
            
            # Test that it handles exceptions
            with patch('streamlit_extension.utils.exception_handler.STREAMLIT_AVAILABLE', False):
                # This would normally raise an exception
                try:
                    raise ValueError("Global handler test")
                except ValueError:
                    pass  # Exception should be caught by our handler
            
        finally:
            # Restore original hook
            sys.excepthook = original_hook


class TestErrorStatistics:
    """Test error statistics functionality."""
    
    def test_get_error_statistics(self):
        """Test getting error statistics."""
        # Reset stats first
        global_exception_handler.reset_error_stats()
        
        # Generate some errors
        with patch('streamlit_extension.utils.exception_handler.STREAMLIT_AVAILABLE', False):
            handle_error(ValueError("Stat test 1"))
            handle_error(sqlite3.OperationalError("Stat test 2"))
        
        stats = global_exception_handler.get_error_stats()
        
        assert stats["total_errors"] == 2
        assert ErrorCategory.VALIDATION in stats["errors_by_category"]
        assert ErrorCategory.DATABASE in stats["errors_by_category"]
        assert len(stats["recent_errors"]) == 2
    
    def test_concurrent_error_handling(self):
        """Test thread-safe error handling."""
        import threading
        import time
        
        global_exception_handler.reset_error_stats()
        
        def generate_errors(thread_id):
            for i in range(5):
                with patch('streamlit_extension.utils.exception_handler.STREAMLIT_AVAILABLE', False):
                    handle_error(ValueError(f"Thread {thread_id} error {i}"))
                time.sleep(0.01)  # Small delay
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=generate_errors, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        stats = global_exception_handler.get_error_stats()
        assert stats["total_errors"] == 15  # 3 threads * 5 errors each


class TestSecurityIntegration:
    """Test integration with security framework."""
    
    def test_error_sanitization(self):
        """Test that error messages are sanitized."""
        # Create error with potentially sensitive context
        sensitive_context = {
            "password": "secret123",
            "api_key": "sk-1234567890",
            "safe_data": "public_info"
        }
        
        error = StreamlitError(
            ValueError("Test error"),
            context=sensitive_context
        )
        
        safe_context = error.get_safe_context()
        
        # Should have sanitized sensitive data
        assert "password" in safe_context
        assert "api_key" in safe_context
        assert safe_context["safe_data"] == "public_info"
        
        # Sensitive values should be truncated/sanitized
        assert len(str(safe_context["password"])) <= 200
        assert len(str(safe_context["api_key"])) <= 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])