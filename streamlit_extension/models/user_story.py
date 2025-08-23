#!/usr/bin/env python3
"""
📚 MODELS - UserStory ORM Model (corrigido e otimizado)

SQLAlchemy ORM model para a tabela framework_user_stories — requisitos detalhados
focados no usuário, conectando Epics e Tasks, com integrações Agile/Scrum, TDD e TDAH.

Principais ajustes nesta versão:
- ✅ Colunas JSON padronizadas como `Text` (armazenando JSON serializado) para compatibilidade
  com `JSONFieldMixin` (que usa `json.dumps/json.loads`)
- ✅ Campos `DateTime` com `timezone=True` e valores em UTC (consistência com AuditMixin)
- ✅ Enum helpers robustos (fallback seguro)
- ✅ Correções de cálculos/comparações usando enums (evita comparar strings literais)
- ✅ Tipagem e defaults consistentes

Uso:
    from streamlit_extension.models.user_story import UserStory
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Integer, String, Text, Date, DateTime, ForeignKey, Boolean, DECIMAL, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .mixins import AuditMixin, JSONFieldMixin, TDDWorkflowMixin, TDAHOptimizationMixin

logger = logging.getLogger(__name__)


# =============================================================================
# User Story Enums
# =============================================================================

class StoryType(Enum):
    """Tipos de user story."""
    FEATURE = "feature"
    BUG = "bug"
    TECHNICAL = "technical"
    SPIKE = "spike"
    ENHANCEMENT = "enhancement"


class StorySize(Enum):
    """Tamanhos/estimativas."""
    XS = "XS"  # < 1 dia
    S = "S"    # 1–2 dias
    M = "M"    # 3–5 dias
    L = "L"    # 1–2 semanas
    XL = "XL"  # > 2 semanas


class WorkflowStage(Enum):
    """Estágios do fluxo de trabalho."""
    DISCOVERY = "discovery"
    ANALYSIS = "analysis"
    READY = "ready"
    DEVELOPMENT = "development"
    TESTING = "testing"
    REVIEW = "review"
    DONE = "done"


class UserImpact(Enum):
    """Nível de impacto para o usuário."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StoryStatus(Enum):
    """Status da user story."""
    BACKLOG = "backlog"
    SELECTED = "selected"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    IN_REVIEW = "in_review"
    TESTING = "testing"
    DONE = "done"
    CANCELLED = "cancelled"


# =============================================================================
# UserStory ORM Model
# =============================================================================

class UserStory(Base, AuditMixin, JSONFieldMixin, TDDWorkflowMixin, TDAHOptimizationMixin):
    """
    UserStory representa requisitos detalhados orientados ao usuário, ligando Epics a Tasks.

    Recursos:
    - Ciclo completo Agile/Scrum + gestão de critérios de aceitação/DoD
    - Persona, jornada do usuário e requisitos técnicos/UX
    - Integração com TDD (cenários de teste) e otimizações TDAH
    """
    __tablename__ = "framework_user_stories"

    # Chave primária e relacionamento
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    epic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("framework_epics.id", ondelete="CASCADE"), nullable=False
    )

    # Identificação
    story_key: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Conteúdo da user story
    user_story: Mapped[str] = mapped_column(Text, nullable=False)  # "As a [user], I want..."
    user_persona: Mapped[Optional[str]] = mapped_column(String(100))
    user_journey_stage: Mapped[Optional[str]] = mapped_column(String(50))

    # Detalhes
    description: Mapped[Optional[str]] = mapped_column(Text)
    business_value: Mapped[Optional[str]] = mapped_column(Text)
    user_benefit: Mapped[Optional[str]] = mapped_column(Text)
    technical_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Campos JSON (armazenados como texto serializado)
    acceptance_criteria: Mapped[str] = mapped_column(Text, nullable=False)   # array
    definition_of_done: Mapped[Optional[str]] = mapped_column(Text)          # array
    test_scenarios: Mapped[Optional[str]] = mapped_column(Text)              # array
    edge_cases: Mapped[Optional[str]] = mapped_column(Text)                  # array

    # Atributos
    story_type: Mapped[str] = mapped_column(String(50), default=StoryType.FEATURE.value)
    story_size: Mapped[str] = mapped_column(String(10), default=StorySize.M.value)
    story_points: Mapped[int] = mapped_column(Integer, default=3)
    complexity_level: Mapped[int] = mapped_column(Integer, default=5)  # 1–10

    # Priorização & planejamento
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1–5
    business_priority: Mapped[int] = mapped_column(Integer, default=3)
    technical_priority: Mapped[int] = mapped_column(Integer, default=3)
    user_impact: Mapped[str] = mapped_column(String(20), default=UserImpact.MEDIUM.value)

    # Dependências/Relacionamentos (como arrays JSON serializados)
    parent_story_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_user_stories.id"))
    depends_on: Mapped[Optional[str]] = mapped_column(Text)        # array de IDs
    blocks: Mapped[Optional[str]] = mapped_column(Text)            # array de IDs
    related_stories: Mapped[Optional[str]] = mapped_column(Text)   # array de IDs

    # Status & workflow
    status: Mapped[str] = mapped_column(String(50), default=StoryStatus.BACKLOG.value)
    workflow_stage: Mapped[str] = mapped_column(String(50), default=WorkflowStage.DISCOVERY.value)
    blocked_reason: Mapped[Optional[str]] = mapped_column(Text)
    blocked_until: Mapped[Optional[date]] = mapped_column(Date)

    # Estimativas & tracking
    estimated_hours: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2))
    actual_hours: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=Decimal("0"))
    estimated_story_points: Mapped[int] = mapped_column(Integer, default=3)
    actual_story_points: Mapped[Optional[int]] = mapped_column(Integer)

    # QA (campos JSON serializados)
    qa_notes: Mapped[Optional[str]] = mapped_column(Text)
    testing_requirements: Mapped[Optional[str]] = mapped_column(Text)
    performance_criteria: Mapped[Optional[str]] = mapped_column(Text)
    accessibility_requirements: Mapped[Optional[str]] = mapped_column(Text)

    # UX (campos JSON serializados)
    ux_requirements: Mapped[Optional[str]] = mapped_column(Text)
    ui_mockups: Mapped[Optional[str]] = mapped_column(Text)
    interaction_design: Mapped[Optional[str]] = mapped_column(Text)
    responsive_requirements: Mapped[Optional[str]] = mapped_column(Text)

    # Especificações técnicas (campos JSON serializados)
    technical_requirements: Mapped[Optional[str]] = mapped_column(Text)
    api_specifications: Mapped[Optional[str]] = mapped_column(Text)
    database_changes: Mapped[Optional[str]] = mapped_column(Text)
    integration_requirements: Mapped[Optional[str]] = mapped_column(Text)
    security_requirements: Mapped[Optional[str]] = mapped_column(Text)

    # Validação & feedback (campos JSON serializados)
    validation_plan: Mapped[Optional[str]] = mapped_column(Text)
    user_feedback: Mapped[Optional[str]] = mapped_column(Text)
    testing_results: Mapped[Optional[str]] = mapped_column(Text)
    performance_results: Mapped[Optional[str]] = mapped_column(Text)

    # Classificações (campos JSON serializados)
    labels: Mapped[Optional[str]] = mapped_column(Text)
    components: Mapped[Optional[str]] = mapped_column(Text)
    platforms: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[str]] = mapped_column(Text)

    # Multi-usuário
    assigned_to: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    product_owner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    developer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    qa_engineer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    ux_designer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))

    # Colaboração (arrays JSON serializados de IDs)
    reviewers: Mapped[Optional[str]] = mapped_column(Text)
    collaborators: Mapped[Optional[str]] = mapped_column(Text)
    watchers: Mapped[Optional[str]] = mapped_column(Text)

    # Integrações externas
    external_ticket_id: Mapped[Optional[str]] = mapped_column(String(100))
    external_system: Mapped[Optional[str]] = mapped_column(String(50))
    github_issue_number: Mapped[Optional[int]] = mapped_column(Integer)
    figma_link: Mapped[Optional[str]] = mapped_column(String(500))

    # Trilhas extras (além do AuditMixin) — timezone-aware
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deployed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Restrições
    __table_args__ = (
        UniqueConstraint("epic_id", "story_key", name="uq_user_stories_epic_key"),
    )

    # Relationships (opcional, conforme necessidade do projeto)
    # epic = relationship("Epic", back_populates="user_stories")
    # parent_story = relationship("UserStory", remote_side=[id])
    # child_stories = relationship("UserStory", back_populates="parent_story")
    # tasks = relationship("Task", back_populates="user_story")

    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        key = getattr(self, "story_key", "?")
        title = (getattr(self, "title", "") or "")[:50]
        return f"<UserStory(id={self.id}, key='{key}', title='{title}...')>"

    # =============================================================================
    # Enum Properties
    # =============================================================================

    @property
    def story_type_enum(self) -> StoryType:
        try:
            return StoryType(self.story_type)
        except Exception:
            return StoryType.FEATURE

    @story_type_enum.setter
    def story_type_enum(self, story_type: StoryType) -> None:
        self.story_type = story_type.value

    @property
    def story_size_enum(self) -> StorySize:
        try:
            return StorySize(self.story_size)
        except Exception:
            return StorySize.M

    @story_size_enum.setter
    def story_size_enum(self, size: StorySize) -> None:
        self.story_size = size.value

    @property
    def workflow_stage_enum(self) -> WorkflowStage:
        try:
            return WorkflowStage(self.workflow_stage)
        except Exception:
            return WorkflowStage.DISCOVERY

    @workflow_stage_enum.setter
    def workflow_stage_enum(self, stage: WorkflowStage) -> None:
        self.workflow_stage = stage.value

    @property
    def status_enum(self) -> StoryStatus:
        try:
            return StoryStatus(self.status)
        except Exception:
            return StoryStatus.BACKLOG

    @status_enum.setter
    def status_enum(self, status: StoryStatus) -> None:
        self.status = status.value

    @property
    def user_impact_enum(self) -> UserImpact:
        try:
            return UserImpact(self.user_impact)
        except Exception:
            return UserImpact.MEDIUM

    @user_impact_enum.setter
    def user_impact_enum(self, impact: UserImpact) -> None:
        self.user_impact = impact.value

    # =============================================================================
    # Acceptance Criteria Management
    # =============================================================================

    def get_acceptance_criteria(self) -> List[Dict[str, Any]]:
        return self.get_json_field("acceptance_criteria", [])

    def add_acceptance_criterion(
        self,
        criterion: str,
        description: str = "",
        priority: str = "must",
        test_method: str = "",
    ) -> bool:
        item = {
            "id": len(self.get_acceptance_criteria()) + 1,
            "criterion": criterion,
            "description": description,
            "priority": priority,  # must, should, could, wont
            "test_method": test_method,
            "status": "not_tested",  # not_tested, testing, passed, failed
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.append_to_json_array("acceptance_criteria", item)

    def update_criterion_status(self, criterion_id: int, status: str, notes: str = "") -> bool:
        criteria = self.get_acceptance_criteria()
        for c in criteria:
            if c.get("id") == criterion_id:
                c["status"] = status
                c["test_notes"] = notes
                c["tested_at"] = datetime.now(timezone.utc).isoformat()
                return self.set_json_field("acceptance_criteria", criteria)
        return False

    def get_definition_of_done(self) -> List[Dict[str, Any]]:
        return self.get_json_field("definition_of_done", [])

    def add_done_criterion(self, criterion: str, responsible_role: str = "", validation_method: str = "") -> bool:
        obj = {
            "criterion": criterion,
            "responsible_role": responsible_role,  # developer, qa, po, ux
            "validation_method": validation_method,
            "completed": False,
            "completed_at": None,
            "completed_by": None,
        }
        return self.append_to_json_array("definition_of_done", obj)

    # =============================================================================
    # Test Scenarios Management
    # =============================================================================

    def get_test_scenarios(self) -> List[Dict[str, Any]]:
        return self.get_json_field("test_scenarios", [])

    def add_test_scenario(
        self,
        scenario_name: str,
        description: str,
        steps: List[str],
        expected_result: str,
        test_type: str = "functional",
    ) -> bool:
        obj = {
            "name": scenario_name,
            "description": description,
            "type": test_type,  # functional, integration, performance, security
            "steps": steps,
            "expected_result": expected_result,
            "actual_result": None,
            "status": "not_executed",  # not_executed, passed, failed, blocked
            "priority": "medium",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.append_to_json_array("test_scenarios", obj)

    def update_test_result(self, scenario_name: str, status: str, actual_result: str = "") -> bool:
        scenarios = self.get_test_scenarios()
        for s in scenarios:
            if s.get("name") == scenario_name:
                s["status"] = status
                s["actual_result"] = actual_result
                s["executed_at"] = datetime.now(timezone.utc).isoformat()
                return self.set_json_field("test_scenarios", scenarios)
        return False

    def get_edge_cases(self) -> List[Dict[str, Any]]:
        return self.get_json_field("edge_cases", [])

    def add_edge_case(
        self,
        case_name: str,
        description: str,
        expected_behavior: str,
        risk_level: str = "medium",
    ) -> bool:
        obj = {
            "name": case_name,
            "description": description,
            "expected_behavior": expected_behavior,
            "risk_level": risk_level,  # low, medium, high, critical
            "tested": False,
            "test_result": None,
            "mitigation": None,
        }
        return self.append_to_json_array("edge_cases", obj)

    # =============================================================================
    # Technical Requirements Management
    # =============================================================================

    def get_technical_requirements(self) -> Dict[str, Any]:
        return self.get_json_field("technical_requirements", {})

    def update_technical_requirements(self, **requirements) -> bool:
        tech = self.get_technical_requirements()
        tech.update(requirements)
        tech["last_updated"] = datetime.now(timezone.utc).isoformat()
        return self.set_json_field("technical_requirements", tech)

    def get_api_specifications(self) -> Dict[str, Any]:
        return self.get_json_field("api_specifications", {})

    def add_api_endpoint(
        self,
        method: str,
        endpoint: str,
        description: str,
        request_format: Optional[Dict[str, Any]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> bool:
        specs = self.get_api_specifications()
        if "endpoints" not in specs:
            specs["endpoints"] = []
        specs["endpoints"].append(
            {
                "method": method.upper(),
                "endpoint": endpoint,
                "description": description,
                "request_format": request_format or {},
                "response_format": response_format or {},
                "authentication_required": True,
                "rate_limit": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return self.set_json_field("api_specifications", specs)

    def get_database_changes(self) -> List[Dict[str, Any]]:
        return self.get_json_field("database_changes", [])

    def add_database_change(
        self,
        change_type: str,
        table_name: str,
        description: str,
        migration_script: str = "",
    ) -> bool:
        obj = {
            "type": change_type,  # create_table, alter_table, add_index, etc.
            "table_name": table_name,
            "description": description,
            "migration_script": migration_script,
            "rollback_script": "",
            "applied": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.append_to_json_array("database_changes", obj)

    # =============================================================================
    # Team Collaboration Management
    # =============================================================================

    def get_team_members(self) -> List[Dict[str, Any]]:
        team: List[Dict[str, Any]] = []
        if self.assigned_to:
            team.append({"role": "assignee", "user_id": self.assigned_to})
        if self.product_owner_id:
            team.append({"role": "product_owner", "user_id": self.product_owner_id})
        if self.developer_id:
            team.append({"role": "developer", "user_id": self.developer_id})
        if self.qa_engineer_id:
            team.append({"role": "qa_engineer", "user_id": self.qa_engineer_id})
        if self.ux_designer_id:
            team.append({"role": "ux_designer", "user_id": self.ux_designer_id})

        for reviewer_id in self.get_json_field("reviewers", []):
            team.append({"role": "reviewer", "user_id": reviewer_id})
        for collaborator_id in self.get_json_field("collaborators", []):
            team.append({"role": "collaborator", "user_id": collaborator_id})
        for watcher_id in self.get_json_field("watchers", []):
            team.append({"role": "watcher", "user_id": watcher_id})

        return team

    def assign_role(self, user_id: int, role: str) -> bool:
        if role == "assignee":
            self.assigned_to = user_id
        elif role == "product_owner":
            self.product_owner_id = user_id
        elif role == "developer":
            self.developer_id = user_id
        elif role == "qa_engineer":
            self.qa_engineer_id = user_id
        elif role == "ux_designer":
            self.ux_designer_id = user_id
        elif role == "reviewer":
            return self.append_to_json_array("reviewers", user_id)
        elif role == "collaborator":
            return self.append_to_json_array("collaborators", user_id)
        elif role == "watcher":
            return self.append_to_json_array("watchers", user_id)
        else:
            return False
        return True

    # =============================================================================
    # Dependency Management
    # =============================================================================

    def get_dependencies(self) -> List[int]:
        return self.get_json_field("depends_on", [])

    def add_dependency(self, story_id: int) -> bool:
        deps = self.get_dependencies()
        if story_id not in deps and story_id != self.id:
            return self.append_to_json_array("depends_on", story_id)
        return False

    def remove_dependency(self, story_id: int) -> bool:
        deps = self.get_dependencies()
        if story_id in deps:
            deps.remove(story_id)
            return self.set_json_field("depends_on", deps)
        return False

    def get_blocking_stories(self) -> List[int]:
        return self.get_json_field("blocks", [])

    def add_blocks(self, story_id: int) -> bool:
        blocks = self.get_blocking_stories()
        if story_id not in blocks and story_id != self.id:
            return self.append_to_json_array("blocks", story_id)
        return False

    def get_related_stories(self) -> List[int]:
        return self.get_json_field("related_stories", [])

    def add_related_story(self, story_id: int) -> bool:
        related = self.get_related_stories()
        if story_id not in related and story_id != self.id:
            return self.append_to_json_array("related_stories", story_id)
        return False

    # =============================================================================
    # Status & Workflow
    # =============================================================================

    def get_valid_status_transitions(self) -> List[StoryStatus]:
        transitions = {
            StoryStatus.BACKLOG: [StoryStatus.SELECTED, StoryStatus.CANCELLED],
            StoryStatus.SELECTED: [StoryStatus.IN_PROGRESS, StoryStatus.BACKLOG],
            StoryStatus.IN_PROGRESS: [StoryStatus.BLOCKED, StoryStatus.IN_REVIEW, StoryStatus.TESTING],
            StoryStatus.BLOCKED: [StoryStatus.IN_PROGRESS, StoryStatus.BACKLOG],
            StoryStatus.IN_REVIEW: [StoryStatus.IN_PROGRESS, StoryStatus.TESTING, StoryStatus.DONE],
            StoryStatus.TESTING: [StoryStatus.IN_PROGRESS, StoryStatus.DONE],
            StoryStatus.DONE: [],
            StoryStatus.CANCELLED: [StoryStatus.BACKLOG],
        }
        return transitions.get(self.status_enum, [])

    def can_transition_to_status(self, new_status: StoryStatus) -> bool:
        return new_status in self.get_valid_status_transitions()

    def transition_status(self, new_status: StoryStatus, user_id: Optional[int] = None, reason: str = "") -> bool:
        if not self.can_transition_to_status(new_status):
            logger.warning(f"Invalid status transition from {self.status} to {new_status.value}")
            return False

        old_status = self.status_enum
        self.status_enum = new_status

        now = datetime.now(timezone.utc)
        if new_status == StoryStatus.IN_PROGRESS:
            self.started_at = now
        elif new_status == StoryStatus.DONE:
            self.completed_at = now
        elif new_status == StoryStatus.BLOCKED:
            self.blocked_reason = reason

        self.updated_by = user_id
        self.touch(user_id)

        logger.info(f"UserStory {self.id} status changed: {old_status.value} -> {new_status.value}")
        return True

    def get_valid_workflow_transitions(self) -> List[WorkflowStage]:
        transitions = {
            WorkflowStage.DISCOVERY: [WorkflowStage.ANALYSIS],
            WorkflowStage.ANALYSIS: [WorkflowStage.READY, WorkflowStage.DISCOVERY],
            WorkflowStage.READY: [WorkflowStage.DEVELOPMENT, WorkflowStage.ANALYSIS],
            WorkflowStage.DEVELOPMENT: [WorkflowStage.TESTING, WorkflowStage.READY],
            WorkflowStage.TESTING: [WorkflowStage.REVIEW, WorkflowStage.DEVELOPMENT],
            WorkflowStage.REVIEW: [WorkflowStage.DONE, WorkflowStage.DEVELOPMENT],
            WorkflowStage.DONE: [],
        }
        return transitions.get(self.workflow_stage_enum, [])

    def advance_workflow_stage(self) -> bool:
        valid = self.get_valid_workflow_transitions()
        if valid:
            self.workflow_stage_enum = valid[0]
            return True
        return False

    # =============================================================================
    # Progress & Analytics
    # =============================================================================

    def calculate_completion_percentage(self) -> float:
        """Retorna 0–100%. Usa pesos de critérios, cenários de teste, DoD e estágio."""
        factors: List[tuple[str, float, float]] = []

        # Critérios de aceitação
        criteria = self.get_acceptance_criteria()
        criteria_completion = (
            (sum(1 for c in criteria if c.get("status") == "passed") / len(criteria)) if criteria else 0.0
        )
        factors.append(("criteria", criteria_completion, 0.4))

        # Cenários de teste
        scenarios = self.get_test_scenarios()
        if scenarios:
            scen_ok = sum(1 for s in scenarios if s.get("status") == "passed")
            scenarios_completion = scen_ok / len(scenarios)
        else:
            scenarios_completion = 1.0 if self.story_type_enum == StoryType.SPIKE else 0.0
        factors.append(("testing", scenarios_completion, 0.3))

        # Definition of Done
        done_criteria = self.get_definition_of_done()
        done_completion = (
            (sum(1 for d in done_criteria if d.get("completed")) / len(done_criteria)) if done_criteria else 0.0
        )
        factors.append(("done", done_completion, 0.2))

        # Estágio do workflow
        stage_weights = {
            WorkflowStage.DISCOVERY: 0.1,
            WorkflowStage.ANALYSIS: 0.2,
            WorkflowStage.READY: 0.3,
            WorkflowStage.DEVELOPMENT: 0.6,
            WorkflowStage.TESTING: 0.8,
            WorkflowStage.REVIEW: 0.9,
            WorkflowStage.DONE: 1.0,
        }
        workflow_completion = stage_weights.get(self.workflow_stage_enum, 0.0)
        factors.append(("workflow", workflow_completion, 0.1))

        score = sum(v * w for _, v, w in factors)
        return min(score * 100, 100.0)

    def get_story_health(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "overall_health": "good",
            "completion_percentage": self.calculate_completion_percentage(),
            "blocked": self.status_enum == StoryStatus.BLOCKED,
            "overdue": False,
            "risk_factors": [],
            "recommendations": [],
        }

        if self.blocked_until and self.blocked_until < date.today():
            data["overdue"] = True
            data["risk_factors"].append("blocked_overdue")

        criteria = self.get_acceptance_criteria()
        if len(criteria) < 3:
            data["risk_factors"].append("insufficient_criteria")
            data["recommendations"].append("Add more acceptance criteria for better clarity")

        scenarios = self.get_test_scenarios()
        if len(scenarios) < 2 and self.story_type_enum != StoryType.SPIKE:
            data["risk_factors"].append("insufficient_test_coverage")
            data["recommendations"].append("Add more test scenarios for thorough testing")

        if not self.assigned_to:
            data["risk_factors"].append("unassigned")
            data["recommendations"].append("Assign story to a team member")

        risks = len(data["risk_factors"])
        if risks == 0:
            data["overall_health"] = "excellent"
        elif risks <= 2:
            data["overall_health"] = "good"
        elif risks <= 4:
            data["overall_health"] = "fair"
        else:
            data["overall_health"] = "poor"

        return data

    # =============================================================================
    # TDAH & TDD (overrides)
    # =============================================================================

    def calculate_tdah_complexity(self) -> int:
        score = self.complexity_level

        size_adj = {
            StorySize.XS: -2,
            StorySize.S: -1,
            StorySize.M: 0,
            StorySize.L: +1,
            StorySize.XL: +2,
        }
        score += size_adj.get(self.story_size_enum, 0)

        criteria_count = len(self.get_acceptance_criteria())
        if criteria_count > 10:
            score += 2
        elif criteria_count > 5:
            score += 1

        tech = self.get_technical_requirements()
        if len(tech) > 5:
            score += 2
        elif len(tech) > 2:
            score += 1

        deps = len(self.get_dependencies()) + len(self.get_blocking_stories())
        if deps > 3:
            score += 1

        return max(1, min(score, 10))

    def validate_tdd_workflow(self) -> bool:
        if self.is_tdd_exempt:
            return True

        scenarios = self.get_test_scenarios()
        if len(scenarios) < 2:
            return False

        criteria = self.get_acceptance_criteria()
        if len(criteria) < 3:
            return False

        return True

    # =============================================================================
    # Utilidades
    # =============================================================================

    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "epic_id": self.epic_id,
            "story_key": self.story_key,
            "title": self.title,
            "status": self.status,
            "workflow_stage": self.workflow_stage,
            "story_type": self.story_type,
            "story_size": self.story_size,
            "story_points": self.story_points,
            "priority": self.priority,
            "user_impact": self.user_impact,
            "completion_percentage": self.calculate_completion_percentage(),
            "health": self.get_story_health()["overall_health"],
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def clone(self, new_story_key: str, new_title: str, target_epic_id: Optional[int] = None) -> "UserStory":
        return UserStory(
            epic_id=target_epic_id or self.epic_id,
            story_key=new_story_key,
            title=new_title,
            user_story=self.user_story,
            description=self.description,
            business_value=self.business_value,
            user_benefit=self.user_benefit,
            # Campos JSON (copiados como strings serializadas)
            acceptance_criteria=self.acceptance_criteria,
            definition_of_done=self.definition_of_done,
            test_scenarios=self.test_scenarios,
            technical_requirements=self.technical_requirements,
            # Atributos
            story_type=self.story_type,
            story_size=self.story_size,
            story_points=self.story_points,
            complexity_level=self.complexity_level,
            priority=self.priority,
            business_priority=self.business_priority,
            technical_priority=self.technical_priority,
            # Status resetado
            status=StoryStatus.BACKLOG.value,
            workflow_stage=WorkflowStage.DISCOVERY.value,
        )
