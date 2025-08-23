#!/usr/bin/env python3
"""
🏷️ MODELS - Task Labels System ORM Models

Sistema de rotulagem de tarefas com hierarquia de labels, regras de auto‑atribuição,
analytics de uso e relacionamentos N↔N com tarefas.

Mapeia as tabelas:
- task_labels
- task_label_assignments

Compatível com os mixins do projeto (AuditMixin, JSONFieldMixin) e com o padrão
de serialização/ desserialização JSON já utilizado.

Principais melhorias desta revisão:
- ✅ Imports corrigidos (dataclass, etc.)
- ✅ Tipagem consistente (Decimal/JSON/Optional)
- ✅ Defaults de data em UTC (evita timezone local)
- ✅ CheckConstraint para confidence_score ∈ [0,1]
- ✅ Métodos utilitários robustos com fallback seguro
- ✅ __repr__ e propriedades mantendo compatibilidade
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DECIMAL,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import AuditMixin, JSONFieldMixin


# =============================================================================
# Enums
# =============================================================================

class LabelVisibility(Enum):
    """Nível de visibilidade do label para controle de acesso."""
    PUBLIC = "public"      # Visível para todos
    PRIVATE = "private"    # Visível apenas ao criador
    TEAM = "team"          # Visível aos membros da(s) equipe(s) restrita(s)


class AssignmentContext(Enum):
    """Contexto de atribuição do label à tarefa."""
    MANUAL = "manual"         # Atribuído manualmente por um usuário
    AUTOMATIC = "automatic"   # Atribuído por regras automáticas
    BULK = "bulk"             # Atribuição em lote
    IMPORT = "import"         # Atribuído durante importação de dados


# =============================================================================
# Dataclasses auxiliares
# =============================================================================

@dataclass
class LabelUsageStats:
    """Estatísticas de uso de um label."""
    total_usage: int
    recent_usage: int
    unique_tasks: int
    avg_confidence: float
    top_assigners: List[Dict[str, Any]]


@dataclass
class AutoAssignmentRule:
    """Regra de auto‑atribuição de label."""
    condition_type: str        # title_contains, description_contains, task_type_equals, title_starts_with, regex_match
    condition_value: str
    confidence_threshold: float
    rule_priority: int


# =============================================================================
# ORM: TaskLabelORM
# =============================================================================

class TaskLabelORM(Base, AuditMixin, JSONFieldMixin):
    """
    ORM para a tabela task_labels com gestão de:
    - Identidade e propriedades visuais
    - Hierarquia (parent/children)
    - Regras de auto‑atribuição
    - Estatísticas de uso e acesso
    """
    __tablename__ = "task_labels"

    # Chave primária
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Identidade do label
    label_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    # Propriedades
    label_description: Mapped[Optional[str]] = mapped_column(Text)
    label_color: Mapped[str] = mapped_column(String(20), default="#3498db")  # Hex color code
    label_icon: Mapped[Optional[str]] = mapped_column(String(50))            # Ex.: "alert-triangle"
    label_category: Mapped[str] = mapped_column(String(50), default="general")

    # Comportamento / Automação
    is_system_label: Mapped[bool] = mapped_column(Boolean, default=False)
    is_exclusive: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_apply_rules: Mapped[Optional[str]] = mapped_column(JSON)  # lista de regras

    # Estatísticas
    usage_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Organização
    display_order: Mapped[int] = mapped_column(Integer, default=100)
    parent_label_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("task_labels.id"))

    # Acesso
    visibility: Mapped[str] = mapped_column(String(20), default=LabelVisibility.PUBLIC.value)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    team_restricted: Mapped[Optional[str]] = mapped_column(JSON)  # lista de IDs de equipes/usuários autorizados

    # Auditoria estendida
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relacionamentos
    parent_label: Mapped[Optional["TaskLabelORM"]] = relationship(
        "TaskLabelORM", remote_side="TaskLabelORM.id", back_populates="child_labels"
    )
    child_labels: Mapped[List["TaskLabelORM"]] = relationship(
        "TaskLabelORM", back_populates="parent_label", cascade="all, delete-orphan"
    )
    # label_assignments = relationship("TaskLabelAssignmentORM", back_populates="label")

    def __repr__(self) -> str:
        return f"<TaskLabelORM(id={self.id}, name='{self.label_name}', category='{self.label_category}')>"

    # ----------------------------
    # Propriedades utilitárias
    # ----------------------------

    @property
    def visibility_enum(self) -> LabelVisibility:
        """Visibilidade como enum (com fallback seguro)."""
        try:
            return LabelVisibility(self.visibility)
        except ValueError:
            return LabelVisibility.PUBLIC

    @property
    def is_deleted(self) -> bool:
        """Indica se o label foi logicamente removido (soft delete)."""
        return self.deleted_at is not None

    @property
    def has_children(self) -> bool:
        """Indica se o label possui filhos (hierarquia)."""
        return bool(getattr(self, "child_labels", []))

    @property
    def is_popular(self) -> bool:
        """Define popularidade por uso (threshold simples e configurável)."""
        return self.usage_count >= 10

    @property
    def recently_used(self) -> bool:
        """Indica uso recente (≤ 30 dias)."""
        if not self.last_used_at:
            return False
        return (datetime.utcnow() - self.last_used_at).days <= 30

    # ----------------------------
    # Gestão do ciclo de vida
    # ----------------------------

    def soft_delete(self) -> None:
        """Marca o label como removido (soft delete)."""
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restaura um label removido logicamente."""
        self.deleted_at = None

    def increment_usage(self) -> None:
        """Incrementa contador de uso e atualiza last_used_at (UTC)."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()

    def decrement_usage(self) -> None:
        """Decrementa contador de uso (não deixa negativo)."""
        self.usage_count = max(0, self.usage_count - 1)

    # ----------------------------
    # Regras de auto‑atribuição
    # ----------------------------

    def get_auto_apply_rules(self) -> List[AutoAssignmentRule]:
        """Retorna as regras de auto‑atribuição como objetos estruturados."""
        if not self.auto_apply_rules:
            return []

        data = self.deserialize_json(self.auto_apply_rules)
        if not isinstance(data, list):
            return []

        rules: List[AutoAssignmentRule] = []
        for rule in data:
            if not isinstance(rule, dict):
                continue
            ct = rule.get("condition_type", "")
            cv = rule.get("condition_value", "")
            if not ct or not cv:
                continue
            rules.append(
                AutoAssignmentRule(
                    condition_type=ct,
                    condition_value=cv,
                    confidence_threshold=float(rule.get("confidence_threshold", 0.8)),
                    rule_priority=int(rule.get("rule_priority", 1)),
                )
            )
        return rules

    def add_auto_apply_rule(
        self,
        condition_type: str,
        condition_value: str,
        confidence_threshold: float = 0.8,
        rule_priority: int = 1,
    ) -> None:
        """Adiciona uma nova regra de auto‑atribuição."""
        current = self.deserialize_json(self.auto_apply_rules) if self.auto_apply_rules else []
        if not isinstance(current, list):
            current = []

        current.append(
            {
                "condition_type": condition_type,
                "condition_value": condition_value,
                "confidence_threshold": float(confidence_threshold),
                "rule_priority": int(rule_priority),
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        self.auto_apply_rules = self.serialize_json(current)

    def check_auto_apply_match(self, task_title: str, task_description: str, task_type: str) -> float:
        """
        Calcula a confiança máxima para auto‑aplicação deste label a uma tarefa
        com base nas regras registradas.
        """
        rules = self.get_auto_apply_rules()
        if not rules:
            return 0.0

        max_confidence = 0.0
        full_text = f"{task_title} {task_description}".lower()

        for rule in rules:
            confidence = 0.0
            cond = rule.condition_type
            val = rule.condition_value.lower()

            try:
                if cond == "title_contains" and val in task_title.lower():
                    confidence = 0.9
                elif cond == "description_contains" and val in task_description.lower():
                    confidence = 0.8
                elif cond == "task_type_equals" and val == task_type.lower():
                    confidence = 0.95
                elif cond == "title_starts_with" and task_title.lower().startswith(val):
                    confidence = 0.85
                elif cond == "regex_match":
                    import re
                    if re.search(rule.condition_value, full_text, re.IGNORECASE):
                        confidence = 0.7
            except Exception:
                # Regra inválida não deve quebrar o fluxo de classificação
                confidence = 0.0

            # Peso por prioridade (1–10 ⇒ 0.1–1.0)
            confidence *= (rule.rule_priority / 10.0)
            max_confidence = max(max_confidence, confidence)

        return min(max_confidence, 1.0)

    # ----------------------------
    # Acesso / Permissões
    # ----------------------------

    def get_team_restrictions(self) -> List[int]:
        """Retorna a lista de IDs (equipes/usuários) com permissão de uso."""
        if not self.team_restricted:
            return []
        data = self.deserialize_json(self.team_restricted)
        if isinstance(data, list):
            out: List[int] = []
            for uid in data:
                if isinstance(uid, int):
                    out.append(uid)
                elif isinstance(uid, str) and uid.isdigit():
                    out.append(int(uid))
            return out
        return []

    def set_team_restrictions(self, team_ids: List[int]) -> None:
        """Define restrições de acesso; ao definir, visibilidade torna‑se TEAM."""
        self.team_restricted = self.serialize_json(team_ids)
        if team_ids:
            self.visibility = LabelVisibility.TEAM.value

    def can_be_used_by(self, user_id: int, user_teams: Optional[List[int]] = None) -> bool:
        """
        Verifica se o usuário pode usar o label:
        - PUBLIC: sempre
        - PRIVATE: somente o criador
        - TEAM: pertencendo a alguma equipe autorizada (ou ID listado)
        """
        if self.is_deleted:
            return False

        vis = self.visibility_enum
        if vis == LabelVisibility.PUBLIC:
            return True
        if vis == LabelVisibility.PRIVATE:
            return self.created_by == user_id
        if vis == LabelVisibility.TEAM:
            restrictions = self.get_team_restrictions()
            if not restrictions:
                return True  # Sem restrições explícitas
            # Preferir interseção por equipes; fallback por ID direto
            if user_teams and any(team_id in restrictions for team_id in user_teams):
                return True
            return user_id in restrictions
        return False

    # ----------------------------
    # Hierarquia
    # ----------------------------

    def get_full_path(self) -> str:
        """
        Retorna o caminho hierárquico "pai > filho".
        Observação: implementação simplificada (sem consulta recursiva).
        """
        if not self.parent_label:
            return self.label_name
        return f"{self.parent_label.label_name} > {self.label_name}"

    def get_hierarchy_level(self) -> int:
        """Nível hierárquico: 0 = raiz; 1 = possui pai (simplificado)."""
        return 1 if self.parent_label_id else 0

    # ----------------------------
    # Relatórios / Sumários
    # ----------------------------

    def get_usage_stats(self, days: int = 30) -> LabelUsageStats:
        """
        Retorna estatísticas de uso (placeholder sem consultas agregadas).
        Integração real deve consultar a tabela de assignments.
        """
        return LabelUsageStats(
            total_usage=self.usage_count,
            recent_usage=0,
            unique_tasks=0,
            avg_confidence=0.0,
            top_assigners=[],
        )

    def suggest_similar_labels(self, limit: int = 5) -> List["TaskLabelORM"]:
        """Sugere labels semelhantes (placeholder; requer sessão/consultas)."""
        return []

    @classmethod
    def create_system_label(
        cls,
        name: str,
        description: str,
        color: str,
        category: str,
        display_order: int = 100,
    ) -> "TaskLabelORM":
        """Fábrica para criar labels de sistema com configuração padrão."""
        return cls(
            label_name=name,
            label_description=description,
            label_color=color,
            label_category=category,
            is_system_label=True,
            display_order=display_order,
            visibility=LabelVisibility.PUBLIC.value,
        )

    def get_label_summary(self) -> Dict[str, Any]:
        """Resumo consolidado do label para UI/relatórios."""
        return {
            "basic_info": {
                "id": self.id,
                "name": self.label_name,
                "description": self.label_description,
                "color": self.label_color,
                "icon": self.label_icon,
                "category": self.label_category,
            },
            "configuration": {
                "is_system_label": self.is_system_label,
                "is_exclusive": self.is_exclusive,
                "visibility": self.visibility,
                "display_order": self.display_order,
            },
            "usage": {
                "usage_count": self.usage_count,
                "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
                "is_popular": self.is_popular,
                "recently_used": self.recently_used,
            },
            "hierarchy": {
                "parent_label_id": self.parent_label_id,
                "has_children": self.has_children,
                "hierarchy_level": self.get_hierarchy_level(),
                "full_path": self.get_full_path(),
            },
            "automation": {
                "has_auto_rules": bool(self.auto_apply_rules),
                "rule_count": len(self.get_auto_apply_rules()),
            },
            "access": {
                "created_by": self.created_by,
                "has_team_restrictions": bool(self.team_restricted),
                "is_deleted": self.is_deleted,
            },
        }


# =============================================================================
# ORM: TaskLabelAssignmentORM
# =============================================================================

class TaskLabelAssignmentORM(Base, AuditMixin):
    """
    ORM para a tabela task_label_assignments com:
    - Contexto de atribuição (manual/automático/bulk/import)
    - Confiança da atribuição
    - Validação e auditoria
    """
    __tablename__ = "task_label_assignments"

    # PK
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Relacionamentos (FKs)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("framework_tasks.id"), nullable=False)
    label_id: Mapped[int] = mapped_column(Integer, ForeignKey("task_labels.id"), nullable=False)

    # Contexto / metadados
    assigned_reason: Mapped[Optional[str]] = mapped_column(Text)
    assignment_context: Mapped[str] = mapped_column(String(100), default=AssignmentContext.MANUAL.value)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3, 2))  # 0.00–1.00

    # Autores / validação
    assigned_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    validated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    is_validated: Mapped[bool] = mapped_column(Boolean, default=True)

    # Auditoria
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    removed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        UniqueConstraint("task_id", "label_id", name="uq_task_label_assignment"),
        # Garante que confidence_score (quando definido) esteja no intervalo [0, 1]
        CheckConstraint("(confidence_score IS NULL) OR (confidence_score >= 0 AND confidence_score <= 1)", name="ck_confidence_range_0_1"),
    )

    # Relações opcionais (mantidas comentadas para evitar dependências fortes)
    # task = relationship("TaskORM", back_populates="label_assignments")
    # label = relationship("TaskLabelORM", back_populates="label_assignments")
    # assigner = relationship("UserORM", foreign_keys=[assigned_by])
    # validator = relationship("UserORM", foreign_keys=[validated_by])

    def __repr__(self) -> str:
        return (
            f"<TaskLabelAssignmentORM(id={self.id}, task_id={self.task_id}, "
            f"label_id={self.label_id}, context='{self.assignment_context}')>"
        )

    # ----------------------------
    # Propriedades utilitárias
    # ----------------------------

    @property
    def assignment_context_enum(self) -> AssignmentContext:
        """Contexto de atribuição como enum (com fallback)."""
        try:
            return AssignmentContext(self.assignment_context)
        except ValueError:
            return AssignmentContext.MANUAL

    @property
    def is_auto_assigned(self) -> bool:
        """Indica se a atribuição foi automática (por regra)."""
        return self.assignment_context_enum == AssignmentContext.AUTOMATIC

    @property
    def is_high_confidence(self) -> bool:
        """True se confidence_score ≥ 0.8."""
        return self.confidence_score is not None and float(self.confidence_score) >= 0.8

    @property
    def is_removed(self) -> bool:
        """Indica se a atribuição foi removida (soft delete)."""
        return self.removed_at is not None

    # ----------------------------
    # Gestão da atribuição
    # ----------------------------

    def validate_assignment(self, validated_by: int, notes: str = "") -> bool:
        """Marca a atribuição como validada (uma vez)."""
        if self.is_validated:
            return False
        self.is_validated = True
        self.validated_by = validated_by
        self.validated_at = datetime.utcnow()
        if notes:
            prefix = "VALIDATED: "
            self.assigned_reason = f"{prefix}{notes}" if not self.assigned_reason else f"{self.assigned_reason}\n{prefix}{notes}"
        return True

    def remove_assignment(self, reason: str = "") -> None:
        """Remove logicamente a atribuição."""
        self.removed_at = datetime.utcnow()
        if reason:
            prefix = "REMOVED: "
            self.assigned_reason = f"{prefix}{reason}" if not self.assigned_reason else f"{self.assigned_reason}\n{prefix}{reason}"

    def restore_assignment(self) -> None:
        """Restaura atribuição removida logicamente."""
        self.removed_at = None

    def update_confidence(self, new_confidence: float, reason: str = "") -> None:
        """Atualiza a confiança (clamp 0–1) e registra motivo (se fornecido)."""
        old = float(self.confidence_score) if self.confidence_score is not None else 0.0
        clamped = max(0.0, min(float(new_confidence), 1.0))
        self.confidence_score = Decimal(str(clamped))

        if reason:
            note = f"Confidence updated from {old:.2f} to {clamped:.2f}: {reason}"
            self.assigned_reason = f"{self.assigned_reason}\n{note}" if self.assigned_reason else note

    # ----------------------------
    # Fábricas
    # ----------------------------

    @classmethod
    def create_manual_assignment(
        cls,
        task_id: int,
        label_id: int,
        assigned_by: int,
        reason: str = "",
    ) -> "TaskLabelAssignmentORM":
        """Cria atribuição manual com confiança 1.00 e já validada."""
        return cls(
            task_id=task_id,
            label_id=label_id,
            assignment_context=AssignmentContext.MANUAL.value,
            assigned_by=assigned_by,
            assigned_reason=reason,
            confidence_score=Decimal("1.00"),
            is_validated=True,
        )

    @classmethod
    def create_auto_assignment(
        cls,
        task_id: int,
        label_id: int,
        confidence_score: float,
        rule_reason: str = "",
    ) -> "TaskLabelAssignmentORM":
        """Cria atribuição automática (requer validação posterior)."""
        score = max(0.0, min(float(confidence_score), 1.0))
        return cls(
            task_id=task_id,
            label_id=label_id,
            assignment_context=AssignmentContext.AUTOMATIC.value,
            confidence_score=Decimal(str(score)),
            assigned_reason=f"Auto-assigned: {rule_reason}" if rule_reason else "Auto-assigned by system rule",
            is_validated=False,
        )

    @classmethod
    def create_bulk_assignment(
        cls,
        task_id: int,
        label_id: int,
        assigned_by: int,
        batch_reason: str = "",
    ) -> "TaskLabelAssignmentORM":
        """Cria atribuição em lote (confiança alta, já validada)."""
        return cls(
            task_id=task_id,
            label_id=label_id,
            assignment_context=AssignmentContext.BULK.value,
            assigned_by=assigned_by,
            assigned_reason=f"Bulk operation: {batch_reason}" if batch_reason else "Bulk assignment",
            confidence_score=Decimal("0.90"),
            is_validated=True,
        )

    # ----------------------------
    # Relatórios / Sumários
    # ----------------------------

    def get_assignment_summary(self) -> Dict[str, Any]:
        """Resumo consolidado da atribuição para UI/relatórios."""
        return {
            "basic_info": {
                "id": self.id,
                "task_id": self.task_id,
                "label_id": self.label_id,
                "assignment_context": self.assignment_context,
            },
            "confidence": {
                "confidence_score": float(self.confidence_score) if self.confidence_score is not None else 0.0,
                "is_high_confidence": self.is_high_confidence,
                "is_auto_assigned": self.is_auto_assigned,
            },
            "validation": {
                "is_validated": self.is_validated,
                "validated_by": self.validated_by,
                "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            },
            "status": {
                "is_removed": self.is_removed,
                "assigned_at": self.assigned_at.isoformat(),
                "removed_at": self.removed_at.isoformat() if self.removed_at else None,
            },
            "metadata": {
                "assigned_by": self.assigned_by,
                "assigned_reason": self.assigned_reason,
            },
        }
