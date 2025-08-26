import pytest
from unittest.mock import MagicMock

from streamlit_extension.pages.projetos.controllers.product_vision_controller import (
    ProductVisionController,
)
from streamlit_extension.pages.projetos.repositories.product_vision_repository import (
    InMemoryProductVisionRepository,
)


@pytest.fixture
def repo():
    return InMemoryProductVisionRepository()


@pytest.fixture
def service():
    # não usado por save_draft, mas o controller exige no __init__
    return MagicMock()


@pytest.fixture
def controller(repo, service):
    return ProductVisionController(refine_service=service, repository=repo)


def _valid_payload(**overrides):
    base = {
        "vision_statement": "Nossa visão é X",
        "problem_statement": "Usuários não conseguem Y",
        "target_audience": "PMEs digitais",
        "value_proposition": "Automatizar Z com baixo custo",
        "constraints": ["LGPD", "lançar em 90 dias"],
    }
    base.update(overrides)
    return base


# 1) Recusa salvar quando payload inválido
@pytest.mark.parametrize(
    "bad_payload",
    [
        _valid_payload(vision_statement=""),
        _valid_payload(problem_statement="  "),
        _valid_payload(target_audience=""),
        _valid_payload(value_proposition=""),
        _valid_payload(constraints=[]),
        _valid_payload(constraints=["   "]),
    ],
)
def test_save_draft_rejects_invalid_payload(controller, repo, bad_payload):
    ok, msg = controller.save_draft("proj-123", bad_payload)
    assert ok is False
    assert isinstance(msg, str) and msg  # mensagem amigável
    # garante que nada foi salvo no repo
    assert repo.load("proj-123") == {}


# 2) Caso feliz: salva com payload válido
def test_save_draft_saves_valid_payload(controller, repo):
    payload = _valid_payload()
    ok, msg = controller.save_draft("proj-123", payload)
    assert ok is True
    assert msg is None or msg == ""

    saved = repo.load("proj-123")
    # confere que os campos chegaram corretos
    assert saved.get("vision_statement") == payload["vision_statement"]
    assert saved.get("problem_statement") == payload["problem_statement"]
    assert saved.get("target_audience") == payload["target_audience"]
    assert saved.get("value_proposition") == payload["value_proposition"]
    assert saved.get("constraints") == payload["constraints"]
