"""
🧪 Integration Tests Package

Integration tests for the TDD Framework Streamlit Extension.

These tests verify that components work correctly together and integrate
properly with external systems and dependencies.

Test Coverage:
- Cache system integration and performance
- UI component rendering and interaction  
- Theme system functionality and persistence
- Analytics export and reporting
- Configuration backup and restore
- Database integration and query optimization

Running Tests:
    # Run all integration tests
    pytest tests/integration/
    
    # Run specific test module
    pytest tests/integration/test_cache_system.py
    
    # Run with coverage
    pytest tests/integration/ --cov=streamlit_extension
    
    # Run only cache-related tests
    pytest tests/integration/ -m cache
    
    # Run excluding slow tests
    pytest tests/integration/ -m "not slow"

Test Markers:
    @pytest.mark.integration - Integration test
    @pytest.mark.cache - Cache system test
    @pytest.mark.ui - UI component test  
    @pytest.mark.theme - Theme system test
    @pytest.mark.slow - Slow running test
    @pytest.mark.requires_streamlit - Requires Streamlit
"""

# Test configuration
TEST_CONFIG = {
    "cache_test_ttl": 1,  # Short TTL for testing
    "cache_test_max_size": 10,  # Small cache for testing
    "theme_test_timeout": 5,  # Theme operation timeout
    "ui_render_timeout": 2,  # UI rendering timeout
}

# Test utilities that can be imported
__all__ = ["TEST_CONFIG"]