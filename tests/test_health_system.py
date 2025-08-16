"""Test health check and shutdown systems."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import signal

from streamlit_extension.utils.health_check import HealthChecker, HealthStatus
from streamlit_extension.utils.shutdown_handler import ShutdownHandler


class TestHealthChecker:
    def test_database_health_check(self):
        """Test database health checking."""

        checker = HealthChecker()
        result = checker.check_database_health()
        assert result.name == "database"
        assert result.status == HealthStatus.HEALTHY

    def test_redis_health_check(self):
        """Test Redis health checking."""

        checker = HealthChecker()
        result = checker.check_redis_health()
        assert result.name == "redis"
        assert result.status == HealthStatus.HEALTHY

    def test_overall_health_status(self):
        """Test overall health status calculation."""

        checker = HealthChecker()
        # register a failing custom check
        checker.register_custom_check("failing", lambda: False)
        status = checker.get_overall_health()
        assert status == HealthStatus.UNHEALTHY

    def test_health_endpoint_response(self):
        """Test health endpoint JSON response format."""

        checker = HealthChecker()
        response = checker.get_health_endpoint_response()
        assert "status" in response
        assert isinstance(response.get("components"), list)
        assert response["status"] in {
            HealthStatus.HEALTHY,
            HealthStatus.UNHEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNKNOWN,
        }


class TestShutdownHandler:
    def test_cleanup_registration(self):
        """Test cleanup function registration."""

        handler = ShutdownHandler()
        called = {"value": False}

        def cleanup():
            called["value"] = True

        handler.register_cleanup_function("test", cleanup)
        assert "test" in handler.cleanup_functions

        handler.perform_graceful_shutdown()
        assert called["value"] is True

    def test_graceful_shutdown_sequence(self):
        """Test complete shutdown sequence."""

        handler = ShutdownHandler()
        calls = []

        handler.register_cleanup_function("database", lambda: calls.append("db"))
        handler.register_cleanup_function("redis", lambda: calls.append("redis"))
        handler.register_cleanup_function("sessions", lambda: calls.append("sess"))
        handler.register_cleanup_function("temp_files", lambda: calls.append("tmp"))

        handler.perform_graceful_shutdown()
        assert set(calls) == {"db", "redis", "sess", "tmp"}

    def test_signal_handling(self):
        """Test signal handler installation."""

        handler = ShutdownHandler()
        handler.install_signal_handlers()
        assert signal.getsignal(signal.SIGTERM) == handler._signal_handler
        assert signal.getsignal(signal.SIGINT) == handler._signal_handler
