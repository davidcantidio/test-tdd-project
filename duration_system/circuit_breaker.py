"""
⚡ Circuit Breaker Pattern for Resilience and DoS Protection

Advanced circuit breaker implementation for protecting against:
- Database overload and connection exhaustion
- External service failures
- Resource exhaustion attacks
- Cascading failures

This complements the rate limiter by providing fail-fast behavior
when downstream services are unavailable or overloaded.

Usage:
    from duration_system.circuit_breaker import CircuitBreaker, circuit_breaker
    
    # Protect database operations
    @circuit_breaker(name="database", failure_threshold=5, timeout=30)
    def database_query():
        # Database operation that might fail
        pass
    
    # Manual circuit breaker usage
    breaker = CircuitBreaker("api_service", failure_threshold=3)
    with breaker:
        # Protected operation
        result = external_api_call()
"""

import time
import threading
import logging
import statistics
from typing import Dict, Optional, Any, Callable, List, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum
from collections import deque

# Security and resilience logging
breaker_logger = logging.getLogger('security.circuit_breaker')
breaker_logger.setLevel(logging.INFO)

if not breaker_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - RESILIENCE - %(levelname)s - [CIRCUIT_BREAKER] %(message)s'
    )
    handler.setFormatter(formatter)
    breaker_logger.addHandler(handler)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Blocking requests due to failures
    HALF_OPEN = "HALF_OPEN"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 3          # Successes to close from half-open
    timeout_seconds: int = 60           # Time before trying half-open
    failure_rate_threshold: float = 0.5 # Failure rate to trigger opening
    min_requests: int = 10              # Minimum requests before rate calculation
    slow_call_threshold: float = 5.0    # Seconds to consider a call slow
    slow_call_rate_threshold: float = 0.5  # Slow call rate to trigger opening
    max_wait_time: float = 300.0        # Maximum wait time in open state
    exponential_backoff: bool = True    # Use exponential backoff
    
    def __post_init__(self):
        if self.failure_threshold <= 0:
            raise ValueError("failure_threshold must be positive")
        if self.success_threshold <= 0:
            raise ValueError("success_threshold must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass
class CallRecord:
    """Record of a single function call."""
    
    timestamp: float
    duration: float
    success: bool
    error_type: Optional[str] = None


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


class CircuitBreaker:
    """
    Advanced circuit breaker with multiple failure detection strategies.
    
    Features:
    - Failure count and failure rate thresholds
    - Slow call detection and rate thresholds
    - Exponential backoff in open state
    - Detailed metrics and monitoring
    - Thread-safe operation
    - Memory-efficient call history tracking
    """
    
    def __init__(self, 
                 name: str,
                 config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.
        
        Args:
            name: Unique name for this circuit breaker
            config: Configuration settings
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # State management
        self._state = CircuitState.CLOSED
        self._state_lock = threading.RLock()
        
        # Failure tracking
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._next_attempt_time = 0.0
        
        # Call history for rate calculations (limited size for memory efficiency)
        self._call_history: deque[CallRecord] = deque(maxlen=1000)
        self._history_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "slow_calls": 0,
            "blocked_calls": 0,
            "state_changes": 0,
            "current_state": self._state.value,
            "failure_rate": 0.0,
            "slow_call_rate": 0.0,
            "average_response_time": 0.0,
            "last_failure_time": None,
            "time_in_current_state": 0.0
        }
        
        # State transition callbacks
        self._state_change_callbacks: List[Callable] = []
        
        breaker_logger.info(f"Circuit breaker '{name}' initialized")
    
    def add_state_change_callback(self, callback: Callable[[str, CircuitState, CircuitState], None]):
        """Add callback for state changes."""
        self._state_change_callbacks.append(callback)
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker protection.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original function exceptions when circuit is closed/half-open
        """
        if not self._can_execute():
            self.stats["blocked_calls"] += 1
            retry_after = max(0, self._next_attempt_time - time.time())
            
            breaker_logger.warning(
                f"Circuit breaker '{self.name}' is OPEN - blocking call"
            )
            
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is open. Service unavailable.",
                retry_after=retry_after
            )
        
        return self._execute_call(func, *args, **kwargs)
    
    def _can_execute(self) -> bool:
        """Check if calls can be executed based on current state."""
        with self._state_lock:
            current_time = time.time()
            
            if self._state == CircuitState.CLOSED:
                return True
            elif self._state == CircuitState.OPEN:
                if current_time >= self._next_attempt_time:
                    self._transition_to_half_open()
                    return True
                return False
            elif self._state == CircuitState.HALF_OPEN:
                return True
            
        return False
    
    def _execute_call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute the actual function call and track results."""
        start_time = time.time()
        self.stats["total_calls"] += 1
        
        try:
            result = func(*args, **kwargs)
            
            # Record successful call
            duration = time.time() - start_time
            self._record_call(start_time, duration, True)
            self._on_success()
            
            return result
            
        except Exception as e:
            # Record failed call
            duration = time.time() - start_time
            self._record_call(start_time, duration, False, type(e).__name__)
            self._on_failure()
            
            raise
    
    def _record_call(self, 
                    timestamp: float, 
                    duration: float, 
                    success: bool,
                    error_type: Optional[str] = None):
        """Record call details for metrics calculation."""
        record = CallRecord(timestamp, duration, success, error_type)
        
        with self._history_lock:
            self._call_history.append(record)
        
        # Update basic stats
        if success:
            self.stats["successful_calls"] += 1
        else:
            self.stats["failed_calls"] += 1
        
        if duration > self.config.slow_call_threshold:
            self.stats["slow_calls"] += 1
    
    def _on_success(self):
        """Handle successful call."""
        with self._state_lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                
                if self._success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            else:
                # Reset failure count on success in closed state
                self._failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        with self._state_lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                # Single failure in half-open returns to open
                self._transition_to_open()
            elif self._state == CircuitState.CLOSED:
                # Check if we should open the circuit
                if self._should_open_circuit():
                    self._transition_to_open()
    
    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened based on failure patterns."""
        # Simple failure count threshold
        if self._failure_count >= self.config.failure_threshold:
            return True
        
        # Calculate failure rate over recent calls
        with self._history_lock:
            if len(self._call_history) < self.config.min_requests:
                return False
            
            recent_calls = list(self._call_history)[-self.config.min_requests:]
            failure_rate = sum(1 for call in recent_calls if not call.success) / len(recent_calls)
            
            self.stats["failure_rate"] = failure_rate
            
            if failure_rate >= self.config.failure_rate_threshold:
                breaker_logger.warning(
                    f"Circuit breaker '{self.name}' - high failure rate: {failure_rate:.2%}"
                )
                return True
            
            # Calculate slow call rate
            slow_calls = sum(1 for call in recent_calls 
                           if call.duration > self.config.slow_call_threshold)
            slow_call_rate = slow_calls / len(recent_calls)
            
            self.stats["slow_call_rate"] = slow_call_rate
            
            if slow_call_rate >= self.config.slow_call_rate_threshold:
                breaker_logger.warning(
                    f"Circuit breaker '{self.name}' - high slow call rate: {slow_call_rate:.2%}"
                )
                return True
        
        return False
    
    def _transition_to_closed(self):
        """Transition circuit breaker to CLOSED state."""
        old_state = self._state
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        
        self._notify_state_change(old_state, CircuitState.CLOSED)
        
        breaker_logger.info(f"Circuit breaker '{self.name}' transitioned to CLOSED")
    
    def _transition_to_open(self):
        """Transition circuit breaker to OPEN state."""
        old_state = self._state
        self._state = CircuitState.OPEN
        self._success_count = 0
        
        # Calculate next attempt time with exponential backoff
        if self.config.exponential_backoff:
            backoff_multiplier = min(2 ** (self._failure_count - 1), 32)  # Cap at 32x
            timeout = min(
                self.config.timeout_seconds * backoff_multiplier,
                self.config.max_wait_time
            )
        else:
            timeout = self.config.timeout_seconds
        
        self._next_attempt_time = time.time() + timeout
        
        self._notify_state_change(old_state, CircuitState.OPEN)
        
        breaker_logger.error(
            f"Circuit breaker '{self.name}' transitioned to OPEN - "
            f"next attempt in {timeout:.1f}s"
        )
    
    def _transition_to_half_open(self):
        """Transition circuit breaker to HALF_OPEN state."""
        old_state = self._state
        self._state = CircuitState.HALF_OPEN
        self._success_count = 0
        
        self._notify_state_change(old_state, CircuitState.HALF_OPEN)
        
        breaker_logger.info(f"Circuit breaker '{self.name}' transitioned to HALF_OPEN")
    
    def _notify_state_change(self, old_state: CircuitState, new_state: CircuitState):
        """Notify callbacks of state changes."""
        self.stats["state_changes"] += 1
        self.stats["current_state"] = new_state.value
        
        for callback in self._state_change_callbacks:
            try:
                callback(self.name, old_state, new_state)
            except Exception as e:
                breaker_logger.error(f"State change callback error: {e}")
    
    def force_open(self):
        """Manually force circuit breaker to open state."""
        with self._state_lock:
            self._transition_to_open()
        
        breaker_logger.warning(f"Circuit breaker '{self.name}' manually forced to OPEN")
    
    def force_closed(self):
        """Manually force circuit breaker to closed state."""
        with self._state_lock:
            self._transition_to_closed()
        
        breaker_logger.info(f"Circuit breaker '{self.name}' manually forced to CLOSED")
    
    def reset(self):
        """Reset circuit breaker to initial state."""
        with self._state_lock:
            with self._history_lock:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                self._last_failure_time = 0.0
                self._next_attempt_time = 0.0
                self._call_history.clear()
                
                # Reset stats
                for key in self.stats:
                    if isinstance(self.stats[key], (int, float)):
                        self.stats[key] = 0
                    elif key == "current_state":
                        self.stats[key] = CircuitState.CLOSED.value
                    elif key == "last_failure_time":
                        self.stats[key] = None
        
        breaker_logger.info(f"Circuit breaker '{self.name}' reset to initial state")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive circuit breaker statistics."""
        with self._history_lock:
            # Calculate dynamic metrics
            if self._call_history:
                recent_calls = list(self._call_history)[-100:]  # Last 100 calls
                
                if recent_calls:
                    durations = [call.duration for call in recent_calls]
                    self.stats["average_response_time"] = statistics.mean(durations)
                    
                    failures = [call for call in recent_calls if not call.success]
                    self.stats["failure_rate"] = len(failures) / len(recent_calls)
                    
                    slow_calls = [call for call in recent_calls 
                                if call.duration > self.config.slow_call_threshold]
                    self.stats["slow_call_rate"] = len(slow_calls) / len(recent_calls)
        
        stats = self.stats.copy()
        stats.update({
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "next_attempt_time": self._next_attempt_time if self._state == CircuitState.OPEN else None,
            "last_failure_time": datetime.fromtimestamp(self._last_failure_time).isoformat() if self._last_failure_time else None,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
                "failure_rate_threshold": self.config.failure_rate_threshold,
                "slow_call_threshold": self.config.slow_call_threshold
            }
        })
        
        return stats
    
    def __enter__(self):
        """Context manager entry - just return self."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - record call result."""
        if exc_type is None:
            # Success
            self._record_call(time.time(), 0.0, True)
            self._on_success()
        else:
            # Failure
            self._record_call(time.time(), 0.0, False, exc_type.__name__)
            self._on_failure()
        
        return False  # Don't suppress exceptions


# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_registry_lock = threading.Lock()


def get_circuit_breaker(name: str, 
                       config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    with _registry_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(name, config)
        return _circuit_breakers[name]


def circuit_breaker(name: str,
                   failure_threshold: int = 5,
                   success_threshold: int = 3,
                   timeout: int = 60,
                   failure_rate_threshold: float = 0.5,
                   slow_call_threshold: float = 5.0):
    """
    Decorator for protecting functions with circuit breaker pattern.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures before opening
        success_threshold: Number of successes to close from half-open
        timeout: Timeout before attempting half-open (seconds)
        failure_rate_threshold: Failure rate to trigger opening
        slow_call_threshold: Response time threshold for slow calls
    """
    def decorator(func: Callable) -> Callable:
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout_seconds=timeout,
            failure_rate_threshold=failure_rate_threshold,
            slow_call_threshold=slow_call_threshold
        )
        
        breaker = get_circuit_breaker(name, config)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        # Add management methods
        wrapper.get_stats = lambda: breaker.get_stats()
        wrapper.reset = lambda: breaker.reset()
        wrapper.force_open = lambda: breaker.force_open()
        wrapper.force_closed = lambda: breaker.force_closed()
        
        return wrapper
    
    return decorator


def get_all_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all circuit breakers."""
    with _registry_lock:
        return {name: breaker.get_stats() for name, breaker in _circuit_breakers.items()}


if __name__ == "__main__":
    # Example usage and testing
    def test_circuit_breaker():
        """Test circuit breaker functionality."""
        print("Testing Circuit Breaker...")
        
        # Create a test function that fails sometimes
        failure_count = 0
        
        @circuit_breaker("test_service", failure_threshold=3, timeout=2)
        def unreliable_service():
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 5:  # Fail first 5 calls
                raise Exception(f"Service failure #{failure_count}")
            return "success"
        
        # Test failure detection and circuit opening
        for i in range(8):
            try:
                result = unreliable_service()
                print(f"Call {i+1}: {result}")
            except CircuitBreakerError as e:
                print(f"Call {i+1}: Circuit breaker blocked - {e}")
            except Exception as e:
                print(f"Call {i+1}: Service error - {e}")
        
        # Wait for circuit to attempt half-open
        print("\nWaiting for circuit breaker timeout...")
        time.sleep(2.1)
        
        # Try again - should work now
        try:
            result = unreliable_service()
            print(f"After timeout: {result}")
        except Exception as e:
            print(f"After timeout: {e}")
        
        # Show statistics
        stats = unreliable_service.get_stats()
        print(f"\nCircuit Breaker Stats:")
        for key, value in stats.items():
            if key != "config":
                print(f"  {key}: {value}")
    
    test_circuit_breaker()