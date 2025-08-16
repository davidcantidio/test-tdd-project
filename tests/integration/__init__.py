"""
🧪 Integration Tests Package

Comprehensive integration tests for the TDD Framework Streamlit Extension.

These tests verify that components work correctly together and integrate
properly with external systems and dependencies across the entire system stack.

Test Coverage:
- End-to-end user workflows (E2E)
- Cross-system integration (Security, Auth, Rate Limiting)
- Performance under realistic load conditions
- Cache system integration and performance
- UI component rendering and interaction  
- Theme system functionality and persistence
- Database transaction safety and concurrency
- Error handling and correlation tracking
- Resource usage and memory efficiency

Test Suites:
    test_e2e_workflows.py - Complete user workflow testing
    test_cross_system.py - Integration between security/auth/monitoring systems
    test_performance_integration.py - System performance under load
    test_cache_system.py - Cache system integration and performance
    test_ui_components.py - UI component integration
    test_theme_system.py - Theme system integration

Running Tests:
    # Run comprehensive integration test suite
    python tests/integration/test_runner.py --mode full
    
    # Run only high-priority tests (quick)
    python tests/integration/test_runner.py --mode quick
    
    # Run essential tests (high + medium priority)
    python tests/integration/test_runner.py --mode essential
    
    # Run specific test module
    pytest tests/integration/test_e2e_workflows.py -v
    
    # Run with performance monitoring
    pytest tests/integration/test_performance_integration.py --tb=short
    
    # Run with coverage
    pytest tests/integration/ --cov=streamlit_extension --cov-report=html
    
    # Run only specific categories
    pytest tests/integration/ -m "e2e or performance"
    
    # Run excluding slow tests
    pytest tests/integration/ -m "not slow"

Test Markers:
    @pytest.mark.integration - Integration test
    @pytest.mark.e2e - End-to-end workflow test
    @pytest.mark.cross_system - Cross-system integration test
    @pytest.mark.performance - Performance test
    @pytest.mark.cache - Cache system test
    @pytest.mark.ui - UI component test  
    @pytest.mark.theme - Theme system test
    @pytest.mark.slow - Slow running test (>30s)
    @pytest.mark.load_test - Load testing (high resource usage)
    @pytest.mark.security - Security integration test
    @pytest.mark.database - Database integration test
    @pytest.mark.requires_streamlit - Requires Streamlit environment

Test Priorities:
    HIGH: E2E workflows, Cross-system integration
    MEDIUM: Performance, Cache system
    LOW: UI components, Theme system

Performance Targets:
    - Response time: <3s for complex operations
    - Throughput: >50 req/s for normal operations  
    - Memory usage: <1GB for 100 concurrent users
    - Success rate: >95% under normal load
    - Error rate: <1% under normal conditions
"""

# Test configuration
TEST_CONFIG = {
    # Cache testing
    "cache_test_ttl": 1,  # Short TTL for testing
    "cache_test_max_size": 10,  # Small cache for testing
    
    # UI testing
    "theme_test_timeout": 5,  # Theme operation timeout
    "ui_render_timeout": 2,  # UI rendering timeout
    
    # Performance testing
    "performance_test_duration": 60,  # Performance test duration (seconds)
    "load_test_max_workers": 20,  # Maximum concurrent workers for load testing
    "memory_limit_mb": 500,  # Memory limit for performance tests
    
    # E2E testing
    "e2e_test_timeout": 300,  # E2E test timeout (seconds)
    "concurrent_users": 10,  # Number of concurrent users to simulate
    
    # Cross-system testing
    "security_test_iterations": 100,  # Number of security test iterations
    "rate_limit_test_requests": 200,  # Number of requests for rate limit testing
    
    # Database testing
    "db_test_records": 1000,  # Number of test records to create
    "transaction_test_threads": 5,  # Number of concurrent transaction threads
}

# Test utilities and frameworks that can be imported
from .test_e2e_workflows import IntegrationTestFramework
from .test_cross_system import CrossSystemTestFramework
from .test_performance_integration import PerformanceTestFramework

__all__ = [
    "TEST_CONFIG",
    "IntegrationTestFramework", 
    "CrossSystemTestFramework",
    "PerformanceTestFramework"
]