"""Infrastructure Repository Implementations

Concrete implementations of domain repository interfaces.

Future repositories (História 3.3):
    - SQLiteProjectRepository: SQLite project data access
    - SQLiteEpicRepository: SQLite epic data access with topological sorting
    - SQLiteTaskRepository: SQLite task data access
    - SQLitePrioritySettingsRepository: Priority weights persistence

Status: História 1.1 Complete - Structure Ready  
Next: História 3.3 - Repository Implementation
"""

from .sqlite_product_vision_repository import ProductVisionRepository

__all__: list[str] = [
    "ProductVisionRepository",
]
