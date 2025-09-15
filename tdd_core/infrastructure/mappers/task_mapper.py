"""
Task Mapper

Maps between database rows and the Task domain entity.
Assumes framework_tasks has standard columns (task_key, title, tdd_phase, etc.).
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping

from ...domain.entities.task import Task


class TaskMapper:
    """Mapper entre linha de banco e entidade Task."""

    @staticmethod
    def from_db_row(row: Mapping[str, Any]) -> Task:
        def get(key: str, default: Any = None) -> Any:
            if hasattr(row, "keys"):
                try:
                    return row[key]
                except Exception:
                    return default
            if hasattr(row, "get"):
                return row.get(key, default)
            return default

        return Task(
            epic_id=int(get("epic_id", 0)),
            key=str(get("task_key", "")),
            name=str(get("title", "")),
            description=str(get("description", "")),
            id=get("id", None),
            user_story_id=get("user_story_id", None),
            status=str(get("status", "todo")),
            tdd_status=str(get("tdd_phase", "pending")),
            estimated_duration=int(get("estimate_minutes", 0) or 0) or None,
            actual_duration=int(get("actual_minutes", 0) or 0) or None,
            story_points=int(get("story_points", 0) or 0) or None,
            created_at=get("created_at", None),
            updated_at=get("updated_at", None),
        )

    @staticmethod
    def to_db_fields(entity: Task) -> MutableMapping[str, Any]:
        return {
            "id": entity.id,
            "epic_id": entity.epic_id,
            "user_story_id": entity.user_story_id,
            "task_key": entity.key,
            "title": entity.name,
            "description": entity.description,
            "status": entity.status,
            "tdd_phase": entity.tdd_status,
            "estimate_minutes": entity.estimated_duration,
            "actual_minutes": entity.actual_duration,
            "story_points": entity.story_points,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }


__all__ = ["TaskMapper"]
