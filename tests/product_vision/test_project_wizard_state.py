import pytest
from streamlit_extension.pages.projetos.state import (
    DEFAULT_DRAFT,
    init_wizard_state,
    current_step,
    move_to,
    validate_project_name,
    advance_from_name,
)

def test_init_wizard_state_sets_defaults():
    ss = {}
    init_wizard_state(ss)
    assert "projeto_wizard" in ss
    wiz = ss["projeto_wizard"]
    assert wiz["current_step"] == "project_name"
    # garante estrutura do rascunho
    assert sorted(wiz["project_draft"].keys()) == sorted(DEFAULT_DRAFT.keys())

def test_current_step_after_init_is_project_name():
    ss = {}
    init_wizard_state(ss)
    assert current_step(ss) == "project_name"

@pytest.mark.parametrize("name,ok", [
    ("", False),
    ("  ", False),
    ("ab", False),
    ("Meu Projeto", True),
])
def test_validate_project_name(name, ok):
    valid, msg = validate_project_name(name)
    assert valid == ok
    if ok:
        assert msg is None
    else:
        assert isinstance(msg, str) and msg != ""

def test_move_to_changes_step():
    ss = {}
    init_wizard_state(ss)
    move_to(ss, "product_vision")
    assert current_step(ss) == "product_vision"

def test_advance_from_name_success_moves_and_sets_name():
    ss = {}
    init_wizard_state(ss)
    ok, msg = advance_from_name(ss, "Plataforma de Cursos")
    assert ok is True and msg is None
    assert current_step(ss) == "product_vision"
    assert ss["projeto_wizard"]["project_draft"]["name"] == "Plataforma de Cursos"

def test_advance_from_name_fails_on_invalid_name():
    ss = {}
    init_wizard_state(ss)
    ok, msg = advance_from_name(ss, "  ")
    assert ok is False
    assert isinstance(msg, str) and msg  # mensagem presente
    # não deve avançar
    assert current_step(ss) == "project_name"
    assert ss["projeto_wizard"]["project_draft"]["name"] == ""
