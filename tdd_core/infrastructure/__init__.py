"""
Infrastructure Layer - External Interfaces and Implementations

This layer contains adapters and implementations that connect the core
business logic to external frameworks, databases, and services.

Components (to be implemented in future stories):
    - adapters: Framework adapters (Streamlit, FastAPI, CLI) (História 3.1)
    - mappers: Data transformation between layers (História 3.2)
    - repositories: Concrete repository implementations (História 3.3)
    - ai: AI service implementations and configurations (História 2.3)

Principles:
    - Implements domain interfaces
    - Framework specific code allowed
    - Dependency injection ready
    - Easily replaceable implementations
    - Plugin architecture

Dependencies: domain + application layers

Status: História 1.1 - Structure Ready
Next: História 3.1 - StreamlitAdapter Creation
"""

# Future imports (to be populated in História 3.x)
# from .adapters import StreamlitAdapter
# from .mappers import ProductVisionMapper, EpicMapper
# from .repositories import SQLiteProjectRepository
# from .ai import OpenAIService, MockAIService

__all__: list[str] = []  # Will be populated in História 3.x

# Layer metadata
LAYER_INFO = {
    "name": "infrastructure",
    "description": "External interfaces and implementations",
    "dependencies": ["domain", "application"],
    "principles": ["Adapter Pattern", "Dependency Injection", "Plugin Architecture"],
    "status": "História 1.1 Complete - Structure Ready",
}
