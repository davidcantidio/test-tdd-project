"""
🎮 Product Vision Controller - Business Logic Orchestration

This controller orchestrates Product Vision business operations by coordinating
between the domain layer (pure business logic), infrastructure layer (repositories),
and external services (AI refinement). It implements use cases and application-specific
business workflows while maintaining clean architecture principles.

Controller Responsibilities:
    - Coordinate domain operations with external services
    - Provide UI-friendly APIs with proper error handling
    - Manage application-specific business workflows
    - Handle data shape normalization for consistent processing
    - Integrate AI services with domain business rules

Key Functions:
    - Validation: Check if Product Vision can be refined or saved
    - Summarization: Create human-readable summaries for UI display
    - Refinement: Coordinate AI enhancement with business rules
    - Data Normalization: Ensure consistent data shapes across operations

Clean Architecture Compliance:
    - Imports only from domain layer (inward dependency)
    - Provides thin coordination layer without business logic
    - Delegates all business rules to domain services
    - Returns data structures, never UI components

Usage:
    This controller is designed to be called from UI layer components
    that need to perform Product Vision business operations.
"""

# streamlit_extension/pages/projetos/controllers/product_vision_controller.py
from __future__ import annotations
from typing import Dict, Any

from ..domain.product_vision_state import (
    DEFAULT_PV,
    validate_product_vision,
    apply_refine_result,
    refine_all_and_apply,
)

# Human-readable labels for UI display
# Maps domain field names to user-friendly Portuguese labels
HUMAN_LABELS = {
    "vision_statement": "Declaração de Visão",
    "problem_statement": "Problema", 
    "target_audience": "Público-alvo",
    "value_proposition": "Proposta de Valor",
    "constraints": "Restrições",
}

def _ensure_shape(pv: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Product Vision data to ensure consistent structure and types.
    
    This internal function ensures that Product Vision data has the correct
    structure and data types before processing. It provides a defensive
    programming approach by guaranteeing data shape consistency.
    
    Args:
        pv: Product Vision data (may be incomplete or malformed)
        
    Returns:
        Normalized Product Vision with all required fields and correct types
        
    Note:
        This is an internal function used by other controller methods to
        ensure data consistency before delegating to domain services.
    """
    data = {**DEFAULT_PV}
    data.update(pv or {})
    # Guarantee basic data types
    if not isinstance(data["constraints"], list):
        data["constraints"] = []
    return data


# -------- Public API expected by tests and UI components --------

def can_refine(pv: Dict[str, Any]) -> bool:
    """
    Check if a Product Vision can be refined by AI services.
    
    This function determines whether the current Product Vision state
    meets the business requirements for AI refinement processing.
    
    Args:
        pv: Product Vision data to check for refinement eligibility
        
    Returns:
        True if the Product Vision can be refined, False otherwise
        
    Examples:
        >>> complete_pv = {
        ...     "vision_statement": "Transform development", 
        ...     "problem_statement": "TDD complexity",
        ...     "target_audience": "Dev teams",
        ...     "value_proposition": "Simplified workflow",
        ...     "constraints": ["Time constraints"]
        ... }
        >>> can_refine(complete_pv)
        True
        
        >>> incomplete_pv = {"vision_statement": ""}
        >>> can_refine(incomplete_pv)
        False
    """
    ok, _ = validate_product_vision(_ensure_shape(pv))
    return ok


def can_save(pv: Dict[str, Any]) -> bool:
    """
    Check if a Product Vision meets requirements for saving/persistence.
    
    This function validates whether the Product Vision data is complete
    and valid enough to be saved to persistent storage.
    
    Args:
        pv: Product Vision data to validate for saving
        
    Returns:
        True if the Product Vision can be saved, False otherwise
        
    Examples:
        >>> valid_pv = {
        ...     "vision_statement": "Clear vision",
        ...     "problem_statement": "Specific problem", 
        ...     "target_audience": "Target users",
        ...     "value_proposition": "Unique value",
        ...     "constraints": ["Budget limit"]
        ... }
        >>> can_save(valid_pv)
        True
        
        >>> invalid_pv = {"vision_statement": "", "constraints": []}
        >>> can_save(invalid_pv)
        False
    """
    ok, _ = validate_product_vision(_ensure_shape(pv))
    return ok

def build_summary(pv: Dict[str, Any]) -> Dict[str, str]:
    """
    Build a human-readable summary of Product Vision for UI display.
    
    This function transforms Product Vision data into a format suitable
    for user interface display, using human-readable labels and formatting
    constraints as a readable comma-separated string.
    
    Args:
        pv: Product Vision data to summarize
        
    Returns:
        Dictionary mapping human-readable field labels to formatted values
        
    Examples:
        >>> pv_data = {
        ...     "vision_statement": "Transform development",
        ...     "problem_statement": "TDD is complex",
        ...     "target_audience": "Development teams", 
        ...     "value_proposition": "Simplified workflow",
        ...     "constraints": ["90 days", "Limited budget"]
        ... }
        >>> summary = build_summary(pv_data)
        >>> summary["Declaração de Visão"]
        "Transform development"
        >>> summary["Restrições"]
        "90 days, Limited budget"
        
    UI Integration:
        The returned dictionary uses Portuguese labels that can be directly
        displayed in the user interface without additional translation.
    """
    pv = _ensure_shape(pv)
    cons_list = [c for c in (pv.get("constraints") or []) if isinstance(c, str) and c.strip()]
    cons_str = ", ".join(cons_list)
    return {
        HUMAN_LABELS["vision_statement"]: pv.get("vision_statement", "").strip(),
        HUMAN_LABELS["problem_statement"]: pv.get("problem_statement", "").strip(),
        HUMAN_LABELS["target_audience"]: pv.get("target_audience", "").strip(),
        HUMAN_LABELS["value_proposition"]: pv.get("value_proposition", "").strip(),
        HUMAN_LABELS["constraints"]: cons_str,
    }


def apply_refinement(current: Dict[str, Any], refined: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply AI refinement results to current Product Vision data.
    
    This controller function coordinates the application of AI refinement
    results to existing Product Vision data, ensuring data normalization
    and delegating business logic to the domain layer.
    
    Args:
        current: Current Product Vision data
        refined: AI refinement results to apply (may be partial)
        
    Returns:
        Enhanced Product Vision with refinements applied
        
    Examples:
        >>> current = {"vision_statement": "Basic vision", "constraints": []}
        >>> refined = {"vision_statement": "Enhanced vision", "constraints": ["New constraint"]}
        >>> result = apply_refinement(current, refined)
        >>> result["vision_statement"]
        "Enhanced vision"
        >>> len(result["constraints"])
        1
        
    Architecture:
        This function normalizes data shapes and delegates business logic
        to the domain layer's apply_refine_result function.
    """
    current = _ensure_shape(current)
    refined = refined or {}
    return apply_refine_result(current, refined)

def refine_with_service(current: Dict[str, Any], service) -> Dict[str, Any]:
    """
    Orchestrate AI refinement of Product Vision using external service.
    
    This controller function coordinates the complete AI refinement workflow
    by integrating with external AI services while maintaining proper error
    handling and business rule enforcement. It serves as the primary entry
    point for AI-powered Product Vision enhancement.
    
    Service Contract:
        The service parameter must expose a .refine(payload: dict) -> dict method
        that follows the database taxonomy for input/output format.
    
    Args:
        current: Current Product Vision data to be enhanced
        service: AI refinement service implementing .refine() method
        
    Returns:
        Enhanced Product Vision with AI refinements applied
        
    Raises:
        ValueError: If AI service fails or returns invalid data
                   (Converted from original exception for consistent error handling)
        
    Examples:
        >>> class MockAIService:
        ...     def refine(self, payload):
        ...         return {"vision_statement": payload["vision_statement"] + " (Enhanced)"}
        
        >>> current_pv = {"vision_statement": "Basic vision", "constraints": []}
        >>> ai_service = MockAIService()
        >>> result = refine_with_service(current_pv, ai_service)
        >>> "Enhanced" in result["vision_statement"]
        True
        
        >>> # Error handling example
        >>> class FailingService:
        ...     def refine(self, payload):
        ...         raise RuntimeError("AI service unavailable")
        
        >>> try:
        ...     refine_with_service(current_pv, FailingService())
        ... except ValueError as e:
        ...     print("Handled gracefully:", str(e))
        Handled gracefully: AI service unavailable
        
    Architecture:
        This function provides controller-level coordination:
        1. Normalizes input data shape
        2. Delegates to domain layer for business logic
        3. Handles errors with proper exception translation
        4. Returns enhanced data for UI consumption
    """
    current = _ensure_shape(current)
    try:
        merged = refine_all_and_apply(current, service)
    except Exception as e:
        # Convert to ValueError for consistent error handling in tests and UI
        raise ValueError(str(e))
    return merged
