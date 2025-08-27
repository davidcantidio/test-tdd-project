# streamlit_extension/pages/projetos/steps/_pv_state.py
from __future__ import annotations
from typing import Any, Dict, List

DEFAULT_PV: Dict[str, Any] = {
    "vision_statement": "",
    "problem_statement": "",
    "target_audience": "",
    "value_proposition": "",
    "constraints": [],  # list[str]
}

PV_FIELDS = [
    ("vision_statement", "Declaração de Visão"),
    ("problem_statement", "Problema a Resolver"),
    ("target_audience", "Público-alvo"),
    ("value_proposition", "Proposta de Valor"),
    ("constraints", "Restrições (uma por linha)"),
]

def init_pv_state(ss) -> None:
    """Garante chaves e tipos corretos no session_state."""
    if "pv" not in ss or not isinstance(ss.pv, dict):
        ss.pv = dict(DEFAULT_PV)
    else:
        # corrige tipos e campos ausentes
        for k, v in DEFAULT_PV.items():
            if k not in ss.pv:
                ss.pv[k] = v
        if not isinstance(ss.pv.get("constraints"), list):
            ss.pv["constraints"] = []

    if "pv_mode" not in ss or ss.pv_mode not in {"form", "steps"}:
        ss.pv_mode = "form"

    if "pv_step_idx" not in ss or not isinstance(ss.pv_step_idx, int):
        ss.pv_step_idx = 0
    clamp_pv_step_idx(ss)

def clamp_pv_step_idx(ss) -> None:
    """Mantém o índice de passo dentro do range válido."""
    max_idx = len(PV_FIELDS) - 1
    ss.pv_step_idx = max(0, min(ss.pv_step_idx, max_idx))

def set_pv_mode(ss, mode: str) -> None:
    """Alterna entre 'form' e 'steps' sem perder dados."""
    ss.pv_mode = "form" if mode not in {"form", "steps"} else mode

def next_step(ss) -> None:
    ss.pv_step_idx += 1
    clamp_pv_step_idx(ss)

def prev_step(ss) -> None:
    ss.pv_step_idx -= 1
    clamp_pv_step_idx(ss)

def constraints_to_text(lst: List[str]) -> str:
    return "\n".join([x for x in (lst or []) if isinstance(x, str) and x.strip()])

def constraints_from_text(txt: str) -> List[str]:
    items = [line.strip() for line in (txt or "").splitlines()]
    return [x for x in items if x]
