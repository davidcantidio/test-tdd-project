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
from typing import Dict, Any, Optional
from datetime import datetime

from ..services import get_task_service, ServiceResult
from ..utils.exception_handler import handle_streamlit_exceptions, streamlit_error_boundary
from ..auth.middleware import is_authenticated, get_current_user
from ..utils.security import check_rate_limit

logger = logging.getLogger(__name__)

@handle_streamlit_exceptions(show_error=False, attempt_recovery=False)
def handle_api_request(api_endpoint: str, query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Main API request handler for TaskExecutionPlanner endpoints.
    
    Args:
        api_endpoint: The API endpoint name (execution, validate, scoring, etc.)
        query_params: Dict of query parameters from Streamlit
        
    Returns:
        Dict containing JSON response data
    """
    # Authentication check
    if not is_authenticated():
        return {
            "error": "Authentication required",
            "code": "AUTH_REQUIRED",
            "timestamp": datetime.now().isoformat()
        }
    
    # Rate limiting check
    rate_allowed, rate_error = check_rate_limit("api_request")
    if not rate_allowed:
        return {
            "error": f"Rate limit exceeded: {rate_error}",
            "code": "RATE_LIMIT_EXCEEDED", 
            "timestamp": datetime.now().isoformat()
        }
    
    # Route to appropriate handler
    handlers = {
        "execution": handle_execution_planning,
        "validate": handle_epic_validation,
        "scoring": handle_scoring_analysis,
        "summary": handle_execution_summary,
        "presets": handle_presets_list
    }
    
    handler = handlers.get(api_endpoint)
    if not handler:
        return {
            "error": f"Unknown API endpoint: {api_endpoint}",
            "code": "INVALID_ENDPOINT",
            "available_endpoints": list(handlers.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        with streamlit_error_boundary(f"api_handler_{api_endpoint}"):
            return handler(query_params)
    except Exception as e:
        logger.error(f"API handler error for {api_endpoint}: {e}")
        return {
            "error": f"Internal server error: {str(e)}",
            "code": "INTERNAL_ERROR",
            "timestamp": datetime.now().isoformat()
        }

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
    # Validate required parameters
    epic_id_str = query_params.get("epic_id")
    if not epic_id_str:
        return {
            "error": "Missing required parameter: epic_id",
            "code": "MISSING_PARAMETER",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        epic_id = int(epic_id_str)
    except ValueError:
        return {
            "error": f"Invalid epic_id: {epic_id_str}. Must be integer.",
            "code": "INVALID_PARAMETER",
            "timestamp": datetime.now().isoformat()
        }
    
    # Optional parameters
    preset = query_params.get("preset", "balanced")
    custom_weights_str = query_params.get("custom_weights")
    
    custom_weights = None
    if custom_weights_str:
        try:
            custom_weights = json.loads(custom_weights_str)
        except json.JSONDecodeError as e:
            return {
                "error": f"Invalid custom_weights JSON: {str(e)}",
                "code": "INVALID_JSON",
                "timestamp": datetime.now().isoformat()
            }
    
    # Get task service and execute planning
    task_service = get_task_service()
    if not task_service:
        return {
            "error": "Task service not available",
            "code": "SERVICE_UNAVAILABLE",
            "timestamp": datetime.now().isoformat()
        }
    
    result = task_service.plan_epic_execution(
        epic_id=epic_id,
        scoring_preset=preset,
        custom_weights=custom_weights
    )
    
    if result.success:
        plan = result.data
        return {
            "success": True,
            "data": {
                "epic_id": plan.epic_id,
                "execution_order": plan.execution_order,
                "task_scores": plan.task_scores,
                "critical_path": plan.critical_path,
                "execution_metrics": plan.execution_metrics,
                "dag_validation": plan.dag_validation,
                "created_at": plan.created_at.isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "error": "Execution planning failed",
            "code": "PLANNING_FAILED",
            "details": result.errors,
            "timestamp": datetime.now().isoformat()
        }

def handle_epic_validation(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle epic dependency validation API endpoint.
    
    Query params:
        epic_id (required): Epic ID to validate
        
    Returns:
        JSON response with validation results
    """
    # Validate required parameters
    epic_id_str = query_params.get("epic_id")
    if not epic_id_str:
        return {
            "error": "Missing required parameter: epic_id",
            "code": "MISSING_PARAMETER",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        epic_id = int(epic_id_str)
    except ValueError:
        return {
            "error": f"Invalid epic_id: {epic_id_str}. Must be integer.",
            "code": "INVALID_PARAMETER",
            "timestamp": datetime.now().isoformat()
        }
    
    # Get task service and validate dependencies
    task_service = get_task_service()
    if not task_service:
        return {
            "error": "Task service not available",
            "code": "SERVICE_UNAVAILABLE",
            "timestamp": datetime.now().isoformat()
        }
    
    result = task_service.validate_epic_dependencies(epic_id)
    
    if result.success:
        validation = result.data
        return {
            "success": True,
            "data": validation,
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "error": "Dependency validation failed",
            "code": "VALIDATION_FAILED",
            "details": result.errors,
            "timestamp": datetime.now().isoformat()
        }

def handle_scoring_analysis(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle task scoring analysis API endpoint.
    
    Query params:
        epic_id (required): Epic ID to analyze
        preset (optional): Scoring preset (default: balanced)
        
    Returns:
        JSON response with scoring analysis
    """
    # Validate required parameters
    epic_id_str = query_params.get("epic_id")
    if not epic_id_str:
        return {
            "error": "Missing required parameter: epic_id",
            "code": "MISSING_PARAMETER",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        epic_id = int(epic_id_str)
    except ValueError:
        return {
            "error": f"Invalid epic_id: {epic_id_str}. Must be integer.",
            "code": "INVALID_PARAMETER",
            "timestamp": datetime.now().isoformat()
        }
    
    # Optional parameters
    preset = query_params.get("preset", "balanced")
    
    # Get task service and analyze scoring
    task_service = get_task_service()
    if not task_service:
        return {
            "error": "Task service not available",
            "code": "SERVICE_UNAVAILABLE",
            "timestamp": datetime.now().isoformat()
        }
    
    result = task_service.get_task_scoring_analysis(epic_id, preset)
    
    if result.success:
        analysis = result.data
        return {
            "success": True,
            "data": analysis,
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "error": "Scoring analysis failed",
            "code": "ANALYSIS_FAILED",
            "details": result.errors,
            "timestamp": datetime.now().isoformat()
        }

def handle_execution_summary(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle execution summary API endpoint.
    
    Query params:
        epic_id (required): Epic ID to summarize
        preset (optional): Scoring preset (default: balanced)
        
    Returns:
        JSON response with execution summary
    """
    # Validate required parameters
    epic_id_str = query_params.get("epic_id")
    if not epic_id_str:
        return {
            "error": "Missing required parameter: epic_id",
            "code": "MISSING_PARAMETER",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        epic_id = int(epic_id_str)
    except ValueError:
        return {
            "error": f"Invalid epic_id: {epic_id_str}. Must be integer.",
            "code": "INVALID_PARAMETER",
            "timestamp": datetime.now().isoformat()
        }
    
    # Optional parameters
    preset = query_params.get("preset", "balanced")
    
    # Get task service and get summary
    task_service = get_task_service()
    if not task_service:
        return {
            "error": "Task service not available",
            "code": "SERVICE_UNAVAILABLE",
            "timestamp": datetime.now().isoformat()
        }
    
    result = task_service.get_execution_summary(epic_id, preset)
    
    if result.success:
        summary = result.data
        return {
            "success": True,
            "data": summary,
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "error": "Execution summary failed",
            "code": "SUMMARY_FAILED",
            "details": result.errors,
            "timestamp": datetime.now().isoformat()
        }

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
        
        return {
            "success": True,
            "data": {
                "presets": presets,
                "default_preset": "balanced",
                "total_presets": len(presets)
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing presets: {e}")
        return {
            "error": f"Failed to list presets: {str(e)}",
            "code": "PRESETS_ERROR",
            "timestamp": datetime.now().isoformat()
        }

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