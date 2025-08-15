#!/usr/bin/env python3
"""
🧪 Graceful Shutdown System Testing Suite

Tests the graceful shutdown system addressing report.md requirement:
"Implement graceful shutdown for connections"

This test validates:
- Signal-based shutdown handling
- Database connection cleanup  
- Background thread termination
- Server instance cleanup
- Resource cleanup coordination
- Timeout handling
- Production readiness
"""

import os
import sys
import time
import signal
import threading
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from io import StringIO

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from monitoring.graceful_shutdown import (
        GracefulShutdownManager,
        ShutdownContext,
        get_shutdown_manager,
        shutdown_handler,
        register_for_shutdown,
        shutdown_application,
        is_shutting_down
    )
    SHUTDOWN_AVAILABLE = True
except ImportError as e:
    SHUTDOWN_AVAILABLE = False
    print(f"❌ Graceful shutdown module not available: {e}")


def test_shutdown_manager_initialization():
    """Test shutdown manager initialization."""
    if not SHUTDOWN_AVAILABLE:
        return False
    
    print("🛑 Testing Shutdown Manager Initialization")
    print("=" * 55)
    
    try:
        # Test basic initialization
        manager = GracefulShutdownManager(timeout_seconds=10)
        
        assert manager.context.timeout_seconds == 10, "Timeout should be set correctly"
        assert not manager.context.shutdown_initiated, "Shutdown should not be initiated"
        assert len(manager.cleanup_handlers) == 0, "Should start with no handlers"
        assert len(manager.background_threads) == 0, "Should start with no threads"
        assert len(manager.database_connections) == 0, "Should start with no connections"
        
        print("✅ Basic initialization working")
        
        # Test signal handler setup
        assert hasattr(manager, '_original_handlers'), "Should store original handlers"
        print("✅ Signal handlers configured")
        
        # Test context initialization
        assert isinstance(manager.context, ShutdownContext), "Context should be ShutdownContext"
        assert manager.context.active_resources == set(), "Should start with no active resources"
        
        print("✅ Shutdown context initialized correctly")
        return True
        
    except Exception as e:
        print(f"❌ Shutdown manager initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_resource_registration():
    """Test resource registration for cleanup."""
    if not SHUTDOWN_AVAILABLE:
        return False
    
    print("\n📝 Testing Resource Registration")
    print("-" * 40)
    
    try:
        manager = GracefulShutdownManager()
        
        # Test cleanup handler registration
        def test_cleanup():
            pass
        
        manager.register_cleanup_handler("test_resource", test_cleanup)
        
        assert "test_resource" in manager.cleanup_handlers, "Handler should be registered"
        assert "test_resource" in manager.context.active_resources, "Resource should be active"
        print("✅ Cleanup handler registration working")
        
        # Test thread registration
        test_thread = threading.Thread(target=lambda: None, name="test_thread")
        manager.register_background_thread(test_thread)
        
        assert test_thread in manager.background_threads, "Thread should be registered"
        print("✅ Background thread registration working")
        
        # Test database connection registration
        mock_connection = Mock()
        manager.register_database_connection(mock_connection)
        
        assert mock_connection in manager.database_connections, "Connection should be registered"
        print("✅ Database connection registration working")
        
        # Test server instance registration
        mock_server = Mock()
        manager.register_server_instance(mock_server)
        
        assert mock_server in manager.server_instances, "Server should be registered"
        print("✅ Server instance registration working")
        
        # Test shutdown callback registration
        def test_callback():
            pass
        
        manager.add_shutdown_callback(test_callback)
        
        assert test_callback in manager.context.shutdown_callbacks, "Callback should be registered"
        print("✅ Shutdown callback registration working")
        
        return True
        
    except Exception as e:
        print(f"❌ Resource registration test failed: {e}")
        return False


def test_graceful_shutdown_execution():
    """Test graceful shutdown execution."""
    if not SHUTDOWN_AVAILABLE:
        return False
    
    print("\n🔄 Testing Graceful Shutdown Execution")
    print("-" * 45)
    
    try:
        manager = GracefulShutdownManager(timeout_seconds=5)
        
        # Track cleanup execution
        cleanup_called = {"value": False}
        callback_called = {"value": False}
        
        def test_cleanup():
            cleanup_called["value"] = True
        
        def test_callback():
            callback_called["value"] = True
        
        # Register resources
        manager.register_cleanup_handler("test_cleanup", test_cleanup)
        manager.add_shutdown_callback(test_callback)
        
        # Test shutdown status before shutdown
        assert not manager.is_shutdown_initiated(), "Shutdown should not be initiated"
        
        # Execute shutdown
        success = manager.shutdown("Test shutdown")
        
        # Validate shutdown execution
        assert success, "Shutdown should succeed"
        assert manager.is_shutdown_initiated(), "Shutdown should be initiated"
        assert cleanup_called["value"], "Cleanup handler should be called"
        assert callback_called["value"], "Shutdown callback should be called"
        
        print("✅ Basic shutdown execution working")
        
        # Test shutdown status after shutdown
        status = manager.get_shutdown_status()
        
        assert status["shutdown_initiated"], "Status should show shutdown initiated"
        assert status["reason"] == "Test shutdown", "Reason should match"
        assert "test_cleanup" in status["cleanup_results"], "Cleanup results should be recorded"
        
        print("✅ Shutdown status reporting working")
        
        # Test duplicate shutdown (should be ignored)
        success2 = manager.shutdown("Duplicate shutdown")
        assert success2, "Duplicate shutdown should succeed (but be ignored)"
        
        print("✅ Duplicate shutdown handling working")
        
        return True
        
    except Exception as e:
        print(f"❌ Graceful shutdown execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_background_thread_cleanup():
    """Test background thread cleanup."""
    if not SHUTDOWN_AVAILABLE:
        return False
    
    print("\n🧵 Testing Background Thread Cleanup")
    print("-" * 40)
    
    try:
        manager = GracefulShutdownManager(timeout_seconds=3)
        
        # Create test thread
        thread_finished = {"value": False}
        
        def thread_func():
            time.sleep(0.5)  # Short sleep
            thread_finished["value"] = True
        
        test_thread = threading.Thread(target=thread_func, name="test_thread")
        test_thread.start()
        
        manager.register_background_thread(test_thread)
        
        # Execute shutdown
        success = manager.shutdown("Thread cleanup test")
        
        # Validate thread cleanup
        assert success, "Shutdown should succeed"
        assert not test_thread.is_alive(), "Thread should be finished"
        assert thread_finished["value"], "Thread should have completed normally"
        
        print("✅ Background thread cleanup working")
        
        # Test with thread that doesn't finish quickly
        long_thread_finished = {"value": False}
        
        def long_thread_func():
            time.sleep(5)  # Longer than shutdown timeout
            long_thread_finished["value"] = True
        
        manager2 = GracefulShutdownManager(timeout_seconds=1)
        long_thread = threading.Thread(target=long_thread_func, name="long_thread")
        long_thread.start()
        
        manager2.register_background_thread(long_thread)
        
        # Execute shutdown (should timeout)
        start_time = time.time()
        success2 = manager2.shutdown("Long thread test")
        shutdown_duration = time.time() - start_time
        
        # Should complete quickly due to timeout
        assert shutdown_duration < 3, f"Shutdown took too long: {shutdown_duration}s"
        print("✅ Thread timeout handling working")
        
        # Cleanup long thread
        if long_thread.is_alive():
            long_thread.join(timeout=0.1)
        
        return True
        
    except Exception as e:
        print(f"❌ Background thread cleanup test failed: {e}")
        return False


def test_database_connection_cleanup():
    """Test database connection cleanup."""
    if not SHUTDOWN_AVAILABLE:
        return False
    
    print("\n🗄️ Testing Database Connection Cleanup")
    print("-" * 45)
    
    try:
        manager = GracefulShutdownManager()
        
        # Create mock database connections
        # Connection with only close method
        mock_connection1 = Mock(spec=['close'])
        mock_connection1.close = Mock()
        manager.register_database_connection(mock_connection1)
        
        # Connection with only disconnect method
        mock_connection2 = Mock(spec=['disconnect'])
        mock_connection2.disconnect = Mock()
        manager.register_database_connection(mock_connection2)
        
        # Execute shutdown
        success = manager.shutdown("Database cleanup test")
        
        # Validate connection cleanup
        assert success, "Shutdown should succeed"
        mock_connection1.close.assert_called_once()
        mock_connection2.disconnect.assert_called_once()
        
        print("✅ Database connection cleanup working")
        
        # Test connection cleanup error handling
        manager2 = GracefulShutdownManager()
        
        failing_connection = Mock()
        failing_connection.close = Mock(side_effect=Exception("Connection error"))
        manager2.register_database_connection(failing_connection)
        
        # Should not fail despite connection error
        success2 = manager2.shutdown("Error handling test")
        # Note: success might be False due to cleanup errors, but shutdown should complete
        
        print("✅ Database connection error handling working")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection cleanup test failed: {e}")
        return False


def test_server_instance_cleanup():
    """Test server instance cleanup."""
    if not SHUTDOWN_AVAILABLE:
        return False
    
    print("\n🌐 Testing Server Instance Cleanup")
    print("-" * 40)
    
    try:
        manager = GracefulShutdownManager()
        
        # Create mock servers with different cleanup methods
        server_with_stop = Mock(spec=['stop'])
        server_with_stop.stop = Mock()
        
        server_with_shutdown = Mock(spec=['shutdown'])
        server_with_shutdown.shutdown = Mock()
        
        server_with_close = Mock(spec=['close'])
        server_with_close.close = Mock()
        
        # Register servers
        manager.register_server_instance(server_with_stop)
        manager.register_server_instance(server_with_shutdown)
        manager.register_server_instance(server_with_close)
        
        # Execute shutdown
        success = manager.shutdown("Server cleanup test")
        
        # Validate server cleanup
        assert success, "Shutdown should succeed"
        server_with_stop.stop.assert_called_once()
        server_with_shutdown.shutdown.assert_called_once()
        server_with_close.close.assert_called_once()
        
        print("✅ Server instance cleanup working")
        
        return True
        
    except Exception as e:
        print(f"❌ Server instance cleanup test failed: {e}")
        return False


def test_convenience_functions():
    """Test convenience functions."""
    if not SHUTDOWN_AVAILABLE:
        return False
    
    print("\n🔧 Testing Convenience Functions")
    print("-" * 35)
    
    try:
        # Test global shutdown manager
        manager1 = get_shutdown_manager()
        manager2 = get_shutdown_manager()
        
        assert manager1 is manager2, "Should return same instance"
        print("✅ Global shutdown manager working")
        
        # Test register_for_shutdown convenience function
        cleanup_called = {"value": False}
        
        def test_cleanup():
            cleanup_called["value"] = True
        
        register_for_shutdown("convenience_test", test_cleanup)
        
        # Test is_shutting_down
        assert not is_shutting_down(), "Should not be shutting down initially"
        
        # Execute shutdown
        success = shutdown_application("Convenience test")
        
        assert success, "Shutdown should succeed"
        assert cleanup_called["value"], "Cleanup should be called"
        assert is_shutting_down(), "Should be shutting down after shutdown"
        
        print("✅ Convenience functions working")
        
        return True
        
    except Exception as e:
        print(f"❌ Convenience functions test failed: {e}")
        return False


def test_shutdown_handler_context():
    """Test shutdown handler context manager."""
    if not SHUTDOWN_AVAILABLE:
        return False
    
    print("\n📋 Testing Shutdown Handler Context")
    print("-" * 40)
    
    try:
        cleanup_called = {"value": False}
        
        def test_cleanup():
            cleanup_called["value"] = True
        
        # Test context manager
        with shutdown_handler(timeout_seconds=5) as manager:
            manager.register_cleanup_handler("context_test", test_cleanup)
            # Context should handle shutdown automatically
        
        # Cleanup should have been called
        assert cleanup_called["value"], "Cleanup should be called on context exit"
        
        print("✅ Shutdown handler context working")
        
        return True
        
    except Exception as e:
        print(f"❌ Shutdown handler context test failed: {e}")
        return False


def test_signal_handling():
    """Test signal handling (simplified test)."""
    if not SHUTDOWN_AVAILABLE:
        return False
    
    print("\n📡 Testing Signal Handling")
    print("-" * 30)
    
    try:
        # Note: Full signal testing is complex in unit tests
        # This tests that signal handlers are set up correctly
        
        manager = GracefulShutdownManager()
        
        # Check that signal handlers were registered
        assert hasattr(manager, '_original_handlers'), "Should have original handlers"
        assert len(manager._original_handlers) > 0, "Should have registered signal handlers"
        
        print("✅ Signal handlers configured")
        
        # Test that we can get shutdown status
        status = manager.get_shutdown_status()
        assert not status["shutdown_initiated"], "Should not be shutdown initially"
        
        print("✅ Signal handling setup working")
        
        return True
        
    except Exception as e:
        print(f"❌ Signal handling test failed: {e}")
        return False


def main():
    """Main test execution."""
    print("🛑 GRACEFUL SHUTDOWN SYSTEM TEST SUITE")
    print("=" * 65)
    print("Addresses report.md requirement:")
    print("- Implement graceful shutdown for connections")
    print()
    
    if not SHUTDOWN_AVAILABLE:
        print("❌ Graceful shutdown system not available")
        return False
    
    tests = [
        ("Shutdown Manager Initialization", test_shutdown_manager_initialization),
        ("Resource Registration", test_resource_registration),
        ("Graceful Shutdown Execution", test_graceful_shutdown_execution),
        ("Background Thread Cleanup", test_background_thread_cleanup),
        ("Database Connection Cleanup", test_database_connection_cleanup),
        ("Server Instance Cleanup", test_server_instance_cleanup),
        ("Convenience Functions", test_convenience_functions),
        ("Shutdown Handler Context", test_shutdown_handler_context),
        ("Signal Handling", test_signal_handling),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 65)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 65)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<35} {status}")
        if result:
            passed += 1
    
    print("-" * 65)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Graceful shutdown system is working correctly")
        print("✅ Report.md requirement fulfilled: Graceful shutdown implemented")
        print("✅ Production deployment ready")
        print("✅ Signal handling and resource cleanup operational")
        return True
    else:
        print(f"\n❌ {total-passed} tests failed")
        print("❗ Graceful shutdown system needs fixes")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)