"""Light‑weight monitoring helpers used for unit tests.

The goal of this module is to provide a minimal yet functional monitoring
framework.  It gathers basic metrics, evaluates them against configured
thresholds and can export the data in a Prometheus friendly plain text
format.  The implementation is intentionally simple so that tests can
exercise behaviour without needing heavy dependencies or external
services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import os
import shutil


# ---------------------------------------------------------------------------
# Metrics collection

@dataclass
class MetricsCollector:
    """Collect basic system and application metrics."""

    def cpu_usage(self) -> float:
        # ``os.getloadavg`` is not available on Windows; fall back to 0.0
        try:
            load1, _, _ = os.getloadavg()
            # normalise to a 0-100 percentage assuming 1 CPU
            return float(min(load1 * 100.0, 100.0))
        except OSError:  # pragma: no cover - platform specific
            return 0.0

    def memory_usage(self) -> float:
        # Process memory usage via ``resource`` would be possible but is
        # avoided to keep things portable.  Instead we use the total
        # virtual memory from ``os.sysconf`` when available.
        try:
            used = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
            return float(used / 1024 / 1024)
        except (ValueError, AttributeError, OSError):  # pragma: no cover
            return 0.0

    def disk_usage(self) -> float:
        usage = shutil.disk_usage("/")
        return float(usage.used) / float(usage.total) * 100.0

    def connection_pool_stats(self) -> Dict[str, int]:
        return {"active": 0, "idle": 0, "max": 0}

    def response_time_metrics(self) -> Dict[str, float]:
        return {"average_ms": 0.0, "p95_ms": 0.0}


# ---------------------------------------------------------------------------
# Alerting

@dataclass
class AlertManager:
    """Basic threshold based alert manager."""

    thresholds: Dict[str, float] = field(default_factory=dict)
    notifications: List[str] = field(default_factory=list)

    def define_thresholds(self, thresholds: Dict[str, float]) -> None:
        self.thresholds.update(thresholds)

    def check_alerts(self, metrics: Dict[str, float]) -> List[str]:
        alerts: List[str] = []
        for key, value in metrics.items():
            threshold = self.thresholds.get(key)
            if threshold is not None and value > threshold:
                alerts.append(f"{key} threshold exceeded: {value} > {threshold}")
        return alerts

    def send_notifications(self, alerts: List[str]) -> None:
        self.notifications.extend(alerts)


# ---------------------------------------------------------------------------
# System monitor facade

@dataclass
class SystemMonitor:
    """Facade coordinating metrics collection and alerting."""

    collector: MetricsCollector = field(default_factory=MetricsCollector)
    alert_manager: AlertManager = field(default_factory=AlertManager)

    def collect_metrics(self) -> Dict[str, float]:
        return {
            "cpu_usage": self.collector.cpu_usage(),
            "memory_usage": self.collector.memory_usage(),
            "disk_usage": self.collector.disk_usage(),
        }

    def check_performance(self) -> Dict[str, str]:
        metrics = self.collect_metrics()
        status: Dict[str, str] = {}
        for key, value in metrics.items():
            threshold = self.alert_manager.thresholds.get(key, float("inf"))
            status[key] = "healthy" if value <= threshold else "degraded"
        return status

    def generate_alerts(self) -> List[str]:
        metrics = self.collect_metrics()
        alerts = self.alert_manager.check_alerts(metrics)
        self.alert_manager.send_notifications(alerts)
        return alerts

    def export_metrics(self) -> str:
        metrics = self.collect_metrics()
        # Export in a simple Prometheus-style text format
        return "\n".join(f"{key} {value}" for key, value in metrics.items())
