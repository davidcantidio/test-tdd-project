"""
Rate Limiting Decorators for Streamlit
Integrates with existing security.py rate limiting
"""

import time
from functools import wraps
from typing import Callable, Optional

# Safe imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

# Import existing rate limiting from security
try:
    from ..utils.security import security_manager
    SECURITY_AVAILABLE = True
    
    # Check if RateLimitExceededException exists
    try:
        from ..utils.security import RateLimitExceededException
    except ImportError:
        class RateLimitExceededException(Exception):
            pass
            
except ImportError:
    SECURITY_AVAILABLE = False
    security_manager = None
    
    class RateLimitExceededException(Exception):
        pass

def rate_limit(operation: str, max_attempts: Optional[int] = None, window_minutes: Optional[int] = None):
    """
    Rate limiting decorator for Streamlit functions
    
    Args:
        operation: Operation name for rate limiting
        max_attempts: Max attempts in window (uses security manager default if None)
        window_minutes: Time window in minutes (uses security manager default if None)
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            if not SECURITY_AVAILABLE or security_manager is None:
                # If security manager not available, proceed without rate limiting
                if STREAMLIT_AVAILABLE and st:
                    st.warning("⚠️ Rate limiting não configurado")
                return func(*args, **kwargs)
            
            try:
                # Check rate limit using existing security manager
                if hasattr(security_manager, 'check_rate_limit'):
                    is_allowed = security_manager.check_rate_limit(
                        operation,
                        max_attempts=max_attempts,
                        window_minutes=window_minutes
                    )
                    
                    if not is_allowed:
                        raise RateLimitExceededException(f"Rate limit exceeded for operation: {operation}")
                
                # Execute function if rate limit allows
                return func(*args, **kwargs)
                
            except RateLimitExceededException:
                # Show user-friendly rate limit message
                if STREAMLIT_AVAILABLE and st:
                    st.error(f"""
                    🚫 **Limite de Tentativas Excedido**
                    
                    Você está fazendo muitas tentativas. 
                    Aguarde alguns minutos antes de tentar novamente.
                    
                    *Operação: {operation}*
                    """)
                    
                    # Optional: Show cooldown timer
                    if hasattr(security_manager, 'get_rate_limit_cooldown'):
                        cooldown = security_manager.get_rate_limit_cooldown(operation)
                        if cooldown > 0:
                            st.info(f"⏱️ Tente novamente em {cooldown} segundos")
                
                return None
                
            except Exception:
                # Let other exceptions bubble up to global handler
                raise
                
        return wrapper
    return decorator

# Specific decorators for common operations
def rate_limit_login(func: Callable) -> Callable:
    """Rate limit login attempts"""
    return rate_limit("login", max_attempts=5, window_minutes=15)(func)

def rate_limit_form_submission(func: Callable) -> Callable:
    """Rate limit form submissions"""  
    return rate_limit("form_submission", max_attempts=20, window_minutes=5)(func)

def rate_limit_api_call(func: Callable) -> Callable:
    """Rate limit API calls"""
    return rate_limit("api_call", max_attempts=100, window_minutes=1)(func)

def rate_limit_search(func: Callable) -> Callable:
    """Rate limit search operations"""
    return rate_limit("search", max_attempts=50, window_minutes=1)(func)

def rate_limit_file_upload(func: Callable) -> Callable:
    """Rate limit file uploads"""
    return rate_limit("file_upload", max_attempts=10, window_minutes=10)(func)

# Helper function to show rate limit status
def show_rate_limit_status(operation: str):
    """Show current rate limit status for operation"""
    
    if SECURITY_AVAILABLE and security_manager and hasattr(security_manager, 'get_rate_limit_status'):
