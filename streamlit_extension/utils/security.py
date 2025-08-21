"""Comprehensive security framework for web application protection.

This module implements layered security measures for the Streamlit
application including XSS sanitization, CSRF protection, input
validation, rate limiting and basic DoS mitigation.  It integrates with
the JSON security library and optional logging utilities to provide
enterprise grade monitoring and threat detection.

Classes:
    StreamlitSecurityManager: Central security management for Streamlit
        forms and API calls.

Functions:
    sanitize_form_input: Sanitize user supplied text.
    validate_csrf_token: Validate form submission tokens.
    check_rate_limit: Apply rate limiting checks on operations.

Example:
    Protecting form input::

        security = StreamlitSecurityManager()
        clean = security.sanitize_form_input(user_value)

Note:
    Requires optional dependencies ``json_security`` and ``rate_limiter``
    for full functionality.
"""

import sys
import time
import hashlib
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add duration_system to path for security module
sys.path.append(str(Path(__file__).parent.parent.parent / "duration_system"))

try:
    from log_sanitization import create_secure_logger, sanitize_log_message, sanitize_exception
    LOG_SANITIZATION_AVAILABLE = True
except ImportError:
    LOG_SANITIZATION_AVAILABLE = False
    create_secure_logger = sanitize_log_message = sanitize_exception = None

try:
    from json_security import JSONSecurityValidator, SecurityViolation
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    JSONSecurityValidator = None

try:
    from rate_limiter import get_rate_limiter, RateLimitConfig, RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    get_rate_limiter = None
    RateLimitConfig = None
    RateLimitExceeded = None

try:
    from dos_protection import get_dos_protector, DoSProtector, RequestContext, ResourceError, ThreatDetectedError
    from circuit_breaker import CircuitBreakerError
    DOS_PROTECTION_AVAILABLE = True
except ImportError:
    DOS_PROTECTION_AVAILABLE = False
    get_dos_protector = None
    DoSProtector = None
    RequestContext = None
    ResourceError = None
    ThreatDetectedError = None
    CircuitBreakerError = None


class StreamlitSecurityManager:
    # Delegation to StreamlitSecurityManagerUiinteraction
    def __init__(self):
        self._streamlitsecuritymanageruiinteraction = StreamlitSecurityManagerUiinteraction()
    # Delegation to StreamlitSecurityManagerLogging
    def __init__(self):
        self._streamlitsecuritymanagerlogging = StreamlitSecurityManagerLogging()
    # Delegation to StreamlitSecurityManagerConfiguration
    def __init__(self):
        self._streamlitsecuritymanagerconfiguration = StreamlitSecurityManagerConfiguration()
    # Delegation to StreamlitSecurityManagerValidation
    def __init__(self):
        self._streamlitsecuritymanagervalidation = StreamlitSecurityManagerValidation()
    # Delegation to StreamlitSecurityManagerErrorhandling
    def __init__(self):
        self._streamlitsecuritymanagererrorhandling = StreamlitSecurityManagerErrorhandling()
    # Delegation to StreamlitSecurityManagerFormatting
    def __init__(self):
        self._streamlitsecuritymanagerformatting = StreamlitSecurityManagerFormatting()
    # Delegation to StreamlitSecurityManagerBusinesslogic
    def __init__(self):
        self._streamlitsecuritymanagerbusinesslogic = StreamlitSecurityManagerBusinesslogic()
    # Delegation to StreamlitSecurityManagerNetworking
    def __init__(self):
        self._streamlitsecuritymanagernetworking = StreamlitSecurityManagerNetworking()
    # Delegation to StreamlitSecurityManagerCalculation
    def __init__(self):
        self._streamlitsecuritymanagercalculation = StreamlitSecurityManagerCalculation()
    """Manage security for Streamlit forms and data display.

    The manager combines XSS sanitization, JSON payload validation, rate
    limiting and DoS protection behind a single interface tailored for
    Streamlit applications.

    Attributes:
        logger: Logging object used for sanitized security logging.
        validator: Optional JSONSecurityValidator instance.
        rate_limiter: Optional rate limiter instance.
        dos_protector: Optional DoS protection instance.
    """

    def __init__(self):
        """Initialize security manager with safe defaults."""
        # Initialize secure logging
        if LOG_SANITIZATION_AVAILABLE:
            self.logger = create_secure_logger('streamlit_security')
        else:
            import logging
            self.logger = logging.getLogger('streamlit_security')
        
        if SECURITY_AVAILABLE:
            self.validator = JSONSecurityValidator(
                max_depth=5,  # Reasonable depth for form data
                max_size=50000,  # 50KB max for form inputs
                max_string_length=5000,  # 5KB max per field
                allow_dangerous_keys=False,
                strict_mode=True
            )
        else:
            self.validator = None
        
        # Initialize rate limiter
        if RATE_LIMITING_AVAILABLE:
            self.rate_limiter = get_rate_limiter()
            # Configure Streamlit-specific rate limits
            self._configure_streamlit_rate_limits()
        else:
            self.rate_limiter = None
        
        # Initialize DoS protector
        if DOS_PROTECTION_AVAILABLE:
            self.dos_protector = get_dos_protector()
            self._configure_streamlit_dos_protection()
        else:
            self.dos_protector = None
    
    def _configure_streamlit_rate_limits(self):
        """Configure rate limits for Streamlit operations."""
        if not self.rate_limiter:
            return
        
        # Database operations - conservative limits
        self.rate_limiter.configure_limit(
            "db_read", 
            RateLimitConfig(max_requests=100, window_seconds=60, algorithm="sliding_window")
        )
        self.rate_limiter.configure_limit(
            "db_write", 
            RateLimitConfig(max_requests=20, window_seconds=60, algorithm="sliding_window")
        )
        
        # Form submissions - prevent abuse
        self.rate_limiter.configure_limit(
            "form_submit", 
            RateLimitConfig(max_requests=10, window_seconds=60, algorithm="sliding_window")
        )
        
        # Page loads - generous limits for normal browsing
        self.rate_limiter.configure_limit(
            "page_load", 
            RateLimitConfig(max_requests=200, window_seconds=60, algorithm="sliding_window")
        )
        
        # Search operations - moderate limits
        self.rate_limiter.configure_limit(
            "search", 
            RateLimitConfig(max_requests=50, window_seconds=60, algorithm="sliding_window")
        )
        
        # Authentication attempts - strict limits
        self.rate_limiter.configure_limit(
            "auth_attempts", 
            RateLimitConfig(max_requests=5, window_seconds=300, penalty_multiplier=2.0, algorithm="sliding_window")
        )
    
    def _configure_streamlit_dos_protection(self):
        """Configure DoS protection for Streamlit operations."""
        if not self.dos_protector:
            return
        
        # Add circuit breakers for critical operations
        try:
            from circuit_breaker import CircuitBreakerConfig
        except ImportError:
            print("CircuitBreakerConfig not available, skipping circuit breaker configuration")
            return
        
        # Database circuit breaker - fails fast when DB is overloaded
        db_breaker_config = CircuitBreakerConfig(
            failure_threshold=5,        # Open after 5 failures
            timeout_seconds=30,         # Stay open for 30 seconds
            success_threshold=3,        # Close after 3 successes
            failure_rate_threshold=0.6  # 60% failure rate triggers opening
        )
        self.dos_protector.add_circuit_breaker("database_operations", db_breaker_config)
        
        # Authentication circuit breaker - protect against auth attacks
        auth_breaker_config = CircuitBreakerConfig(
            failure_threshold=3,        # Very sensitive for auth
            timeout_seconds=60,         # Longer timeout for auth
            success_threshold=2,
            failure_rate_threshold=0.5  # 50% failure rate
        )
        self.dos_protector.add_circuit_breaker("authentication", auth_breaker_config)
        
        # File operations circuit breaker - protect against file system abuse
        file_breaker_config = CircuitBreakerConfig(
            failure_threshold=10,
            timeout_seconds=20,
            success_threshold=5,
            failure_rate_threshold=0.7  # 70% failure rate
        )
        self.dos_protector.add_circuit_breaker("file_operations", file_breaker_config)
    
    def sanitize_form_input(self, value: str, field_name: str = "input") -> str:
        """
        Sanitize user input from Streamlit forms.
        
        Args:
            value: Raw input value from form
            field_name: Name of the field for error reporting
            
        Returns:
            Sanitized value safe for display and storage
        """
        if not value or not isinstance(value, str):
            return value
        
        # Preferir API pública quando disponível
        if SECURITY_AVAILABLE and self.validator:
            try:
                # Supondo que a lib possua um método público 'sanitize_string'
                sanitize_fn = getattr(self.validator, "sanitize_string", None)
                if callable(sanitize_fn):
                    return sanitize_fn(value)
                # fallback para validação + escape controlado
                ok, _ = self.validate_form_data({"field": value})
                return value if ok else self._basic_html_escape(value)
            except Exception as e:
                # Fallback para escape básico em caso de erro
                if LOG_SANITIZATION_AVAILABLE and sanitize_log_message:
                    self.logger.warning(sanitize_log_message(f"Advanced sanitization failed for field: {e}", 'WARNING'))
                else:
                    self.logger.warning("Advanced sanitization failed for field: %s", str(e)[:100])
                return self._basic_html_escape(value)
        else:
            return self._basic_html_escape(value)
    
    def validate_form_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate form data for security threats.
        
        Args:
            data: Dictionary of form data
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        if not SECURITY_AVAILABLE or not self.validator:
            return True, []
        
        try:
            is_valid, violations = self.validator.validate_data(data)
            
            error_messages = []
            for violation in violations:
                error_messages.append(
                    f"Security violation in {violation.path}: {violation.message}"
                )
            
            return is_valid, error_messages
        except Exception as e:
            # On validation error, fail safe
            return False, [f"Security validation error: {e}"]
    
    def sanitize_display_text(self, text: str, max_length: int = 1000) -> str:
        """
        Sanitize text for safe display in Streamlit UI.
        
        Args:
            text: Text to display
            max_length: Maximum length for display
            
        Returns:
            Safely encoded text for display
        """
        if not text or not isinstance(text, str):
            return str(text) if text is not None else ""
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        if SECURITY_AVAILABLE and self.validator:
            try:
                sanitize_fn = getattr(self.validator, "sanitize_string", None)
                if callable(sanitize_fn):
                    return sanitize_fn(text)
                ok, _ = self.validate_form_data({"field": text})
                return text if ok else self._basic_html_escape(text)
            except Exception:
                return self._basic_html_escape(text)
        else:
            return self._basic_html_escape(text)
    
    def _basic_html_escape(self, text: str) -> str:
        """
        Basic HTML escaping as fallback.
        
        Args:
            text: Text to escape
            
        Returns:
            HTML-escaped text
        """
        if not isinstance(text, str):
            return str(text)
        
        # Basic HTML escaping
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#x27;')
        text = text.replace('\x00', '')  # Remove null bytes
        
        return text
    
    def create_safe_client_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create safely sanitized client data from form input.
        
        Args:
            form_data: Raw form data from Streamlit
            
        Returns:
            Sanitized client data safe for database storage
        """
        safe_data = {}
        
        # Fields that need sanitization
        text_fields = [
            'client_key', 'name', 'description', 'industry',
            'primary_contact_name', 'primary_contact_email', 'primary_contact_phone'
        ]
        
        for key, value in form_data.items():
            if key in text_fields and isinstance(value, str):
                safe_data[key] = self.sanitize_form_input(value, key)
            else:
                safe_data[key] = value
        
        return safe_data
    
    def create_safe_project_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create safely sanitized project data from form input.
        
        Args:
            form_data: Raw form data from Streamlit
            
        Returns:
            Sanitized project data safe for database storage
        """
        safe_data = {}
        
        # Fields that need sanitization
        text_fields = [
            'project_key', 'name', 'description', 'project_type', 'methodology'
        ]
        
        for key, value in form_data.items():
            if key in text_fields and isinstance(value, str):
                safe_data[key] = self.sanitize_form_input(value, key)
            else:
                safe_data[key] = value
        
        return safe_data
    
    def check_rate_limit(self, 
                        operation_type: str, 
                        user_id: Optional[str] = None,
                        ip_address: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if operation is within rate limits.
        
        Args:
            operation_type: Type of operation (db_read, db_write, form_submit, etc.)
            user_id: Optional user identifier
            ip_address: Optional IP address
            
        Returns:
            Tuple of (allowed, error_message)
        """
        if not RATE_LIMITING_AVAILABLE or not self.rate_limiter:
            return True, None
        
        try:
            # Extract session info from Streamlit if available
            if not user_id and hasattr(self, '_get_streamlit_session_id'):
                user_id = self._get_streamlit_session_id()
            
            allowed = self.rate_limiter.check_limit(
                limit_type=operation_type,
                user_id=user_id,
                ip_address=ip_address
            )
            
            if not allowed:
                # Get remaining info for better error message
                remaining_info = self.rate_limiter.get_remaining_requests(
                    operation_type, user_id=user_id, ip_address=ip_address
                )
                
                reset_time = remaining_info.get("reset_time")
                window_seconds = remaining_info.get("window_seconds", 60)
                
                if reset_time:
                    import time
                    wait_seconds = max(0, reset_time - time.time())
                    error_msg = f"Rate limit exceeded. Please wait {wait_seconds:.0f} seconds."
                else:
                    error_msg = f"Rate limit exceeded. Please wait {window_seconds} seconds."
                
                return False, error_msg
            
            return True, None
            
        except Exception as e:
            # On error, allow but log warning
            if LOG_SANITIZATION_AVAILABLE:
                self.logger.warning(sanitize_log_message(f"Rate limiting error: {e}", 'WARNING'))
            else:
                self.logger.warning(f"Rate limiting error: {str(e)[:100]}")
            return True, None
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        if not RATE_LIMITING_AVAILABLE or not self.rate_limiter:
            return {"rate_limiting": "disabled"}
        
        try:
            return self.rate_limiter.get_stats()
        except Exception as e:
            return {"error": str(e)}
    
    def reset_rate_limits(self, 
                         operation_type: str,
                         user_id: Optional[str] = None,
                         ip_address: Optional[str] = None):
        """Reset rate limits for specific user/operation."""
        if not RATE_LIMITING_AVAILABLE or not self.rate_limiter:
            return
        
        try:
            self.rate_limiter.reset_entity(
                limit_type=operation_type,
                user_id=user_id,
                ip_address=ip_address
            )
        except Exception as e:
            if LOG_SANITIZATION_AVAILABLE:
                self.logger.error(sanitize_log_message(f"Failed to reset rate limits: {e}", 'ERROR'))
            else:
                self.logger.error(f"Failed to reset rate limits: {str(e)[:100]}")
    
    def _get_streamlit_session_id(self) -> str:
        """Obtém ID único da sessão Streamlit de forma segura."""
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and hasattr(st.session_state, 'session_id'):
                return str(st.session_state.session_id)
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            ctx = get_script_run_ctx()
            if ctx and hasattr(ctx, 'session_id'):
                return str(ctx.session_id)
        except Exception:
            pass
        import uuid
        return str(uuid.uuid4())
    
    def is_security_enabled(self) -> bool:
        """Check if advanced security features are available."""
        return SECURITY_AVAILABLE and self.validator is not None
    
    def is_rate_limiting_enabled(self) -> bool:
        """Check if rate limiting is available."""
        return RATE_LIMITING_AVAILABLE and self.rate_limiter is not None
    
    def create_request_context(self, 
                              endpoint: str = "unknown",
                              request_size: int = 0,
                              user_id: Optional[str] = None) -> Optional[Any]:
        """Create RequestContext for DoS protection from Streamlit session."""
        if not DOS_PROTECTION_AVAILABLE or not RequestContext:
            return None
        
        try:
            import streamlit as st
            
            # Extract session information
            session_id = self._get_streamlit_session_id()
            
            # Get IP address (best effort - may not be available in all deployments)
            ip_address = self._get_client_ip() or "127.0.0.1"
            
            # Get user agent (if available from browser context)
            user_agent = self._get_user_agent() or "Streamlit/Unknown"
            
            context = RequestContext(
                timestamp=time.time(),
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                request_size=request_size,
                user_id=user_id,
                session_id=session_id
            )
            
            return context
            
        except Exception as e:
            if LOG_SANITIZATION_AVAILABLE:
                self.logger.error(sanitize_log_message(f"Failed to create request context: {e}", 'ERROR'))
            else:
                self.logger.error(f"Failed to create request context: {str(e)[:100]}")
            return None
    
    def check_comprehensive_protection(self, 
                                     operation_type: str,
                                     endpoint: str = "unknown",
                                     request_size: int = 0,
                                     user_id: Optional[str] = None,
                                     profile_name: str = "default") -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Apply comprehensive DoS protection including threat detection.
        
        Args:
            operation_type: Type of operation (db_read, db_write, form_submit, etc.)
            endpoint: Endpoint being accessed
            request_size: Size of request in bytes
            user_id: Optional user identifier
            profile_name: Threat detection profile
            
        Returns:
            Tuple of (allowed, error_message, protection_details)
        """
        if not DOS_PROTECTION_AVAILABLE or not self.dos_protector:
            # Fallback to basic rate limiting
            allowed, error = self.check_rate_limit(operation_type, user_id)
            return allowed, error, {"fallback": "basic_rate_limiting"}
        
        try:
            import time
            
            # Create request context
            context = self.create_request_context(endpoint, request_size, user_id)
            
            # Apply comprehensive protection
            protection_result = self.dos_protector.protect(
                protection_type=operation_type,
                context=context,
                profile_name=profile_name
            )
            
            return True, None, protection_result
            
        except ResourceError as e:
            return False, f"System overloaded: {e}", {"error_type": "resource_limit"}
        except ThreatDetectedError as e:
            return False, f"Suspicious activity detected: {e}", {
                "error_type": "threat_detected",
                "threat_score": e.threat_score,
                "reasons": e.reasons
            }
        except RateLimitExceeded as e:
            return False, f"Rate limit exceeded: {e}", {"error_type": "rate_limit"}
        except CircuitBreakerError as e:
            return False, f"Service temporarily unavailable: {e}", {"error_type": "circuit_breaker"}
        except Exception as e:
            # On error, allow but log warning
            if LOG_SANITIZATION_AVAILABLE:
                self.logger.error(sanitize_log_message(f"DoS protection error: {e}", 'ERROR'))
            else:
                self.logger.error(f"DoS protection error: {str(e)[:100]}")
            return True, None, {"error": str(e)}
    
    def _get_client_ip(self) -> Optional[str]:
        """Extract client IP address from Streamlit context."""
        try:
            import streamlit as st
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            
            ctx = get_script_run_ctx()
            if ctx and hasattr(ctx, 'session_info'):
                # Try to get IP from session info
                session_info = ctx.session_info
                if hasattr(session_info, 'client_ip'):
                    return session_info.client_ip
                elif hasattr(session_info, 'headers'):
                    # Check common IP headers
                    headers = session_info.headers
                    ip_headers = ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP']
                    for header in ip_headers:
                        if header in headers:
                            return headers[header].split(',')[0].strip()
            
            # Fallback: check if running in cloud environment
            import os
            if os.environ.get('STREAMLIT_SERVER_ADDRESS'):
                return '0.0.0.0'  # Cloud deployment
            
        except Exception:
            pass
        
        return None
    
    def _get_user_agent(self) -> Optional[str]:
        """Extract user agent from Streamlit context."""
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            
            ctx = get_script_run_ctx()
            if ctx and hasattr(ctx, 'session_info'):
                session_info = ctx.session_info
                if hasattr(session_info, 'headers') and 'User-Agent' in session_info.headers:
                    return session_info.headers['User-Agent']
        except Exception:
            pass
        
        return None
    
    def get_dos_protection_stats(self) -> Dict[str, Any]:
        """Get comprehensive DoS protection statistics."""
        if not DOS_PROTECTION_AVAILABLE or not self.dos_protector:
            return {"dos_protection": "disabled"}
        
        try:
            return self.dos_protector.get_comprehensive_stats()
        except Exception as e:
            return {"error": str(e)}
    
    def reset_dos_protection(self, operation_type: str, user_id: Optional[str] = None):
        """Reset DoS protection for specific user/operation."""
        if not DOS_PROTECTION_AVAILABLE or not self.dos_protector:
            return
        
        try:
            # Reset rate limits
            if self.rate_limiter:
                self.rate_limiter.reset_entity(operation_type, user_id=user_id)
            
            # Reset threat scores (if entity key can be determined)
            if user_id:
                entity_key = f"user:{user_id}"
                if entity_key in self.dos_protector.threat_detector.threat_scores:
                    self.dos_protector.threat_detector.threat_scores[entity_key] = 0.0
                    
        except Exception as e:
            if LOG_SANITIZATION_AVAILABLE:
                self.logger.error(sanitize_log_message(f"Failed to reset DoS protection: {e}", 'ERROR'))
            else:
                self.logger.error(f"Failed to reset DoS protection: {str(e)[:100]}")
    
    def is_dos_protection_enabled(self) -> bool:
        """Check if DoS protection is available."""
        return DOS_PROTECTION_AVAILABLE and self.dos_protector is not None
    
    def generate_csrf_token(self, form_id: str) -> str:
        """
        Generate a secure CSRF token for a form.
        
        Args:
            form_id: Unique identifier for the form
            
        Returns:
            Secure CSRF token string
        """
        try:
            import streamlit as st
            
            # Get or create session ID
            session_id = self._get_streamlit_session_id() or "default_session"
            
            # Generate token components
            timestamp = str(int(time.time()))
            random_bytes = secrets.token_hex(16)
            
            # Create token payload
            token_data = f"{session_id}:{form_id}:{timestamp}:{random_bytes}"
            
            # Generate secure hash
            token_hash = hashlib.sha256(token_data.encode()).hexdigest()
            
            # Create final token (timestamp:hash for validation)
            csrf_token = f"{timestamp}:{token_hash}"
            
            # Store in session state for validation
            if hasattr(st, 'session_state'):
                csrf_key = f"csrf_token_{form_id}"
                st.session_state[csrf_key] = csrf_token
                st.session_state[f"{csrf_key}_created"] = time.time()
            
            return csrf_token
            
        except Exception as e:
            if LOG_SANITIZATION_AVAILABLE:
                self.logger.error(sanitize_log_message(f"Failed to generate CSRF token: {e}", 'ERROR'))
            else:
                self.logger.error(f"Failed to generate CSRF token: {str(e)[:100]}")
            # Fallback robusto: manter alta entropia (~256 bits)
            return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, form_id: str, provided_token: str, max_age_seconds: int = 3600) -> bool:
        """
        Validate a CSRF token for a form.
        
        Args:
            form_id: Unique identifier for the form
            provided_token: Token provided with form submission
            max_age_seconds: Maximum age of token in seconds (default 1 hour)
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            import streamlit as st
            
            if not provided_token:
                return False
            
            # Get stored token from session
            if hasattr(st, 'session_state'):
                csrf_key = f"csrf_token_{form_id}"
                stored_token = st.session_state.get(csrf_key)
                token_created = st.session_state.get(f"{csrf_key}_created", 0)
                
                if not stored_token:
                    return False
                
                # Check token age
                if time.time() - token_created > max_age_seconds:
                    # Token expired, clean up
                    if csrf_key in st.session_state:
                        del st.session_state[csrf_key]
                    if f"{csrf_key}_created" in st.session_state:
                        del st.session_state[f"{csrf_key}_created"]
                    return False
                
                # Validate token match
                return secrets.compare_digest(provided_token, stored_token)
            
            return False
            
        except Exception as e:
            if LOG_SANITIZATION_AVAILABLE:
                self.logger.error(sanitize_log_message(f"Failed to validate CSRF token: {e}", 'ERROR'))
            else:
                self.logger.error(f"Failed to validate CSRF token: {str(e)[:100]}")
            return False
    
    def require_csrf_protection(self, form_id: str, provided_token: Optional[str]) -> Tuple[bool, str]:
        """
        Check CSRF protection for a form submission.
        
        Args:
            form_id: Unique identifier for the form
            provided_token: Token provided with form submission
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not provided_token:
            return False, "CSRF token is required for this operation"
        
        if not self.validate_csrf_token(form_id, provided_token):
            return False, "Invalid or expired CSRF token. Please refresh the page and try again."
        
        return True, ""
    
    def get_csrf_form_field(self, form_id: str) -> Dict[str, str]:
        """
        Get CSRF token and field name for embedding in forms.
        
        Args:
            form_id: Unique identifier for the form
            
        Returns:
            Dictionary with field name and token value
        """
        token = self.generate_csrf_token(form_id)
        return {
            "field_name": "csrf_token",
            "token_value": token
        }


# Global security manager instance
security_manager = StreamlitSecurityManager()


# Convenience functions for easy import
def sanitize_input(value: str, field_name: str = "input") -> str:
    """Sanitize user input from forms."""
    return security_manager.sanitize_form_input(value, field_name)


def sanitize_display(text: str, max_length: int = 1000) -> str:
    """Sanitize text for display."""
    return security_manager.sanitize_display_text(text, max_length)


def validate_form(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate form data for security threats."""
    return security_manager.validate_form_data(data)


def create_safe_client(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create safe client data."""
    return security_manager.create_safe_client_data(form_data)


def create_safe_project(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create safe project data."""
    return security_manager.create_safe_project_data(form_data)


def check_rate_limit(operation_type: str, 
                    user_id: Optional[str] = None,
                    ip_address: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Check if operation is within rate limits."""
    return security_manager.check_rate_limit(operation_type, user_id, ip_address)


def get_rate_limit_stats() -> Dict[str, Any]:
    """Get rate limiting statistics."""
    return security_manager.get_rate_limit_stats()


def reset_rate_limits(operation_type: str,
                     user_id: Optional[str] = None,
                     ip_address: Optional[str] = None):
    """Reset rate limits for specific user/operation."""
    return security_manager.reset_rate_limits(operation_type, user_id, ip_address)


def is_rate_limiting_enabled() -> bool:
    """Check if rate limiting is enabled."""
    return security_manager.is_rate_limiting_enabled()


def check_dos_protection(operation_type: str,
                        endpoint: str = "unknown", 
                        request_size: int = 0,
                        user_id: Optional[str] = None,
                        profile_name: str = "default") -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Apply comprehensive DoS protection including threat detection."""
    return security_manager.check_comprehensive_protection(
        operation_type, endpoint, request_size, user_id, profile_name
    )


def get_dos_protection_stats() -> Dict[str, Any]:
    """Get comprehensive DoS protection statistics."""
    return security_manager.get_dos_protection_stats()


def reset_dos_protection(operation_type: str, user_id: Optional[str] = None):
    """Reset DoS protection for specific user/operation."""
    return security_manager.reset_dos_protection(operation_type, user_id)


def is_dos_protection_enabled() -> bool:
    """Check if DoS protection is enabled."""
    return security_manager.is_dos_protection_enabled()


def create_request_context(endpoint: str = "unknown",
                          request_size: int = 0,
                          user_id: Optional[str] = None) -> Optional[Any]:
    """Create RequestContext for DoS protection."""
    return security_manager.create_request_context(endpoint, request_size, user_id)