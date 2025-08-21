#!/usr/bin/env python3
"""
🧪 TESTS - API Endpoints

Test suite for TaskExecutionPlanner API endpoints.
Tests the Streamlit-integrated API functionality.

Test Categories:
- API endpoint validation
- Authentication and authorization
- Parameter validation
- Response format validation
- Error handling
- Rate limiting
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import modules under test
from streamlit_extension.endpoints.execution_api import (
    handle_api_request,
    handle_execution_planning,
    handle_epic_validation,
    handle_scoring_analysis,
    handle_execution_summary,
    handle_presets_list
)
from streamlit_extension.endpoints.api_middleware import (
    authenticate_api_request,
    validate_api_request,
    verify_api_key,
    generate_dev_api_key,
    create_api_error_response,
    create_api_success_response
)

class TestAPIEndpoints:
    """Test API endpoint functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.sample_epic_id = 1
        self.sample_query_params = {
            "epic_id": "1",
            "preset": "balanced"
        }
        self.sample_execution_plan = Mock()
        self.sample_execution_plan.epic_id = 1
        self.sample_execution_plan.execution_order = ["TASK_001", "TASK_002"]
        self.sample_execution_plan.task_scores = {"TASK_001": 8.5, "TASK_002": 7.2}
        self.sample_execution_plan.critical_path = ["TASK_001"]
        self.sample_execution_plan.execution_metrics = {"total_tasks": 2}
        self.sample_execution_plan.dag_validation = {"is_valid": True}
        self.sample_execution_plan.created_at = Mock()
        self.sample_execution_plan.created_at.isoformat.return_value = "2025-01-15T14:30:00Z"

    @patch('streamlit_extension.endpoints.execution_api.is_authenticated')
    @patch('streamlit_extension.endpoints.execution_api.check_rate_limit')
    def test_handle_api_request_authentication_required(self, mock_rate_limit, mock_auth):
        """Test API request with authentication required."""
        mock_auth.return_value = False
        mock_rate_limit.return_value = (True, None)
        
        result = handle_api_request("execution", self.sample_query_params)
        
        assert "error" in result
        assert result["code"] == "AUTH_REQUIRED"
        assert "Authentication required" in result["error"]

    @patch('streamlit_extension.endpoints.execution_api.is_authenticated')
    @patch('streamlit_extension.endpoints.execution_api.check_rate_limit')
    def test_handle_api_request_rate_limit_exceeded(self, mock_rate_limit, mock_auth):
        """Test API request with rate limit exceeded."""
        mock_auth.return_value = True
        mock_rate_limit.return_value = (False, "Too many requests")
        
        result = handle_api_request("execution", self.sample_query_params)
        
        assert "error" in result
        assert result["code"] == "RATE_LIMIT_EXCEEDED"
        assert "Too many requests" in result["error"]

    @patch('streamlit_extension.endpoints.execution_api.is_authenticated')
    @patch('streamlit_extension.endpoints.execution_api.check_rate_limit')
    def test_handle_api_request_invalid_endpoint(self, mock_rate_limit, mock_auth):
        """Test API request with invalid endpoint."""
        mock_auth.return_value = True
        mock_rate_limit.return_value = (True, None)
        
        result = handle_api_request("invalid_endpoint", self.sample_query_params)
        
        assert "error" in result
        assert result["code"] == "INVALID_ENDPOINT"
        assert "invalid_endpoint" in result["error"]
        assert "available_endpoints" in result

    @patch('streamlit_extension.endpoints.execution_api.is_authenticated')
    @patch('streamlit_extension.endpoints.execution_api.check_rate_limit')
    @patch('streamlit_extension.endpoints.execution_api.get_task_service')
    def test_handle_execution_planning_success(self, mock_get_service, mock_rate_limit, mock_auth):
        """Test successful execution planning."""
        mock_auth.return_value = True
        mock_rate_limit.return_value = (True, None)
        
        # Mock task service
        mock_service = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = self.sample_execution_plan
        mock_service.plan_epic_execution.return_value = mock_result
        mock_get_service.return_value = mock_service
        
        result = handle_execution_planning(self.sample_query_params)
        
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["epic_id"] == 1
        assert result["data"]["execution_order"] == ["TASK_001", "TASK_002"]
        mock_service.plan_epic_execution.assert_called_once_with(
            epic_id=1, scoring_preset="balanced", custom_weights=None
        )

    def test_handle_execution_planning_missing_epic_id(self):
        """Test execution planning with missing epic_id."""
        params = {"preset": "balanced"}  # Missing epic_id
        
        result = handle_execution_planning(params)
        
        assert "error" in result
        assert result["code"] == "MISSING_PARAMETER"
        assert "epic_id" in result["error"]

    def test_handle_execution_planning_invalid_epic_id(self):
        """Test execution planning with invalid epic_id."""
        params = {"epic_id": "not_a_number", "preset": "balanced"}
        
        result = handle_execution_planning(params)
        
        assert "error" in result
        assert result["code"] == "INVALID_PARAMETER"
        assert "Invalid epic_id" in result["error"]

    def test_handle_execution_planning_invalid_custom_weights(self):
        """Test execution planning with invalid custom weights JSON."""
        params = {
            "epic_id": "1",
            "preset": "balanced",
            "custom_weights": "invalid json"
        }
        
        result = handle_execution_planning(params)
        
        assert "error" in result
        assert result["code"] == "INVALID_JSON"
        assert "custom_weights" in result["error"]

    @patch('streamlit_extension.endpoints.execution_api.get_task_service')
    def test_handle_execution_planning_service_unavailable(self, mock_get_service):
        """Test execution planning with service unavailable."""
        mock_get_service.return_value = None
        
        result = handle_execution_planning(self.sample_query_params)
        
        assert "error" in result
        assert result["code"] == "SERVICE_UNAVAILABLE"

    @patch('streamlit_extension.endpoints.execution_api.get_task_service')
    def test_handle_execution_planning_service_failure(self, mock_get_service):
        """Test execution planning with service failure."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.success = False
        mock_result.errors = ["Planning failed"]
        mock_service.plan_epic_execution.return_value = mock_result
        mock_get_service.return_value = mock_service
        
        result = handle_execution_planning(self.sample_query_params)
        
        assert "error" in result
        assert result["code"] == "PLANNING_FAILED"
        assert result["details"] == ["Planning failed"]

    def test_handle_presets_list_success(self):
        """Test successful presets listing."""
        with patch('streamlit_extension.endpoints.execution_api.ScoringSystem') as mock_scoring:
            mock_system = Mock()
            mock_system.list_presets.return_value = {
                "balanced": "Balanced configuration",
                "critical_path": "Critical path focus"
            }
            mock_scoring.return_value = mock_system
            
            result = handle_presets_list({})
            
            assert result["success"] is True
            assert "data" in result
            assert "presets" in result["data"]
            assert result["data"]["default_preset"] == "balanced"
            assert result["data"]["total_presets"] == 2

class TestAPIMiddleware:
    """Test API middleware functionality."""
    
    def test_verify_api_key_valid(self):
        """Test API key verification with valid key."""
        api_key = "tdd_api_testuser_12345678"
        
        is_valid, user_id = verify_api_key(api_key)
        
        assert is_valid is True
        assert user_id == "testuser"

    def test_verify_api_key_invalid(self):
        """Test API key verification with invalid key."""
        api_key = "invalid_key"
        
        is_valid, user_id = verify_api_key(api_key)
        
        assert is_valid is False
        assert user_id is None

    def test_verify_api_key_empty(self):
        """Test API key verification with empty key."""
        is_valid, user_id = verify_api_key("")
        
        assert is_valid is False
        assert user_id is None

    @patch('streamlit_extension.endpoints.api_middleware.is_authenticated')
    @patch('streamlit_extension.endpoints.api_middleware.get_current_user')
    def test_authenticate_api_request_session_auth(self, mock_get_user, mock_is_auth):
        """Test API request authentication via session."""
        mock_is_auth.return_value = True
        mock_user = Mock()
        mock_user.username = "testuser"
        mock_get_user.return_value = mock_user
        
        query_params = {"epic_id": "1"}
        
        is_auth, user_id, auth_method = authenticate_api_request(query_params)
        
        assert is_auth is True
        assert user_id == "testuser"
        assert auth_method == "session"

    def test_authenticate_api_request_api_key_auth(self):
        """Test API request authentication via API key."""
        query_params = {
            "api_key": "tdd_api_testuser_12345678",
            "epic_id": "1"
        }
        
        is_auth, user_id, auth_method = authenticate_api_request(query_params)
        
        assert is_auth is True
        assert user_id == "testuser"
        assert auth_method == "api_key"

    @patch('streamlit_extension.endpoints.api_middleware.is_authenticated')
    def test_authenticate_api_request_no_auth(self, mock_is_auth):
        """Test API request authentication with no valid auth."""
        mock_is_auth.return_value = False
        
        query_params = {"epic_id": "1"}
        
        is_auth, user_id, auth_method = authenticate_api_request(query_params)
        
        assert is_auth is False
        assert user_id is None
        assert auth_method is None

    @patch('streamlit_extension.endpoints.api_middleware.authenticate_api_request')
    @patch('streamlit_extension.endpoints.api_middleware.check_api_rate_limit')
    def test_validate_api_request_success(self, mock_rate_limit, mock_auth):
        """Test successful API request validation."""
        mock_auth.return_value = (True, "testuser", "session")
        mock_rate_limit.return_value = (True, None)
        
        query_params = {"api": "execution", "epic_id": "1"}
        
        result = validate_api_request(query_params)
        
        assert result["success"] is True
        assert result["user_id"] == "testuser"
        assert result["auth_method"] == "session"
        assert result["rate_limit_ok"] is True
        assert len(result["errors"]) == 0

    @patch('streamlit_extension.endpoints.api_middleware.authenticate_api_request')
    def test_validate_api_request_auth_failed(self, mock_auth):
        """Test API request validation with auth failure."""
        mock_auth.return_value = (False, None, None)
        
        query_params = {"api": "execution", "epic_id": "1"}
        
        result = validate_api_request(query_params)
        
        assert result["success"] is False
        assert "Authentication required" in result["errors"]

    @patch('streamlit_extension.endpoints.api_middleware.authenticate_api_request')
    @patch('streamlit_extension.endpoints.api_middleware.check_api_rate_limit')
    def test_validate_api_request_missing_params(self, mock_rate_limit, mock_auth):
        """Test API request validation with missing parameters."""
        mock_auth.return_value = (True, "testuser", "session")
        mock_rate_limit.return_value = (True, None)
        
        query_params = {"api": "execution"}  # Missing epic_id
        
        result = validate_api_request(query_params)
        
        assert result["success"] is False
        assert any("Missing required parameter: epic_id" in error for error in result["errors"])

    def test_create_api_error_response(self):
        """Test API error response creation."""
        response = create_api_error_response(
            "Test error", "TEST_ERROR", {"detail": "test detail"}
        )
        
        assert response["error"] == "Test error"
        assert response["code"] == "TEST_ERROR"
        assert response["details"]["detail"] == "test detail"
        assert "timestamp" in response

    def test_create_api_success_response(self):
        """Test API success response creation."""
        data = {"result": "success"}
        metadata = {"total": 1}
        
        response = create_api_success_response(data, metadata)
        
        assert response["success"] is True
        assert response["data"] == data
        assert response["metadata"] == metadata
        assert "timestamp" in response

    def test_generate_dev_api_key(self):
        """Test development API key generation."""
        user_id = "testuser"
        
        api_key = generate_dev_api_key(user_id)
        
        assert api_key.startswith("tdd_api_testuser_")
        assert len(api_key) > 20  # Should include hash suffix

class TestAPIIntegration:
    """Integration tests for API functionality."""
    
    @patch('streamlit_extension.endpoints.execution_api.is_authenticated')
    @patch('streamlit_extension.endpoints.execution_api.check_rate_limit')
    @patch('streamlit_extension.endpoints.execution_api.get_task_service')
    def test_full_api_workflow(self, mock_get_service, mock_rate_limit, mock_auth):
        """Test complete API workflow from request to response."""
        # Setup mocks
        mock_auth.return_value = True
        mock_rate_limit.return_value = (True, None)
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = self.setup_sample_plan()
        mock_service.plan_epic_execution.return_value = mock_result
        mock_get_service.return_value = mock_service
        
        # Test execution planning endpoint
        query_params = {"epic_id": "1", "preset": "balanced"}
        
        result = handle_api_request("execution", query_params)
        
        assert result.get("success") is True
        assert "data" in result
        assert result["data"]["epic_id"] == 1
        assert "timestamp" in result

    def setup_sample_plan(self):
        """Setup sample execution plan for testing."""
        plan = Mock()
        plan.epic_id = 1
        plan.execution_order = ["TASK_001", "TASK_002", "TASK_003"]
        plan.task_scores = {"TASK_001": 8.5, "TASK_002": 7.2, "TASK_003": 6.8}
        plan.critical_path = ["TASK_001", "TASK_003"]
        plan.execution_metrics = {
            "total_tasks": 3,
            "total_estimated_hours": 24.5,
            "avg_score": 7.5
        }
        plan.dag_validation = {"is_valid": True}
        plan.created_at = Mock()
        plan.created_at.isoformat.return_value = "2025-01-15T14:30:00Z"
        return plan

# Pytest markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.streamlit,
    pytest.mark.fast
]