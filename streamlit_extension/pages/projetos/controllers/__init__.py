# streamlit_extension/pages/projetos/controllers/__init__.py
"""
🎮 Controller Layer - Business Logic Orchestration

This package contains controllers that orchestrate business operations by
coordinating between the domain layer (pure business logic) and infrastructure
layer (repositories, external services). Controllers implement use cases and
application-specific business logic.

Controller Responsibilities:
    - Use case orchestration and workflow coordination
    - Domain logic coordination with infrastructure services
    - Transaction boundary management
    - Input validation and error handling delegation
    - Business operation sequencing

Key Principles:
    - Thin controllers that delegate to domain services
    - No direct UI dependencies (receive data, return data)
    - Coordinate between domain and infrastructure layers
    - Handle application-specific business workflows

Controllers Available:
    - ProductVisionController: Manages Product Vision business operations
        - Validation delegation to domain layer
        - AI service integration for refinement
        - Repository coordination for persistence
        - Business rule enforcement

Usage Pattern:
    UI Layer → Controller → Domain Layer
                ↓
         Infrastructure Layer (Repositories)

Example:
    >>> from .product_vision_controller import can_refine, build_summary
    >>> if can_refine(product_vision):
    ...     summary = build_summary(product_vision)
    ...     # Proceed with business operation

Architecture Notes:
    Controllers should be thin and focus on coordination rather than
    business logic implementation. Business rules belong in the domain layer,
    while technical concerns belong in the infrastructure layer.
"""