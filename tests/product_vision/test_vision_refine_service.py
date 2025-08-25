import pytest

# Serviço alvo — vamos garantir injeção de dependência para não chamar rede:
from src.ia.services.vision_refine_service import VisionRefineService

REQUIRED_KEYS = {
    "vision_statement",
    "problem_statement",
    "target_audience",
    "value_proposition",
    "constraints",
}


def _pv_ok():
    return {
        "vision_statement": "V",
        "problem_statement": "P",
        "target_audience": "T",
        "value_proposition": "VP",
        "constraints": ["c1"],
    }


class FakeAgentOK:
    def __init__(self):
        self.last_payload = None

    def run(self, payload: dict) -> dict:
        # captura o payload enviado pelo service
        self.last_payload = payload
        # retorna todos os campos válidos
        return {
            "vision_statement": "V refinado",
            "problem_statement": "P refinado",
            "target_audience": "T refinado",
            "value_proposition": "VP refinado",
            "constraints": ["regulatório", "prazo 90 dias"],
        }


class FakeAgentMissingField:
    def run(self, payload: dict) -> dict:
        # falta 'constraints' -> deve disparar erro de validação
        return {
            "vision_statement": "V",
            "problem_statement": "P",
            "target_audience": "T",
            "value_proposition": "VP",
            # "constraints" ausente
        }


class FakeAgentBadConstraints:
    def run(self, payload: dict) -> dict:
        # retorna constraints como string; service deve normalizar para lista
        return {
            "vision_statement": "V",
            "problem_statement": "P",
            "target_audience": "T",
            "value_proposition": "VP",
            "constraints": "LGPD\n90 dias\n",
        }


def test_service_returns_required_keys_and_list_constraints():
    agent = FakeAgentOK()
    svc = VisionRefineService(agent=agent)
    out = svc.refine(_pv_ok())
    assert set(out.keys()) == REQUIRED_KEYS
    assert isinstance(out["constraints"], list)
    assert all(isinstance(x, str) for x in out["constraints"])
    # garante que um payload foi passado ao agente
    assert agent.last_payload is not None
    assert set(agent.last_payload.keys()) == REQUIRED_KEYS


def test_service_raises_on_missing_required_key():
    agent = FakeAgentMissingField()
    svc = VisionRefineService(agent=agent)
    with pytest.raises(ValueError):
        svc.refine(_pv_ok())


def test_service_normalizes_string_constraints_to_list():
    agent = FakeAgentBadConstraints()
    svc = VisionRefineService(agent=agent)
    out = svc.refine(_pv_ok())
    assert isinstance(out["constraints"], list)
    assert out["constraints"] == ["LGPD", "90 dias"]
