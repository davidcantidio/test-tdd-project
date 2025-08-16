"""Circuit breaker utility for database resilience."""
import time
import logging
from typing import Callable, Type, Any


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is open."""


class CircuitBreaker:
    """Simple circuit breaker implementation.

    Args:
        failure_threshold: Number of consecutive failures to open the circuit.
        recovery_timeout: Seconds to keep the circuit open before allowing
            another attempt.
        expected_exception: Exception type that counts as a failure.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.fail_counter = 0
        self.opened_at: float | None = None
        self.logger = logging.getLogger(__name__)

    def is_open(self) -> bool:
        """Check if the circuit is currently open."""
        if self.opened_at is None:
            return False
        if (time.time() - self.opened_at) >= self.recovery_timeout:
            # Allow retries after timeout (half-open)
            return False
        return True

    def _record_failure(self) -> None:
        self.fail_counter += 1
        if self.fail_counter >= self.failure_threshold:
            self.opened_at = time.time()
            self.logger.warning("Circuit opened after %s failures", self.fail_counter)

    def _reset(self) -> None:
        self.fail_counter = 0
        self.opened_at = None

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute ``func`` while applying circuit breaker logic."""
        if self.is_open():
            raise CircuitBreakerOpenError("Circuit is open")
        try:
            result = func(*args, **kwargs)
        except self.expected_exception:
            self._record_failure()
            raise
        else:
            self._reset()
            return result
