"""
\U0001f504 Graceful Shutdown Handler

Manages clean application shutdown:
- Database connection cleanup
- Redis connection closure
- Active session completion
- Resource cleanup
- Signal handling (SIGTERM, SIGINT)
"""

import signal
from typing import Callable, Dict


class ShutdownHandler:
    """Manages graceful application shutdown."""

    def __init__(self) -> None:
        """Initialize shutdown handler."""

        self.cleanup_functions: Dict[str, Callable[[], None]] = {}
        self._installed = False
        self.shutdown_performed = False

    def register_cleanup_function(self, name: str, cleanup_func: Callable[[], None]) -> None:
        """Register cleanup function for shutdown."""

        self.cleanup_functions[name] = cleanup_func

    def cleanup_database_connections(self) -> None:
        """Clean up all database connections."""

        func = self.cleanup_functions.get("database")
        if func:
            func()

    def cleanup_redis_connections(self) -> None:
        """Clean up Redis connections."""

        func = self.cleanup_functions.get("redis")
        if func:
            func()

    def cleanup_active_sessions(self) -> None:
        """Complete or save active user sessions."""

        func = self.cleanup_functions.get("sessions")
        if func:
            func()

    def cleanup_temporary_files(self) -> None:
        """Clean up temporary files and caches."""

        func = self.cleanup_functions.get("temp_files")
        if func:
            func()

    def perform_graceful_shutdown(self) -> None:
        """Execute complete graceful shutdown sequence."""

        if self.shutdown_performed:
            return
        self.shutdown_performed = True

        # Run all registered cleanup functions
        for func in list(self.cleanup_functions.values()):
            try:
                func()
            except Exception:
                pass

        self.cleanup_database_connections()
        self.cleanup_redis_connections()
        self.cleanup_active_sessions()
        self.cleanup_temporary_files()

    def _signal_handler(self, signum, frame) -> None:  # pragma: no cover - called by signal
        self.perform_graceful_shutdown()

    def install_signal_handlers(self) -> None:
        """Install signal handlers for clean shutdown."""

        if self._installed:
            return
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        self._installed = True
