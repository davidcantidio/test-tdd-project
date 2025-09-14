"""
Domain Layer - Pure Business Logic

This layer contains the core business logic of the TDD Enterprise Framework.
It has NO dependencies on external frameworks or infrastructure.

Components (to be implemented in future stories):
    - entities: Core business objects with identity (História 1.2)
    - value_objects: Immutable descriptive objects (História 1.3)
    - exceptions: Domain-specific exceptions
    - repositories: Abstract interfaces for data access

Principles:
    - No framework dependencies
    - Rich domain model  
    - Business rules encapsulated
    - Testable without infrastructure
    - Framework independence

Status: História 1.1 - Structure Ready
Next: História 1.2 - Domain Entities Extraction
"""

# Future imports will be added as entities are created
# from .entities import ProductVision, Project, Epic, Task
# from .value_objects import Priority, TddPhase, ComplexityScore
# from .exceptions import DomainError, ValidationError
# from .repositories import IProjectRepository, IEpicRepository

__all__: list[str] = []  # Will be populated in História 1.2-1.3

# Layer metadata
LAYER_INFO = {
    "name": "domain",
    "description": "Pure business logic layer",
    "dependencies": [],  # No external dependencies allowed
    "principles": ["DDD", "Rich Domain Model", "Framework Independence"],
    "status": "História 1.1 Complete - Structure Ready",
}
