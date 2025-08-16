"""Enhanced graceful shutdown system for production deployment.

This module provides comprehensive shutdown handling with proper resource cleanup,
connection draining, and signal management for production environments.
"""

from __future__ import annotations

import os
import signal
import threading
import time
import atexit
import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ShutdownPhase(Enum):
    """Enhanced shutdown phases for production"""
    RUNNING = auto()
    STOP_ACCEPTING_REQUESTS = auto()
    DRAIN_CONNECTIONS = auto()
    CLEANUP_RESOURCES = auto()
    FINAL_SHUTDOWN = auto()
    EMERGENCY_SHUTDOWN = auto()


@dataclass
class ShutdownHandler:
    """Individual shutdown handler with priority and timeout"""
    name: str
    handler: Callable[[], None]
    priority: int = 100  # Lower numbers execute first
    timeout: float = 30.0


class GracefulShutdownHandler:
    """Enhanced graceful shutdown coordinator for production deployment."""

    def __init__(self, shutdown_timeout: float = 60.0):
        self.cleanup_handlers: Dict[str, ShutdownHandler] = {}
        self.shutdown_timeout = shutdown_timeout
        self.shutdown_initiated = False
        self.current_phase = ShutdownPhase.RUNNING
        self._sequence: List[ShutdownPhase] = []
        self._shutdown_lock = threading.Lock()
        self._active_connections = set()
        self._connection_lock = threading.Lock()
        
        # Register signal handlers and atexit
        self.register_signal_handlers()
        atexit.register(self._emergency_cleanup)

    def register_signal_handlers(self) -> None:
        """Install OS signal handlers for graceful shutdown."""
        try:
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, self._signal_handler)
            if hasattr(signal, 'SIGINT'):
                signal.signal(signal.SIGINT, self._signal_handler)
            if hasattr(signal, 'SIGHUP'):
                signal.signal(signal.SIGHUP, self._signal_handler)
            logger.info("Signal handlers registered for graceful shutdown")
        except Exception as e:
            logger.warning(f"Could not register signal handlers: {e}")

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        signal_name = getattr(signal.Signals, 'name', str(signum)) if hasattr(signal, 'Signals') else str(signum)
        logger.info(f"Received shutdown signal: {signal_name}")
        self.initiate_shutdown(f"Signal {signal_name}")

    def initiate_shutdown(self, reason: str = "Manual shutdown") -> None:
        """Initiate graceful shutdown process."""
        with self._shutdown_lock:
            if self.shutdown_initiated:
                logger.warning("Shutdown already initiated")
                return
            
            self.shutdown_initiated = True
            self.current_phase = ShutdownPhase.STOP_ACCEPTING_REQUESTS

        logger.info(f"Initiating graceful shutdown: {reason}")
        
        # Execute shutdown in separate thread
        shutdown_thread = threading.Thread(
            target=self._execute_shutdown_sequence,
            args=(reason,),
            name="GracefulShutdown"
        )
        shutdown_thread.start()

    def _execute_shutdown_sequence(self, reason: str) -> None:
        """Execute the complete shutdown sequence."""
        start_time = time.time()
        
        try:
            self._sequence = [
                ShutdownPhase.STOP_ACCEPTING_REQUESTS,
                ShutdownPhase.DRAIN_CONNECTIONS,
                ShutdownPhase.CLEANUP_RESOURCES,
                ShutdownPhase.FINAL_SHUTDOWN
            ]
            
            for phase in self._sequence:
                self.current_phase = phase
                logger.info(f"Shutdown phase: {phase.name}")
                
                if phase == ShutdownPhase.STOP_ACCEPTING_REQUESTS:
                    self._stop_accepting_requests()
                elif phase == ShutdownPhase.DRAIN_CONNECTIONS:
                    self._drain_connections()
                elif phase == ShutdownPhase.CLEANUP_RESOURCES:
                    self.cleanup_resources()
                elif phase == ShutdownPhase.FINAL_SHUTDOWN:
                    self._final_shutdown()
            
            total_time = time.time() - start_time
            logger.info(f"Graceful shutdown completed in {total_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error during shutdown sequence: {e}")
            self._emergency_cleanup()

    def _stop_accepting_requests(self) -> None:
        """Stop accepting new requests/connections."""
        logger.info("Stopping acceptance of new requests")
        # Mark system as shutting down
        # Additional logic can be added here for specific frameworks

    def _drain_connections(self, timeout: float = 30.0) -> None:
        """Wait for active connections to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self._connection_lock:
                if not self._active_connections:
                    logger.info("All connections drained successfully")
                    return
                
                logger.info(f"Waiting for {len(self._active_connections)} active connections")
            
            time.sleep(1)
        
        # Timeout reached
        with self._connection_lock:
            if self._active_connections:
                logger.warning(f"Timeout reached, {len(self._active_connections)} connections still active")

    def cleanup_resources(self) -> None:
        """Execute all registered cleanup handlers."""
        # Sort handlers by priority (lower numbers first)
        sorted_handlers = sorted(
            self.cleanup_handlers.values(),
            key=lambda h: h.priority
        )
        
        for handler in sorted_handlers:
            start_time = time.time()
            
            try:
                logger.info(f"Executing cleanup handler: {handler.name}")
                
                # Execute with timeout
                self._execute_with_timeout(handler.handler, handler.timeout)
                
                duration = time.time() - start_time
                logger.info(f"Cleanup handler '{handler.name}' completed in {duration:.2f}s")
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Cleanup handler '{handler.name}' failed after {duration:.2f}s: {e}")

    def _execute_with_timeout(self, func: Callable, timeout: float) -> Any:
        """Execute function with timeout."""
        result = None
        exception = None
        
        def target():
            nonlocal result, exception
            try:
                result = func()
            except Exception as e:
                exception = e
        
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            logger.warning(f"Handler timed out after {timeout}s")
            raise TimeoutError(f"Handler execution timed out after {timeout}s")
        
        if exception:
            raise exception
        
        return result

    def _final_shutdown(self) -> None:
        """Final shutdown steps."""
        logger.info("Performing final shutdown steps")
        # Any final cleanup logic

    def _emergency_cleanup(self) -> None:
        """Emergency cleanup on unexpected exit."""
        if self.current_phase == ShutdownPhase.FINAL_SHUTDOWN:
            return
        
        logger.warning("Performing emergency cleanup")
        self.current_phase = ShutdownPhase.EMERGENCY_SHUTDOWN
        
        # Execute only high-priority handlers quickly
        for handler in self.cleanup_handlers.values():
            if handler.priority <= 10:  # Only critical handlers
                try:
                    handler.handler()
                    logger.info(f"Emergency cleanup: {handler.name}")
                except Exception as e:
                    logger.error(f"Emergency cleanup failed for {handler.name}: {e}")

    def shutdown_sequence(self) -> List[ShutdownPhase]:
        """Get the current shutdown sequence."""
        return list(self._sequence)

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for shutdown to complete."""
        timeout = timeout or self.shutdown_timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.current_phase == ShutdownPhase.FINAL_SHUTDOWN:
                return True
            time.sleep(0.1)
        
        return False

    def add_cleanup_handler(
        self, 
        name: str, 
        handler: Callable[[], None],
        priority: int = 100,
        timeout: float = 30.0
    ) -> None:
        """Add a cleanup handler with priority and timeout."""
        shutdown_handler = ShutdownHandler(
            name=name,
            handler=handler,
            priority=priority,
            timeout=timeout
        )
        self.cleanup_handlers[name] = shutdown_handler
        logger.info(f"Registered cleanup handler: {name} (priority: {priority})")

    @contextmanager
    def track_connection(self, connection_id: str):
        """Track active connections for proper draining."""
        with self._connection_lock:
            if self.shutdown_initiated:
                raise RuntimeError("Shutdown in progress, new connections not allowed")
            self._active_connections.add(connection_id)
        
        try:
            yield
        finally:
            with self._connection_lock:
                self._active_connections.discard(connection_id)

    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self.shutdown_initiated

    def get_status(self) -> Dict[str, Any]:
        """Get current shutdown status."""
        with self._connection_lock:
            active_connections = len(self._active_connections)
        
        return {
            "shutdown_initiated": self.shutdown_initiated,
            "current_phase": self.current_phase.name,
            "active_connections": active_connections,
            "registered_handlers": len(self.cleanup_handlers),
            "sequence": [phase.name for phase in self._sequence]
        }


# Global shutdown handler instance
shutdown_handler = GracefulShutdownHandler()

# Convenience functions
def register_cleanup(name: str, priority: int = 100, timeout: float = 30.0):
    """Decorator to register a function as a cleanup handler."""
    def decorator(func: Callable[[], None]) -> Callable[[], None]:
        shutdown_handler.add_cleanup_handler(name, func, priority, timeout)
        return func
    return decorator

def track_connection(connection_id: str):
    """Context manager to track connections during shutdown."""
    return shutdown_handler.track_connection(connection_id)

def is_shutting_down() -> bool:
    """Check if application is shutting down."""
    return shutdown_handler.is_shutting_down()

def get_shutdown_status() -> Dict[str, Any]:
    """Get current shutdown status."""
    return shutdown_handler.get_status()
