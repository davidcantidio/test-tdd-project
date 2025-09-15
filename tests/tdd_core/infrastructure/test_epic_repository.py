import sqlite3

from tdd_core.domain.entities.epic import Epic
from tdd_core.infrastructure.repositories import EpicRepository


def _setup_epics_schema(conn: sqlite3.Connection) -> None:
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
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 3,
            ai_generated INTEGER DEFAULT 0,
            ai_confidence REAL DEFAULT 0.0,
            complexity_score REAL DEFAULT 3.0,
            effort_estimate INTEGER DEFAULT 5,
            sort_order INTEGER DEFAULT 0,
            unblock_potential INTEGER DEFAULT 0,
            critical_path_weight REAL DEFAULT 0.0,
            tdd_phase TEXT DEFAULT 'analysis',
            tdd_order INTEGER DEFAULT 1,
            business_value INTEGER DEFAULT 5,
            risk_mitigation INTEGER DEFAULT 5,
            strategic_alignment INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP NULL,
            completed_at TIMESTAMP NULL,
            FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS framework_epic_dependencies (
            epic_id INTEGER,
            depends_on_key TEXT
        );
        """
    )


def test_epic_repository_round_trip():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    _setup_epics_schema(conn)

    repo = EpicRepository(conn)

    epic = Epic(
        project_id=1,
        key="EP-100",
        name="Order Management",
        description="Implement order processing",
        ai_generated=True,
        ai_confidence=0.85,
        complexity_score=2.5,
        effort_estimate=8,
        tdd_phase="red",
        tdd_order=2,
        business_value=9,
        risk_mitigation=4,
        strategic_alignment=7,
    )
    epic.epic_dependencies = ["EP-001", "EP-050"]

    created = repo.create(epic)
    print("[CREATE] Epic criado:", created.id, created.key, created.epic_dependencies)
    assert created.id is not None
    assert created.key == epic.key
    assert created.is_ai_generated() is True
    assert created.has_dependencies() is True

    # Update
    created.ai_confidence = 0.9
    created.sort_order = 3
    created.epic_dependencies.append("EP-051")

    updated = repo.update(created)
    print("[UPDATE] Epic atualizado:", updated.id, updated.ai_confidence, updated.sort_order, updated.epic_dependencies)
    assert updated.ai_confidence == 0.9
    assert updated.sort_order == 3
    assert "EP-051" in updated.epic_dependencies

    fetched = repo.get_by_id(updated.id)
    print("[FETCH] Epic carregado:", fetched.id, fetched.key)
    assert fetched is not None and fetched.key == epic.key

    ok = repo.delete(updated.id)
    print("[DELETE] Remoção:", ok)
    assert ok is True
    assert repo.get_by_id(updated.id) is None

