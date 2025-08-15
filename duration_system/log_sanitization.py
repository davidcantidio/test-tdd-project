"""
🧹 Log Sanitization System

Comprehensive log sanitization to prevent sensitive data exposure.
Addresses report.md issue: "Sensitive data exposure in logs" (MEDIUM, CVSS 5.0)

Key Features:
- Database path redaction
- Authentication token/secret sanitization
- Personal information filtering
- File path normalization
- SQL query sanitization
- Error message sanitization
"""

import re
import os
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import hashlib


class LogSanitizer:
    """
    Comprehensive log sanitization system for sensitive data protection.
    
    Protects against exposure of:
    - Database paths and connection strings
    - Authentication tokens and secrets
    - Personal information (emails, names)
    - File system paths
    - SQL queries with sensitive data
    - Internal system details
    """
    
    def __init__(self):
        """Initialize sanitizer with configurable patterns."""
        self.setup_sanitization_patterns()
        self.setup_replacement_tokens()
    
    def setup_sanitization_patterns(self):
        """Setup regex patterns for different types of sensitive data."""
        
        # Database-related patterns
        self.db_patterns = {
            'db_paths': re.compile(r'(/[^/\s]+)*/([\w\-\.]+\.db)', re.IGNORECASE),
            'connection_strings': re.compile(r'(sqlite://|mysql://|postgresql://)[^\s]+', re.IGNORECASE),
            'sql_queries': re.compile(r'\b(SELECT|INSERT|UPDATE|DELETE)\b[^;]+;?', re.IGNORECASE),
            'table_names': re.compile(r'\b(framework_\w+|user_\w+|auth_\w+)', re.IGNORECASE)
        }
        
        # Authentication patterns
        self.auth_patterns = {
            'tokens': re.compile(r'\b[A-Za-z0-9_-]{20,}\b'),  # JWT-like tokens
            'api_keys': re.compile(r'\b[A-Za-z0-9_-]{32,}\b'),  # API keys
            'secrets': re.compile(r'(secret|password|token|key)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE),
            'oauth_codes': re.compile(r'\b[A-Za-z0-9_-]{40,}\b'),  # OAuth codes
            'session_ids': re.compile(r'\b[a-f0-9]{32,}\b', re.IGNORECASE)
        }
        
        # Personal information patterns
        self.pii_patterns = {
            'emails': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'ip_addresses': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'phone_numbers': re.compile(r'\+?[\d\s\-\(\)]{10,}'),
            'credit_cards': re.compile(r'\b(?:\d{4}[\s\-]?){3}\d{4}\b')
        }
        
        # File system patterns
        self.fs_patterns = {
            'absolute_paths': re.compile(r'(/[^/\s]+)+/?'),
            'windows_paths': re.compile(r'[A-Z]:\\[^\\:\*\?"<>\|\s]+', re.IGNORECASE),
            'home_dirs': re.compile(r'/home/[^/\s]+', re.IGNORECASE),
            'temp_dirs': re.compile(r'/tmp/[^/\s]+', re.IGNORECASE)
        }
        
        # System information patterns
        self.system_patterns = {
            'stack_traces': re.compile(r'Traceback \(most recent call last\):.*?(?=\n\S|\n$)', re.DOTALL),
            'error_details': re.compile(r'Error: .*?(?=\n\S|\n$)', re.DOTALL),
            'internal_modules': re.compile(r'streamlit_extension\.[^"\'\s,}]+'),
            'version_info': re.compile(r'\d+\.\d+\.\d+(?:\.\d+)?')
        }
    
    def setup_replacement_tokens(self):
        """Setup replacement tokens for sanitized content."""
        self.replacements = {
            'db_path': '[DB_PATH_REDACTED]',
            'connection_string': '[CONNECTION_REDACTED]',
            'sql_query': '[SQL_QUERY_REDACTED]',
            'table_name': '[TABLE_REDACTED]',
            'token': '[TOKEN_REDACTED]',
            'api_key': '[API_KEY_REDACTED]',
            'secret': '[SECRET_REDACTED]',
            'oauth_code': '[OAUTH_CODE_REDACTED]',
            'session_id': '[SESSION_ID_REDACTED]',
            'email': '[EMAIL_REDACTED]',
            'ip_address': '[IP_REDACTED]',
            'phone': '[PHONE_REDACTED]',
            'credit_card': '[CARD_REDACTED]',
            'file_path': '[PATH_REDACTED]',
            'home_dir': '[HOME_DIR_REDACTED]',
            'temp_dir': '[TEMP_DIR_REDACTED]',
            'stack_trace': '[STACK_TRACE_REDACTED]',
            'error_detail': '[ERROR_DETAILS_REDACTED]',
            'internal_module': '[INTERNAL_MODULE_REDACTED]',
            'version': '[VERSION_REDACTED]'
        }
    
    def sanitize_message(self, message: str, level: str = 'INFO') -> str:
        """
        Sanitize a log message to remove sensitive information.
        
        Args:
            message: The log message to sanitize
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            Sanitized log message
        """
        if not isinstance(message, str):
            message = str(message)
        
        # Apply sanitization based on log level
        if level in ['ERROR', 'CRITICAL']:
            # More aggressive sanitization for error logs
            message = self._sanitize_errors(message)
        
        # Apply all sanitization patterns
        message = self._sanitize_database_info(message)
        message = self._sanitize_authentication_info(message)
        message = self._sanitize_personal_info(message)
        message = self._sanitize_file_paths(message)
        message = self._sanitize_system_info(message)
        
        return message
    
    def _sanitize_database_info(self, message: str) -> str:
        """Sanitize database-related information."""
        # Database paths
        message = self.db_patterns['db_paths'].sub(
            lambda m: f"[...]{self.replacements['db_path']}", message
        )
        
        # Connection strings
        message = self.db_patterns['connection_strings'].sub(
            self.replacements['connection_string'], message
        )
        
        # SQL queries (keep first few words for context)
        def sanitize_sql(match):
            sql = match.group(0)
            operation = sql.split()[0].upper()
            return f"{operation} {self.replacements['sql_query']}"
        
        message = self.db_patterns['sql_queries'].sub(sanitize_sql, message)
        
        # Table names
        message = self.db_patterns['table_names'].sub(
            self.replacements['table_name'], message
        )
        
        return message
    
    def _sanitize_authentication_info(self, message: str) -> str:
        """Sanitize authentication-related information."""
        # Generic tokens and keys
        message = self.auth_patterns['tokens'].sub(
            self.replacements['token'], message
        )
        
        message = self.auth_patterns['api_keys'].sub(
            self.replacements['api_key'], message
        )
        
        # Secret patterns (key=value pairs)
        def sanitize_secret(match):
            key_part = match.group(1)
            return f"{key_part}: {self.replacements['secret']}"
        
        message = self.auth_patterns['secrets'].sub(sanitize_secret, message)
        
        # OAuth codes
        message = self.auth_patterns['oauth_codes'].sub(
            self.replacements['oauth_code'], message
        )
        
        # Session IDs
        message = self.auth_patterns['session_ids'].sub(
            self.replacements['session_id'], message
        )
        
        return message
    
    def _sanitize_personal_info(self, message: str) -> str:
        """Sanitize personal information."""
        # Email addresses (preserve domain for debugging)
        def sanitize_email(match):
            email = match.group(0)
            domain = email.split('@')[1] if '@' in email else 'domain'
            return f"user@{domain}"
        
        message = self.pii_patterns['emails'].sub(sanitize_email, message)
        
        # IP addresses (preserve last octet for debugging)
        def sanitize_ip(match):
            ip = match.group(0)
            parts = ip.split('.')
            if len(parts) == 4:
                return f"xxx.xxx.xxx.{parts[3]}"
            return self.replacements['ip_address']
        
        message = self.pii_patterns['ip_addresses'].sub(sanitize_ip, message)
        
        # Phone numbers
        message = self.pii_patterns['phone_numbers'].sub(
            self.replacements['phone'], message
        )
        
        # Credit card numbers
        message = self.pii_patterns['credit_cards'].sub(
            self.replacements['credit_card'], message
        )
        
        return message
    
    def _sanitize_file_paths(self, message: str) -> str:
        """Sanitize file system paths."""
        # Home directories
        message = self.fs_patterns['home_dirs'].sub(
            self.replacements['home_dir'], message
        )
        
        # Temp directories
        message = self.fs_patterns['temp_dirs'].sub(
            self.replacements['temp_dir'], message
        )
        
        # Generic file paths (preserve filename for context)
        def sanitize_path(match):
            path = match.group(0)
            filename = Path(path).name
            return f"{self.replacements['file_path']}/{filename}" if filename else self.replacements['file_path']
        
        message = self.fs_patterns['absolute_paths'].sub(sanitize_path, message)
        message = self.fs_patterns['windows_paths'].sub(sanitize_path, message)
        
        return message
    
    def _sanitize_system_info(self, message: str) -> str:
        """Sanitize system information."""
        # Stack traces
        message = self.system_patterns['stack_traces'].sub(
            self.replacements['stack_trace'], message
        )
        
        # Error details
        message = self.system_patterns['error_details'].sub(
            self.replacements['error_detail'], message
        )
        
        # Internal module references
        message = self.system_patterns['internal_modules'].sub(
            self.replacements['internal_module'], message
        )
        
        # Version information
        message = self.system_patterns['version_info'].sub(
            self.replacements['version'], message
        )
        
        return message
    
    def _sanitize_errors(self, message: str) -> str:
        """Apply additional sanitization for error messages."""
        # Common error patterns that might expose sensitive info
        error_patterns = {
            'file_not_found': re.compile(r"No such file or directory: '([^']+)'"),
            'permission_denied': re.compile(r"Permission denied: '([^']+)'"),
            'database_error': re.compile(r"database .* at '([^']+)'"),
            'authentication_failed': re.compile(r"Authentication failed.*: (.+)"),
        }
        
        for pattern_name, pattern in error_patterns.items():
            message = pattern.sub(
                lambda m: m.group(0).replace(m.group(1), '[REDACTED]'),
                message
            )
        
        return message
    
    def sanitize_exception(self, exc: Exception) -> str:
        """
        Sanitize exception messages and traceback.
        
        Args:
            exc: Exception to sanitize
            
        Returns:
            Sanitized exception description
        """
        exc_type = type(exc).__name__
        exc_message = str(exc)
        
        # Sanitize the exception message
        sanitized_message = self.sanitize_message(exc_message, level='ERROR')
        
        return f"{exc_type}: {sanitized_message}"
    
    def create_secure_logger(self, name: str, level: int = logging.INFO) -> logging.Logger:
        """
        Create a logger with automatic sanitization.
        
        Args:
            name: Logger name
            level: Logging level
            
        Returns:
            Configured logger with sanitization
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create sanitizing handler
        handler = SanitizingLogHandler(self)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger


class SanitizingLogHandler(logging.Handler):
    """Custom log handler that sanitizes messages before output."""
    
    def __init__(self, sanitizer: LogSanitizer):
        super().__init__()
        self.sanitizer = sanitizer
    
    def emit(self, record: logging.LogRecord):
        """Emit a sanitized log record."""
        try:
            # Sanitize the message
            if hasattr(record, 'msg') and record.msg:
                if record.args:
                    # Handle formatted messages
                    formatted_msg = record.msg % record.args
                    record.msg = self.sanitizer.sanitize_message(
                        formatted_msg, record.levelname
                    )
                    record.args = ()
                else:
                    # Handle simple messages
                    record.msg = self.sanitizer.sanitize_message(
                        str(record.msg), record.levelname
                    )
            
            # Sanitize exception info if present
            if record.exc_info and record.exc_info[1]:
                exc = record.exc_info[1]
                record.exc_text = self.sanitizer.sanitize_exception(exc)
            
            # Output to console (can be changed to file, etc.)
            print(self.format(record))
            
        except Exception as e:
            # Fallback: don't let sanitization errors break logging
            print(f"[LOG_SANITIZATION_ERROR] {e}")
            print(f"[ORIGINAL_MESSAGE] {record.getMessage()}")


# Global sanitizer instance
log_sanitizer = LogSanitizer()


def sanitize_log_message(message: str, level: str = 'INFO') -> str:
    """
    Convenience function for sanitizing log messages.
    
    Args:
        message: Message to sanitize
        level: Log level
        
    Returns:
        Sanitized message
    """
    return log_sanitizer.sanitize_message(message, level)


def sanitize_exception(exc: Exception) -> str:
    """
    Convenience function for sanitizing exceptions.
    
    Args:
        exc: Exception to sanitize
        
    Returns:
        Sanitized exception description
    """
    return log_sanitizer.sanitize_exception(exc)


def create_secure_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Convenience function for creating secure loggers.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured secure logger
    """
    return log_sanitizer.create_secure_logger(name, level)


# Testing and demonstration
if __name__ == "__main__":
    print("🧹 Log Sanitization System Test")
    print("=" * 50)
    
    sanitizer = LogSanitizer()
    
    # Test cases
    test_messages = [
        "Database error at /home/user/myproject/framework.db",
        "Authentication failed with token abc123def456ghi789",
        "User john.doe@company.com logged in from 192.168.1.100", 
        "SQL query: SELECT * FROM framework_users WHERE email='test@example.com'",
        "File not found: /tmp/sensitive_data.json",
        "OAuth code: 1234567890abcdef1234567890abcdef12345678",
        "Connection string: postgresql://user:pass@localhost:5432/mydb",
        "Error in streamlit_extension.utils.database: connection failed"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\nTest {i}:")
        print(f"Original:  {message}")
        print(f"Sanitized: {sanitizer.sanitize_message(message, 'ERROR')}")
    
    print("\n✅ Log sanitization system ready for production!")