#!/usr/bin/env python3
"""
🚨 TDD Error Handler - Standardized Error Management

This module provides centralized error handling, logging, and custom exceptions
for the TDD project template. Ensures consistent error messages and logging
across all components.

Features:
- Custom exception hierarchy
- Structured logging with different levels
- User-friendly error messages
- Development vs production error modes
- Error reporting and analytics
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
import traceback


class ErrorSeverity(Enum):
    """Error severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error category classification."""
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    FILE_SYSTEM = "filesystem"
    NETWORK = "network"
    PROCESS = "process"
    USER_INPUT = "user_input"
    ANALYTICS = "analytics"
    TEMPLATE = "template"
    GIT = "git"
    GITHUB = "github"


@dataclass
class ErrorReport:
    """Structured error report."""
    timestamp: str
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    details: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    user_action: Optional[str] = None  # Suggested action for user


class TDDBaseException(Exception):
    """Base exception for TDD template errors."""
    
    def __init__(
        self, 
        message: str,
        category: ErrorCategory = ErrorCategory.TEMPLATE,
        details: Optional[str] = None,
        user_action: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.details = details
        self.user_action = user_action
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()


class ValidationError(TDDBaseException):
    """Environment or configuration validation errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.VALIDATION, **kwargs)


class ConfigurationError(TDDBaseException):
    """Configuration-related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.CONFIGURATION, **kwargs)


class DependencyError(TDDBaseException):
    """Missing or incompatible dependency errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.DEPENDENCY, **kwargs)


class FileSystemError(TDDBaseException):
    """File system related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.FILE_SYSTEM, **kwargs)


class ProcessError(TDDBaseException):
    """External process execution errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.PROCESS, **kwargs)


class UserInputError(TDDBaseException):
    """User input validation errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.USER_INPUT, **kwargs)


class AnalyticsError(TDDBaseException):
    """Analytics and data processing errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.ANALYTICS, **kwargs)


class GitError(TDDBaseException):
    """Git operation errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.GIT, **kwargs)


class GitHubError(TDDBaseException):
    """GitHub API and integration errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.GITHUB, **kwargs)


class TDDErrorHandler:
    """Centralized error handling and logging system."""
    
    def __init__(
        self, 
        log_file: Optional[Path] = None,
        console_level: str = "INFO",
        file_level: str = "DEBUG",
        development_mode: bool = False
    ):
        """Initialize error handler with logging configuration."""
        self.log_file = log_file or Path("tdd_errors.log")
        self.console_level = getattr(logging, console_level.upper())
        self.file_level = getattr(logging, file_level.upper())
        self.development_mode = development_mode
        self.error_reports: List[ErrorReport] = []
        
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure structured logging."""
        # Create logs directory if it doesn't exist
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Clear any existing handlers
        logging.getLogger().handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.console_level)
        console_handler.setFormatter(formatter)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(self.file_level)
        file_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # Create TDD-specific logger
        self.logger = logging.getLogger("TDD_TEMPLATE")
    
    def handle_exception(
        self,
        exception: Exception,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        user_action: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        reraise: bool = False
    ) -> ErrorReport:
        """Handle and log exception with structured reporting."""
        
        # Extract exception details
        exc_type = type(exception).__name__
        exc_message = str(exception)
        
        # Get stack trace info
        tb = traceback.extract_tb(exception.__traceback__)
        if tb:
            last_frame = tb[-1]
            file_path = last_frame.filename
            line_number = last_frame.lineno
            function_name = last_frame.name
        else:
            file_path = None
            line_number = None
            function_name = None
        
        # Determine category
        if isinstance(exception, TDDBaseException):
            category = exception.category
            details = exception.details
            user_action = user_action or exception.user_action
            context = {**(context or {}), **exception.context}
        else:
            category = self._classify_exception(exception)
            details = None
        
        # Format user-friendly message
        if isinstance(exception, TDDBaseException):
            message = exception.message
        else:
            message = self._format_user_message(exc_type, exc_message, category)
        
        # Create error report
        error_report = ErrorReport(
            timestamp=datetime.now().isoformat(),
            severity=severity,
            category=category,
            message=message,
            details=details or exc_message,
            file_path=file_path,
            line_number=line_number,
            function_name=function_name,
            stack_trace=traceback.format_exc() if self.development_mode else None,
            context=context,
            user_action=user_action
        )
        
        # Log the error
        self._log_error_report(error_report)
        
        # Store for analytics
        self.error_reports.append(error_report)
        
        # Re-raise if requested
        if reraise:
            raise exception
        
        return error_report
    
    def _classify_exception(self, exception: Exception) -> ErrorCategory:
        """Classify exception into appropriate category."""
        exc_type = type(exception).__name__
        exc_message = str(exception).lower()
        
        # Classification logic
        if "import" in exc_message or "module" in exc_message:
            return ErrorCategory.DEPENDENCY
        elif "file" in exc_message or "directory" in exc_message:
            return ErrorCategory.FILE_SYSTEM
        elif "network" in exc_message or "connection" in exc_message:
            return ErrorCategory.NETWORK
        elif "subprocess" in exc_type or "process" in exc_message:
            return ErrorCategory.PROCESS
        elif "validation" in exc_message or "invalid" in exc_message:
            return ErrorCategory.VALIDATION
        elif "config" in exc_message:
            return ErrorCategory.CONFIGURATION
        elif "git" in exc_message:
            return ErrorCategory.GIT
        else:
            return ErrorCategory.TEMPLATE
    
    def _format_user_message(self, exc_type: str, exc_message: str, category: ErrorCategory) -> str:
        """Format user-friendly error message."""
        category_messages = {
            ErrorCategory.DEPENDENCY: f"📦 Missing dependency: {exc_message}",
            ErrorCategory.FILE_SYSTEM: f"📁 File system error: {exc_message}",
            ErrorCategory.NETWORK: f"🌐 Network error: {exc_message}",
            ErrorCategory.PROCESS: f"⚙️ Process execution failed: {exc_message}",
            ErrorCategory.VALIDATION: f"✅ Validation failed: {exc_message}",
            ErrorCategory.CONFIGURATION: f"⚙️ Configuration error: {exc_message}",
            ErrorCategory.GIT: f"📝 Git operation failed: {exc_message}",
            ErrorCategory.GITHUB: f"🐙 GitHub integration error: {exc_message}",
            ErrorCategory.ANALYTICS: f"📊 Analytics error: {exc_message}",
            ErrorCategory.USER_INPUT: f"👤 Input validation failed: {exc_message}",
        }
        
        return category_messages.get(category, f"❌ {exc_type}: {exc_message}")
    
    def _log_error_report(self, report: ErrorReport) -> None:
        """Log error report at appropriate level."""
        # Format log message
        log_message = f"[{report.category.value.upper()}] {report.message}"
        
        if report.details and report.details != report.message:
            log_message += f" | Details: {report.details}"
        
        if report.user_action:
            log_message += f" | Action: {report.user_action}"
        
        if report.context:
            log_message += f" | Context: {report.context}"
        
        # Log at appropriate level
        if report.severity == ErrorSeverity.DEBUG:
            self.logger.debug(log_message)
        elif report.severity == ErrorSeverity.INFO:
            self.logger.info(log_message)
        elif report.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        elif report.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif report.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
    
    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log informational message."""
        log_msg = message
        if context:
            log_msg += f" | Context: {context}"
        self.logger.info(log_msg)
    
    def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        log_msg = message
        if context:
            log_msg += f" | Context: {context}"
        self.logger.warning(log_msg)
    
    def log_error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error message."""
        log_msg = message
        if context:
            log_msg += f" | Context: {context}"
        self.logger.error(log_msg)
    
    def export_error_report(self, output_path: Path) -> None:
        """Export error analytics to JSON file."""
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "total_errors": len(self.error_reports),
            "by_category": {},
            "by_severity": {},
            "errors": []
        }
        
        # Group by category and severity
        for report in self.error_reports:
            # By category
            category = report.category.value
            if category not in report_data["by_category"]:
                report_data["by_category"][category] = 0
            report_data["by_category"][category] += 1
            
            # By severity
            severity = report.severity.value
            if severity not in report_data["by_severity"]:
                report_data["by_severity"][severity] = 0
            report_data["by_severity"][severity] += 1
            
            # Add to errors list
            error_dict = {
                "timestamp": report.timestamp,
                "severity": report.severity.value,
                "category": report.category.value,
                "message": report.message,
                "details": report.details,
                "file_path": report.file_path,
                "line_number": report.line_number,
                "function_name": report.function_name,
                "context": report.context,
                "user_action": report.user_action
            }
            
            if self.development_mode:
                error_dict["stack_trace"] = report.stack_trace
            
            report_data["errors"].append(error_dict)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Error report exported to {output_path}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors for display."""
        if not self.error_reports:
            return {"total": 0, "message": "No errors recorded"}
        
        by_severity = {}
        by_category = {}
        
        for report in self.error_reports:
            severity = report.severity.value
            category = report.category.value
            
            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_category[category] = by_category.get(category, 0) + 1
        
        return {
            "total": len(self.error_reports),
            "by_severity": by_severity,
            "by_category": by_category,
            "latest": self.error_reports[-1].message if self.error_reports else None
        }


# Global error handler instance
_global_handler: Optional[TDDErrorHandler] = None


def get_error_handler(
    log_file: Optional[Path] = None,
    development_mode: bool = False
) -> TDDErrorHandler:
    """Get or create global error handler instance."""
    global _global_handler
    
    if _global_handler is None:
        _global_handler = TDDErrorHandler(
            log_file=log_file,
            development_mode=development_mode
        )
    
    return _global_handler


def handle_error(
    exception: Exception,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    user_action: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    reraise: bool = False
) -> ErrorReport:
    """Convenience function for error handling."""
    handler = get_error_handler()
    return handler.handle_exception(
        exception=exception,
        severity=severity,
        user_action=user_action,
        context=context,
        reraise=reraise
    )


def log_info(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function for info logging."""
    handler = get_error_handler()
    handler.log_info(message, context)


def log_warning(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function for warning logging."""
    handler = get_error_handler()
    handler.log_warning(message, context)


def log_error(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function for error logging.""" 
    handler = get_error_handler()
    handler.log_error(message, context)


def with_error_handling(
    user_action: Optional[str] = None,
    reraise: bool = True
):
    """Decorator for automatic error handling."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(
                    exception=e,
                    user_action=user_action,
                    context={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)},
                    reraise=reraise
                )
                return None
        return wrapper
    return decorator