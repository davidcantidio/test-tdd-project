"""
Epic Entity (História 1.2)

Clean, framework-independent domain entity representing an Epic.
Includes AI-related fields and topological ordering metadata.
Scoring logic is intentionally not part of the entity (handled by services).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Epic:
    """Entidade Epic com campos IA e ordenação topológica.

    Observações:
    - Cálculo de prioridade NÃO fica na entidade. Use PriorityScorer (camada de aplicação).
    - Mapeamento típico para o banco:
        • key -> epic_key
        • epic_dependencies -> tabela de junção (framework_epic_dependencies)
    """

    # Campos obrigatórios
    project_id: int
    key: str  # mapeia para epic_key no banco
    name: str
    description: str

    # Identificação e status
    id: Optional[int] = None
    product_vision_id: Optional[int] = None  # vínculo explícito com Product Vision
    status: str = "pending"
    priority: int = 3

    # Campos IA (Phase 5.1)
    ai_generated: bool = False
    ai_confidence: float = 0.0  # 0.0-1.0
    complexity_score: float = 3.0  # 1.0-5.0
    effort_estimate: int = 5  # dias (>=1)

    # Ordenação topológica
    sort_order: int = 0
    unblock_potential: int = 0
    critical_path_weight: float = 0.0
    epic_dependencies: List[str] = field(default_factory=list)

    # TDD
    tdd_phase: str = "analysis"  # analysis/red/green/refactor/review
    tdd_order: int = 1  # 1-3 prioridade dentro da fase

    # Negócio (placeholders compatíveis com docs)
    business_value: int = 5  # 1-10
    risk_mitigation: int = 5  # 1-10
    strategic_alignment: int = 5  # 1-10

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
        """Valida a entidade Epic e retorna lista de erros (se houver)."""
        errors: List[str] = []

        # Obrigatórios
        if not self.project_id:
            errors.append("project_id is required")
        if not self.key or not self.key.strip():
            errors.append("key is required and cannot be empty")
        if not self.name or not self.name.strip():
            errors.append("name is required and cannot be empty")

        # Ranges
        if not 0.0 <= self.ai_confidence <= 1.0:
            errors.append("ai_confidence must be between 0.0 and 1.0")
        if not 1.0 <= self.complexity_score <= 5.0:
            errors.append("complexity_score must be between 1.0 and 5.0")
        if self.effort_estimate <= 0:
            errors.append("effort_estimate must be greater than zero")

        # TDD phase
        valid_phases = ["analysis", "red", "green", "refactor", "review"]
        if self.tdd_phase not in valid_phases:
            errors.append(f"tdd_phase must be one of {valid_phases}")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    def has_dependencies(self) -> bool:
        return bool(self.epic_dependencies)

    def is_ai_generated(self) -> bool:
        return self.ai_generated

    def is_high_confidence(self) -> bool:
        return self.ai_confidence >= 0.8
