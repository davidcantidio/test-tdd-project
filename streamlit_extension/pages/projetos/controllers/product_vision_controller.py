# streamlit_extension/pages/projetos/controllers/product_vision_controller.py
from __future__ import annotations
from typing import Dict, Any

from ..domain.product_vision_state import (
    DEFAULT_PV,
    validate_product_vision,
    apply_refine_result,
    refine_all_and_apply,
)

HUMAN_LABELS = {
    "vision_statement": "Declaração de Visão",
    "problem_statement": "Problema",
    "target_audience": "Público-alvo",
    "value_proposition": "Proposta de Valor",
    "constraints": "Restrições",
}

def _ensure_shape(pv: Dict[str, Any]) -> Dict[str, Any]:
    data = {**DEFAULT_PV}
    data.update(pv or {})
    # garante tipos básicos
    if not isinstance(data["constraints"], list):
        data["constraints"] = []
    return data

# -------- API esperada pelos testes --------
def can_refine(pv: Dict[str, Any]) -> bool:
    ok, _ = validate_product_vision(_ensure_shape(pv))
    return ok

def can_save(pv: Dict[str, Any]) -> bool:
    ok, _ = validate_product_vision(_ensure_shape(pv))
    return ok

def build_summary(pv: Dict[str, Any]) -> Dict[str, str]:
    pv = _ensure_shape(pv)
    cons_list = [c for c in (pv.get("constraints") or []) if isinstance(c, str) and c.strip()]
    cons_str = ", ".join(cons_list)
    return {
        HUMAN_LABELS["vision_statement"]: pv.get("vision_statement", "").strip(),
        HUMAN_LABELS["problem_statement"]: pv.get("problem_statement", "").strip(),
        HUMAN_LABELS["target_audience"]: pv.get("target_audience", "").strip(),
        HUMAN_LABELS["value_proposition"]: pv.get("value_proposition", "").strip(),
        HUMAN_LABELS["constraints"]: cons_str,
    }

def apply_refinement(current: Dict[str, Any], refined: Dict[str, Any]) -> Dict[str, Any]:
    current = _ensure_shape(current)
    refined = refined or {}
    return apply_refine_result(current, refined)

def refine_with_service(current: Dict[str, Any], service) -> Dict[str, Any]:
    """service deve expor .refine(payload: dict) -> dict"""
    current = _ensure_shape(current)
    try:
        merged = refine_all_and_apply(current, service)
    except Exception as e:
        # propaga como ValueError para os testes capturarem
        raise ValueError(str(e))
    return merged
