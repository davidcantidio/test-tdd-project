"""
init_nav
========

Inicialização de estado em `st.session_state` (ou objeto similar) e
*clamp* do índice de passos.

Regras implementadas:
- Sempre garantir as chaves do `DEFAULT_PV`
- `pv_mode` **padrão = "steps"** (decisão de produto)
- `pv_step_idx` começa em 0
- O índice é **limitado** para incluir também o *passo de revisão final*,
  que corresponde ao formulário completo no último passo.
"""

from __future__ import annotations
from typing import Any

from .state_core import DEFAULT_PV, PV_FIELDS


def init_pv_state(ss: Any) -> None:
    """
    Inicializa o estado do Product Vision no objeto de sessão.

    Parâmetros
    ----------
    ss : Any
        Um dicionário (ou objeto dict-like) usado como `session_state`.

    Efeitos
    -------
    - Garante existência e tipos em `ss["pv"]`.
    - Define `ss["pv_mode"]` para `"steps"` se ausente/ inválido.
    - Define `ss["pv_step_idx"]` para 0 se ausente/ inválido.
    - Faz *clamp* do índice com `clamp_pv_step_idx`.
    """
    if "pv" not in ss or not isinstance(ss["pv"], dict):
        ss["pv"] = dict(DEFAULT_PV)
    else:
        # Completa campos ausentes e corrige tipo de constraints
        for k, v in DEFAULT_PV.items():
            if k not in ss["pv"]:
                ss["pv"][k] = v
        if not isinstance(ss["pv"].get("constraints"), list):
            ss["pv"]["constraints"] = []

    # 🎯 Decisão de produto: default é step-by-step
    if "pv_mode" not in ss or ss["pv_mode"] not in {"form", "steps"}:
        ss["pv_mode"] = "steps"

    if "pv_step_idx" not in ss or not isinstance(ss["pv_step_idx"], int):
        ss["pv_step_idx"] = 0

    clamp_pv_step_idx(ss)


def clamp_pv_step_idx(ss: Any) -> None:
    """
    Mantém `pv_step_idx` dentro do intervalo permitido.

    - Índices `0..len(PV_FIELDS)-1` → campos individuais.
    - Índice `len(PV_FIELDS)`       → **passo de revisão** (formulário completo).

    Isso permite que o fluxo tenha um passo extra de revisão ao final.
    """
    max_idx = len(PV_FIELDS)  # último índice é a revisão
    ss["pv_step_idx"] = max(0, min(ss["pv_step_idx"], max_idx))


def set_pv_mode(ss: Any, mode: str) -> None:
    """
    Altera o modo de preenchimento do Product Vision.

    Parâmetros
    ----------
    ss : Any
        Objeto de sessão.
    mode : {"form", "steps"}
        Modo desejado.

    Observação
    ----------
    Se o valor for inválido, *fallback* para `"form"` por ser mais permissivo.
    """
    ss["pv_mode"] = "form" if mode not in {"form", "steps"} else mode
