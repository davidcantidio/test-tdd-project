"""Database resilience helpers with retry and circuit breaker."""
from __future__ import annotations

import time
import logging
from contextlib import contextmanager
from typing import Generator, Optional

from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

logger = logging.getLogger(__name__)


@contextmanager
def resilient_connection(
    db_manager,
    db_name: str = "framework",
    retries: int = 3,
    delay: float = 0.1,
    breaker: Optional[CircuitBreaker] = None,
) -> Generator:
    """Context manager that provides a resilient database connection.

    Retries transient failures and opens a circuit after repeated errors to
    prevent resource exhaustion.

    Args:
        db_manager: ``DatabaseManager`` instance.
        db_name: Target database name.
        retries: Number of retry attempts per call.
        delay: Delay between retries in seconds.
        breaker: Optional :class:`CircuitBreaker` instance.
    """

    breaker = breaker or CircuitBreaker(failure_threshold=retries)
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            conn_cm = breaker.call(db_manager.get_connection, db_name)
            with conn_cm as conn:
                yield conn
                return
        except CircuitBreakerOpenError:
            logger.error("Circuit breaker open; aborting connection attempts")
            raise
        except Exception as exc:  # pragma: no cover - generic
            last_exc = exc
            logger.warning("Connection attempt %s failed: %s", attempt, exc)
            if attempt == retries:
                raise
            time.sleep(delay)
    if last_exc:
        raise last_exc
