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
from .sqlite_epic_repository import EpicRepository
from .sqlite_task_repository import TaskRepository
from .sqlite_user_story_repository import UserStoryRepository

__all__: list[str] = [
    "ProductVisionRepository",
    "EpicRepository",
    "TaskRepository",
    "UserStoryRepository",
]
