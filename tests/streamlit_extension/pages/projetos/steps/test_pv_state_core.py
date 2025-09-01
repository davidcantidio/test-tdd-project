"""
Testes do pacote pv_state.

Objetivo: garantir o contrato público antes/depois da refatoração.
"""

# Simples *fake* de session_state
class SS(dict):
    pass


def test_defaults_and_modes():
    from streamlit_extension.pages.projetos.steps.pv_state import init_pv_state, total_steps, is_review_step

    ss = SS()
    init_pv_state(ss)
    assert ss["pv_mode"] == "steps"
    assert ss["pv_step_idx"] == 0
    assert total_steps() >= 2  # há pelo menos 1 campo + 1 revisão
    assert is_review_step(ss) is False


def test_review_step_bounds():
    from streamlit_extension.pages.projetos.steps.pv_state import init_pv_state, clamp_pv_step_idx, total_steps, is_review_step

    ss = SS()
    init_pv_state(ss)
    ss["pv_step_idx"] = 999
    clamp_pv_step_idx(ss)
    assert ss["pv_step_idx"] == total_steps() - 1
    assert is_review_step(ss) is True


def test_constraints_roundtrip():
    from streamlit_extension.pages.projetos.steps.pv_state import constraints_to_text, constraints_from_text

    text = constraints_to_text([" a ", "", "b", " ", "c"])
    assert text.splitlines() == [" a ", "b", "c"]

    back = constraints_from_text(text)
    assert back == ["a", "b", "c"]
