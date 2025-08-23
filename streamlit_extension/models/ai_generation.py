#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 MODELS - AI Generation & Change Log ORM Models

AI-generated content tracking and comprehensive audit trail system with
performance metrics, quality assessment, and learning integration.

Maps to ai_generations and change_log tables from migration
009_sprint_system_and_advanced_features.sql

Usage:
    from streamlit_extension.models.ai_generation import (
        AiGenerationORM, ChangeLogORM, GenerationType
    )

    # Track AI generation
    ai_gen = AiGenerationORM(
        generation_type=GenerationType.CODE_GENERATION.value,
        context_type="task",
        context_id=1,
        ai_model="claude-3",
        user_prompt="Generate OAuth 2.0 authentication function",
        ai_response="def authenticate_user(token): ...",
        user_id=user_id
    )

    # Log system change
    change = ChangeLogORM(
        change_type="update",
        entity_type="task",
        entity_id=1,
        field_name="status",
        old_value="in_progress",
        new_value="completed",
        user_id=user_id
    )

Features:
- Complete AI generation lifecycle tracking
- Cost and performance monitoring
- Quality assessment and user feedback
- Comprehensive audit trail with rollback capability
- Compliance and security tracking
- Business impact assessment
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    DECIMAL,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship  # noqa: F401 (kept for future relations)

from .base import Base
from .mixins import AuditMixin, JSONFieldMixin


# =========================
# Enums
# =========================

class GenerationType(Enum):
    """AI generation types."""
    CODE_GENERATION = "code_generation"
    TASK_CREATION = "task_creation"
    PLANNING_ASSISTANCE = "planning_assistance"
    ESTIMATION = "estimation"
    REVIEW = "review"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REFACTORING = "refactoring"


class ContextType(Enum):
    """Context types for AI generations."""
    TASK = "task"
    EPIC = "epic"
    USER_STORY = "user_story"
    SPRINT = "sprint"
    PROJECT = "project"
    GENERAL = "general"


class ReviewStatus(Enum):
    """AI generation review status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_MODIFICATION = "needs_modification"


class ContentType(Enum):
    """Generated content types."""
    TEXT = "text"
    CODE = "code"
    JSON = "json"
    MARKDOWN = "markdown"
    SQL = "sql"
    YAML = "yaml"


class ChangeType(Enum):
    """System change types."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    STATUS_CHANGE = "status_change"
    ASSIGNMENT_CHANGE = "assignment_change"
    BULK_UPDATE = "bulk_update"


class EntityType(Enum):
    """Entity types for change tracking."""
    TASK = "task"
    EPIC = "epic"
    USER_STORY = "user_story"
    SPRINT = "sprint"
    PROJECT = "project"
    USER = "user"
    MILESTONE = "milestone"
    DEPENDENCY = "dependency"


# =========================
# Dataclasses (DTOs)
# =========================

@dataclass
class GenerationMetrics:
    """AI generation performance metrics."""
    input_tokens: int
    output_tokens: int
    processing_time_ms: int
    generation_cost: Decimal
    quality_score: float
    user_satisfaction: float


@dataclass
class ChangeContext:
    """Change context information."""
    change_reason: str
    business_impact: str
    affected_systems: List[str]
    rollback_complexity: str


# =========================
# ORM: AiGenerationORM
# =========================

class AiGenerationORM(Base, AuditMixin, JSONFieldMixin):
    """
    AI Generation ORM model for tracking AI-generated content.

    Maps to ai_generations table with 30+ fields supporting comprehensive
    AI interaction tracking, performance monitoring, and quality assessment.
    """
    __tablename__ = "ai_generations"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Generation Context
    generation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    context_type: Mapped[Optional[str]] = mapped_column(String(50))
    context_id: Mapped[Optional[int]] = mapped_column(Integer)

    # AI Model Information
    ai_model: Mapped[Optional[str]] = mapped_column(String(100))
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    provider: Mapped[Optional[str]] = mapped_column(String(50))

    # Generation Request
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)
    input_context: Mapped[Optional[str]] = mapped_column(JSON)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))

    # Generation Response
    ai_response: Mapped[str] = mapped_column(Text, nullable=False)
    generation_metadata: Mapped[Optional[str]] = mapped_column(JSON)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))

    # Content Analysis
    content_type: Mapped[Optional[str]] = mapped_column(String(50))
    content_language: Mapped[Optional[str]] = mapped_column(String(20))
    content_quality_score: Mapped[Optional[int]] = mapped_column(Integer)  # 1-10

    # Usage and Feedback
    used_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    user_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 stars
    user_feedback: Mapped[Optional[str]] = mapped_column(Text)
    modifications_made: Mapped[Optional[str]] = mapped_column(Text)

    # Generation Statistics
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    generation_cost: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))

    # Quality Assurance
    reviewed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    review_status: Mapped[Optional[str]] = mapped_column(String(50))
    review_notes: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Integration
    applied_to_system: Mapped[bool] = mapped_column(Boolean, default=False)
    integration_results: Mapped[Optional[str]] = mapped_column(JSON)
    rollback_data: Mapped[Optional[str]] = mapped_column(JSON)

    # Learning and Improvement
    feedback_loop_data: Mapped[Optional[str]] = mapped_column(JSON)
    success_metrics: Mapped[Optional[str]] = mapped_column(JSON)
    improvement_suggestions: Mapped[Optional[str]] = mapped_column(Text)

    # Enhanced Audit
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships (kept commented for future activation)
    # user = relationship("UserORM", foreign_keys=[user_id])
    # reviewer = relationship("UserORM", foreign_keys=[reviewed_by])

    # -------------------------
    # Repr
    # -------------------------
    def __repr__(self) -> str:
        return (
            f"<AiGenerationORM(id={self.id}, type='{self.generation_type}', "
            f"model='{self.ai_model}', user_id={self.user_id})>"
        )

    # -------------------------
    # Enum helpers
    # -------------------------
    @property
    def generation_type_enum(self) -> GenerationType:
        try:
            return GenerationType(self.generation_type)
        except ValueError:
            return GenerationType.CODE_GENERATION

    @property
    def context_type_enum(self) -> Optional[ContextType]:
        if not self.context_type:
            return None
        try:
            return ContextType(self.context_type)
        except ValueError:
            return None

    @property
    def review_status_enum(self) -> Optional[ReviewStatus]:
        if not self.review_status:
            return None
        try:
            return ReviewStatus(self.review_status)
        except ValueError:
            return None

    @property
    def content_type_enum(self) -> Optional[ContentType]:
        if not self.content_type:
            return None
        try:
            return ContentType(self.content_type)
        except ValueError:
            return None

    # -------------------------
    # Derived properties
    # -------------------------
    @property
    def is_expired(self) -> bool:
        return bool(self.expires_at and datetime.now() > self.expires_at)

    @property
    def is_reviewed(self) -> bool:
        return self.review_status is not None

    @property
    def total_tokens(self) -> int:
        return (self.input_tokens or 0) + (self.output_tokens or 0)

    @property
    def cost_per_token(self) -> Decimal:
        if not self.generation_cost or self.total_tokens == 0:
            return Decimal("0.000000")
        return self.generation_cost / Decimal(str(self.total_tokens))

    # -------------------------
    # Generation Management
    # -------------------------
    def mark_used_by_user(self, modifications: str = "") -> None:
        self.used_by_user = True
        if modifications:
            self.modifications_made = modifications

    def add_user_feedback(self, rating: int, feedback: str = "") -> None:
        """Clamp rating to 1..5 and set feedback."""
        if rating is not None:
            self.user_rating = max(1, min(5, int(rating)))
        if feedback:
            self.user_feedback = feedback

    def mark_applied_to_system(
        self,
        integration_results: Dict[str, Any],
        rollback_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.applied_to_system = True
        self.integration_results = self.serialize_json(integration_results)
        if rollback_data:
            self.rollback_data = self.serialize_json(rollback_data)

    def review_generation(self, reviewed_by: int, status: ReviewStatus, notes: str = "") -> None:
        self.reviewed_by = reviewed_by
        self.review_status = status.value
        self.review_notes = notes
        self.reviewed_at = datetime.now()

    # -------------------------
    # Content Analysis
    # -------------------------
    def analyze_content(self) -> Dict[str, Any]:
        """Analyze generated content characteristics."""
        content = self.ai_response or ""

        word_count = len(content.split())
        line_count = content.count("\n") + 1 if content else 0
        char_count = len(content)

        # Detect content type if not set
        if not self.content_type:
            self.content_type = self._detect_content_type(content).value

        # Language detection (simplified/heuristic)
        if not self.content_language:
            self.content_language = self._detect_language(content)

        return {
            "metrics": {
                "word_count": word_count,
                "line_count": line_count,
                "character_count": char_count,
            },
            "content_type": self.content_type,
            "language": self.content_language,
            "complexity_score": self._calculate_complexity_score(content),
        }

    def _detect_content_type(self, content: str) -> ContentType:
        content_lower = content.lower().strip()
        if content_lower.startswith(("def ", "class ", "import ", "from ")):
            return ContentType.CODE
        if content_lower.startswith(("select ", "insert ", "update ", "delete ")):
            return ContentType.SQL
        if content.startswith(("# ", "## ", "### ")):
            return ContentType.MARKDOWN
        if content.startswith(("{", "[")):
            try:
                import json  # safe usage
                json.loads(content)
                return ContentType.JSON
            except Exception:
                pass
        return ContentType.TEXT

    def _detect_language(self, content: str) -> str:
        cl = content.lower()
        if "def " in cl and "import " in cl:
            return "python"
        if "function " in cl or "=> {" in cl:
            return "javascript"
        if "select " in cl or "insert " in cl or "update " in cl or "delete " in cl:
            return "sql"
        if "# " in content or "## " in content:
            return "markdown"
        return "text"

    def _calculate_complexity_score(self, content: str) -> int:
        """Rough complexity score (1-10) based on length and structures."""
        score = 1
        lines = content.splitlines()
        if len(lines) > 10:
            score += 1
        if len(lines) > 50:
            score += 1

        nesting_indicators = ["{", "}", "[", "]", "if ", "for ", "while ", "try:"]
        nesting_count = sum(content.count(ind) for ind in nesting_indicators)
        score += min(nesting_count // 10, 3)

        technical_terms = ["class", "function", "async", "await", "exception", "algorithm"]
        tech_count = sum(1 for term in technical_terms if term in content.lower())
        score += min(tech_count, 3)

        return min(score, 10)

    # -------------------------
    # Performance Metrics
    # -------------------------
    def calculate_generation_metrics(self) -> GenerationMetrics:
        return GenerationMetrics(
            input_tokens=self.input_tokens or 0,
            output_tokens=self.output_tokens or 0,
            processing_time_ms=self.processing_time_ms or 0,
            generation_cost=self.generation_cost or Decimal("0.000000"),
            quality_score=float(self.content_quality_score or 0),
            user_satisfaction=float(self.user_rating or 0) * 20.0,  # 1-5 → 0-100
        )

    def get_cost_efficiency(self) -> Dict[str, float]:
        metrics = self.calculate_generation_metrics()

        if float(metrics.generation_cost or 0) == 0.0:
            return {"cost_per_token": 0.0, "cost_per_word": 0.0, "efficiency_score": 100.0}

        word_count = len((self.ai_response or "").split())
        cost = float(metrics.generation_cost)
        cost_per_word = cost / max(word_count, 1)
        cost_per_token = cost / max(self.total_tokens, 1)

        efficiency_score = 0.0
        if self.user_rating and cost > 0:
            # simplistic: higher rating / lower cost ⇒ higher efficiency
            efficiency_score = min((float(self.user_rating) * 20.0) / (cost * 1000.0), 100.0)

        return {
            "cost_per_token": float(cost_per_token),
            "cost_per_word": float(cost_per_word),
            "efficiency_score": float(efficiency_score),
        }

    # -------------------------
    # Learning & Improvement
    # -------------------------
    def get_feedback_loop_data(self) -> Dict[str, Any]:
        return self.deserialize_json(self.feedback_loop_data) if self.feedback_loop_data else {}

    def add_feedback_loop_data(self, data: Dict[str, Any]) -> None:
        current = self.get_feedback_loop_data()
        current.update(data or {})
        self.feedback_loop_data = self.serialize_json(current)

    def generate_improvement_suggestions(self) -> List[str]:
        suggestions: List[str] = []
        if self.user_rating and self.user_rating < 3:
            suggestions.append("Consider providing more specific prompts for better results.")
        if self.processing_time_ms and self.processing_time_ms > 30_000:
            suggestions.append("Long processing time — consider breaking into smaller requests.")
        if not self.used_by_user:
            suggestions.append("Generation was not used — review prompt relevance and accuracy.")
        if self.user_feedback and "incomplete" in (self.user_feedback or "").lower():
            suggestions.append("Provide more complete context in prompts.")
        return suggestions

    # -------------------------
    # Reporting
    # -------------------------
    def get_generation_summary(self) -> Dict[str, Any]:
        metrics = self.calculate_generation_metrics()
        cost_efficiency = self.get_cost_efficiency()
        response_text = self.ai_response or ""

        return {
            "basic_info": {
                "id": self.id,
                "generation_type": self.generation_type,
                "context_type": self.context_type,
                "context_id": self.context_id,
                "ai_model": self.ai_model,
                "provider": self.provider,
            },
            "content": {
                "content_type": self.content_type,
                "content_language": self.content_language,
                "quality_score": self.content_quality_score,
                "word_count": len(response_text.split()),
                "character_count": len(response_text),
            },
            "performance": {
                "input_tokens": metrics.input_tokens,
                "output_tokens": metrics.output_tokens,
                "total_tokens": self.total_tokens,
                "processing_time_ms": metrics.processing_time_ms,
                "generation_cost": float(metrics.generation_cost),
            },
            "usage": {
                "used_by_user": self.used_by_user,
                "user_rating": self.user_rating,
                "has_modifications": bool(self.modifications_made),
                "applied_to_system": self.applied_to_system,
            },
            "review": {
                "is_reviewed": self.is_reviewed,
                "review_status": self.review_status,
                "reviewed_by": self.reviewed_by,
                "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            },
            "efficiency": cost_efficiency,
            "lifecycle": {
                "generated_at": self.generated_at.isoformat(),
                "expires_at": self.expires_at.isoformat() if self.expires_at else None,
                "is_expired": self.is_expired,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            },
        }


# =========================
# ORM: ChangeLogORM
# =========================

class ChangeLogORM(Base, AuditMixin, JSONFieldMixin):
    """
    Change Log ORM model for comprehensive audit trail.

    Maps to change_log table with 40+ fields supporting detailed change tracking,
    rollback capability, and compliance monitoring.
    """
    __tablename__ = "change_log"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Change Identification
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Change Details
    field_name: Mapped[Optional[str]] = mapped_column(String(100))
    old_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)
    change_summary: Mapped[Optional[str]] = mapped_column(Text)

    # Change Context
    change_reason: Mapped[Optional[str]] = mapped_column(String(100))
    change_context: Mapped[Optional[str]] = mapped_column(JSON)
    business_impact: Mapped[Optional[str]] = mapped_column(Text)

    # User and Session
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    session_id: Mapped[Optional[str]] = mapped_column(String(100))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))

    # System Context
    system_version: Mapped[Optional[str]] = mapped_column(String(50))
    component: Mapped[Optional[str]] = mapped_column(String(50))
    api_endpoint: Mapped[Optional[str]] = mapped_column(String(255))
    request_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Change Metadata
    change_batch_id: Mapped[Optional[str]] = mapped_column(String(100))
    is_automated: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_level: Mapped[Optional[int]] = mapped_column(Integer)  # 1-10
    validation_status: Mapped[Optional[str]] = mapped_column(String(50))

    # Reversal and Rollback
    is_reversible: Mapped[bool] = mapped_column(Boolean, default=True)
    reversal_data: Mapped[Optional[str]] = mapped_column(JSON)
    reversed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reversed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    reversal_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Approval Workflow
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("framework_users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    approval_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Notification and Communication
    notifications_sent: Mapped[Optional[str]] = mapped_column(JSON)
    change_visibility: Mapped[str] = mapped_column(String(50), default="internal")
    announcement_made: Mapped[bool] = mapped_column(Boolean, default=False)

    # Performance Impact
    performance_impact: Mapped[Optional[str]] = mapped_column(String(50))
    resource_usage: Mapped[Optional[str]] = mapped_column(JSON)
    affected_queries: Mapped[Optional[str]] = mapped_column(JSON)

    # Data Quality
    data_validation_passed: Mapped[bool] = mapped_column(Boolean, default=True)
    validation_errors: Mapped[Optional[str]] = mapped_column(JSON)
    data_quality_score: Mapped[Optional[int]] = mapped_column(Integer)  # 1-10

    # Compliance and Security
    compliance_relevant: Mapped[bool] = mapped_column(Boolean, default=False)
    security_classification: Mapped[Optional[str]] = mapped_column(String(50))
    retention_period: Mapped[Optional[int]] = mapped_column(Integer)  # Days

    # Enhanced Audit
    indexed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships (kept commented for future activation)
    # user = relationship("UserORM", foreign_keys=[user_id])
    # reverser = relationship("UserORM", foreign_keys=[reversed_by])
    # approver = relationship("UserORM", foreign_keys=[approved_by])

    # -------------------------
    # Repr
    # -------------------------
    def __repr__(self) -> str:
        return (
            f"<ChangeLogORM(id={self.id}, type='{self.change_type}', "
            f"entity='{self.entity_type}:{self.entity_id}', user_id={self.user_id})>"
        )

    # -------------------------
    # Enum helpers
    # -------------------------
    @property
    def change_type_enum(self) -> ChangeType:
        try:
            return ChangeType(self.change_type)
        except ValueError:
            return ChangeType.UPDATE

    @property
    def entity_type_enum(self) -> EntityType:
        try:
            return EntityType(self.entity_type)
        except ValueError:
            return EntityType.TASK

    # -------------------------
    # Derived properties
    # -------------------------
    @property
    def is_reversed(self) -> bool:
        return self.reversed_at is not None

    @property
    def is_approved(self) -> bool:
        return self.approved_at is not None

    @property
    def needs_approval(self) -> bool:
        return self.requires_approval and not self.is_approved

    # -------------------------
    # Change Management
    # -------------------------
    def reverse_change(self, reversed_by: int, reason: str = "") -> bool:
        if not self.is_reversible or self.is_reversed:
            return False
        self.reversed_at = datetime.now()
        self.reversed_by = reversed_by
        self.reversal_reason = reason
        return True

    def approve_change(self, approved_by: int, notes: str = "") -> bool:
        if self.is_approved:
            return False
        self.approved_by = approved_by
        self.approved_at = datetime.now()
        if notes:
            self.approval_notes = notes
        return True

    # -------------------------
    # Context Management
    # -------------------------
    def get_change_context(self) -> Dict[str, Any]:
        return self.deserialize_json(self.change_context) if self.change_context else {}

    def set_change_context(self, context_data: Dict[str, Any]) -> None:
        self.change_context = self.serialize_json(context_data or {})

    def get_reversal_data(self) -> Dict[str, Any]:
        return self.deserialize_json(self.reversal_data) if self.reversal_data else {}

    def set_reversal_data(self, reversal_data: Dict[str, Any]) -> None:
        self.reversal_data = self.serialize_json(reversal_data or {})

    # -------------------------
    # Notification Management
    # -------------------------
    def get_notifications_sent(self) -> List[Dict[str, Any]]:
        data = self.deserialize_json(self.notifications_sent) if self.notifications_sent else []
        return data if isinstance(data, list) else []

    def add_notification_sent(self, recipient: str, method: str, timestamp: Optional[datetime] = None) -> None:
        current = self.get_notifications_sent()
        current.append(
            {
                "recipient": recipient,
                "method": method,
                "sent_at": (timestamp or datetime.now()).isoformat(),
                "status": "sent",
            }
        )
        self.notifications_sent = self.serialize_json(current)

    # -------------------------
    # Performance Tracking
    # -------------------------
    def get_resource_usage(self) -> Dict[str, Any]:
        return self.deserialize_json(self.resource_usage) if self.resource_usage else {}

    def set_resource_usage(self, cpu_usage: float, memory_usage: float, io_operations: int = 0) -> None:
        usage = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "io_operations": io_operations,
            "timestamp": datetime.now().isoformat(),
        }
        self.resource_usage = self.serialize_json(usage)

    # -------------------------
    # Business Logic
    # -------------------------
    def calculate_impact_score(self) -> float:
        score = 0.0

        entity_impacts = {
            EntityType.PROJECT: 5.0,
            EntityType.SPRINT: 4.0,
            EntityType.EPIC: 3.0,
            EntityType.TASK: 2.0,
            EntityType.USER: 3.5,
            EntityType.MILESTONE: 4.5,
        }
        score += entity_impacts.get(self.entity_type_enum, 2.0)

        change_impacts = {
            ChangeType.DELETE: 3.0,
            ChangeType.CREATE: 1.0,
            ChangeType.UPDATE: 2.0,
            ChangeType.STATUS_CHANGE: 2.5,
            ChangeType.BULK_UPDATE: 4.0,
        }
        score += change_impacts.get(self.change_type_enum, 2.0)

        if self.performance_impact == "high":
            score += 2.0
        elif self.performance_impact == "medium":
            score += 1.0

        if self.compliance_relevant:
            score += 1.5

        return min(score, 10.0)

    # -------------------------
    # Reporting
    # -------------------------
    def get_change_summary(self) -> Dict[str, Any]:
        impact_score = self.calculate_impact_score()

        return {
            "basic_info": {
                "id": self.id,
                "change_type": self.change_type,
                "entity_type": self.entity_type,
                "entity_id": self.entity_id,
                "field_name": self.field_name,
            },
            "change_details": {
                "old_value": self.old_value,
                "new_value": self.new_value,
                "change_summary": self.change_summary,
                "change_reason": self.change_reason,
                "business_impact": self.business_impact,
            },
            "context": {
                "user_id": self.user_id,
                "session_id": self.session_id,
                "ip_address": self.ip_address,
                "system_version": self.system_version,
                "component": self.component,
            },
            "metadata": {
                "is_automated": self.is_automated,
                "confidence_level": self.confidence_level,
                "validation_status": self.validation_status,
                "change_batch_id": self.change_batch_id,
            },
            "reversal": {
                "is_reversible": self.is_reversible,
                "is_reversed": self.is_reversed,
                "reversed_at": self.reversed_at.isoformat() if self.reversed_at else None,
                "reversal_reason": self.reversal_reason,
            },
            "approval": {
                "requires_approval": self.requires_approval,
                "is_approved": self.is_approved,
                "approved_at": self.approved_at.isoformat() if self.approved_at else None,
                "approval_notes": self.approval_notes,
            },
            "quality": {
                "data_validation_passed": self.data_validation_passed,
                "data_quality_score": self.data_quality_score,
                "impact_score": impact_score,
            },
            "compliance": {
                "compliance_relevant": self.compliance_relevant,
                "security_classification": self.security_classification,
                "retention_period": self.retention_period,
            },
            "timeline": {
                "created_at": self.created_at.isoformat() if getattr(self, "created_at", None) else None,
                "indexed_at": self.indexed_at.isoformat(),
                "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            },
        }

    # -------------------------
    # Factories
    # -------------------------
    @classmethod
    def create_entity_change(
        cls,
        change_type: ChangeType,
        entity_type: EntityType,
        entity_id: int,
        user_id: int,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        change_reason: str = "",
    ) -> "ChangeLogORM":
        """Create a standard entity change log entry."""
        return cls(
            change_type=change_type.value,
            entity_type=entity_type.value,
            entity_id=entity_id,
            user_id=user_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            change_reason=change_reason or f"{change_type.value.title()} operation",
            confidence_level=10,  # High confidence for direct user actions
            is_automated=False,
        )
