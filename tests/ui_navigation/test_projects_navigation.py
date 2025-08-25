import pytest

from streamlit_extension.pages.projetos.actions import (
    create_new_project_draft,
    validate_project_name,
)

def test_validate_project_name_rejects_short_names():
    assert validate_project_name("") is False
    assert validate_project_name("  ") is False
    assert validate_project_name("ab") is False  # < 3 chars

def test_validate_project_name_accepts_ok():
    assert validate_project_name("Meu Projeto") is True

def test_create_new_project_redirects_and_returns_draft():
    draft, route = create_new_project_draft("Meu Projeto")
    assert route == "projeto_wizard"
    # estrutura mínima do draft
    assert draft["name"] == "Meu Projeto"
    assert draft["id"] is None
    assert draft["current_phase"] == "product_vision"
    # rascunho deve carregar os campos da primeira etapa do wizard
    assert draft["product_vision"] == {
        "vision_statement": "",
        "problem_statement": "",
        "target_audience": "",
        "value_proposition": "",
        "constraints": [],
    }

def test_create_new_project_raises_on_invalid_name():
    with pytest.raises(ValueError):
        create_new_project_draft("ab")
