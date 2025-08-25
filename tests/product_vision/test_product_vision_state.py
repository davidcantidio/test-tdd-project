import pytest
from streamlit_extension.pages.projetos.domain.product_vision_state import (
    DEFAULT_PV,
    all_fields_filled,
    normalize_constraints,
    validate_product_vision,
    apply_refine_result,
    refine_all_and_apply,
)

class FakeRefinerOK:
    def refine(self, payload: dict) -> dict:
        # retorna todos os campos preenchidos e lapidados
        return {
            "vision_statement": (payload.get("vision_statement","") + " (refinado)").strip(),
            "problem_statement": (payload.get("problem_statement","") + " (refinado)").strip(),
            "target_audience": (payload.get("target_audience","") + " (refinado)").strip(),
            "value_proposition": (payload.get("value_proposition","") + " (refinado)").strip(),
            "constraints": ["prazo de 90 dias", "orçamento limitado"],
        }

class FakeRefinerPartial:
    def refine(self, payload: dict) -> dict:
        # retorna só 1 campo, garante que merge não apaga os outros
        return {
            "vision_statement": "Visão lapidada",
        }

def _pv(**over):
    base = {**DEFAULT_PV}
    base.update(over)
    return base

def test_default_shape():
    assert set(DEFAULT_PV.keys()) == {
        "vision_statement","problem_statement","target_audience","value_proposition","constraints"
    }
    assert isinstance(DEFAULT_PV["constraints"], list)

@pytest.mark.parametrize("pv,ok", [
    (_pv(vision_statement="", problem_statement="x", target_audience="y", value_proposition="z", constraints=["c"]), False),
    (_pv(vision_statement="x", problem_statement="", target_audience="y", value_proposition="z", constraints=["c"]), False),
    (_pv(vision_statement="x", problem_statement="y", target_audience="", value_proposition="z", constraints=["c"]), False),
    (_pv(vision_statement="x", problem_statement="y", target_audience="z", value_proposition="", constraints=["c"]), False),
    (_pv(vision_statement="x", problem_statement="y", target_audience="z", value_proposition="w", constraints=[]), False),
    (_pv(vision_statement="x", problem_statement="y", target_audience="z", value_proposition="w", constraints=["c"]), True),
])
def test_all_fields_filled(pv, ok):
    assert all_fields_filled(pv) == ok

def test_normalize_constraints_strips_and_removes_empty():
    raw = ["  A  ", "", "B", "   ", "C  "]
    assert normalize_constraints(raw) == ["A", "B", "C"]

def test_validate_product_vision_messages():
    ok, msg = validate_product_vision(_pv(
        vision_statement="", problem_statement="a", target_audience="b", value_proposition="c", constraints=["d"]
    ))
    assert ok is False and "vision_statement" in msg

    ok2, msg2 = validate_product_vision(_pv(
        vision_statement="a", problem_statement="b", target_audience="c", value_proposition="d", constraints=[]
    ))
    assert ok2 is False and "constraints" in msg2

    ok3, msg3 = validate_product_vision(_pv(
        vision_statement="a", problem_statement="b", target_audience="c", value_proposition="d", constraints=["x"]
    ))
    assert ok3 is True and msg3 is None

def test_apply_refine_result_merges_without_erasing():
    pv = _pv(
        vision_statement="Visão atual",
        problem_statement="Problema atual",
        target_audience="Público atual",
        value_proposition="Valor atual",
        constraints=["atual 1"]
    )
    res = {"vision_statement": "Visão lapidada"}  # parcial
    merged = apply_refine_result(pv, res)
    assert merged["vision_statement"] == "Visão lapidada"
    # não deve apagar os demais
    assert merged["problem_statement"] == "Problema atual"
    assert merged["constraints"] == ["atual 1"]

def test_refine_all_and_apply_uses_service_and_normalizes_constraints():
    pv = _pv(
        vision_statement="V1",
        problem_statement="P1",
        target_audience="T1",
        value_proposition="VP1",
        constraints=[" c1 ", "c2", ""]
    )
    merged = refine_all_and_apply(pv, FakeRefinerOK())
    assert merged["vision_statement"].endswith("(refinado)")
    assert merged["problem_statement"].endswith("(refinado)")
    assert merged["target_audience"].endswith("(refinado)")
    assert merged["value_proposition"].endswith("(refinado)")
    # normalizado e substituído pelo retorno do serviço
    assert merged["constraints"] == ["prazo de 90 dias", "orçamento limitado"]

def test_refine_all_and_apply_handles_partial_service_response():
    pv = _pv(
        vision_statement="V1",
        problem_statement="P1",
        target_audience="T1",
        value_proposition="VP1",
        constraints=["c1"]
    )
    merged = refine_all_and_apply(pv, FakeRefinerPartial())
    assert merged["vision_statement"] == "Visão lapidada"
    # não deve apagar os demais
    assert merged["problem_statement"] == "P1"
    assert merged["constraints"] == ["c1"]
