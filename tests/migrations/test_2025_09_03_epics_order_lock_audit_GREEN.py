# tests/migrations/test_2025_09_03_epics_order_lock_audit_GREEN.py
"""
A2 [GREEN] — Auditoria (ai_score/ai_sort_version/ai_sort_explainer) e trava de ordem (order_locked).
Depois da migration:
 - Campos existem e aceitam gravação (ai_score, ai_sort_version, ai_sort_explainer).
 - Trigger bloqueia UPDATE de sort_order quando order_locked=1 (IntegrityError).
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
import importlib.util, sys
import pytest


def load_migration_module(path: Path):
    spec = importlib.util.spec_from_file_location("mig_mod_a2", str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["mig_mod_a2"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def make_conn(tmp_path: Path) -> sqlite3.Connection:
    db = tmp_path / "a2_green.db"
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA foreign_keys=ON;")

    # schema mínimo com sort_order (como na A1) — agora receberá colunas novas via migration
    conn.executescript(
        """
        CREATE TABLE framework_epics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT,
            priority INTEGER,
            sort_order INTEGER
        );

        INSERT INTO framework_epics (project_id, name, priority, sort_order)
        VALUES (1, 'Epic A', 3, 0), (1, 'Epic B', 2, 1);
        """
    )
    conn.commit()
    return conn


def test_a2_columns_and_lock_behavior(tmp_path: Path):
    conn = make_conn(tmp_path)
    try:
        # Apply migration
        mig_path = Path(__file__).parents[2] / "scripts" / "migration" / "m_2025_09_03_epics_order_lock_audit.py"
        mod = load_migration_module(mig_path)
        mod.up(conn)

        cur = conn.cursor()

        # 1) Colunas de auditoria devem existir e aceitar escrita
        cur.execute("UPDATE framework_epics SET ai_score = 0.92, ai_sort_version = 'semrank_v1', ai_sort_explainer = '{\"w\":1}' WHERE name = 'Epic A'")
        conn.commit()

        row = conn.execute("SELECT ai_score, ai_sort_version, ai_sort_explainer FROM framework_epics WHERE name = 'Epic A'").fetchone()
        assert row == (0.92, 'semrank_v1', '{"w":1}')

        # 2) Trava de ordem: quando order_locked=1, alterar sort_order deve falhar
        cur.execute("UPDATE framework_epics SET order_locked = 1 WHERE name = 'Epic A'")
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            cur.execute("UPDATE framework_epics SET sort_order = 5 WHERE name = 'Epic A'")
            conn.commit()

        # 3) Já em Epic B (sem lock), deve permitir atualizar sort_order
        cur.execute("UPDATE framework_epics SET sort_order = 9 WHERE name = 'Epic B'")
        conn.commit()
        so = conn.execute("SELECT sort_order FROM framework_epics WHERE name = 'Epic B'").fetchone()[0]
        assert so == 9

    finally:
        conn.close()
