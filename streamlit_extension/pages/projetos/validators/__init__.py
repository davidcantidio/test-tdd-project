"""
Módulo de validação para Product Vision e Epic Suggestions.

Este módulo implementa funções de validação independentes que podem ser
reutilizadas em diferentes partes do sistema.
"""

from .product_vision_validator import (
    validate_product_vision_dto,
    normalize_constraint_list
)

from .epic_suggestion_validator import (
    validate_epic_suggestion_dto,
    normalize_tag_list,
    validate_confidence_range,
    validate_source_type
)

__all__ = [
    # Product Vision validators
    'validate_product_vision_dto',
    'normalize_constraint_list',
    # Epic Suggestion validators
    'validate_epic_suggestion_dto',
    'normalize_tag_list',
    'validate_confidence_range',
    'validate_source_type'
]