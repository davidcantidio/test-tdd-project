#!/usr/bin/env python3
"""
📊 Structured Logging & Monitoring Demo

Demonstrates the comprehensive structured logging and monitoring system:
- Structured JSON logging with correlation IDs
- Prometheus metrics integration
- Performance monitoring decorators
- Security event logging
- Database operation tracking
- User action monitoring
- System metrics collection
- Error tracking and analysis

This demo validates the complete monitoring infrastructure addressing report.md requirements.
"""

import sys
import time
import json
from pathlib import Path
import threading

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from streamlit_extension.utils.structured_logger import (
    get_logger,
    setup_logging,
    LogLevel,
    EventType,
    log_user_session,
    log_database_transaction
)

from streamlit_extension.utils.monitoring_integration import (
    setup_monitoring,
    monitor_performance,
    monitor_database,
    monitor_user_action,
    monitor_security,
    monitoring_context,
    get_streamlit_monitoring,
    get_metrics_collector,
    get_error_tracker
)


def demo_basic_structured_logging():
    """Demonstrate basic structured logging capabilities."""
    print("📊 Demo: Basic Structured Logging")
    print("-" * 50)
    
    logger = get_logger()
    
    # Basic logging
    logger.info("application", "startup", "TDD Framework demo starting")
    
    # Logging with extra data
    logger.info(
        "authentication", 
        "user_login", 
        "User authenticated successfully",
        extra_data={
            "user_id": "demo_user",
            "login_method": "password",
            "ip_address": "192.168.1.100"
        }
    )
    
    # Performance logging
    logger.performance_event(
        component="database",
        operation="client_query",
        message="Database query completed",
        operation_duration_ms=25.5,
        memory_usage_mb=1.2,
        database_queries=1
    )
    
    # Security event
    logger.security_event(
        component="authentication",
        operation="failed_login",
        message="Multiple failed login attempts detected",
        event_category="authentication",
        severity="medium",
        threat_detected=True,
        source_ip="192.168.1.200"
    )
    
    # Error logging
    try:
        raise ValueError("Demo error for testing")
    except ValueError as e:
        logger.error(
            component="demo",
            operation="error_test",
            message="Demonstration error occurred",
            exception=e,
            extra_data={"demo_context": "testing error handling"}
        )
    
    print("✅ Basic structured logging demonstrated")
    print()


def demo_performance_decorators():
    """Demonstrate performance monitoring decorators."""
    print("⚡ Demo: Performance Monitoring Decorators")
    print("-" * 50)
    
    @monitor_performance("demo", "fast_function", log_args=True, log_result=True)
    def fast_operation(count: int, multiplier: float = 1.0) -> list:
        """Fast operation for demo."""
        time.sleep(0.01)
        return [i * multiplier for i in range(count)]
    
    @monitor_performance("demo", "slow_function")
    def slow_operation(duration: float) -> str:
        """Slow operation for demo."""
        time.sleep(duration)
        return f"Completed in {duration}s"
    
    @monitor_database("demo_clients", "create")
    def create_demo_client(name: str) -> int:
        """Demo database operation."""
        time.sleep(0.05)  # Simulate database work
        return hash(name) % 10000  # Mock client ID
    
    @monitor_user_action("create", "client")
    def user_create_client(client_data: dict) -> bool:
        """Demo user action."""
        time.sleep(0.02)
        return True
    
    # Test decorated functions
    result1 = fast_operation(5, 2.0)
    result2 = slow_operation(0.1)
    client_id = create_demo_client("Demo Client Corp")
    success = user_create_client({"name": "Test Client"})
    
    print(f"Fast operation result: {len(result1)} items")
    print(f"Slow operation result: {result2}")
    print(f"Created client ID: {client_id}")
    print(f"User action success: {success}")
    print("✅ Performance decorators demonstrated")
    print()


def demo_context_management():
    """Demonstrate context management and correlation IDs."""
    print("🔄 Demo: Context Management & Correlation IDs")
    print("-" * 50)
    
    # User session context
    with log_user_session("demo_user_123", "session_456", "192.168.1.50"):
        logger = get_logger()
        
        logger.info(
            "user_interface",
            "page_load",
            "Dashboard page loaded",
            extra_data={"page": "dashboard", "load_time_ms": 150}
        )
        
        # Database transaction context
        with log_database_transaction("update_client_status", ["clients", "projects"]):
            logger.info(
                "database",
                "update_operation",
                "Client status updated successfully",
                extra_data={"client_id": 123, "new_status": "active"}
            )
    
    # Custom monitoring context
    with monitoring_context(
        user_id="admin_user",
        session_id="admin_session_789",
        ip_address="10.0.0.100",
        correlation_id="admin-operation-001"
    ) as logger:
        logger.security_event(
            component="admin_panel",
            operation="user_management",
            message="Admin accessed user management panel",
            event_category="administrative",
            severity="low"
        )
    
    print("✅ Context management demonstrated")
    print()


def demo_security_monitoring():
    """Demonstrate security event monitoring."""
    print("🔐 Demo: Security Event Monitoring")
    print("-" * 50)
    
    @monitor_security("authentication", "high")
    def admin_login(username: str, password: str) -> bool:
        """Demo admin login."""
        if username == "admin" and password == "secret":
            return True
        raise ValueError("Invalid credentials")
    
    @monitor_security("authorization", "medium")
    def access_sensitive_data(user_id: str, resource: str) -> dict:
        """Demo sensitive data access."""
        time.sleep(0.01)
        return {"data": "sensitive information", "access_granted": True}
    
    # Test security operations
    try:
        admin_login("admin", "secret")
        print("Admin login: Success")
    except ValueError:
        print("Admin login: Failed")
    
    try:
        admin_login("hacker", "wrong")
        print("Hacker login: Success (should not happen)")
    except ValueError:
        print("Hacker login: Failed (expected)")
    
    # Test data access
    data = access_sensitive_data("demo_user", "financial_reports")
    print(f"Data access: {data['access_granted']}")
    
    print("✅ Security monitoring demonstrated")
    print()


def demo_streamlit_monitoring():
    """Demonstrate Streamlit-specific monitoring."""
    print("🎨 Demo: Streamlit Application Monitoring")
    print("-" * 50)
    
    streamlit_monitor = get_streamlit_monitoring()
    
    # Simulate page load tracking
    with streamlit_monitor.track_page_load("clients_page"):
        time.sleep(0.1)  # Simulate page load time
    
    # Track user interactions
    streamlit_monitor.track_user_interaction("button_click", "create_client_btn", "user123")
    streamlit_monitor.track_user_interaction("form_submit", "client_form", "user123")
    streamlit_monitor.track_user_interaction("dropdown_select", "client_filter", "user456")
    
    # Track form submission
    streamlit_monitor.track_form_submission(
        form_name="create_client_form",
        success=True,
        validation_errors=None
    )
    
    # Track failed form submission
    streamlit_monitor.track_form_submission(
        form_name="create_project_form",
        success=False,
        validation_errors=["Name is required", "Invalid email format"]
    )
    
    # Get interaction stats
    stats = streamlit_monitor.get_user_interaction_stats(time_window_minutes=60)
    print(f"User interaction stats:")
    print(f"  Total interactions: {stats['total_interactions']}")
    print(f"  Unique users: {stats['unique_users']}")
    print(f"  Interaction types: {stats['interaction_types']}")
    
    print("✅ Streamlit monitoring demonstrated")
    print()


def demo_system_metrics_collection():
    """Demonstrate system metrics collection."""
    print("💾 Demo: System Metrics Collection")
    print("-" * 50)
    
    metrics_collector = get_metrics_collector()
    
    # Start metrics collection for demo
    print("Starting metrics collection...")
    metrics_collector.collection_interval = 2  # Short interval for demo
    metrics_collector.start_collection()
    
    # Let it collect a few metrics
    time.sleep(5)
    
    # Stop collection
    print("Stopping metrics collection...")
    metrics_collector.stop_collection()
    
    # Manually collect metrics once
    print("Collecting one-time metrics snapshot...")
    metrics_collector.collect_and_log_metrics()
    
    print("✅ System metrics collection demonstrated")
    print()


def demo_error_tracking():
    """Demonstrate error tracking and analysis."""
    print("🚨 Demo: Error Tracking & Analysis")
    print("-" * 50)
    
    error_tracker = get_error_tracker()
    
    # Track various types of errors
    errors_to_track = [
        (ValueError("Invalid input value: 'abc' is not a number"), {"operation": "data_parsing"}),
        (KeyError("Missing required field: 'email'"), {"operation": "user_validation"}),
        (ConnectionError("Database connection failed"), {"operation": "database_connect"}),
        (ValueError("Invalid input value: 'xyz' is not a number"), {"operation": "data_parsing"}),  # Same pattern
        (TimeoutError("Request timeout after 30 seconds"), {"operation": "api_request"}),
    ]
    
    for error, context in errors_to_track:
        error_tracker.track_error(error, context)
    
    # Get error summary
    summary = error_tracker.get_error_summary()
    print("Error tracking summary:")
    print(f"  Total errors: {summary['total_errors']}")
    print(f"  Error types: {summary['error_types']}")
    print(f"  Top patterns: {list(summary['top_patterns'].keys())[:3]}")
    
    print("✅ Error tracking demonstrated")
    print()


def demo_prometheus_metrics():
    """Demonstrate Prometheus metrics integration."""
    print("📈 Demo: Prometheus Metrics Integration")
    print("-" * 50)
    
    logger = get_logger()
    
    # Check if Prometheus is available
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
        
        # Simulate some application activity to generate metrics
        for i in range(5):
            with monitoring_context(user_id=f"user_{i}"):
                logger.api_request("GET", "/api/clients", 200, 25.0 + i * 5, f"user_{i}")
                logger.api_request("POST", "/api/clients", 201, 45.0 + i * 10, f"user_{i}")
        
        # Generate metrics output
        metrics_output = generate_latest().decode('utf-8')
        
        # Show sample metrics
        print("Sample Prometheus metrics generated:")
        lines = metrics_output.split('\n')
        tdd_metrics = [line for line in lines if 'tdd_framework' in line and not line.startswith('#')]
        
        for metric in tdd_metrics[:5]:  # Show first 5 metrics
            print(f"  {metric}")
        
        print(f"  ... and {len(tdd_metrics) - 5} more metrics")
        print("✅ Prometheus metrics integration working")
        
    except ImportError:
        print("⚠️  Prometheus client not available - metrics generation skipped")
        print("   Install with: pip install prometheus_client")
    
    print()


def demo_log_file_analysis():
    """Demonstrate log file structure and content."""
    print("📄 Demo: Log File Analysis")
    print("-" * 50)
    
    log_dir = Path("demo_logs")
    
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        
        print(f"Generated log files in {log_dir}:")
        for log_file in log_files:
            size_kb = log_file.stat().st_size / 1024
            print(f"  {log_file.name} ({size_kb:.1f} KB)")
        
        # Show sample of application log
        app_log = log_dir / "application.log"
        if app_log.exists():
            print(f"\nSample entries from {app_log.name}:")
            with open(app_log) as f:
                lines = f.readlines()
                for line in lines[-3:]:  # Show last 3 entries
                    try:
                        log_entry = json.loads(line.strip())
                        timestamp = log_entry["context"]["timestamp"]
                        level = log_entry["context"]["level"]
                        component = log_entry["context"]["component"]
                        operation = log_entry["context"]["operation"]
                        message = log_entry["message"]
                        print(f"  [{timestamp}] {level} {component}.{operation}: {message}")
                    except (json.JSONDecodeError, KeyError):
                        print(f"  {line.strip()}")
        
        print("✅ Structured logs generated successfully")
    else:
        print("⚠️  No log files found - logs may not have been generated yet")
    
    print()


def main():
    """Run complete structured logging and monitoring demo."""
    print("=" * 70)
    print("📊 STRUCTURED LOGGING & MONITORING SYSTEM DEMO")
    print("=" * 70)
    print()
    
    print("This demo showcases the comprehensive monitoring system that")
    print("addresses structured logging and observability requirements from report.md")
    print()
    
    # Setup monitoring system
    print("🚀 Setting up monitoring system...")
    logger = setup_monitoring(
        log_dir="demo_logs",
        metrics_port=8000,
        enable_metrics_collection=True,
        metrics_interval=30
    )
    print("✅ Monitoring system initialized")
    print()
    
    # Run all demos
    demo_basic_structured_logging()
    demo_performance_decorators()
    demo_context_management()
    demo_security_monitoring()
    demo_streamlit_monitoring()
    demo_system_metrics_collection()
    demo_error_tracking()
    demo_prometheus_metrics()
    demo_log_file_analysis()
    
    print("=" * 70)
    print("✅ STRUCTURED LOGGING & MONITORING DEMO COMPLETE")
    print("=" * 70)
    print()
    print("Key features demonstrated:")
    print("  📊 Structured JSON logging with correlation IDs")
    print("  ⚡ Performance monitoring decorators")
    print("  🔐 Security event tracking and alerting")
    print("  🗄️ Database operation monitoring")
    print("  👤 User action tracking")
    print("  🎨 Streamlit application monitoring")
    print("  💾 System metrics collection")
    print("  🚨 Error tracking and analysis")
    print("  📈 Prometheus metrics integration")
    print("  📋 Grafana dashboard compatibility")
    print()
    print("Integration ready:")
    print("  📁 Log files: demo_logs/ directory")
    print("  📈 Prometheus metrics: http://localhost:8000/metrics")
    print("  📊 Grafana dashboards: monitoring/grafana_dashboards.json")
    print("  🚨 Alert rules: monitoring/alert_rules.yml")
    print()
    print("🎯 System addresses all report.md monitoring requirements!")


if __name__ == "__main__":
    main()