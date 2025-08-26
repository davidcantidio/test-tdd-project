"""
📄 Wizard State Management - UI State Coordination

This module manages the state of the Project Wizard across multiple steps
and user interactions. It provides a clean interface for managing wizard
workflow state within Streamlit's session state system.

State Management Responsibilities:
    - Initialize and maintain wizard state structure
    - Coordinate step transitions and navigation
    - Preserve user data across wizard steps
    - Provide validation for step progression
    - Manage draft data before persistence

Key Concepts:
    - Wizard state is stored in Streamlit session state under a specific key
    - State includes current step and project draft data
    - Draft data follows domain model structure for consistency
    - State transitions are validated before execution

Usage:
    This module is used by wizard UI components to maintain consistent
    state across multiple user interactions and page reloads.
"""

from __future__ import annotations
from typing import Dict, Any, Tuple

# Session state key for wizard data isolation
WIZ_KEY = "projeto_wizard"

# Default project draft structure following domain model
DEFAULT_DRAFT: Dict[str, Any] = {
    "name": "",
    # Product Vision fields following database taxonomy (in-memory draft)
    "vision_statement": "",
    "problem_statement": "",
    "target_audience": "",
    "value_proposition": "",
    "constraints": [],  # list[str]
}

def init_wizard_state(session_state: Dict[str, Any]) -> None:
    """
    Initialize wizard state structure in session state.
    
    This function ensures the wizard has proper state structure in the session
    state dictionary, creating the initial state if it doesn't exist and
    ensuring all required keys are present without overwriting existing data.
    
    Args:
        session_state: Streamlit session state or compatible dictionary
        
    State Structure:
        - current_step: Current wizard step identifier
        - project_draft: Draft project data being built by user
        
    Examples:
        >>> state = {}
        >>> init_wizard_state(state)
        >>> state[WIZ_KEY]["current_step"]
        "project_name"
        >>> state[WIZ_KEY]["project_draft"]["name"]
        ""
        
    Note:
        This function is idempotent - safe to call multiple times.
        It preserves existing user data while ensuring structure consistency.
    """
    if WIZ_KEY not in session_state:
        session_state[WIZ_KEY] = {
            "current_step": "project_name",
            "project_draft": dict(DEFAULT_DRAFT),
        }
    else:
        wiz = session_state[WIZ_KEY]
        wiz.setdefault("current_step", "project_name")
        wiz.setdefault("project_draft", dict(DEFAULT_DRAFT))
        # garante todas as chaves do draft (sem perder dados existentes)
        for k, v in DEFAULT_DRAFT.items():
            wiz["project_draft"].setdefault(k, v)

def current_step(session_state: Dict[str, Any]) -> str:
    """
    Get the current wizard step identifier.
    
    Args:
        session_state: Session state containing wizard data
        
    Returns:
        Current step identifier string
        
    Examples:
        >>> state = {WIZ_KEY: {"current_step": "product_vision"}}
        >>> current_step(state)
        "product_vision"
    """
    return session_state[WIZ_KEY]["current_step"]

def move_to(session_state: Dict[str, Any], step: str) -> None:
    """
    Move wizard to a specific step.
    
    Args:
        session_state: Session state containing wizard data
        step: Target step identifier
        
    Examples:
        >>> state = {WIZ_KEY: {"current_step": "project_name"}}
        >>> move_to(state, "product_vision")
        >>> current_step(state)
        "product_vision"
    """
    session_state[WIZ_KEY]["current_step"] = step

def validate_project_name(name: str) -> Tuple[bool, str | None]:
    """
    Validate project name with user-friendly error messages.
    
    This function provides UI-level validation for project names with
    Portuguese error messages suitable for user display.
    
    Validation Rules:
        - Must be a string type
        - Must contain at least 3 characters after trimming whitespace
        
    Args:
        name: Project name string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if validation passes
        - error_message: Portuguese error message (None if valid)
        
    Examples:
        >>> validate_project_name("Valid Name")
        (True, None)
        
        >>> validate_project_name("AB")
        (False, "Informe um nome com pelo menos 3 caracteres.")
        
        >>> validate_project_name(None)
        (False, "Nome inválido.")
    """
    if name is None or not isinstance(name, str):
        return False, "Nome inválido."
    trimmed = name.strip()
    if len(trimmed) < 3:
        return False, "Informe um nome com pelo menos 3 caracteres."
    return True, None

def advance_from_name(session_state: Dict[str, Any], name: str) -> Tuple[bool, str | None]:
    """
    Handle advancement from project name step to product vision step.
    
    This function processes the "Continue" button action from the project
    name step, performing validation and state transition if successful.
    
    Workflow:
        1. Validate the provided project name
        2. Store validated name in project draft
        3. Advance to product_vision step
        4. Return success/failure status
    
    Args:
        session_state: Session state containing wizard data
        name: Project name entered by user
        
    Returns:
        Tuple of (success, error_message)
        - success: True if advancement was successful
        - error_message: Portuguese error message (None if successful)
        
    Examples:
        >>> state = {WIZ_KEY: {"current_step": "project_name", "project_draft": {}}}
        >>> success, error = advance_from_name(state, "My Project")
        >>> success
        True
        >>> state[WIZ_KEY]["current_step"]
        "product_vision"
        >>> state[WIZ_KEY]["project_draft"]["name"]
        "My Project"
        
        >>> success, error = advance_from_name(state, "AB")
        >>> success
        False
        >>> "3 caracteres" in error
        True
    """
    ok, msg = validate_project_name(name)
    if not ok:
        return False, msg
    session_state[WIZ_KEY]["project_draft"]["name"] = name.strip()
    move_to(session_state, "product_vision")
    return True, None
