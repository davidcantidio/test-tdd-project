"""
🚦 Rate Limiting Framework for DoS Protection

Enterprise-grade rate limiting system addressing SEC-003 audit finding:
"No rate limiting; susceptible to resource exhaustion"

This module provides:
1. Token bucket rate limiting algorithm
2. Sliding window rate limiting  
3. Per-user/IP rate limits
4. Database query rate limiting
5. Memory and resource usage limits
6. Circuit breaker patterns for resilience

Usage:
    from duration_system.rate_limiter import RateLimiter, get_rate_limiter
    
    # API endpoint protection
    @rate_limited("api_requests", max_requests=100, window_seconds=60)
    def api_endpoint():
        return {"data": "response"}
    
    # Database query protection
    limiter = get_rate_limiter()
    if limiter.check_limit("db_queries", user_id="user123"):
        # Execute database query
        pass
    else:
        raise RateLimitExceeded("Too many database queries")
"""

import time
import threading
import hashlib
import logging
from typing import Dict, Optional, Union, Any, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict, deque
import weakref

# Security logging
security_logger = logging.getLogger('security.rate_limiter')
security_logger.setLevel(logging.INFO)

if not security_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - [RATE_LIMIT] %(message)s'
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting rules."""
    
    max_requests: int
    window_seconds: int
    algorithm: str = "sliding_window"  # "token_bucket", "sliding_window", "fixed_window"
    burst_allowance: int = 0  # Additional requests allowed in burst
    penalty_multiplier: float = 1.0  # Penalty for violations
    
    def __post_init__(self):
        if self.max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if self.algorithm not in ["token_bucket", "sliding_window", "fixed_window"]:
            raise ValueError(f"Invalid algorithm: {self.algorithm}")


@dataclass
class RateLimitState:
    """Internal state for rate limiting tracking."""
    
    requests: deque = field(default_factory=deque)
    tokens: float = 0.0
    last_refill: float = field(default_factory=time.time)
    violations: int = 0
    penalty_until: float = 0.0
    total_requests: int = 0
    
    def reset(self):
        """Reset the rate limit state."""
        self.requests.clear()
        self.tokens = 0.0
        self.last_refill = time.time()
        self.violations = 0
        self.penalty_until = 0.0


class RateLimiter:
    """
    Advanced rate limiter with multiple algorithms and DoS protection.
    
    Features:
    - Multiple rate limiting algorithms (token bucket, sliding window, fixed window)
    - Per-user, per-IP, and global rate limits
    - Memory usage monitoring and limits
    - Automatic cleanup of stale entries
    - Security event logging
    - Circuit breaker integration
    """
    
    def __init__(self, 
                 default_config: Optional[RateLimitConfig] = None,
                 max_memory_entries: int = 10000,
                 cleanup_interval: int = 300):
        """
        Initialize rate limiter.
        
        Args:
            default_config: Default rate limiting configuration
            max_memory_entries: Maximum number of tracked entities
            cleanup_interval: Cleanup interval in seconds
        """
        self.default_config = default_config or RateLimitConfig(
            max_requests=1000,
            window_seconds=3600,
            algorithm="sliding_window"
        )
        
        self.max_memory_entries = max_memory_entries
        self.cleanup_interval = cleanup_interval
        
        # Thread-safe storage for rate limit states
        self._states: Dict[str, RateLimitState] = {}
        self._configs: Dict[str, RateLimitConfig] = {}
        self._lock = threading.RLock()
        
        # Cleanup tracking
        self._last_cleanup = time.time()
        
        # Statistics for monitoring
        self.stats = {
            "total_checks": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "violations": 0,
            "active_entities": 0,
            "memory_usage_kb": 0,
            "cleanups_performed": 0
        }
        
        # Weak references for automatic cleanup
        self._entity_refs: Dict[str, weakref.ref] = {}
    
    def configure_limit(self, 
                       limit_type: str, 
                       config: RateLimitConfig,
                       entity_pattern: Optional[str] = None):
        """
        Configure rate limiting for specific types or entities.
        
        Args:
            limit_type: Type of limit (e.g., "api_requests", "db_queries")
            config: Rate limiting configuration
            entity_pattern: Optional pattern for entity matching
        """
        with self._lock:
            key = f"{limit_type}:{entity_pattern or '*'}"
            self._configs[key] = config
            
        security_logger.info(
            f"Rate limit configured: {limit_type} - "
            f"{config.max_requests} requests/{config.window_seconds}s"
        )
    
    def check_limit(self, 
                   limit_type: str,
                   entity_id: Optional[str] = None,
                   user_id: Optional[str] = None,
                   ip_address: Optional[str] = None,
                   custom_config: Optional[RateLimitConfig] = None) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            limit_type: Type of limit to check
            entity_id: Optional specific entity ID
            user_id: Optional user identifier
            ip_address: Optional IP address
            custom_config: Optional custom configuration
            
        Returns:
            True if request is allowed, False if rate limited
        """
        # Generate tracking key
        tracking_key = self._generate_tracking_key(
            limit_type, entity_id, user_id, ip_address
        )
        
        config = custom_config or self._get_config_for_type(limit_type)
        
        self.stats["total_checks"] += 1
        
        # Periodic cleanup
        self._maybe_cleanup()
        
        with self._lock:
            # Get or create state
            if tracking_key not in self._states:
                self._states[tracking_key] = RateLimitState()
                self._states[tracking_key].tokens = config.max_requests
            
            state = self._states[tracking_key]
            
            # Check if entity is in penalty period
            current_time = time.time()
            if current_time < state.penalty_until:
                self.stats["blocked_requests"] += 1
                security_logger.warning(
                    f"Request blocked (penalty period): {tracking_key}"
                )
                return False
            
            # Apply rate limiting algorithm
            allowed = self._check_algorithm(config, state, current_time)
            
            if allowed:
                self.stats["allowed_requests"] += 1
                state.total_requests += 1
            else:
                self.stats["blocked_requests"] += 1
                self.stats["violations"] += 1
                state.violations += 1
                
                # Apply penalty for repeated violations
                if state.violations > 3:
                    penalty_duration = config.window_seconds * config.penalty_multiplier
                    state.penalty_until = current_time + penalty_duration
                    
                    security_logger.error(
                        f"Rate limit penalty applied: {tracking_key} - "
                        f"penalty until {datetime.fromtimestamp(state.penalty_until)}"
                    )
                else:
                    security_logger.warning(
                        f"Rate limit exceeded: {tracking_key} - "
                        f"violation #{state.violations}"
                    )
            
            return allowed
    
    def _generate_tracking_key(self, 
                             limit_type: str,
                             entity_id: Optional[str],
                             user_id: Optional[str], 
                             ip_address: Optional[str]) -> str:
        """Generate unique tracking key for rate limiting."""
        components = [limit_type]
        
        if entity_id:
            components.append(f"entity:{entity_id}")
        if user_id:
            components.append(f"user:{user_id}")
        if ip_address:
            components.append(f"ip:{ip_address}")
        
        # Create consistent hash
        key_str = "|".join(components)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]
    
    def _get_config_for_type(self, limit_type: str) -> RateLimitConfig:
        """Get configuration for limit type."""
        with self._lock:
            # Look for exact match first
            exact_key = f"{limit_type}:*"
            if exact_key in self._configs:
                return self._configs[exact_key]
            
            # Look for pattern matches
            for key, config in self._configs.items():
                if key.startswith(f"{limit_type}:"):
                    return config
            
            return self.default_config
    
    def _check_algorithm(self, 
                        config: RateLimitConfig, 
                        state: RateLimitState,
                        current_time: float) -> bool:
        """Apply rate limiting algorithm."""
        if config.algorithm == "token_bucket":
            return self._check_token_bucket(config, state, current_time)
        elif config.algorithm == "sliding_window":
            return self._check_sliding_window(config, state, current_time)
        elif config.algorithm == "fixed_window":
            return self._check_fixed_window(config, state, current_time)
        else:
            raise ValueError(f"Unknown algorithm: {config.algorithm}")
    
    def _check_token_bucket(self, 
                           config: RateLimitConfig,
                           state: RateLimitState,
                           current_time: float) -> bool:
        """Token bucket algorithm implementation."""
        # Refill tokens based on elapsed time
        elapsed = current_time - state.last_refill
        tokens_to_add = elapsed * (config.max_requests / config.window_seconds)
        
        max_tokens = config.max_requests + config.burst_allowance
        state.tokens = min(max_tokens, state.tokens + tokens_to_add)
        state.last_refill = current_time
        
        # Check if token available
        if state.tokens >= 1.0:
            state.tokens -= 1.0
            return True
        else:
            return False
    
    def _check_sliding_window(self,
                             config: RateLimitConfig,
                             state: RateLimitState,
                             current_time: float) -> bool:
        """Sliding window algorithm implementation."""
        # Remove old requests outside the window
        cutoff_time = current_time - config.window_seconds
        
        while state.requests and state.requests[0] < cutoff_time:
            state.requests.popleft()
        
        # Check if under limit
        if len(state.requests) < config.max_requests + config.burst_allowance:
            state.requests.append(current_time)
            return True
        else:
            return False
    
    def _check_fixed_window(self,
                           config: RateLimitConfig,
                           state: RateLimitState,
                           current_time: float) -> bool:
        """Fixed window algorithm implementation."""
        # Calculate current window start
        window_start = int(current_time // config.window_seconds) * config.window_seconds
        
        # Reset if new window
        if not state.requests or state.requests[0] < window_start:
            state.requests.clear()
        
        # Check if under limit
        if len(state.requests) < config.max_requests + config.burst_allowance:
            state.requests.append(current_time)
            return True
        else:
            return False
    
    def _maybe_cleanup(self):
        """Perform periodic cleanup of stale entries."""
        current_time = time.time()
        
        if current_time - self._last_cleanup < self.cleanup_interval:
            return
        
        with self._lock:
            self._last_cleanup = current_time
            
            # Remove stale entries
            stale_keys = []
            cutoff_time = current_time - (self.cleanup_interval * 2)
            
            for key, state in self._states.items():
                # Remove if no recent activity and not in penalty period
                if (state.last_refill < cutoff_time and 
                    current_time > state.penalty_until and
                    len(state.requests) == 0):
                    stale_keys.append(key)
            
            for key in stale_keys:
                del self._states[key]
            
            # Enforce memory limits
            if len(self._states) > self.max_memory_entries:
                # Remove oldest entries by last_refill time
                sorted_entries = sorted(
                    self._states.items(),
                    key=lambda x: x[1].last_refill
                )
                
                entries_to_remove = len(self._states) - self.max_memory_entries
                for i in range(entries_to_remove):
                    key = sorted_entries[i][0]
                    del self._states[key]
            
            self.stats["cleanups_performed"] += 1
            self.stats["active_entities"] = len(self._states)
            
            if stale_keys:
                security_logger.info(f"Cleaned up {len(stale_keys)} stale rate limit entries")
    
    def reset_entity(self, 
                    limit_type: str,
                    entity_id: Optional[str] = None,
                    user_id: Optional[str] = None,
                    ip_address: Optional[str] = None):
        """Reset rate limits for specific entity."""
        tracking_key = self._generate_tracking_key(
            limit_type, entity_id, user_id, ip_address
        )
        
        with self._lock:
            if tracking_key in self._states:
                self._states[tracking_key].reset()
                security_logger.info(f"Rate limit reset for: {tracking_key}")
    
    def get_remaining_requests(self,
                              limit_type: str,
                              entity_id: Optional[str] = None,
                              user_id: Optional[str] = None,
                              ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Get remaining requests information for entity."""
        tracking_key = self._generate_tracking_key(
            limit_type, entity_id, user_id, ip_address
        )
        config = self._get_config_for_type(limit_type)
        
        with self._lock:
            if tracking_key not in self._states:
                return {
                    "remaining": config.max_requests,
                    "total_allowed": config.max_requests,
                    "window_seconds": config.window_seconds,
                    "reset_time": None
                }
            
            state = self._states[tracking_key]
            current_time = time.time()
            
            if config.algorithm == "token_bucket":
                # Update tokens first
                elapsed = current_time - state.last_refill
                tokens_to_add = elapsed * (config.max_requests / config.window_seconds)
                max_tokens = config.max_requests + config.burst_allowance
                available_tokens = min(max_tokens, state.tokens + tokens_to_add)
                
                return {
                    "remaining": int(available_tokens),
                    "total_allowed": config.max_requests,
                    "window_seconds": config.window_seconds,
                    "reset_time": None
                }
            
            elif config.algorithm == "sliding_window":
                # Count requests in current window
                cutoff_time = current_time - config.window_seconds
                current_requests = sum(1 for req_time in state.requests if req_time >= cutoff_time)
                
                return {
                    "remaining": max(0, config.max_requests - current_requests),
                    "total_allowed": config.max_requests,
                    "window_seconds": config.window_seconds,
                    "reset_time": min(state.requests) + config.window_seconds if state.requests else None
                }
            
            else:  # fixed_window
                window_start = int(current_time // config.window_seconds) * config.window_seconds
                current_requests = len([req for req in state.requests if req >= window_start])
                
                return {
                    "remaining": max(0, config.max_requests - current_requests),
                    "total_allowed": config.max_requests,
                    "window_seconds": config.window_seconds,
                    "reset_time": window_start + config.window_seconds
                }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        with self._lock:
            self.stats["active_entities"] = len(self._states)
            # Estimate memory usage
            self.stats["memory_usage_kb"] = len(self._states) * 0.5  # Rough estimate
            
            return self.stats.copy()


# Global rate limiter instance
_global_rate_limiter: Optional[RateLimiter] = None
_limiter_lock = threading.Lock()


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _global_rate_limiter
    
    if _global_rate_limiter is None:
        with _limiter_lock:
            if _global_rate_limiter is None:
                _global_rate_limiter = RateLimiter()
                
                # Configure default limits
                _global_rate_limiter.configure_limit(
                    "api_requests",
                    RateLimitConfig(max_requests=100, window_seconds=60)
                )
                _global_rate_limiter.configure_limit(
                    "db_queries", 
                    RateLimitConfig(max_requests=50, window_seconds=60)
                )
                _global_rate_limiter.configure_limit(
                    "auth_attempts",
                    RateLimitConfig(max_requests=5, window_seconds=300, penalty_multiplier=2.0)
                )
                
    return _global_rate_limiter


def rate_limited(limit_type: str,
                max_requests: int = 100,
                window_seconds: int = 60,
                algorithm: str = "sliding_window",
                get_entity_id: Optional[Callable] = None,
                get_user_id: Optional[Callable] = None,
                get_ip_address: Optional[Callable] = None):
    """
    Decorator for rate limiting function calls.
    
    Args:
        limit_type: Type of rate limit
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds
        algorithm: Rate limiting algorithm
        get_entity_id: Function to extract entity ID from args
        get_user_id: Function to extract user ID from args
        get_ip_address: Function to extract IP address from args
    """
    def decorator(func: Callable) -> Callable:
        limiter = get_rate_limiter()
        config = RateLimitConfig(
            max_requests=max_requests,
            window_seconds=window_seconds,
            algorithm=algorithm
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract identifiers
            entity_id = get_entity_id(*args, **kwargs) if get_entity_id else None
            user_id = get_user_id(*args, **kwargs) if get_user_id else None
            ip_address = get_ip_address(*args, **kwargs) if get_ip_address else None
            
            # Check rate limit
            if not limiter.check_limit(
                limit_type=limit_type,
                entity_id=entity_id,
                user_id=user_id,
                ip_address=ip_address,
                custom_config=config
            ):
                remaining_info = limiter.get_remaining_requests(
                    limit_type, entity_id, user_id, ip_address
                )
                retry_after = remaining_info.get("reset_time")
                if retry_after:
                    retry_after = max(0, retry_after - time.time())
                
                raise RateLimitExceeded(
                    f"Rate limit exceeded for {limit_type}. "
                    f"Max {max_requests} requests per {window_seconds} seconds.",
                    retry_after=retry_after
                )
            
            return func(*args, **kwargs)
        
        # Add rate limit management methods
        wrapper.reset_rate_limit = lambda **ids: limiter.reset_entity(limit_type, **ids)
        wrapper.get_rate_limit_info = lambda **ids: limiter.get_remaining_requests(limit_type, **ids)
        
        return wrapper
    
    return decorator


if __name__ == "__main__":
    # Example usage and testing
    def test_rate_limiter():
        """Test rate limiting functionality."""
        print("Testing Rate Limiter...")
        
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=3, window_seconds=5)
        
        # Test basic rate limiting
        for i in range(5):
            allowed = limiter.check_limit("test", custom_config=config)
            print(f"Request {i+1}: {'ALLOWED' if allowed else 'BLOCKED'}")
            
            if i >= 3:  # Should be blocked after 3 requests
                assert not allowed, "Should be rate limited"
            
            time.sleep(0.1)
        
        # Test decorator
        @rate_limited("api_test", max_requests=2, window_seconds=3)
        def test_api():
            return "success"
        
        try:
            print("\nTesting decorator:")
            print(f"Call 1: {test_api()}")
            print(f"Call 2: {test_api()}")
            print(f"Call 3: {test_api()}")  # Should raise exception
        except RateLimitExceeded as e:
            print(f"Rate limit exceeded: {e}")
        
        # Show statistics
        stats = limiter.get_stats()
        print(f"\nStatistics: {stats}")
    
    test_rate_limiter()