from tdd_core.domain.entities.task import Task


def test_task_entity_creation_and_defaults():
    task = Task(
        epic_id=1,
        key="TASK-001",
        name="Write unit tests",
        description="Create unit tests for new feature",
    )

    print("[CREATE] Task criada com defaults")
    print(f"  - status default: {task.status}")
    print(f"  - tdd_status default: {task.tdd_status}")
    print(f"  - coverage default: {task.test_coverage}")
    print(f"  - TDAH defaults: focus={task.focus_rating}, energy={task.energy_level}, interruptions={task.interruption_count}")

    assert task.is_valid()
    assert task.status == "todo"
    assert task.tdd_status == "pending"
    assert task.test_coverage == 0.0


def test_task_validation_errors():
    task = Task(
        epic_id=0,  # inválido
        key=" ",   # inválido
        name=" ",  # inválido
        description=" ",  # inválido
        status="invalid",
        tdd_status="invalid",
        test_coverage=-10.0,
        tests_passing=5,
        tests_total=3,
        tests_failing=-1,
        focus_rating=0,
        energy_level="ultra",
        estimated_duration=-5,
        actual_duration=-1,
        priority=6,
        complexity=0,
        story_points=0,
    )

    errors = task.validate()
    print("[VALIDATE] Erros de validação esperados:")
    for e in errors:
        print(f"  - {e}")

    # Checagens principais
    assert "epic_id is required" in errors
    assert "key is required and cannot be empty" in errors
    assert "name is required and cannot be empty" in errors
    assert "description is required and cannot be empty" in errors
    assert "status must be one of" in " ".join(errors)
    assert "tdd_status must be one of" in " ".join(errors)
    assert "test_coverage must be between 0 and 100" in errors
    assert "tests_passing + tests_failing must be <= tests_total" in errors
    assert "tests_failing must be non-negative" in errors
    assert "focus_rating must be between 1 and 5" in errors
    assert "energy_level must be one of" in " ".join(errors)
    assert "estimated_duration must be non-negative" in errors
    assert "actual_duration must be non-negative" in errors
    assert "priority must be between 1 and 5" in errors
    assert "complexity must be between 1 and 5" in errors
    assert "story_points must be > 0 when provided" in errors


def test_task_tdd_helpers_and_efficiency():
    task = Task(
        epic_id=2,
        key="TASK-002",
        name="Refactor code",
        description="Refactor module for clarity",
        tdd_status="refactor",
        test_coverage=85.0,
        estimated_duration=60,
        actual_duration=30,
    )

    print("[HELPERS] Checando TDD e eficiência")
    print(f"  - is_tdd_complete: {task.is_tdd_complete()}")
    print(f"  - efficiency: {task.calculate_efficiency()}")
    assert task.is_tdd_complete() is True
    assert task.calculate_efficiency() == 200.0

    task.mark_interrupted()
    print(f"  - interruptions após mark: {task.interruption_count}")
    assert task.interruption_count == 1

