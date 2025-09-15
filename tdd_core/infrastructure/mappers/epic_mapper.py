"""
Epic Mapper

Maps between database rows and the Epic domain entity.
Assumes a framework_epics table with explicit columns for AI/topological fields.
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping

from ...domain.entities.epic import Epic


class EpicMapper:
    """Mapper entre linha de banco e entidade Epic."""

    @staticmethod
    def from_db_row(row: Mapping[str, Any]) -> Epic:
        def get(key: str, default: Any = None) -> Any:
            if hasattr(row, "keys"):
                try:
                    return row[key]
                except Exception:
                    return default
            if hasattr(row, "get"):
                return row.get(key, default)
            return default

        return Epic(
            # obrigatórios
            project_id=int(get("project_id", 0)),
            key=str(get("epic_key", "")),
            name=str(get("name", "")),
            description=str(get("description", "")),
            # opcionais e IA/topologia
            id=get("id", None),
            product_vision_id=get("product_vision_id", None),
            status=str(get("status", "pending")),
            priority=int(get("priority", 3) or 3),
            ai_generated=bool(get("ai_generated", 0)),
            ai_confidence=float(get("ai_confidence", 0.0) or 0.0),
            complexity_score=float(get("complexity_score", 3.0) or 3.0),
            effort_estimate=int(get("effort_estimate", 5) or 5),
            sort_order=int(get("sort_order", 0) or 0),
            unblock_potential=int(get("unblock_potential", 0) or 0),
            critical_path_weight=float(get("critical_path_weight", 0.0) or 0.0),
            tdd_phase=str(get("tdd_phase", "analysis")),
            tdd_order=int(get("tdd_order", 1) or 1),
            business_value=int(get("business_value", 5) or 5),
            risk_mitigation=int(get("risk_mitigation", 5) or 5),
            strategic_alignment=int(get("strategic_alignment", 5) or 5),
            created_at=get("created_at", None),
            updated_at=get("updated_at", None),
            started_at=get("started_at", None),
            completed_at=get("completed_at", None),
        )

    @staticmethod
    def to_db_fields(entity: Epic) -> MutableMapping[str, Any]:
        return {
            "id": entity.id,
            "project_id": entity.project_id,
            "epic_key": entity.key,
            "name": entity.name,
            "description": entity.description,
            "product_vision_id": entity.product_vision_id,
            "status": entity.status,
            "priority": entity.priority,
            "ai_generated": 1 if entity.ai_generated else 0,
            "ai_confidence": entity.ai_confidence,
            "complexity_score": entity.complexity_score,
            "effort_estimate": entity.effort_estimate,
            "sort_order": entity.sort_order,
            "unblock_potential": entity.unblock_potential,
            "critical_path_weight": entity.critical_path_weight,
            "tdd_phase": entity.tdd_phase,
            "tdd_order": entity.tdd_order,
            "business_value": entity.business_value,
            "risk_mitigation": entity.risk_mitigation,
            "strategic_alignment": entity.strategic_alignment,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "started_at": entity.started_at,
            "completed_at": entity.completed_at,
        }


__all__ = ["EpicMapper"]
