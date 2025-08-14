import sqlite3
import pytest


@pytest.fixture()
def hierarchy_db():
    """Create an in-memory database with hierarchy tables and seed data."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(
        """
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            name TEXT
        );
        CREATE TABLE framework_epics (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            epic_key TEXT UNIQUE,
            name TEXT
        );
        CREATE TABLE framework_tasks (
            id INTEGER PRIMARY KEY,
            epic_id INTEGER NOT NULL REFERENCES framework_epics(id) ON DELETE CASCADE,
            task_key TEXT UNIQUE,
            title TEXT
        );
        """
    )
    conn.execute("INSERT INTO clients (name) VALUES ('Client A')")
    client_id = conn.execute("SELECT id FROM clients").fetchone()[0]
    conn.execute("INSERT INTO projects (client_id, name) VALUES (?, 'Project A')", (client_id,))
    project_id = conn.execute("SELECT id FROM projects").fetchone()[0]
    conn.execute(
        "INSERT INTO framework_epics (project_id, epic_key, name) VALUES (?, 'EPIC-1', 'Epic 1')",
        (project_id,),
    )
    epic_id = conn.execute("SELECT id FROM framework_epics").fetchone()[0]
    conn.execute(
        "INSERT INTO framework_tasks (epic_id, task_key, title) VALUES (?, 'TASK-1', 'Task 1')",
        (epic_id,),
    )
    conn.commit()
    yield conn
    conn.close()


def test_cascade_delete_project_removes_epics_and_tasks(hierarchy_db):
    conn = hierarchy_db
    conn.execute("DELETE FROM projects")
    conn.commit()
    epic_count = conn.execute("SELECT COUNT(*) FROM framework_epics").fetchone()[0]
    task_count = conn.execute("SELECT COUNT(*) FROM framework_tasks").fetchone()[0]
    assert epic_count == 0
    assert task_count == 0


def test_task_invalid_epic_rejected(hierarchy_db):
    conn = hierarchy_db
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO framework_tasks (epic_id, task_key, title) VALUES (?, 'TASK-2', 'Invalid Task')",
            (999,),
        )
        conn.commit()
