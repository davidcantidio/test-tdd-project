"""🔍 Form Validation Module

Centraliza validações de formulários:
- Campos obrigatórios
- Regras de negócio
- Formatos (email, telefone)
- Sanitização de entradas
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

try:
    from .security import sanitize_input, validate_form
except ImportError:  # pragma: no cover
    sanitize_input = lambda x, field_name="input": x  # type: ignore
    validate_form = None

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_RE = re.compile(r"^[+\d][\d\s().-]{7,}$")

__all__ = [
    "validate_required_fields", "validate_email_format", "validate_phone_format",
    "validate_text_length", "validate_business_rules_client",
    "validate_business_rules_project", "sanitize_form_inputs",
]


def validate_required_fields(data: Dict[str, Any], required_fields: Iterable[str]) -> List[str]:
    """Valida se campos obrigatórios existem e não são vazios/whitespace."""
    errors: List[str] = []
    for field in required_fields:
        value = data.get(field)
        if value is None:
            errors.append(f"Missing required field: {field}")
        elif isinstance(value, str) and value.strip() == "":
            errors.append(f"Missing required field: {field}")
    return errors


def validate_email_format(email: str) -> bool:
    """Valida formato de email (regex pré-compilado e fullmatch)."""
    if not email:
        return False
    return EMAIL_RE.fullmatch(email) is not None


def validate_phone_format(phone: str) -> bool:
    """Valida telefone (compatível internacional)."""
    if not phone:
        return False
    return PHONE_RE.fullmatch(phone) is not None


def validate_text_length(text: str, min_len: int, max_len: int, field_name: str) -> List[str]:
    """Validate text length constraints."""
    errors: List[str] = []
    text = text or ""
    if len(text) < min_len:
        errors.append(f"{field_name} must be at least {min_len} characters")
    if len(text) > max_len:
        errors.append(f"{field_name} must be at most {max_len} characters")
    return errors


def validate_business_rules_client(data: Dict[str, Any]) -> List[str]:
    """Validate business rules specific to client entities."""
    errors: List[str] = []
    errors.extend(validate_text_length(data.get("client_key", ""), 2, 50, "client_key"))
    errors.extend(validate_text_length(data.get("name", ""), 1, 255, "name"))
    return errors


def validate_business_rules_project(data: Dict[str, Any]) -> List[str]:
    """Validate business rules specific to project entities."""
    errors: List[str] = []
    errors.extend(validate_text_length(data.get("project_key", ""), 2, 50, "project_key"))
    errors.extend(validate_text_length(data.get("name", ""), 1, 255, "name"))
    return errors


def sanitize_form_inputs(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitiza todas as entradas string; preserva None e tipos primitivos.

    Observação: `validate_form` (se existir) roda após sanitização.
    """
    sanitized: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_input(value, key)
        else:
            sanitized[key] = value

    if validate_form:
        validate_form(sanitized)  # type: ignore[misc]
    return sanitized