"""
Relations Adapter

Convenience functions to traverse domain relationships using repositories.
Useful for UI/API layers to fetch hierarchical data with minimal wiring.
"""

from __future__ import annotations

import sqlite3
from typing import List

from ..repositories import EpicRepository, UserStoryRepository, TaskRepository
from ...domain.entities import Epic, UserStory, Task


def get_epics_for_product_vision(conn: sqlite3.Connection, product_vision_id: int) -> List[Epic]:
    return EpicRepository(conn).list_by_product_vision_id(product_vision_id)


def get_user_stories_for_epic(conn: sqlite3.Connection, epic_id: int) -> List[UserStory]:
    return UserStoryRepository(conn).list_by_epic_id(epic_id)


def get_tasks_for_user_story(conn: sqlite3.Connection, user_story_id: int) -> List[Task]:
    return TaskRepository(conn).list_by_user_story_id(user_story_id)


__all__ = [
    "get_epics_for_product_vision",
    "get_user_stories_for_epic",
    "get_tasks_for_user_story",
]

