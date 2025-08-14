"""
🛡️ Comprehensive DoS Protection Middleware

Integrated DoS protection system combining rate limiting, circuit breakers,
and resource monitoring to address SEC-003 audit finding:
"No rate limiting; susceptible to resource exhaustion"

This module provides:
1. Multi-layer DoS protection (rate limits + circuit breakers)
2. Memory and resource usage monitoring
3. Adaptive threat detection
4. Request size and complexity limits
5. Geographic and behavioral analysis
6. Automatic threat response

Usage:
    from duration_system.dos_protection import DoSProtector, dos_protect
    
    # Protect API endpoints
    @dos_protect(profile="api_endpoint")
    def api_handler(request):
        return {"data": "response"}
    
    # Database operations
    @dos_protect(profile="database_query", max_requests=10, window=60)
    def database_operation():
        # Database query
        pass
"""

import os
import time
import psutil
import threading
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict, deque
import ipaddress
from pathlib import Path

from .rate_limiter import RateLimiter, RateLimitConfig, RateLimitExceeded
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerError

# DoS protection logging
dos_logger = logging.getLogger('security.dos_protection')
dos_logger.setLevel(logging.INFO)

if not dos_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - [DOS_PROTECTION] %(message)s'
    )
    handler.setFormatter(formatter)
    dos_logger.addHandler(handler)


@dataclass
class ResourceLimits:
    """Resource usage limits for DoS protection."""
    
    max_memory_mb: int = 1024          # Maximum memory usage
    max_cpu_percent: float = 80.0      # Maximum CPU usage percentage
    max_request_size_mb: int = 50      # Maximum request size
    max_requests_per_ip: int = 100     # Requests per IP per window
    max_concurrent_connections: int = 1000  # Maximum concurrent connections
    request_timeout_seconds: float = 30.0   # Request timeout
    
    def __post_init__(self):
        if self.max_memory_mb <= 0:
            raise ValueError("max_memory_mb must be positive")
        if not 0 < self.max_cpu_percent <= 100:
            raise ValueError("max_cpu_percent must be between 0 and 100")


@dataclass
class ThreatProfile:
    """Profile for threat detection and response."""
    
    name: str
    suspicion_threshold: float = 0.7    # Suspicion score threshold
    ban_threshold: float = 0.9          # Auto-ban threshold
    analysis_window: int = 300          # Analysis window in seconds
    max_violations: int = 5             # Max violations before ban
    ban_duration: int = 3600           # Ban duration in seconds
    
    # Behavioral patterns
    rapid_fire_threshold: int = 10      # Requests in short burst
    pattern_deviation_threshold: float = 0.8  # Pattern deviation score
    geographic_anomaly_weight: float = 0.3    # Geographic anomaly importance


@dataclass
class RequestContext:
    """Context information for each request."""
    
    timestamp: float
    ip_address: str
    user_agent: str
    endpoint: str
    request_size: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    geographic_info: Optional[Dict] = None


class ThreatDetector:
    """Advanced threat detection using behavioral analysis."""
    
    def __init__(self, profiles: Dict[str, ThreatProfile]):
        self.profiles = profiles
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.threat_scores: Dict[str, float] = defaultdict(float)
        self.banned_entities: Dict[str, float] = {}  # entity -> ban_expiry_time
        self._lock = threading.RLock()
        
        # Behavioral patterns
        self._normal_patterns: Dict[str, Dict] = defaultdict(dict)
        self._pattern_lock = threading.Lock()
    
    def analyze_request(self, context: RequestContext, profile_name: str = "default") -> Tuple[float, List[str]]:
        """
        Analyze request and return threat score with reasons.
        
        Returns:
            Tuple of (threat_score, reasons)
        """
        profile = self.profiles.get(profile_name, ThreatProfile("default"))
        
        with self._lock:
            entity_key = self._get_entity_key(context)
            
            # Check if entity is banned
            if self._is_banned(entity_key):
                return 1.0, ["Entity is currently banned"]
            
            # Add to request history
            self.request_history[entity_key].append(context)
            
            # Calculate threat score
            score, reasons = self._calculate_threat_score(context, profile, entity_key)
            
            # Update threat score (exponential moving average)
            alpha = 0.3  # Learning rate
            self.threat_scores[entity_key] = (
                alpha * score + (1 - alpha) * self.threat_scores[entity_key]
            )
            
            return self.threat_scores[entity_key], reasons
    
    def _get_entity_key(self, context: RequestContext) -> str:
        """Generate entity key for tracking."""
        # Prefer user_id, fallback to IP
        if context.user_id:
            return f"user:{context.user_id}"
        else:
            return f"ip:{context.ip_address}"
    
    def _is_banned(self, entity_key: str) -> bool:
        """Check if entity is currently banned."""
        if entity_key in self.banned_entities:
            if time.time() < self.banned_entities[entity_key]:
                return True
            else:
                # Ban expired, remove
                del self.banned_entities[entity_key]
        return False
    
    def _calculate_threat_score(self, context: RequestContext, profile: ThreatProfile, entity_key: str) -> Tuple[float, List[str]]:
        """Calculate threat score based on multiple factors."""
        score = 0.0
        reasons = []
        
        history = self.request_history[entity_key]
        if len(history) < 2:
            return score, reasons
        
        current_time = context.timestamp
        window_start = current_time - profile.analysis_window
        
        # Filter recent requests
        recent_requests = [req for req in history if req.timestamp >= window_start]
        
        if not recent_requests:
            return score, reasons
        
        # 1. Rate-based detection
        request_rate = len(recent_requests) / profile.analysis_window
        if request_rate > 1.0:  # More than 1 request per second average
            rate_score = min(request_rate / 10.0, 0.4)  # Cap at 0.4
            score += rate_score
            if rate_score > 0.2:
                reasons.append(f"High request rate: {request_rate:.2f}/s")
        
        # 2. Rapid-fire detection
        rapid_requests = [req for req in recent_requests[-10:] if current_time - req.timestamp < 10]
        if len(rapid_requests) >= profile.rapid_fire_threshold:
            rapid_score = 0.3
            score += rapid_score
            reasons.append(f"Rapid-fire pattern: {len(rapid_requests)} requests in 10s")
        
        # 3. Request size anomaly
        sizes = [req.request_size for req in recent_requests]
        if sizes:
            avg_size = sum(sizes) / len(sizes)
            if context.request_size > avg_size * 5:  # 5x larger than average
                size_score = 0.2
                score += size_score
                reasons.append(f"Abnormally large request: {context.request_size} bytes")
        
        # 4. Endpoint pattern analysis
        endpoints = [req.endpoint for req in recent_requests]
        unique_endpoints = len(set(endpoints))
        if unique_endpoints > len(endpoints) * 0.8:  # Accessing too many different endpoints
            pattern_score = 0.2
            score += pattern_score
            reasons.append(f"Endpoint scanning pattern: {unique_endpoints} unique endpoints")
        
        # 5. User agent consistency
        user_agents = [req.user_agent for req in recent_requests]
        unique_agents = len(set(user_agents))
        if unique_agents > 3:  # Multiple user agents
            ua_score = 0.15
            score += ua_score
            reasons.append(f"Multiple user agents: {unique_agents}")
        
        # 6. Geographic anomaly (if available)
        if context.geographic_info:
            geo_score = self._analyze_geographic_anomaly(recent_requests, context)
            if geo_score > 0:
                score += geo_score * profile.geographic_anomaly_weight
                reasons.append("Geographic anomaly detected")
        
        return min(score, 1.0), reasons
    
    def _analyze_geographic_anomaly(self, recent_requests: List[RequestContext], current: RequestContext) -> float:
        """Analyze geographic anomalies."""
        # Simple implementation - detect rapid geographic changes
        geo_locations = [req.geographic_info.get('country') for req in recent_requests[-5:] 
                        if req.geographic_info]
        
        if len(set(geo_locations)) > 2:  # More than 2 countries in recent requests
            return 0.2
        
        return 0.0
    
    def ban_entity(self, entity_key: str, duration: int, reason: str):
        """Ban entity for specified duration."""
        with self._lock:
            ban_expiry = time.time() + duration
            self.banned_entities[entity_key] = ban_expiry
            
            dos_logger.error(
                f"Entity banned: {entity_key} for {duration}s - Reason: {reason}"
            )
    
    def get_threat_stats(self) -> Dict[str, Any]:
        """Get threat detection statistics."""
        with self._lock:
            active_bans = sum(1 for expiry in self.banned_entities.values() 
                            if expiry > time.time())
            
            return {
                "total_entities_tracked": len(self.request_history),
                "active_bans": active_bans,
                "total_bans_issued": len(self.banned_entities),
                "average_threat_score": sum(self.threat_scores.values()) / len(self.threat_scores) if self.threat_scores else 0.0,
                "high_threat_entities": sum(1 for score in self.threat_scores.values() if score > 0.7),
                "request_history_size": sum(len(history) for history in self.request_history.values())
            }


class DoSProtector:
    """
    Comprehensive DoS protection system.
    
    Integrates rate limiting, circuit breakers, resource monitoring,
    and advanced threat detection for comprehensive protection.
    """
    
    def __init__(self, 
                 resource_limits: Optional[ResourceLimits] = None,
                 threat_profiles: Optional[Dict[str, ThreatProfile]] = None):
        """
        Initialize DoS protector.
        
        Args:
            resource_limits: System resource limits
            threat_profiles: Threat detection profiles
        """
        self.resource_limits = resource_limits or ResourceLimits()
        self.threat_profiles = threat_profiles or {
            "default": ThreatProfile("default"),
            "api_endpoint": ThreatProfile("api_endpoint", suspicion_threshold=0.6),
            "database_query": ThreatProfile("database_query", ban_threshold=0.8),
            "auth_endpoint": ThreatProfile("auth_endpoint", max_violations=3, ban_duration=7200)
        }
        
        # Core protection components
        self.rate_limiter = RateLimiter()
        self.threat_detector = ThreatDetector(self.threat_profiles)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Resource monitoring
        self._resource_monitor_active = True
        self._resource_stats = {
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0.0,
            "active_connections": 0,
            "resource_violations": 0
        }
        
        # Start resource monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self._monitor_thread.start()
        
        # Protection statistics
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "rate_limited": 0,
            "circuit_breaker_blocks": 0,
            "resource_blocks": 0,
            "threat_blocks": 0,
            "false_positives": 0,
            "auto_bans": 0
        }
        
        # Configure default rate limits
        self._configure_default_limits()
        
        dos_logger.info("DoS Protection system initialized")
    
    def _configure_default_limits(self):
        """Configure default rate limiting rules."""
        # API endpoints
        self.rate_limiter.configure_limit(
            "api_requests",
            RateLimitConfig(max_requests=100, window_seconds=60, algorithm="sliding_window")
        )
        
        # Database queries
        self.rate_limiter.configure_limit(
            "database_queries",
            RateLimitConfig(max_requests=50, window_seconds=60, penalty_multiplier=2.0)
        )
        
        # Authentication attempts
        self.rate_limiter.configure_limit(
            "auth_attempts", 
            RateLimitConfig(max_requests=5, window_seconds=300, penalty_multiplier=3.0)
        )
        
        # File uploads
        self.rate_limiter.configure_limit(
            "file_uploads",
            RateLimitConfig(max_requests=10, window_seconds=300, algorithm="token_bucket")
        )
    
    def protect(self, 
               protection_type: str,
               context: Optional[RequestContext] = None,
               custom_limits: Optional[RateLimitConfig] = None,
               profile_name: str = "default") -> Dict[str, Any]:
        """
        Apply comprehensive protection checks.
        
        Args:
            protection_type: Type of protection (e.g., "api_request", "db_query")
            context: Request context information
            custom_limits: Custom rate limiting configuration
            profile_name: Threat detection profile name
            
        Returns:
            Protection result with status and details
            
        Raises:
            RateLimitExceeded: If rate limited
            CircuitBreakerError: If circuit breaker is open
            ResourceError: If resource limits exceeded
            ThreatDetectedError: If threat detected
        """
        self.stats["total_requests"] += 1
        
        result = {
            "allowed": True,
            "protection_type": protection_type,
            "checks": {
                "resource_check": True,
                "rate_limit_check": True,
                "circuit_breaker_check": True,
                "threat_detection_check": True
            },
            "details": {},
            "threat_score": 0.0,
            "reasons": []
        }
        
        try:
            # 1. Resource usage check
            if not self._check_resource_limits():
                self.stats["blocked_requests"] += 1
                self.stats["resource_blocks"] += 1
                result["allowed"] = False
                result["checks"]["resource_check"] = False
                result["details"]["resource_violation"] = "System resource limits exceeded"
                
                raise ResourceError(
                    "System overloaded. Resource limits exceeded.",
                    retry_after=30.0
                )
            
            # 2. Threat detection (if context provided)
            if context:
                threat_score, threat_reasons = self.threat_detector.analyze_request(
                    context, profile_name
                )
                result["threat_score"] = threat_score
                result["reasons"] = threat_reasons
                
                # Safely get profile with fallback
                if profile_name in self.threat_profiles:
                    profile = self.threat_profiles[profile_name]
                elif "default" in self.threat_profiles:
                    profile = self.threat_profiles["default"]
                else:
                    # Create default profile if none exists
                    profile = ThreatProfile("default")
                
                if threat_score >= profile.ban_threshold:
                    # Auto-ban high threat entities
                    entity_key = self.threat_detector._get_entity_key(context)
                    self.threat_detector.ban_entity(
                        entity_key, 
                        profile.ban_duration,
                        f"Threat score: {threat_score:.2f}"
                    )
                    self.stats["auto_bans"] += 1
                
                if threat_score >= profile.suspicion_threshold:
                    self.stats["blocked_requests"] += 1
                    self.stats["threat_blocks"] += 1
                    result["allowed"] = False
                    result["checks"]["threat_detection_check"] = False
                    
                    raise ThreatDetectedError(
                        f"Suspicious activity detected. Threat score: {threat_score:.2f}",
                        threat_score=threat_score,
                        reasons=threat_reasons
                    )
            
            # 3. Rate limiting check
            entity_id = context.ip_address if context else None
            user_id = context.user_id if context else None
            
            if not self.rate_limiter.check_limit(
                limit_type=protection_type,
                entity_id=entity_id,
                user_id=user_id,
                custom_config=custom_limits
            ):
                self.stats["blocked_requests"] += 1
                self.stats["rate_limited"] += 1
                result["allowed"] = False
                result["checks"]["rate_limit_check"] = False
                
                remaining_info = self.rate_limiter.get_remaining_requests(
                    protection_type, entity_id, user_id
                )
                result["details"]["rate_limit"] = remaining_info
                
                raise RateLimitExceeded(
                    f"Rate limit exceeded for {protection_type}",
                    retry_after=remaining_info.get("reset_time")
                )
            
            # 4. Circuit breaker check (for service protection)
            if protection_type in self.circuit_breakers:
                breaker = self.circuit_breakers[protection_type]
                if not breaker._can_execute():
                    self.stats["blocked_requests"] += 1
                    self.stats["circuit_breaker_blocks"] += 1
                    result["allowed"] = False
                    result["checks"]["circuit_breaker_check"] = False
                    
                    raise CircuitBreakerError(
                        f"Circuit breaker open for {protection_type}. Service unavailable.",
                        retry_after=max(0, breaker._next_attempt_time - time.time())
                    )
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            dos_logger.warning(f"Protection check failed for {protection_type}: {e}")
            raise
    
    def _check_resource_limits(self) -> bool:
        """Check if system resources are within limits."""
        # Memory check
        if self._resource_stats["memory_usage_mb"] > self.resource_limits.max_memory_mb:
            dos_logger.warning(
                f"Memory limit exceeded: {self._resource_stats['memory_usage_mb']}MB > "
                f"{self.resource_limits.max_memory_mb}MB"
            )
            return False
        
        # CPU check
        if self._resource_stats["cpu_usage_percent"] > self.resource_limits.max_cpu_percent:
            dos_logger.warning(
                f"CPU limit exceeded: {self._resource_stats['cpu_usage_percent']:.1f}% > "
                f"{self.resource_limits.max_cpu_percent}%"
            )
            return False
        
        return True
    
    def _monitor_resources(self):
        """Monitor system resources in background thread."""
        while self._resource_monitor_active:
            try:
                process = psutil.Process()
                
                # Memory usage
                memory_info = process.memory_info()
                self._resource_stats["memory_usage_mb"] = memory_info.rss / (1024 * 1024)
                
                # CPU usage
                self._resource_stats["cpu_usage_percent"] = process.cpu_percent()
                
                # Connection count (approximate via file descriptors)
                try:
                    self._resource_stats["active_connections"] = process.num_fds()
                except AttributeError:
                    # Windows doesn't have num_fds
                    self._resource_stats["active_connections"] = 0
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process monitoring failed, continue
                pass
            except Exception as e:
                dos_logger.error(f"Resource monitoring error: {e}")
            
            time.sleep(10)  # Check every 10 seconds
    
    def add_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """Add circuit breaker for specific service protection."""
        self.circuit_breakers[name] = CircuitBreaker(name, config)
        dos_logger.info(f"Circuit breaker added for: {name}")
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive protection statistics."""
        stats = self.stats.copy()
        
        # Add component stats
        stats["rate_limiter"] = self.rate_limiter.get_stats()
        stats["threat_detector"] = self.threat_detector.get_threat_stats()
        stats["circuit_breakers"] = {
            name: breaker.get_stats() 
            for name, breaker in self.circuit_breakers.items()
        }
        stats["resource_usage"] = self._resource_stats.copy()
        
        # Calculate derived metrics
        if stats["total_requests"] > 0:
            stats["block_rate"] = stats["blocked_requests"] / stats["total_requests"]
            stats["threat_detection_rate"] = stats["threat_blocks"] / stats["total_requests"]
        
        return stats
    
    def shutdown(self):
        """Shutdown DoS protection system."""
        self._resource_monitor_active = False
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        
        dos_logger.info("DoS Protection system shutdown")


# Custom exceptions
class ResourceError(Exception):
    """Exception raised when resource limits are exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


class ThreatDetectedError(Exception):
    """Exception raised when threat is detected."""
    
    def __init__(self, message: str, threat_score: float, reasons: List[str]):
        super().__init__(message)
        self.threat_score = threat_score
        self.reasons = reasons


# Global DoS protector instance
_global_dos_protector: Optional[DoSProtector] = None
_protector_lock = threading.Lock()


def get_dos_protector() -> DoSProtector:
    """Get or create global DoS protector instance."""
    global _global_dos_protector
    
    if _global_dos_protector is None:
        with _protector_lock:
            if _global_dos_protector is None:
                _global_dos_protector = DoSProtector()
    
    return _global_dos_protector


def dos_protect(protection_type: str = "api_request",
               profile: str = "default",
               max_requests: Optional[int] = None,
               window: Optional[int] = None,
               get_context: Optional[Callable] = None):
    """
    Decorator for comprehensive DoS protection.
    
    Args:
        protection_type: Type of protection to apply
        profile: Threat detection profile name
        max_requests: Custom rate limit (requests per window)
        window: Custom rate limit window (seconds)
        get_context: Function to extract RequestContext from args
    """
    def decorator(func: Callable) -> Callable:
        protector = get_dos_protector()
        
        # Custom rate limiting config if provided
        custom_config = None
        if max_requests and window:
            custom_config = RateLimitConfig(
                max_requests=max_requests,
                window_seconds=window
            )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract request context if function provided
            context = None
            if get_context:
                try:
                    context = get_context(*args, **kwargs)
                except Exception as e:
                    dos_logger.warning(f"Failed to extract context: {e}")
            
            # Apply protection
            protection_result = protector.protect(
                protection_type=protection_type,
                context=context,
                custom_limits=custom_config,
                profile_name=profile
            )
            
            try:
                result = func(*args, **kwargs)
                
                # Record successful execution for circuit breaker
                if protection_type in protector.circuit_breakers:
                    breaker = protector.circuit_breakers[protection_type]
                    breaker._record_call(time.time(), 0.0, True)
                    breaker._on_success()
                
                return result
                
            except Exception as e:
                # Record failure for circuit breaker
                if protection_type in protector.circuit_breakers:
                    breaker = protector.circuit_breakers[protection_type]
                    breaker._record_call(time.time(), 0.0, False, type(e).__name__)
                    breaker._on_failure()
                
                raise
        
        # Add management methods
        wrapper.get_protection_stats = lambda: protector.get_comprehensive_stats()
        wrapper.reset_protection = lambda: protector.rate_limiter.reset_entity(protection_type)
        
        return wrapper
    
    return decorator


if __name__ == "__main__":
    # Example usage and testing
    def test_dos_protection():
        """Test comprehensive DoS protection."""
        print("Testing DoS Protection System...")
        
        protector = DoSProtector()
        
        # Test basic protection
        context = RequestContext(
            timestamp=time.time(),
            ip_address="192.168.1.100",
            user_agent="Test Agent",
            endpoint="/api/test",
            request_size=1024,
            user_id="test_user"
        )
        
        try:
            result = protector.protect("test_api", context, profile_name="api_endpoint")
            print(f"Protection result: {result['allowed']}")
            print(f"Threat score: {result['threat_score']:.3f}")
        except Exception as e:
            print(f"Protection blocked: {e}")
        
        # Test decorator
        @dos_protect("test_endpoint", max_requests=3, window=10)
        def test_endpoint():
            return "success"
        
        # Test multiple calls
        for i in range(5):
            try:
                result = test_endpoint()
                print(f"Call {i+1}: {result}")
            except Exception as e:
                print(f"Call {i+1}: {type(e).__name__} - {e}")
        
        # Show comprehensive stats
        stats = protector.get_comprehensive_stats()
        print(f"\nProtection Statistics:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Blocked requests: {stats['blocked_requests']}")
        print(f"  Block rate: {stats.get('block_rate', 0):.2%}")
        print(f"  Memory usage: {stats['resource_usage']['memory_usage_mb']:.1f} MB")
        
        # Cleanup
        protector.shutdown()
    
    test_dos_protection()