"""
📄 UI Actions - User Interface Action Handlers

This module contains UI action handlers that bridge user interface interactions
with business logic. Actions are responsible for handling user inputs,
coordinating with controllers, and managing UI state transitions.

UI Layer Responsibilities:
    - Handle user interface events and interactions
    - Validate user inputs at the UI level
    - Coordinate with controller layer for business operations  
    - Manage navigation and UI state transitions
    - Provide user feedback and error handling

Clean Architecture Compliance:
    - Focuses on UI concerns and user experience
    - Delegates business logic to controller layer
    - Handles UI-specific validation and formatting
    - Manages application navigation and routing

Usage:
    Actions are called by Streamlit UI components in response to user
    interactions such as button clicks, form submissions, and navigation.
"""

from typing import Dict, Tuple

# Business rule: minimum project name length
MIN_NAME_LEN = 3


def validate_project_name(name: str) -> bool:
    """
    Validate project name at the UI level for immediate user feedback.
    
    This function provides quick validation of project names for immediate
    user interface feedback before delegating to more comprehensive
    business rule validation in the domain layer.
    
    UI Validation Rules:
        - Must be a valid string type
        - Must contain at least 3 characters after trimming whitespace
        - Provides immediate feedback for user experience
    
    Args:
        name: Project name string to validate
        
    Returns:
        True if name passes UI-level validation, False otherwise
        
    Examples:
        >>> validate_project_name("Valid Project Name")
        True
        
        >>> validate_project_name("AB")  # Too short
        False
        
        >>> validate_project_name("   ")  # Only whitespace
        False
        
        >>> validate_project_name(123)  # Wrong type
        False
        
    Note:
        This is UI-level validation for immediate feedback. More comprehensive
        validation should be performed by domain services before persistence.
    """
    if not isinstance(name, str):
        return False
    name = name.strip()
    return len(name) >= MIN_NAME_LEN

def _empty_product_vision() -> Dict:
    """
    Create empty Product Vision structure for new project drafts.
    
    This private function provides the initial structure for a new
    Product Vision, following the domain model while serving UI needs
    for form initialization and state management.
    
    Returns:
        Dictionary with empty Product Vision fields
        
    Note:
        This function serves UI initialization needs. The authoritative
        empty Product Vision structure is defined in the domain layer.
    """
    return {
        "vision_statement": "",
        "problem_statement": "",
        "target_audience": "",
        "value_proposition": "",
        "constraints": [],
    }


def create_new_project_draft(name: str) -> Tuple[Dict, str]:
    """
    Create a new project draft with initial Product Vision structure.
    
    This action handler creates a new project draft for the wizard workflow,
    performing UI-level validation and setting up the initial project structure
    with an empty Product Vision ready for user input.
    
    Args:
        name: Project name provided by the user
        
    Returns:
        Tuple containing:
        - draft: Project draft dictionary with initial structure
        - route: Navigation route name for the wizard ("projeto_wizard")
        
    Raises:
        ValueError: If project name fails UI validation rules
        
    Examples:
        >>> draft, route = create_new_project_draft("My New Project")
        >>> draft["name"]
        "My New Project"
        >>> draft["current_phase"]
        "product_vision"
        >>> route
        "projeto_wizard"
        
        >>> create_new_project_draft("AB")  # Too short
        Traceback (most recent call last):
        ...
        ValueError: Nome do projeto inválido (mínimo 3 caracteres).
        
    UI Flow:
        1. User enters project name in UI
        2. This action validates name and creates draft
        3. UI navigates to wizard route for Product Vision input
        4. Draft serves as initial state for wizard workflow
        
    Data Structure:
        The returned draft contains:
        - id: None (not yet persisted)
        - name: Validated and trimmed project name
        - current_phase: "product_vision" (initial wizard phase)
        - product_vision: Empty structure ready for user input
    """
    if not validate_project_name(name):
        raise ValueError("Nome do projeto inválido (mínimo 3 caracteres).")

    draft: Dict = {
        "id": None,                # Not yet persisted to storage
        "name": name.strip(),
        "current_phase": "product_vision",
        "product_vision": _empty_product_vision(),
    }
    return draft, "projeto_wizard"
