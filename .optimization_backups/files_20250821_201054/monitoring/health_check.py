#!/usr/bin/env python3
"""
🩺 Health Check Endpoint System

Addresses report.md requirement: "Implement health-check endpoint for orchestration"

This module provides:
- RESTful health check endpoint
- Database connectivity verification
- System resource monitoring
- Service dependency checks
- Kubernetes/Docker readiness probe support
"""

import os
import sys
import time
import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config.environment import get_config, is_production
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    get_config = None
    is_production = lambda: False

try:
    from streamlit_extension.utils.database import DatabaseManager
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    DatabaseManager = None

logger = logging.getLogger(__name__)


class HealthStatus:
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheck:
    """Individual health check component."""
    
    def __init__(self, name: str, check_func, timeout: float = 5.0, critical: bool = True):
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
        self.critical = critical
        self.last_check_time = None
        self.last_result = None
        self.last_error = None
    
    # TODO: Consider extracting this block into a separate method
    # TODO: Consider extracting this block into a separate method
    def run(self) -> Dict[str, Any]:
        """Run health check with timeout."""
        start_time = time.time()
        
        try:
            # Run check with timeout
            result = self._run_with_timeout()
            self.last_check_time = datetime.now(timezone.utc)
            self.last_result = result
            self.last_error = None
            
            return {
                "name": self.name,
                "status": result.get("status", HealthStatus.HEALTHY),
                "message": result.get("message", "Check passed"),
                "details": result.get("details", {}),
                "critical": self.critical,
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": self.last_check_time.isoformat()
            }
            
        except Exception as e:
            self.last_check_time = datetime.now(timezone.utc)
            self.last_error = str(e)
            self.last_result = None
            
            return {
                "name": self.name,
                "status": HealthStatus.UNHEALTHY,
                "message": f"Health check failed: {e}",
                "details": {"error": str(e)},
                "critical": self.critical,
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": self.last_check_time.isoformat()
            }
    
# TODO: Consider extracting this block into a separate method
    
# TODO: Consider extracting this block into a separate method
    
    def _run_with_timeout(self) -> Dict[str, Any]:
        """Run check function with timeout."""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Health check '{self.name}' timed out after {self.timeout}s")
        
        # Set timeout (Unix only)
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(self.timeout))
        
        try:
            result = self.check_func()
            return result if isinstance(result, dict) else {"status": HealthStatus.HEALTHY}
        finally:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)


# TODO: Consider extracting this block into a separate method
# TODO: Consider extracting this block into a separate method
class HealthCheckManager:
    """Manages multiple health checks and provides endpoints."""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.start_time = datetime.now(timezone.utc)
        self.version = "1.0.0"
        self.environment = "unknown"
        
        if CONFIG_AVAILABLE:
            try:
                config = get_config()
                self.environment = config.environment
                self.version = config.version
            except Exception:
                # TODO: Consider extracting this block into a separate method
                # TODO: Consider extracting this block into a separate method
                pass
        
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks."""
        # Database connectivity check
        if DATABASE_AVAILABLE:
            self.add_check("database", self._check_database, timeout=3.0, critical=True)
        
        # Configuration check
        if CONFIG_AVAILABLE:
            self.add_check("configuration", self._check_configuration, timeout=1.0, critical=True)
        
        # Disk space check
        self.add_check("disk_space", self._check_disk_space, timeout=2.0, critical=False)
        
        # Memory check
        self.add_check("memory", self._check_memory, timeout=1.0, critical=False)
        
        # System uptime
        self.add_check("uptime", self._check_uptime, timeout=0.5, critical=False)
    
    def add_check(self, name: str, check_func, timeout: float = 5.0, critical: bool = True):
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        """Add a custom health check."""
        check = HealthCheck(name, check_func, timeout, critical)
        self.checks.append(check)
        logger.info(f"Added health check: {name}")
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all health checks and return aggregated results."""
        start_time = time.time()
        check_results = []
        
        # Run all checks
        for check in self.checks:
            result = check.run()
            check_results.append(result)
        
        # Calculate overall status
        overall_status = self._calculate_overall_status(check_results)
        
        # Build response
        response = {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": self.environment,
            "version": self.version,
            "uptime_seconds": round((datetime.now(timezone.utc) - self.start_time).total_seconds()),
            # TODO: Consider extracting this block into a separate method
            # TODO: Consider extracting this block into a separate method
            "duration_ms": round((time.time() - start_time) * 1000, 2),
            "checks": check_results
        }
        
        return response
    
    def _calculate_overall_status(self, check_results: List[Dict[str, Any]]) -> str:
        """Calculate overall health status from individual checks."""
        critical_failed = any(
            result["status"] == HealthStatus.UNHEALTHY and result["critical"]
            for result in check_results
        )
        
        any_failed = any(
            result["status"] in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]
            for result in check_results
        )
        
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        if critical_failed:
            return HealthStatus.UNHEALTHY
        elif any_failed:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        if not DATABASE_AVAILABLE:
            return {
                "status": HealthStatus.DEGRADED,
                "message": "Database manager not available"
            }
        
        try:
            db_manager = DatabaseManager()
            
            # Test framework database
            with db_manager.get_connection("framework") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Database connectivity verified",
                "details": {
                    "tables": table_count,
                    "framework_db": str(db_manager.framework_db_path),
                    "timer_db": str(db_manager.timer_db_path)
                }
            }
            
# TODO: Consider extracting this block into a separate method
            
# TODO: Consider extracting this block into a separate method
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Database check failed: {e}",
                "details": {"error": str(e)}
            }
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration loading."""
        if not CONFIG_AVAILABLE:
            return {
                "status": HealthStatus.DEGRADED,
                "message": "Configuration system not available"
            }
        
        try:
            config = get_config()
            
            # Validate critical settings
            issues = []
            
            if is_production():
                if not config.google_oauth.client_id:
                    issues.append("Missing Google OAuth client ID")
                if not config.google_oauth.client_secret:
                    issues.append("Missing Google OAuth client secret")
            
            if issues:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": "Configuration issues detected",
                    "details": {"issues": issues}
                }
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Configuration loaded successfully",
                "details": {
                    "environment": config.environment,
                    "debug": config.debug,
                    "auth_required": config.security.require_auth
                # TODO: Consider extracting this block into a separate method
                # TODO: Consider extracting this block into a separate method
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Configuration check failed: {e}",
                "details": {"error": str(e)}
            }
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            import shutil
            
            # Check current directory disk space
            total, used, free = shutil.disk_usage(".")
            free_percent = (free / total) * 100
            
            # Warning thresholds
            if free_percent < 5:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: Only {free_percent:.1f}% disk space remaining"
            elif free_percent < 15:
                status = HealthStatus.DEGRADED
                message = f"Warning: Only {free_percent:.1f}% disk space remaining"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk space: {free_percent:.1f}% available"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "total_gb": round(total / (1024**3), 2),
                    "used_gb": round(used / (1024**3), 2),
                    "free_gb": round(free / (1024**3), 2),
                    # TODO: Consider extracting this block into a separate method
                    # TODO: Consider extracting this block into a separate method
                    "free_percent": round(free_percent, 1)
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.DEGRADED,
                "message": f"Disk space check failed: {e}",
                "details": {"error": str(e)}
            }
    
    def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            available_percent = memory.available / memory.total * 100
            
            # Memory thresholds
            if available_percent < 10:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: Only {available_percent:.1f}% memory available"
            elif available_percent < 20:
                status = HealthStatus.DEGRADED
                message = f"Warning: Only {available_percent:.1f}% memory available"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory: {available_percent:.1f}% available"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": round(memory.percent, 1),
                    "available_percent": round(available_percent, 1)
                }
            }
            
        except ImportError:
            # TODO: Consider extracting this block into a separate method
            # TODO: Consider extracting this block into a separate method
            return {
                "status": HealthStatus.DEGRADED,
                "message": "psutil not available for memory monitoring",
                "details": {"note": "Install psutil for memory monitoring"}
            }
        except Exception as e:
            return {
                "status": HealthStatus.DEGRADED,
                "message": f"Memory check failed: {e}",
                "details": {"error": str(e)}
            }
    
    def _check_uptime(self) -> Dict[str, Any]:
        """Check application uptime."""
        try:
            uptime_seconds = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            uptime_hours = uptime_seconds / 3600
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": f"Application uptime: {uptime_hours:.1f} hours",
                "details": {
                    "uptime_seconds": round(uptime_seconds),
                    "uptime_hours": round(uptime_hours, 2),
                    "start_time": self.start_time.isoformat()
                }
            }
            
        except Exception as e:
            return {
                # TODO: Consider extracting this block into a separate method
                # TODO: Consider extracting this block into a separate method
                "status": HealthStatus.DEGRADED,
                "message": f"Uptime check failed: {e}",
                "details": {"error": str(e)}
            }


class HealthCheckRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health check endpoints."""
    
    def __init__(self, health_manager: HealthCheckManager, *args, **kwargs):
        self.health_manager = health_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/health":
            self._handle_health_check()
        elif parsed_path.path == "/ready":
            # TODO: Consider extracting this block into a separate method
            # TODO: Consider extracting this block into a separate method
            self._handle_readiness_check()
        elif parsed_path.path == "/live":
            self._handle_liveness_check()
        elif parsed_path.path == "/metrics":
            self._handle_metrics()
        else:
            self._send_response(404, {"error": "Not found"})
    
    def _handle_health_check(self):
        """Handle full health check."""
        result = self.health_manager.run_checks()
        status_code = 200 if result["status"] == HealthStatus.HEALTHY else 503
        self._send_response(status_code, result)
    
    def _handle_readiness_check(self):
        """Handle Kubernetes readiness probe."""
        result = self.health_manager.run_checks()
        
        # Ready if no critical checks are failing
        critical_failed = any(
            check["status"] == HealthStatus.UNHEALTHY and check["critical"]
            for check in result["checks"]
        )
        
        if critical_failed:
            self._send_response(503, {
                "status": "not_ready",
                "message": "Critical health checks failing"
            # TODO: Consider extracting this block into a separate method
            # TODO: Consider extracting this block into a separate method
            })
        else:
            self._send_response(200, {
                "status": "ready",
                "message": "Service is ready to accept traffic"
            })
    
    def _handle_liveness_check(self):
        """Handle Kubernetes liveness probe."""
        # Simple alive check - just return 200 if process is running
        self._send_response(200, {
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def _handle_metrics(self):
        """Handle basic metrics endpoint."""
        result = self.health_manager.run_checks()
        
        # Convert to simple metrics format
        metrics = {
            "health_status": 1 if result["status"] == HealthStatus.HEALTHY else 0,
            "uptime_seconds": result["uptime_seconds"],
            "total_checks": len(result["checks"]),
            "failed_checks": sum(1 for check in result["checks"] 
                               if check["status"] != HealthStatus.HEALTHY),
            "check_duration_ms": result["duration_ms"]
        }
        
        self._send_response(200, metrics)
    
    def _send_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
# TODO: Consider extracting this block into a separate method
    
# TODO: Consider extracting this block into a separate method
    
    def log_message(self, format, *args):
        """Override to use Python logging."""
        logger.info(f"{self.address_string()} - {format % args}")


class HealthCheckServer:
    """HTTP server for health check endpoints."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.health_manager = HealthCheckManager()
        self.server = None
        self.server_thread = None
    
    def start(self, blocking: bool = False):
        """Start the health check server."""
        # Create request handler with health manager
        def handler_factory(*args, **kwargs):
            return HealthCheckRequestHandler(self.health_manager, *args, **kwargs)
        
        try:
            self.server = HTTPServer((self.host, self.port), handler_factory)
            logger.info(f"Health check server starting on {self.host}:{self.port}")
            
            if blocking:
                self.server.serve_forever()
            else:
                self.server_thread = threading.Thread(target=self.server.serve_forever)
                self.server_thread.daemon = True
                self.server_thread.start()
                logger.info(f"Health check server running in background")
                
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")
            raise
    
    def stop(self):
        """Stop the health check server."""
        if self.server:
            logger.info("Stopping health check server")
            self.server.shutdown()
            self.server.server_close()
            
        if self.server_thread:
            self.server_thread.join(timeout=5)


# Global health check server instance
_health_server: Optional[HealthCheckServer] = None


def start_health_check_server(host: str = "0.0.0.0", port: int = 8080, blocking: bool = False) -> HealthCheckServer:
    """Start the global health check server."""
    global _health_server
    
    if _health_server is None:
        _health_server = HealthCheckServer(host, port)
    
    _health_server.start(blocking=blocking)
    return _health_server


def stop_health_check_server():
    """Stop the global health check server."""
    global _health_server
    
    if _health_server:
        _health_server.stop()
        _health_server = None


def get_health_status() -> Dict[str, Any]:
    """Get current health status without starting server."""
    health_manager = HealthCheckManager()
    return health_manager.run_checks()


if __name__ == "__main__":
    # CLI interface for health checks
    import argparse
    
    parser = argparse.ArgumentParser(description="TDD Framework Health Check System")
    parser.add_argument("--port", type=int, default=8080, help="Server port")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--check-only", action="store_true", help="Run checks and exit")
    
    args = parser.parse_args()
    
    if args.check_only:
        # Run health checks and print results
        print("🩺 TDD Framework Health Check")
        print("=" * 50)
        
        result = get_health_status()
        
        print(f"Overall Status: {result['status'].upper()}")
        print(f"Environment: {result['environment']}")
        print(f"Version: {result['version']}")
        print(f"Uptime: {result['uptime_seconds']}s")
        print()
        
        for check in result['checks']:
            status_emoji = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.DEGRADED: "⚠️",
                HealthStatus.UNHEALTHY: "❌"
            }.get(check['status'], "❓")
            
            critical_mark = " (CRITICAL)" if check['critical'] else ""
            print(f"{status_emoji} {check['name']}{critical_mark}: {check['message']}")
        
        # Exit with appropriate code
        sys.exit(0 if result['status'] == HealthStatus.HEALTHY else 1)
    
    else:
        # Start server
        try:
            logging.basicConfig(level=logging.INFO)
            server = start_health_check_server(args.host, args.port, blocking=True)
        except KeyboardInterrupt:
            print("\nShutting down health check server...")
            stop_health_check_server()