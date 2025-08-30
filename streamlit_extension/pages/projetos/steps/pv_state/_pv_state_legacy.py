# streamlit_extension/pages/projetos/steps/_pv_state.py
from __future__ import annotations
from typing import Any, Dict, List

# -----------------------------
# Estado e metadados do Product Vision
# -----------------------------

DEFAULT_PV: Dict[str, Any] = {
    "vision_statement": "",
    "problem_statement": "",
    "target_audience": "",
    "value_proposition": "",
    "constraints": [],  # list[str]
}

# Ordem dos campos no fluxo step-by-step
PV_FIELDS = [
    ("vision_statement", "Declaração de Visão"),
    ("problem_statement", "Problema a Resolver"),
    ("target_audience", "Público-alvo"),
    ("value_proposition", "Proposta de Valor"),
    ("constraints", "Restrições (uma por linha)"),
]

# -----------------------------
# Inicialização e navegação
# -----------------------------

def init_pv_state(ss) -> None:
    """Garante chaves/tipos corretos no session_state e define defaults."""
    if "pv" not in ss or not isinstance(ss.pv, dict):
        ss.pv = dict(DEFAULT_PV)
    else:
        # Corrige tipos e campos ausentes
        for k, v in DEFAULT_PV.items():
            if k not in ss.pv:
                ss.pv[k] = v
        if not isinstance(ss.pv.get("constraints"), list):
            ss.pv["constraints"] = []

    # Default agora é step-by-step
    if "pv_mode" not in ss or ss.pv_mode not in {"form", "steps"}:
        ss.pv_mode = "steps"

    if "pv_step_idx" not in ss or not isinstance(ss.pv_step_idx, int):
        ss.pv_step_idx = 0
    clamp_pv_step_idx(ss)


def clamp_pv_step_idx(ss) -> None:
    """Mantém o índice de passo dentro do range válido (inclui passo de revisão)."""
    # Permitimos um passo extra de "revisão final" (formulário completo)
    max_idx = len(PV_FIELDS)  # índices 0..len(PV_FIELDS)-1 = campos, len(PV_FIELDS) = revisão
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


def is_review_step(ss) -> bool:
    """True se o índice atual for o passo de revisão final (form completo)."""
    return ss.pv_step_idx == len(PV_FIELDS)


def total_steps() -> int:
    """Total de passos considerando o passo de revisão final."""
    return len(PV_FIELDS) + 1

# -----------------------------
# Utilidades para constraints
# -----------------------------

def constraints_to_text(lst: List[str]) -> str:
    return "\n".join([x for x in (lst or []) if isinstance(x, str) and x.strip()])


def constraints_from_text(txt: str) -> List[str]:
    items = [line.strip() for line in (txt or "").splitlines()]
    return [x for x in items if x]
