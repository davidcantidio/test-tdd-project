"""
Caracterização de navegação do fluxo step-by-step:
- next_step / prev_step
- clamp de limites
- total_steps inclui passo de revisão
"""

import pytest

# Fake session_state simples
class SS(dict):
    pass


def _init():
    from streamlit_extension.pages.projetos.steps.pv_state import init_pv_state
    ss = SS()
    init_pv_state(ss)
    return ss


def test_total_steps_includes_review():
    from streamlit_extension.pages.projetos.steps.pv_state import total_steps, PV_FIELDS
    assert total_steps() == len(PV_FIELDS) + 1


def test_next_prev_basic_flow():
    from streamlit_extension.pages.projetos.steps.pv_state import next_step, prev_step, is_review_step, total_steps

    ss = _init()
    assert ss["pv_step_idx"] == 0
    assert is_review_step(ss) is False

    # Avança até o penúltimo passo (último campo)
    for _ in range(total_steps() - 2):
        next_step(ss)
    assert ss["pv_step_idx"] == total_steps() - 2
    assert is_review_step(ss) is False

    # Avança para passo de revisão
    next_step(ss)
    assert ss["pv_step_idx"] == total_steps() - 1
    assert is_review_step(ss) is True

    # Avançar além não ultrapassa (clamp)
    next_step(ss)
    assert ss["pv_step_idx"] == total_steps() - 1

    # Voltar remove flag de revisão
    prev_step(ss)
    assert is_review_step(ss) is False
    assert ss["pv_step_idx"] == total_steps() - 2

    # Voltar até zero e clamp no início
    for _ in range(100):
        prev_step(ss)
    assert ss["pv_step_idx"] == 0


def test_clamp_manual_set_large_and_negative():
    from streamlit_extension.pages.projetos.steps.pv_state import clamp_pv_step_idx, total_steps

    ss = _init()
    ss["pv_step_idx"] = 999
    clamp_pv_step_idx(ss)
    assert ss["pv_step_idx"] == total_steps() - 1

    ss["pv_step_idx"] = -42
    clamp_pv_step_idx(ss)
    assert ss["pv_step_idx"] == 0
