from tdd_core.domain.entities.epic import Epic


def test_epic_entity_creation_and_defaults():
    epic = Epic(
        project_id=1,
        key="EP-001",
        name="Backend Infrastructure",
        description="Setup backend foundation",
        business_value=8,
        risk_mitigation=6,
        strategic_alignment=7,
        effort_estimate=10,
    )

    print("[CREATE] Epic criado com valores básicos e defaults")
    print(f"  - status default: {epic.status}")
    print(f"  - tdd_phase default: {epic.tdd_phase}")
    print(f"  - epic_dependencies default: {epic.epic_dependencies}")
    print(f"  - AI defaults: generated={epic.ai_generated}, confidence={epic.ai_confidence}")

    assert epic.is_valid()
    assert epic.status == "pending"
    assert epic.tdd_phase == "analysis"
    assert isinstance(epic.epic_dependencies, list) and len(epic.epic_dependencies) == 0
    assert epic.ai_generated is False and epic.ai_confidence == 0.0


def test_epic_validation_ranges_and_tdd_phase():
    epic = Epic(
        project_id=0,  # inválido
        key=" ",       # inválido
        name=" ",      # inválido
        description="x",
        ai_confidence=1.5,      # inválido
        complexity_score=6.0,   # inválido
        effort_estimate=0,      # inválido
        tdd_phase="invalid",    # inválido
    )
    errors = epic.validate()

    print("[VALIDATE] Erros de validação esperados:")
    for e in errors:
        print(f"  - {e}")

    assert "project_id is required" in errors
    assert "key is required and cannot be empty" in errors
    assert "name is required and cannot be empty" in errors
    assert "ai_confidence must be between 0.0 and 1.0" in errors
    assert "complexity_score must be between 1.0 and 5.0" in errors
    assert "effort_estimate must be greater than zero" in errors
    assert "tdd_phase must be one of" in " ".join(errors)


def test_epic_ai_flags_and_dependencies_helpers():
    epic = Epic(
        project_id=2,
        key="EP-002",
        name="API Layer",
        description="Build REST API",
        ai_generated=True,
        ai_confidence=0.9,
        effort_estimate=3,
    )

    epic.epic_dependencies.extend(["EP-001", "EP-000"])

    print("[FLAGS] Checando helpers de IA e dependências")
    print(f"  - is_ai_generated: {epic.is_ai_generated()}")
    print(f"  - is_high_confidence: {epic.is_high_confidence()}")
    print(f"  - has_dependencies: {epic.has_dependencies()} -> {epic.epic_dependencies}")

    assert epic.is_ai_generated() is True
    assert epic.is_high_confidence() is True
    assert epic.has_dependencies() is True

