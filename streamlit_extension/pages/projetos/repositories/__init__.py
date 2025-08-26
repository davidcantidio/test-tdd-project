# streamlit_extension/pages/projetos/repositories/__init__.py
"""
💾 Repository Layer - Data Persistence Abstraction

This package implements the Repository Pattern to provide a clean abstraction
over data persistence mechanisms. Repositories encapsulate data access logic
and provide a more object-oriented view of the persistence layer.

Repository Pattern Benefits:
    - Database implementation abstraction
    - Testability through interface substitution
    - Flexibility to change persistence mechanisms
    - Clear separation between business and data access logic

Repository Responsibilities:
    - Data entity persistence and retrieval
    - Query encapsulation and optimization
    - Data mapping between domain entities and persistence models
    - Transaction boundary management at the data level

Available Repositories:
    - ProductVisionRepository (Abstract Interface):
        * save_draft(): Persist Product Vision draft
        * get_by_project_id(): Retrieve by project identifier
        * get_by_id(): Retrieve by entity identifier
        * delete_by_project_id(): Remove by project identifier

    - InMemoryProductVisionRepository:
        * In-memory implementation for testing/development
        * Fast, no external dependencies
        * Ideal for unit tests and prototyping

    - DatabaseProductVisionRepository:
        * SQLite-based production implementation
        * Integrated with existing database infrastructure
        * Full ACID transaction support

Usage Example:
    >>> from .product_vision_repository import InMemoryProductVisionRepository
    >>> repo = InMemoryProductVisionRepository()
    >>> entity = ProductVisionEntity(vision_statement="Build great software")
    >>> saved_entity = repo.save_draft(entity)
    >>> retrieved = repo.get_by_id(saved_entity.id)

Architecture Integration:
    Controllers → Repositories → Data Storage
    
    Repositories are injected into controllers to maintain dependency
    inversion and enable easy testing with mock implementations.

Testing Strategy:
    - Unit tests use InMemoryProductVisionRepository
    - Integration tests use DatabaseProductVisionRepository
    - Repository interfaces enable test doubles and mocking
"""

from .product_vision_repository import InMemoryProductVisionRepository

__all__ = ["InMemoryProductVisionRepository"]
