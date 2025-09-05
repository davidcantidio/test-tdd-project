# scripts/migration/m_2025_09_01_add_sort_order_epics.py
from __future__ import annotations
import sqlite3

# Registro no sistema de migrations do projeto (com fallback para testes/standalone)
try:
    from scripts.migration.migration_utility import register  # type: ignore
except Exception:
    def register(name, up, down):
        # Shim simples para permitir import/execução em testes sem o utility real
        globals()["_MIGRATION_NAME"] = name
        globals()["_MIGRATION_UP"] = up
        globals()["_MIGRATION_DOWN"] = down

MIGRATION_NAME = "2025_09_01_add_sort_order_to_framework_epics"


def _col_exists(cur: sqlite3.Cursor, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == col for row in cur.fetchall())


def _init_sort_order(conn: sqlite3.Connection) -> None:
    """
    Inicializa sort_order por projeto.
    Preferimos created_at se existir; caso contrário, caímos para id.
    """
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(framework_epics)")
    cols = [r[1] for r in cur.fetchall()]

    if "created_at" in cols:
        order_sql = """
            WITH ranked AS (
                SELECT id,
                       ROW_NUMBER() OVER (
                         PARTITION BY project_id
                         ORDER BY COALESCE(created_at, datetime('now')), id
                       ) - 1 AS rn
                FROM framework_epics
            )
            UPDATE framework_epics
               SET sort_order = (SELECT rn FROM ranked WHERE ranked.id = framework_epics.id);
        """
    else:
        order_sql = """
            WITH ranked AS (
                SELECT id,
                       ROW_NUMBER() OVER (
                         PARTITION BY project_id
                         ORDER BY id
                       ) - 1 AS rn
                FROM framework_epics
            )
            UPDATE framework_epics
               SET sort_order = (SELECT rn FROM ranked WHERE ranked.id = framework_epics.id);
        """
    cur.execute(order_sql)


def up(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON;")

    # 1) Adiciona coluna sort_order se não existir
    if not _col_exists(cur, "framework_epics", "sort_order"):
        cur.execute("ALTER TABLE framework_epics ADD COLUMN sort_order INTEGER;")
        _init_sort_order(conn)

    # 2) Índices
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_framework_epics_project_order
            ON framework_epics (project_id, sort_order);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_framework_epics_project
            ON framework_epics (project_id);
    """)

    # 3) Trigger para auto-atribuir sort_order quando vier NULL em novos inserts
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_framework_epics_sort_order_ai
        AFTER INSERT ON framework_epics
        FOR EACH ROW
        WHEN NEW.sort_order IS NULL
        BEGIN
          UPDATE framework_epics
             SET sort_order = (
               SELECT COALESCE(MAX(sort_order) + 1, 0)
                 FROM framework_epics
                WHERE project_id = NEW.project_id
                  AND id <> NEW.id
             )
           WHERE id = NEW.id;
        END;
    """)

    conn.commit()


def down(conn: sqlite3.Connection) -> None:
    """
    SQLite não tem DROP COLUMN estável. Mantemos a coluna e limpamos index/trigger.
    """
    cur = conn.cursor()
    cur.execute("DROP TRIGGER IF EXISTS trg_framework_epics_sort_order_ai;")
    cur.execute("DROP INDEX IF EXISTS idx_framework_epics_project_order;")
    # Mantemos a coluna (sem DROP COLUMN).
    conn.commit()


register(MIGRATION_NAME, up, down)
