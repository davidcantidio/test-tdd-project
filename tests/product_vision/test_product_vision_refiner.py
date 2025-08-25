import pytest
from src.ai.product_vision_refiner import FakeClaudeRefiner, ProductVisionDTO

def test_refiner_requires_all_fields_present():
    """A IA só deve aceitar rodar se TODOS os campos da visão forem preenchidos."""

    refiner = FakeClaudeRefiner()

    # Caso com campo vazio → deve falhar
    incomplete = {
        "product_name": "App Cursos",
        "target_user": "",
        "problem": "Dificuldade em vender cursos",
        "outcome": "Ajudar professores",
        "constraints": ["Compatível com LGPD"]
    }
    with pytest.raises(ValueError):
        refiner.refine(incomplete)

def test_refiner_runs_when_all_fields_filled():
    """Quando todos os campos são preenchidos, deve retornar ProductVisionDTO válido."""

    refiner = FakeClaudeRefiner()

    complete = {
        "product_name": "Plataforma Financeira",
        "target_user": "jovens adultos",
        "problem": "falta de controle de gastos pessoais",
        "outcome": "ajudar usuários a economizar dinheiro",
        "constraints": ["deve funcionar em mobile"]
    }

    result: ProductVisionDTO = refiner.refine(complete)

    assert isinstance(result, ProductVisionDTO)
    # Todos os campos continuam preenchidos
    assert result.product_name != ""
    assert result.target_user != ""
    assert result.problem != ""
    assert result.outcome != ""
    assert isinstance(result.constraints, list) and len(result.constraints) > 0
