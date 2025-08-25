#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📋 MODELS - ProductVision ORM Model (Minimalist)

Minimalist ProductVision focused purely on product vision essence.
Post ultra-normalization with framework_projects as comprehensive project hub.

Usage:
    from streamlit_extension.models.product_vision import ProductVisionORM
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
    Index,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .mixins import AuditMixin, JSONFieldMixin

logger = logging.getLogger(__name__)


JsonObj = Dict[str, Any]
JsonArr = List[Dict[str, Any]]
JsonVal = Union[JsonObj, JsonArr, List[Any], Dict[str, Any]]


class ProductVisionORM(Base, AuditMixin, JSONFieldMixin):
    """
    Minimalist product vision model focused on core vision essence:
    - Vision statement, problem definition, target audience, value proposition
    - Constraints and limitations
    - Pure product vision without project management overhead
    """

    __tablename__ = "product_visions"

    # -------------------------------------------------------------------------
    # Primary Key and Relationships
    # -------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("framework_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # -------------------------------------------------------------------------
    # CORE VISION FIELDS (5 fields total)
    # -------------------------------------------------------------------------
    
    # Vision Content - The essence of product vision
    vision_statement: Mapped[str] = mapped_column(Text, nullable=False)
    problem_statement: Mapped[Optional[str]] = mapped_column(Text)
    target_audience: Mapped[Optional[str]] = mapped_column(Text)
    value_proposition: Mapped[Optional[str]] = mapped_column(Text)
    
    # Constraints - New field for limitations and restrictions
    constraints: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # List of constraints

    # -------------------------------------------------------------------------
    # SYSTEM FIELDS (10 fields total)
    # -------------------------------------------------------------------------
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        server_default=text("'active'"),
        nullable=False,
    )  # active, draft, archived
    
    # Version control
    version: Mapped[int] = mapped_column(
        Integer, default=1, server_default=text("1"), nullable=False
    )
    
    # Additional metadata
    notes: Mapped[Optional[str]] = mapped_column(Text)
    metadata: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # Extensibility field

    # AuditMixin provides: created_at, updated_at, created_by, updated_by

    __table_args__ = (
        Index("ix_product_visions_project_status", "project_id", "status"),
    )

    # -------------------------------------------------------------------------
    # Dunder & Representation
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        vid = getattr(self, "id", None)
        vstmt = getattr(self, "vision_statement", "") or ""
        suffix = "..." if len(vstmt) > 30 else ""
        return f"<ProductVision(id={vid}, vision='{vstmt[:30]}{suffix}')>"

    # -------------------------------------------------------------------------
    # Constraints Management
    # -------------------------------------------------------------------------
    def get_constraints(self) -> List[Dict[str, Any]]:
        """Get list of constraints."""
        return self.get_json_field("constraints", [])

    def add_constraint(
        self,
        constraint: str,
        constraint_type: str = "general",
        description: str = "",
        severity: str = "medium",
    ) -> bool:
        """Add a constraint to the vision."""
        constraint_obj: Dict[str, Any] = {
            "constraint": constraint,
            "type": constraint_type,  # technical, business, regulatory, resource
            "description": description,
            "severity": severity,  # low, medium, high, critical
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.append_to_json_array("constraints", constraint_obj)

    def remove_constraint(self, constraint: str) -> bool:
        """Remove a constraint by name."""
        constraints = self.get_constraints()
        updated_constraints = [c for c in constraints if c.get("constraint") != constraint]
        
        if len(updated_constraints) != len(constraints):
            return self.set_json_field("constraints", updated_constraints)
        return False

    def get_critical_constraints(self) -> List[Dict[str, Any]]:
        """Get constraints marked as critical."""
        constraints = self.get_constraints()
        return [c for c in constraints if c.get("severity") == "critical"]

    # -------------------------------------------------------------------------
    # Vision Validation
    # -------------------------------------------------------------------------
    def validate_vision_completeness(self) -> Dict[str, Any]:
        """Validate if vision has all essential components."""
        validation_result = {
            "is_complete": True,
            "missing_components": [],
            "completion_score": 0.0,
            "recommendations": []
        }

        # Check essential fields
        essential_fields = [
            ("vision_statement", "Vision Statement", 0.4),
            ("problem_statement", "Problem Statement", 0.3),
            ("target_audience", "Target Audience", 0.2),
            ("value_proposition", "Value Proposition", 0.1)
        ]

        total_score = 0.0
        for field, name, weight in essential_fields:
            field_value = getattr(self, field, None)
            if field_value and field_value.strip():
                total_score += weight
            else:
                validation_result["missing_components"].append(name)
                validation_result["recommendations"].append(f"Add {name} to complete the vision")

        validation_result["completion_score"] = total_score * 100
        validation_result["is_complete"] = total_score >= 0.8  # 80% threshold

        # Additional recommendations
        if len(self.get_constraints()) == 0:
            validation_result["recommendations"].append("Consider adding constraints to clarify limitations")

        if self.notes is None or len(self.notes.strip()) == 0:
            validation_result["recommendations"].append("Add notes for additional context")

        return validation_result

    def calculate_vision_clarity_score(self) -> float:
        """Calculate how clear and well-defined the vision is."""
        score = 0.0

        # Vision statement quality (0-40 points)
        if self.vision_statement:
            statement_length = len(self.vision_statement.strip())
            if 50 <= statement_length <= 200:  # Optimal length
                score += 40
            elif 20 <= statement_length <= 300:  # Acceptable length
                score += 30
            else:  # Too short or too long
                score += 15

        # Problem statement quality (0-30 points)
        if self.problem_statement:
            if len(self.problem_statement.strip()) >= 30:
                score += 30
            else:
                score += 15

        # Target audience specificity (0-20 points)
        if self.target_audience:
            if len(self.target_audience.strip()) >= 20:
                score += 20
            else:
                score += 10

        # Value proposition clarity (0-10 points)
        if self.value_proposition:
            if len(self.value_proposition.strip()) >= 20:
                score += 10
            else:
                score += 5

        return min(score, 100.0)

    # -------------------------------------------------------------------------
    # Vision Analysis
    # -------------------------------------------------------------------------
    def get_vision_summary(self) -> Dict[str, Any]:
        """Get comprehensive vision summary."""
        validation = self.validate_vision_completeness()
        clarity = self.calculate_vision_clarity_score()

        return {
            "id": self.id,
            "project_id": self.project_id,
            "vision_statement": self.vision_statement,
            "status": self.status,
            "version": self.version,
            "completeness": validation,
            "clarity_score": clarity,
            "constraints_count": len(self.get_constraints()),
            "critical_constraints_count": len(self.get_critical_constraints()),
            "created_at": self.created_at.isoformat() if getattr(self, "created_at", None) else None,
            "updated_at": self.updated_at.isoformat() if getattr(self, "updated_at", None) else None,
        }

    def get_vision_health(self) -> Dict[str, Any]:
        """Get vision health indicators."""
        validation = self.validate_vision_completeness()
        clarity = self.calculate_vision_clarity_score()
        constraints = self.get_constraints()

        # Overall health calculation
        health_score = (
            (validation["completion_score"] * 0.5) +
            (clarity * 0.3) +
            (min(len(constraints) * 10, 20) * 0.2)  # Up to 2 constraints = 20 points
        )

        health_status = "excellent"
        if health_score < 60:
            health_status = "poor"
        elif health_score < 75:
            health_status = "fair"
        elif health_score < 90:
            health_status = "good"

        return {
            "overall_score": health_score,
            "health_status": health_status,
            "completion_score": validation["completion_score"],
            "clarity_score": clarity,
            "constraints_health": len(constraints) > 0,
            "recommendations": validation["recommendations"]
        }

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "vision_statement": self.vision_statement,
            "problem_statement": self.problem_statement,
            "target_audience": self.target_audience,
            "value_proposition": self.value_proposition,
            "constraints_count": len(self.get_constraints()),
            "status": self.status,
            "version": self.version,
            "clarity_score": self.calculate_vision_clarity_score(),
            "created_at": self.created_at.isoformat() if getattr(self, "created_at", None) else None,
            "updated_at": self.updated_at.isoformat() if getattr(self, "updated_at", None) else None,
        }

    def clone(self, new_vision_statement: str, new_project_id: Optional[int] = None) -> "ProductVisionORM":
        """Create a copy of this product vision with new vision statement."""
        return ProductVisionORM(
            project_id=new_project_id or self.project_id,
            vision_statement=new_vision_statement,
            problem_statement=self.problem_statement,
            target_audience=self.target_audience,
            value_proposition=self.value_proposition,
            constraints=self.constraints,
            # Reset system fields for new instance
            status="draft",
            version=1,
            notes=self.notes,
        )

    def archive(self) -> bool:
        """Archive this vision."""
        if self.status == "archived":
            return False
        
        old_status = self.status
        self.status = "archived"
        self.updated_at = datetime.now(timezone.utc)
        
        logger.info(
            "ProductVision %s archived: %s -> %s",
            getattr(self, "id", None),
            old_status,
            self.status,
        )
        return True

    def activate(self) -> bool:
        """Activate this vision."""
        if self.status == "active":
            return False
        
        old_status = self.status
        self.status = "active"
        self.updated_at = datetime.now(timezone.utc)
        
        logger.info(
            "ProductVision %s activated: %s -> %s",
            getattr(self, "id", None),
            old_status,
            self.status,
        )
        return True