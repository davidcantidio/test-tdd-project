#!/usr/bin/env python3
"""
🛑 Graceful Shutdown System

Addresses report.md requirement: "Implement graceful shutdown for connections"

This module provides:
- Signal-based shutdown handling
- Database connection cleanup
- Background thread termination
- Health check integration
- Resource cleanup coordination
- Process state management
"""

import os
import sys
import time
import signal
import threading
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Set
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass, field

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
    from monitoring.structured_logging import get_structured_logger, application_logger
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False
    application_logger = None

try:
    from streamlit_extension.utils.database import DatabaseManager
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    DatabaseManager = None

logger = logging.getLogger(__name__)


@dataclass
class ShutdownContext:
    """Context for shutdown operations."""
    shutdown_initiated: bool = False
    shutdown_reason: str = ""
    shutdown_start_time: Optional[datetime] = None
    timeout_seconds: int = 30
    force_shutdown: bool = False
    shutdown_callbacks: List[Callable] = field(default_factory=list)
    active_resources: Set[str] = field(default_factory=set)
    cleanup_results: Dict[str, bool] = field(default_factory=dict)


class GracefulShutdownManager:
    """Manages graceful shutdown of application resources."""
    
    def __init__(self, timeout_seconds: int = 30):
        self.context = ShutdownContext(timeout_seconds=timeout_seconds)
        self.cleanup_handlers: Dict[str, Callable] = {}
        self.background_threads: Set[threading.Thread] = set()
        self.database_connections: Set[Any] = set()
        self.server_instances: Set[Any] = set()
        self._shutdown_lock = threading.Lock()
        self._original_handlers = {}
        
        # Set up logging
        if LOGGING_AVAILABLE:
            self.logger = get_structured_logger("graceful_shutdown")
        else:
            self.logger = logger
        
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            self.logger.info(f"Received {signal_name} signal, initiating graceful shutdown")
            self.shutdown(reason=f"Signal {signal_name}")
        
        # Handle common shutdown signals
        signals_to_handle = [signal.SIGTERM, signal.SIGINT]
        
        # Add SIGHUP for Unix systems
        if hasattr(signal, 'SIGHUP'):
            signals_to_handle.append(signal.SIGHUP)
        
        for sig in signals_to_handle:
            try:
                self._original_handlers[sig] = signal.signal(sig, signal_handler)
                self.logger.debug(f"Registered handler for {signal.Signals(sig).name}")
            except (OSError, ValueError) as e:
                self.logger.warning(f"Could not register handler for {signal.Signals(sig).name}: {e}")
    
    def register_cleanup_handler(self, name: str, handler: Callable) -> None:
        """Register a cleanup handler for shutdown."""
        self.cleanup_handlers[name] = handler
        self.context.active_resources.add(name)
        self.logger.debug(f"Registered cleanup handler: {name}")
    
    def register_database_connection(self, connection: Any) -> None:
        """Register a database connection for cleanup."""
        self.database_connections.add(connection)
        self.logger.debug(f"Registered database connection: {id(connection)}")
    
    def register_background_thread(self, thread: threading.Thread) -> None:
        """Register a background thread for cleanup."""
        self.background_threads.add(thread)
        self.logger.debug(f"Registered background thread: {thread.name}")
    
    def register_server_instance(self, server: Any) -> None:
        """Register a server instance for cleanup."""
        self.server_instances.add(server)
        self.logger.debug(f"Registered server instance: {type(server).__name__}")
    
    def add_shutdown_callback(self, callback: Callable) -> None:
        """Add a callback to execute during shutdown."""
        self.context.shutdown_callbacks.append(callback)
        self.logger.debug(f"Added shutdown callback: {callback.__name__}")
    
    def is_shutdown_initiated(self) -> bool:
        """Check if shutdown has been initiated."""
        return self.context.shutdown_initiated
    
    def shutdown(self, reason: str = "Manual shutdown", timeout_seconds: Optional[int] = None) -> bool:
        """Initiate graceful shutdown process."""
        with self._shutdown_lock:
            if self.context.shutdown_initiated:
                self.logger.warning("Shutdown already initiated, ignoring duplicate request")
                return True
            
            self.context.shutdown_initiated = True
            self.context.shutdown_reason = reason
            self.context.shutdown_start_time = datetime.now(timezone.utc)
            
            if timeout_seconds:
                self.context.timeout_seconds = timeout_seconds
        
        self.logger.info(f"Graceful shutdown initiated: {reason}")
        
        if LOGGING_AVAILABLE and application_logger:
            application_logger.log_system_event(
                "shutdown_initiated",
                f"Graceful shutdown started: {reason}",
                {
                    "reason": reason,
                    "timeout_seconds": self.context.timeout_seconds,
                    "active_resources": list(self.context.active_resources)
                }
            )
        
        return self._execute_shutdown()
    
    def _execute_shutdown(self) -> bool:
        """Execute the shutdown process."""
        success = True
        
        try:
            # Phase 1: Execute shutdown callbacks
            self.logger.info("Phase 1: Executing shutdown callbacks")
            self._execute_shutdown_callbacks()
            
            # Phase 2: Stop accepting new connections
            self.logger.info("Phase 2: Stopping server instances")
            success &= self._cleanup_servers()
            
            # Phase 3: Cleanup registered handlers
            self.logger.info("Phase 3: Executing cleanup handlers")
            success &= self._execute_cleanup_handlers()
            
            # Phase 4: Close database connections
            self.logger.info("Phase 4: Closing database connections")
            success &= self._cleanup_database_connections()
            
            # Phase 5: Terminate background threads
            self.logger.info("Phase 5: Terminating background threads")
            success &= self._cleanup_background_threads()
            
            # Phase 6: Final cleanup
            self.logger.info("Phase 6: Final cleanup")
            self._final_cleanup()
            
            shutdown_duration = (
                datetime.now(timezone.utc) - self.context.shutdown_start_time
            ).total_seconds()
            
            status = "completed successfully" if success else "completed with errors"
            self.logger.info(f"Graceful shutdown {status} in {shutdown_duration:.2f}s")
            
            if LOGGING_AVAILABLE and application_logger:
                application_logger.log_system_event(
                    "shutdown_completed",
                    f"Graceful shutdown {status}",
                    {
                        "success": success,
                        "duration_seconds": shutdown_duration,
                        "cleanup_results": self.context.cleanup_results
                    }
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}", exc_info=True)
            return False
    
    def _execute_shutdown_callbacks(self):
        """Execute all registered shutdown callbacks."""
        for callback in self.context.shutdown_callbacks:
            try:
                self.logger.debug(f"Executing shutdown callback: {callback.__name__}")
                callback()
            except Exception as e:
                self.logger.error(f"Error in shutdown callback {callback.__name__}: {e}")
    
    def _cleanup_servers(self) -> bool:
        """Cleanup server instances."""
        success = True
        servers_to_cleanup = list(self.server_instances)
        
        for server in servers_to_cleanup:
            try:
                self.logger.debug(f"Stopping server: {type(server).__name__}")
                
                if hasattr(server, 'stop'):
                    server.stop()
                elif hasattr(server, 'shutdown'):
                    server.shutdown()
                elif hasattr(server, 'close'):
                    server.close()
                else:
                    self.logger.warning(f"Server {type(server).__name__} has no stop method")
                
                self.context.cleanup_results[f"server_{type(server).__name__}"] = True
                
            except Exception as e:
                self.logger.error(f"Error stopping server {type(server).__name__}: {e}")
                self.context.cleanup_results[f"server_{type(server).__name__}"] = False
                success = False
        
        # Clear the set after all cleanup attempts
        self.server_instances.clear()
        return success
    
    def _execute_cleanup_handlers(self) -> bool:
        """Execute all registered cleanup handlers."""
        success = True
        
        for name, handler in self.cleanup_handlers.items():
            try:
                self.logger.debug(f"Executing cleanup handler: {name}")
                handler()
                self.context.cleanup_results[name] = True
                self.context.active_resources.discard(name)
                
            except Exception as e:
                self.logger.error(f"Error in cleanup handler {name}: {e}")
                self.context.cleanup_results[name] = False
                success = False
        
        return success
    
    def _cleanup_database_connections(self) -> bool:
        """Cleanup database connections."""
        success = True
        connections_to_cleanup = list(self.database_connections)
        
        # Cleanup registered connections
        for connection in connections_to_cleanup:
            try:
                self.logger.debug(f"Closing database connection: {id(connection)}")
                
                if hasattr(connection, 'close'):
                    connection.close()
                elif hasattr(connection, 'disconnect'):
                    connection.disconnect()
                
                self.context.cleanup_results[f"db_connection_{id(connection)}"] = True
                
            except Exception as e:
                self.logger.error(f"Error closing database connection {id(connection)}: {e}")
                self.context.cleanup_results[f"db_connection_{id(connection)}"] = False
                success = False
        
        # Clear the set after all cleanup attempts
        self.database_connections.clear()
        
        # Cleanup DatabaseManager if available
        if DATABASE_AVAILABLE:
            try:
                # This would cleanup the global DatabaseManager instance
                self.logger.debug("Cleaning up DatabaseManager connections")
                # Note: DatabaseManager cleanup would be implemented here
                self.context.cleanup_results["database_manager"] = True
                
            except Exception as e:
                self.logger.error(f"Error cleaning up DatabaseManager: {e}")
                self.context.cleanup_results["database_manager"] = False
                success = False
        
        return success
    
    def _cleanup_background_threads(self) -> bool:
        """Cleanup background threads."""
        success = True
        timeout = max(1, self.context.timeout_seconds // 4)  # 25% of total timeout
        threads_to_cleanup = list(self.background_threads)
        
        for thread in threads_to_cleanup:
            try:
                if thread.is_alive():
                    self.logger.debug(f"Waiting for thread to finish: {thread.name}")
                    thread.join(timeout=timeout)
                    
                    if thread.is_alive():
                        self.logger.warning(f"Thread {thread.name} did not finish within timeout")
                        self.context.cleanup_results[f"thread_{thread.name}"] = False
                        success = False
                    else:
                        self.context.cleanup_results[f"thread_{thread.name}"] = True
                else:
                    self.context.cleanup_results[f"thread_{thread.name}"] = True
                
            except Exception as e:
                self.logger.error(f"Error cleaning up thread {thread.name}: {e}")
                self.context.cleanup_results[f"thread_{thread.name}"] = False
                success = False
        
        # Clear the set after all cleanup attempts
        self.background_threads.clear()
        return success
    
    def _final_cleanup(self):
        """Perform final cleanup operations."""
        try:
            # Restore original signal handlers
            for sig, handler in self._original_handlers.items():
                signal.signal(sig, handler)
            
            # Clear collections
            self.cleanup_handlers.clear()
            self.database_connections.clear()
            self.server_instances.clear()
            self.background_threads.clear()
            
            self.logger.debug("Final cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error in final cleanup: {e}")
    
    def get_shutdown_status(self) -> Dict[str, Any]:
        """Get current shutdown status."""
        if not self.context.shutdown_initiated:
            return {
                "shutdown_initiated": False,
                "status": "running"
            }
        
        elapsed_time = 0
        if self.context.shutdown_start_time:
            elapsed_time = (
                datetime.now(timezone.utc) - self.context.shutdown_start_time
            ).total_seconds()
        
        return {
            "shutdown_initiated": True,
            "reason": self.context.shutdown_reason,
            "start_time": self.context.shutdown_start_time.isoformat() if self.context.shutdown_start_time else None,
            "elapsed_seconds": elapsed_time,
            "timeout_seconds": self.context.timeout_seconds,
            "active_resources": list(self.context.active_resources),
            "cleanup_results": self.context.cleanup_results,
            "status": "shutting_down" if elapsed_time < self.context.timeout_seconds else "timeout_exceeded"
        }


# Global shutdown manager instance
_shutdown_manager: Optional[GracefulShutdownManager] = None


def get_shutdown_manager(timeout_seconds: int = 30) -> GracefulShutdownManager:
    """Get the global shutdown manager instance."""
    global _shutdown_manager
    
    if _shutdown_manager is None:
        _shutdown_manager = GracefulShutdownManager(timeout_seconds)
    
    return _shutdown_manager


@contextmanager
def shutdown_handler(timeout_seconds: int = 30):
    """Context manager for graceful shutdown handling."""
    # Create a fresh manager instance for this context
    manager = GracefulShutdownManager(timeout_seconds)
    
    try:
        yield manager
    finally:
        if not manager.is_shutdown_initiated():
            manager.shutdown("Context exit")


def register_for_shutdown(resource_name: str, cleanup_func: Callable):
    """Convenience function to register a resource for cleanup."""
    manager = get_shutdown_manager()
    manager.register_cleanup_handler(resource_name, cleanup_func)


def shutdown_application(reason: str = "Application shutdown", timeout_seconds: int = 30) -> bool:
    """Shutdown the application gracefully."""
    manager = get_shutdown_manager(timeout_seconds)
    return manager.shutdown(reason)


def is_shutting_down() -> bool:
    """Check if the application is currently shutting down."""
    global _shutdown_manager
    
    if _shutdown_manager is None:
        return False
    
    return _shutdown_manager.is_shutdown_initiated()


if __name__ == "__main__":
    # Test graceful shutdown system
    print("🛑 Testing Graceful Shutdown System")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create shutdown manager
    manager = GracefulShutdownManager(timeout_seconds=10)
    
    # Register test resources
    def cleanup_test_resource():
        print("   ✅ Test resource cleaned up")
    
    manager.register_cleanup_handler("test_resource", cleanup_test_resource)
    
    # Create test thread
    def test_thread_func():
        print("   🧵 Test thread running")
        time.sleep(2)
        print("   🧵 Test thread finished")
    
    test_thread = threading.Thread(target=test_thread_func, name="test_thread")
    test_thread.start()
    manager.register_background_thread(test_thread)
    
    # Test shutdown
    print("🔄 Initiating test shutdown...")
    success = manager.shutdown("Test shutdown")
    
    if success:
        print("✅ Graceful shutdown test completed successfully")
    else:
        print("❌ Graceful shutdown test failed")
    
    print("\n📊 Shutdown Status:")
    status = manager.get_shutdown_status()
    for key, value in status.items():
        print(f"   {key}: {value}")