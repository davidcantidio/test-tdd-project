# streamlit_extension/pages/projetos/domain/__init__.py
"""
🧠 Domain Layer - Pure Business Logic

This package contains the core business logic for the Project Wizard with
ZERO external dependencies. Following Clean Architecture principles, this
layer represents the heart of the business rules and is completely isolated
from UI frameworks, databases, and other infrastructure concerns.

Domain Responsibilities:
    - Product Vision business rules and validation
    - Pure data transformations and calculations  
    - Business invariants and constraints enforcement
    - Domain-specific error conditions and rules

Key Principles:
    - No dependencies on Streamlit, databases, or external services
    - Pure functions with deterministic behavior
    - High testability through isolation
    - Business rule centralization

Domain Entities:
    - Product Vision state management and validation
    - Business rule enforcement for project creation
    - Data normalization and transformation logic

Usage:
    This layer should only be imported by:
    - Controller Layer (for business logic orchestration)
    - Unit tests (for isolated business logic testing)
    
    Never import UI frameworks or persistence layers here.

Example:
    >>> from .product_vision_state import validate_product_vision
    >>> is_valid, errors = validate_product_vision(product_vision_data)
    >>> if is_valid:
    ...     # Business logic execution
    ...     pass

Architecture Notes:
    The domain layer is the most stable part of the system. Changes here
    should be rare and driven by actual business requirement changes,
    not technical considerations.
"""