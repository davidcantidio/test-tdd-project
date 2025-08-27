# streamlit_extension/pages/projetos/project_wizard_state.py
"""
Project Wizard Global State Management

This module manages the overall wizard state across multiple steps and phases.
It complements the _pv_state.py module by providing wizard-level state management
while _pv_state.py focuses specifically on Product Vision state.

Features:
    - Multi-step wizard navigation state
    - Global wizard configuration and settings
    - Step validation and progression rules
    - Integration with Streamlit session state
    - Support for future wizard expansion

Architecture:
    This module works alongside:
    - _pv_state.py: Product Vision specific state
    - projeto_wizard.py: Main wizard orchestration
    - Individual step modules: Step-specific implementations
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import streamlit as st

# Wizard step configuration following official Streamlit pattern
WIZARD_STEPS = {
    1: "product_vision",
    # Future steps can be added here:
    # 2: "project_details", 
    # 3: "resources_budget",
    # 4: "team_setup",
    # 5: "review_create"
}

# Step metadata with validation requirements
STEP_METADATA = {
    1: {
        "name": "product_vision",
        "title": "Product Vision",
        "description": "Define the vision and scope of your product",
        "icon": "🎯",
        "required": True,
        "validation_function": "validate_product_vision_step"
    },
    # Future step metadata
    # 2: {
    #     "name": "project_details",
    #     "title": "Project Details", 
    #     "description": "Set project timeline, budget, and resources",
    #     "icon": "📋",
    #     "required": True,
    #     "validation_function": "validate_project_details_step"
    # }
}

# Default wizard state structure
DEFAULT_WIZARD_STATE: Dict[str, Any] = {
    "current_step": 1,
    "completed_steps": [],
    "project_name": "",
    "created_at": None,
    "last_modified": None,
    "wizard_version": "2.0",  # Updated to reflect multi-step implementation
}


def init_global_wizard_state(session_state) -> None:
    """
    Initialize global wizard state in Streamlit session state.
    
    This function ensures the wizard has proper global state structure,
    complementing the Product Vision specific state managed by _pv_state.py.
    
    Args:
        session_state: Streamlit session state object
        
    State Structure:
        - wizard_state: Global wizard configuration and navigation
        - Individual step states managed by respective modules
    """
    if "wizard_state" not in session_state:
        session_state.wizard_state = dict(DEFAULT_WIZARD_STATE)
        session_state.wizard_state["created_at"] = _get_current_timestamp()
    else:
        # Ensure all required keys are present
        for key, default_value in DEFAULT_WIZARD_STATE.items():
            session_state.wizard_state.setdefault(key, default_value)
    
    # Update last modified timestamp
    session_state.wizard_state["last_modified"] = _get_current_timestamp()


def get_current_step(session_state) -> int:
    """Get the current wizard step number."""
    return session_state.get("wizard_state", {}).get("current_step", 1)


def set_current_step(session_state, step: int) -> None:
    """Set the current wizard step with validation."""
    if "wizard_state" not in session_state:
        init_global_wizard_state(session_state)
    
    # Validate step number
    if step not in WIZARD_STEPS:
        raise ValueError(f"Invalid step number: {step}")
    
    session_state.wizard_state["current_step"] = step
    session_state.wizard_state["last_modified"] = _get_current_timestamp()


def mark_step_completed(session_state, step: int) -> None:
    """Mark a wizard step as completed."""
    if "wizard_state" not in session_state:
        init_global_wizard_state(session_state)
    
    completed_steps = session_state.wizard_state.setdefault("completed_steps", [])
    if step not in completed_steps:
        completed_steps.append(step)
        completed_steps.sort()  # Keep sorted for easier processing


def is_step_completed(session_state, step: int) -> bool:
    """Check if a wizard step has been completed."""
    completed_steps = session_state.get("wizard_state", {}).get("completed_steps", [])
    return step in completed_steps


def can_access_step(session_state, target_step: int) -> bool:
    """
    Determine if a user can access a specific wizard step.
    
    Business rules:
        - Step 1 is always accessible
        - Other steps require previous step completion or current step + 1
        
    Args:
        session_state: Streamlit session state
        target_step: Step number to check access for
        
    Returns:
        True if step can be accessed, False otherwise
    """
    if target_step == 1:
        return True  # First step always accessible
    
    current_step = get_current_step(session_state)
    
    # Can access current step or next step
    if target_step <= current_step + 1:
        return True
    
    # Can access if previous step is completed
    return is_step_completed(session_state, target_step - 1)


def get_step_info(step: int) -> Dict[str, Any]:
    """Get metadata information for a specific wizard step."""
    return STEP_METADATA.get(step, {
        "name": "unknown",
        "title": f"Step {step}",
        "description": "Unknown step",
        "icon": "❓",
        "required": False,
        "validation_function": None
    })


def get_wizard_progress(session_state) -> Dict[str, Any]:
    """
    Calculate wizard completion progress and status.
    
    Returns:
        Dictionary with progress information:
        - total_steps: Total number of wizard steps
        - current_step: Current active step
        - completed_steps: List of completed step numbers
        - progress_percentage: Completion percentage (0-100)
        - is_complete: Whether all steps are completed
    """
    total_steps = len(WIZARD_STEPS)
    current_step = get_current_step(session_state)
    completed_steps = session_state.get("wizard_state", {}).get("completed_steps", [])
    
    progress_percentage = (len(completed_steps) / total_steps) * 100
    is_complete = len(completed_steps) == total_steps
    
    return {
        "total_steps": total_steps,
        "current_step": current_step,
        "completed_steps": completed_steps,
        "progress_percentage": progress_percentage,
        "is_complete": is_complete,
        "next_step": current_step + 1 if current_step < total_steps else None,
        "prev_step": current_step - 1 if current_step > 1 else None
    }


def validate_step_data(session_state, step: int) -> Tuple[bool, Optional[str]]:
    """
    Validate data for a specific wizard step.
    
    This function delegates to step-specific validation functions
    defined in the STEP_METADATA configuration.
    
    Args:
        session_state: Streamlit session state
        step: Step number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    step_info = get_step_info(step)
    validation_function = step_info.get("validation_function")
    
    if not validation_function:
        return True, None  # No validation defined
    
    # Route to appropriate validation function
    if validation_function == "validate_product_vision_step":
        return _validate_product_vision_step(session_state)
    
    # Add more validation functions as needed
    # elif validation_function == "validate_project_details_step":
    #     return _validate_project_details_step(session_state)
    
    return True, None  # Default: assume valid


def _validate_product_vision_step(session_state) -> Tuple[bool, Optional[str]]:
    """Validate Product Vision step data."""
    # Check if Product Vision state exists and is complete
    if not hasattr(session_state, 'pv'):
        return False, "Product Vision data not initialized"
    
    pv_data = session_state.pv
    required_fields = ["vision_statement", "problem_statement", "target_audience", "value_proposition", "constraints"]
    
    for field in required_fields:
        if field == "constraints":
            constraints = pv_data.get(field, [])
            if not isinstance(constraints, list) or not constraints:
                return False, f"Campo '{field}' eh obrigatorio e deve conter ao menos uma restricao."
        else:
            value = pv_data.get(field, "")
            if not isinstance(value, str) or not value.strip():
                return False, f"Campo '{field}' eh obrigatorio."
    
    return True, None


def reset_wizard_state(session_state) -> None:
    """Reset wizard to initial state (useful for starting over)."""
    if "wizard_state" in session_state:
        del session_state.wizard_state
    
    # Reset Product Vision state if it exists
    if "pv" in session_state:
        del session_state.pv
    if "pv_mode" in session_state:
        del session_state.pv_mode  
    if "pv_step_idx" in session_state:
        del session_state.pv_step_idx
    
    # Reinitialize
    init_global_wizard_state(session_state)


def export_wizard_data(session_state) -> Dict[str, Any]:
    """
    Export complete wizard data for persistence or analysis.
    
    Returns:
        Dictionary containing all wizard data including:
        - Global wizard state
        - Product Vision data
        - Step completion status
        - Metadata and timestamps
    """
    wizard_data = {
        "wizard_state": session_state.get("wizard_state", {}),
        "product_vision": session_state.get("pv", {}),
        "pv_mode": session_state.get("pv_mode", "form"),
        "pv_step_idx": session_state.get("pv_step_idx", 0),
        "exported_at": _get_current_timestamp(),
        "wizard_version": "2.0"
    }
    
    return wizard_data


def import_wizard_data(session_state, wizard_data: Dict[str, Any]) -> bool:
    """
    Import wizard data from external source.
    
    Args:
        session_state: Streamlit session state
        wizard_data: Previously exported wizard data
        
    Returns:
        True if import successful, False otherwise
    """
    try:
        # Import global wizard state
        if "wizard_state" in wizard_data:
            session_state.wizard_state = wizard_data["wizard_state"]
        
        # Import Product Vision data
        if "product_vision" in wizard_data:
            session_state.pv = wizard_data["product_vision"]
        if "pv_mode" in wizard_data:
            session_state.pv_mode = wizard_data["pv_mode"]
        if "pv_step_idx" in wizard_data:
            session_state.pv_step_idx = wizard_data["pv_step_idx"]
        
        return True
    except Exception as e:
        st.error(f"Error importing wizard data: {e}")
        return False


def _get_current_timestamp() -> str:
    """Get current timestamp as ISO string."""
    from datetime import datetime
    return datetime.now().isoformat()


# Utility functions for wizard UI components
def get_step_button_type(current_step: int, target_step: int) -> str:
    """Determine button type for step navigation."""
    if target_step == current_step:
        return "primary"
    elif target_step < current_step:
        return "secondary"
    else:
        return "secondary"


def get_step_status_icon(session_state, step: int) -> str:
    """Get status icon for a wizard step."""
    current_step = get_current_step(session_state)
    
    if is_step_completed(session_state, step):
        return "✅"
    elif step == current_step:
        return "🔄"
    elif step < current_step:
        return "⏳"
    else:
        return "⭕"