#!/usr/bin/env python3
"""
🎯 MODELS - Sprint Milestones ORM Model

Sprint milestone management with quality gates, stakeholder communication,
risk management, and comprehensive tracking capabilities.

Maps to sprint_milestones table from migration 009_sprint_system_and_advanced_features.sql

Usage:
    from streamlit_extension.models.sprint_milestone import (
        SprintMilestoneORM, MilestoneType, MilestoneStatus
    )

    milestone = SprintMilestoneORM(
        sprint_id=1,
        milestone_name="User Authentication Complete",
        milestone_description="Complete OAuth 2.0 implementation with security validation",
        milestone_type=MilestoneType.DELIVERABLE.value,
        target_date=date(2025, 8, 25)
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Integer, String, Text, Date, Boolean, DateTime, DECIMAL, ForeignKey, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import AuditMixin, JSONFieldMixin


# =============================================================================
# Enums
# =============================================================================

class MilestoneType(Enum):
    """Sprint milestone types."""
    DELIVERABLE = "deliverable"   # Tangible deliverable completion
    CHECKPOINT = "checkpoint"     # Progress checkpoint
    REVIEW = "review"             # Review milestone
    DEMO = "demo"                 # Demo/presentation milestone
    RELEASE = "release"           # Release milestone


class MilestoneStatus(Enum):
    """Milestone status progression."""
    PLANNED = "planned"           # Initial planning state
    IN_PROGRESS = "in_progress"   # Active work in progress
    AT_RISK = "at_risk"           # Behind schedule or issues
    COMPLETED = "completed"       # Successfully completed
    MISSED = "missed"             # Deadline missed


class QualityStatus(Enum):
    """Quality gate status."""
    PENDING = "pending"           # Quality check not started
    IN_REVIEW = "in_review"       # Under quality review
    PASSED = "passed"             # Quality gates passed
    FAILED = "failed"             # Quality gates failed
    WAIVED = "waived"             # Quality requirements waived


class UpdateFrequency(Enum):
    """Status update frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"
    MONTHLY = "monthly"
    AS_NEEDED = "as_needed"


# =============================================================================
# Typed DTOs
# =============================================================================

@dataclass
class MilestoneProgress:
    """Milestone progress calculation result."""
    completion_percentage: float
    days_remaining: int
    is_on_track: bool
    risk_level: str
    blockers_count: int
    quality_score: float


@dataclass
class StakeholderInfo:
    """Stakeholder information structure."""
    user_id: int
    name: str
    role: str
    contact_method: str
    notification_preferences: Dict[str, bool]


# =============================================================================
# ORM Model
# =============================================================================

class SprintMilestoneORM(Base, AuditMixin, JSONFieldMixin):
    """
    Complete Sprint Milestone ORM model with comprehensive milestone management.

    Maps to sprint_milestones table with fields supporting milestone tracking,
    quality gates, stakeholder management, and risk mitigation.
    """
    __tablename__ = "sprint_milestones"

    # Primary Key and Relations
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sprint_id: Mapped[int] = mapped_column(Integer, ForeignKey("sprints.id"), nullable=False)

    # Milestone Identity
    milestone_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Milestone Details
    milestone_description: Mapped[Optional[str]] = mapped_column(Text)
    milestone_type: Mapped[str] = mapped_column(String(50), default=MilestoneType.DELIVERABLE.value)
    success_criteria: Mapped[Optional[str]] = mapped_column(JSON)  # Array of success criteria

    # Milestone Planning
    target_date: Mapped[Optional[date]] = mapped_column(Date)
    planned_effort: Mapped[Optional[int]] = mapped_column(Integer)  # Minutes
    dependencies: Mapped[Optional[str]] = mapped_column(JSON)  # Array of task/milestone IDs
    deliverables: Mapped[Optional[str]] = mapped_column(JSON)  # Array of expected deliverables

    # Milestone Status
    status: Mapped[str] = mapped_column(String(50), default=MilestoneStatus.PLANNED.value)
    completion_percentage: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), default=Decimal("0.00"))
    actual_completion_date: Mapped[Optional[date]] = mapped_column(Date)

    # Quality Gates
    quality_criteria: Mapped[Optional[str]] = mapped_column(JSON)  # Quality requirements
    quality_status: Mapped[Optional[str]] = mapped_column(String(50))  # e.g. QualityStatus.PASSED.value
    quality_notes: Mapped[Optional[str]] = mapped_column(Text)
    sign_off_required: Mapped[bool] = mapped_column(Boolean, default=False)
    signed_off_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    signed_off_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Stakeholder Management
    stakeholders: Mapped[Optional[str]] = mapped_column(JSON)           # Array of stakeholder user IDs
    communication_plan: Mapped[Optional[str]] = mapped_column(JSON)     # Communication strategy/config
    status_update_frequency: Mapped[str] = mapped_column(String(50), default=UpdateFrequency.WEEKLY.value)

    # Risk Management
    risk_factors: Mapped[Optional[str]] = mapped_column(JSON)           # Array of risk factors
    mitigation_plans: Mapped[Optional[str]] = mapped_column(JSON)       # Mitigation strategies
    contingency_plans: Mapped[Optional[str]] = mapped_column(JSON)      # Backup plans
    escalation_path: Mapped[Optional[str]] = mapped_column(JSON)        # Escalation procedures

    # Integration & External
    external_dependencies: Mapped[Optional[str]] = mapped_column(JSON)  # External dependencies
    external_milestone_id: Mapped[Optional[str]] = mapped_column(String(100))
    external_system: Mapped[Optional[str]] = mapped_column(String(50))

    # Enhanced Audit
    achieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    # sprint = relationship("SprintORM", back_populates="milestones")
    # sign_off_user = relationship("UserORM", foreign_keys=[signed_off_by])

    # -------------------------------------------------------------------------
    # Repr
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"<SprintMilestoneORM(id={self.id}, sprint_id={self.sprint_id}, "
            f"name='{self.milestone_name}', status='{self.status}')>"
        )

    # -------------------------------------------------------------------------
    # Enum helpers (robust to unexpected DB values)
    # -------------------------------------------------------------------------
    @property
    def milestone_type_enum(self) -> MilestoneType:
        try:
            return MilestoneType(self.milestone_type)
        except ValueError:
            return MilestoneType.DELIVERABLE

    @property
    def status_enum(self) -> MilestoneStatus:
        try:
            return MilestoneStatus(self.status)
        except ValueError:
            return MilestoneStatus.PLANNED

    @property
    def quality_status_enum(self) -> Optional[QualityStatus]:
        if not self.quality_status:
            return None
        try:
            return QualityStatus(self.quality_status)
        except ValueError:
            return None

    @property
    def update_frequency_enum(self) -> UpdateFrequency:
        try:
            return UpdateFrequency(self.status_update_frequency)
        except ValueError:
            return UpdateFrequency.WEEKLY

    # -------------------------------------------------------------------------
    # Computed properties
    # -------------------------------------------------------------------------
    @property
    def is_completed(self) -> bool:
        return self.status_enum == MilestoneStatus.COMPLETED

    @property
    def is_at_risk(self) -> bool:
        return self.status_enum == MilestoneStatus.AT_RISK

    @property
    def is_overdue(self) -> bool:
        if not self.target_date or self.is_completed:
            return False
        return date.today() > self.target_date

    @property
    def days_remaining(self) -> int:
        if not self.target_date or self.is_completed:
            return 0
        today = date.today()
        if today > self.target_date:
            return 0
        return (self.target_date - today).days + 1

    @property
    def progress_percentage_float(self) -> float:
        return float(self.completion_percentage) if self.completion_percentage is not None else 0.0

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------
    def start_milestone(self) -> bool:
        """Move from PLANNED to IN_PROGRESS."""
        if self.status_enum != MilestoneStatus.PLANNED:
            return False
        self.status = MilestoneStatus.IN_PROGRESS.value
        return True

    def set_completion_percentage(self, value: float) -> None:
        """Safely set completion percentage (0-100)."""
        clamped = max(0.0, min(100.0, value))
        self.completion_percentage = Decimal(f"{clamped:.2f}")

    def complete_milestone(self, completed_by: Optional[int] = None) -> bool:
        """Complete the milestone with validation of quality gates/sign-off."""
        if not self._validate_completion():
            return False

        self.status = MilestoneStatus.COMPLETED.value
        self.completion_percentage = Decimal("100.00")
        self.actual_completion_date = date.today()
        self.achieved_at = datetime.now()

        # Optional sign-off record (if required and provided)
        if self.sign_off_required and completed_by:
            self.signed_off_by = completed_by
            self.signed_off_at = datetime.now()

        return True

    def _validate_completion(self) -> bool:
        """Validate milestone can be completed."""
        # Must be fully complete
        if self.progress_percentage_float < 100.0:
            return False

        # If quality criteria exist, there must be an evaluated quality_status
        if self.quality_criteria and not self.quality_status:
            return False

        # Cannot complete with failed quality
        if self.quality_status_enum == QualityStatus.FAILED:
            return False

        # If sign-off required, ensure it has been provided (or will be set by caller)
        if self.sign_off_required and not self.signed_off_by:
            # Allow completion if caller will set sign-off via completed_by
            # The complete_milestone method will set it if provided.
            # If not provided, block.
            return False

        return True

    def mark_at_risk(self, reason: str = "") -> None:
        """Mark milestone as at risk and register reason in risk factors."""
        self.status = MilestoneStatus.AT_RISK.value
        if reason:
            risk_factors = self.get_risk_factors_list()
            risk_factors.append({
                "type": "status_change",
                "description": f"Marked at risk: {reason}",
                "severity": "medium",
                "identified_at": datetime.now().isoformat()
            })
            self.risk_factors = self.serialize_json(risk_factors)

    def mark_missed(self, reason: str = "") -> None:
        """Mark milestone as missed."""
        self.status = MilestoneStatus.MISSED.value
        if reason:
            self.quality_notes = f"MISSED: {reason}"

    # -------------------------------------------------------------------------
    # Success Criteria
    # -------------------------------------------------------------------------
    def get_success_criteria_list(self) -> List[Dict[str, Any]]:
        if not self.success_criteria:
            return []
        data = self.deserialize_json(self.success_criteria)
        return data if isinstance(data, list) else []

    def add_success_criterion(self, description: str, weight: float = 1.0, is_critical: bool = False) -> None:
        criteria = self.get_success_criteria_list()
        criteria.append({
            "id": len(criteria) + 1,
            "description": description,
            "weight": weight,
            "is_critical": is_critical,
            "status": "pending",      # pending, met, not_met
            "verified_at": None,
            "verified_by": None
        })
        self.success_criteria = self.serialize_json(criteria)

    def update_criterion_status(self, criterion_id: int, status: str, verified_by: Optional[int] = None) -> bool:
        criteria = self.get_success_criteria_list()
        for c in criteria:
            if c.get("id") == criterion_id:
                c["status"] = status
                c["verified_at"] = datetime.now().isoformat()
                if verified_by:
                    c["verified_by"] = verified_by
                self.success_criteria = self.serialize_json(criteria)
                self._recalculate_progress()
                return True
        return False

    def _recalculate_progress(self) -> None:
        criteria = self.get_success_criteria_list()
        if not criteria:
            return
        total_weight = sum(c.get("weight", 1.0) for c in criteria)
        met_weight = sum(c.get("weight", 1.0) for c in criteria if c.get("status") == "met")
        if total_weight > 0:
            progress = (met_weight / total_weight) * 100
            self.set_completion_percentage(progress)

    # -------------------------------------------------------------------------
    # Deliverables
    # -------------------------------------------------------------------------
    def get_deliverables_list(self) -> List[Dict[str, Any]]:
        if not self.deliverables:
            return []
        data = self.deserialize_json(self.deliverables)
        return data if isinstance(data, list) else []

    def add_deliverable(self, name: str, description: str, responsible_party: Optional[int] = None) -> None:
        items = self.get_deliverables_list()
        items.append({
            "id": len(items) + 1,
            "name": name,
            "description": description,
            "responsible_party": responsible_party,
            "status": "pending",     # pending, in_progress, completed
            "completion_date": None,
            "location": None         # File path, URL, etc.
        })
        self.deliverables = self.serialize_json(items)

    def complete_deliverable(self, deliverable_id: int, location: Optional[str] = None) -> bool:
        items = self.get_deliverables_list()
        for d in items:
            if d.get("id") == deliverable_id:
                d["status"] = "completed"
                d["completion_date"] = date.today().isoformat()
                if location:
                    d["location"] = location
                self.deliverables = self.serialize_json(items)
                return True
        return False

    # -------------------------------------------------------------------------
    # Stakeholders & Communication
    # -------------------------------------------------------------------------
    def get_stakeholders_list(self) -> List[int]:
        if not self.stakeholders:
            return []
        data = self.deserialize_json(self.stakeholders)
        if isinstance(data, list):
            return [int(uid) for uid in data if isinstance(uid, (int, str)) and str(uid).isdigit()]
        return []

    def add_stakeholder(self, user_id: int) -> bool:
        current = self.get_stakeholders_list()
        if user_id not in current:
            current.append(user_id)
            self.stakeholders = self.serialize_json(current)
            return True
        return False

    def remove_stakeholder(self, user_id: int) -> bool:
        current = self.get_stakeholders_list()
        if user_id in current:
            current.remove(user_id)
            self.stakeholders = self.serialize_json(current)
            return True
        return False

    def get_communication_plan(self) -> Dict[str, Any]:
        if not self.communication_plan:
            return {
                "update_frequency": self.status_update_frequency,
                "notification_methods": ["email"],
                "escalation_triggers": [],
                "report_format": "standard"
            }
        data = self.deserialize_json(self.communication_plan)
        return data if isinstance(data, dict) else {}

    def update_communication_plan(self, plan_data: Dict[str, Any]) -> None:
        self.communication_plan = self.serialize_json(plan_data)

    # -------------------------------------------------------------------------
    # Risk Management
    # -------------------------------------------------------------------------
    def get_risk_factors_list(self) -> List[Dict[str, Any]]:
        if not self.risk_factors:
            return []
        data = self.deserialize_json(self.risk_factors)
        return data if isinstance(data, list) else []

    def add_risk_factor(self, description: str, severity: str = "medium", probability: str = "medium") -> None:
        risks = self.get_risk_factors_list()
        risks.append({
            "id": len(risks) + 1,
            "description": description,
            "severity": severity,       # low, medium, high, critical
            "probability": probability, # low, medium, high
            "status": "active",         # active, mitigated, resolved
            "identified_at": datetime.now().isoformat(),
            "mitigation_assigned": False
        })
        self.risk_factors = self.serialize_json(risks)

    def get_mitigation_plans_list(self) -> List[Dict[str, Any]]:
        if not self.mitigation_plans:
            return []
        data = self.deserialize_json(self.mitigation_plans)
        return data if isinstance(data, list) else []

    def add_mitigation_plan(self, risk_id: int, plan: str, responsible_party: Optional[int] = None) -> None:
        plans = self.get_mitigation_plans_list()
        plans.append({
            "id": len(plans) + 1,
            "risk_id": risk_id,
            "plan": plan,
            "responsible_party": responsible_party,
            "status": "planned",    # planned, in_progress, implemented
            "effectiveness": None,
            "created_at": datetime.now().isoformat()
        })
        self.mitigation_plans = self.serialize_json(plans)

    # -------------------------------------------------------------------------
    # Quality Gates
    # -------------------------------------------------------------------------
    def get_quality_criteria_list(self) -> List[Dict[str, Any]]:
        if not self.quality_criteria:
            return []
        data = self.deserialize_json(self.quality_criteria)
        return data if isinstance(data, list) else []

    def add_quality_criterion(self, name: str, description: str, threshold: Optional[float] = None) -> None:
        criteria = self.get_quality_criteria_list()
        criteria.append({
            "id": len(criteria) + 1,
            "name": name,
            "description": description,
            "threshold": threshold,
            "status": "pending",     # pending, passed, failed
            "measured_value": None,
            "evaluated_at": None
        })
        self.quality_criteria = self.serialize_json(criteria)

    def evaluate_quality_gates(self) -> bool:
        """Evaluate all quality gates and update status field accordingly."""
        criteria = self.get_quality_criteria_list()
        if not criteria:
            self.quality_status = QualityStatus.PASSED.value
            return True

        all_passed = all(c.get("status") == "passed" for c in criteria)
        if all_passed:
            self.quality_status = QualityStatus.PASSED.value
            return True

        if any(c.get("status") == "failed" for c in criteria):
            self.quality_status = QualityStatus.FAILED.value
            return False

        if any(c.get("status") == "pending" for c in criteria):
            self.quality_status = QualityStatus.IN_REVIEW.value
            return False

        # If none failed and none pending, consider passed
        self.quality_status = QualityStatus.PASSED.value
        return True

    # -------------------------------------------------------------------------
    # Dependencies
    # -------------------------------------------------------------------------
    def get_dependencies_list(self) -> List[Dict[str, Any]]:
        if not self.dependencies:
            return []
        data = self.deserialize_json(self.dependencies)
        return data if isinstance(data, list) else []

    def add_dependency(self, dependency_type: str, dependency_id: int, description: str = "") -> None:
        deps = self.get_dependencies_list()
        deps.append({
            "id": len(deps) + 1,
            "type": dependency_type,  # task, milestone, external
            "dependency_id": dependency_id,
            "description": description,
            "status": "active",       # active, resolved, blocked
            "blocking": True
        })
        self.dependencies = self.serialize_json(deps)

    # -------------------------------------------------------------------------
    # Progress & Summary
    # -------------------------------------------------------------------------
    def calculate_milestone_progress(self) -> MilestoneProgress:
        completion_percentage = self.progress_percentage_float
        days_remaining = self.days_remaining

        # On-track assessment
        is_on_track = (
            not self.is_overdue and
            self.status_enum not in [MilestoneStatus.AT_RISK, MilestoneStatus.MISSED]
        )

        # Risk level assessment
        risks = self.get_risk_factors_list()
        critical_risks = sum(1 for r in risks if r.get("severity") == "critical" and r.get("status") == "active")
        high_risks = sum(1 for r in risks if r.get("severity") == "high" and r.get("status") == "active")

        if critical_risks > 0:
            risk_level = "critical"
        elif high_risks > 1:
            risk_level = "high"
        elif high_risks > 0 or self.is_overdue:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Blockers count
        blockers_count = sum(
            1 for d in self.get_dependencies_list()
            if d.get("status") == "blocked" and d.get("blocking")
        )

        # Quality score
        quality_criteria = self.get_quality_criteria_list()
        if quality_criteria:
            passed = sum(1 for c in quality_criteria if c.get("status") == "passed")
            quality_score = (passed / len(quality_criteria)) * 100
        else:
            quality_score = 100.0

        return MilestoneProgress(
            completion_percentage=completion_percentage,
            days_remaining=days_remaining,
            is_on_track=is_on_track,
            risk_level=risk_level,
            blockers_count=blockers_count,
            quality_score=quality_score
        )

    def get_milestone_summary(self) -> Dict[str, Any]:
        progress = self.calculate_milestone_progress()
        return {
            "basic_info": {
                "id": self.id,
                "sprint_id": self.sprint_id,
                "name": self.milestone_name,
                "description": self.milestone_description,
                "type": self.milestone_type,
                "status": self.status
            },
            "timeline": {
                "target_date": self.target_date.isoformat() if self.target_date else None,
                "actual_completion_date": self.actual_completion_date.isoformat() if self.actual_completion_date else None,
                "days_remaining": progress.days_remaining,
                "is_overdue": self.is_overdue,
                "planned_effort": self.planned_effort
            },
            "progress": {
                "completion_percentage": progress.completion_percentage,
                "is_on_track": progress.is_on_track,
                "risk_level": progress.risk_level,
                "blockers_count": progress.blockers_count
            },
            "quality": {
                "quality_status": self.quality_status,
                "quality_score": progress.quality_score,
                "sign_off_required": self.sign_off_required,
                "is_signed_off": bool(self.signed_off_by)
            },
            "stakeholders": {
                "stakeholder_count": len(self.get_stakeholders_list()),
                "update_frequency": self.status_update_frequency,
                "has_communication_plan": bool(self.communication_plan)
            },
            "risk_management": {
                "risk_count": len(self.get_risk_factors_list()),
                "mitigation_plans_count": len(self.get_mitigation_plans_list()),
                "has_contingency": bool(self.contingency_plans)
            },
            "deliverables": {
                "deliverable_count": len(self.get_deliverables_list()),
                "success_criteria_count": len(self.get_success_criteria_list()),
                "dependency_count": len(self.get_dependencies_list())
            },
            "external": {
                "has_external_dependencies": bool(self.external_dependencies),
                "external_system": self.external_system,
                "external_milestone_id": self.external_milestone_id
            }
        }

    # -------------------------------------------------------------------------
    # Factories
    # -------------------------------------------------------------------------
    @classmethod
    def create_standard_milestone(
        cls,
        sprint_id: int,
        name: str,
        target_date: date,
        milestone_type: MilestoneType = MilestoneType.DELIVERABLE
    ) -> "SprintMilestoneORM":
        """Create a standard milestone with sane defaults."""
        return cls(
            sprint_id=sprint_id,
            milestone_name=name,
            milestone_type=milestone_type.value,
            target_date=target_date,
            status=MilestoneStatus.PLANNED.value,
            completion_percentage=Decimal("0.00")
        )
