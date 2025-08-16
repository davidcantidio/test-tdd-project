import pathlib
import sys
import sqlite3
from contextlib import contextmanager

import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from streamlit_extension.utils.db_resilience import resilient_connection
from streamlit_extension.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


class FlakyDBManager:
    """DB manager that fails twice before succeeding."""

    def __init__(self):
        self.attempts = 0

    @contextmanager
    def get_connection(self, db_name: str = "framework"):
        self.attempts += 1
        if self.attempts <= 2:
            raise sqlite3.OperationalError("temporary failure")
        conn = sqlite3.connect(":memory:")
        try:
            yield conn
        finally:
            conn.close()


class FailingDBManager:
    @contextmanager
    def get_connection(self, db_name: str = "framework"):
        raise sqlite3.OperationalError("fail")


def test_resilient_connection_recovers_from_transient_errors():
    manager = FlakyDBManager()
    with resilient_connection(manager) as conn:
        assert conn.execute("SELECT 1").fetchone()[0] == 1


def test_circuit_breaker_opens_after_failures():
    manager = FailingDBManager()
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
    for _ in range(2):
        with pytest.raises(sqlite3.OperationalError):
            with resilient_connection(manager, retries=1, breaker=breaker):
                pass
    with pytest.raises(CircuitBreakerOpenError):
        with resilient_connection(manager, retries=1, breaker=breaker):
            pass
