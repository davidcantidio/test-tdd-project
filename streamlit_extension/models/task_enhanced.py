#!/usr/bin/env python3
"""
✅ MODELS - Enhanced Task Models

Enhanced task models combining existing dataclass functionality with new SQLAlchemy ORM model.
Includes 12 new fields from migration 008 and comprehensive TDD/TDAH integration.

Usage:
    from streamlit_extension.models.task_enhanced import TaskORM, Task

    # SQLAlchemy ORM model (new)
    task_orm = TaskORM(title="Implement authentication", epic_id=1, task_key="T-001")

    # Original dataclass (compatibility)
    task_dc = Task(id=1, task_key="T-001", epic_id=1, title="Test task")

Features:
- TaskORM: New SQLAlchemy model with enhanced fields
- Task: Original dataclass for backward compatibility
- Migration 008 fields: 12 new fields integrated
- TDD workflow support with phase management (via TDDWorkflowMixin)
- TDAH optimization with complexity scoring
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from enum import Enum

from sqlalchemy import (
    Integer,
    String,
    Text,
    Date,
    ForeignKey,
    JSON,
    Boolean,
    DECIMAL,
    UniqueConstraint,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property

from .base import Base
from .mixins import AuditMixin, JSONFieldMixin, TDDWorkflowMixin, TDAHOptimizationMixin, TDDPhase

logger = logging.getLogger(__name__)


# =============================================================================
# Task Enums (Enhanced from original)
# =============================================================================

class TaskStatus(Enum):
    """Enhanced task status with additional states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"
    READY = "ready"
    IN_REVIEW = "in_review"
    DEPLOYED = "deployed"


class TaskType(Enum):
    """Enhanced task types with additional categories."""
    DEVELOPMENT = "development"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REFACTORING = "refactoring"
    BUG_FIX = "bug_fix"
    SPIKE = "spike"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"
    RESEARCH = "research"


class DependencyType(Enum):
    """Dependency types for task relationships."""
    BLOCKING = "blocking"
    TDD_SEQUENCE = "tdd_sequence"
    RELATED = "related"
    OPTIONAL = "optional"
    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKLOG = 5


# =============================================================================
# SQLAlchemy Task ORM Model (New Enhanced Model)
# =============================================================================

class TaskORM(Base, AuditMixin, JSONFieldMixin, TDDWorkflowMixin, TDAHOptimizationMixin):
    """
    Enhanced SQLAlchemy Task ORM model with migration 008 fields.

    Comprehensive task management with TDD workflow integration, TDAH optimization,
    dependency management, and enhanced project planning capabilities.

    Features:
    - All original framework_tasks fields
    - 12 new fields from migration 008
    - TDD workflow integration with phase management (from TDDWorkflowMixin)
    - TDAH cognitive complexity scoring
    - Task dependencies and relationships
    - Milestone tracking and planning
    - Comprehensive audit trail
    """

    __tablename__ = "framework_tasks"

    # Primary Key and Core Fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_key: Mapped[str] = mapped_column(String(50), nullable=False)
    epic_id: Mapped[int] = mapped_column(Integer, ForeignKey("framework_epics.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Description and Content
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Workflow & Classification (status/type here; TDD fields come from TDDWorkflowMixin)
    task_type: Mapped[str] = mapped_column(String(50), default=TaskType.DEVELOPMENT.value)
    status: Mapped[str] = mapped_column(String(50), default=TaskStatus.PENDING.value)

    # Estimation and Tracking
    estimate_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    actual_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    story_points: Mapped[Optional[int]] = mapped_column(Integer)
    position: Mapped[Optional[int]] = mapped_column(Integer)

    # Priority and Planning
    priority: Mapped[int] = mapped_column(Integer, default=3)

    # Task Organization
    task_group: Mapped[Optional[str]] = mapped_column(String(100))
    task_sequence: Mapped[Optional[int]] = mapped_column(Integer)
    parent_task_key: Mapped[Optional[str]] = mapped_column(String(50))

    # Gamification
    points_earned: Mapped[int] = mapped_column(Integer, default=0)
    difficulty_modifier: Mapped[Decimal] = mapped_column(DECIMAL(3, 2), default=Decimal("1.0"))
    streak_bonus: Mapped[int] = mapped_column(Integer, default=0)
    perfectionist_bonus: Mapped[int] = mapped_column(Integer, default=0)
    points_value: Mapped[int] = mapped_column(Integer, default=5)

    # GitHub Integration
    github_issue_number: Mapped[Optional[int]] = mapped_column(Integer)
    github_branch: Mapped[Optional[str]] = mapped_column(String(255))
    github_pr_number: Mapped[Optional[int]] = mapped_column(Integer)

    # User Assignment
    assigned_to: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    reviewer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))

    # Dates
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[Optional[date]] = mapped_column(Date)

    # JSON Fields (note: JSONFieldMixin serializa/deserializa; manter consistência)
    test_plan: Mapped[Optional[str]] = mapped_column(JSON)
    test_specs: Mapped[Optional[str]] = mapped_column(JSON)
    deliverables: Mapped[Optional[str]] = mapped_column(JSON)
    files_touched: Mapped[Optional[str]] = mapped_column(JSON)
    priority_tags: Mapped[Optional[str]] = mapped_column(JSON)
    task_labels: Mapped[Optional[str]] = mapped_column(JSON)
    task_notes: Mapped[Optional[str]] = mapped_column(JSON)  # usado por update_estimate()

    # Risk Management
    risk: Mapped[Optional[str]] = mapped_column(String(20))
    mitigation: Mapped[Optional[str]] = mapped_column(Text)

    # === NEW FIELDS FROM MIGRATION 008 ===

    # Milestone Tracking
    is_milestone: Mapped[bool] = mapped_column(Boolean, default=False)

    # Enhanced Date Planning
    planned_start_date: Mapped[Optional[date]] = mapped_column(Date)
    planned_end_date: Mapped[Optional[date]] = mapped_column(Date)

    # Parent-Child Relationships
    parent_task_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_tasks.id"))

    # Task Ordering
    task_order: Mapped[int] = mapped_column(Integer, default=0)

    # Enhanced Effort Tracking
    original_estimate: Mapped[Optional[int]] = mapped_column(Integer)  # Baseline estimate

    # User Story Relationship
    user_story_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_user_stories.id"))

    # Constraints
    __table_args__ = (
        UniqueConstraint("epic_id", "task_key", name="uq_tasks_epic_key"),
    )

    # Relationships (comentado para evitar dependências cíclicas até serem necessárias)
    # epic = relationship("Epic", back_populates="tasks")
    # user_story = relationship("UserStory", back_populates="tasks")
    # parent_task = relationship("TaskORM", remote_side=[id])
    # child_tasks = relationship("TaskORM", back_populates="parent_task")

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        safe_title = (self.title or "")[:30]
        return f"<TaskORM(id={self.id}, key='{self.task_key}', title='{safe_title}...')>"

    # =============================================================================
    # Enhanced Properties and Methods
    # =============================================================================

    @hybrid_property
    def status_enum(self) -> TaskStatus:
        """Get status as enum."""
        try:
            return TaskStatus(self.status)
        except ValueError:
            return TaskStatus.PENDING

    @status_enum.setter
    def status_enum(self, status: TaskStatus) -> None:
        """Set status from enum."""
        self.status = status.value

    @hybrid_property
    def task_type_enum(self) -> TaskType:
        """Get task type as enum."""
        try:
            return TaskType(self.task_type)
        except ValueError:
            return TaskType.DEVELOPMENT

    @task_type_enum.setter
    def task_type_enum(self, task_type: TaskType) -> None:
        """Set task type from enum."""
        self.task_type = task_type.value

    @hybrid_property
    def priority_enum(self) -> TaskPriority:
        """Get priority as enum."""
        try:
            return TaskPriority(self.priority)
        except ValueError:
            return TaskPriority.MEDIUM

    @priority_enum.setter
    def priority_enum(self, priority: TaskPriority) -> None:
        """Set priority from enum."""
        self.priority = priority.value

    @hybrid_property
    def is_tdd_task(self) -> bool:
        """Check if this is a TDD task (fields from TDDWorkflowMixin)."""
        # tdd_order, tdd_phase e tdd_skip_reason são definidos no mixin
        return (
            getattr(self, "tdd_order", None) is not None
            and getattr(self, "tdd_phase", None) is not None
            and not getattr(self, "tdd_skip_reason", None)
        )

    @hybrid_property
    def is_blocked(self) -> bool:
        """Check if task is blocked."""
        return self.status == TaskStatus.BLOCKED.value

    @hybrid_property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status in (TaskStatus.COMPLETED.value, TaskStatus.DEPLOYED.value)

    @hybrid_property
    def effort_estimate(self) -> int:
        """Get effort estimate with fallback logic."""
        if self.estimate_minutes:
            return self.estimate_minutes
        elif self.original_estimate:
            return self.original_estimate
        elif self.story_points:
            return self.story_points * 30  # 30 minutes per story point
        else:
            return 60  # Default 1 hour

    @hybrid_property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date:
            return False
        return self.due_date < date.today() and not self.is_completed

    @hybrid_property
    def days_until_due(self) -> Optional[int]:
        """Get days until due date."""
        if not self.due_date:
            return None
        return (self.due_date - date.today()).days

    # =============================================================================
    # Acceptance Criteria Management (usa o campo do TDDWorkflowMixin)
    # =============================================================================

    def get_acceptance_criteria(self) -> List[Dict[str, Any]]:
        """Get acceptance criteria as structured list."""
        return self.get_json_field("acceptance_criteria", [])

    def add_acceptance_criterion(
        self, criterion: str, priority: str = "must", validation_method: str = ""
    ) -> bool:
        """Add acceptance criterion."""
        criterion_obj = {
            "id": len(self.get_acceptance_criteria()) + 1,
            "criterion": criterion,
            "priority": priority,  # must, should, could, wont
            "validation_method": validation_method,
            "status": "pending",  # pending, verified, failed
            "notes": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.append_to_json_array("acceptance_criteria", criterion_obj)

    def update_criterion_status(self, criterion_id: int, status: str, notes: str = "") -> bool:
        """Update acceptance criterion status."""
        criteria = self.get_acceptance_criteria()
        for criterion in criteria:
            if criterion.get("id") == criterion_id:
                criterion["status"] = status
                criterion["notes"] = notes
                criterion["validated_at"] = datetime.now(timezone.utc).isoformat()
                return self.set_json_field("acceptance_criteria", criteria)
        return False

    # =============================================================================
    # Task Hierarchy Management
    # =============================================================================

    def is_parent_task(self) -> bool:
        """Check if this task has child tasks."""
        # Sem sessão ativa para consulta de filhos: inferência mínima
        return self.is_milestone

    def is_child_task(self) -> bool:
        """Check if this task has a parent."""
        return self.parent_task_id is not None

    def calculate_hierarchy_depth(self) -> int:
        """Calculate depth in task hierarchy (simplificado; sem recursão)."""
        return 1 if self.parent_task_id else 0

    # =============================================================================
    # Milestone Management
    # =============================================================================

    def make_milestone(self, milestone_name: str = "") -> None:
        """Convert task to milestone."""
        self.is_milestone = True
        if milestone_name:
            self.title = f"MILESTONE: {milestone_name}"

        # Milestones tipicamente possuem características diferentes
        self.task_type = TaskType.DEPLOYMENT.value
        self.points_value = max(self.points_value * 2, 20)  # Maior pontuação

    def remove_milestone_status(self) -> None:
        """Remove milestone status."""
        self.is_milestone = False
        if (self.title or "").startswith("MILESTONE: "):
            self.title = (self.title or "").replace("MILESTONE: ", "", 1)

    # =============================================================================
    # Planning and Estimation
    # =============================================================================

    def update_planned_dates(self, start_date: date, end_date: date) -> bool:
        """Update planned start and end dates with validation."""
        if start_date > end_date:
            logger.warning("Start date cannot be after end date")
            return False
        self.planned_start_date = start_date
        self.planned_end_date = end_date
        return True

    def calculate_planned_duration_days(self) -> Optional[int]:
        """Calculate planned duration in days."""
        if self.planned_start_date and self.planned_end_date:
            return (self.planned_end_date - self.planned_start_date).days + 1
        return None

    def update_estimate(self, new_estimate: int, reason: str = "") -> None:
        """Update task estimate while preserving original for comparison."""
        if self.original_estimate is None:
            self.original_estimate = self.estimate_minutes or 0

        self.estimate_minutes = new_estimate

        # Log a justificativa da mudança em task_notes (JSON)
        if reason:
            notes = self.get_json_field("task_notes", [])
            notes.append(
                {
                    "type": "estimate_change",
                    "old_estimate": self.original_estimate,
                    "new_estimate": new_estimate,
                    "reason": reason,
                    "changed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            self.set_json_field("task_notes", notes)

    def calculate_estimate_accuracy(self) -> Optional[float]:
        """Calculate estimate accuracy if task is completed."""
        if not self.is_completed or not self.actual_minutes or self.original_estimate is None:
            return None
        if self.original_estimate == 0:
            return 0.0
        accuracy = 1.0 - abs(self.actual_minutes - self.original_estimate) / float(self.original_estimate)
        return max(0.0, accuracy)

    # =============================================================================
    # TDD Workflow Integration Overrides
    # =============================================================================

    def validate_tdd_workflow(self) -> bool:
        """Validate TDD workflow constraints for this task."""
        if not self.is_tdd_task:
            return True

        # TDD tasks need acceptance criteria
        criteria = self.get_acceptance_criteria()
        if len(criteria) < 1:
            return False

        # TDD tasks need test specifications
        test_specs = self.get_json_field("test_specs", [])
        if len(test_specs) < 1:
            return False

        return True

    def start_tdd_cycle(self) -> bool:
        """Start TDD cycle for this task."""
        if not self.is_tdd_task:
            return False

        # Usar enum padronizado do mixin (valores "Red/Green/Refactor/Complete")
        self.tdd_phase = TDDPhase.RED.value
        self.status = TaskStatus.IN_PROGRESS.value
        self.started_at = datetime.now(timezone.utc)

        return True

    # =============================================================================
    # TDAH Integration Overrides
    # =============================================================================

    def calculate_tdah_complexity(self) -> int:
        """Calculate TDAH cognitive complexity for this task."""
        complexity_score = 1

        # Base complexity from story points
        if self.story_points:
            complexity_score += min(self.story_points // 2, 3)

        # Complexity from acceptance criteria
        criteria_count = len(self.get_acceptance_criteria())
        if criteria_count > 5:
            complexity_score += 2
        elif criteria_count > 2:
            complexity_score += 1

        # Complexity from task type
        type_complexity = {
            TaskType.ANALYSIS: 3,
            TaskType.RESEARCH: 3,
            TaskType.SPIKE: 2,
            TaskType.DEVELOPMENT: 2,
            TaskType.TESTING: 1,
            TaskType.DOCUMENTATION: 1,
            TaskType.BUG_FIX: 2,
            TaskType.REFACTORING: 2,
            TaskType.DEPLOYMENT: 1,
            TaskType.MAINTENANCE: 1,
        }
        complexity_score += type_complexity.get(self.task_type_enum, 1)

        # Complexity from dependencies (simples)
        if self.parent_task_id:
            complexity_score += 1

        # Milestone complexity
        if self.is_milestone:
            complexity_score += 2

        return min(complexity_score, 10)  # Cap at 10

    def estimate_focus_session_duration(self, user_energy_level: int = 5) -> int:
        """Estimate optimal focus session duration for TDAH users."""
        base_duration = 25  # Pomodoro default

        # Ajustar por complexidade
        complexity = self.calculate_tdah_complexity()
        if complexity >= 8:
            base_duration = 15  # sessões mais curtas
        elif complexity <= 3:
            base_duration = 35  # sessões mais longas

        # Ajustar por energia (1-10)
        energy_multiplier = max(0.4, min(user_energy_level / 5.0, 2.0))
        adjusted_duration = int(base_duration * energy_multiplier)

        return max(10, min(adjusted_duration, 90))  # 10-90 min

    # =============================================================================
    # Progress and Analytics
    # =============================================================================

    def calculate_completion_percentage(self) -> float:
        """Calculate task completion percentage."""
        completion_factors = []

        # Status-based completion
        status_completion = {
            TaskStatus.PENDING: 0.0,
            TaskStatus.READY: 0.1,
            TaskStatus.IN_PROGRESS: 0.4,
            TaskStatus.IN_REVIEW: 0.8,
            TaskStatus.COMPLETED: 1.0,
            TaskStatus.DEPLOYED: 1.0,
            TaskStatus.BLOCKED: 0.2,
            TaskStatus.ON_HOLD: 0.2,
            TaskStatus.CANCELLED: 0.0,
        }
        status_score = status_completion.get(self.status_enum, 0.0)
        completion_factors.append(("status", status_score, 0.5))

        # Acceptance criteria completion (usa campo do mixin)
        criteria = self.get_acceptance_criteria()
        if criteria:
            verified_count = sum(1 for c in criteria if c.get("status") in ("verified", "passed"))
            criteria_score = verified_count / len(criteria)
        else:
            criteria_score = 1.0 if self.is_completed else 0.0
        completion_factors.append(("criteria", criteria_score, 0.3))

        # Time-based completion
        if self.actual_minutes and self.effort_estimate:
            time_ratio = min(self.actual_minutes / self.effort_estimate, 1.0)
            time_score = time_ratio if self.is_completed else time_ratio * 0.7
        else:
            time_score = status_score
        completion_factors.append(("time", time_score, 0.2))

        total_score = sum(score * weight for _, score, weight in completion_factors)
        return min(total_score * 100, 100.0)

    def get_task_health(self) -> Dict[str, Any]:
        """Get comprehensive task health assessment."""
        health_data = {
            "overall_health": "good",
            "completion_percentage": self.calculate_completion_percentage(),
            "is_blocked": self.is_blocked,
            "is_overdue": self.is_overdue,
            "estimate_accuracy": self.calculate_estimate_accuracy(),
            "risk_factors": [],
            "recommendations": [],
        }

        # Risk factor assessment
        if self.is_overdue:
            health_data["risk_factors"].append("overdue")
            health_data["recommendations"].append("Prioritize completion or update due date")

        if self.is_blocked:
            health_data["risk_factors"].append("blocked")
            health_data["recommendations"].append("Resolve blocking issues to continue progress")

        if not self.assigned_to:
            health_data["risk_factors"].append("unassigned")
            health_data["recommendations"].append("Assign task to a team member")

        if len(self.get_acceptance_criteria()) == 0:
            health_data["risk_factors"].append("no_criteria")
            health_data["recommendations"].append("Add acceptance criteria for clarity")

        # Overall health calculation
        risk_count = len(health_data["risk_factors"])
        completion = health_data["completion_percentage"]

        if completion >= 90 and risk_count == 0:
            health_data["overall_health"] = "excellent"
        elif completion >= 70 and risk_count <= 1:
            health_data["overall_health"] = "good"
        elif completion >= 40 and risk_count <= 2:
            health_data["overall_health"] = "fair"
        else:
            health_data["overall_health"] = "poor"

        return health_data

    # =============================================================================
    # Utility Methods
    # =============================================================================

    def to_summary_dict(self) -> Dict[str, Any]:
        """Get summary dictionary for API/UI display."""
        return {
            "id": self.id,
            "task_key": self.task_key,
            "epic_id": self.epic_id,
            "user_story_id": self.user_story_id,
            "title": self.title,
            "status": self.status,
            "task_type": self.task_type,
            "priority": self.priority,
            "story_points": self.story_points,
            "is_milestone": self.is_milestone,
            "tdd_phase": getattr(self, "tdd_phase", None),
            "completion_percentage": self.calculate_completion_percentage(),
            "health": self.get_task_health().get("overall_health"),
            "assigned_to": self.assigned_to,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat() if getattr(self, "created_at", None) else None,
            "updated_at": self.updated_at.isoformat() if getattr(self, "updated_at", None) else None,
        }


# =============================================================================
# Original Task Dataclass (Backward Compatibility)
# =============================================================================

@dataclass
class Task:
    """
    Original Task dataclass for backward compatibility.

    This maintains compatibility with existing code while the new
    TaskORM model provides enhanced functionality.
    """
    # Core fields (required)
    id: int
    task_key: str
    epic_id: int
    title: str

    # Description
    description: Optional[str] = None

    # TDD and workflow
    tdd_phase: Optional[str] = None
    tdd_order: Optional[int] = None
    task_type: str = "implementation"
    status: str = "pending"

    # Estimation and tracking
    estimate_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    story_points: Optional[int] = None
    position: Optional[int] = None

    # Priority
    priority: int = 3

    # Task organization
    task_group: Optional[str] = None
    task_sequence: Optional[int] = None
    parent_task_key: Optional[str] = None

    # Gamification
    points_earned: int = 0
    difficulty_modifier: float = 1.0
    streak_bonus: int = 0
    perfectionist_bonus: int = 0
    points_value: int = 5

    # GitHub integration
    github_issue_number: Optional[int] = None
    github_branch: Optional[str] = None
    github_pr_number: Optional[int] = None

    # User assignment
    assigned_to: Optional[int] = None
    reviewer_id: Optional[int] = None

    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    deleted_at: Optional[str] = None
    due_date: Optional[str] = None

    # JSON fields (stored as strings)
    test_plan: Optional[str] = None
    test_specs: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    deliverables: Optional[str] = None
    files_touched: Optional[str] = None
    priority_tags: Optional[str] = None
    task_labels: Optional[str] = None

    # Risk management
    risk: Optional[str] = None
    mitigation: Optional[str] = None
    tdd_skip_reason: Optional[str] = None

    # NEW FIELDS FROM MIGRATION 008 (for compatibility)
    is_milestone: bool = False
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    parent_task_id: Optional[int] = None
    task_order: int = 0
    original_estimate: Optional[int] = None
    user_story_id: Optional[int] = None

    def __post_init__(self):
        """Validation and normalization after initialization."""
        # Normalize priority
        if self.priority < 1:
            self.priority = 1
        elif self.priority > 5:
            self.priority = 5

        # Extract task_group if not defined
        if not self.task_group and self.task_key:
            self._extract_task_group()

    def _extract_task_group(self):
        """Extract task_group from task_key."""
        parts = self.task_key.split(".")
        if len(parts) >= 2:
            if parts[-1].isdigit():
                self.task_group = ".".join(parts[:-1])
                if not self.task_sequence:
                    self.task_sequence = int(parts[-1])
            else:
                self.task_group = self.task_key
                if not self.task_sequence:
                    self.task_sequence = 1

    @property
    def is_tdd_task(self) -> bool:
        """Check if this is a TDD task."""
        return self.tdd_order is not None and self.tdd_phase is not None

    @property
    def is_analysis_task(self) -> bool:
        """Check if this is an analysis task."""
        return self.task_type == "analysis" or self.tdd_skip_reason is not None

    @property
    def is_blocked(self) -> bool:
        """Check if task is blocked."""
        return self.status == TaskStatus.BLOCKED.value

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status in (TaskStatus.COMPLETED.value, TaskStatus.DEPLOYED.value)

    @property
    def effort_estimate(self) -> int:
        """Return effort estimate with fallback logic."""
        if self.estimate_minutes:
            return self.estimate_minutes
        elif self.original_estimate:
            return self.original_estimate
        elif self.story_points:
            return self.story_points * 30
        else:
            return 60

    @property
    def value_density(self) -> float:
        """Calculate value density (value/effort)."""
        effort = max(self.effort_estimate, 1)
        value_score = (6 - self.priority)
        return value_score / effort

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            result[field_name] = value
        return result

    @classmethod
    def from_db_row(cls, row) -> "Task":
        """Create Task from sqlite3.Row."""
        if hasattr(row, "keys"):
            data = dict(row)
        else:
            data = row

        # Filter valid fields
        valid_fields = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        return cls(**filtered_data)


# =============================================================================
# Supporting Classes (preserved from original)
# =============================================================================

@dataclass
class TaskDependency:
    """Task dependency model (preserved for compatibility)."""
    id: int
    task_id: int
    depends_on_task_key: str
    depends_on_task_id: Optional[int] = None
    dependency_type: str = "blocking"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def dependency_type_enum(self) -> DependencyType:
        """Return dependency type as enum."""
        try:
            return DependencyType(self.dependency_type)
        except ValueError:
            return DependencyType.BLOCKING

    @classmethod
    def from_db_row(cls, row) -> "TaskDependency":
        """Create TaskDependency from sqlite3.Row."""
        if hasattr(row, "keys"):
            data = dict(row)
        else:
            data = row

        valid_fields = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        return cls(**filtered_data)


@dataclass
class TaskExecutionResult:
    """Task execution result model (preserved for compatibility)."""
    epic_id: int
    execution_order: List[str]
    parallel_batches: List[List[str]]
    total_tasks: int
    tasks_with_dependencies: int
    total_dependencies: int
    estimated_total_minutes: int
    critical_path_length: int
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Check if there are errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return len(self.warnings) > 0

    @property
    def dependency_percentage(self) -> float:
        """Percentage of tasks with dependencies."""
        if self.total_tasks == 0:
            return 0.0
        return (self.tasks_with_dependencies / self.total_tasks) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "epic_id": self.epic_id,
            "execution_order": self.execution_order,
            "parallel_batches": self.parallel_batches,
            "total_tasks": self.total_tasks,
            "tasks_with_dependencies": self.tasks_with_dependencies,
            "total_dependencies": self.total_dependencies,
            "estimated_total_minutes": self.estimated_total_minutes,
            "critical_path_length": self.critical_path_length,
            "warnings": self.warnings,
            "errors": self.errors,
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
        }


@dataclass
class TaskPriorityScore:
    """Task priority score model (preserved for compatibility)."""
    task_key: str
    total_score: float
    priority_score: float
    value_density_score: float
    unblock_score: float
    critical_path_score: float
    tdd_bonus_score: float
    aging_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_key": self.task_key,
            "total_score": self.total_score,
            "priority_score": self.priority_score,
            "value_density_score": self.value_density_score,
            "unblock_score": self.unblock_score,
            "critical_path_score": self.critical_path_score,
            "tdd_bonus_score": self.tdd_bonus_score,
            "aging_score": self.aging_score,
        }


# =============================================================================
# Custom Exceptions (preserved from original)
# =============================================================================

class TaskModelError(Exception):
    """Base error for task models."""
    pass


class InvalidTaskDataError(TaskModelError):
    """Error for invalid task data."""
    pass


class CyclicDependencyError(TaskModelError):
    """Error for cyclic dependencies."""
    pass


class TaskNotFoundError(TaskModelError):
    """Error for task not found."""
    pass


class TDDWorkflowError(TaskModelError):
    """Error for TDD workflow violations."""
    pass
