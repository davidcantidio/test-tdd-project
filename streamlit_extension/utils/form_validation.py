"""
🔍 Form Validation Module

Centralized validation functions for form components:
- Required field validation
- Business rules validation
- Format validation (email, phone)
- Input sanitization
"""

import re
from typing import Dict, List, Optional, Any

try:
    from .security import sanitize_input, validate_form
except ImportError:  # pragma: no cover
    sanitize_input = lambda x, field_name="input": x  # type: ignore
    validate_form = None


def validate_required_fields(data: Dict, required_fields: List[str]) -> List[str]:
    """Validate that required fields are present and non-empty."""
    errors = []
    for field in required_fields:
        if not data.get(field):
            errors.append(f"Missing required field: {field}")
    return errors


def validate_email_format(email: str) -> bool:
    """Validate email format using regex pattern."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email or ""))


def validate_phone_format(phone: str) -> bool:
    """Validate phone number format (international compatible)."""
    pattern = r"^[+\d][\d\s().-]{7,}$"
    return bool(re.match(pattern, phone or ""))


def validate_text_length(text: str, min_len: int, max_len: int, field_name: str) -> List[str]:
    """Validate text length constraints."""
    errors = []
    text = text or ""
    if len(text) < min_len:
        errors.append(f"{field_name} must be at least {min_len} characters")
    if len(text) > max_len:
        errors.append(f"{field_name} must be at most {max_len} characters")
    return errors


def validate_business_rules_client(data: Dict) -> List[str]:
    """Validate business rules specific to client entities."""
    errors: List[str] = []
    errors.extend(validate_text_length(data.get("client_key", ""), 2, 50, "client_key"))
    errors.extend(validate_text_length(data.get("name", ""), 1, 255, "name"))
    return errors


def validate_business_rules_project(data: Dict) -> List[str]:
    """Validate business rules specific to project entities."""
    errors: List[str] = []
    errors.extend(validate_text_length(data.get("project_key", ""), 2, 50, "project_key"))
    errors.extend(validate_text_length(data.get("name", ""), 1, 255, "name"))
    return errors


def sanitize_form_inputs(data: Dict) -> Dict:
    """Sanitize all form inputs for security."""
    sanitized: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_input(value, key)
        else:
            sanitized[key] = value
    
    # Apply additional form validation if available
    if validate_form:
        validate_form(sanitized)
    
    return sanitized