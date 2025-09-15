import sqlite3

from tdd_core.domain.entities.task import Task
from tdd_core.infrastructure.repositories import TaskRepository


def _setup_tasks_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS framework_projects (
            id INTEGER PRIMARY KEY
        );
        INSERT INTO framework_projects (id) VALUES (1);

        CREATE TABLE IF NOT EXISTS framework_epics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            epic_key TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending'
        );
        INSERT INTO framework_epics (project_id, epic_key, name, description) VALUES (1, 'EP-000', 'Root', 'Root epic');

        CREATE TABLE IF NOT EXISTS framework_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_key TEXT NOT NULL,
            epic_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            tdd_phase TEXT,
            status TEXT DEFAULT 'todo',
            estimate_minutes INTEGER,
            actual_minutes INTEGER,
            story_points INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (epic_id) REFERENCES framework_epics(id) ON DELETE CASCADE
        );
        """
    )


def test_task_repository_round_trip():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    _setup_tasks_schema(conn)

    repo = TaskRepository(conn)

    task = Task(
        epic_id=1,
        key="TASK-100",
        name="Write tests",
        description="Write tests for task repository",
        tdd_status="red",
        estimated_duration=90,
        story_points=3,
    )

    created = repo.create(task)
    print("[CREATE] Task criada:", created.id, created.key, created.name)
    assert created.id is not None
    assert created.key == task.key
    assert created.tdd_status == "red"
    assert created.estimated_duration == 90

    created.tdd_status = "green"
    created.actual_duration = 80
    updated = repo.update(created)
    print("[UPDATE] Task atualizada:", updated.id, updated.tdd_status, updated.actual_duration)
    assert updated.tdd_status == "green"
    assert updated.actual_duration == 80

    fetched = repo.get_by_id(updated.id)
    print("[FETCH] Task carregada:", fetched.id, fetched.key, fetched.tdd_status)
    assert fetched is not None and fetched.key == task.key

    ok = repo.delete(updated.id)
    print("[DELETE] Remoção:", ok)
    assert ok is True
    assert repo.get_by_id(updated.id) is None

