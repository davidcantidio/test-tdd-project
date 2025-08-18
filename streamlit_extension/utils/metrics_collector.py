from __future__ import annotations

"""Simple metrics collection utilities for load testing.

This module provides a minimal `MetricsCollector` class that records
response times and error counts while a load test is running. It can
calculate common statistics such as percentiles and throughput which are
useful for basic performance analysis.
"""

from dataclasses import dataclass, field
import math
import statistics
import time
from typing import Dict, List, Optional


def _percentile(values: List[float], percent: float) -> float:
    """Return the requested percentile from a list of values.

    This implementation avoids an optional numpy dependency while still
    providing deterministic results for small datasets used in tests.
    """

    if not values:
        return 0.0
    if not 0 <= percent <= 100:
        raise ValueError("percent must be in the range 0..100")
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (percent / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return d0 + d1


@dataclass
class MetricsCollector:
    """Collect response time and error metrics during load tests."""

    response_times: List[float] = field(default_factory=list)
    errors: int = 0
    start_time: float | None = None
    end_time: float | None = None
    _fail_examples: List[str] = field(default_factory=list)

    def start(self) -> None:
        """Record the start time of the measurement window."""

        self.start_time = time.perf_counter()

    def end(self) -> None:
        """Record the end time of the measurement window."""

        self.end_time = time.perf_counter()

    def record(self, elapsed_ms: float, success: bool = True) -> None:
        """Store a single operation's elapsed time and success flag."""
        if elapsed_ms < 0:
            # Protege contra valores negativos por clock skew/erros
            elapsed_ms = 0.0
        self.response_times.append(float(elapsed_ms))
        if not success:
            self.errors += 1

    def record_exception(self, exc: BaseException, elapsed_ms: float) -> None:
        """Atalho para registrar falha com amostra do erro (limitado)."""
        self.record(elapsed_ms, success=False)
        if len(self._fail_examples) < 5:
            self._fail_examples.append(type(exc).__name__)

    # summary returns dict with response_time, throughput, errors
    def summary(self) -> Dict[str, Dict[str, float]]:
        """Return a summary of all collected metrics."""

        rt_stats: Dict[str, float] = {}
        if self.response_times:
            rts = self.response_times
            rt_stats = {
                "min": min(rts),
                "max": max(rts),
                "mean": statistics.mean(rts),
                "median": statistics.median(rts),
                "p95": _percentile(rts, 95),
                "p99": _percentile(rts, 99),
            }
        duration = 0.0
        if self.start_time is not None and self.end_time is not None:
            duration = self.end_time - self.start_time
        throughput = len(self.response_times) / duration if duration > 0 else 0.0
        error_rate = (
            self.errors / len(self.response_times) if self.response_times else 0.0
        )
        return {
            "response_time": rt_stats,
            "throughput": {"requests_per_second": throughput},
            "errors": {
                "total_errors": self.errors,
                "error_rate": error_rate,
            },
        }