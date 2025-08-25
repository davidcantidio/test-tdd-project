import pytest
from unittest.mock import MagicMock
from streamlit_extension.pages.projetos.controllers.product_vision_controller import ProductVisionController
from streamlit_extension.pages.projetos.repositories.product_vision_repository import InMemoryProductVisionRepository

@pytest.fixture
def repo():
    return InMemoryProductVisionRepository()

@pytest.fixture
def fake_service():
    return MagicMock()

@pytest.fixture
def controller(repo, fake_service):
    return ProductVisionController(refine_service=fake_service, repository=repo)

def test_refine_with_ai_validates_and_calls_service(controller, fake_service):
    payload = {
        "vision_statement": "Visão",
        "problem_statement": "Problema",
        "target_audience": "Usuários",
        "value_proposition": "Proposta",
        "constraints": ["limite de tempo"]
    }
    refined = {**payload, "vision_statement": "Visão refinada"}
    fake_service.refine.return_value = refined

    result = controller.refine_with_ai(payload)

    fake_service.refine.assert_called_once_with(payload)
    assert result["vision_statement"] == "Visão refinada"

def test_refine_with_ai_propagates_valueerror(controller, fake_service):
    payload = {
        "vision_statement": "",
        "problem_statement": "Problema",
        "target_audience": "Usuários",
        "value_proposition": "Proposta",
        "constraints": ["limite de tempo"]
    }
    fake_service.refine.side_effect = ValueError("Erro de IA")

    with pytest.raises(ValueError):
        controller.refine_with_ai(payload)

def test_save_draft_refuses_on_missing_fields(controller):
    invalid = {
        "vision_statement": "",
        "problem_statement": "",
        "target_audience": "",
        "value_proposition": "",
        "constraints": []
    }
    ok, msg = controller.save_draft("p1", invalid)
    assert not ok
    assert "ausentes" in msg

def test_save_draft_calls_repository_on_valid(controller, repo):
    valid = {
        "vision_statement": "Visão",
        "problem_statement": "Problema",
        "target_audience": "Usuários",
        "value_proposition": "Proposta",
        "constraints": ["LGPD"]
    }
    ok, msg = controller.save_draft("p1", valid)
    assert ok
    saved = repo.load("p1")
    assert saved["vision_statement"] == "Visão"
