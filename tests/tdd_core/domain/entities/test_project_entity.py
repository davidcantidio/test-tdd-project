from tdd_core.domain.entities.project import Project


def test_project_entity_creation_and_defaults():
    project = Project(
        name="TDD Project",
        description="Enterprise TDD framework",
    )

    print("[CREATE] Project criado com defaults alinhados")
    print(f"  - status default: {project.status}")
    print(f"  - current_phase default: {project.current_phase}")
    print(f"  - phases_completed default: {project.phases_completed}")

    assert project.is_valid()
    assert project.status == "planning"
    assert project.current_phase == "roteiro"
    assert isinstance(project.phases_completed, list) and len(project.phases_completed) == 0


def test_project_validation_and_progress():
    project = Project(name="X", description="Y")
    project.total_tasks = 10
    project.completed_tasks = 4

    progress = project.calculate_progress()
    print("[PROGRESS] Progresso calculado:", progress)
    assert progress == 40.0

    project.progress_percentage = 120  # inválido
    errors = project.validate()
    print("[VALIDATE] Erros esperados:")
    for e in errors:
        print("  -", e)
    assert "progress_percentage must be between 0 and 100" in errors


def test_project_phases_and_completion_flag():
    project = Project(name="X", description="Y")
    project.mark_phase_complete("roteiro")
    project.mark_phase_complete("capitulos")

    print("[WIZARD] Fases completas:", project.phases_completed)
    assert project.phases_completed == ["roteiro", "capitulos"]

    print("[WIZARD] Flag wizard_completed (esperado False):", project.is_wizard_complete())
    assert project.is_wizard_complete() is False

