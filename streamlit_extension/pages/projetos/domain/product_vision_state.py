from __future__ import annotations
from typing import Dict, Any, Tuple, List

DEFAULT_PV: Dict[str, Any] = {
    "vision_statement": "",
    "problem_statement": "",
    "target_audience": "",
    "value_proposition": "",
    "constraints": [],  # list[str]
}

REQUIRED_FIELDS = [
    "vision_statement",
    "problem_statement",
    "target_audience",
    "value_proposition",
    "constraints",
]

def normalize_constraints(items: List[str]) -> List[str]:
    return [x.strip() for x in (items or []) if isinstance(x, str) and x.strip()]

def all_fields_filled(pv: Dict[str, Any]) -> bool:
    for k in REQUIRED_FIELDS:
        v = pv.get(k)
        if isinstance(v, str):
            if not v.strip():
                return False
        elif isinstance(v, list):
            if len(normalize_constraints(v)) == 0:
                return False
        else:
            return False
    return True

def validate_product_vision(pv: Dict[str, Any]) -> Tuple[bool, str | None]:
    # mensagens objetivas para UX
    missing: List[str] = []
    for k in ["vision_statement","problem_statement","target_audience","value_proposition"]:
        if not isinstance(pv.get(k), str) or not pv[k].strip():
            missing.append(k)
    if not isinstance(pv.get("constraints"), list) or len(normalize_constraints(pv["constraints"])) == 0:
        missing.append("constraints")

    if missing:
        return False, f"Campos obrigatórios ausentes/invalidos: {', '.join(missing)}"
    return True, None

def apply_refine_result(current: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(current)
    for k in ["vision_statement","problem_statement","target_audience","value_proposition"]:
        val = result.get(k)
        if isinstance(val, str) and val.strip():
            merged[k] = val.strip()
    cons = result.get("constraints")
    if isinstance(cons, list) and len(normalize_constraints(cons)) > 0:
        merged["constraints"] = normalize_constraints(cons)
    return merged

def refine_all_and_apply(pv: Dict[str, Any], refiner) -> Dict[str, Any]:
    """
    refiner deve expor .refine(payload: dict) -> dict
    payload/retorno seguem a mesma taxonomia do banco.
    """
    payload = {
        "vision_statement": pv.get("vision_statement", "").strip(),
        "problem_statement": pv.get("problem_statement", "").strip(),
        "target_audience": pv.get("target_audience", "").strip(),
        "value_proposition": pv.get("value_proposition", "").strip(),
        "constraints": normalize_constraints(pv.get("constraints", [])),
    }
    result = refiner.refine(payload)  # pode ser parcial
    return apply_refine_result(pv, result)
