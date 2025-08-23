#!/usr/bin/env python3
"""
🏃 MODELS - Sprint System ORM Model

Sprint system implementation with comprehensive Agile sprint management,
TDD workflow integration, and TDAH optimization.

Maps to sprints table from migration 009_sprint_system_and_advanced_features.sql

Usage:
    from streamlit_extension.models.sprint import SprintORM, SprintStatus

    # Create new sprint
    sprint = SprintORM(
        project_id=1,
        sprint_key="SPRINT-2025-01",
        sprint_name="Authentication System Sprint",
        sprint_goal="Implement complete OAuth 2.0 authentication"
    )

Features:
- Complete Agile sprint lifecycle management
- TDD workflow integration with phase tracking
- TDAH-optimized sprint planning and metrics
- Team collaboration and communication tools
- Comprehensive analytics and reporting
- Sprint health monitoring and risk management
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .mixins import AuditMixin, JSONFieldMixin, TDDWorkflowMixin, TDAHOptimizationMixin


# =============================================================================
# Enums & Dataclasses
# =============================================================================

class SprintStatus(Enum):
    """Sprint status enumeration with complete lifecycle."""
    PLANNING = "planning"
    ACTIVE = "active"
    REVIEW = "review"
    RETROSPECTIVE = "retrospective"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SprintHealthStatus(Enum):
    """Sprint health status with visual indicators."""
    GREEN = "green"      # On track
    YELLOW = "yellow"    # At risk
    RED = "red"          # Critical issues


class SprintSyncStatus(Enum):
    """External system synchronization status."""
    SYNCED = "synced"
    PENDING = "pending"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class SprintMetrics:
    """Sprint metrics calculation result."""
    velocity_achievement: float
    scope_completion: float
    quality_score: float
    team_satisfaction: float
    burndown_health: str
    risk_level: str


@dataclass
class SprintBurndownPoint:
    """Single point in sprint burndown chart."""
    date: date
    remaining_story_points: int
    remaining_tasks: int
    ideal_remaining: int
    team_capacity: float


# =============================================================================
# ORM Model
# =============================================================================

class SprintORM(Base, AuditMixin, JSONFieldMixin, TDDWorkflowMixin, TDAHOptimizationMixin):
    """
    Complete Sprint ORM model with Agile management and TDD integration.

    Maps to sprints table (35+ fields) with comprehensive sprint lifecycle,
    team management, metrics tracking, and TDD workflow integration.
    """
    __tablename__ = "sprints"

    # Primary Key and Relations
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("framework_projects.id"), nullable=False)

    # Sprint Identity
    sprint_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sprint_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Sprint Planning
    sprint_goal: Mapped[Optional[str]] = mapped_column(Text)
    sprint_description: Mapped[Optional[str]] = mapped_column(Text)
    capacity_points: Mapped[Optional[int]] = mapped_column(Integer)
    planned_velocity: Mapped[Optional[int]] = mapped_column(Integer)
    actual_velocity: Mapped[Optional[int]] = mapped_column(Integer)

    # Sprint Timeline
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    planned_hours: Mapped[Optional[int]] = mapped_column(Integer)
    actual_hours: Mapped[int] = mapped_column(Integer, default=0)

    # Sprint Status
    status: Mapped[str] = mapped_column(String(50), default=SprintStatus.PLANNING.value)
    sprint_number: Mapped[Optional[int]] = mapped_column(Integer)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    # Team Configuration (JSON fields)
    team_members: Mapped[Optional[str]] = mapped_column(JSON)        # Array[int]
    scrum_master_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    product_owner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    development_team: Mapped[Optional[str]] = mapped_column(JSON)    # Array[int]

    # Sprint Metrics
    story_points_committed: Mapped[int] = mapped_column(Integer, default=0)
    story_points_completed: Mapped[int] = mapped_column(Integer, default=0)
    tasks_committed: Mapped[int] = mapped_column(Integer, default=0)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    bugs_introduced: Mapped[int] = mapped_column(Integer, default=0)
    bugs_resolved: Mapped[int] = mapped_column(Integer, default=0)

    # Sprint Health (JSON fields)
    burndown_data: Mapped[Optional[str]] = mapped_column(JSON)       # Array[dict]
    health_status: Mapped[str] = mapped_column(String(20), default=SprintHealthStatus.GREEN.value)
    risk_factors: Mapped[Optional[str]] = mapped_column(JSON)        # Array[dict]
    impediments: Mapped[Optional[str]] = mapped_column(JSON)         # Array[dict]

    # Sprint Events
    planning_date: Mapped[Optional[date]] = mapped_column(Date)
    review_date: Mapped[Optional[date]] = mapped_column(Date)
    retrospective_date: Mapped[Optional[date]] = mapped_column(Date)
    demo_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Quality Metrics
    code_review_coverage: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))
    test_coverage: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))
    deployment_success_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))
    customer_satisfaction: Mapped[Optional[int]] = mapped_column(Integer)  # 1-10 scale

    # Sprint Outcomes (JSON fields)
    demo_feedback: Mapped[Optional[str]] = mapped_column(JSON)       # Array[dict]
    retrospective_notes: Mapped[Optional[str]] = mapped_column(Text)
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text)
    improvement_actions: Mapped[Optional[str]] = mapped_column(JSON) # Array[dict]

    # Integration Fields
    external_sprint_id: Mapped[Optional[str]] = mapped_column(String(100))
    external_system: Mapped[Optional[str]] = mapped_column(String(50))
    sync_status: Mapped[str] = mapped_column(String(50), default=SprintSyncStatus.SYNCED.value)

    # Enhanced Audit Fields (beyond AuditMixin)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Table Constraints
    __table_args__ = (
        UniqueConstraint('project_id', 'sprint_key', name='uq_sprint_key_per_project'),
        CheckConstraint('start_date <= end_date', name='ck_sprint_date_order'),
    )

    # Relationships (comentadas para evitar imports cíclicos)
    # project = relationship("ProjectORM", back_populates="sprints")
    # scrum_master = relationship("UserORM", foreign_keys=[scrum_master_id])
    # product_owner = relationship("UserORM", foreign_keys=[product_owner_id])
    # sprint_tasks = relationship("SprintTaskORM", back_populates="sprint")
    # sprint_milestones = relationship("SprintMilestoneORM", back_populates="sprint")

    # -------------------------------------------------------------------------
    # Representação
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"<SprintORM(id={self.id}, key='{self.sprint_key}', "
            f"name='{self.sprint_name}', status='{self.status}')>"
        )

    # -------------------------------------------------------------------------
    # Enum helpers
    # -------------------------------------------------------------------------
    @property
    def status_enum(self) -> SprintStatus:
        try:
            return SprintStatus(self.status)
        except ValueError:
            return SprintStatus.PLANNING

    @property
    def health_status_enum(self) -> SprintHealthStatus:
        try:
            return SprintHealthStatus(self.health_status)
        except ValueError:
            return SprintHealthStatus.GREEN

    @property
    def sync_status_enum(self) -> SprintSyncStatus:
        try:
            return SprintSyncStatus(self.sync_status)
        except ValueError:
            return SprintSyncStatus.SYNCED

    # -------------------------------------------------------------------------
    # Propriedades derivadas
    # -------------------------------------------------------------------------
    @property
    def duration_days(self) -> int:
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    @property
    def progress_percentage(self) -> float:
        if self.story_points_committed == 0:
            return 0.0
        return (self.story_points_completed / self.story_points_committed) * 100

    @property
    def velocity_achievement(self) -> float:
        if not self.planned_velocity:
            return 0.0
        actual = self.actual_velocity or 0
        return (actual / self.planned_velocity) * 100

    @property
    def is_active(self) -> bool:
        return self.status_enum == SprintStatus.ACTIVE

    @property
    def is_completed(self) -> bool:
        return self.status_enum == SprintStatus.COMPLETED

    @property
    def days_remaining(self) -> int:
        if not self.end_date or self.is_completed:
            return 0
        today = date.today()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days + 1

    # -------------------------------------------------------------------------
    # Sprint Lifecycle
    # -------------------------------------------------------------------------
    def start_sprint(self) -> bool:
        """Start the sprint with validation."""
        if not self._validate_sprint_start():
            return False

        self.status = SprintStatus.ACTIVE.value
        self.started_at = datetime.now()
        self.is_current = True

        # Initialize burndown data
        if not self.burndown_data:
            self.set_json_field('burndown_data', [])

        return True

    def _validate_sprint_start(self) -> bool:
        return (
            self.status_enum == SprintStatus.PLANNING
            and self.start_date
            and self.end_date
            and self.sprint_goal
            and len(self.sprint_goal.strip()) > 0
            and self.story_points_committed > 0
        )

    def complete_sprint(self, retrospective_notes: str = "", lessons_learned: str = "") -> bool:
        """Complete the sprint with final metrics."""
        if not self._validate_sprint_completion():
            return False

        self.status = SprintStatus.COMPLETED.value
        self.completed_at = datetime.now()
        self.is_current = False
        self.retrospective_notes = retrospective_notes
        self.lessons_learned = lessons_learned

        # Calculate final velocity
        if not self.actual_velocity:
            self.actual_velocity = self.story_points_completed

        return True

    def _validate_sprint_completion(self) -> bool:
        return (
            self.status_enum in (SprintStatus.ACTIVE, SprintStatus.REVIEW)
            and self.story_points_completed >= 0
            and self.tasks_completed >= 0
        )

    def cancel_sprint(self, reason: str = "") -> bool:
        """Cancel the sprint with reason."""
        if self.status_enum == SprintStatus.COMPLETED:
            return False

        self.status = SprintStatus.CANCELLED.value
        self.cancelled_at = datetime.now()
        self.is_current = False

        if reason:
            self.retrospective_notes = f"CANCELLED: {reason}"

        return True

    # -------------------------------------------------------------------------
    # Team Management
    # -------------------------------------------------------------------------
    def get_team_members_list(self) -> List[int]:
        data = self.get_json_field('team_members', [])
        if isinstance(data, list):
            return [int(x) for x in data if isinstance(x, (int, str)) and str(x).isdigit()]
        return []

    def add_team_member(self, user_id: int) -> bool:
        current = self.get_team_members_list()
        if user_id not in current:
            current.append(user_id)
            return self.set_json_field('team_members', current)
        return False

    def remove_team_member(self, user_id: int) -> bool:
        current = self.get_team_members_list()
        if user_id in current:
            current.remove(user_id)
            return self.set_json_field('team_members', current)
        return False

    def get_development_team_list(self) -> List[int]:
        data = self.get_json_field('development_team', [])
        if isinstance(data, list):
            return [int(x) for x in data if isinstance(x, (int, str)) and str(x).isdigit()]
        return []

    def set_development_team(self, developer_ids: List[int]) -> None:
        self.set_json_field('development_team', developer_ids)

    # -------------------------------------------------------------------------
    # Sprint Health & Risks
    # -------------------------------------------------------------------------
    def get_risk_factors_list(self) -> List[Dict[str, Any]]:
        risks = self.get_json_field('risk_factors', [])
        return risks if isinstance(risks, list) else []

    def add_risk_factor(self, risk_description: str, severity: str = "medium", mitigation: str = "") -> None:
        risks = self.get_risk_factors_list()
        new_risk = {
            "id": len(risks) + 1,
            "description": risk_description,
            "severity": severity,      # low, medium, high, critical
            "mitigation": mitigation,
            "identified_at": datetime.now().isoformat(),
            "status": "active"         # active, mitigated, resolved
        }
        risks.append(new_risk)
        self.set_json_field('risk_factors', risks)
        self._update_health_status()

    def get_impediments_list(self) -> List[Dict[str, Any]]:
        impediments = self.get_json_field('impediments', [])
        return impediments if isinstance(impediments, list) else []

    def add_impediment(self, description: str, impact: str = "medium", assigned_to: Optional[int] = None) -> None:
        impediments = self.get_impediments_list()
        new_imp = {
            "id": len(impediments) + 1,
            "description": description,
            "impact": impact,                  # low, medium, high
            "assigned_to": assigned_to,
            "reported_at": datetime.now().isoformat(),
            "status": "open"                   # open, in_progress, resolved
        }
        impediments.append(new_imp)
        self.set_json_field('impediments', impediments)
        self._update_health_status()

    def _update_health_status(self) -> None:
        risks = self.get_risk_factors_list()
        impediments = self.get_impediments_list()

        critical_risks = len([r for r in risks if r.get("severity") == "critical" and r.get("status") == "active"])
        high_risks = len([r for r in risks if r.get("severity") == "high" and r.get("status") == "active"])
        high_impediments = len([i for i in impediments if i.get("impact") == "high" and i.get("status") in ("open", "in_progress")])

        if critical_risks > 0 or high_impediments > 2:
            self.health_status = SprintHealthStatus.RED.value
        elif high_risks > 1 or high_impediments > 0:
            self.health_status = SprintHealthStatus.YELLOW.value
        else:
            self.health_status = SprintHealthStatus.GREEN.value

    # -------------------------------------------------------------------------
    # Burndown Chart
    # -------------------------------------------------------------------------
    def get_burndown_data_list(self) -> List[SprintBurndownPoint]:
        raw = self.get_json_field('burndown_data', [])
        if not isinstance(raw, list):
            return []
        points: List[SprintBurndownPoint] = []
        for point in raw:
            if all(k in point for k in ("date", "remaining_story_points", "remaining_tasks", "ideal_remaining")):
                points.append(
                    SprintBurndownPoint(
                        date=datetime.fromisoformat(point["date"]).date(),
                        remaining_story_points=int(point["remaining_story_points"]),
                        remaining_tasks=int(point["remaining_tasks"]),
                        ideal_remaining=int(point["ideal_remaining"]),
                        team_capacity=float(point.get("team_capacity", 1.0)),
                    )
                )
        return points

    def add_burndown_point(self, remaining_story_points: int, remaining_tasks: int, team_capacity: float = 1.0) -> None:
        data: List[Dict[str, Any]] = self.get_json_field('burndown_data', [])
        today = date.today()
        ideal_remaining = self._calculate_ideal_remaining(today)

        # remove point for today if exists
        data = [p for p in data if p.get("date") != today.isoformat()]
        data.append({
            "date": today.isoformat(),
            "remaining_story_points": int(remaining_story_points),
            "remaining_tasks": int(remaining_tasks),
            "ideal_remaining": int(ideal_remaining),
            "team_capacity": float(team_capacity),
        })
        data.sort(key=lambda x: x["date"])
        self.set_json_field('burndown_data', data)

    def _calculate_ideal_remaining(self, current_date: date) -> int:
        if not self.start_date or not self.end_date or not self.story_points_committed:
            return 0
        total_days = (self.end_date - self.start_date).days + 1
        days_elapsed = max(0, (current_date - self.start_date).days + 1)
        if days_elapsed >= total_days:
            return 0
        progress = days_elapsed / total_days
        return int(self.story_points_committed * (1 - progress))

    # -------------------------------------------------------------------------
    # Métricas e Analytics
    # -------------------------------------------------------------------------
    def calculate_sprint_metrics(self) -> SprintMetrics:
        # Velocity achievement
        velocity_achievement = self.velocity_achievement

        # Scope completion
        scope_completion = self.progress_percentage

        # Quality score (teste + bugs)
        test_coverage_score = float(self.test_coverage or 0)
        if self.bugs_introduced <= 0:
            bug_ratio_score = 100.0  # sem bugs introduzidos => “perfeito” neste componente
        else:
            bug_ratio = self.bugs_resolved / max(self.bugs_introduced, 1)
            bug_ratio_score = max(0.0, min(bug_ratio * 100.0, 100.0))
        quality_score = (test_coverage_score + bug_ratio_score) / 2.0

        # Team satisfaction (usando customer_satisfaction como proxy)
        team_satisfaction = float(self.customer_satisfaction or 5) * 10.0  # 1-10 => 0-100

        # Burndown health & Risk level
        burndown_health = self._assess_burndown_health()
        risk_level = self._assess_risk_level()

        return SprintMetrics(
            velocity_achievement=velocity_achievement,
            scope_completion=scope_completion,
            quality_score=quality_score,
            team_satisfaction=team_satisfaction,
            burndown_health=burndown_health,
            risk_level=risk_level,
        )

    def _assess_burndown_health(self) -> str:
        points = self.get_burndown_data_list()
        if len(points) < 2:
            return "insufficient_data"
        latest = points[-1]
        # dentro de 10% do ideal = ok; até 30% = atrás; >30% = crítico
        if latest.remaining_story_points <= latest.ideal_remaining * 1.1:
            return "on_track"
        elif latest.remaining_story_points <= latest.ideal_remaining * 1.3:
            return "behind"
        else:
            return "critical"

    def _assess_risk_level(self) -> str:
        risks = self.get_risk_factors_list()
        imps = self.get_impediments_list()

        critical_issues = len([r for r in risks if r.get("severity") == "critical" and r.get("status") == "active"])
        high_issues = len([r for r in risks if r.get("severity") == "high" and r.get("status") == "active"])
        high_impediments = len([i for i in imps if i.get("impact") == "high" and i.get("status") in ("open", "in_progress")])

        if critical_issues > 0:
            return "critical"
        elif high_issues > 1 or high_impediments > 1:
            return "high"
        elif high_issues > 0 or high_impediments > 0:
            return "medium"
        else:
            return "low"

    # -------------------------------------------------------------------------
    # TDD/TDAH hooks (placeholders de agregação)
    # -------------------------------------------------------------------------
    def calculate_tdd_adoption_rate(self) -> float:
        """Aggregate TDD adoption across sprint items (placeholder)."""
        return 0.0

    def get_tdd_effectiveness_score(self) -> float:
        """Aggregate TDD effectiveness across sprint items (placeholder)."""
        return 0.0

    def calculate_cognitive_load_score(self) -> float:
        """Calculate cognitive load score for sprint complexity (1-10)."""
        base_complexity = min(self.story_points_committed / 10.0, 10.0)

        team_size = len(self.get_team_members_list())
        if team_size > 8:
            base_complexity *= 1.2
        elif team_size < 4:
            base_complexity *= 1.1

        active_risks = len([r for r in self.get_risk_factors_list() if r.get("status") == "active"])
        open_impediments = len([i for i in self.get_impediments_list() if i.get("status") in ("open", "in_progress")])
        complexity_modifier = 1 + (active_risks * 0.1) + (open_impediments * 0.15)

        return float(min(base_complexity * complexity_modifier, 10.0))

    def get_tdah_friendly_recommendations(self) -> List[str]:
        recs: List[str] = []
        complexity = self.calculate_cognitive_load_score()

        if complexity > 8:
            recs.append("🧠 Sprint com alta complexidade - quebre histórias grandes em menores.")
            recs.append("📋 Use acompanhamento visual e check-ins frequentes.")

        if len(self.get_impediments_list()) > 2:
            recs.append("🚫 Muitos impedimentos - priorize a remoção de bloqueios.")

        if self.story_points_committed > 50:
            recs.append("⏰ Sprint grande - agende revisões de progresso regulares.")

        if len(self.get_team_members_list()) > 8:
            recs.append("👥 Time grande - considere sub-times por área/feature.")

        return recs

    # -------------------------------------------------------------------------
    # JSON helpers específicos
    # -------------------------------------------------------------------------
    def get_demo_feedback_list(self) -> List[Dict[str, Any]]:
        fb = self.get_json_field('demo_feedback', [])
        return fb if isinstance(fb, list) else []

    def add_demo_feedback(self, stakeholder: str, rating: int, comments: str) -> None:
        fb = self.get_demo_feedback_list()
        fb.append(
            {
                "stakeholder": stakeholder,
                "rating": int(rating),  # 1-10
                "comments": comments,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self.set_json_field('demo_feedback', fb)

    def get_improvement_actions_list(self) -> List[Dict[str, Any]]:
        acts = self.get_json_field('improvement_actions', [])
        return acts if isinstance(acts, list) else []

    def add_improvement_action(self, action: str, assignee: Optional[int] = None, priority: str = "medium") -> None:
        acts = self.get_improvement_actions_list()
        acts.append(
            {
                "id": len(acts) + 1,
                "action": action,
                "assignee": assignee,
                "priority": priority,  # low, medium, high
                "status": "open",      # open, in_progress, completed
                "created_at": datetime.now().isoformat(),
            }
        )
        self.set_json_field('improvement_actions', acts)

    # -------------------------------------------------------------------------
    # Business helpers
    # -------------------------------------------------------------------------
    def can_be_started(self) -> bool:
        return self.status_enum == SprintStatus.PLANNING and self._validate_sprint_start()

    def can_be_completed(self) -> bool:
        return self.status_enum in (SprintStatus.ACTIVE, SprintStatus.REVIEW) and self._validate_sprint_completion()

    def get_sprint_summary(self) -> Dict[str, Any]:
        metrics = self.calculate_sprint_metrics()
        return {
            "basic_info": {
                "sprint_key": self.sprint_key,
                "sprint_name": self.sprint_name,
                "status": self.status,
                "duration_days": self.duration_days,
                "days_remaining": self.days_remaining,
            },
            "metrics": {
                "velocity_achievement": metrics.velocity_achievement,
                "scope_completion": metrics.scope_completion,
                "quality_score": metrics.quality_score,
                "team_satisfaction": metrics.team_satisfaction,
            },
            "health": {
                "status": self.health_status,
                "burndown_health": metrics.burndown_health,
                "risk_level": metrics.risk_level,
                "active_impediments": len([i for i in self.get_impediments_list() if i.get("status") in ("open", "in_progress")]),
            },
            "team": {
                "team_size": len(self.get_team_members_list()),
                "development_team_size": len(self.get_development_team_list()),
                "has_scrum_master": self.scrum_master_id is not None,
                "has_product_owner": self.product_owner_id is not None,
            },
            "progress": {
                "story_points_completed": self.story_points_completed,
                "story_points_committed": self.story_points_committed,
                "tasks_completed": self.tasks_completed,
                "tasks_committed": self.tasks_committed,
                "progress_percentage": self.progress_percentage,
            },
        }
