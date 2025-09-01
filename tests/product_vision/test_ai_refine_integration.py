"""
Integration tests for AI refinement in product vision step.

Tests the integration between wizard UI and unified vision service.
"""

import pytest
from unittest.mock import patch, Mock
import os

from streamlit_extension.pages.projetos.steps.product_vision_step.ai_refine import (
    get_vision_service,
    VisionRefineService,
    UnifiedVisionRefineAdapter
)


class TestAIRefineIntegration:
    """Test AI refinement integration with wizard."""
    
    @pytest.fixture
    def wizard_payload(self):
        """Product vision payload as used in wizard."""
        return {
            "vision_statement": "Build the next generation learning platform",
            "problem_statement": "Current e-learning platforms lack personalization",
            "target_audience": "Online learners and educators",
            "value_proposition": "AI-powered personalized learning paths",
            "constraints": ["GDPR compliance required", "Mobile-first design"]
        }
    
    def test_get_vision_service_function(self):
        """Test get_vision_service function."""
        service = get_vision_service()
        
        assert hasattr(service, 'refine')
        assert hasattr(service, 'is_using_real_ai')
        assert hasattr(service, 'service_type')
        
        # Should default to mock in test environment
        assert service.service_type in ["FakeClaudeRefiner", "RealGPTRefiner"]
    
    def test_vision_refine_service_callable(self, wizard_payload):
        """Test VisionRefineService callable interface."""
        # VisionRefineService is now a function that returns a service
        service = VisionRefineService()
        
        result = service.refine(wizard_payload)
        
        assert isinstance(result, dict)
        assert all(key in result for key in wizard_payload.keys())
    
    def test_unified_vision_refine_adapter(self, wizard_payload):
        """Test UnifiedVisionRefineAdapter class."""
        adapter = UnifiedVisionRefineAdapter()
        
        # Test properties
        assert isinstance(adapter.is_using_real_ai, bool)
        assert isinstance(adapter.service_type, str)
        
        # Test refinement
        result = adapter.refine(wizard_payload)
        
        assert isinstance(result, dict)
        for key in ["vision_statement", "problem_statement", "target_audience", "value_proposition", "constraints"]:
            assert key in result
    
    @patch('streamlit_extension.services.get_service_container')
    def test_service_container_integration(self, mock_container, wizard_payload):
        """Test integration with service container."""
        # Mock the service container
        mock_service = Mock()
        mock_service.refine.return_value = wizard_payload
        mock_service.is_using_real_ai = False
        mock_service.service_type = "MockService"
        
        mock_container.return_value.get_vision_refine_service.return_value = mock_service
        
        # Test integration
        service = get_vision_service()
        result = service.refine(wizard_payload)
        
        assert result == wizard_payload
        mock_container.assert_called_once()
    
    @patch('streamlit_extension.services.get_service_container')
    def test_service_container_failure_fallback(self, mock_container, wizard_payload):
        """Test fallback when service container fails."""
        # Make service container fail
        mock_container.side_effect = Exception("Container error")
        
        # Should fallback to MockVisionRefineService
        service = get_vision_service()
        result = service.refine(wizard_payload)
        
        # Should still work with fallback
        assert isinstance(result, dict)
        # MockVisionRefineService returns mock-refined data
        assert "[MOCK]" in result["vision_statement"]
    
    @patch.dict(os.environ, {"TDD_ENVIRONMENT": "development"})
    def test_development_environment_behavior(self, wizard_payload):
        """Test behavior in development environment."""
        service = get_vision_service()
        result = service.refine(wizard_payload)
        
        assert isinstance(result, dict)
        # In development, should use mock service
        assert service.service_type == "FakeClaudeRefiner"
    
    @patch.dict(os.environ, {"TDD_ENVIRONMENT": "production", "OPENAI_API_KEY": "test_key"})
    @patch('src.ia.product_vision_refiner.RealGPTRefiner')
    def test_production_environment_behavior(self, mock_real_refiner, wizard_payload):
        """Test behavior in production environment with credentials."""
        # Mock successful real service
        mock_dto = Mock()
        mock_dto.dict.return_value = wizard_payload
        mock_real_refiner.return_value.refine.return_value = mock_dto
        
        service = get_vision_service()
        
        # Should attempt to use real service in production
        assert service.is_using_real_ai or service.service_type == "RealGPTRefiner"


class TestBackwardCompatibility:
    """Test backward compatibility with existing wizard code."""
    
    @pytest.fixture
    def legacy_payload(self):
        """Legacy payload format for compatibility testing."""
        return {
            "vision_statement": "Legacy vision",
            "problem_statement": "Legacy problem", 
            "target_audience": "Legacy audience",
            "value_proposition": "Legacy value",
            "constraints": ["Legacy constraint"]
        }
    
    def test_mock_refiner_still_available(self):
        """Test that MockVisionRefineService is still available."""
        from streamlit_extension.pages.projetos.steps.product_vision_step.ai_refine import MockVisionRefineService
        
        service = MockVisionRefineService()
        assert hasattr(service, 'refine')
    
    def test_single_field_mock_refiner_still_available(self):
        """Test that SingleFieldMockRefiner is still available."""
        from streamlit_extension.pages.projetos.steps.product_vision_step.ai_refine import SingleFieldMockRefiner
        
        refiner = SingleFieldMockRefiner()
        assert hasattr(refiner, 'refine_field')
    
    def test_legacy_interface_compatibility(self, legacy_payload):
        """Test that legacy interface still works."""
        from streamlit_extension.pages.projetos.steps.product_vision_step.ai_refine import MockVisionRefineService
        
        # Legacy direct instantiation
        legacy_service = MockVisionRefineService()
        result = legacy_service.refine(legacy_payload)
        
        assert isinstance(result, dict)
        assert all(key in result for key in legacy_payload.keys())
    
    def test_new_interface_compatibility(self, legacy_payload):
        """Test that new interface works with legacy payload."""
        adapter = UnifiedVisionRefineAdapter()
        result = adapter.refine(legacy_payload)
        
        assert isinstance(result, dict)
        assert all(key in result for key in legacy_payload.keys())


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_payload_handling(self):
        """Test handling of invalid payloads."""
        service = get_vision_service()
        
        # Empty payload
        with pytest.raises(ValueError):
            service.refine({})
        
        # Payload with empty required fields
        with pytest.raises(ValueError):
            service.refine({
                "vision_statement": "",
                "problem_statement": "test",
                "target_audience": "test",
                "value_proposition": "test"
            })
    
    def test_missing_fields_handling(self):
        """Test handling of missing required fields."""
        service = get_vision_service()
        
        with pytest.raises(ValueError):
            service.refine({
                "vision_statement": "test",
                # missing other required fields
            })
    
    @patch('streamlit_extension.pages.projetos.steps.product_vision_step.ai_refine.logger')
    def test_error_logging(self, mock_logger):
        """Test that errors are properly logged."""
        service = get_vision_service()
        
        try:
            service.refine({})
        except ValueError:
            pass  # Expected
        
        # Should have logged the service creation
        mock_logger.info.assert_called()
    
    @patch('streamlit_extension.services.get_service_container')
    def test_graceful_degradation(self, mock_container):
        """Test graceful degradation when service container fails."""
        # Make container fail
        mock_container.side_effect = Exception("Service unavailable")
        
        # Should still work with fallback
        service = get_vision_service()
        
        # Should be MockVisionRefineService as fallback
        assert callable(service.refine)
        
        # Test with valid payload
        payload = {
            "vision_statement": "test",
            "problem_statement": "test",
            "target_audience": "test", 
            "value_proposition": "test",
            "constraints": []
        }
        
        result = service.refine(payload)
        assert isinstance(result, dict)


@pytest.mark.integration  
class TestWizardIntegration:
    """Integration tests with actual wizard components."""
    
    @pytest.fixture
    def wizard_session_state(self):
        """Mock wizard session state."""
        return {
            "pv": {
                "vision_statement": "Transform education through technology",
                "problem_statement": "Students are disengaged with traditional learning",
                "target_audience": "High school and university students",
                "value_proposition": "Gamified learning that increases engagement by 300%",
                "constraints": ["Budget: $200K", "Timeline: 6 months", "Team: 5 developers"]
            }
        }
    
    def test_wizard_refinement_workflow(self, wizard_session_state):
        """Test complete refinement workflow as used in wizard."""
        # Simulate wizard usage
        payload = wizard_session_state["pv"]
        
        # Get service as wizard would
        service = get_vision_service()
        
        # Refine as wizard would
        refined_data = service.refine(payload)
        
        # Validate result structure
        assert isinstance(refined_data, dict)
        assert all(key in refined_data for key in payload.keys())
        
        # Refined data should be different from original (mock adds [MOCK] prefix)
        if not service.is_using_real_ai:
            assert refined_data["vision_statement"] != payload["vision_statement"]
            assert "[MOCK]" in refined_data["vision_statement"]
    
    def test_field_specific_refinement(self):
        """Test field-specific refinement as used in steps mode."""
        from streamlit_extension.pages.projetos.steps.product_vision_step.ai_refine import SingleFieldMockRefiner
        
        refiner = SingleFieldMockRefiner()
        
        field_value = "Basic vision statement"
        context = {
            "vision_statement": field_value,
            "problem_statement": "Context problem",
            "target_audience": "Context audience",
            "value_proposition": "Context value",
            "constraints": []
        }
        
        refined_value = refiner.refine_field("vision_statement", field_value, context)
        
        assert isinstance(refined_value, str)
        assert refined_value != field_value  # Should be refined
    
    def test_service_switching_simulation(self, wizard_session_state):
        """Test simulation of switching between environments."""
        payload = wizard_session_state["pv"]
        
        # Test mock service
        mock_service = get_vision_service()
        mock_result = mock_service.refine(payload)
        
        # Mock should add [MOCK] prefix
        if not mock_service.is_using_real_ai:
            assert "[MOCK]" in mock_result["vision_statement"]
        
        # Results should be valid regardless of service type
        assert isinstance(mock_result, dict)
        assert all(key in mock_result for key in payload.keys())