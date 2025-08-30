# Compat shim: reexporta API pública a partir de steps.pv_state
from .pv_state import (
    DEFAULT_PV, PV_FIELDS,
    init_pv_state, clamp_pv_step_idx, set_pv_mode,
    next_step, prev_step, total_steps, is_review_step,
    constraints_to_text, constraints_from_text,
)
"""
_pv_state (compat shim)
=======================

Arquivo de **compatibilidade retroativa** para manter imports existentes:

    from ._pv_state import ...

Ele **reexporta** a API pública do novo pacote `pv_state`.  
Pode ser removido no futuro após a migração total dos imports.
"""

from .pv_state import (
    DEFAULT_PV,
    PV_FIELDS,
    init_pv_state,
    clamp_pv_step_idx,
    set_pv_mode,
    next_step,
    prev_step,
    total_steps,
    is_review_step,
    constraints_to_text,
    constraints_from_text,
)
