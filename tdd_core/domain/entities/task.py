"""
Task Entity (História 1.2)

Framework-independent domain entity representing a Task.
Includes TDD workflow and TDAH support fields with basic validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Task:
    """Entidade Task com suporte TDD e TDAH."""

    # Campos obrigatórios (sem defaults)
    epic_id: int
    key: str
    name: str
    description: str

    # Identificação/Status
    id: Optional[int] = None
    user_story_id: Optional[int] = None  # vínculo explícito com UserStory
    status: str = "todo"  # todo/in_progress/done/blocked/pending
    tdd_status: str = "pending"  # pending/red/green/refactor

    # Métricas TDD
    test_coverage: float = 0.0  # 0-100
    tests_passing: int = 0
    tests_total: int = 0
    tests_failing: int = 0

    # TDAH Support
    focus_rating: Optional[int] = None  # 1-5
    interruption_count: int = 0
    energy_level: Optional[str] = None  # low/medium/high
    estimated_duration: Optional[int] = None  # minutos
    actual_duration: Optional[int] = None  # minutos

    # Prioridade e complexidade
    priority: int = 3  # 1-5
    complexity: int = 3  # 1-5
    story_points: Optional[int] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

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
        if not isinstance(self.name, str) or not self.name.strip():
            errors.append("name is required and cannot be empty")
        if not isinstance(self.description, str) or not self.description.strip():
            errors.append("description is required and cannot be empty")

        # Status válidos (inclui 'pending' para compatibilidade)
        valid_statuses = ["todo", "in_progress", "done", "blocked", "pending"]
        if self.status not in valid_statuses:
            errors.append(f"status must be one of {valid_statuses}")

        # TDD status
        valid_tdd = ["pending", "red", "green", "refactor"]
        if self.tdd_status not in valid_tdd:
            errors.append(f"tdd_status must be one of {valid_tdd}")

        # Cobertura de testes
        if not (0.0 <= float(self.test_coverage) <= 100.0):
            errors.append("test_coverage must be between 0 and 100")

        # Counters não-negativos e consistência básica
        for fname in ("tests_passing", "tests_total", "tests_failing"):
            if getattr(self, fname) < 0:
                errors.append(f"{fname} must be non-negative")
        if self.tests_passing + self.tests_failing > self.tests_total:
            errors.append("tests_passing + tests_failing must be <= tests_total")

        # TDAH
        if self.focus_rating is not None and not (1 <= int(self.focus_rating) <= 5):
            errors.append("focus_rating must be between 1 and 5")
        if self.energy_level and self.energy_level not in ["low", "medium", "high"]:
            errors.append("energy_level must be one of ['low', 'medium', 'high']")
        if self.estimated_duration is not None and self.estimated_duration < 0:
            errors.append("estimated_duration must be non-negative")
        if self.actual_duration is not None and self.actual_duration < 0:
            errors.append("actual_duration must be non-negative")

        # Prioridade/complexidade/story_points
        if not (1 <= int(self.priority) <= 5):
            errors.append("priority must be between 1 and 5")
        if not (1 <= int(self.complexity) <= 5):
            errors.append("complexity must be between 1 and 5")
        if self.story_points is not None and self.story_points <= 0:
            errors.append("story_points must be > 0 when provided")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    def is_tdd_complete(self) -> bool:
        return self.tdd_status == "refactor" and float(self.test_coverage) > 80.0

    def mark_interrupted(self) -> None:
        self.interruption_count += 1
        self.updated_at = datetime.now()

    def calculate_efficiency(self) -> Optional[float]:
        if self.estimated_duration and self.actual_duration and self.actual_duration > 0:
            return (self.estimated_duration / self.actual_duration) * 100.0
        return None
