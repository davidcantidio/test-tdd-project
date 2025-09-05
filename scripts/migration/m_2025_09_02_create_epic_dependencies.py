# scripts/migration/m_2025_09_02_create_epic_dependencies.py
from __future__ import annotations
import sqlite3

try:
    from scripts.migration.migration_utility import register  # type: ignore
except Exception:
    def register(name, up, down):
        # shim para permitir import/execução em testes sem o utility real
        globals()["_MIGRATION_NAME"] = name
        globals()["_MIGRATION_UP"] = up
        globals()["_MIGRATION_DOWN"] = down

MIGRATION_NAME = "2025_09_02_create_framework_epic_dependencies"

def up(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON;")

    # 1) Tabela
    cur.execute("""
        CREATE TABLE IF NOT EXISTS framework_epic_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            epic_id INTEGER NOT NULL,
            depends_on_epic_id INTEGER NOT NULL,
            dep_type TEXT,
            rationale TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(project_id, epic_id, depends_on_epic_id),
            FOREIGN KEY (epic_id) REFERENCES framework_epics(id) ON DELETE CASCADE,
            FOREIGN KEY (depends_on_epic_id) REFERENCES framework_epics(id) ON DELETE CASCADE
        );
    """)

    # 2) Índices
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_epic_dep_project_epic
            ON framework_epic_dependencies (project_id, epic_id);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_epic_dep_project_depends_on
            ON framework_epic_dependencies (project_id, depends_on_epic_id);
    """)

    # 3) Triggers de integridade

    # Sem auto-dependência
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_epic_dep_no_self_insert
        BEFORE INSERT ON framework_epic_dependencies
        FOR EACH ROW
        WHEN NEW.epic_id = NEW.depends_on_epic_id
        BEGIN
            SELECT RAISE(ABORT, 'Epic dependency cannot reference itself');
        END;
    """)
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_epic_dep_no_self_update
        BEFORE UPDATE OF epic_id, depends_on_epic_id ON framework_epic_dependencies
        FOR EACH ROW
        WHEN NEW.epic_id = NEW.depends_on_epic_id
        BEGIN
            SELECT RAISE(ABORT, 'Epic dependency cannot reference itself');
        END;
    """)

    # project_id do registro deve bater com o project_id dos dois épicos
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_epic_dep_project_match_insert
        BEFORE INSERT ON framework_epic_dependencies
        FOR EACH ROW
        BEGIN
            -- épico deve existir e pertencer ao project_id informado
            SELECT CASE
                WHEN (SELECT project_id FROM framework_epics WHERE id = NEW.epic_id) IS NULL
                THEN RAISE(ABORT, 'Epic not found for epic_id')
            END;
            SELECT CASE
                WHEN (SELECT project_id FROM framework_epics WHERE id = NEW.depends_on_epic_id) IS NULL
                THEN RAISE(ABORT, 'Epic not found for depends_on_epic_id')
            END;
            SELECT CASE
                WHEN (SELECT project_id FROM framework_epics WHERE id = NEW.epic_id) != NEW.project_id
                THEN RAISE(ABORT, 'project_id mismatch for epic_id')
            END;
            SELECT CASE
                WHEN (SELECT project_id FROM framework_epics WHERE id = NEW.depends_on_epic_id) != NEW.project_id
                THEN RAISE(ABORT, 'project_id mismatch for depends_on_epic_id')
            END;
        END;
    """)

    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_epic_dep_project_match_update
        BEFORE UPDATE OF project_id, epic_id, depends_on_epic_id ON framework_epic_dependencies
        FOR EACH ROW
        BEGIN
            SELECT CASE
                WHEN (SELECT project_id FROM framework_epics WHERE id = NEW.epic_id) IS NULL
                THEN RAISE(ABORT, 'Epic not found for epic_id')
            END;
            SELECT CASE
                WHEN (SELECT project_id FROM framework_epics WHERE id = NEW.depends_on_epic_id) IS NULL
                THEN RAISE(ABORT, 'Epic not found for depends_on_epic_id')
            END;
            SELECT CASE
                WHEN (SELECT project_id FROM framework_epics WHERE id = NEW.epic_id) != NEW.project_id
                THEN RAISE(ABORT, 'project_id mismatch for epic_id')
            END;
            SELECT CASE
                WHEN (SELECT project_id FROM framework_epics WHERE id = NEW.depends_on_epic_id) != NEW.project_id
                THEN RAISE(ABORT, 'project_id mismatch for depends_on_epic_id')
            END;
        END;
    """)

    conn.commit()

def down(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DROP TRIGGER IF EXISTS trg_epic_dep_no_self_insert;")
    cur.execute("DROP TRIGGER IF EXISTS trg_epic_dep_no_self_update;")
    cur.execute("DROP TRIGGER IF EXISTS trg_epic_dep_project_match_insert;")
    cur.execute("DROP TRIGGER IF EXISTS trg_epic_dep_project_match_update;")
    cur.execute("DROP INDEX IF EXISTS idx_epic_dep_project_epic;")
    cur.execute("DROP INDEX IF EXISTS idx_epic_dep_project_depends_on;")
    cur.execute("DROP TABLE IF EXISTS framework_epic_dependencies;")
    conn.commit()

register(MIGRATION_NAME, up, down)
