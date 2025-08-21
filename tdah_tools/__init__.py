"""
TDAH Tools - TDD Task Management and Analytics

Convenience package exports for error handling, performance utils and analytics.
"""

__all__ = [
    "__version__",
    # error handler
    "get_error_handler",
    "handle_error",
    "log_info",
    "log_warning",
    "log_error",
    "with_error_handling",
    "TDDErrorHandler",
    "ErrorSeverity",
    "ErrorCategory",
    "TDDBaseException",
    "ValidationError",
    "ConfigurationError",
    "DependencyError",
    "FileSystemError",
    "ProcessError",
    "UserInputError",
    "AnalyticsError",
    "GitError",
    "GitHubError",
    # performance
    "get_performance_monitor",
    "cached",
    "performance_critical",
]

__version__ = "0.1.0"

from .error_handler import (  # noqa: E402
    get_error_handler, handle_error, log_info, log_warning, log_error,
    with_error_handling, TDDErrorHandler, ErrorSeverity, ErrorCategory,
    TDDBaseException, ValidationError, ConfigurationError, DependencyError,
    FileSystemError, ProcessError, UserInputError, AnalyticsError, GitError, GitHubError,
)
from .performance_utils import get_performance_monitor, cached, performance_critical  # noqa: E402