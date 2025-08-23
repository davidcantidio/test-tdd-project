#!/usr/bin/env python3
"""
🧩 MODELS - SQLAlchemy Mixins

Common mixins for TDD workflow integration, TDAH optimization, audit trails,
and JSON field handling. Provides reusable functionality across all ORM models.

Usage:
    from streamlit_extension.models.mixins import (
        TDDWorkflowMixin,
        TDAHOptimizationMixin,
        AuditMixin,
        JSONFieldMixin,
        TDDPhase,
        TDAHEnergyLevel,
        CognitiveComplexity,
        TDDTransitionError,
        setup_mixin_event_listeners,
    )

    class Task(Base, TDDWorkflowMixin, TDAHOptimizationMixin, AuditMixin, JSONFieldMixin):
        __tablename__ = "tasks"
        id: Mapped[int] = mapped_column(primary_key=True)

Features:
- TDD workflow state management and validation
- TDAH cognitive load assessment and optimization
- Comprehensive audit trail tracking
- JSON field serialization/deserialization (safe & flexible)
- Timestamp management with timezone support
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
    event,
)
from sqlalchemy.orm import Mapped, Session, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property

logger = logging.getLogger(__name__)

# Public API
__all__ = [
    "TDDWorkflowMixin",
    "TDAHOptimizationMixin",
    "AuditMixin",
    "JSONFieldMixin",
    "TDDPhase",
    "TDAHEnergyLevel",
    "CognitiveComplexity",
    "TDDTransitionError",
    "setup_mixin_event_listeners",
]

# =============================================================================
# Enums & Exceptions
# =============================================================================

class TDDPhase(Enum):
    """TDD cycle phases with clear progression."""
    RED = "Red"            # Test creation phase - write failing tests
    GREEN = "Green"        # Implementation phase - make tests pass
    REFACTOR = "Refactor"  # Optimization phase - improve code quality
    COMPLETE = "Complete"  # Cycle complete - ready for next iteration


class TDDTransitionError(Exception):
    """Exception for invalid TDD phase transitions."""
    pass


class TDAHEnergyLevel(Enum):
    """TDAH energy levels for session optimization."""
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5


class CognitiveComplexity(Enum):
    """Cognitive complexity levels for TDAH task assessment (10-point scale)."""
    TRIVIAL = 1        # < 5 minutes, no decision making
    SIMPLE = 2         # 5-15 minutes, minimal decisions
    EASY = 3           # 15-30 minutes, straightforward work
    MODERATE = 4       # 30-60 minutes, some complexity
    COMPLEX = 5        # 1-2 hours, multiple decisions
    HARD = 6           # 2-4 hours, significant complexity
    VERY_HARD = 7      # 4+ hours, high cognitive load
    EXPERT = 8         # Requires deep expertise
    OVERWHELMING = 9   # May need to be broken down
    EXTREME = 10       # Definitely needs decomposition


# =============================================================================
# TDD Workflow Mixin
# =============================================================================

class TDDWorkflowMixin:
    """
    Mixin providing TDD workflow functionality.

    Features:
    - TDD phase state management
    - Phase transition validation and automation
    - TDD cycle timing and metrics
    - Test requirement tracking
    - Progress calculation based on TDD completion
    """

    # TDD Phase Management
    tdd_phase: Mapped[Optional[str]] = mapped_column(String(20), default=TDDPhase.RED.value)
    tdd_cycle_id: Mapped[Optional[str]] = mapped_column(String(100))
    tdd_order: Mapped[Optional[int]] = mapped_column(Integer)

    # TDD Phase Timing (UTC, timezone-aware)
    red_phase_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    green_phase_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    refactor_phase_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cycle_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # TDD Phase Duration (in minutes)
    red_phase_duration: Mapped[Optional[int]] = mapped_column(Integer)
    green_phase_duration: Mapped[Optional[int]] = mapped_column(Integer)
    refactor_phase_duration: Mapped[Optional[int]] = mapped_column(Integer)
    total_cycle_duration: Mapped[Optional[int]] = mapped_column(Integer)

    # Test Integration (store as JSON Python types)
    test_requirements: Mapped[Optional[List[str]]] = mapped_column(JSON)
    acceptance_criteria: Mapped[Optional[List[str]]] = mapped_column(JSON)
    test_file_path: Mapped[Optional[str]] = mapped_column(String(500))
    test_coverage_percentage: Mapped[Optional[float]] = mapped_column(Float)

    # Test Status
    test_passing_count: Mapped[int] = mapped_column(Integer, default=0)
    test_failing_count: Mapped[int] = mapped_column(Integer, default=0)
    test_total_count: Mapped[int] = mapped_column(Integer, default=0)

    # TDD Phase Completion Flags
    red_phase_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    green_phase_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    refactor_phase_complete: Mapped[bool] = mapped_column(Boolean, default=False)

    # TDD Skip/Bypass
    tdd_skip_reason: Mapped[Optional[str]] = mapped_column(Text)
    is_tdd_exempt: Mapped[bool] = mapped_column(Boolean, default=False)

    @hybrid_property
    def tdd_phase_enum(self) -> Optional[TDDPhase]:
        """Get TDD phase as enum."""
        if self.tdd_phase:
            try:
                return TDDPhase(self.tdd_phase)
            except ValueError:
                return None
        return None

    @tdd_phase_enum.setter
    def tdd_phase_enum(self, phase: Optional[TDDPhase]) -> None:
        """Set TDD phase from enum."""
        self.tdd_phase = phase.value if phase else None

    @hybrid_property
    def is_tdd_task(self) -> bool:
        """Check if this is a TDD task."""
        return (
            not getattr(self, "is_tdd_exempt", False)
            and self.tdd_order is not None
            and self.tdd_phase is not None
        )

    @hybrid_property
    def is_cycle_complete(self) -> bool:
        """Check if TDD cycle is complete."""
        return bool(self.red_phase_complete and self.green_phase_complete and self.refactor_phase_complete)

    def get_valid_transitions(self) -> List[TDDPhase]:
        """Get valid TDD phase transitions from current phase."""
        if not self.tdd_phase_enum:
            return [TDDPhase.RED]

        transitions = {
            TDDPhase.RED: [TDDPhase.GREEN],
            TDDPhase.GREEN: [TDDPhase.REFACTOR, TDDPhase.COMPLETE],
            TDDPhase.REFACTOR: [TDDPhase.COMPLETE, TDDPhase.GREEN],  # can return to GREEN
            TDDPhase.COMPLETE: [],  # terminal
        }
        return transitions.get(self.tdd_phase_enum, [])

    def can_transition_to(self, target_phase: TDDPhase) -> bool:
        """Check if transition to target phase is valid."""
        return target_phase in self.get_valid_transitions()

    def transition_tdd_phase(self, target_phase: TDDPhase, session: Optional[Session] = None) -> bool:
        """
        Transition to target TDD phase with validation.

        Args:
            target_phase: Target TDD phase
            session: Optional database session for validation

        Returns:
            True if transition successful, otherwise raises.

        Raises:
            TDDTransitionError: If transition is invalid or requirements not met.
        """
        if not self.can_transition_to(target_phase):
            raise TDDTransitionError(
                f"Invalid TDD transition from {self.tdd_phase} to {target_phase.value}"
            )

        # Phase-specific validation
        if target_phase == TDDPhase.GREEN:
            if not self._validate_red_phase_completion():
                raise TDDTransitionError("Red phase requirements not met for Green transition")

        elif target_phase == TDDPhase.REFACTOR:
            if not self._validate_green_phase_completion():
                raise TDDTransitionError("Green phase requirements not met for Refactor transition")

        elif target_phase == TDDPhase.COMPLETE:
            if not self._validate_refactor_phase_completion():
                raise TDDTransitionError("Refactor phase requirements not met for Complete transition")

        previous_phase = self.tdd_phase_enum
        self.tdd_phase_enum = target_phase

        # Update timestamps & durations
        now = datetime.now(timezone.utc)
        if target_phase == TDDPhase.GREEN:
            # If entering GREEN from RED
            if self.red_phase_started_at and not self.red_phase_duration:
                self.red_phase_duration = int((now - self.red_phase_started_at).total_seconds() / 60)
            self.green_phase_started_at = now

        elif target_phase == TDDPhase.REFACTOR:
            if self.green_phase_started_at and not self.green_phase_duration:
                self.green_phase_duration = int((now - self.green_phase_started_at).total_seconds() / 60)
            self.refactor_phase_started_at = now

        elif target_phase == TDDPhase.COMPLETE:
            if self.refactor_phase_started_at and not self.refactor_phase_duration:
                self.refactor_phase_duration = int((now - self.refactor_phase_started_at).total_seconds() / 60)
            self.cycle_completed_at = now
            if self.red_phase_started_at:
                self.total_cycle_duration = int((now - self.red_phase_started_at).total_seconds() / 60)

        logger.info(f"TDD phase transition: {previous_phase} -> {target_phase.value}")
        return True

    def start_red_phase(self, test_requirements: List[str], criteria: List[str]) -> bool:
        """Start Red phase with requirements."""
        if self.tdd_phase_enum and self.tdd_phase_enum != TDDPhase.RED:
            return False
        # store Python lists directly in JSON columns
        self.test_requirements = list(test_requirements)
        self.acceptance_criteria = list(criteria)
        self.red_phase_started_at = datetime.now(timezone.utc)
        self.red_phase_complete = False
        return True

    def complete_red_phase(self) -> bool:
        """Complete Red phase with validation and move to GREEN."""
        if not self._validate_red_phase_completion():
            return False
        self.red_phase_complete = True
        return self.transition_tdd_phase(TDDPhase.GREEN)

    def complete_green_phase(self) -> bool:
        """Complete Green phase with validation and move to REFACTOR."""
        if not self._validate_green_phase_completion():
            return False
        self.green_phase_complete = True
        return self.transition_tdd_phase(TDDPhase.REFACTOR)

    def complete_refactor_phase(self, improvements: List[str]) -> bool:
        """Complete Refactor phase with validation and move to COMPLETE."""
        if not self._validate_refactor_phase_completion():
            return False
        # Persist improvements alongside acceptance criteria (append)
        current_criteria: List[str] = list(self.acceptance_criteria or [])
        current_criteria.extend(improvements)
        self.acceptance_criteria = current_criteria

        self.refactor_phase_complete = True
        return self.transition_tdd_phase(TDDPhase.COMPLETE)

    # ---- Validations ---------------------------------------------------------

    def _validate_red_phase_completion(self) -> bool:
        """Validate Red phase completion requirements."""
        return bool(
            self.test_requirements
            and self.acceptance_criteria
            and self.test_failing_count > 0  # must have failing tests
        )

    def _validate_green_phase_completion(self) -> bool:
        """Validate Green phase completion requirements."""
        return bool(
            self.test_passing_count > 0
            and self.test_failing_count == 0  # all tests must pass
        )

    def _validate_refactor_phase_completion(self) -> bool:
        """Validate Refactor phase completion requirements."""
        coverage_ok = (self.test_coverage_percentage or 0.0) >= 80.0
        return bool(
            self.test_passing_count > 0
            and self.test_failing_count == 0
            and coverage_ok
        )

    # ---- Metrics -------------------------------------------------------------

    def calculate_tdd_effectiveness(self) -> Dict[str, float]:
        """Calculate TDD cycle effectiveness metrics."""
        if not self.total_cycle_duration or self.total_cycle_duration <= 0:
            return {"effectiveness": 0.0}

        # Phase distribution (percentages)
        red_pct = (self.red_phase_duration or 0) / self.total_cycle_duration * 100
        green_pct = (self.green_phase_duration or 0) / self.total_cycle_duration * 100
        refactor_pct = (self.refactor_phase_duration or 0) / self.total_cycle_duration * 100

        ideal = {"red": 30.0, "green": 50.0, "refactor": 20.0}
        actual = {"red": red_pct, "green": green_pct, "refactor": refactor_pct}

        # Balance score: smaller deviation from ideal → higher score
        balance_score = 100.0 - sum(abs(ideal[k] - actual[k]) for k in ideal) / 3.0

        # Test quality score
        coverage_score = float(self.test_coverage_percentage or 0.0)
        test_ratio_score = (self.test_passing_count / max(self.test_total_count, 1)) * 100.0
        test_quality = (coverage_score + test_ratio_score) / 2.0

        # Overall effectiveness (weighted)
        effectiveness = (balance_score * 0.4) + (test_quality * 0.6)

        return {
            "effectiveness": effectiveness,
            "balance_score": balance_score,
            "test_quality": test_quality,
            "phase_distribution": actual,
            "duration_minutes": float(self.total_cycle_duration),
        }


# =============================================================================
# TDAH Optimization Mixin
# =============================================================================

class TDAHOptimizationMixin:
    """
    Mixin providing TDAH optimization functionality.

    Features:
    - Cognitive complexity assessment
    - Energy level matching and optimization
    - Focus time estimation and tracking
    - Interruption handling and recovery
    - Task breakdown recommendations
    """

    # Cognitive Load Assessment
    cognitive_complexity: Mapped[int] = mapped_column(Integer, default=1)  # 1-10 scale
    estimated_complexity: Mapped[Optional[int]] = mapped_column(Integer)
    actual_complexity: Mapped[Optional[int]] = mapped_column(Integer)

    # Focus and Energy Management
    estimated_focus_time: Mapped[Optional[int]] = mapped_column(Integer)  # minutes
    actual_focus_time: Mapped[Optional[int]] = mapped_column(Integer)
    optimal_energy_level: Mapped[int] = mapped_column(Integer, default=TDAHEnergyLevel.MODERATE.value)

    # Interruption Tracking
    interruption_count: Mapped[int] = mapped_column(Integer, default=0)
    interruption_recovery_time: Mapped[int] = mapped_column(Integer, default=0)  # minutes
    interruption_tolerance: Mapped[str] = mapped_column(String(20), default="medium")  # low/medium/high

    # TDAH-Specific Flags
    requires_hyperfocus: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_multitasking: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_external_structure: Mapped[bool] = mapped_column(Boolean, default=False)
    benefits_from_gamification: Mapped[bool] = mapped_column(Boolean, default=True)

    # Session Context
    focus_sessions_used: Mapped[int] = mapped_column(Integer, default=0)
    successful_sessions: Mapped[int] = mapped_column(Integer, default=0)
    average_session_rating: Mapped[Optional[float]] = mapped_column(Float)

    # Motivation and Feedback (JSON)
    dopamine_triggers: Mapped[Optional[List[str]]] = mapped_column(JSON)   # array
    motivation_factors: Mapped[Optional[List[str]]] = mapped_column(JSON)  # array
    feedback_preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # object

    @hybrid_property
    def cognitive_complexity_enum(self) -> CognitiveComplexity:
        """Get cognitive complexity as enum."""
        try:
            return CognitiveComplexity(self.cognitive_complexity)
        except Exception:
            return CognitiveComplexity.MODERATE

    @cognitive_complexity_enum.setter
    def cognitive_complexity_enum(self, complexity: CognitiveComplexity) -> None:
        """Set cognitive complexity from enum."""
        self.cognitive_complexity = complexity.value

    @hybrid_property
    def optimal_energy_enum(self) -> TDAHEnergyLevel:
        """Get optimal energy level as enum."""
        try:
            return TDAHEnergyLevel(self.optimal_energy_level)
        except Exception:
            return TDAHEnergyLevel.MODERATE

    @optimal_energy_enum.setter
    def optimal_energy_enum(self, energy: TDAHEnergyLevel) -> None:
        """Set optimal energy level from enum."""
        self.optimal_energy_level = energy.value

    # ---- Scoring & Estimates -------------------------------------------------

    def calculate_tdah_suitability(self, user_energy: TDAHEnergyLevel) -> float:
        """
        Calculate task suitability for current user energy level.
        Returns score from 0.0 (unsuitable) to 1.0 (perfect match).
        """
        energy_diff = abs(user_energy.value - self.optimal_energy_level)
        # Perfect match gets 1.0, each level difference reduces by 0.15
        suitability = max(0.0, 1.0 - (energy_diff * 0.15))

        # Adjust for complexity
        if self.cognitive_complexity > 7 and user_energy.value < 4:
            suitability *= 0.5  # High complexity needs high energy

        # Adjust for interruption tolerance
        if self.interruption_tolerance == "low" and user_energy.value < 3:
            suitability *= 0.7  # Low interruption tolerance needs focus

        return float(max(0.0, min(1.0, suitability)))

    def estimate_session_duration(self, user_energy: TDAHEnergyLevel) -> int:
        """
        Estimate optimal session duration based on complexity and user energy.
        Returns duration in minutes (5..90).
        """
        base_duration_map = {
            1: 10,  # VERY_LOW
            2: 15,  # LOW
            3: 25,  # MODERATE
            4: 35,  # HIGH
            5: 45,  # VERY_HIGH
        }
        base_duration = base_duration_map.get(user_energy.value, 25)

        complexity_multiplier_map = {
            1: 0.5,   # TRIVIAL
            2: 0.7,   # SIMPLE
            3: 1.0,   # EASY
            4: 1.2,   # MODERATE
            5: 1.5,   # COMPLEX
            6: 1.8,   # HARD
            7: 2.0,   # VERY_HARD
            8: 2.5,   # EXPERT
            9: 3.0,   # OVERWHELMING
            10: 3.5,  # EXTREME
        }
        complexity_multiplier = complexity_multiplier_map.get(self.cognitive_complexity, 1.0)
        duration = int(base_duration * complexity_multiplier)
        return int(min(max(duration, 5), 90))

    def get_tdah_recommendations(self) -> List[str]:
        """Get TDAH-specific recommendations for this task."""
        recommendations: List[str] = []

        # Complexity-based recommendations
        if self.cognitive_complexity >= 8:
            recommendations.append("🧠 Alta complexidade — quebre em subtarefas menores")

        if self.cognitive_complexity <= 2:
            recommendations.append("⚡ Tarefa simples — excelente para períodos de baixa energia")

        # Interruption-based recommendations
        if self.interruption_count > 3:
            recommendations.append("🔄 Múltiplas interrupções — ative o modo foco")

        if self.interruption_tolerance == "low":
            recommendations.append("📱 Minimize distrações — silencie notificações")

        # Energy-based recommendations
        if self.optimal_energy_level >= 4:
            recommendations.append("☀️ Requer alta energia — agende nos seus horários de pico")

        # Focus time recommendations
        if (self.estimated_focus_time or 0) > 60:
            recommendations.append("⏰ Tarefa longa — planeje várias sessões com pausas")

        # Hyperfocus recommendations
        if self.requires_hyperfocus:
            recommendations.append("🎯 Requer foco profundo — bloqueie distrações")
            recommendations.append("⏰ Use um timer para evitar burnout de hyperfocus")

        # Success pattern recommendations
        success_rate = (
            self.successful_sessions / max(self.focus_sessions_used, 1)
            if self.focus_sessions_used > 0 else 0.0
        )
        if success_rate < 0.5:
            recommendations.append("📊 Ajuste duração da sessão ou complexidade")

        return recommendations

    def record_session_outcome(self, duration: int, success: bool, rating: int) -> None:
        """Record the outcome of a focus session."""
        self.focus_sessions_used += 1
        self.actual_focus_time = (self.actual_focus_time or 0) + max(0, int(duration))

        if success:
            self.successful_sessions += 1

        # Update average rating (incremental mean)
        if self.average_session_rating is None:
            self.average_session_rating = float(rating)
        else:
            total_sessions = self.focus_sessions_used
            total_rating = self.average_session_rating * (total_sessions - 1) + float(rating)
            self.average_session_rating = total_rating / total_sessions

    def add_interruption(self, interruption_type: str, recovery_minutes: int) -> None:
        """Record an interruption and recovery time."""
        self.interruption_count += 1
        self.interruption_recovery_time += max(0, int(recovery_minutes))
        logger.info(f"Interruption recorded: {interruption_type}, recovery: {recovery_minutes} min")


# =============================================================================
# Audit Trail Mixin
# =============================================================================

class AuditMixin:
    """
    Mixin providing comprehensive audit trail functionality.

    Features:
    - Automatic timestamp management (UTC)
    - User tracking for all operations
    - Soft delete support
    - Simple versioning via monotonically increasing integer
    """

    # Timestamp Management (UTC, timezone-aware)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # User Tracking
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer)
    deleted_by: Mapped[Optional[int]] = mapped_column(Integer)

    # Version Control
    version: Mapped[int] = mapped_column(Integer, default=1)

    @hybrid_property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None

    @hybrid_property
    def age_minutes(self) -> int:
        """Get age in minutes since creation."""
        if self.created_at:
            return int((datetime.now(timezone.utc) - self.created_at).total_seconds() / 60)
        return 0

    def soft_delete(self, user_id: Optional[int] = None) -> None:
        """Perform soft delete."""
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = user_id

    def restore(self) -> None:
        """Restore soft-deleted record."""
        self.deleted_at = None
        self.deleted_by = None

    def touch(self, user_id: Optional[int] = None) -> None:
        """Update timestamp without changing content."""
        self.updated_at = datetime.now(timezone.utc)
        self.updated_by = user_id
        self.version += 1


# =============================================================================
# JSON Field Mixin
# =============================================================================

class JSONFieldMixin:
    """
    Mixin providing JSON field serialization/deserialization utilities.

    Works seamlessly whether your ORM column is declared as JSON or as Text/String
    storing a serialized JSON string. The helpers auto-detect and do the right thing.
    """

    # ---- Internal helpers ----------------------------------------------------

    def _deserialize_if_string(self, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (TypeError, ValueError, json.JSONDecodeError):
                # Not a JSON string; return original
                return value
        return value

    def _should_store_as_string(self, field_name: str) -> bool:
        """
        Best-effort check: if current value is a string OR the attribute has never
        been set, we can't reliably introspect column type from here. We choose:
        - If value is str → keep as str (compat)
        - Else → prefer Python types and let SQLAlchemy JSON handle serialization
        """
        try:
            current = getattr(self, field_name)
            return isinstance(current, str)
        except Exception:
            return False

    # ---- Public API ----------------------------------------------------------

    def set_json_field(self, field_name: str, value: Any) -> bool:
        """
        Set a JSON-capable field with proper serialization.
        If the underlying column is JSON, store Python objects directly.
        If it's Text/String, store a compact JSON string.
        """
        try:
            if not hasattr(self, field_name):
                return False
            if self._should_store_as_string(field_name):
                setattr(self, field_name, json.dumps(value, default=str, ensure_ascii=False))
            else:
                setattr(self, field_name, value)
            return True
        except (TypeError, ValueError) as e:
            logger.error(f"JSON serialization failed for '{field_name}': {e}")
            return False

    def get_json_field(self, field_name: str, default: Any = None) -> Any:
        """
        Get a JSON-capable field with proper deserialization.
        Returns Python objects for JSON columns or parsed strings; otherwise default.
        """
        try:
            if not hasattr(self, field_name):
                return default
            raw = getattr(self, field_name)
            if raw is None:
                return default
            return self._deserialize_if_string(raw)
        except Exception as e:
            logger.error(f"JSON deserialization failed for '{field_name}': {e}")
            return default

    def append_to_json_array(self, field_name: str, item: Any) -> bool:
        """Append item to JSON array field (creates array if missing)."""
        arr = self.get_json_field(field_name, [])
        if not isinstance(arr, list):
            arr = []
        arr.append(item)
        return self.set_json_field(field_name, arr)

    def update_json_object(self, field_name: str, updates: Dict[str, Any]) -> bool:
        """Update JSON object field with new keys/values (creates object if missing)."""
        obj = self.get_json_field(field_name, {})
        if not isinstance(obj, dict):
            obj = {}
        obj.update(updates)
        return self.set_json_field(field_name, obj)


# =============================================================================
# Event Listeners for Automatic Processing
# =============================================================================

def setup_mixin_event_listeners() -> None:
    """Set up SQLAlchemy event listeners for mixin functionality."""
    # Automatic audit field updates
    @event.listens_for(AuditMixin, "before_update", propagate=True)
    def _update_audit_fields(mapper, connection, target: AuditMixin):
        target.updated_at = datetime.now(timezone.utc)
        try:
            target.version = int(target.version) + 1
        except Exception:
            target.version = 1

    # TDD workflow validation (hook for models whose Base implements validate_tdd_workflow)
    @event.listens_for(TDDWorkflowMixin, "before_update", propagate=True)
    def _validate_tdd_workflow(mapper, connection, target):
        if hasattr(target, "validate_tdd_workflow"):
            if not target.validate_tdd_workflow():  # type: ignore[attr-defined]
                raise ValueError("TDD workflow validation failed")

    # TDAH complexity validation (clamp to 1..10 on insert/update)
    @event.listens_for(TDAHOptimizationMixin, "before_insert", propagate=True)
    @event.listens_for(TDAHOptimizationMixin, "before_update", propagate=True)
    def _validate_tdah_complexity(mapper, connection, target: TDAHOptimizationMixin):
        try:
            cc = int(target.cognitive_complexity)
        except Exception:
            cc = 1
        target.cognitive_complexity = max(1, min(10, cc))


# Initialize event listeners eagerly (safe to call multiple times)
setup_mixin_event_listeners()
