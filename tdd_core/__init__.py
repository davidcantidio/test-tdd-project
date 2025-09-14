"""
TDD Core - Domain Layer for TDD Project

Clean Architecture implementation following Domain-Driven Design principles.
Provides isolated business logic foundation for API-first migration.

Architecture:
    - domain: Pure business logic (entities, value objects, exceptions)
    - application: Use cases and services (orchestration layer)  
    - infrastructure: External interfaces (adapters, repositories, AI)

Version: 1.0.0
Author: TDD Project Team
License: MIT

Status: História 1.1 - Structure Complete ✅
Next: História 1.2 - Domain Extraction
"""

__version__ = "1.0.0"
__author__ = "TDD Project Team"
__license__ = "MIT"

# Layer imports (basic structure available)
from . import application, domain, infrastructure

# Placeholder specific imports - will be populated in future stories
# from .domain import entities, value_objects, exceptions
# from .application import services, dto, validators
# from .infrastructure import adapters, mappers, repositories

__all__: list[str] = []  # Will be populated as components are implemented

# Module metadata for introspection
MODULE_INFO = {
    "name": "tdd_core",
    "version": __version__,
    "architecture": "Clean Architecture + DDD",
    "layers": ["domain", "application", "infrastructure"],
    "python_version": "^3.11",
    "dependencies": ["pydantic>=2.0", "typing-extensions>=4.0"],
    "status": "História 1.1 Complete",
}


def get_version() -> str:
    """Return the current version of tdd_core."""
    return __version__


def get_info() -> dict:
    """Return basic module information."""
    return {
        "name": "tdd_core",
        "version": __version__,
        "architecture": "Clean Architecture + DDD",
        "layers": ["domain", "application", "infrastructure"],
        "status": "História 1.1 Complete - Structure Ready",
    }


def get_architecture_info() -> dict:
    """Return detailed architecture information for debugging."""
    return MODULE_INFO.copy()
