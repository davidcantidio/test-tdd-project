from __future__ import annotations

"""Minimal load testing engine used by the automated tests.

The implementation focuses on deterministic behaviour and low resource
usage rather than absolute performance. It supports spawning a number of
virtual users that execute a set of actions for a given duration while
collecting metrics and basic system statistics.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, List, Optional

from .metrics_collector import MetricsCollector
from .performance_monitor import PerformanceMonitor


class LoadTester:
    """Execute simple load test scenarios."""

    def __init__(self, users: int, duration: float, actions: Iterable[Callable[[], None]], on_error: Optional[Callable[[BaseException], None]] = None):
        self.users = users
        self.duration = duration
        self.actions: List[Callable[[], None]] = list(actions)
        self.metrics = MetricsCollector()
        self.monitor = PerformanceMonitor()
        self._on_error = on_error

    def _user_loop(self, stop_time: float) -> None:
        while time.perf_counter() < stop_time:
            for action in self.actions:
                start = time.perf_counter()
                success = True
                try:
                    action()
                except Exception as exc:  # captura exceção para telemetria
                    success = False
                    if self._on_error:
                        try:
                            self._on_error(exc)
                        except Exception:
                            pass
                    self.metrics.record_exception(exc, (time.perf_counter() - start) * 1000)
                    # Verifica tempo novamente para não ultrapassar duração
                    if time.perf_counter() >= stop_time:
                        break
                    continue
                elapsed = (time.perf_counter() - start) * 1000
                self.metrics.record(elapsed, success)
                if time.perf_counter() >= stop_time:
                    break

    def run(self) -> dict:
        """Run the configured scenario and return collected metrics."""

        self.metrics.start()
        stop_time = time.perf_counter() + self.duration
        with ThreadPoolExecutor(max_workers=self.users) as executor:
            for _ in range(self.users):
                executor.submit(self._user_loop, stop_time)
        self.metrics.end()
        summary = self.metrics.summary()
        summary["resources"] = self.monitor.sample()
        return summary