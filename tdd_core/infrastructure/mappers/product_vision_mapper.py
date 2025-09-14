"""
ProductVision Mapper

Maps between database rows and the ProductVision domain entity.
Assumes migration 012 is applied: all fields are first-class columns
and must_have/cannot_have are stored as TEXT (strings).
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping

from ...domain.entities.product_vision import ProductVision


class ProductVisionMapper:
    """Mapeador entre linha do banco e entidade ProductVision."""

    @staticmethod
    def from_db_row(row: Mapping[str, Any]) -> ProductVision:
        """Cria ProductVision a partir de uma linha do banco (dict ou sqlite3.Row)."""
        def get(key: str, default: Any = "") -> Any:
            # sqlite3.Row does not implement 'in' or 'get'; use keys() + try/except
            if hasattr(row, "keys"):
                try:
                    return row[key]
                except Exception:
                    return default
            if hasattr(row, "get"):
                return row.get(key, default)
            return default

        return ProductVision(
            # Obrigatórios
            name=str(get("name", "")),
            vision_statement=str(get("vision_statement", "")),
            target_user=str(get("target_audience", "")),
            user_problem=str(get("problem_statement", "")),
            expected_benefits=str(get("value_proposition", "")),
            product_description=str(get("product_description", "")),
            success_metrics=str(get("success_metrics", "")),
            tech_requirements=str(get("tech_requirements", "")),
            non_functional_requirements=str(get("non_functional_requirements", "")),
            compliance_requirements=str(get("compliance_requirements", "")),
            risks=str(get("risks", "")),
            assumptions=str(get("assumptions", "")),
            must_have=str(get("must_have", "")),
            cannot_have=str(get("cannot_have", "")),
            deliverables=str(get("deliverables", "")),
            market_opportunity=str(get("market_opportunity", "")),
            # Opcionais/Metadados
            id=get("id", None),
            created_at=get("created_at", None),
            updated_at=get("updated_at", None),
        )

    @staticmethod
    def to_db_fields(entity: ProductVision) -> MutableMapping[str, Any]:
        """Converte ProductVision para dict de colunas do banco (INSERT/UPDATE)."""
        return {
            "id": entity.id,
            "project_id": None,  # preencher no repositório ao associar ao projeto
            "name": entity.name,
            "vision_statement": entity.vision_statement,
            "problem_statement": entity.user_problem,
            "target_audience": entity.target_user,
            "value_proposition": entity.expected_benefits,
            "product_description": entity.product_description,
            "success_metrics": entity.success_metrics,
            "tech_requirements": entity.tech_requirements,
            "non_functional_requirements": entity.non_functional_requirements,
            "compliance_requirements": entity.compliance_requirements,
            "risks": entity.risks,
            "assumptions": entity.assumptions,
            "must_have": entity.must_have,
            "cannot_have": entity.cannot_have,
            "deliverables": entity.deliverables,
            "market_opportunity": entity.market_opportunity,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }


__all__ = ["ProductVisionMapper"]
