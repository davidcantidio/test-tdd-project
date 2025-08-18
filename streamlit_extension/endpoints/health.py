"""Health check endpoints for orchestration tools.

This module provides simple health-check utilities that can be used by
monitoring systems or orchestration tools such as Kubernetes.  The
implementation intentionally keeps the logic lightweight – the goal of
these utilities is to offer predictable structures that are easy to
consume in tests and during development.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import time
from typing import Dict, Tuple


class HealthStatus(str, Enum):
    """Enum representing component health states."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"


@dataclass
class ComponentChecker:
    """Collection of helper methods used by the health endpoints.

    The real project would integrate with databases, caches and other
    dependencies.  For the purposes of the tests we implement simple
    placeholders that return deterministic data which can easily be
    monkey‑patched to simulate different scenarios.
    """

    def check_database(self) -> Dict[str, str]:
        return {"status": HealthStatus.HEALTHY.value, "response_time": "1ms"}

    def check_cache(self) -> Dict[str, str]:
        return {
            "status": HealthStatus.HEALTHY.value,
            "hit_rate": "100%",
            "memory_usage": "0%",
        }

    def check_external_apis(self) -> Dict[str, str]:
        return {"status": HealthStatus.HEALTHY.value, "latency": "0ms"}

    def check_disk_space(self) -> Dict[str, str]:
        return {"status": HealthStatus.HEALTHY.value, "disk_usage": "0%"}

    def check_memory_usage(self) -> Dict[str, str]:
        return {
            "status": HealthStatus.HEALTHY.value,
            "cpu_usage": "0%",
            "memory_usage": "0%",
        }


class HealthCheckEndpoint:
    """Implements the different health‑check endpoints."""

    def __init__(self, start_time: float | None = None, version: str = "1.0.0", checker: ComponentChecker | None = None) -> None:
        self.start_time = start_time or time.time()
        self.version = version
        self.checker = checker or ComponentChecker()

    # ------------------------------------------------------------------
    # Helpers
    def _current_timestamp(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    # ------------------------------------------------------------------
    def basic_health(self) -> Dict[str, object]:
        """Return a very small health payload."""

        uptime_seconds = int(time.time() - self.start_time)
        uptime = str(timedelta(seconds=uptime_seconds))
        return {
            "status": HealthStatus.HEALTHY.value,
            "timestamp": self._current_timestamp(),
            "uptime": uptime,
            "version": self.version,
        }

    def detailed_health(self) -> Dict[str, object]:
        """Return detailed component information.

        The overall status is derived from the status of individual
        components – ``unhealthy`` takes precedence over ``degraded``
        which in turn takes precedence over ``healthy``.
        """

        database = self.checker.check_database()
        cache = self.checker.check_cache()
        memory = self.checker.check_memory_usage()
        disk = self.checker.check_disk_space()

        system = {
            "cpu_usage": memory.get("cpu_usage", "0%"),
            "memory_usage": memory.get("memory_usage", "0%"),
            "disk_usage": disk.get("disk_usage", "0%"),
        }

        components = {
            "database": database,
            "cache": cache,
            "system": system,
        }

        statuses = [database.get("status"), cache.get("status"), memory.get("status"), disk.get("status")]
        overall = HealthStatus.HEALTHY.value
        if HealthStatus.UNHEALTHY.value in statuses:
            overall = HealthStatus.UNHEALTHY.value
        elif HealthStatus.DEGRADED.value in statuses:
            overall = HealthStatus.DEGRADED.value

        return {
            "status": overall,
            "timestamp": self._current_timestamp(),
            "components": components,
        }

    def readiness_check(self) -> Tuple[int, Dict[str, object]]:
        """Readiness probe suitable for Kubernetes."""

        db = self.checker.check_database()
        cache = self.checker.check_cache()
        ready = db.get("status") == HealthStatus.HEALTHY.value and cache.get("status") == HealthStatus.HEALTHY.value
        status_code = 200 if ready else 503
        payload = {
            "ready": ready,
            "dependencies": {
                "database": "connected" if db.get("status") == HealthStatus.HEALTHY.value else "unavailable",
                "cache": "available" if cache.get("status") == HealthStatus.HEALTHY.value else "unavailable",
            },
        }
        return status_code, payload

    def liveness_check(self) -> Tuple[int, Dict[str, object]]:
        """Simple liveness probe."""

        return 200, {"alive": True, "last_heartbeat": self._current_timestamp()}
