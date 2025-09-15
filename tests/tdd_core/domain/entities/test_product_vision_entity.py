from datetime import datetime

from tdd_core.domain.entities.product_vision import ProductVision


def _valid_pv(**overrides):
    base = dict(
        name="TDD Framework",
        vision_statement="Revolucionar desenvolvimento com TDD",
        target_user="Desenvolvedores",
        user_problem="Complexidade em testes",
        expected_benefits="Qualidade e produtividade",
        product_description="Framework completo TDD",
        success_metrics="98% cobertura, zero bugs",
        tech_requirements="Python 3.11+, SQLite",
        non_functional_requirements="Performance <1ms",
        compliance_requirements="GDPR, SOC2",
        risks="Curva de aprendizado",
        assumptions="Equipe experiente",
        must_have="Persistência explícita sem JSON genérico",
        cannot_have="Campos sem semântica",
        deliverables="API, CLI, Web",
        market_opportunity="10M desenvolvedores",
    )
    base.update(overrides)
    return ProductVision(**base)


def test_product_vision_creation_and_timestamps():
    pv = _valid_pv()
    print("[CREATE] ProductVision criado com campos obrigatórios")
    print(f"  - name: {pv.name}")
    print(f"  - must_have: {pv.must_have}")
    print(f"  - cannot_have: {pv.cannot_have}")
    print(f"  - created_at: {pv.created_at}")
    print(f"  - updated_at: {pv.updated_at}")

    assert pv.is_valid()
    assert isinstance(pv.created_at, datetime)
    assert isinstance(pv.updated_at, datetime)


def test_product_vision_validation_missing_fields():
    pv = _valid_pv(name=" ", must_have=" ", cannot_have=" ")
    errors = pv.validate()
    print("[VALIDATE] Erros esperados (campos vazios):")
    for e in errors:
        print("  -", e)

    assert "name is required and cannot be empty" in errors
    assert "must_have is required and cannot be empty" in errors
    assert "cannot_have is required and cannot be empty" in errors
    assert pv.is_valid() is False


def test_product_vision_validation_invalid_types():
    # must_have/cannot_have devem ser strings; aqui passamos tipos inválidos
    pv = _valid_pv(must_have=["A", "B"], cannot_have=123)
    errors = pv.validate()
    print("[VALIDATE] Erros esperados (tipos inválidos):")
    for e in errors:
        print("  -", e)

    assert "must_have has invalid type:" in " ".join(errors)
    assert "cannot_have has invalid type:" in " ".join(errors)
    assert pv.is_valid() is False

