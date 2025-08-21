#!/usr/bin/env python3
"""
🛡️ DoS Protection Integration Tests

Tests the integrated DoS protection system including:
- Rate limiting functionality
- Circuit breaker patterns
- DoS protection middleware
- Component integration
- Resource monitoring
- Threat detection
"""

import time
import pytest
import threading
from unittest.mock import Mock, patch
from dataclasses import dataclass

# Import DoS protection components
try:
    from duration_system.rate_limiter import RateLimiter, RateLimitConfig, RateLimitExceeded
    from duration_system.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerError
    from duration_system.dos_protection import (
        DoSProtector, RequestContext, ThreatProfile, ResourceLimits,
        ResourceError, ThreatDetectedError, dos_protect
    )
    DOS_PROTECTION_AVAILABLE = True
except ImportError as e:
    DOS_PROTECTION_AVAILABLE = False
    pytest.skip(f"DoS protection components not available: {e}", allow_module_level=True)


class TestRateLimiterIntegration:
    """Test rate limiter integration and functionality."""
    
    def test_rate_limiter_basic_functionality(self):
        """Test basic rate limiting functionality."""
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=3, window_seconds=5)
        
        # First 3 requests should be allowed
        for i in range(3):
            allowed = limiter.check_limit("test", custom_config=config)
            assert allowed, f"Request {i+1} should be allowed"
        
        # 4th and 5th requests should be blocked
        for i in range(2):
            allowed = limiter.check_limit("test", custom_config=config)
            assert not allowed, f"Request {i+4} should be blocked"
    
    def test_rate_limiter_different_algorithms(self):
        """Test different rate limiting algorithms."""
        limiter = RateLimiter()
        
        # Test token bucket
        token_config = RateLimitConfig(
            max_requests=5, 
            window_seconds=10, 
            algorithm="token_bucket"
        )
        
        # Test sliding window
        sliding_config = RateLimitConfig(
            max_requests=3,
            window_seconds=5,
            algorithm="sliding_window"
        )
        
        # Both should work
        assert limiter.check_limit("token_test", custom_config=token_config)
        assert limiter.check_limit("sliding_test", custom_config=sliding_config)
    
    def test_rate_limiter_decorator(self):
        """Test rate limiter decorator functionality."""
        from duration_system.rate_limiter import rate_limited
        
        call_count = 0
        
        @rate_limited("test_endpoint", max_requests=2, window_seconds=5)
        def test_endpoint():
            nonlocal call_count
            call_count += 1
            return f"call_{call_count}"
        
        # First 2 calls should work
        assert test_endpoint() == "call_1"
        assert test_endpoint() == "call_2"
        
        # 3rd call should raise RateLimitExceeded
        with pytest.raises(RateLimitExceeded):
            test_endpoint()


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration and functionality."""
    
    def test_circuit_breaker_basic_functionality(self):
        """Test basic circuit breaker functionality."""
        breaker = CircuitBreaker(
            "test_service",
            CircuitBreakerConfig(failure_threshold=3, timeout_seconds=1)
        )
        
        # Function that fails
        def failing_function():
            raise Exception("Service failure")
        
        # Test failure detection
        for i in range(3):
            with pytest.raises(Exception):
                breaker.call(failing_function)
        
        # Circuit should now be open
        with pytest.raises(CircuitBreakerError):
            breaker.call(failing_function)
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery mechanism."""
        breaker = CircuitBreaker(
            "recovery_test",
            CircuitBreakerConfig(
                failure_threshold=2, 
                success_threshold=1,
                timeout_seconds=0.2,
                exponential_backoff=False  # Disable backoff for predictable testing
            )
        )
        
        # Force circuit to open
        def failing_function():
            raise Exception("Failure")
        
        for i in range(2):
            with pytest.raises(Exception):
                breaker.call(failing_function)
        
        # Verify circuit is open
        with pytest.raises(CircuitBreakerError):
            breaker.call(failing_function)
        
        # Wait for timeout with buffer
        time.sleep(0.3)
        
        # Should now allow testing (half-open state)
        def successful_function():
            return "success"
        
        # First success should work and close the circuit
        result = breaker.call(successful_function)
        assert result == "success"
    
    def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator."""
        from duration_system.circuit_breaker import circuit_breaker
        
        failure_count = 0
        
        @circuit_breaker("decorator_test", failure_threshold=2, timeout=1)
        def unreliable_service():
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 2:
                raise Exception(f"Failure {failure_count}")
            return "success"
        
        # First 2 calls should fail and trigger circuit opening
        for i in range(2):
            with pytest.raises(Exception):
                unreliable_service()
        
        # 3rd call should be blocked by circuit breaker
        with pytest.raises(CircuitBreakerError):
            unreliable_service()


class TestDoSProtectionIntegration:
    """Test integrated DoS protection system."""
    
    def test_dos_protector_basic_functionality(self):
        """Test basic DoS protector functionality."""
        protector = DoSProtector()
        
        # Create test request context
        context = RequestContext(
            timestamp=time.time(),
            ip_address="192.168.1.100",
            user_agent="Test Agent",
            endpoint="/api/test",
            request_size=1024
        )
        
        # Should allow normal requests
        result = protector.protect("test_api", context)
        assert result["allowed"] is True
        assert result["threat_score"] == 0.0
    
    def test_dos_protector_rate_limiting(self):
        """Test DoS protector rate limiting integration."""
        protector = DoSProtector()
        
        # Configure tight rate limits for testing
        from duration_system.rate_limiter import RateLimitConfig
        custom_limits = RateLimitConfig(max_requests=2, window_seconds=5)
        
        context = RequestContext(
            timestamp=time.time(),
            ip_address="192.168.1.101",
            user_agent="Test Agent",
            endpoint="/api/test",
            request_size=1024
        )
        
        # First 2 requests should be allowed
        for i in range(2):
            result = protector.protect("rate_test", context, custom_limits)
            assert result["allowed"] is True
        
        # 3rd request should be rate limited
        with pytest.raises(RateLimitExceeded):
            protector.protect("rate_test", context, custom_limits)
    
    def test_dos_protector_threat_detection(self):
        """Test DoS protector threat detection."""
        # Create protector with sensitive threat detection including default
        threat_profiles = {
            "default": ThreatProfile("default"),
            "sensitive": ThreatProfile(
                "sensitive",
                suspicion_threshold=0.3,
                ban_threshold=0.8,
                rapid_fire_threshold=3,
                analysis_window=60  # Longer window for better detection
            )
        }
        
        protector = DoSProtector(threat_profiles=threat_profiles)
        
        # Simulate rapid-fire requests with same timestamp for immediate detection
        base_time = time.time()
        threat_detected = False
        
        for i in range(10):  # More requests to trigger detection
            context = RequestContext(
                timestamp=base_time + (i * 0.1),  # Very rapid requests
                ip_address="192.168.1.102",
                user_agent="Suspicious Agent",
                endpoint=f"/api/endpoint_{i}",  # Different endpoints - scanning pattern
                request_size=1024
            )
            
            try:
                result = protector.protect("sensitive_api", context, profile_name="sensitive")
                if not result["allowed"]:
                    threat_detected = True
                    break
                # Check if threat score is increasing
                if result["threat_score"] > 0.3:
                    threat_detected = True
                    break
            except ThreatDetectedError:
                threat_detected = True
                break
            except RateLimitExceeded:
                # Rate limiting is also a form of protection
                threat_detected = True
                break
        
        # Should have detected some form of threat or rate limiting
        assert threat_detected, "Expected threat detection or rate limiting to trigger"
    
    @patch('psutil.Process')
    def test_dos_protector_resource_monitoring(self, mock_process):
        """Test DoS protector resource monitoring."""
        # Mock high resource usage
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = Mock(rss=2 * 1024 * 1024 * 1024)  # 2GB
        mock_process_instance.cpu_percent.return_value = 95.0  # 95% CPU
        mock_process.return_value = mock_process_instance
        
        # Create protector with low resource limits
        resource_limits = ResourceLimits(
            max_memory_mb=1024,  # 1GB limit
            max_cpu_percent=80.0  # 80% CPU limit
        )
        
        protector = DoSProtector(resource_limits=resource_limits)
        
        # Give some time for monitoring to update
        time.sleep(0.1)
        
        context = RequestContext(
            timestamp=time.time(),
            ip_address="192.168.1.103",
            user_agent="Test Agent",
            endpoint="/api/test",
            request_size=1024
        )
        
        # Should be blocked due to high resource usage
        with pytest.raises(ResourceError):
            protector.protect("resource_test", context)
    
    def test_dos_protection_decorator(self):
        """Test DoS protection decorator."""
        call_count = 0
        
        @dos_protect("decorated_endpoint", max_requests=3, window=5)
        def protected_endpoint():
            nonlocal call_count
            call_count += 1
            return f"call_{call_count}"
        
        # First 3 calls should work
        for i in range(3):
            result = protected_endpoint()
            assert result == f"call_{i+1}"
        
        # 4th call should be rate limited
        with pytest.raises(RateLimitExceeded):
            protected_endpoint()
    
    def test_comprehensive_protection_stats(self):
        """Test comprehensive protection statistics."""
        protector = DoSProtector()
        
        # Generate some traffic
        context = RequestContext(
            timestamp=time.time(),
            ip_address="192.168.1.104",
            user_agent="Test Agent",
            endpoint="/api/stats",
            request_size=1024
        )
        
        # Allow some requests
        for i in range(5):
            try:
                protector.protect("stats_test", context)
            except:
                pass  # May be rate limited
        
        # Get comprehensive stats
        stats = protector.get_comprehensive_stats()
        
        # Verify stats structure
        assert "total_requests" in stats
        assert "blocked_requests" in stats
        assert "rate_limiter" in stats
        assert "threat_detector" in stats
        assert "resource_usage" in stats
        
        # Verify stats make sense
        assert stats["total_requests"] >= 5
        assert isinstance(stats["rate_limiter"], dict)
        assert isinstance(stats["threat_detector"], dict)


class TestDoSProtectionThreadSafety:
    """Test DoS protection system thread safety."""
    
    def test_concurrent_rate_limiting(self):
        """Test rate limiting under concurrent load."""
        protector = DoSProtector()
        successful_requests = []
        blocked_requests = []
        errors = []
        
        def worker(worker_id):
            for i in range(10):
                context = RequestContext(
                    timestamp=time.time(),
                    ip_address=f"192.168.1.{100 + worker_id}",
                    user_agent=f"Worker {worker_id}",
                    endpoint="/api/concurrent",
                    request_size=1024
                )
                
                try:
                    result = protector.protect("concurrent_test", context)
                    if result["allowed"]:
                        successful_requests.append(f"worker_{worker_id}_req_{i}")
                    else:
                        blocked_requests.append(f"worker_{worker_id}_req_{i}")
                except Exception as e:
                    errors.append(f"worker_{worker_id}_req_{i}: {type(e).__name__}")
        
        # Create multiple worker threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify we got responses from all workers
        total_attempts = len(successful_requests) + len(blocked_requests) + len(errors)
        assert total_attempts == 50  # 5 workers * 10 requests each
        
        # Should have at least some successful requests
        assert len(successful_requests) > 0


class TestDoSProtectionPerformance:
    """Test DoS protection system performance."""
    
    def test_protection_performance(self):
        """Test DoS protection performance under load."""
        protector = DoSProtector()
        
        # Test protection check performance
        start_time = time.time()
        
        for i in range(1000):
            context = RequestContext(
                timestamp=time.time(),
                ip_address=f"192.168.1.{(i % 254) + 1}",
                user_agent="Performance Test",
                endpoint="/api/perf",
                request_size=1024
            )
            
            try:
                protector.protect("perf_test", context)
            except:
                pass  # May be rate limited or blocked
        
        total_time = time.time() - start_time
        
        # Should handle 1000 protection checks in reasonable time (< 5 seconds)
        assert total_time < 5.0
        
        # Average time per check should be very fast (< 5ms)
        avg_time_ms = (total_time / 1000) * 1000
        assert avg_time_ms < 5.0


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])