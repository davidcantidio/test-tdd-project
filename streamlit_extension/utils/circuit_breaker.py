#!/usr/bin/env python3
"""
Enhanced Circuit Breaker System
Implements connection retry logic and circuit breakers for database and external services.
"""

import time
import logging
import threading
from typing import Callable, Any, Optional, Dict
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
import sqlite3
import random
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


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
    base_delay: float = 1.0             # Base delay for exponential backoff
    max_delay: float = 60.0             # Maximum delay between retries
    jitter: bool = True                 # Add random jitter to delays


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


class CircuitBreakerOpenError(CircuitOpenError):
    """Backward compatibility alias for CircuitOpenError."""
    pass


class MaxRetriesExceededError(CircuitBreakerError):
    """Raised when maximum retry attempts exceeded."""
    pass


class CircuitBreaker:
    """Enhanced circuit breaker with retry logic and exponential backoff."""

    def __init__(self, name: str = "default", config: Optional[CircuitConfig] = None, **legacy_kwargs):
        """Initialize circuit breaker.

        Accepts a ``name`` and optional ``config``. Legacy arguments such as
        ``failure_threshold`` or ``recovery_timeout`` are also supported for
        backward compatibility.
        """
        if config is None:
            if legacy_kwargs:
                config = CircuitConfig(
                    failure_threshold=legacy_kwargs.get("failure_threshold", 5),
                    success_threshold=legacy_kwargs.get("success_threshold", 3),
                    timeout=legacy_kwargs.get("timeout") or legacy_kwargs.get("recovery_timeout", 60),
                    max_retry_attempts=legacy_kwargs.get("max_retry_attempts", 1),
                    base_delay=legacy_kwargs.get("base_delay", 1.0),
                    max_delay=legacy_kwargs.get("max_delay", 60.0),
                    jitter=legacy_kwargs.get("jitter", True),
                )
            else:
                config = CircuitConfig()
        self.name = name
        self.config = config
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

        if not self._can_proceed():
            raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")

        return self._execute_with_retry(func, *args, **kwargs)

    def _can_proceed(self) -> bool:
        """Check if circuit breaker allows request to proceed."""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if self._last_failure_time:
                    time_since_failure = time.time() - self._last_failure_time
                    if time_since_failure >= self.config.timeout:
                        logger.info("Circuit %s transitioning to HALF_OPEN", self.name)
                        self.state = CircuitState.HALF_OPEN
                        return True
                return False
            if self.state == CircuitState.HALF_OPEN:
                return True
        return False

    def _execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry logic."""
        last_exception: Optional[Exception] = None
        for attempt in range(self.config.max_retry_attempts):
            try:
                result = func(*args, **kwargs)
                self._record_success()
                return result
            except Exception as exc:  # pragma: no cover - generic catch
                last_exception = exc
                self._record_failure()
                if attempt == self.config.max_retry_attempts - 1:
                    break
                delay = self._calculate_delay(attempt)
                logger.warning(
                    "Circuit %s attempt %s failed: %s. Retrying in %.2fs",
                    self.name,
                    attempt + 1,
                    exc,
                    delay,
                )
                time.sleep(delay)
        if self.config.max_retry_attempts == 1 and last_exception:
            raise last_exception
        raise MaxRetriesExceededError(
            f"Max retries exceeded for circuit {self.name}"
        ) from last_exception

    # --- Novas utilidades para observabilidade/integração ---
    def get_state(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "stats": {
                    "total_requests": self.stats.total_requests,
                    "successful_requests": self.stats.successful_requests,
                    "failed_requests": self.stats.failed_requests,
                    "circuit_opened_count": self.stats.circuit_opened_count,
                    "success_rate": self.stats.success_rate,
                    "failure_rate": self.stats.failure_rate,
                }
            }

    def reset(self) -> None:
        with self._lock:
            self.state = CircuitState.CLOSED
            self.stats = CircuitStats()
            self._last_failure_time = None

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = self.config.base_delay * (2 ** attempt)
        delay = min(delay, self.config.max_delay)
        if self.config.jitter:
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        return max(0.1, delay)

    def _record_success(self) -> None:
        """Record successful operation."""
        with self._lock:
            self.stats.successful_requests += 1
            self.stats.last_success_time = datetime.now()
            self.stats.current_consecutive_failures = 0
            self.stats.current_consecutive_successes += 1
            if self.state == CircuitState.HALF_OPEN and self.stats.current_consecutive_successes >= self.config.success_threshold:
                logger.info("Circuit %s transitioning to CLOSED", self.name)
                self.state = CircuitState.CLOSED

    def _record_failure(self) -> None:
        """Record failed operation."""
        with self._lock:
            self.stats.failed_requests += 1
            self.stats.last_failure_time = datetime.now()
            self.stats.current_consecutive_successes = 0
            self.stats.current_consecutive_failures += 1
            self._last_failure_time = time.time()
            if self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN) and \
                self.stats.current_consecutive_failures >= self.config.failure_threshold:
                logger.warning("Circuit %s transitioning to OPEN", self.name)
                self.state = CircuitState.OPEN
                self.stats.circuit_opened_count += 1

    def force_open(self) -> None:
        """Force circuit to OPEN state."""
        with self._lock:
            self.state = CircuitState.OPEN
            self._last_failure_time = time.time()
            self.stats.circuit_opened_count += 1
            logger.warning("Circuit %s forced OPEN", self.name)

    def force_close(self) -> None:
        """Force circuit to CLOSED state."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.stats.current_consecutive_failures = 0
            logger.info("Circuit %s forced CLOSED", self.name)

    def get_stats(self) -> Dict[str, Any]:
        """Get current circuit breaker statistics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "total_requests": self.stats.total_requests,
                "successful_requests": self.stats.successful_requests,
                "failed_requests": self.stats.failed_requests,
                "success_rate": self.stats.success_rate,
                "failure_rate": self.stats.failure_rate,
                "circuit_opened_count": self.stats.circuit_opened_count,
                "consecutive_failures": self.stats.current_consecutive_failures,
                "consecutive_successes": self.stats.current_consecutive_successes,
                "last_failure": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
                "last_success": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
            }


class DatabaseCircuitBreaker(CircuitBreaker):
    """Specialized circuit breaker for database operations."""

    def __init__(self, name: str = "database"):
        config = CircuitConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=30,
            max_retry_attempts=3,
            base_delay=0.5,
            max_delay=10.0,
            jitter=True,
        )
        super().__init__(name, config)

    def call(self, func: Callable, *args, **kwargs) -> Any:
        try:
            return super().call(func, *args, **kwargs)
        except sqlite3.OperationalError as exc:
            msg = str(exc).lower()
            if "database is locked" in msg:
                logger.warning("Database locked, circuit %s will retry", self.name)
                raise
            if "database is busy" in msg:
                logger.warning("Database busy, circuit %s will retry", self.name)
                raise
            self._record_failure()
            raise
        except sqlite3.IntegrityError:
            logger.error("Database integrity error in circuit %s", self.name)
            raise
        except Exception:
            raise


class ExternalServiceCircuitBreaker(CircuitBreaker):
    """Specialized circuit breaker for external service calls."""

    def __init__(self, name: str, service_url: str):
        config = CircuitConfig(
            failure_threshold=5,
            success_threshold=3,
            timeout=60,
            max_retry_attempts=3,
            base_delay=2.0,
            max_delay=60.0,
            jitter=True,
        )
        super().__init__(name, config)
        self.service_url = service_url


_circuit_breakers: Dict[str, CircuitBreaker] = {}
_registry_lock = threading.RLock()


def get_circuit_breaker(name: str, breaker_type: str = "generic", **kwargs) -> CircuitBreaker:
    """Get or create circuit breaker instance."""
    with _registry_lock:
        if name not in _circuit_breakers:
            if breaker_type == "database":
                _circuit_breakers[name] = DatabaseCircuitBreaker(name)
            elif breaker_type == "external":
                service_url = kwargs.get("service_url", "")
                _circuit_breakers[name] = ExternalServiceCircuitBreaker(name, service_url)
            else:
                config = kwargs.get("config")
                if config is None:
                    config = CircuitConfig()
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


def reset_all_circuit_breakers() -> None:
    """Reset all registered circuit breakers."""
    with _registry_lock:
        for breaker in _circuit_breakers.values():
            breaker.reset()
        logger.info("All circuit breakers reset")


def circuit_breaker_health_check() -> Dict[str, Any]:
    """Health check for circuit breaker system."""
    stats = get_all_circuit_stats()
    healthy_circuits = sum(1 for s in stats.values() if s["state"] == "closed")
    total_circuits = len(stats)
    overall_health = "healthy" if healthy_circuits == total_circuits else "degraded"
    if healthy_circuits == 0 and total_circuits > 0:
        overall_health = "unhealthy"
    return {
        "status": overall_health,
        "healthy_circuits": healthy_circuits,
        "total_circuits": total_circuits,
        "circuit_details": stats,
        "timestamp": datetime.now().isoformat(),
    }


__all__ = [
    "CircuitBreaker",
    "DatabaseCircuitBreaker",
    "ExternalServiceCircuitBreaker",
    "CircuitConfig",
    "CircuitState",
    "CircuitBreakerError",
    "CircuitOpenError",
    "CircuitBreakerOpenError",
    "MaxRetriesExceededError",
    "get_circuit_breaker",
    "circuit_breaker",
    "database_circuit_breaker",
    "external_service_circuit_breaker",
    "get_all_circuit_stats",
    "reset_all_circuit_breakers",
    "circuit_breaker_health_check",
]