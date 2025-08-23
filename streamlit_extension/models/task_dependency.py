#!/usr/bin/env python3
"""
🔗 MODELS - Task Dependencies ORM Model

Task dependency management with complex relationship types, timing constraints,
and risk management integration.

Maps to task_dependencies table from migration 008_task_enhancements_and_dependencies.sql

Usage:
    from streamlit_extension.models.task_dependency import TaskDependencyORM, DependencyType
    
    # Create blocking dependency
    dependency = TaskDependencyORM(
        task_id=1,
        depends_on_task_id=2,
        dependency_type=DependencyType.FINISH_TO_START.value,
        dependency_strength="hard",
        dependency_reason="User authentication must be complete before dashboard implementation"
    )
    
Features:
- Complex dependency relationship types (finish-to-start, start-to-start, etc.)
- Dependency strength management (hard, soft, preferred)
- Lead/lag timing support
- Risk management and mitigation planning
- External dependency tracking
- Comprehensive validation and cycle detection support
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .mixins import AuditMixin, JSONFieldMixin


# =============================================================================
# Enums
# =============================================================================

class DependencyType(Enum):
    """Task dependency relationship types."""
    FINISH_TO_START = "finish_to_start"    # Task B starts when Task A finishes
    START_TO_START = "start_to_start"      # Task B starts when Task A starts
    FINISH_TO_FINISH = "finish_to_finish"  # Task B finishes when Task A finishes
    START_TO_FINISH = "start_to_finish"    # Task B finishes when Task A starts


class DependencyStrength(Enum):
    """Dependency strength levels."""
    HARD = "hard"        # Must be respected, blocks task execution
    SOFT = "soft"        # Should be respected, but can be overridden
    PREFERRED = "preferred"  # Nice to have, minimal impact if ignored


class RiskLevel(Enum):
    """Risk levels for dependencies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# Value Objects
# =============================================================================

@dataclass
class DependencyValidationResult:
    """Result of dependency validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cycle_detected: bool
    cycle_path: Optional[List[int]] = None


# =============================================================================
# ORM Model
# =============================================================================

class TaskDependencyORM(Base, AuditMixin, JSONFieldMixin):
    """
    Complete Task Dependency ORM model with comprehensive relationship management.
    
    Maps to task_dependencies table with 20+ fields supporting complex dependency
    relationships, timing constraints, risk management, and external integrations.
    """
    __tablename__ = "task_dependencies"

    # Primary Key and Relations
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("framework_tasks.id"), nullable=False)
    depends_on_task_id: Mapped[int] = mapped_column(Integer, ForeignKey("framework_tasks.id"), nullable=False)

    # Dependency Type and Strength
    dependency_type: Mapped[str] = mapped_column(String(50), default=DependencyType.FINISH_TO_START.value)
    dependency_strength: Mapped[str] = mapped_column(String(20), default=DependencyStrength.HARD.value)

    # Timing Configuration
    lead_lag_days: Mapped[int] = mapped_column(Integer, default=0)  # Positive = lag, Negative = lead

    # Metadata and Documentation
    dependency_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_reason: Mapped[Optional[str]] = mapped_column(Text)
    business_impact: Mapped[Optional[str]] = mapped_column(Text)

    # Status and Validation
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Risk Management
    risk_level: Mapped[str] = mapped_column(String(20), default=RiskLevel.MEDIUM.value)
    mitigation_plan: Mapped[Optional[str]] = mapped_column(Text)
    alternative_approaches: Mapped[Optional[str]] = mapped_column(Text)

    # External Dependencies
    external_dependency: Mapped[bool] = mapped_column(Boolean, default=False)
    external_system: Mapped[Optional[str]] = mapped_column(String(100))
    external_reference: Mapped[Optional[str]] = mapped_column(String(255))
    external_contact: Mapped[Optional[str]] = mapped_column(JSON)  # Contact info JSON (serialized)

    # Tracking and Audit
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    validated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    removed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Table Constraints
    __table_args__ = (
        # Allow self-dependency ONLY when flagged as external (used to represent non-internal predecessor)
        CheckConstraint(
            "(task_id != depends_on_task_id) OR external_dependency = 1",
            name="ck_no_self_dependency_unless_external",
        ),
        UniqueConstraint("task_id", "depends_on_task_id", name="uq_task_dependency_pair"),
    )

    # Relationships (left commented for integration layer to decide mapping directionality)
    # task = relationship("TaskORM", foreign_keys=[task_id], back_populates="dependencies")
    # depends_on_task = relationship("TaskORM", foreign_keys=[depends_on_task_id])
    # creator = relationship("UserORM", foreign_keys=[created_by])
    # validator = relationship("UserORM", foreign_keys=[validated_by])

    # -------------------------------------------------------------------------
    # Representation
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"<TaskDependencyORM(id={self.id}, task_id={self.task_id}, "
            f"depends_on={self.depends_on_task_id}, type='{self.dependency_type}')>"
        )

    # -------------------------------------------------------------------------
    # Enum helpers
    # -------------------------------------------------------------------------
    @property
    def dependency_type_enum(self) -> DependencyType:
        """Get dependency type as enum."""
        try:
            return DependencyType(self.dependency_type)
        except ValueError:
            return DependencyType.FINISH_TO_START

    @property
    def dependency_strength_enum(self) -> DependencyStrength:
        """Get dependency strength as enum."""
        try:
            return DependencyStrength(self.dependency_strength)
        except ValueError:
            return DependencyStrength.HARD

    @property
    def risk_level_enum(self) -> RiskLevel:
        """Get risk level as enum."""
        try:
            return RiskLevel(self.risk_level)
        except ValueError:
            return RiskLevel.MEDIUM

    # -------------------------------------------------------------------------
    # Derived flags
    # -------------------------------------------------------------------------
    @property
    def is_blocking(self) -> bool:
        """Check if this is a blocking dependency."""
        return self.is_active and self.dependency_strength_enum in (
            DependencyStrength.HARD,
            DependencyStrength.SOFT,
        )

    @property
    def is_external(self) -> bool:
        """Check if this is an external dependency."""
        return self.external_dependency

    @property
    def has_timing_constraint(self) -> bool:
        """Check if dependency has lead/lag timing constraint."""
        return self.lead_lag_days != 0

    # -------------------------------------------------------------------------
    # Validation & Lifecycle
    # -------------------------------------------------------------------------
    def validate_dependency(self) -> DependencyValidationResult:
        """Validate this dependency for consistency and cycles."""
        errors: List[str] = []
        warnings: List[str] = []
        cycle_detected = False
        cycle_path: Optional[List[int]] = None

        # Basic validation
        if (self.task_id == self.depends_on_task_id) and (not self.external_dependency):
            errors.append("Task cannot depend on itself (unless marked as external dependency)")

        if not self.is_active and self.dependency_strength_enum == DependencyStrength.HARD:
            warnings.append("Hard dependency is inactive - may cause scheduling issues")

        if self.external_dependency and not self.external_system:
            warnings.append("External dependency missing system information")

        if self.risk_level_enum == RiskLevel.CRITICAL and not self.mitigation_plan:
            errors.append("Critical risk dependency must have mitigation plan")

        # Timing validation
        if self.dependency_type_enum == DependencyType.START_TO_FINISH and self.lead_lag_days > 0:
            warnings.append("Start-to-finish with positive lag may create scheduling conflicts")

        # Cycle detection requires full graph (performed at service layer)
        is_valid = len(errors) == 0

        return DependencyValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            cycle_detected=cycle_detected,
            cycle_path=cycle_path,
        )

    def mark_validated(self, validated_by: int, notes: str = "") -> bool:
        """Mark dependency as validated."""
        if self.is_validated:
            return False

        validation_result = self.validate_dependency()
        if not validation_result.is_valid:
            return False

        self.is_validated = True
        self.validated_by = validated_by
        self.validated_at = datetime.now()
        if notes:
            self.validation_notes = notes

        return True

    def deactivate(self, reason: str = "") -> None:
        """Deactivate this dependency."""
        self.is_active = False
        self.removed_at = datetime.now()
        if reason:
            self.validation_notes = f"DEACTIVATED: {reason}"

    def reactivate(self) -> bool:
        """Reactivate this dependency after validation."""
        validation_result = self.validate_dependency()
        if not validation_result.is_valid:
            return False

        self.is_active = True
        self.removed_at = None
        return True

    # -------------------------------------------------------------------------
    # External Dependency Management
    # -------------------------------------------------------------------------
    @staticmethod
    def _serialize_json(value: Any) -> str:
        """Serialize arbitrary value to JSON string (UTF-8, safe)."""
        import json
        return json.dumps(value, ensure_ascii=False, default=str)

    @staticmethod
    def _deserialize_json(raw: Optional[str]) -> Any:
        """Deserialize JSON string to Python value with error fallback."""
        import json
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def get_external_contact_info(self) -> Dict[str, Any]:
        """Get external contact information as structured data."""
        data = self._deserialize_json(self.external_contact)
        return data if isinstance(data, dict) else {}

    def set_external_contact_info(self, contact_data: Dict[str, Any]) -> None:
        """Set external contact information."""
        self.external_contact = self._serialize_json(contact_data)

    def update_external_reference(
        self,
        system: str,
        reference: str,
        contact_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update external dependency information."""
        self.external_dependency = True
        self.external_system = system
        self.external_reference = reference
        if contact_data:
            self.set_external_contact_info(contact_data)

    # -------------------------------------------------------------------------
    # Risk Management
    # -------------------------------------------------------------------------
    def assess_risk_level(self) -> RiskLevel:
        """Assess risk level based on dependency characteristics."""
        risk_score = 0

        # Base risk from dependency type
        type_risk_scores = {
            DependencyType.FINISH_TO_START: 1,
            DependencyType.START_TO_START: 2,
            DependencyType.FINISH_TO_FINISH: 2,
            DependencyType.START_TO_FINISH: 3,  # Most complex
        }
        risk_score += type_risk_scores.get(self.dependency_type_enum, 1)

        # External dependency risk
        if self.external_dependency:
            risk_score += 2

        # Timing constraint risk
        if abs(self.lead_lag_days) > 7:  # More than a week lag/lead
            risk_score += 1

        # Hard dependency risk
        if self.dependency_strength_enum == DependencyStrength.HARD:
            risk_score += 1

        # Validation risk
        if not self.is_validated:
            risk_score += 1

        # Map score to risk level
        if risk_score >= 6:
            return RiskLevel.CRITICAL
        elif risk_score >= 4:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def update_risk_assessment(self, auto_assess: bool = True) -> RiskLevel:
        """Update risk level assessment."""
        if auto_assess:
            self.risk_level = self.assess_risk_level().value
        return self.risk_level_enum

    def create_mitigation_plan(self, plan: str, alternatives: Optional[str] = None) -> None:
        """Create risk mitigation plan."""
        self.mitigation_plan = plan
        if alternatives:
            self.alternative_approaches = alternatives

        # Auto-update risk level after creating mitigation
        current = self.assess_risk_level()
        if current == RiskLevel.CRITICAL and self.mitigation_plan:
            # Lower risk level if mitigation exists
            self.risk_level = RiskLevel.HIGH.value

    # -------------------------------------------------------------------------
    # Timing Calculations
    # -------------------------------------------------------------------------
    def calculate_timing_impact(self, predecessor_end_date: datetime) -> datetime:
        """
        Calculate timing impact on successor task target date.

        Notes:
            - For START_TO_START you should pass predecessor START date instead of end date.
            - For START_TO_FINISH / FINISH_TO_FINISH, this returns the *target* date
              aligned with predecessor timing + lag/lead.
        """
        delta = timedelta(days=self.lead_lag_days)

        if self.dependency_type_enum == DependencyType.FINISH_TO_START:
            # Successor starts after predecessor finishes + lag
            return predecessor_end_date + delta

        elif self.dependency_type_enum == DependencyType.START_TO_START:
            # Should use predecessor start; we keep signature simple
            return predecessor_end_date + delta

        elif self.dependency_type_enum == DependencyType.FINISH_TO_FINISH:
            # Successor finishes when predecessor finishes + lag
            return predecessor_end_date + delta

        elif self.dependency_type_enum == DependencyType.START_TO_FINISH:
            # Successor finishes when predecessor starts + lag
            return predecessor_end_date + delta

        return predecessor_end_date

    # -------------------------------------------------------------------------
    # Business Logic & Summaries
    # -------------------------------------------------------------------------
    def get_dependency_summary(self) -> Dict[str, Any]:
        """Get comprehensive dependency summary for reporting."""
        validation_result = self.validate_dependency()

        return {
            "basic_info": {
                "id": self.id,
                "task_id": self.task_id,
                "depends_on_task_id": self.depends_on_task_id,
                "dependency_type": self.dependency_type,
                "dependency_strength": self.dependency_strength,
            },
            "timing": {
                "lead_lag_days": self.lead_lag_days,
                "has_timing_constraint": self.has_timing_constraint,
            },
            "status": {
                "is_active": self.is_active,
                "is_validated": self.is_validated,
                "is_blocking": self.is_blocking,
                "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            },
            "risk": {
                "risk_level": self.risk_level,
                "has_mitigation_plan": bool(self.mitigation_plan),
                "has_alternatives": bool(self.alternative_approaches),
            },
            "external": {
                "is_external": self.external_dependency,
                "external_system": self.external_system,
                "external_reference": self.external_reference,
                "has_contact_info": bool(self.external_contact),
            },
            "validation": {
                "is_valid": validation_result.is_valid,
                "error_count": len(validation_result.errors),
                "warning_count": len(validation_result.warnings),
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
            },
            "documentation": {
                "has_reason": bool(self.dependency_reason),
                "has_business_impact": bool(self.business_impact),
                "has_validation_notes": bool(self.validation_notes),
            },
        }

    def can_be_removed(self) -> bool:
        """Check if dependency can be safely removed."""
        return (not self.is_active) or (self.dependency_strength_enum == DependencyStrength.PREFERRED)

    def get_impact_description(self) -> str:
        """Get human-readable impact description."""
        type_descriptions = {
            DependencyType.FINISH_TO_START: "must finish before this task can start",
            DependencyType.START_TO_START: "must start before this task can start",
            DependencyType.FINISH_TO_FINISH: "must finish before this task can finish",
            DependencyType.START_TO_FINISH: "must start before this task can finish",
        }

        base = type_descriptions.get(
            self.dependency_type_enum,
            "has a dependency relationship with this task",
        )

        if self.lead_lag_days > 0:
            return f"{base} (with {self.lead_lag_days} day lag)"
        elif self.lead_lag_days < 0:
            return f"{base} (with {abs(self.lead_lag_days)} day lead time)"
        else:
            return base

    # -------------------------------------------------------------------------
    # Factory Helpers
    # -------------------------------------------------------------------------
    @classmethod
    def create_standard_dependency(
        cls,
        task_id: int,
        depends_on_task_id: int,
        reason: str,
        created_by: int,
    ) -> "TaskDependencyORM":
        """Create a standard finish-to-start hard dependency."""
        return cls(
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
            dependency_type=DependencyType.FINISH_TO_START.value,
            dependency_strength=DependencyStrength.HARD.value,
            dependency_reason=reason,
            created_by=created_by,
            risk_level=RiskLevel.MEDIUM.value,
        )

    @classmethod
    def create_external_dependency(
        cls,
        task_id: int,
        system: str,
        reference: str,
        reason: str,
        contact_info: Dict[str, Any],
        created_by: int,
    ) -> "TaskDependencyORM":
        """
        Create an external system dependency.

        Note:
            - Uses a self-reference for depends_on_task_id to satisfy FK while
              allowing it via the dedicated CheckConstraint that permits self-
              reference when external_dependency=1.
        """
        dep = cls(
            task_id=task_id,
            depends_on_task_id=task_id,  # allowed by ck_no_self_dependency_unless_external
            dependency_type=DependencyType.FINISH_TO_START.value,
            dependency_strength=DependencyStrength.HARD.value,
            dependency_reason=reason,
            external_dependency=True,
            external_system=system,
            external_reference=reference,
            created_by=created_by,
            risk_level=RiskLevel.HIGH.value,  # External dependencies are higher risk
        )
        dep.set_external_contact_info(contact_info)
        return dep
