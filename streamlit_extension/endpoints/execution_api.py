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
"""

import json
import logging
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_epic_id(query_params: Dict[str, str]) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    """Parse and validate 'epic_id' from query params."""
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


def _parse_preset(query_params: Dict[str, str], default: str = "balanced") -> str:
    """Get preset parameter with default."""
    preset = (query_params.get("preset") or default).strip()
    return preset or default


def _parse_custom_weights(query_params: Dict[str, str]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Parse optional custom_weights as JSON string.
    Returns (weights_dict, error_response_or_none)
    """
    raw = query_params.get("custom_weights")
    if not raw:
        return None, None
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None, create_api_error_response(
                "Parameter 'custom_weights' must be a JSON object", "INVALID_PARAMETER"
            )
        return data, None
    except json.JSONDecodeError as e:
        return None, create_api_error_response(
            f"Invalid JSON in 'custom_weights': {e}", "INVALID_PARAMETER"
        )


def _call_execution_planner(task_service: Any, epic_id: int, preset: str, custom_weights: Optional[Dict[str, Any]]):
    """
    Call whichever execution planner method exists on the service.
    Expected ServiceResult-like object with (.success, .data, .errors).
    """
    # Try common method names in a stable order
    candidates = [
        "plan_execution",           # preferred
        "get_execution_plan",       # alternative
        "plan_task_execution",      # legacy
    ]
    method = next((name for name in candidates if hasattr(task_service, name)), None)
    if not method:
        raise AttributeError(
            "Task service does not expose an execution planning method. "
            f"Tried: {', '.join(candidates)}"
        )
    func = getattr(task_service, method)

    # Support both signatures: (epic_id, preset, custom_weights) and (epic_id, preset)
    try:
        return func(epic_id, preset, custom_weights)  # type: ignore[arg-type]
    except TypeError:
        return func(epic_id, preset)  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Endpoint handlers
# ---------------------------------------------------------------------------

@handle_streamlit_exceptions(show_error=False, attempt_recovery=False)
def handle_api_request(api_endpoint: str, query_params: Dict[str, str]) -> Dict[str, Any]:
    """Main API request handler for TaskExecutionPlanner endpoints."""
    validation = {}
    try:
        validation = validate_api_request(query_params) or {}
    except Exception as e:
        # Tolerância caso a função importada ainda não esteja finalizada
        logger.warning("validate_api_request raised an exception: %s", e)
        validation = {"success": False, "errors": ["Validation subsystem error"], "auth_method": None}

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

    started = datetime.now()
    try:
        with streamlit_error_boundary(f"api_handler_{api_endpoint}"):
            resp = handler(query_params)
    except Exception as e:
        logger.exception("API handler error for %s", api_endpoint)
        resp = create_api_error_response(
            error_message="Internal server error",
            error_code="INTERNAL_ERROR",
            details=str(e),
        )

    # Log fora de finally/return para não mascarar exceções
    try:
        log_api_request(
            query_params,
            user_id=user_id,
            auth_method=validation.get("auth_method"),
            response_time=(datetime.now() - started).total_seconds(),
        )
    except Exception as e:
        logger.warning("Failed to log API request: %s", e)

    return resp


def handle_execution_planning(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Plan task execution order with prioritization.
    Params:
      - epic_id (int, required)
      - preset (str, optional; default 'balanced')
      - custom_weights (json string, optional)
    """
    epic_id, err = _parse_epic_id(query_params)
    if err:
        return err

    preset = _parse_preset(query_params, default="balanced")
    custom_weights, cw_err = _parse_custom_weights(query_params)
    if cw_err:
        return cw_err

    task_service = get_task_service()
    if not task_service:
        return create_api_error_response("Task service not available", "SERVICE_UNAVAILABLE")

    try:
        result = _call_execution_planner(task_service, epic_id, preset, custom_weights)
    except AttributeError as e:
        return create_api_error_response("Execution planner not available", "SERVICE_MISSING_METHOD", details=str(e))
    except Exception as e:
        logger.exception("Error while calling execution planner")
        return create_api_error_response("Execution planning failed", "EXECUTION_ERROR", details=str(e))

    # ServiceResult expected
    if getattr(result, "success", False):
        return create_api_success_response(getattr(result, "data", {}))
    errors = getattr(result, "errors", None) or ["Unknown error"]
    return create_api_error_response("Execution planning failed", "EXECUTION_FAILED", details=errors)


def handle_epic_validation(query_params: Dict[str, str]) -> Dict[str, Any]:
    """Validate epic dependency graph."""
    epic_id, err = _parse_epic_id(query_params)
    if err:
        return err

    task_service = get_task_service()
    if not task_service:
        return create_api_error_response("Task service not available", "SERVICE_UNAVAILABLE")

    result = task_service.validate_epic_dependencies(epic_id)
    if result.success:
        return create_api_success_response(result.data)
    return create_api_error_response("Dependency validation failed", "VALIDATION_FAILED", details=result.errors)


def handle_scoring_analysis(query_params: Dict[str, str]) -> Dict[str, Any]:
    """Analyze task scoring with a given preset."""
    epic_id, err = _parse_epic_id(query_params)
    if err:
        return err

    preset = _parse_preset(query_params, default="balanced")

    task_service = get_task_service()
    if not task_service:
        return create_api_error_response("Task service not available", "SERVICE_UNAVAILABLE")

    result = task_service.get_task_scoring_analysis(epic_id, preset)
    if result.success:
        return create_api_success_response(result.data)
    return create_api_error_response("Scoring analysis failed", "ANALYSIS_FAILED", details=result.errors)


def handle_execution_summary(query_params: Dict[str, str]) -> Dict[str, Any]:
    """Get execution summary for an epic."""
    epic_id, err = _parse_epic_id(query_params)
    if err:
        return err

    preset = _parse_preset(query_params, default="balanced")

    task_service = get_task_service()
    if not task_service:
        return create_api_error_response("Task service not available", "SERVICE_UNAVAILABLE")

    result = task_service.get_execution_summary(epic_id, preset)
    if result.success:
        return create_api_success_response(result.data)
    return create_api_error_response("Execution summary failed", "SUMMARY_FAILED", details=result.errors)


def handle_presets_list(_query_params: Dict[str, str]) -> Dict[str, Any]:
    """List available scoring presets."""
    from ..models.scoring import ScoringSystem

    try:
        scoring_system = ScoringSystem()
        presets = scoring_system.list_presets()
        return create_api_success_response(
            {"presets": presets, "default_preset": "balanced", "total_presets": len(presets)}
        )
    except Exception as e:
        logger.exception("Error listing presets")
        return create_api_error_response("Failed to list presets", "PRESETS_ERROR", details=str(e))


def get_api_documentation() -> Dict[str, Any]:
    """Return self-documented interface for the endpoints."""
    return {
        "api_version": "1.0.0",
        "description": "TaskExecutionPlanner API integrated with Streamlit",
        "authentication": "Streamlit session or API Key (see middleware)",
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
            "success": {"success": True, "data": "...", "timestamp": "ISO 8601 timestamp"},
            "error": {"error": "Error message", "code": "ERROR_CODE", "details": "Optional", "timestamp": "ISO 8601 timestamp"}
        },
        "scoring_presets": ["balanced", "critical_path", "tdd_workflow", "business_value"]
    }
