# 🤖 PROMPT EE: ENHANCED CIRCUIT BREAKERS

## 🎯 OBJECTIVE
Implement comprehensive circuit breakers and connection retry logic to address report.md requirement: "Add connection retry logic and circuit breakers for DB" in the Production Deployment Checklist.

## 📁 FILE TO CREATE

### streamlit_extension/utils/circuit_breaker.py (NEW FILE)

```python
#!/usr/bin/env python3
"""
Enhanced Circuit Breaker System
Implements connection retry logic and circuit breakers for database and external services.
"""

import time
import logging
import threading
from typing import Callable, Any, Optional, Dict, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
import sqlite3
import random

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 3          # Successes to close from half-open
    timeout: int = 60                   # Seconds before retry from open
    max_retry_attempts: int = 3         # Max retries per request
    base_delay: float = 1.0            # Base delay for exponential backoff
    max_delay: float = 60.0            # Maximum delay between retries
    jitter: bool = True                # Add random jitter to delays


@dataclass
class CircuitStats:
    """Circuit breaker statistics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_opened_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    current_consecutive_failures: int = 0
    current_consecutive_successes: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100
        
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100


class CircuitBreakerError(Exception):
    """Circuit breaker specific exceptions."""
    pass


class CircuitOpenError(CircuitBreakerError):
    """Raised when circuit is open and blocking requests."""
    pass


class MaxRetriesExceededError(CircuitBreakerError):
    """Raised when maximum retry attempts exceeded."""
    pass


class CircuitBreaker:
    """Enhanced circuit breaker with retry logic and exponential backoff."""
    
    def __init__(self, name: str, config: CircuitConfig = None):
        """Initialize circuit breaker."""
        self.name = name
        self.config = config or CircuitConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self._lock = threading.RLock()
        self._last_failure_time: Optional[float] = None
        
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with circuit breaker."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        with self._lock:
            self.stats.total_requests += 1
            
        # Check if circuit allows request
        if not self._can_proceed():
            raise CircuitOpenError(f"Circuit breaker {self.name} is OPEN")
            
        # Execute with retry logic
        return self._execute_with_retry(func, *args, **kwargs)
        
    def _can_proceed(self) -> bool:
        """Check if circuit breaker allows request to proceed."""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
                
            elif self.state == CircuitState.OPEN:
                # Check if timeout expired
                if self._last_failure_time:
                    time_since_failure = time.time() - self._last_failure_time
                    if time_since_failure >= self.config.timeout:
                        logger.info(f"Circuit {self.name} transitioning to HALF_OPEN")
                        self.state = CircuitState.HALF_OPEN
                        return True
                return False
                
            elif self.state == CircuitState.HALF_OPEN:
                return True
                
        return False
        
    def _execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_retry_attempts):
            try:
                result = func(*args, **kwargs)
                self._record_success()
                return result
                
            except Exception as e:
                last_exception = e
                self._record_failure()
                
                # Don't retry on final attempt
                if attempt == self.config.max_retry_attempts - 1:
                    break
                    
                # Calculate delay with exponential backoff
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"Circuit {self.name} attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s"
                )
                time.sleep(delay)
                
        # All retries exhausted
        self._record_failure()
        raise MaxRetriesExceededError(
            f"Circuit {self.name} failed after {self.config.max_retry_attempts} attempts"
        ) from last_exception
        
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = self.config.base_delay * (2 ** attempt)
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            # Add random jitter (±25%)
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
            
        return max(0.1, delay)  # Minimum 100ms
        
    def _record_success(self):
        """Record successful operation."""
        with self._lock:
            self.stats.successful_requests += 1
            self.stats.last_success_time = datetime.now()
            self.stats.current_consecutive_failures = 0
            self.stats.current_consecutive_successes += 1
            
            # Transition from HALF_OPEN to CLOSED
            if (self.state == CircuitState.HALF_OPEN and 
                self.stats.current_consecutive_successes >= self.config.success_threshold):
                logger.info(f"Circuit {self.name} transitioning to CLOSED")
                self.state = CircuitState.CLOSED
                
    def _record_failure(self):
        """Record failed operation."""
        with self._lock:
            self.stats.failed_requests += 1
            self.stats.last_failure_time = datetime.now()
            self.stats.current_consecutive_successes = 0
            self.stats.current_consecutive_failures += 1
            self._last_failure_time = time.time()
            
            # Transition to OPEN if threshold exceeded
            if (self.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN] and 
                self.stats.current_consecutive_failures >= self.config.failure_threshold):
                logger.warning(f"Circuit {self.name} transitioning to OPEN")
                self.state = CircuitState.OPEN
                self.stats.circuit_opened_count += 1
                
    def reset(self):
        """Reset circuit breaker to initial state."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.stats = CircuitStats()
            self._last_failure_time = None
            logger.info(f"Circuit {self.name} reset")
            
    def force_open(self):
        """Force circuit to OPEN state."""
        with self._lock:
            self.state = CircuitState.OPEN
            self._last_failure_time = time.time()
            self.stats.circuit_opened_count += 1
            logger.warning(f"Circuit {self.name} forced OPEN")
            
    def force_close(self):
        """Force circuit to CLOSED state."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.stats.current_consecutive_failures = 0
            logger.info(f"Circuit {self.name} forced CLOSED")
            
    def get_stats(self) -> Dict[str, Any]:
        """Get current circuit breaker statistics."""
        with self._lock:
            return {
                'name': self.name,
                'state': self.state.value,
                'total_requests': self.stats.total_requests,
                'successful_requests': self.stats.successful_requests,
                'failed_requests': self.stats.failed_requests,
                'success_rate': self.stats.success_rate,
                'failure_rate': self.stats.failure_rate,
                'circuit_opened_count': self.stats.circuit_opened_count,
                'consecutive_failures': self.stats.current_consecutive_failures,
                'consecutive_successes': self.stats.current_consecutive_successes,
                'last_failure': self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
                'last_success': self.stats.last_success_time.isoformat() if self.stats.last_success_time else None
            }


class DatabaseCircuitBreaker(CircuitBreaker):
    """Specialized circuit breaker for database operations."""
    
    def __init__(self, name: str = "database"):
        # Database-specific configuration
        config = CircuitConfig(
            failure_threshold=3,        # Lower threshold for DB
            success_threshold=2,        # Faster recovery
            timeout=30,                 # Shorter timeout for DB
            max_retry_attempts=3,
            base_delay=0.5,            # Faster initial retry
            max_delay=10.0,            # Lower max delay for DB
            jitter=True
        )
        super().__init__(name, config)
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute database function with special error handling."""
        try:
            return super().call(func, *args, **kwargs)
        except sqlite3.OperationalError as e:
            # Database locked or busy - these are retryable
            if "database is locked" in str(e).lower():
                logger.warning(f"Database locked, circuit {self.name} will retry")
                raise  # Let retry logic handle it
            elif "database is busy" in str(e).lower():
                logger.warning(f"Database busy, circuit {self.name} will retry")
                raise  # Let retry logic handle it
            else:
                # Other operational errors might not be retryable
                self._record_failure()
                raise
        except sqlite3.IntegrityError:
            # Integrity errors shouldn't trigger circuit breaker
            logger.error(f"Database integrity error in circuit {self.name}")
            raise
        except Exception:
            # All other exceptions trigger circuit breaker
            raise


class ExternalServiceCircuitBreaker(CircuitBreaker):
    """Specialized circuit breaker for external service calls."""
    
    def __init__(self, name: str, service_url: str):
        # External service configuration
        config = CircuitConfig(
            failure_threshold=5,        # Higher threshold for external services
            success_threshold=3,
            timeout=60,                 # Longer timeout for external services
            max_retry_attempts=3,
            base_delay=2.0,            # Longer delays for external services
            max_delay=60.0,
            jitter=True
        )
        super().__init__(name, config)
        self.service_url = service_url


# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_registry_lock = threading.RLock()


def get_circuit_breaker(name: str, breaker_type: str = "generic", **kwargs) -> CircuitBreaker:
    """Get or create circuit breaker instance."""
    with _registry_lock:
        if name not in _circuit_breakers:
            if breaker_type == "database":
                _circuit_breakers[name] = DatabaseCircuitBreaker(name)
            elif breaker_type == "external":
                service_url = kwargs.get('service_url', '')
                _circuit_breakers[name] = ExternalServiceCircuitBreaker(name, service_url)
            else:
                config = kwargs.get('config', CircuitConfig())
                _circuit_breakers[name] = CircuitBreaker(name, config)
                
        return _circuit_breakers[name]


def circuit_breaker(name: str, breaker_type: str = "generic", **kwargs):
    """Decorator to add circuit breaker to function."""
    def decorator(func: Callable) -> Callable:
        breaker = get_circuit_breaker(name, breaker_type, **kwargs)
        return breaker(func)
    return decorator


def database_circuit_breaker(name: str = "database"):
    """Decorator for database operations."""
    return circuit_breaker(name, "database")


def external_service_circuit_breaker(name: str, service_url: str = ""):
    """Decorator for external service calls."""
    return circuit_breaker(name, "external", service_url=service_url)


def get_all_circuit_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all registered circuit breakers."""
    with _registry_lock:
        return {name: breaker.get_stats() for name, breaker in _circuit_breakers.items()}


def reset_all_circuit_breakers():
    """Reset all registered circuit breakers."""
    with _registry_lock:
        for breaker in _circuit_breakers.values():
            breaker.reset()
        logger.info("All circuit breakers reset")


# Health check for circuit breakers
def circuit_breaker_health_check() -> Dict[str, Any]:
    """Health check for circuit breaker system."""
    stats = get_all_circuit_stats()
    
    healthy_circuits = sum(1 for s in stats.values() if s['state'] == 'closed')
    total_circuits = len(stats)
    
    overall_health = "healthy" if healthy_circuits == total_circuits else "degraded"
    if healthy_circuits == 0 and total_circuits > 0:
        overall_health = "unhealthy"
        
    return {
        'status': overall_health,
        'healthy_circuits': healthy_circuits,
        'total_circuits': total_circuits,
        'circuit_details': stats,
        'timestamp': datetime.now().isoformat()
    }


# Export main components
__all__ = [
    'CircuitBreaker',
    'DatabaseCircuitBreaker', 
    'ExternalServiceCircuitBreaker',
    'CircuitConfig',
    'CircuitState',
    'CircuitBreakerError',
    'CircuitOpenError',
    'MaxRetriesExceededError',
    'get_circuit_breaker',
    'circuit_breaker',
    'database_circuit_breaker',
    'external_service_circuit_breaker',
    'get_all_circuit_stats',
    'reset_all_circuit_breakers',
    'circuit_breaker_health_check'
]
```

## 📋 INTEGRATION EXAMPLES

### 1. Database Operations
```python
# In database.py
from streamlit_extension.utils.circuit_breaker import database_circuit_breaker

class DatabaseManager:
    
    @database_circuit_breaker("epic_queries")
    def get_epics(self, client_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get epics with circuit breaker protection."""
        # Existing implementation
        
    @database_circuit_breaker("task_queries") 
    def get_tasks(self, epic_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get tasks with circuit breaker protection."""
        # Existing implementation
```

### 2. External Service Calls
```python
# For GitHub API or other external services
from streamlit_extension.utils.circuit_breaker import external_service_circuit_breaker

@external_service_circuit_breaker("github_api", "https://api.github.com")
def sync_with_github(repo_data: Dict[str, Any]) -> bool:
    """Sync with GitHub API with circuit breaker protection."""
    # GitHub API implementation
```

### 3. Health Endpoint Integration
```python
# In health.py
from streamlit_extension.utils.circuit_breaker import circuit_breaker_health_check

def get_health_json() -> Dict[str, object]:
    """Enhanced health check including circuit breakers."""
    health = {
        # Existing health checks
        'circuit_breakers': circuit_breaker_health_check()
    }
    return health
```

## ✅ REQUIREMENTS

1. **Create comprehensive circuit breaker system** in new file
2. **Implement exponential backoff retry logic** with jitter
3. **Add specialized breakers** for database and external services
4. **Include state management** (CLOSED/OPEN/HALF_OPEN)
5. **Add comprehensive statistics** and monitoring
6. **Provide decorators** for easy integration
7. **Include health check integration**
8. **Add thread-safe operations** for concurrent usage

## 🚫 WHAT NOT TO CHANGE
- Existing method signatures
- Current functionality or logic
- Import statements in existing files
- Database schema or connections
- Performance characteristics

## ✅ VERIFICATION CHECKLIST
- [ ] Circuit breaker system created with all states
- [ ] Exponential backoff retry logic implemented
- [ ] Database-specific circuit breaker included
- [ ] External service circuit breaker included
- [ ] Thread-safe operations ensured
- [ ] Statistics and monitoring included
- [ ] Health check integration provided
- [ ] Decorators for easy integration
- [ ] Comprehensive error handling
- [ ] Documentation and examples included

## 🎯 CONTEXT
This addresses report.md requirement: "Add connection retry logic and circuit breakers for DB" in the Production Deployment Checklist and "Connection pool test hang indicates potential deadlock or unreleased connections" in Performance Bottleneck Analysis.

The circuit breaker system will prevent cascade failures and improve system resilience.