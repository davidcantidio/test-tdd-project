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

logger = logging.getLogger(__name__)

class APIAuthenticationError(Exception):
    """Exception for API authentication failures"""
    pass

class APIRateLimitError(Exception):
    """Exception for API rate limit exceeded"""
    pass

def verify_api_key(api_key: str) -> Tuple[bool, Optional[str]]:
    """
    Verify API key if provided.
    
    Args:
        api_key: API key to verify
        
    Returns:
        Tuple of (is_valid, user_id)
    """
    if not api_key:
        return False, None
    
    # For demo purposes, accept a simple API key format
    # In production, this would check against a database of API keys
    if api_key.startswith("tdd_api_"):
        # Extract user identifier from API key
        try:
            # Simple validation - in production use proper key validation
            key_parts = api_key.split("_")
            if len(key_parts) >= 3:
                user_id = key_parts[2]
                return True, user_id
        except Exception as e:
            logger.warning(f"API key validation error: {e}")
    
    return False, None

def check_api_rate_limit(request_type: str = "api_request", user_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Check rate limits for API requests with specific limits.
    
    Args:
        request_type: Type of request (api_request, api_heavy, etc.)
        user_id: User ID for rate limiting (optional)
        
    Returns:
        Tuple of (allowed, error_message)
    """
    # Use more restrictive rate limits for API calls
    api_rate_configs = {
        "api_request": {"requests": 100, "window": 3600},  # 100 per hour
        "api_heavy": {"requests": 10, "window": 600},      # 10 per 10 minutes
        "api_execution": {"requests": 20, "window": 3600}  # 20 execution plans per hour
    }
    
    # For now, use the existing rate limiting system
    # TODO: Implement API-specific rate limiting with user-based limits
    return check_rate_limit(request_type)

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
    Comprehensive API request validation.
    
    Args:
        query_params: Query parameters from request
        
    Returns:
        Dict with validation results and user info
    """
    validation_result = {
        "success": False,
        "user_id": None,
        "auth_method": None,
        "rate_limit_ok": False,
        "errors": []
    }
    
    try:
        # 1. Authentication check
        is_auth, user_id, auth_method = authenticate_api_request(query_params)
        if not is_auth:
            validation_result["errors"].append("Authentication required")
            return validation_result
        
        validation_result["user_id"] = user_id
        validation_result["auth_method"] = auth_method
        
        # 2. Rate limiting check
        api_endpoint = query_params.get("api", "unknown")
        rate_limit_type = "api_heavy" if api_endpoint == "execution" else "api_request"
        
        rate_ok, rate_error = check_api_rate_limit(rate_limit_type, user_id)
        if not rate_ok:
            validation_result["errors"].append(f"Rate limit exceeded: {rate_error}")
            return validation_result
        
        validation_result["rate_limit_ok"] = True
        
        # 3. Parameter validation
        required_params = get_required_params(api_endpoint)
        for param in required_params:
            if param not in query_params:
                validation_result["errors"].append(f"Missing required parameter: {param}")
        
        if validation_result["errors"]:
            return validation_result
        
        validation_result["success"] = True
        return validation_result
        
    except Exception as e:
        logger.error(f"API validation error: {e}")
        validation_result["errors"].append(f"Validation error: {str(e)}")
        return validation_result

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
    "add_cors_headers",
    "log_api_request",
    "create_api_error_response",
    "create_api_success_response",
    "generate_dev_api_key",
    "APIAuthenticationError",
    "APIRateLimitError"
]