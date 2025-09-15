"""Domain Entities - Core Business Objects

Entities represent the core concepts of the business domain with identity.
All entities are framework-independent and contain business logic.

Available entities:
    - ProductVision: Product vision (16 fields, must_have/cannot_have)
    - Project: Project hub with wizard metadata and metrics
    - Epic: Epic with AI fields and topological ordering metadata
    - Task: Task with TDD workflow and TDAH support

Status: História 1.2 Complete - Entities Extracted
"""

from .product_vision import ProductVision
from .project import Project
from .epic import Epic
from .task import Task
from .user_story import UserStory

__all__: list[str] = [
    "ProductVision",
    "Project",
    "Epic",
    "Task",
    "UserStory",
]
