# tests/migrations/test_2025_09_02_epic_dependencies_GREEN.py
"""
A1. [DB] GREEN - Tabela de dependencias de epicos

Depois de aplicar a migration:
  - Tabela existe e aceita insercao valida
  - Auto-dependencia falha (IntegrityError)
  - Cross-project falha (IntegrityError)
  - Duplicidade (UNIQUE) falha (IntegrityError)
  - FKs invalidas falham (IntegrityError)
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
import importlib.util, sys
import pytest

def load_migration_module(path: Path):
    spec = importlib.util.spec_from_file_location("mig_mod", str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["mig_mod"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore
    return mod

def make_conn(tmp_path: Path) -> sqlite3.Connection:
    db = tmp_path / "deps_green.db"
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.executescript(
        """
        CREATE TABLE framework_epics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            epic_key TEXT,
            name TEXT,
            priority INTEGER,
            created_at TEXT
        );
        -- Seed: project 1 -> epics 1,2 ; project 2 -> epic 3
        INSERT INTO framework_epics (project_id, epic_key, name) VALUES (1, 'E1', 'Epic 1'); -- id=1
        INSERT INTO framework_epics (project_id, epic_key, name) VALUES (1, 'E2', 'Epic 2'); -- id=2
        INSERT INTO framework_epics (project_id, epic_key, name) VALUES (2, 'E3', 'Epic 3'); -- id=3
        """
    )
    conn.commit()
    return conn

def test_dependencies_constraints(tmp_path: Path):
    conn = make_conn(tmp_path)
    try:
        # Apply migration
        mig_path = Path(__file__).parents[2] / "scripts" / "migration" / "m_2025_09_02_create_epic_dependencies.py"
        mod = load_migration_module(mig_path)
        mod.up(conn)

        # 1) Insert valid dependency (same project, different epics)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO framework_epic_dependencies (project_id, epic_id, depends_on_epic_id, dep_type) VALUES (1, 1, 2, 'blocks')"
        )
        conn.commit()

        # 2) Duplicate (UNIQUE) must fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO framework_epic_dependencies (project_id, epic_id, depends_on_epic_id, dep_type) VALUES (1, 1, 2, 'blocks')"
            )
            conn.commit()

        # 3) Self-dependency must fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO framework_epic_dependencies (project_id, epic_id, depends_on_epic_id) VALUES (1, 1, 1)"
            )
            conn.commit()

        # 4) Cross-project mismatch must fail
        # epic 1 (project 1) depends on epic 3 (project 2) but project_id=1 => mismatch
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO framework_epic_dependencies (project_id, epic_id, depends_on_epic_id) VALUES (1, 1, 3)"
            )
            conn.commit()

        # 5) FK invalid epic_id must fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO framework_epic_dependencies (project_id, epic_id, depends_on_epic_id) VALUES (1, 999, 2)"
            )
            conn.commit()

        # 6) FK invalid depends_on_epic_id must fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO framework_epic_dependencies (project_id, epic_id, depends_on_epic_id) VALUES (1, 1, 999)"
            )
            conn.commit()

        # Sanity: tabela ficou só com a dependência válida
        rows = conn.execute(
            "SELECT project_id, epic_id, depends_on_epic_id, dep_type FROM framework_epic_dependencies"
        ).fetchall()
        assert rows == [(1, 1, 2, 'blocks')]

    finally:
        conn.close()
