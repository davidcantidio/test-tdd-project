# tests/repositories/test_epic_dependency_repository.py
from __future__ import annotations
import sqlite3
from pathlib import Path
import importlib.util, sys
import pytest

# Importa a classe do repositório (ajuste o caminho se você colocou em outro módulo)
from epic_service import EpicDependencyRepository


def load_migration_module(path: Path):
    spec = importlib.util.spec_from_file_location("mig_dep", str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["mig_dep"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def make_conn(tmp_path: Path) -> sqlite3.Connection:
    db = tmp_path / "repo_deps_green.db"
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
        -- Seed: projeto 1 -> (id=1, id=2); projeto 2 -> (id=3)
        INSERT INTO framework_epics (project_id, epic_key, name) VALUES (1, 'E1', 'Epic 1'); -- id=1
        INSERT INTO framework_epics (project_id, epic_key, name) VALUES (1, 'E2', 'Epic 2'); -- id=2
        INSERT INTO framework_epics (project_id, epic_key, name) VALUES (2, 'E3', 'Epic 3'); -- id=3
        """
    )
    conn.commit()
    return conn


def test_add_and_list_dependencies_happy_path(tmp_path: Path):
    conn = make_conn(tmp_path)
    # aplica migration de A1
    mig_path = Path(__file__).parents[2] / "scripts" / "migration" / "m_2025_09_02_create_epic_dependencies.py"
    mig = load_migration_module(mig_path)
    mig.up(conn)

    repo = EpicDependencyRepository(conn)
    # add válida: (proj 1) epic 1 depende de epic 2
    repo.add_dependency(project_id=1, epic_id=1, depends_on_epic_id=2, dep_type="blocks", rationale="exemplo")

    deps = repo.list_dependencies(project_id=1)
    assert len(deps) == 1
    d = deps[0]
    assert d["epic_id"] == 1
    assert d["depends_on_epic_id"] == 2
    assert d["dep_type"] == "blocks"
    assert d["rationale"] == "exemplo"
    assert "created_at" in d


def test_add_dependency_self_loop_raises(tmp_path: Path):
    conn = make_conn(tmp_path)
    mig_path = Path(__file__).parents[2] / "scripts" / "migration" / "m_2025_09_02_create_epic_dependencies.py"
    mig = load_migration_module(mig_path)
    mig.up(conn)

    repo = EpicDependencyRepository(conn)
    with pytest.raises(ValueError):
        repo.add_dependency(project_id=1, epic_id=1, depends_on_epic_id=1)


def test_add_dependency_cross_project_raises(tmp_path: Path):
    conn = make_conn(tmp_path)
    mig_path = Path(__file__).parents[2] / "scripts" / "migration" / "m_2025_09_02_create_epic_dependencies.py"
    mig = load_migration_module(mig_path)
    mig.up(conn)

    repo = EpicDependencyRepository(conn)
    # cross-project: epic 1 (proj 1) depende de epic 3 (proj 2) => falha
    with pytest.raises(ValueError):
        repo.add_dependency(project_id=1, epic_id=1, depends_on_epic_id=3)


def test_add_dependency_duplicate_raises(tmp_path: Path):
    conn = make_conn(tmp_path)
    mig_path = Path(__file__).parents[2] / "scripts" / "migration" / "m_2025_09_02_create_epic_dependencies.py"
    mig = load_migration_module(mig_path)
    mig.up(conn)

    repo = EpicDependencyRepository(conn)
    repo.add_dependency(project_id=1, epic_id=1, depends_on_epic_id=2, dep_type="blocks")
    with pytest.raises(ValueError):
        repo.add_dependency(project_id=1, epic_id=1, depends_on_epic_id=2, dep_type="blocks")


def test_remove_dependency(tmp_path: Path):
    conn = make_conn(tmp_path)
    mig_path = Path(__file__).parents[2] / "scripts" / "migration" / "m_2025_09_02_create_epic_dependencies.py"
    mig = load_migration_module(mig_path)
    mig.up(conn)

    repo = EpicDependencyRepository(conn)
    repo.add_dependency(project_id=1, epic_id=1, depends_on_epic_id=2)
    assert len(repo.list_dependencies(1)) == 1

    removed = repo.remove_dependency(project_id=1, epic_id=1, depends_on_epic_id=2)
    assert removed is True
    assert repo.list_dependencies(1) == []

    removed2 = repo.remove_dependency(project_id=1, epic_id=1, depends_on_epic_id=2)
    assert removed2 is False
