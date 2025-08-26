"""
🧠 Product Vision Domain State - Pure Business Logic

This module implements the core business logic for Product Vision management
without any external dependencies. It contains pure functions that enforce
business rules, validate data, and perform domain-specific transformations.

Following Clean Architecture principles, this module:
- Contains zero dependencies on UI frameworks or persistence layers
- Implements pure business rules and invariants
- Provides deterministic, testable functions
- Serves as the single source of truth for Product Vision business logic

Domain Model:
    A Product Vision consists of:
    - vision_statement: The overarching vision for the product
    - problem_statement: The core problem being solved
    - target_audience: Who will use the product
    - value_proposition: The unique value delivered
    - constraints: List of limitations and restrictions

Business Rules:
    1. All fields are required and must contain meaningful content
    2. Constraints must be a non-empty list of non-empty strings
    3. String fields must contain non-whitespace content
    4. Data normalization preserves business meaning while standardizing format
"""

from __future__ import annotations
from typing import Dict, Any, Tuple, List

# Default empty Product Vision following domain model structure
DEFAULT_PV: Dict[str, Any] = {
    "vision_statement": "",
    "problem_statement": "",
    "target_audience": "",
    "value_proposition": "",
    "constraints": [],  # list[str]
}

# Required fields according to business rules
REQUIRED_FIELDS = [
    "vision_statement",
    "problem_statement",
    "target_audience",
    "value_proposition",
    "constraints",
]


def normalize_constraints(items: List[str]) -> List[str]:
    """
    Normalize constraint list by removing empty/whitespace-only entries.
    
    This function enforces the business rule that constraints must be
    meaningful, non-empty strings. It performs data sanitization while
    preserving business value.
    
    Args:
        items: List of constraint strings (may contain empty/whitespace strings)
        
    Returns:
        List of normalized constraint strings with empty entries removed
        
    Examples:
        >>> normalize_constraints(["budget limited", "  ", "90 day deadline"])
        ["budget limited", "90 day deadline"]
        
        >>> normalize_constraints([])
        []
        
        >>> normalize_constraints(None)  # Handles None gracefully
        []
    """
    return [x.strip() for x in (items or []) if isinstance(x, str) and x.strip()]

def all_fields_filled(pv: Dict[str, Any]) -> bool:
    """
    Check if all required fields in a Product Vision are properly filled.
    
    This function enforces the business rule that all Product Vision fields
    must contain meaningful content. It validates both the presence and
    meaningfulness of data according to domain requirements.
    
    Business Rules Applied:
        - String fields must contain non-whitespace content
        - Constraints must be a non-empty list of meaningful strings
        - All required fields must be present and valid
    
    Args:
        pv: Product Vision dictionary to validate
        
    Returns:
        True if all required fields are properly filled, False otherwise
        
    Examples:
        >>> valid_pv = {
        ...     "vision_statement": "Transform software development",
        ...     "problem_statement": "Teams struggle with TDD adoption",
        ...     "target_audience": "Development teams",
        ...     "value_proposition": "Simplified TDD workflow",
        ...     "constraints": ["90 day timeline", "Limited budget"]
        ... }
        >>> all_fields_filled(valid_pv)
        True
        
        >>> incomplete_pv = {"vision_statement": "", "problem_statement": "Problem"}
        >>> all_fields_filled(incomplete_pv)
        False
    """
    for k in REQUIRED_FIELDS:
        v = pv.get(k)
        if isinstance(v, str):
            if not v.strip():
                return False
        elif isinstance(v, list):
            if len(normalize_constraints(v)) == 0:
                return False
        else:
            return False
    return True

def validate_product_vision(pv: Dict[str, Any]) -> Tuple[bool, str | None]:
    """
    Validate a Product Vision against business rules with user-friendly messages.
    
    This function performs comprehensive validation of a Product Vision,
    checking all business rules and providing clear, actionable error messages
    for the user interface layer.
    
    Validation Rules:
        1. All string fields must exist and contain non-whitespace content
        2. Constraints field must be a list with at least one meaningful constraint
        3. Field types must match expected domain model types
    
    Args:
        pv: Product Vision dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if validation passes, False otherwise  
        - error_message: Human-readable error description (None if valid)
        
    Examples:
        >>> valid_pv = {
        ...     "vision_statement": "Transform development",
        ...     "problem_statement": "Complex TDD adoption", 
        ...     "target_audience": "Dev teams",
        ...     "value_proposition": "Simplified workflow",
        ...     "constraints": ["Budget limited"]
        ... }
        >>> validate_product_vision(valid_pv)
        (True, None)
        
        >>> invalid_pv = {"vision_statement": "", "constraints": []}
        >>> is_valid, error = validate_product_vision(invalid_pv)
        >>> is_valid
        False
        >>> "ausentes/invalidos" in error
        True
    """
    # Generate user-friendly error messages
    missing: List[str] = []
    for k in ["vision_statement","problem_statement","target_audience","value_proposition"]:
        if not isinstance(pv.get(k), str) or not pv[k].strip():
            missing.append(k)
    if not isinstance(pv.get("constraints"), list) or len(normalize_constraints(pv["constraints"])) == 0:
        missing.append("constraints")

    if missing:
        return False, f"Campos obrigatórios ausentes/invalidos: {', '.join(missing)}"
    return True, None

def apply_refine_result(current: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge AI refinement results with current Product Vision data.
    
    This function implements the business rule for safely merging AI-generated
    refinements with existing Product Vision data. It preserves current data
    while selectively applying meaningful improvements from AI processing.
    
    Merging Rules:
        1. Only apply non-empty string values from refinement results
        2. Preserve existing data when refinement provides no improvement
        3. Normalize and validate constraint lists before applying
        4. Maintain data integrity throughout the merge process
    
    Args:
        current: Existing Product Vision data to be enhanced
        result: AI refinement results (may be partial)
        
    Returns:
        Merged Product Vision with refinements applied where appropriate
        
    Examples:
        >>> current = {
        ...     "vision_statement": "Basic vision",
        ...     "problem_statement": "Simple problem",
        ...     "target_audience": "Users",
        ...     "value_proposition": "Some value",
        ...     "constraints": ["Time limit"]
        ... }
        >>> refinement = {
        ...     "vision_statement": "Enhanced AI-refined vision",
        ...     "constraints": ["Time limit", "Budget constraint"]
        ... }
        >>> result = apply_refine_result(current, refinement)
        >>> result["vision_statement"]
        "Enhanced AI-refined vision"
        >>> len(result["constraints"])
        2
    """
    merged = dict(current)
    for k in ["vision_statement","problem_statement","target_audience","value_proposition"]:
        val = result.get(k)
        if isinstance(val, str) and val.strip():
            merged[k] = val.strip()
    cons = result.get("constraints")
    if isinstance(cons, list) and len(normalize_constraints(cons)) > 0:
        merged["constraints"] = normalize_constraints(cons)
    return merged

def refine_all_and_apply(pv: Dict[str, Any], refiner) -> Dict[str, Any]:
    """
    Orchestrate AI refinement of Product Vision with business rule enforcement.
    
    This function coordinates the complete AI refinement workflow by preparing
    normalized data, invoking the AI service, and safely applying results
    while maintaining data integrity and business rules.
    
    Workflow:
        1. Normalize current Product Vision data to standard format
        2. Prepare clean payload for AI refinement service
        3. Invoke AI refinement service with normalized data
        4. Apply refinement results using business rules
        5. Return enhanced Product Vision with original data preserved
    
    Args:
        pv: Current Product Vision data to be refined
        refiner: AI refinement service that exposes .refine(payload: dict) -> dict
                The service follows database taxonomy for input/output format
                
    Returns:
        Enhanced Product Vision with AI refinements applied where appropriate
        
    Raises:
        Exception: If the AI refinement service fails or returns invalid data
        
    Examples:
        >>> class MockRefiner:
        ...     def refine(self, payload):
        ...         return {
        ...             "vision_statement": payload["vision_statement"] + " (AI Enhanced)",
        ...             "constraints": payload["constraints"] + ["AI Suggestion"]
        ...         }
        
        >>> pv = {"vision_statement": "Basic vision", "constraints": ["Time"]}
        >>> refiner = MockRefiner()
        >>> result = refine_all_and_apply(pv, refiner)
        >>> "AI Enhanced" in result["vision_statement"]
        True
        >>> "AI Suggestion" in result["constraints"]
        True
        
    Business Rules Applied:
        - Input data is normalized before refinement
        - Only meaningful improvements are applied to output
        - Original data is preserved when refinement adds no value
        - Constraint lists are normalized and validated
    """
    payload = {
        "vision_statement": pv.get("vision_statement", "").strip(),
        "problem_statement": pv.get("problem_statement", "").strip(),
        "target_audience": pv.get("target_audience", "").strip(),
        "value_proposition": pv.get("value_proposition", "").strip(),
        "constraints": normalize_constraints(pv.get("constraints", [])),
    }
    result = refiner.refine(payload)  # May return partial results
    return apply_refine_result(pv, result)
