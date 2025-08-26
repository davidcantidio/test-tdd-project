from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple

REQUIRED_KEYS = [
    "vision_statement",
    "problem_statement",
    "target_audience",
    "value_proposition",
    "constraints",
]

def _normalize_constraints(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if isinstance(x, (str, int, float)) and str(x).strip()]
    # aceitar string com quebras de linha para facilitar agentes
    if isinstance(value, str):
        items = [line.strip() for line in value.splitlines()]
        return [x for x in items if x]
    # outros tipos → ignora
    return []

def _ensure_payload_shape(pv: Dict[str, Any]) -> Dict[str, Any]:
    data: Dict[str, Any] = {k: "" for k in REQUIRED_KEYS}
    data.update(pv or {})
    data["vision_statement"] = str(data.get("vision_statement", "")).strip()
    data["problem_statement"] = str(data.get("problem_statement", "")).strip()
    data["target_audience"] = str(data.get("target_audience", "")).strip()
    data["value_proposition"] = str(data.get("value_proposition", "")).strip()
    data["constraints"] = _normalize_constraints(data.get("constraints"))
    return data

def _validate_required(d: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    missing = []
    for k in REQUIRED_KEYS[:-1]:  # 4 strings
        if not isinstance(d.get(k), str) or not d[k].strip():
            missing.append(k)
    if len(_normalize_constraints(d.get("constraints"))) == 0:
        missing.append("constraints")
    if missing:
        return False, f"Campos obrigatórios ausentes/invalidos: {', '.join(missing)}"
    return True, None

class VisionRefineService:
    """
    Serviço de refinamento via agente (Agno/OpenAI/etc).
    O agente é injetado no construtor e deve expor: run(payload: dict) -> dict
    """

    def __init__(self, agent) -> None:
        self.agent = agent

    def refine(self, pv: Dict[str, Any]) -> Dict[str, Any]:
        # valida/normaliza entrada
        payload = _ensure_payload_shape(pv)
        ok, msg = _validate_required(payload)
        if not ok:
            raise ValueError(msg or "Entrada inválida.")

        # chama agente
        result = self.agent.run(payload)  # deve devolver dict (pode ser parcial, mas exigimos chaves)
        if not isinstance(result, dict):
            raise ValueError("Resposta inválida da IA (tipo inesperado).")

        # *** DIFERENÇA IMPORTANTE ***
        # Não preenchemos com payload quando o agente omite campos obrigatórios.
        # Em vez disso, exigimos que TODOS estejam presentes para evitar mascarar erros do agente.
        missing_keys = [k for k in REQUIRED_KEYS if k not in result]
        if missing_keys:
            raise ValueError(f"Resposta da IA ausente campo(s) obrigatório(s): {', '.join(missing_keys)}")

        # normaliza saída do agente
        out: Dict[str, Any] = {
            "vision_statement": str(result["vision_statement"]).strip(),
            "problem_statement": str(result["problem_statement"]).strip(),
            "target_audience": str(result["target_audience"]).strip(),
            "value_proposition": str(result["value_proposition"]).strip(),
            "constraints": _normalize_constraints(result["constraints"]),
        }

        # valida final (garante contrato)
        ok2, msg2 = _validate_required(out)
        if not ok2:
            raise ValueError(msg2 or "Resposta inválida da IA.")

        return out
