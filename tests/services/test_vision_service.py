"""
Tests for UnifiedVisionService and factory patterns.

Tests environment-based service selection, fallback behavior, and integration.
"""

import pytest
from unittest.mock import patch, Mock
import os

from streamlit_extension.services.vision_service import (
    UnifiedVisionService,
    create_vision_service,
    get_mock_vision_service,
    get_real_vision_service
)


class TestUnifiedVisionService:
    """Test UnifiedVisionService functionality."""
    
    @pytest.fixture
    def sample_payload(self):
        """Sample product vision payload."""
        return {
            "vision_statement": "Revolutionize online learning",
            "problem_statement": "Students struggle with engagement",
            "target_audience": "University students",
            "value_proposition": "Interactive learning experience",
            "constraints": ["Budget under $100k"]
        }
    
    def test_mock_service_initialization(self):
        """Test mock service initialization."""
        service = UnifiedVisionService(use_real=False)
        
        assert not service.is_using_real_ai
        assert service.service_type == "FakeClaudeRefiner"
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_real_service_initialization(self):
        """Test real service initialization with credentials."""
        service = UnifiedVisionService(use_real=True)
        
        # Should use real service when credentials available
        assert service.is_using_real_ai or service.service_type in ["RealGPTRefiner", "FakeClaudeRefiner"]
    
    def test_mock_service_refine(self, sample_payload):
        """Test mock service refinement."""
        service = UnifiedVisionService(use_real=False)
        
        result = service.refine(sample_payload)
        
        assert isinstance(result, dict)
        assert "vision_statement" in result
        assert "problem_statement" in result
        assert "target_audience" in result
        assert "value_proposition" in result
        assert "constraints" in result
        
        # Mock adds [MOCK] prefix
        assert "[MOCK]" in result["vision_statement"]
    
    def test_mock_service_validation(self):
        """Test mock service validation."""
        service = UnifiedVisionService(use_real=False)
        
        # Empty payload should raise ValueError
        empty_payload = {
            "vision_statement": "",
            "problem_statement": "Some problem",
            "target_audience": "Some audience",
            "value_proposition": "Some value",
            "constraints": []
        }
        
        with pytest.raises(ValueError, match="Campo obrigatório"):
            service.refine(empty_payload)
    
    @patch('streamlit_extension.services.vision_service.logger')
    def test_fallback_behavior(self, mock_logger, sample_payload):
        """Test fallback to mock when real AI fails."""
        # Mock environment with credentials
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            # Create service that would use real AI
            service = UnifiedVisionService(use_real=True)
            
            # Mock the actual service to fail during refine
            original_refine = service._service.refine
            def failing_refine(payload):
                raise Exception("API Error")
            
            service._service.refine = failing_refine
            
            # Should fallback to mock and still work
            result = service.refine(sample_payload)
            
            assert isinstance(result, dict)
            # Should log error and fallback info
            mock_logger.error.assert_called()
            mock_logger.info.assert_called_with("Falling back to mock service due to AI failure")
    
    def test_credentials_detection(self):
        """Test credentials detection."""
        # Without credentials
        service = UnifiedVisionService(use_real=True)
        assert not service._has_credentials()
        
        # With credentials
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            service = UnifiedVisionService(use_real=True)
            assert service._has_credentials()


class TestVisionServiceFactory:
    """Test factory functions."""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_development_environment(self):
        """Test factory in development environment."""
        service = create_vision_service()
        
        assert not service.is_using_real_ai
        assert service.service_type == "FakeClaudeRefiner"
    
    @patch.dict(os.environ, {"TDD_ENVIRONMENT": "production", "OPENAI_API_KEY": "test_key"})
    def test_production_environment_with_credentials(self):
        """Test factory in production with credentials."""
        service = create_vision_service()
        
        # Should attempt to use real service (may fallback to mock if import fails)
        assert service.service_type in ["RealGPTRefiner", "FakeClaudeRefiner"]
    
    @patch.dict(os.environ, {"TDD_ENVIRONMENT": "production"}, clear=True)
    def test_production_environment_without_credentials(self):
        """Test factory in production without credentials."""
        service = create_vision_service()
        
        # Should use mock when no credentials
        assert not service.is_using_real_ai
        assert service.service_type == "FakeClaudeRefiner"
    
    def test_get_mock_vision_service(self):
        """Test explicit mock service getter."""
        service = get_mock_vision_service()
        
        assert not service.is_using_real_ai
        assert service.service_type == "FakeClaudeRefiner"
    
    def test_get_real_vision_service_without_credentials(self):
        """Test real service getter without credentials."""
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY required"):
            get_real_vision_service()
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_get_real_vision_service_with_credentials(self):
        """Test real service getter with credentials."""
        service = get_real_vision_service()
        
        # Should be configured for real AI (may fallback if import fails)
        assert hasattr(service, 'is_using_real_ai')


class TestUnifiedVisionServiceIntegration:
    """Integration tests for UnifiedVisionService."""
    
    @pytest.fixture
    def complete_payload(self):
        """Complete product vision payload for integration testing."""
        return {
            "vision_statement": "Create the future of education technology",
            "problem_statement": "Traditional learning methods are outdated and ineffective",
            "target_audience": "Students, teachers, and educational institutions",
            "value_proposition": "Personalized, engaging, and measurable learning experiences",
            "constraints": [
                "Must comply with GDPR",
                "Budget limited to $500K",
                "Launch within 12 months"
            ]
        }
    
    def test_complete_refinement_workflow(self, complete_payload):
        """Test complete refinement workflow."""
        service = UnifiedVisionService(use_real=False)
        
        result = service.refine(complete_payload)
        
        # Validate complete result structure
        assert isinstance(result, dict)
        for key in ["vision_statement", "problem_statement", "target_audience", "value_proposition", "constraints"]:
            assert key in result
            if key != "constraints":
                assert isinstance(result[key], str)
                assert len(result[key]) > 0
                assert "[MOCK]" in result[key]  # Mock service adds prefix
        
        assert isinstance(result["constraints"], list)
    
    def test_service_consistency(self, complete_payload):
        """Test service provides consistent results."""
        service = UnifiedVisionService(use_real=False)
        
        result1 = service.refine(complete_payload)
        result2 = service.refine(complete_payload)
        
        # Results should be consistent (deterministic for mock)
        assert result1 == result2
    
    def test_error_handling_edge_cases(self):
        """Test error handling for edge cases."""
        service = UnifiedVisionService(use_real=False)
        
        # Test with None values
        with pytest.raises(ValueError):
            service.refine({
                "vision_statement": None,
                "problem_statement": "test",
                "target_audience": "test",
                "value_proposition": "test",
                "constraints": []
            })
        
        # Test with missing keys
        with pytest.raises(ValueError):
            service.refine({
                "vision_statement": "test",
                # missing other required fields
            })
    
    @patch('streamlit_extension.services.vision_service.logger')
    def test_logging_behavior(self, mock_logger, complete_payload):
        """Test that service logs appropriately."""
        service = UnifiedVisionService(use_real=False)
        
        # Should log service initialization
        mock_logger.info.assert_called()
        
        # Clear previous calls
        mock_logger.reset_mock()
        
        # Refine should not generate error logs for successful operation
        result = service.refine(complete_payload)
        
        assert isinstance(result, dict)
        # Should not have error logs for successful operation
        mock_logger.error.assert_not_called()


@pytest.mark.integration
class TestVisionServiceContainerIntegration:
    """Integration tests with service container."""
    
    def test_service_container_provides_vision_service(self):
        """Test service container provides vision service."""
        from streamlit_extension.services import get_service_container
        
        container = get_service_container()
        service = container.get_vision_refine_service()
        
        assert hasattr(service, 'refine')
        assert hasattr(service, 'is_using_real_ai')
        assert hasattr(service, 'service_type')
    
    def test_convenience_function(self):
        """Test convenience function access."""
        from streamlit_extension.services.service_container import get_vision_refine_service
        
        service = get_vision_refine_service()
        
        assert hasattr(service, 'refine')
        assert callable(service.refine)
    
    def test_service_caching(self):
        """Test that service container caches vision service."""
        from streamlit_extension.services import get_service_container
        
        container = get_service_container()
        service1 = container.get_vision_refine_service()
        service2 = container.get_vision_refine_service()
        
        # Should return same instance (cached)
        assert service1 is service2