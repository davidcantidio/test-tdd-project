import pytest
from src.ia.product_vision_refiner import FakeClaudeRefiner
from src.ia.agents.agno_agent import ProductVisionDTO

def test_refiner_requires_all_fields_present():
    """A IA só deve aceitar rodar se TODOS os campos da visão forem preenchidos."""

    refiner = FakeClaudeRefiner()

    # Caso com campo vazio → deve falhar
    incomplete = {
        "vision_statement": "App Cursos",
        "target_audience": "",
        "problem_statement": "Dificuldade em vender cursos",
        "value_proposition": "Ajudar professores",
        "constraints": ["Compatível com LGPD"]
    }
    with pytest.raises(ValueError):
        refiner.refine(incomplete)

def test_refiner_runs_when_all_fields_filled():
    """Quando todos os campos são preenchidos, deve retornar ProductVisionDTO válido."""

    refiner = FakeClaudeRefiner()

    complete = {
        "vision_statement": "Plataforma Financeira",
        "target_audience": "jovens adultos",
        "problem_statement": "falta de controle de gastos pessoais",
        "value_proposition": "ajudar usuários a economizar dinheiro",
        "constraints": ["deve funcionar em mobile"]
    }

    result: ProductVisionDTO = refiner.refine(complete)

    assert isinstance(result, ProductVisionDTO)
    # Todos os campos continuam preenchidos
    assert result.vision_statement != ""
    assert result.target_audience != ""
    assert result.problem_statement != ""
    assert result.value_proposition != ""
    assert isinstance(result.constraints, list) and len(result.constraints) > 0
