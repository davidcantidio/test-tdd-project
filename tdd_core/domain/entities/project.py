"""
Project Entity (História 1.2)

Framework-independent domain entity representing a Project.
Includes wizard metadata, simple metrics and basic validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Project:
    """Entidade Project - Hub central do domínio.

    Observações:
        - Não acoplar a frameworks/banco; mapeamento fica em adapters/repositórios.
        - Status padrão alinhado ao banco: 'planning'.
        - Metadados de wizard são domínio; persistência pode ser adicionada depois.
    """

    # Campos obrigatórios (sem defaults)
    name: str
    description: str

    # Identificação e status
    id: Optional[int] = None
    status: str = "planning"  # planning/active/on_hold/completed/cancelled/archived

    # Relacionamento com ProductVision
    vision_id: Optional[int] = None

    # Metadados do wizard (domínio)
    wizard_completed: bool = False
    current_phase: str = "roteiro"  # roteiro/capitulos/historias/tarefas
    phases_completed: List[str] = field(default_factory=list)

    # Métricas simples (domínio)
    total_epics: int = 0
    completed_epics: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    progress_percentage: float = 0.0

    # Auditoria
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()

    def validate(self) -> List[str]:
        errors: List[str] = []

        # Campos obrigatórios
        if not isinstance(self.name, str) or not self.name.strip():
            errors.append("name is required and cannot be empty")

        # Status permitido (alinhado ao sistema)
        valid_statuses = [
            "planning",
            "active",
            "on_hold",
            "completed",
            "cancelled",
            "archived",
        ]
        if self.status not in valid_statuses:
            errors.append(f"status must be one of {valid_statuses}")

        # Fases do wizard (domínio)
        valid_phases = ["roteiro", "capitulos", "historias", "tarefas"]
        if self.current_phase not in valid_phases:
            errors.append(f"current_phase must be one of {valid_phases}")

        # Progress bounds
        if self.progress_percentage < 0 or self.progress_percentage > 100:
            errors.append("progress_percentage must be between 0 and 100")

        # Métricas não-negativas
        for fname in ("total_epics", "completed_epics", "total_tasks", "completed_tasks"):
            if getattr(self, fname) < 0:
                errors.append(f"{fname} must be non-negative")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    def calculate_progress(self) -> float:
        if self.total_tasks <= 0:
            return 0.0
        return (self.completed_tasks / float(self.total_tasks)) * 100.0

    def mark_phase_complete(self, phase: str) -> None:
        if phase not in self.phases_completed:
            self.phases_completed.append(phase)
        self.updated_at = datetime.now()

    def is_wizard_complete(self) -> bool:
        return self.wizard_completed

