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
from typing import Callable, Iterable, List

from .metrics_collector import MetricsCollector
from .performance_monitor import PerformanceMonitor


class LoadTester:
    """Execute simple load test scenarios."""

    def __init__(self, users: int, duration: float, actions: Iterable[Callable[[], None]]):
        self.users = users
        self.duration = duration
        self.actions: List[Callable[[], None]] = list(actions)
        self.metrics = MetricsCollector()
        self.monitor = PerformanceMonitor()

    def _user_loop(self, stop_time: float) -> None:
        while time.perf_counter() < stop_time:
            for action in self.actions:
                start = time.perf_counter()
                success = True
                try:
                    action()
                except Exception:
                    success = False
                elapsed = (time.perf_counter() - start) * 1000
                self.metrics.record(elapsed, success)

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