#!/usr/bin/env python3
"""
🛡️ ENDPOINTS - API Middleware

Middleware for API authentication, rate limiting, and CORS handling.
Integrates with existing Streamlit authentication and rate limiting systems.

Features:
- ✅ API key authentication (optional, falls back to session auth)
- ✅ Rate limiting with different limits for API vs UI
- ✅ CORS headers for external API consumers
- ✅ Request logging and monitoring
- ✅ Error standardization
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import hmac

from ..auth.middleware import is_authenticated, get_current_user
from ..utils.security import check_rate_limit
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole

logger = logging.getLogger(__name__)

class APIAuthenticationError(Exception):
    """Exception for API authentication failures"""
    pass

class APIRateLimitError(Exception):
    """Exception for API rate limit exceeded"""
    pass

def verify_api_key(api_key: str) -> Tuple[bool, Optional[str]]:
    """
    Verify API key with enhanced security validation.
    
    Args:
        api_key: API key to verify
        
    Returns:
        Tuple of (is_valid, user_id)
    """
    if not api_key:
        return False, None
    
    try:
        # Enhanced API key format: tdd_api_{user_id}_{timestamp}_{hmac_hash}
        if not api_key.startswith("tdd_api_"):
            logger.warning("Invalid API key format: missing prefix")
            return False, None
        
        # Minimum length check (security against brute force)
        if len(api_key) < 32:
            logger.warning("Invalid API key format: too short")
            return False, None
        
        # Split key parts
        key_parts = api_key.split("_")
        if len(key_parts) != 4:
            logger.warning("Invalid API key format: incorrect structure")
            return False, None
        
        prefix, api_part, user_id, hash_part = key_parts
        
        # Validate user_id format (alphanumeric, reasonable length)
        if not user_id or len(user_id) < 2 or len(user_id) > 20:
            logger.warning("Invalid API key format: invalid user ID")
            return False, None
        
        # Validate user_id contains only safe characters
        if not user_id.replace('_', '').replace('-', '').isalnum():
            logger.warning("Invalid API key format: user ID contains invalid characters")
            return False, None
        
        # Validate hash part length and format
        if len(hash_part) < 8 or not all(c in '0123456789abcdef' for c in hash_part.lower()):
            logger.warning("Invalid API key format: invalid hash")
            return False, None
        
        # For enhanced security, validate the hash (simplified for demo)
        # In production, this would verify against a stored hash/HMAC
        expected_hash = hashlib.sha256(f"{user_id}_{api_part}_tdd_secret".encode()).hexdigest()[:8]
        if hash_part.lower() != expected_hash.lower():
            logger.warning("Invalid API key: hash verification failed")
            return False, None
        
        # Additional security: check if key format matches expected pattern
        if not _validate_api_key_format(api_key):
            logger.warning("Invalid API key: format validation failed")
            return False, None
        
        logger.info(f"API key validation successful for user: {user_id}")
        return True, user_id
        
    except Exception as e:
        logger.warning(f"API key validation error: {e}")
        return False, None

def _validate_api_key_format(api_key: str) -> bool:
    """
    Additional format validation for API keys.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if format is valid, False otherwise
    """
    try:
        # Check overall length (should be reasonable)
        if len(api_key) < 32 or len(api_key) > 100:
            return False
        
        # Check for any dangerous characters that shouldn't be in API keys
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')']
        if any(char in api_key for char in dangerous_chars):
            return False
        
        # Validate structure more strictly
        parts = api_key.split('_')
        if len(parts) != 4:
            return False
            
        # Each part should have minimum reasonable length
        if any(len(part) < 2 for part in parts[1:]):  # Skip 'tdd' prefix
            return False
            
        return True
        
    except Exception:
        return False

def check_api_rate_limit(request_type: str = "api_request", user_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Check rate limits for API requests with enhanced user-based tracking.
    
    Args:
        request_type: Type of request (api_request, api_heavy, etc.)
        user_id: User ID for rate limiting (optional)
        
    Returns:
        Tuple of (allowed, error_message)
    """
    global _rate_limit_cache
    
    try:
        # Define API-specific rate limits (more restrictive than UI)
        api_rate_configs = {
            "execution": {"requests": 10, "window": 3600},      # 10 execution plans per hour
            "validate": {"requests": 50, "window": 3600},       # 50 validations per hour
            "scoring": {"requests": 30, "window": 3600},        # 30 scoring requests per hour
            "summary": {"requests": 25, "window": 3600},        # 25 summaries per hour
            "presets": {"requests": 100, "window": 3600},       # 100 preset requests per hour
            "api_request": {"requests": 50, "window": 3600},    # General API limit
            "api_heavy": {"requests": 5, "window": 600},        # Heavy operations: 5 per 10 minutes
        }
        
        # Get rate limit configuration
        config = api_rate_configs.get(request_type, api_rate_configs["api_request"])
        max_requests = config["requests"]
        window_seconds = config["window"]
        
        # Create cache key (include user_id for user-specific limits)
        if user_id:
            cache_key = f"api_rate_limit:{request_type}:{user_id}"
        else:
            cache_key = f"api_rate_limit:{request_type}:anonymous"
        
        current_time = time.time()
        
        # Initialize or get existing cache entry
        if cache_key not in _rate_limit_cache:
            _rate_limit_cache[cache_key] = []
        
        request_times = _rate_limit_cache[cache_key]
        
        # Clean old requests outside the window
        cutoff_time = current_time - window_seconds
        request_times = [req_time for req_time in request_times if req_time > cutoff_time]
        _rate_limit_cache[cache_key] = request_times
        
        # Check if limit exceeded
        if len(request_times) >= max_requests:
            oldest_request = min(request_times)
            reset_time = oldest_request + window_seconds
            remaining_seconds = int(reset_time - current_time)
            
            # Enhanced error message for API consumers
            error_message = _create_rate_limit_error_message(
                request_type, max_requests, window_seconds, remaining_seconds
            )
            
            logger.warning(f"API rate limit exceeded for {cache_key}: {len(request_times)}/{max_requests}")
            return False, error_message
        
        # Add current request to cache
        request_times.append(current_time)
        _rate_limit_cache[cache_key] = request_times
        
        # Log successful rate limit check
        remaining_requests = max_requests - len(request_times)
        logger.info(f"API rate limit check passed for {cache_key}: {remaining_requests} requests remaining")
        
        return True, None
        
    except Exception as e:
        logger.error(f"API rate limit check error: {e}")
        # Fail open - allow request but log the error
        return True, None

def _create_rate_limit_error_message(request_type: str, max_requests: int, 
                                   window_seconds: int, remaining_seconds: int) -> str:
    """
    Create user-friendly rate limit error message.
    
    Args:
        request_type: Type of API request
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds
        remaining_seconds: Seconds until limit resets
        
    Returns:
        Formatted error message
    """
    # Convert window to human-readable format
    if window_seconds >= 3600:
        window_str = f"{window_seconds // 3600} hour(s)"
    elif window_seconds >= 60:
        window_str = f"{window_seconds // 60} minute(s)"
    else:
        window_str = f"{window_seconds} second(s)"
    
    # Convert remaining time to human-readable format
    if remaining_seconds >= 3600:
        remaining_str = f"{remaining_seconds // 3600}h {(remaining_seconds % 3600) // 60}m"
    elif remaining_seconds >= 60:
        remaining_str = f"{remaining_seconds // 60}m {remaining_seconds % 60}s"
    else:
        remaining_str = f"{remaining_seconds}s"
    
    return (
        f"API rate limit exceeded for '{request_type}' endpoint. "
        f"Limit: {max_requests} requests per {window_str}. "
        f"Try again in {remaining_str}."
    )

def get_api_rate_limit_status(request_type: str = "api_request", user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get current rate limit status for API monitoring.
    
    Args:
        request_type: Type of request to check
        user_id: User ID for user-specific limits
        
    Returns:
        Dictionary with rate limit status information
    """
    global _rate_limit_cache
    
    try:
        # Get rate limit configuration
        api_rate_configs = {
            "execution": {"requests": 10, "window": 3600},
            "validate": {"requests": 50, "window": 3600},
            "scoring": {"requests": 30, "window": 3600},
            "summary": {"requests": 25, "window": 3600},
            "presets": {"requests": 100, "window": 3600},
            "api_request": {"requests": 50, "window": 3600},
            "api_heavy": {"requests": 5, "window": 600},
        }
        
        config = api_rate_configs.get(request_type, api_rate_configs["api_request"])
        max_requests = config["requests"]
        window_seconds = config["window"]
        
        # Create cache key
        if user_id:
            cache_key = f"api_rate_limit:{request_type}:{user_id}"
        else:
            cache_key = f"api_rate_limit:{request_type}:anonymous"
        
        current_time = time.time()
        
        # Get current request times
        request_times = _rate_limit_cache.get(cache_key, [])
        
        # Clean old requests
        cutoff_time = current_time - window_seconds
        active_requests = [req_time for req_time in request_times if req_time > cutoff_time]
        
        # Calculate status
        requests_used = len(active_requests)
        requests_remaining = max(0, max_requests - requests_used)
        
        # Calculate reset time
        reset_time = None
        if active_requests:
            oldest_request = min(active_requests)
            reset_time = oldest_request + window_seconds
        
        return {
            "request_type": request_type,
            "user_id": user_id,
            "limit": max_requests,
            "window_seconds": window_seconds,
            "requests_used": requests_used,
            "requests_remaining": requests_remaining,
            "reset_time": reset_time,
            "reset_in_seconds": int(reset_time - current_time) if reset_time else None
        }
        
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        return {
            "error": f"Failed to get rate limit status: {str(e)}",
            "request_type": request_type,
            "user_id": user_id
        }

def add_cors_headers() -> Dict[str, str]:
    """
    Add CORS headers for API responses.
    
    Returns:
        Dict of CORS headers
    """
    return {
        "Access-Control-Allow-Origin": "*",  # In production, be more restrictive
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-Key",
        "Access-Control-Max-Age": "86400"
    }

def authenticate_api_request(query_params: Dict[str, str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Authenticate API request using multiple methods.
    
    Args:
        query_params: Query parameters from request
        
    Returns:
        Tuple of (is_authenticated, user_id, auth_method)
    """
    # Method 1: API Key authentication
    api_key = query_params.get("api_key")
    if api_key:
        is_valid, user_id = verify_api_key(api_key)
        if is_valid:
            return True, user_id, "api_key"
        else:
            logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
    
    # Method 2: Session-based authentication (Streamlit session)
    if is_authenticated():
        current_user = get_current_user()
        user_id = current_user.username if current_user else "anonymous"
        return True, user_id, "session"
    
    # No valid authentication found
    return False, None, None

def validate_api_request(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Validate API request with comprehensive security and business logic checks.
    
    Args:
        query_params: Query parameters from the request
        
    Returns:
        Dict with validation results and any errors
    """
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'sanitized_params': {},
        'required_params_present': True,
        'rate_limit_status': 'ok'
    }
    
    try:
        # 1. Check API endpoint parameter
        api_endpoint = query_params.get('api', '')
        if not api_endpoint:
            validation_results['valid'] = False
            validation_results['errors'].append("Missing required 'api' parameter")
            return validation_results
        
        # 2. Validate required parameters for specific endpoints
        required_params = get_required_params(api_endpoint)
        missing_params = []
        
        for param in required_params:
            if param not in query_params:
                missing_params.append(param)
        
        if missing_params:
            validation_results['valid'] = False
            validation_results['required_params_present'] = False
            validation_results['errors'].append(f"Missing required parameters: {', '.join(missing_params)}")
        
        # 3. Sanitize and validate parameter values
        sanitized_params = {}
        for key, value in query_params.items():
            # Basic sanitization
            if isinstance(value, str):
                sanitized_value = value.strip()
                # Remove potentially dangerous characters
                sanitized_value = sanitized_value.replace('<', '').replace('>', '').replace('script', '')
                sanitized_params[key] = sanitized_value
            else:
                sanitized_params[key] = value
        
        validation_results['sanitized_params'] = sanitized_params
        
        # 4. Validate specific parameter formats
        if 'epic_id' in sanitized_params:
            try:
                epic_id = int(sanitized_params['epic_id'])
                if epic_id <= 0:
                    validation_results['valid'] = False
                    validation_results['errors'].append("epic_id must be a positive integer")
            except (ValueError, TypeError):
                validation_results['valid'] = False
                validation_results['errors'].append("epic_id must be a valid integer")
        
        # 5. Check API rate limiting
        is_allowed, rate_limit_msg = check_api_rate_limit(api_endpoint)
        if not is_allowed:
            validation_results['valid'] = False
            validation_results['rate_limit_status'] = 'exceeded'
            validation_results['errors'].append(rate_limit_msg or "Rate limit exceeded")
        
        # 6. Log validation attempt (but don't log sensitive data)
        logger.info(f"API validation for endpoint '{api_endpoint}': {'valid' if validation_results['valid'] else 'invalid'}")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"API request validation error: {e}")
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"],
            'warnings': [],
            'sanitized_params': {},
            'required_params_present': False,
            'rate_limit_status': 'error'
        }

def get_required_params(api_endpoint: str) -> list:
    """
    Get required parameters for each API endpoint.
    
    Args:
        api_endpoint: API endpoint name
        
    Returns:
        List of required parameter names
    """
    param_requirements = {
        "execution": ["epic_id"],
        "validate": ["epic_id"], 
        "scoring": ["epic_id"],
        "summary": ["epic_id"],
        "presets": []
    }
    
    return param_requirements.get(api_endpoint, [])

def log_api_request(query_params: Dict[str, str], user_id: Optional[str], 
                   auth_method: Optional[str], response_time: float = 0.0):
    """
    Log API request for monitoring and analytics.
    
    Args:
        query_params: Request parameters
        user_id: Authenticated user ID
        auth_method: Authentication method used
        response_time: Request processing time in seconds
    """
    api_endpoint = query_params.get("api", "unknown")
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "api_endpoint": api_endpoint,
        "user_id": user_id,
        "auth_method": auth_method,
        "response_time_ms": round(response_time * 1000, 2),
        "parameters": {k: v for k, v in query_params.items() if k not in ["api_key"]},  # Don't log sensitive data
        "request_id": generate_request_id(user_id, api_endpoint)
    }
    
    logger.info(f"API_REQUEST: {log_data}")

def generate_request_id(user_id: Optional[str], api_endpoint: str) -> str:
    """
    Generate unique request ID for tracing.
    
    Args:
        user_id: User ID
        api_endpoint: API endpoint
        
    Returns:
        Unique request ID
    """
    timestamp = str(int(time.time() * 1000))
    user_part = user_id[:8] if user_id else "anon"
    endpoint_part = api_endpoint[:4]
    
    # Create hash for uniqueness
    hash_input = f"{timestamp}{user_part}{endpoint_part}"
    hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    
    return f"req_{timestamp}_{hash_value}"

def create_api_error_response(error_message: str, error_code: str, 
                            details: Optional[Any] = None) -> Dict[str, Any]:
    """
    Create standardized API error response.
    
    Args:
        error_message: Human-readable error message
        error_code: Machine-readable error code
        details: Additional error details
        
    Returns:
        Standardized error response dict
    """
    response = {
        "error": error_message,
        "code": error_code,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        response["details"] = details
    
    return response

def create_api_success_response(data: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create standardized API success response.
    
    Args:
        data: Response data
        metadata: Optional metadata (pagination, etc.)
        
    Returns:
        Standardized success response dict
    """
    response = {
        "success": True,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    if metadata:
        response["metadata"] = metadata
    
    return response

# Example API key generation for development/testing
def generate_dev_api_key(user_id: str) -> str:
    """
    Generate development API key.
    
    Args:
        user_id: User identifier
        
    Returns:
        Development API key
    """
    timestamp = str(int(time.time()))
    key_data = f"{user_id}_{timestamp}"
    return f"tdd_api_{user_id}_{hashlib.md5(key_data.encode()).hexdigest()[:8]}"

# Rate limiting cache (in-memory for demo - use Redis in production)
_rate_limit_cache = {}

def reset_rate_limits():
    """Reset rate limiting cache - for testing purposes."""
    global _rate_limit_cache
    _rate_limit_cache.clear()

# Export functions
__all__ = [
    "authenticate_api_request",
    "validate_api_request", 
    "check_api_rate_limit",
    "get_api_rate_limit_status",
    "verify_api_key",
    "add_cors_headers",
    "log_api_request",
    "create_api_error_response",
    "create_api_success_response",
    "generate_dev_api_key",
    "reset_rate_limits",
    "APIAuthenticationError",
    "APIRateLimitError"
]

