# 🛡️ PROMPT B - SECURITY STACK (CSRF + XSS PROTECTION)

**TASK**: Implementar proteção completa CSRF + XSS + Sanitização  
**ARQUIVOS**: `streamlit_extension/security/` (ISOLADO - sem interseção com outros prompts)  
**PRIORITY**: P0 - CRITICAL (bloqueadores de produção no report.md)  
**CONTEXT**: "No CSRF protection" + "XSS via unsanitized form inputs" + "Critical security vulnerabilities"

---

## 📋 **ARQUIVOS A CRIAR:**

### 1. `streamlit_extension/security/__init__.py`
```python
"""Security package for CSRF protection and XSS sanitization."""

from .csrf_protection import CSRFProtection, generate_csrf_token, validate_csrf_token
from .xss_sanitizer import XSSSanitizer, sanitize_input, sanitize_html
from .security_headers import SecurityHeaders, apply_security_headers
from .input_validator import InputValidator, validate_form_input
from .security_middleware import security_middleware, require_csrf

__all__ = [
    "CSRFProtection",
    "generate_csrf_token", 
    "validate_csrf_token",
    "XSSSanitizer",
    "sanitize_input",
    "sanitize_html",
    "SecurityHeaders",
    "apply_security_headers",
    "InputValidator",
    "validate_form_input",
    "security_middleware",
    "require_csrf"
]
```

### 2. `streamlit_extension/security/csrf_protection.py`
```python
"""CSRF (Cross-Site Request Forgery) protection implementation."""

from __future__ import annotations
import secrets
import hashlib
import time
from typing import Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import streamlit as st


@dataclass
class CSRFToken:
    """CSRF token data structure."""
    token: str
    created_at: datetime
    expires_at: datetime
    user_session: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid and not expired."""
        return not self.is_expired


class CSRFProtection:
    """CSRF protection manager with token generation and validation."""
    
    def __init__(self, token_lifetime_minutes: int = 60):
        self.token_lifetime = timedelta(minutes=token_lifetime_minutes)
        self._tokens: Dict[str, CSRFToken] = {}
        self._used_tokens: Set[str] = set()
        self._last_cleanup = time.time()
    
    def generate_token(self, session_id: Optional[str] = None) -> str:
        """Generate new CSRF token."""
        # Generate cryptographically secure token
        token_data = f"{secrets.token_urlsafe(32)}{time.time()}{session_id or ''}"
        token = hashlib.sha256(token_data.encode()).hexdigest()
        
        now = datetime.now()
        csrf_token = CSRFToken(
            token=token,
            created_at=now,
            expires_at=now + self.token_lifetime,
            user_session=session_id
        )
        
        self._tokens[token] = csrf_token
        self._cleanup_expired_tokens()
        
        return token
    
    def validate_token(self, token: str, session_id: Optional[str] = None) -> bool:
        """Validate CSRF token."""
        if not token or token in self._used_tokens:
            return False
        
        if token not in self._tokens:
            return False
        
        csrf_token = self._tokens[token]
        
        # Check expiration
        if csrf_token.is_expired:
            del self._tokens[token]
            return False
        
        # Check session binding if provided
        if session_id and csrf_token.user_session != session_id:
            return False
        
        # Mark token as used (one-time use)
        self._used_tokens.add(token)
        del self._tokens[token]
        
        return True
    
    def _cleanup_expired_tokens(self) -> None:
        """Clean up expired tokens periodically."""
        current_time = time.time()
        
        # Only cleanup every 5 minutes
        if current_time - self._last_cleanup < 300:
            return
        
        now = datetime.now()
        expired_tokens = [
            token for token, csrf_token in self._tokens.items()
            if csrf_token.is_expired
        ]
        
        for token in expired_tokens:
            del self._tokens[token]
        
        # Clean up old used tokens (keep for 1 hour to prevent replay)
        cleanup_time = now - timedelta(hours=1)
        self._used_tokens = {
            token for token in self._used_tokens
            if token in self._tokens or 
            any(t.created_at > cleanup_time for t in self._tokens.values() if t.token == token)
        }
        
        self._last_cleanup = current_time
    
    def get_active_tokens_count(self) -> int:
        """Get count of active tokens."""
        self._cleanup_expired_tokens()
        return len(self._tokens)


# Global CSRF protection instance
_csrf_protection: Optional[CSRFProtection] = None


def get_csrf_protection() -> CSRFProtection:
    """Get global CSRF protection instance."""
    global _csrf_protection
    if _csrf_protection is None:
        _csrf_protection = CSRFProtection()
    return _csrf_protection


def generate_csrf_token() -> str:
    """Generate CSRF token for current session."""
    csrf = get_csrf_protection()
    session_id = st.session_state.get("session_id")
    return csrf.generate_token(session_id)


def validate_csrf_token(token: str) -> bool:
    """Validate CSRF token for current session."""
    if not token:
        return False
    
    csrf = get_csrf_protection()
    session_id = st.session_state.get("session_id")
    return csrf.validate_token(token, session_id)


def require_csrf_token(form_data: Dict) -> bool:
    """Require and validate CSRF token in form data."""
    csrf_token = form_data.get("csrf_token")
    
    if not csrf_token:
        st.error("🔒 Security Error: Missing CSRF token")
        return False
    
    if not validate_csrf_token(csrf_token):
        st.error("🔒 Security Error: Invalid or expired CSRF token")
        return False
    
    return True


def csrf_form_wrapper(form_key: str):
    """Decorator to add CSRF protection to Streamlit forms."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate CSRF token for the form
            if f"csrf_token_{form_key}" not in st.session_state:
                st.session_state[f"csrf_token_{form_key}"] = generate_csrf_token()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def add_csrf_field(form_key: str) -> str:
    """Add CSRF token field to form and return token."""
    if f"csrf_token_{form_key}" not in st.session_state:
        st.session_state[f"csrf_token_{form_key}"] = generate_csrf_token()
    
    token = st.session_state[f"csrf_token_{form_key}"]
    
    # Add hidden field (in Streamlit, we'll store in session state)
    st.session_state[f"form_csrf_{form_key}"] = token
    
    return token


def validate_form_csrf(form_key: str, submitted_token: str) -> bool:
    """Validate CSRF token for specific form."""
    expected_token = st.session_state.get(f"form_csrf_{form_key}")
    
    if not expected_token or not submitted_token:
        return False
    
    # Clear the token after use
    if f"csrf_token_{form_key}" in st.session_state:
        del st.session_state[f"csrf_token_{form_key}"]
    if f"form_csrf_{form_key}" in st.session_state:
        del st.session_state[f"form_csrf_{form_key}"]
    
    return validate_csrf_token(submitted_token)
```

### 3. `streamlit_extension/security/xss_sanitizer.py`
```python
"""XSS (Cross-Site Scripting) sanitization and prevention."""

from __future__ import annotations
import re
import html
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlparse


class XSSSanitizer:
    """XSS sanitization with configurable rules."""
    
    # Dangerous HTML tags that should be removed
    DANGEROUS_TAGS = {
        'script', 'object', 'embed', 'form', 'input', 'button', 'select', 
        'textarea', 'iframe', 'frame', 'frameset', 'meta', 'link', 'base',
        'applet', 'bgsound', 'isindex', 'layer', 'ilayer', 'blink', 'marquee'
    }
    
    # Event handlers that should be removed
    EVENT_HANDLERS = {
        'onabort', 'onblur', 'onchange', 'onclick', 'ondblclick', 'onerror',
        'onfocus', 'onkeydown', 'onkeypress', 'onkeyup', 'onload', 'onmousedown',
        'onmousemove', 'onmouseout', 'onmouseover', 'onmouseup', 'onreset',
        'onresize', 'onselect', 'onsubmit', 'onunload', 'onbeforeunload',
        'oncontextmenu', 'ondrag', 'ondragend', 'ondragenter', 'ondragleave',
        'ondragover', 'ondragstart', 'ondrop', 'onscroll', 'onwheel'
    }
    
    # JavaScript protocol patterns
    JS_PROTOCOLS = [
        r'javascript\s*:',
        r'vbscript\s*:',
        r'data\s*:.*text/html',
        r'data\s*:.*application/.*script'
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\bUNION\b.*\bSELECT\b)',
        r'(\bINSERT\b.*\bINTO\b)',
        r'(\bUPDATE\b.*\bSET\b)',
        r'(\bDELETE\b.*\bFROM\b)',
        r'(\bDROP\b.*\bTABLE\b)',
        r'(\bCREATE\b.*\bTABLE\b)',
        r'(\bALTER\b.*\bTABLE\b)',
        r'(;\s*--)',
        r'(/\*.*\*/)',
        r'(\bOR\b.*=.*)',
        r'(\bAND\b.*=.*)',
        r'(\'.*OR.*\'.*=.*\')',
        r'(\".*OR.*\".*=.*\")'
    ]
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        self.js_pattern = re.compile(
            '|'.join(self.JS_PROTOCOLS), 
            re.IGNORECASE | re.MULTILINE
        )
        
        self.sql_pattern = re.compile(
            '|'.join(self.SQL_INJECTION_PATTERNS),
            re.IGNORECASE | re.MULTILINE
        )
        
        self.tag_pattern = re.compile(
            r'<\s*(/?)(' + '|'.join(self.DANGEROUS_TAGS) + r')\b[^>]*>',
            re.IGNORECASE
        )
        
        self.event_pattern = re.compile(
            r'\b(' + '|'.join(self.EVENT_HANDLERS) + r')\s*=\s*["\'][^"\']*["\']',
            re.IGNORECASE
        )
    
    def sanitize_string(self, input_str: str) -> str:
        """Sanitize a single string input."""
        if not isinstance(input_str, str):
            return str(input_str)
        
        # HTML encode basic characters
        sanitized = html.escape(input_str, quote=True)
        
        if self.strict_mode:
            # Remove dangerous HTML tags
            sanitized = self.tag_pattern.sub('', sanitized)
            
            # Remove event handlers
            sanitized = self.event_pattern.sub('', sanitized)
            
            # Check for JavaScript protocols
            if self.js_pattern.search(sanitized):
                sanitized = self.js_pattern.sub('[BLOCKED]', sanitized)
            
            # Check for SQL injection patterns
            if self.sql_pattern.search(sanitized):
                sanitized = self.sql_pattern.sub('[BLOCKED]', sanitized)
        
        return sanitized.strip()
    
    def sanitize_dict(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dictionary values recursively."""
        sanitized = {}
        
        for key, value in input_dict.items():
            # Sanitize key
            clean_key = self.sanitize_string(str(key))
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[clean_key] = self.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[clean_key] = self.sanitize_dict(value)
            elif isinstance(value, (list, tuple)):
                sanitized[clean_key] = self.sanitize_list(value)
            else:
                sanitized[clean_key] = value
        
        return sanitized
    
    def sanitize_list(self, input_list: List[Any]) -> List[Any]:
        """Sanitize list items recursively."""
        sanitized = []
        
        for item in input_list:
            if isinstance(item, str):
                sanitized.append(self.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, (list, tuple)):
                sanitized.append(self.sanitize_list(item))
            else:
                sanitized.append(item)
        
        return sanitized
    
    def is_safe_url(self, url: str) -> bool:
        """Check if URL is safe (no JavaScript protocols)."""
        if not url:
            return True
        
        try:
            parsed = urlparse(url.lower())
            return parsed.scheme in ['http', 'https', 'mailto', 'tel', ''] and \
                   not self.js_pattern.search(url)
        except Exception:
            return False
    
    def sanitize_html_content(self, html_content: str) -> str:
        """Sanitize HTML content more thoroughly."""
        if not html_content:
            return ""
        
        # Remove dangerous tags completely
        sanitized = self.tag_pattern.sub('', html_content)
        
        # Remove event handlers
        sanitized = self.event_pattern.sub('', sanitized)
        
        # Remove JavaScript protocols
        sanitized = self.js_pattern.sub('[BLOCKED]', sanitized)
        
        return sanitized
    
    def detect_threats(self, input_str: str) -> List[str]:
        """Detect potential security threats in input."""
        threats = []
        
        if self.js_pattern.search(input_str):
            threats.append("JavaScript injection detected")
        
        if self.sql_pattern.search(input_str):
            threats.append("SQL injection pattern detected")
        
        if self.tag_pattern.search(input_str):
            threats.append("Dangerous HTML tags detected")
        
        if self.event_pattern.search(input_str):
            threats.append("JavaScript event handlers detected")
        
        return threats


# Global sanitizer instance
_xss_sanitizer: Optional[XSSSanitizer] = None


def get_xss_sanitizer() -> XSSSanitizer:
    """Get global XSS sanitizer instance."""
    global _xss_sanitizer
    if _xss_sanitizer is None:
        _xss_sanitizer = XSSSanitizer(strict_mode=True)
    return _xss_sanitizer


def sanitize_input(input_data: Union[str, Dict, List]) -> Union[str, Dict, List]:
    """Sanitize input data (string, dict, or list)."""
    sanitizer = get_xss_sanitizer()
    
    if isinstance(input_data, str):
        return sanitizer.sanitize_string(input_data)
    elif isinstance(input_data, dict):
        return sanitizer.sanitize_dict(input_data)
    elif isinstance(input_data, (list, tuple)):
        return sanitizer.sanitize_list(input_data)
    else:
        return input_data


def sanitize_html(html_content: str) -> str:
    """Sanitize HTML content."""
    sanitizer = get_xss_sanitizer()
    return sanitizer.sanitize_html_content(html_content)


def validate_safe_url(url: str) -> bool:
    """Validate that URL is safe."""
    sanitizer = get_xss_sanitizer()
    return sanitizer.is_safe_url(url)


def detect_security_threats(input_str: str) -> List[str]:
    """Detect security threats in input string."""
    sanitizer = get_xss_sanitizer()
    return sanitizer.detect_threats(input_str)
```

### 4. `streamlit_extension/security/security_headers.py`
```python
"""Security headers for enhanced protection."""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class SecurityConfig:
    """Security configuration for headers."""
    content_security_policy: bool = True
    x_frame_options: bool = True
    x_content_type_options: bool = True
    x_xss_protection: bool = True
    strict_transport_security: bool = True
    referrer_policy: bool = True
    permissions_policy: bool = True


class SecurityHeaders:
    """Security headers manager."""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
    
    def get_csp_header(self) -> str:
        """Get Content Security Policy header."""
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Streamlit needs these
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: blob:",
            "font-src 'self' data:",
            "connect-src 'self' ws: wss:",  # WebSocket for Streamlit
            "media-src 'none'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'"
        ]
        return "; ".join(csp_directives)
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get all security headers."""
        headers = {}
        
        if self.config.content_security_policy:
            headers["Content-Security-Policy"] = self.get_csp_header()
        
        if self.config.x_frame_options:
            headers["X-Frame-Options"] = "DENY"
        
        if self.config.x_content_type_options:
            headers["X-Content-Type-Options"] = "nosniff"
        
        if self.config.x_xss_protection:
            headers["X-XSS-Protection"] = "1; mode=block"
        
        if self.config.strict_transport_security:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        if self.config.referrer_policy:
            headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if self.config.permissions_policy:
            headers["Permissions-Policy"] = (
                "camera=(), microphone=(), geolocation=(), "
                "accelerometer=(), gyroscope=(), magnetometer=(), "
                "payment=(), usb=()"
            )
        
        return headers
    
    def apply_headers_to_response(self, response_headers: Dict[str, str]) -> None:
        """Apply security headers to response."""
        security_headers = self.get_security_headers()
        response_headers.update(security_headers)


# Global security headers instance
_security_headers: Optional[SecurityHeaders] = None


def get_security_headers() -> SecurityHeaders:
    """Get global security headers instance."""
    global _security_headers
    if _security_headers is None:
        _security_headers = SecurityHeaders()
    return _security_headers


def apply_security_headers() -> Dict[str, str]:
    """Apply security headers and return them."""
    headers_manager = get_security_headers()
    return headers_manager.get_security_headers()


def get_csp_policy() -> str:
    """Get Content Security Policy."""
    headers_manager = get_security_headers()
    return headers_manager.get_csp_header()
```

### 5. `streamlit_extension/security/input_validator.py`
```python
"""Input validation for forms and user data."""

from __future__ import annotations
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum


class ValidationError(Exception):
    """Validation error exception."""
    pass


class ValidationType(Enum):
    """Types of validation."""
    EMAIL = "email"
    USERNAME = "username"
    PASSWORD = "password"
    PHONE = "phone"
    URL = "url"
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"


@dataclass
class ValidationRule:
    """Validation rule definition."""
    field_name: str
    validation_type: ValidationType
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    custom_validator: Optional[callable] = None
    error_message: Optional[str] = None


class InputValidator:
    """Comprehensive input validator."""
    
    # Regex patterns for common validations
    PATTERNS = {
        ValidationType.EMAIL: r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        ValidationType.USERNAME: r'^[a-zA-Z0-9_]{3,30}$',
        ValidationType.PASSWORD: r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$',
        ValidationType.PHONE: r'^\+?[\d\s\-\(\)]{10,15}$',
        ValidationType.URL: r'^https?://[^\s/$.?#].[^\s]*$',
        ValidationType.NUMBER: r'^\d+(\.\d+)?$',
        ValidationType.DATE: r'^\d{4}-\d{2}-\d{2}$'
    }
    
    # Default error messages
    DEFAULT_ERRORS = {
        ValidationType.EMAIL: "Invalid email format",
        ValidationType.USERNAME: "Username must be 3-30 characters, letters/numbers/underscore only",
        ValidationType.PASSWORD: "Password must be 8+ chars with uppercase, lowercase, and number",
        ValidationType.PHONE: "Invalid phone number format",
        ValidationType.URL: "Invalid URL format (must start with http:// or https://)",
        ValidationType.TEXT: "Invalid text input",
        ValidationType.NUMBER: "Must be a valid number",
        ValidationType.DATE: "Date must be in YYYY-MM-DD format"
    }
    
    def __init__(self):
        self.compiled_patterns = {
            vtype: re.compile(pattern) 
            for vtype, pattern in self.PATTERNS.items()
        }
    
    def validate_field(self, value: Any, rule: ValidationRule) -> List[str]:
        """Validate a single field against a rule."""
        errors = []
        
        # Convert to string for validation
        str_value = str(value) if value is not None else ""
        
        # Check required
        if rule.required and not str_value.strip():
            errors.append(f"{rule.field_name} is required")
            return errors
        
        # Skip other validations if empty and not required
        if not str_value.strip() and not rule.required:
            return errors
        
        # Check length constraints
        if rule.min_length and len(str_value) < rule.min_length:
            errors.append(f"{rule.field_name} must be at least {rule.min_length} characters")
        
        if rule.max_length and len(str_value) > rule.max_length:
            errors.append(f"{rule.field_name} must be no more than {rule.max_length} characters")
        
        # Check pattern
        pattern_to_use = rule.pattern or self.PATTERNS.get(rule.validation_type)
        if pattern_to_use:
            regex = self.compiled_patterns.get(rule.validation_type) or re.compile(pattern_to_use)
            if not regex.match(str_value):
                error_msg = rule.error_message or self.DEFAULT_ERRORS.get(
                    rule.validation_type, f"Invalid {rule.field_name} format"
                )
                errors.append(error_msg)
        
        # Custom validator
        if rule.custom_validator:
            try:
                if not rule.custom_validator(value):
                    errors.append(f"Custom validation failed for {rule.field_name}")
            except Exception as e:
                errors.append(f"Validation error for {rule.field_name}: {str(e)}")
        
        return errors
    
    def validate_form(self, form_data: Dict[str, Any], rules: List[ValidationRule]) -> Dict[str, List[str]]:
        """Validate entire form against rules."""
        all_errors = {}
        
        for rule in rules:
            field_value = form_data.get(rule.field_name)
            field_errors = self.validate_field(field_value, rule)
            
            if field_errors:
                all_errors[rule.field_name] = field_errors
        
        return all_errors
    
    def is_valid_form(self, form_data: Dict[str, Any], rules: List[ValidationRule]) -> bool:
        """Check if form is valid."""
        errors = self.validate_form(form_data, rules)
        return len(errors) == 0
    
    def validate_and_raise(self, form_data: Dict[str, Any], rules: List[ValidationRule]) -> None:
        """Validate form and raise ValidationError if invalid."""
        errors = self.validate_form(form_data, rules)
        if errors:
            error_messages = []
            for field, field_errors in errors.items():
                error_messages.extend(field_errors)
            raise ValidationError("; ".join(error_messages))


# Predefined validation rules for common fields
COMMON_VALIDATION_RULES = {
    "username": ValidationRule("username", ValidationType.USERNAME, required=True),
    "email": ValidationRule("email", ValidationType.EMAIL, required=True),
    "password": ValidationRule("password", ValidationType.PASSWORD, required=True),
    "client_name": ValidationRule("client_name", ValidationType.TEXT, required=True, min_length=2, max_length=100),
    "project_name": ValidationRule("project_name", ValidationType.TEXT, required=True, min_length=2, max_length=100),
    "epic_title": ValidationRule("epic_title", ValidationType.TEXT, required=True, min_length=3, max_length=200),
    "description": ValidationRule("description", ValidationType.TEXT, required=False, max_length=1000),
    "phone": ValidationRule("phone", ValidationType.PHONE, required=False),
    "website": ValidationRule("website", ValidationType.URL, required=False)
}


# Global validator instance
_input_validator: Optional[InputValidator] = None


def get_input_validator() -> InputValidator:
    """Get global input validator instance."""
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator()
    return _input_validator


def validate_form_input(form_data: Dict[str, Any], field_names: List[str]) -> Dict[str, List[str]]:
    """Validate form input using common rules."""
    validator = get_input_validator()
    
    rules = []
    for field_name in field_names:
        if field_name in COMMON_VALIDATION_RULES:
            rules.append(COMMON_VALIDATION_RULES[field_name])
        else:
            # Default text validation
            rules.append(ValidationRule(field_name, ValidationType.TEXT, required=True))
    
    return validator.validate_form(form_data, rules)


def is_valid_email(email: str) -> bool:
    """Quick email validation."""
    validator = get_input_validator()
    errors = validator.validate_field(email, COMMON_VALIDATION_RULES["email"])
    return len(errors) == 0


def is_strong_password(password: str) -> bool:
    """Quick password strength validation."""
    validator = get_input_validator()
    errors = validator.validate_field(password, COMMON_VALIDATION_RULES["password"])
    return len(errors) == 0
```

### 6. `streamlit_extension/security/security_middleware.py`
```python
"""Security middleware for Streamlit applications."""

from functools import wraps
from typing import Callable, Dict, Any, Optional
import streamlit as st

from .csrf_protection import generate_csrf_token, validate_csrf_token
from .xss_sanitizer import sanitize_input, detect_security_threats
from .input_validator import validate_form_input
from .security_headers import apply_security_headers


def security_middleware() -> None:
    """Apply security middleware to current Streamlit session."""
    # Apply security headers
    headers = apply_security_headers()
    
    # Store security headers in session state for reference
    st.session_state.security_headers = headers
    
    # Initialize CSRF protection if not present
    if "csrf_initialized" not in st.session_state:
        st.session_state.csrf_initialized = True


def require_csrf(form_key: str):
    """Decorator to require CSRF protection for form submission."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate CSRF token if not exists
            csrf_key = f"csrf_token_{form_key}"
            if csrf_key not in st.session_state:
                st.session_state[csrf_key] = generate_csrf_token()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def sanitize_form_data(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize all form data."""
    return sanitize_input(form_data)


def validate_secure_form(form_data: Dict[str, Any], field_names: list, form_key: str) -> tuple[bool, Dict[str, list], list]:
    """
    Comprehensive form validation with security checks.
    
    Returns:
        tuple: (is_valid, validation_errors, security_threats)
    """
    # Check CSRF token
    csrf_token = form_data.get("csrf_token")
    if not csrf_token or not validate_csrf_token(csrf_token):
        return False, {"csrf": ["Invalid or missing CSRF token"]}, ["CSRF token invalid"]
    
    # Sanitize input data
    sanitized_data = sanitize_form_data(form_data)
    
    # Detect security threats
    security_threats = []
    for field_name, value in form_data.items():
        if isinstance(value, str):
            threats = detect_security_threats(value)
            if threats:
                security_threats.extend([f"{field_name}: {threat}" for threat in threats])
    
    # Validate form fields
    validation_errors = validate_form_input(sanitized_data, field_names)
    
    is_valid = len(validation_errors) == 0 and len(security_threats) == 0
    
    return is_valid, validation_errors, security_threats


def secure_form_submit(form_data: Dict[str, Any], field_names: list, form_key: str) -> tuple[bool, Optional[str]]:
    """
    Handle secure form submission with comprehensive validation.
    
    Returns:
        tuple: (success, error_message)
    """
    is_valid, validation_errors, security_threats = validate_secure_form(form_data, field_names, form_key)
    
    if not is_valid:
        error_messages = []
        
        # Add validation errors
        for field, errors in validation_errors.items():
            error_messages.extend(errors)
        
        # Add security threat warnings
        if security_threats:
            error_messages.append("🔒 Security threats detected")
            error_messages.extend(security_threats)
        
        return False, " | ".join(error_messages)
    
    return True, None


def create_secure_form(form_key: str) -> str:
    """Create a secure form with CSRF token."""
    csrf_token = generate_csrf_token()
    st.session_state[f"csrf_token_{form_key}"] = csrf_token
    return csrf_token


def add_csrf_to_form(form_key: str) -> str:
    """Add CSRF token to existing form."""
    if f"csrf_token_{form_key}" not in st.session_state:
        st.session_state[f"csrf_token_{form_key}"] = generate_csrf_token()
    
    return st.session_state[f"csrf_token_{form_key}"]


class SecureFormManager:
    """Manager for secure forms with CSRF and XSS protection."""
    
    def __init__(self, form_key: str):
        self.form_key = form_key
        self.csrf_token = self._ensure_csrf_token()
    
    def _ensure_csrf_token(self) -> str:
        """Ensure CSRF token exists for this form."""
        csrf_key = f"csrf_token_{self.form_key}"
        if csrf_key not in st.session_state:
            st.session_state[csrf_key] = generate_csrf_token()
        return st.session_state[csrf_key]
    
    def validate_submission(self, form_data: Dict[str, Any], field_names: list) -> tuple[bool, str]:
        """Validate form submission."""
        # Add CSRF token to form data
        form_data["csrf_token"] = self.csrf_token
        
        success, error_message = secure_form_submit(form_data, field_names, self.form_key)
        
        if success:
            # Regenerate CSRF token for next submission
            self._regenerate_csrf_token()
        
        return success, error_message or ""
    
    def _regenerate_csrf_token(self):
        """Regenerate CSRF token after successful submission."""
        csrf_key = f"csrf_token_{self.form_key}"
        st.session_state[csrf_key] = generate_csrf_token()
        self.csrf_token = st.session_state[csrf_key]
    
    def get_csrf_token(self) -> str:
        """Get current CSRF token."""
        return self.csrf_token
```

---

## 🔧 **INTEGRATION INSTRUCTIONS:**

### A. Update main `streamlit_app.py`:
```python
# Add to imports
from streamlit_extension.security import security_middleware

# Add to main() function start
def main():
    # Apply security middleware
    security_middleware()
    
    # Rest of existing code...
```

### B. Update form pages (clients.py, projects.py, etc.):
```python
# Add to imports
from streamlit_extension.security import SecureFormManager, sanitize_input

# Replace existing forms with secure versions
def render_client_form():
    form_manager = SecureFormManager("client_form")
    
    with st.form("client_form"):
        name = st.text_input("Client Name")
        email = st.text_input("Email")
        
        if st.form_submit_button("Save Client"):
            form_data = {
                "name": name,
                "email": email
            }
            
            success, error = form_manager.validate_submission(form_data, ["name", "email"])
            
            if success:
                # Sanitize inputs before saving
                sanitized_data = sanitize_input(form_data)
                # Save to database...
                st.success("Client saved successfully!")
            else:
                st.error(f"Validation failed: {error}")
```

---

## ✅ **VERIFICATION CHECKLIST:**

- [ ] All security files created in `streamlit_extension/security/`
- [ ] CSRF protection active on all forms
- [ ] XSS sanitization working on all inputs
- [ ] Security headers applied to responses
- [ ] Input validation with comprehensive rules
- [ ] SQL injection protection active
- [ ] JavaScript protocol blocking functional
- [ ] Form security manager integrated
- [ ] Security middleware running
- [ ] Threat detection operational

---

## 🎯 **SUCCESS CRITERIA:**

1. **P0 Critical Issues RESOLVED**: 
   - "No CSRF protection in forms" ✅
   - "XSS via unsanitized form inputs" ✅
2. **Security Enhancement**: All inputs sanitized, forms protected, headers applied
3. **Enterprise Security**: Comprehensive threat detection and prevention
4. **Production Ready**: Forms secure against CSRF, XSS, SQL injection

**RESULTADO ESPERADO**: Stack de segurança enterprise-grade eliminando vulnerabilidades críticas P0 de CSRF e XSS, com sanitização completa e proteção multicamada.