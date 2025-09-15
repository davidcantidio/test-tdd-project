import sqlite3

from tdd_core.domain.entities.user_story import UserStory
from tdd_core.infrastructure.repositories import UserStoryRepository


def _setup_user_stories_schema(conn: sqlite3.Connection) -> None:
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
        INSERT INTO framework_epics (project_id, epic_key, name, description) VALUES (1, 'EP-ROOT', 'Root', 'Root Epic');

        CREATE TABLE IF NOT EXISTS framework_user_stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epic_id INTEGER NOT NULL,
            story_key TEXT NOT NULL,
            title TEXT NOT NULL,
            user_story TEXT NOT NULL,
            acceptance_criteria TEXT NOT NULL,
            status TEXT DEFAULT 'backlog',
            workflow_stage TEXT DEFAULT 'discovery',
            story_points INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (epic_id) REFERENCES framework_epics(id) ON DELETE CASCADE
        );
        """
    )


def test_user_story_repository_round_trip():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    _setup_user_stories_schema(conn)

    repo = UserStoryRepository(conn)

    us = UserStory(
        epic_id=1,
        key="US-100",
        title="Como usuário, quero resetar senha",
        narrative="Como usuário, quero recuperar minha senha esquecida",
        acceptance_criteria=["Link enviado por email", "Token expira em 15 minutos"],
        story_points=5,
        status="backlog",
        workflow_stage="analysis",
        description="Fluxo de recuperação via email",
    )

    created = repo.create(us)
    print("[CREATE] UserStory criada:", created.id, created.key, created.title)
    assert created.id is not None
    assert created.key == us.key
    assert created.acceptance_criteria == us.acceptance_criteria

    created.workflow_stage = "ready"
    created.story_points = 8
    updated = repo.update(created)
    print("[UPDATE] UserStory atualizada:", updated.id, updated.workflow_stage, updated.story_points)
    assert updated.workflow_stage == "ready"
    assert updated.story_points == 8

    fetched = repo.get_by_id(updated.id)
    print("[FETCH] UserStory carregada:", fetched.id, fetched.key)
    assert fetched is not None and fetched.key == us.key

    ok = repo.delete(updated.id)
    print("[DELETE] Remoção:", ok)
    assert ok is True
    assert repo.get_by_id(updated.id) is None

