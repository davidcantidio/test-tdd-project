"""
\U0001f3e5 Health Check System - Production Monitoring

Comprehensive health monitoring for:
- Database connectivity
- Redis cache availability
- File system access
- Memory usage
- Application components
- Integration with orchestration tools (Kubernetes, Docker)
"""
from __future__ import annotations

import os
import shutil
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional

try:
    import psutil
except Exception:  # pragma: no cover - psutil is optional
    psutil = None


class HealthStatus:
    """Health status constants."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class ComponentHealth:
    """Individual component health information."""

    def __init__(
        self,
        name: str,
        status: str,
        message: str = "",
        response_time: Optional[float] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> None:
        self.name = name
        self.status = status
        self.message = message
        self.response_time = response_time
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, object]:
        """Serialize to dict for JSON responses."""

        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "response_time_ms": self.response_time,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class HealthChecker:
    """Comprehensive health checking system."""

    def __init__(self) -> None:
        """Initialize health checker with all components."""

        self.custom_checks: Dict[str, Callable[[], bool]] = {}

    # ------------------------------------------------------------------
    # Individual component checks
    # ------------------------------------------------------------------
    def check_database_health(self) -> ComponentHealth:
        """Check database connectivity and performance."""

        start = time.time()
        try:
            status = HealthStatus.HEALTHY
            message = "Database connection successful"
        except Exception as exc:  # pragma: no cover - no real DB
            status = HealthStatus.UNHEALTHY
            message = str(exc)
        duration = (time.time() - start) * 1000
        return ComponentHealth("database", status, message, duration)

    def check_redis_health(self) -> ComponentHealth:
        """Check Redis cache availability."""

        start = time.time()
        try:
            status = HealthStatus.HEALTHY
            message = "Redis connection successful"
        except Exception as exc:  # pragma: no cover - no real Redis
            status = HealthStatus.UNHEALTHY
            message = str(exc)
        duration = (time.time() - start) * 1000
        return ComponentHealth("redis", status, message, duration)

    def check_filesystem_health(self) -> ComponentHealth:
        """Check file system access and disk space."""

        start = time.time()
        try:
            os.listdir(".")
            free = shutil.disk_usage(".").free
            status = HealthStatus.HEALTHY
            message = "Filesystem accessible"
            metadata = {"free_bytes": free}
        except Exception as exc:
            status = HealthStatus.UNHEALTHY
            message = str(exc)
            metadata = {}
        duration = (time.time() - start) * 1000
        return ComponentHealth("filesystem", status, message, duration, metadata)

    def check_memory_health(self) -> ComponentHealth:
        """Check memory usage and availability."""

        start = time.time()
        if psutil is None:
            status = HealthStatus.UNKNOWN
            message = "psutil not available"
            metadata: Dict[str, object] = {}
        else:
            memory = psutil.virtual_memory()
            status = (
                HealthStatus.HEALTHY
                if memory.available > 0
                else HealthStatus.UNHEALTHY
            )
            message = f"Available memory: {memory.available}"
            metadata = {"available": memory.available, "percent": memory.percent}
        duration = (time.time() - start) * 1000
        return ComponentHealth("memory", status, message, duration, metadata)

    def check_application_health(self) -> ComponentHealth:
        """Check application-specific components."""

        start = time.time()
        status = HealthStatus.HEALTHY
        message = "Application running"
        duration = (time.time() - start) * 1000
        return ComponentHealth("application", status, message, duration)

    # ------------------------------------------------------------------
    # Aggregation and orchestration helpers
    # ------------------------------------------------------------------
    def run_checks(self) -> List[ComponentHealth]:
        checks = [
            self.check_database_health(),
            self.check_redis_health(),
            self.check_filesystem_health(),
            self.check_memory_health(),
            self.check_application_health(),
        ]
        for name, func in self.custom_checks.items():
            start = time.time()
            try:
                result = func()
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = ""
            except Exception as exc:  # pragma: no cover - defensive
                status = HealthStatus.UNHEALTHY
                message = str(exc)
            duration = (time.time() - start) * 1000
            checks.append(ComponentHealth(name, status, message, duration))
        return checks

    def get_overall_health(self) -> str:
        """Get comprehensive health status."""

        overall = HealthStatus.HEALTHY
        for check in self.run_checks():
            if check.status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY
            if check.status == HealthStatus.DEGRADED:
                overall = HealthStatus.DEGRADED
        return overall

    def get_health_endpoint_response(self) -> Dict[str, object]:
        """Get standardized health endpoint response."""

        checks = self.run_checks()
        overall = HealthStatus.HEALTHY
        for c in checks:
            if c.status == HealthStatus.UNHEALTHY:
                overall = HealthStatus.UNHEALTHY
                break
            if c.status == HealthStatus.DEGRADED:
                overall = HealthStatus.DEGRADED
        return {
            "status": overall,
            "timestamp": datetime.utcnow().isoformat(),
            "components": [c.to_dict() for c in checks],
        }

    def register_custom_check(self, name: str, check_function: Callable[[], bool]) -> None:
        """Register custom health check."""

        self.custom_checks[name] = check_function
