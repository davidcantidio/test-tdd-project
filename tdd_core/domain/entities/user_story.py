"""
UserStory Entity (História 1.2.x)

Framework-independent domain entity representing a User Story.
Maps conceptually to the framework_user_stories table.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class UserStory:
    """Entidade UserStory com validação básica.

    Campos obrigatórios:
        - epic_id, key, title, narrative, acceptance_criteria
    """

    # Obrigatórios
    epic_id: int
    key: str  # mapeia para story_key
    title: str
    narrative: str  # mapeia para user_story ("Como [usuário]...")
    acceptance_criteria: List[str]

    # Opcionais
    id: Optional[int] = None
    status: str = "backlog"  # backlog, ... conforme workflow
    workflow_stage: str = "discovery"  # discovery, analysis, ready, development, testing, done
    story_points: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()

    def validate(self) -> List[str]:
        errors: List[str] = []

        # Obrigatórios
        if not isinstance(self.epic_id, int) or self.epic_id <= 0:
            errors.append("epic_id is required")
        if not isinstance(self.key, str) or not self.key.strip():
            errors.append("key is required and cannot be empty")
        if not isinstance(self.title, str) or not self.title.strip():
            errors.append("title is required and cannot be empty")
        if not isinstance(self.narrative, str) or not self.narrative.strip():
            errors.append("narrative is required and cannot be empty")
        if not isinstance(self.acceptance_criteria, list) or len(self.acceptance_criteria) == 0:
            errors.append("acceptance_criteria is required and cannot be empty")
        else:
            for i, item in enumerate(self.acceptance_criteria):
                if not isinstance(item, str) or not item.strip():
                    errors.append(f"acceptance_criteria[{i}] must be a non-empty string")
                    break

        # Status/workflow válidos (subset do schema)
        valid_status = ["backlog", "ready", "development", "testing", "done"]
        if self.status not in valid_status:
            errors.append(f"status must be one of {valid_status}")
        valid_stages = ["discovery", "analysis", "ready", "development", "testing", "done"]
        if self.workflow_stage not in valid_stages:
            errors.append(f"workflow_stage must be one of {valid_stages}")

        if self.story_points is not None and self.story_points <= 0:
            errors.append("story_points must be > 0 when provided")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

