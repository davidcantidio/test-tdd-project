#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📋 MODELS - ProductVision ORM Model

Camada estratégica entre Projects e Epics.
Compatibilizada com SQLAlchemy 2.x (typed ORM) e mixins do projeto.

Usage:
    from streamlit_extension.models.product_vision import ProductVisionORM
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import (
    Integer,
    String,
    Text,
    Date,
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
from .mixins import AuditMixin, JSONFieldMixin, TDDWorkflowMixin

logger = logging.getLogger(__name__)


JsonObj = Dict[str, Any]
JsonArr = List[Dict[str, Any]]
JsonVal = Union[JsonObj, JsonArr, List[Any], Dict[str, Any]]


class ProductVisionORM(Base, AuditMixin, JSONFieldMixin, TDDWorkflowMixin):
    """
    Strategic product visions:
    - Goals, personas, KPIs, risks, market analysis
    - TDD validation criteria, testing strategy
    - Aprovação e saúde do roadmap
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

    # Vision Identification
    vision_key: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Vision Content
    vision_statement: Mapped[str] = mapped_column(Text, nullable=False)
    problem_statement: Mapped[Optional[str]] = mapped_column(Text)
    target_audience: Mapped[Optional[str]] = mapped_column(Text)
    value_proposition: Mapped[Optional[str]] = mapped_column(Text)

    # JSON fields — armazenados como JSON nativo; mixin provê helpers get/set
    success_metrics: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array

    # Strategic Goals
    strategic_goals: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array
    key_features: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array
    user_personas: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array
    market_analysis: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # object
    competitive_landscape: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # object

    # Business Context
    business_objectives: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array
    revenue_impact: Mapped[Optional[str]] = mapped_column(Text)
    cost_benefit_analysis: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # object
    risk_assessment: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # object
    assumptions: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array

    # Timeline & Planning
    vision_timeline: Mapped[Optional[str]] = mapped_column(Text)
    target_launch_date: Mapped[Optional[date]] = mapped_column(Date)
    market_readiness_date: Mapped[Optional[date]] = mapped_column(Date)

    # Validation & Testing
    validation_criteria: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array
    testing_strategy: Mapped[Optional[str]] = mapped_column(Text)
    feedback_sources: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array
    iteration_plan: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # object

    # Status & Progress
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        server_default=text("'draft'"),
        nullable=False,
    )  # draft, review, approved, active, launched, retired
    priority: Mapped[int] = mapped_column(
        Integer, default=3, server_default=text("3"), nullable=False
    )  # 1-5
    confidence_level: Mapped[int] = mapped_column(
        Integer, default=5, server_default=text("5"), nullable=False
    )  # 1-10
    approval_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        server_default=text("'pending'"),
        nullable=False,
    )  # pending, approved, rejected

    # Stakeholders
    product_owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("framework_users.id"), index=True
    )
    stakeholders: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array
    approval_committee: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array

    # Metrics & KPIs
    success_kpis: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array
    measurement_plan: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # object
    baseline_metrics: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # object
    target_metrics: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # object

    # Documentation
    documentation_links: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array
    reference_materials: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array
    design_assets: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array
    prototype_links: Mapped[Optional[JsonVal]] = mapped_column(JSON)  # array

    # Multi-user Support (AuditMixin já provê created_by/updated_by/deleted_by)
    assigned_to: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("framework_users.id"), index=True
    )
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("framework_users.id"), index=True
    )

    # Additional Audit Trail
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    launched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("project_id", "vision_key", name="uq_product_visions_project_key"),
        Index("ix_product_visions_project_status", "project_id", "status"),
    )

    # -------------------------------------------------------------------------
    # Dunder & Representation
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        vid = getattr(self, "id", None)
        vkey = getattr(self, "vision_key", "") or ""
        vname = getattr(self, "name", "") or ""
        suffix = "..." if len(vname) > 50 else ""
        return f"<ProductVision(id={vid}, key='{vkey}', name='{vname[:50]}{suffix}')>"

    # -------------------------------------------------------------------------
    # Strategic Goals Management
    # -------------------------------------------------------------------------
    def get_strategic_goals(self) -> List[Dict[str, Any]]:
        return self.get_json_field("strategic_goals", [])

    def add_strategic_goal(
        self,
        goal: str,
        description: str = "",
        success_criteria: Optional[List[str]] = None,
    ) -> bool:
        goal_obj: Dict[str, Any] = {
            "goal": goal,
            "description": description,
            "success_criteria": success_criteria or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.append_to_json_array("strategic_goals", goal_obj)

    def get_key_features(self) -> List[Dict[str, Any]]:
        return self.get_json_field("key_features", [])

    def add_key_feature(
        self, feature: str, description: str = "", priority: str = "medium"
    ) -> bool:
        feature_obj: Dict[str, Any] = {
            "feature": feature,
            "description": description,
            "priority": priority,  # low, medium, high, critical
            "status": "planned",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.append_to_json_array("key_features", feature_obj)

    # -------------------------------------------------------------------------
    # User Personas Management
    # -------------------------------------------------------------------------
    def get_user_personas(self) -> List[Dict[str, Any]]:
        return self.get_json_field("user_personas", [])

    def add_user_persona(
        self,
        name: str,
        description: str,
        demographics: Optional[Dict[str, Any]] = None,
        needs: Optional[List[str]] = None,
        pain_points: Optional[List[str]] = None,
    ) -> bool:
        persona_obj: Dict[str, Any] = {
            "name": name,
            "description": description,
            "demographics": demographics or {},
            "needs": needs or [],
            "pain_points": pain_points or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.append_to_json_array("user_personas", persona_obj)

    # -------------------------------------------------------------------------
    # Success Metrics Management
    # -------------------------------------------------------------------------
    def get_success_metrics(self) -> List[Dict[str, Any]]:
        return self.get_json_field("success_metrics", [])

    def add_success_metric(
        self,
        name: str,
        description: str,
        target_value: Any,
        measurement_method: str = "",
        frequency: str = "monthly",
    ) -> bool:
        metric_obj: Dict[str, Any] = {
            "name": name,
            "description": description,
            "target_value": target_value,
            "measurement_method": measurement_method,
            "frequency": frequency,
            "current_value": None,
            "status": "not_started",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.append_to_json_array("success_metrics", metric_obj)

    def update_metric_value(self, metric_name: str, current_value: Any) -> bool:
        metrics = self.get_success_metrics()
        for metric in metrics:
            if metric.get("name") == metric_name:
                metric["current_value"] = current_value
                metric["last_updated"] = datetime.now(timezone.utc).isoformat()
                return self.set_json_field("success_metrics", metrics)
        return False

    # -------------------------------------------------------------------------
    # Market Analysis Management
    # -------------------------------------------------------------------------
    def get_market_analysis(self) -> Dict[str, Any]:
        return self.get_json_field("market_analysis", {})

    def update_market_analysis(
        self,
        market_size: str = "",
        growth_rate: str = "",
        key_trends: Optional[List[str]] = None,
        opportunities: Optional[List[str]] = None,
        threats: Optional[List[str]] = None,
    ) -> bool:
        analysis_data: Dict[str, Any] = {
            "market_size": market_size,
            "growth_rate": growth_rate,
            "key_trends": key_trends or [],
            "opportunities": opportunities or [],
            "threats": threats or [],
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        return self.update_json_object("market_analysis", analysis_data)

    def get_competitive_landscape(self) -> Dict[str, Any]:
        return self.get_json_field("competitive_landscape", {})

    def add_competitor(
        self,
        name: str,
        strengths: Optional[List[str]] = None,
        weaknesses: Optional[List[str]] = None,
        market_share: str = "",
        differentiation: str = "",
    ) -> bool:
        landscape = self.get_competitive_landscape()
        competitors = landscape.get("competitors") or []
        competitor_obj: Dict[str, Any] = {
            "name": name,
            "strengths": strengths or [],
            "weaknesses": weaknesses or [],
            "market_share": market_share,
            "differentiation": differentiation,
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        competitors.append(competitor_obj)
        landscape["competitors"] = competitors
        return self.set_json_field("competitive_landscape", landscape)

    # -------------------------------------------------------------------------
    # Risk Assessment Management
    # -------------------------------------------------------------------------
    def get_risk_assessment(self) -> Dict[str, Any]:
        return self.get_json_field("risk_assessment", {})

    def add_risk(
        self,
        risk_type: str,
        description: str,
        probability: str,
        impact: str,
        mitigation_strategy: str = "",
        owner: str = "",
    ) -> bool:
        assessment = self.get_risk_assessment()
        risks = assessment.get("risks") or []
        risk_obj: Dict[str, Any] = {
            "type": risk_type,  # technical, market, resource, timeline, financial
            "description": description,
            "probability": probability,  # low, medium, high
            "impact": impact,  # low, medium, high, critical
            "mitigation_strategy": mitigation_strategy,
            "owner": owner,
            "status": "identified",  # identified, planning, mitigating, resolved
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        risks.append(risk_obj)
        assessment["risks"] = risks
        assessment["last_updated"] = datetime.now(timezone.utc).isoformat()
        return self.set_json_field("risk_assessment", assessment)

    # -------------------------------------------------------------------------
    # Validation and Testing Integration
    # -------------------------------------------------------------------------
    def get_validation_criteria(self) -> List[Dict[str, Any]]:
        return self.get_json_field("validation_criteria", [])

    def add_validation_criterion(
        self,
        criterion: str,
        method: str,
        success_threshold: str,
        responsible_party: str = "",
    ) -> bool:
        criterion_obj: Dict[str, Any] = {
            "criterion": criterion,
            "validation_method": method,
            "success_threshold": success_threshold,
            "responsible_party": responsible_party,
            "status": "not_started",  # not_started, in_progress, passed, failed
            "results": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.append_to_json_array("validation_criteria", criterion_obj)

    def update_validation_result(
        self, criterion: str, status: str, results: Optional[Dict[str, Any]] = None
    ) -> bool:
        criteria = self.get_validation_criteria()
        for item in criteria:
            if item.get("criterion") == criterion:
                item["status"] = status
                item["results"] = results or {}
                item["validated_at"] = datetime.now(timezone.utc).isoformat()
                return self.set_json_field("validation_criteria", criteria)
        return False

    # -------------------------------------------------------------------------
    # Status and Workflow Management
    # -------------------------------------------------------------------------
    def can_transition_to_status(self, new_status: str) -> bool:
        valid_transitions = {
            "draft": ["review", "approved"],
            "review": ["draft", "approved", "rejected"],
            "approved": ["active", "rejected"],
            "rejected": ["draft"],
            "active": ["launched", "retired"],
            "launched": ["retired"],
            "retired": [],
        }
        return new_status in valid_transitions.get(self.status, [])

    def transition_status(self, new_status: str, user_id: Optional[int] = None) -> bool:
        if not self.can_transition_to_status(new_status):
            logger.warning(
                "Invalid status transition for ProductVision %s: %s -> %s",
                getattr(self, "id", None),
                self.status,
                new_status,
            )
            return False

        old_status = self.status
        self.status = new_status

        now = datetime.now(timezone.utc)
        if new_status == "approved":
            self.approved_at = now
            self.approval_status = "approved"
        elif new_status == "launched":
            self.launched_at = now
        elif new_status == "retired":
            self.retired_at = now

        # Audit/update
        self.updated_by = user_id
        self.touch(user_id)

        logger.info(
            "ProductVision %s status changed: %s -> %s",
            getattr(self, "id", None),
            old_status,
            new_status,
        )
        return True

    # -------------------------------------------------------------------------
    # Progress and Analytics
    # -------------------------------------------------------------------------
    def calculate_completion_percentage(self) -> float:
        completion_factors: List[tuple[str, float, float]] = []

        # Basic information completeness
        basic_fields = [
            self.vision_statement,
            self.problem_statement,
            self.target_audience,
            self.value_proposition,
        ]
        basic_completeness = sum(1 for field in basic_fields if field) / len(basic_fields)
        completion_factors.append(("basic_info", basic_completeness, 0.2))

        # Strategic goals completeness
        goals = self.get_strategic_goals()
        goals_completeness = 1.0 if len(goals) >= 3 else (len(goals) / 3 if goals else 0.0)
        completion_factors.append(("strategic_goals", goals_completeness, 0.2))

        # User personas completeness
        personas = self.get_user_personas()
        personas_completeness = 1.0 if len(personas) >= 2 else (len(personas) / 2 if personas else 0.0)
        completion_factors.append(("user_personas", personas_completeness, 0.15))

        # Market analysis completeness (mínimo 3 chaves)
        market = self.get_market_analysis()
        market_size = len(market.keys()) if isinstance(market, dict) else 0
        market_completeness = 1.0 if market_size >= 3 else (market_size / 3 if market_size else 0.0)
        completion_factors.append(("market_analysis", market_completeness, 0.15))

        # Success metrics completeness
        metrics = self.get_success_metrics()
        metrics_completeness = 1.0 if len(metrics) >= 3 else (len(metrics) / 3 if metrics else 0.0)
        completion_factors.append(("success_metrics", metrics_completeness, 0.15))

        # Risk assessment completeness
        risks = (self.get_risk_assessment() or {}).get("risks", [])
        risk_completeness = 1.0 if len(risks) >= 2 else (len(risks) / 2 if risks else 0.0)
        completion_factors.append(("risk_assessment", risk_completeness, 0.1))

        # Validation criteria completeness
        validation = self.get_validation_criteria()
        validation_completeness = 1.0 if len(validation) >= 2 else (len(validation) / 2 if validation else 0.0)
        completion_factors.append(("validation", validation_completeness, 0.05))

        total_score = sum(c * w for _, c, w in completion_factors)
        return float(min(total_score * 100, 100.0))

    def get_health_score(self) -> Dict[str, Any]:
        health_data: Dict[str, Any] = {
            "overall_score": 0.0,
            "completion_percentage": self.calculate_completion_percentage(),
            "status_health": self.status in ["approved", "active"],
            "timeline_health": True,
            "stakeholder_health": True,
            "risk_health": True,
            "recommendations": [],
        }

        # Timeline health
        if self.target_launch_date:
            days_to_launch = (self.target_launch_date - date.today()).days
            health_data["timeline_health"] = days_to_launch > 30
            if days_to_launch <= 0:
                health_data["recommendations"].append("Launch date has passed - update timeline")
            elif days_to_launch <= 30:
                health_data["recommendations"].append("Approaching launch date - verify readiness")

        # Stakeholder health
        stakeholders = self.get_json_field("stakeholders", [])
        health_data["stakeholder_health"] = len(stakeholders) >= 2
        if len(stakeholders) < 2:
            health_data["recommendations"].append("Add more stakeholders for better governance")

        # Risk health
        risks = (self.get_risk_assessment() or {}).get("risks", [])
        high_risk_count = sum(1 for risk in risks if risk.get("impact") == "high")
        health_data["risk_health"] = high_risk_count <= 2
        if high_risk_count > 2:
            health_data["recommendations"].append("Address high-impact risks to improve health")

        health_factors = [
            health_data["completion_percentage"] / 100,
            1.0 if health_data["status_health"] else 0.5,
            1.0 if health_data["timeline_health"] else 0.7,
            1.0 if health_data["stakeholder_health"] else 0.8,
            1.0 if health_data["risk_health"] else 0.6,
        ]
        health_data["overall_score"] = sum(health_factors) / len(health_factors) * 100
        return health_data

    # -------------------------------------------------------------------------
    # TDD Integration Overrides
    # -------------------------------------------------------------------------
    def validate_tdd_workflow(self) -> bool:
        if self.is_tdd_exempt:
            return True
        validation_criteria = self.get_validation_criteria()
        return len(validation_criteria) >= 2

    def calculate_tdah_complexity(self) -> int:
        complexity_score = 1

        content_length = len(self.vision_statement or "") + len(self.problem_statement or "")
        if content_length > 1000:
            complexity_score += 2
        elif content_length > 500:
            complexity_score += 1

        goals_count = len(self.get_strategic_goals())
        features_count = len(self.get_key_features())
        total = goals_count + features_count
        if total > 10:
            complexity_score += 3
        elif total > 5:
            complexity_score += 2
        elif total > 2:
            complexity_score += 1

        stakeholders_count = len(self.get_json_field("stakeholders", []))
        if stakeholders_count > 5:
            complexity_score += 2
        elif stakeholders_count > 2:
            complexity_score += 1

        return min(complexity_score, 10)

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "vision_key": self.vision_key,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "confidence_level": self.confidence_level,
            "completion_percentage": self.calculate_completion_percentage(),
            "health_score": self.get_health_score()["overall_score"],
            "target_launch_date": self.target_launch_date.isoformat() if self.target_launch_date else None,
            "created_at": self.created_at.isoformat() if getattr(self, "created_at", None) else None,
            "updated_at": self.updated_at.isoformat() if getattr(self, "updated_at", None) else None,
        }

    def clone(self, new_vision_key: str, new_name: str) -> "ProductVisionORM":
        """Create a copy of this product vision with new key and name."""
        return ProductVisionORM(
            project_id=self.project_id,
            vision_key=new_vision_key,
            name=new_name,
            vision_statement=self.vision_statement,
            problem_statement=self.problem_statement,
            target_audience=self.target_audience,
            value_proposition=self.value_proposition,
            # JSON fields (copiados como objetos/arrays)
            strategic_goals=self.strategic_goals,
            key_features=self.key_features,
            user_personas=self.user_personas,
            market_analysis=self.market_analysis,
            competitive_landscape=self.competitive_landscape,
            business_objectives=self.business_objectives,
            revenue_impact=self.revenue_impact,
            cost_benefit_analysis=self.cost_benefit_analysis,
            risk_assessment=self.risk_assessment,
            assumptions=self.assumptions,
            success_metrics=self.success_metrics,
            validation_criteria=self.validation_criteria,
            testing_strategy=self.testing_strategy,
            # Reset status fields
            status="draft",
            approval_status="pending",
            priority=self.priority,
            confidence_level=5,
        )
