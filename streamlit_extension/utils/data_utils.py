"""
🔄 Data Normalization Utilities

Safe data conversion and normalization helpers.
Extracted from streamlit_helpers.py for better modularity.
"""

from __future__ import annotations

from typing import Any, Dict, List
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


# === DATA NORMALIZATION HELPERS ===========================================

def ensure_list(value: Any) -> List[Any]:
    """
    Ensure value is a list, handling various data formats.
    
    Args:
        value: Value to normalize to list
        
    Returns:
        List representation of value
    """
    if isinstance(value, list):
        return value
    
    if isinstance(value, dict) and "data" in value:
        data = value.get("data") or []
        return data if isinstance(data, list) else []
    
    if value is None:
        return []
    
    # Single value -> wrap in list
    return [value]

def ensure_dict(value: Any) -> Dict[str, Any]:
    """
    Ensure value is a dictionary.
    
    Args:
        value: Value to normalize to dict
        
    Returns:
        Dictionary representation of value
    """
    if isinstance(value, dict):
        return value
    
    if value is None:
        return {}
    
    # Try to convert to dict if possible
    try:
        if hasattr(value, "__dict__"):
            return value.__dict__
        elif hasattr(value, "_asdict"):  # namedtuple
            return value._asdict()
        else:
            return {"value": value}
    except Exception:
        return {"value": str(value)}

def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary with fallback.
    
    Args:
        data: Dictionary to get value from
        key: Key to retrieve
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    if not isinstance(data, dict):
        return default
    
    return data.get(key, default)

def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to integer.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_str(value: Any, default: str = "") -> str:
    """
    Safely convert value to string.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        String value or default
    """
    try:
        if value is None:
            return default
        return str(value)
    except Exception:
        return default

# === EXPORTS ==============================================================

__all__ = [
    # Data normalization
    "ensure_list",
    "ensure_dict",
    "safe_get",
    "safe_int",
    "safe_float", 
    "safe_str",
]