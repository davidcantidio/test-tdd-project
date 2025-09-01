"""
Garante compatibilidade retroativa:
- Imports antigos via ._pv_state continuam válidos
- API pública preservada
"""

def test_compat_shim_reexports_public_api():
    from streamlit_extension.pages.projetos.steps._pv_state import (
        DEFAULT_PV, PV_FIELDS,
        init_pv_state, clamp_pv_step_idx, set_pv_mode,
        next_step, prev_step, total_steps, is_review_step,
        constraints_to_text, constraints_from_text,
    )
    # Apenas valida que símbolos existem e são chamáveis/iteráveis onde esperado
    assert isinstance(DEFAULT_PV, dict)
    assert isinstance(PV_FIELDS, list)
    assert callable(init_pv_state)
    assert callable(clamp_pv_step_idx)
    assert callable(set_pv_mode)
    assert callable(next_step)
    assert callable(prev_step)
    assert callable(total_steps)
    assert callable(is_review_step)
    assert callable(constraints_to_text)
    assert callable(constraints_from_text)
