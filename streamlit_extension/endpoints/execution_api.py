#!/usr/bin/env python3
"""
🔗 ENDPOINTS - Execution API

API endpoints for TaskExecutionPlanner functionality integrated with Streamlit.
Uses query parameters approach to provide REST-like API without Flask.

Usage:
    GET /?api=execution&epic_id=1&preset=balanced
    GET /?api=validate&epic_id=1
    GET /?api=scoring&epic_id=1&preset=tdd_workflow
    GET /?api=summary&epic_id=1
    GET /?api=presets

Features:
- ✅ Integrated with existing Streamlit authentication
- ✅ Uses ServiceContainer and TaskExecutionPlanner
- ✅ JSON responses for external API consumers
- ✅ Parameter validation and error handling
- ✅ Rate limiting integration
"""

import logging
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from ..services import get_task_service
from ..utils.exception_handler import handle_streamlit_exceptions, streamlit_error_boundary
from .api_middleware import (
    validate_api_request,
    log_api_request,
    create_api_error_response,
    create_api_success_response,
)

logger = logging.getLogger(__name__)

@handle_streamlit_exceptions(show_error=False, attempt_recovery=False)
def handle_api_request(api_endpoint: str, query_params: Dict[str, str]) -> Dict[str, Any]:
    """Main API request handler for TaskExecutionPlanner endpoints."""
    validation = validate_api_request(query_params)
    if not validation.get("success"):
        return create_api_error_response(
            error_message="; ".join(validation.get("errors", ["Validation failed"])),
            error_code="VALIDATION_ERROR",
            details={"auth_method": validation.get("auth_method")},
        )
    user_id = validation.get("user_id")

    handlers = {
        "execution": handle_execution_planning,
        "validate": handle_epic_validation,
        "scoring": handle_scoring_analysis,
        "summary": handle_execution_summary,
        "presets": handle_presets_list,
    }

    handler = handlers.get(api_endpoint)
    if not handler:
        return create_api_error_response(
            error_message=f"Unknown API endpoint: {api_endpoint}",
            error_code="INVALID_ENDPOINT",
            details={"available_endpoints": list(handlers.keys())},
        )

    try:
        with streamlit_error_boundary(f"api_handler_{api_endpoint}"):
            started = datetime.now()
            resp = handler(query_params)
            try:
                log_api_request(
                    query_params,
                    user_id=user_id,
                    auth_method=validation.get("auth_method"),
                    response_time=(datetime.now() - started).total_seconds(),
                )
            finally:
                return resp
    except Exception as e:
        logger.exception("API handler error for %s", api_endpoint)
        return create_api_error_response(
            error_message="Internal server error",
            error_code="INTERNAL_ERROR",
            details=str(e),
        )

def _parse_epic_id(query_params: Dict[str, str]) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    """Helper único para ler/validar epic_id."""
    epic_id_str = query_params.get("epic_id")
    if not epic_id_str:
        return None, create_api_error_response("Missing required parameter: epic_id", "MISSING_PARAMETER")
    try:
        return int(epic_id_str), None
    except ValueError:
        return None, create_api_error_response(
            f"Invalid epic_id: {epic_id_str}. Must be integer.",
            "INVALID_PARAMETER",
        )


def handle_execution_planning(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle execution planning API endpoint.
    
    Query params:
        epic_id (required): Epic ID to plan
        preset (optional): Scoring preset (default: balanced)
        custom_weights (optional): JSON string with custom weights
        
    Returns:
        JSON response with execution plan or error
    """
    epic_id, err = _parse_epic_id(query_params)
    if err:
        return err
    
    # Optional parameters
    preset = query_params.get("preset", "balanced")
    custom_weights_str = query_params.get("custom_weights")
    
    custom_weights = None
    if custom_weights_str:
        try:
            custom_weights = json.loads(custom_weights_str)
        except json.JSONDecodeError as e:
            return create_api_error_response(f"Invalid custom_weights JSON: {str(e)}", "INVALID_JSON")
    
    task_service = get_task_service()
    if not task_service:
        return create_api_error_response("Task service not available", "SERVICE_UNAVAILABLE")
    
    result = task_service.plan_epic_execution(
        epic_id=epic_id,
        scoring_preset=preset,
        custom_weights=custom_weights
    )
    
    if result.success:
        plan = result.data
        payload = {
            "epic_id": plan.epic_id,
            "execution_order": plan.execution_order,
            "task_scores": plan.task_scores,
            "critical_path": plan.critical_path,
            "execution_metrics": plan.execution_metrics,
            "dag_validation": plan.dag_validation,
            "created_at": plan.created_at.isoformat(),
        }
        return create_api_success_response(payload)
    return create_api_error_response("Execution planning failed", "PLANNING_FAILED", details=result.errors)

def handle_epic_validation(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle epic dependency validation API endpoint.
    
    Query params:
        epic_id (required): Epic ID to validate
        
    Returns:
        JSON response with validation results
    """
    epic_id, err = _parse_epic_id(query_params)
    if err:
        return err
    
    # Get task service and validate dependencies
    task_service = get_task_service()
    if not task_service:
        return create_api_error_response("Task service not available", "SERVICE_UNAVAILABLE")
    
    result = task_service.validate_epic_dependencies(epic_id)
    
    if result.success:
        return create_api_success_response(result.data)
    return create_api_error_response("Dependency validation failed", "VALIDATION_FAILED", details=result.errors)

def handle_scoring_analysis(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle task scoring analysis API endpoint.
    
    Query params:
        epic_id (required): Epic ID to analyze
        preset (optional): Scoring preset (default: balanced)
        
    Returns:
        JSON response with scoring analysis
    """
    epic_id, err = _parse_epic_id(query_params)
    if err:
        return err
    
    # Optional parameters
    preset = query_params.get("preset", "balanced")
    
    # Get task service and analyze scoring
    task_service = get_task_service()
    if not task_service:
        return create_api_error_response("Task service not available", "SERVICE_UNAVAILABLE")
    
    result = task_service.get_task_scoring_analysis(epic_id, preset)
    
    if result.success:
        return create_api_success_response(result.data)
    return create_api_error_response("Scoring analysis failed", "ANALYSIS_FAILED", details=result.errors)

def handle_execution_summary(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle execution summary API endpoint.
    
    Query params:
        epic_id (required): Epic ID to summarize
        preset (optional): Scoring preset (default: balanced)
        
    Returns:
        JSON response with execution summary
    """
    epic_id, err = _parse_epic_id(query_params)
    if err:
        return err
    
    # Optional parameters
    preset = query_params.get("preset", "balanced")
    
    # Get task service and get summary
    task_service = get_task_service()
    if not task_service:
        return create_api_error_response("Task service not available", "SERVICE_UNAVAILABLE")
    
    result = task_service.get_execution_summary(epic_id, preset)
    
    if result.success:
        return create_api_success_response(result.data)
    return create_api_error_response("Execution summary failed", "SUMMARY_FAILED", details=result.errors)

def handle_presets_list(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle scoring presets listing API endpoint.
    
    Query params:
        None required
        
    Returns:
        JSON response with available scoring presets
    """
    from ..models.scoring import ScoringSystem
    
    try:
        scoring_system = ScoringSystem()
        presets = scoring_system.list_presets()
        
        return create_api_success_response({
            "presets": presets,
            "default_preset": "balanced",
            "total_presets": len(presets),
        })
    except Exception as e:
        logger.exception("Error listing presets")
        return create_api_error_response("Failed to list presets", "PRESETS_ERROR", details=str(e))

def get_api_documentation() -> Dict[str, Any]:
    """
    Get API documentation for TaskExecutionPlanner endpoints.
    
    Returns:
        Dict containing API documentation
    """
    return {
        "api_version": "1.0.0",
        "description": "TaskExecutionPlanner API integrated with Streamlit",
        "authentication": "Streamlit session authentication required",
        "base_url": "/?api=<endpoint>",
        "endpoints": {
            "execution": {
                "method": "GET",
                "url": "/?api=execution",
                "description": "Plan task execution order with prioritization",
                "parameters": {
                    "epic_id": {"type": "integer", "required": True, "description": "Epic ID to plan"},
                    "preset": {"type": "string", "required": False, "default": "balanced", "description": "Scoring preset"},
                    "custom_weights": {"type": "json_string", "required": False, "description": "Custom scoring weights"}
                },
                "example": "/?api=execution&epic_id=1&preset=balanced"
            },
            "validate": {
                "method": "GET", 
                "url": "/?api=validate",
                "description": "Validate epic dependencies and DAG structure",
                "parameters": {
                    "epic_id": {"type": "integer", "required": True, "description": "Epic ID to validate"}
                },
                "example": "/?api=validate&epic_id=1"
            },
            "scoring": {
                "method": "GET",
                "url": "/?api=scoring", 
                "description": "Analyze task scoring with different presets",
                "parameters": {
                    "epic_id": {"type": "integer", "required": True, "description": "Epic ID to analyze"},
                    "preset": {"type": "string", "required": False, "default": "balanced", "description": "Scoring preset"}
                },
                "example": "/?api=scoring&epic_id=1&preset=tdd_workflow"
            },
            "summary": {
                "method": "GET",
                "url": "/?api=summary",
                "description": "Get execution summary for an epic",
                "parameters": {
                    "epic_id": {"type": "integer", "required": True, "description": "Epic ID to summarize"},
                    "preset": {"type": "string", "required": False, "default": "balanced", "description": "Scoring preset"}
                },
                "example": "/?api=summary&epic_id=1"
            },
            "presets": {
                "method": "GET",
                "url": "/?api=presets",
                "description": "List available scoring presets",
                "parameters": {},
                "example": "/?api=presets"
            }
        },
        "response_format": {
            "success": {
                "success": True,
                "data": "...",
                "timestamp": "ISO 8601 timestamp"
            },
            "error": {
                "error": "Error message",
                "code": "ERROR_CODE",
                "details": "Additional details (optional)",
                "timestamp": "ISO 8601 timestamp"
            }
        },
        "scoring_presets": [
            "balanced", "critical_path", "tdd_workflow", "business_value"
        ]
    }