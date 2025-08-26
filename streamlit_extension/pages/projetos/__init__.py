"""
🚀 Project Wizard Package - Clean Architecture Implementation

This package implements the Project Creation Wizard using Clean Architecture principles
for the TDD Enterprise Framework. It provides a comprehensive, AI-assisted interface 
for creating projects with proper setup and Product Vision definition.

Clean Architecture Layers:
    - UI Layer: Streamlit-specific components (actions, state, steps/)
    - Controller Layer: Business logic orchestration (controllers/)
    - Domain Layer: Pure business logic with zero dependencies (domain/)
    - Infrastructure Layer: Repository pattern implementations (repositories/)

Key Features:
    - Domain-Driven Design with clear layer separation
    - Repository Pattern for flexible data persistence
    - AI-powered Product Vision refinement
    - Type-safe interfaces and error handling
    - Zero circular dependencies

Usage:
    >>> from streamlit_extension.pages.projetos import render_projeto_wizard_page
    >>> render_projeto_wizard_page()

Architecture Example:
    UI Layer → Controller Layer → Domain Layer ← Infrastructure Layer
    
    The Domain layer is pure business logic with no external dependencies.
    Controllers orchestrate domain operations and coordinate with repositories.
    UI components handle user interaction and delegate to controllers.
    Repositories provide data persistence abstraction.

Note:
    This module follows Clean Architecture principles where dependencies
    point inward toward the domain layer, ensuring high testability and
    maintainability.
"""

from .projeto_wizard import render_projeto_wizard_page

__all__ = ["render_projeto_wizard_page"]

