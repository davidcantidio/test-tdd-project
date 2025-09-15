"""
UserStory Mapper

Maps between database rows and the UserStory domain entity.
Targets framework_user_stories table.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, MutableMapping, List

from ...domain.entities.user_story import UserStory


class UserStoryMapper:
    @staticmethod
    def from_db_row(row: Mapping[str, Any]) -> UserStory:
        def get(key: str, default: Any = None) -> Any:
            if hasattr(row, "keys"):
                try:
                    return row[key]
                except Exception:
                    return default
            if hasattr(row, "get"):
                return row.get(key, default)
            return default

        criteria_raw = get("acceptance_criteria", "[]")
        try:
            criteria: List[str] = json.loads(criteria_raw) if criteria_raw else []
            if not isinstance(criteria, list):
                criteria = []
        except Exception:
            criteria = []

        return UserStory(
            epic_id=int(get("epic_id", 0)),
            key=str(get("story_key", "")),
            title=str(get("title", "")),
            narrative=str(get("user_story", "")),
            acceptance_criteria=criteria,
            id=get("id", None),
            status=str(get("status", "backlog")),
            workflow_stage=str(get("workflow_stage", "discovery")),
            story_points=int(get("story_points", 0) or 0) or None,
            description=str(get("description", "")) or None,
            created_at=get("created_at", None),
            updated_at=get("updated_at", None),
        )

    @staticmethod
    def to_db_fields(entity: UserStory) -> MutableMapping[str, Any]:
        return {
            "id": entity.id,
            "epic_id": entity.epic_id,
            "story_key": entity.key,
            "title": entity.title,
            "user_story": entity.narrative,
            "acceptance_criteria": json.dumps(entity.acceptance_criteria),
            "status": entity.status,
            "workflow_stage": entity.workflow_stage,
            "story_points": entity.story_points,
            "description": entity.description,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }


__all__ = ["UserStoryMapper"]

