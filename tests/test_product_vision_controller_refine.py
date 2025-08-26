import pytest
from unittest.mock import MagicMock

# Imports do controller e (opcional) do repositório in-memory
from streamlit_extension.pages.projetos.controllers.product_vision_controller import (
    ProductVisionController,
)
from streamlit_extension.pages.projetos.repositories.product_vision_repository import (
    InMemoryProductVisionRepository,
)


@pytest.fixture
def repo():
    # Repositório não é usado em refine_with_ai, mas o controller exige no __init__
    return InMemoryProductVisionRepository()


@pytest.fixture
def service():
    # Serviço de IA será mockado em cada teste
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


# -----------------------------
# 1) NÃO CHAMA IA QUANDO INVÁLIDO
# -----------------------------
@pytest.mark.parametrize(
    "bad_payload",
    [
        _valid_payload(vision_statement=""),    # vazio
        _valid_payload(constraints=[]),         # lista vazia
        _valid_payload(constraints=["   "]),    # só espaços
    ],
)
def test_refine_with_ai_raises_valueerror_when_payload_incomplete(controller, service, bad_payload):
    with pytest.raises(ValueError):
        controller.refine_with_ai(bad_payload)
    # garante que o serviço NÃO foi chamado quando inválido
    service.refine.assert_not_called()


# -----------------------------
# 2) CASO FELIZ (HAPPY PATH)
# -----------------------------
def test_refine_with_ai_calls_service_and_returns_merged_result(controller, service):
    payload = _valid_payload()
    # serviço retorna refinamento parcial (apenas vision_statement)
    service.refine.return_value = {
        "vision_statement": "Visão refinada e clara",
        # demais campos omitidos intencionalmente para testar merge
    }

    result = controller.refine_with_ai(payload)

    # 2a) foi chamado UMA vez com as chaves corretas (normalizadas)
    service.refine.assert_called_once()
    called_args, called_kwargs = service.refine.call_args
    assert called_kwargs == {}  # não usamos kwargs
    assert len(called_args) == 1
    called_payload = called_args[0]

    # chaves esperadas
    expected_keys = {
        "vision_statement",
        "problem_statement",
        "target_audience",
        "value_proposition",
        "constraints",
    }
    assert set(called_payload.keys()) == expected_keys

    # valores devem refletir o payload normalizado (stripped) e constraints como lista
    assert called_payload["vision_statement"] == payload["vision_statement"].strip()
    assert called_payload["problem_statement"] == payload["problem_statement"].strip()
    assert called_payload["target_audience"] == payload["target_audience"].strip()
    assert called_payload["value_proposition"] == payload["value_proposition"].strip()
    assert isinstance(called_payload["constraints"], list)
    assert called_payload["constraints"] == payload["constraints"]

    # 2b) retorno deve ser o MERGE: apenas vision_statement atualizado; resto igual ao original
    assert result["vision_statement"] == "Visão refinada e clara"
    assert result["problem_statement"] == payload["problem_statement"]
    assert result["target_audience"] == payload["target_audience"]
    assert result["value_proposition"] == payload["value_proposition"]
    assert result["constraints"] == payload["constraints"]
