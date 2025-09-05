# scripts/migration/m_2025_09_03_epics_order_lock_audit.py
from __future__ import annotations
import sqlite3

try:
    from scripts.migration.migration_utility import register  # type: ignore
except Exception:
    def register(name, up, down):
        globals()["_MIGRATION_NAME"] = name
        globals()["_MIGRATION_UP"] = up
        globals()["_MIGRATION_DOWN"] = down

MIGRATION_NAME = "2025_09_03_add_ai_audit_and_order_lock_to_framework_epics"


def _col_exists(cur: sqlite3.Cursor, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())


def up(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON;")

    # 1) Colunas opcionais (idempotente)
    if not _col_exists(cur, "framework_epics", "ai_score"):
        cur.execute("ALTER TABLE framework_epics ADD COLUMN ai_score REAL;")
    if not _col_exists(cur, "framework_epics", "ai_sort_version"):
        cur.execute("ALTER TABLE framework_epics ADD COLUMN ai_sort_version TEXT;")
    if not _col_exists(cur, "framework_epics", "ai_sort_explainer"):
        cur.execute("ALTER TABLE framework_epics ADD COLUMN ai_sort_explainer TEXT;")
    if not _col_exists(cur, "framework_epics", "order_locked"):
        cur.execute("ALTER TABLE framework_epics ADD COLUMN order_locked INTEGER NOT NULL DEFAULT 0;")

    # 2) Trigger opcional: bloqueia UPDATE de sort_order quando order_locked=1
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_epics_block_sort_update_when_locked
        BEFORE UPDATE OF sort_order ON framework_epics
        FOR EACH ROW
        WHEN OLD.order_locked = 1 AND NEW.sort_order IS NOT OLD.sort_order
        BEGIN
          SELECT RAISE(ABORT, 'Order is locked for this epic');
        END;
    """)

    conn.commit()


def down(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DROP TRIGGER IF EXISTS trg_epics_block_sort_update_when_locked;")
    # SQLite não tem DROP COLUMN. Mantemos as colunas.
    conn.commit()


register(MIGRATION_NAME, up, down)
