# tests/migrations/test_2025_09_03_epics_order_lock_audit_RED.py
"""
A2 [RED] — Auditoria (ai_score/ai_sort_version/ai_sort_explainer) e trava de ordem (order_locked).
Antes da migration, os campos/trigger não existem, então:
 - Tentar escrever ai_score/ai_sort_version deve falhar (OperationalError).
 - Tentar bloquear update de sort_order com order_locked=1 também falha porque a coluna/trigger não existem.
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
import pytest


def make_conn(tmp_path: Path) -> sqlite3.Connection:
    db = tmp_path / "a2_red.db"
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA foreign_keys=ON;")
    # schema mínimo com sort_order (da A1) — sem colunas novas
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


def test_ai_audit_columns_do_not_exist(tmp_path: Path):
    conn = make_conn(tmp_path)
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("UPDATE framework_epics SET ai_score = 0.85 WHERE name = 'Epic A'")
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("UPDATE framework_epics SET ai_sort_version = 'semrank_v1' WHERE name = 'Epic A'")
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("UPDATE framework_epics SET ai_sort_explainer = '{\"w\":1}' WHERE name = 'Epic A'")
    finally:
        conn.close()


def test_order_locked_does_not_exist_yet(tmp_path: Path):
    conn = make_conn(tmp_path)
    try:
        # Tentativa de setar order_locked deve falhar pois coluna não existe
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("UPDATE framework_epics SET order_locked = 1 WHERE name = 'Epic A'")
        # Tentativa de bloquear update de sort_order não pode ser testada sem a coluna/trigger.
        # O objetivo aqui é apenas RED (comportamento ainda não suportado no schema).
    finally:
        conn.close()
