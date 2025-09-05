
# tests/migrations/test_2025_09_01_sort_order.py
import sqlite3
import tempfile
from pathlib import Path

# Import the migration module
import importlib.util, sys

def load_migration_module(path: Path):
    spec = importlib.util.spec_from_file_location("migration_mod", str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["migration_mod"] = mod
    spec.loader.exec_module(mod)  # type: ignore
    return mod

def create_min_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE framework_epics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT,
            description TEXT,
            priority INTEGER,
            created_at TEXT
        );
    """)
    conn.commit()

def seed_sample_data(conn: sqlite3.Connection):
    cur = conn.cursor()
    # project 1: 3 epics with created_at in chronological order
    cur.execute("INSERT INTO framework_epics (project_id, name, created_at) VALUES (1, 'A', '2025-01-01T10:00:00Z');")
    cur.execute("INSERT INTO framework_epics (project_id, name, created_at) VALUES (1, 'B', '2025-01-01T11:00:00Z');")
    cur.execute("INSERT INTO framework_epics (project_id, name, created_at) VALUES (1, 'C', '2025-01-01T12:00:00Z');")
    # project 2: 2 epics
    cur.execute("INSERT INTO framework_epics (project_id, name, created_at) VALUES (2, 'X', '2025-01-02T09:00:00Z');")
    cur.execute("INSERT INTO framework_epics (project_id, name, created_at) VALUES (2, 'Y', '2025-01-02T10:00:00Z');")
    conn.commit()

def get_sort_orders(conn: sqlite3.Connection, project_id: int):
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, sort_order
        FROM framework_epics
        WHERE project_id = ?
        ORDER BY sort_order ASC, id ASC
    """, (project_id,))
    return cur.fetchall()

def test_migration_adds_column_and_initializes(tmp_path: Path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    try:
        create_min_schema(conn)
        seed_sample_data(conn)

        # Load and run migration
        mig_path = Path(__file__).parents[2] / "scripts" / "migration" / "m_2025_09_01_add_sort_order_epics.py"
        mod = load_migration_module(mig_path)
        mod.up(conn)

        # Column exists
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(framework_epics)")
        cols = [r[1] for r in cur.fetchall()]
        assert "sort_order" in cols

        # Initialized per-project
        p1 = get_sort_orders(conn, 1)
        p2 = get_sort_orders(conn, 2)
        assert [row[2] for row in p1] == [0, 1, 2]
        assert [row[2] for row in p2] == [0, 1]

        # Index exists
        cur.execute("PRAGMA index_list('framework_epics')")
        indexes = [r[1] for r in cur.fetchall()]
        assert "idx_framework_epics_project_order" in indexes

    finally:
        conn.close()

def test_trigger_assigns_sort_order_on_insert(tmp_path: Path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    try:
        create_min_schema(conn)
        seed_sample_data(conn)
        mig_path = Path(__file__).parents[2] / "scripts" / "migration" / "m_2025_09_01_add_sort_order_epics.py"
        mod = load_migration_module(mig_path)
        mod.up(conn)

        cur = conn.cursor()
        # Insert new epic without sort_order for project 1
        cur.execute("INSERT INTO framework_epics (project_id, name, created_at) VALUES (1, 'D', '2025-01-01T13:00:00Z');")
        conn.commit()

        cur.execute("SELECT sort_order FROM framework_epics WHERE project_id = 1 AND name = 'D'")
        so = cur.fetchone()[0]
        assert so == 3  # MAX + 1 from existing [0,1,2]

        # Idempotency: running up() again should not break
        mod.up(conn)
        cur.execute("SELECT COUNT(*) FROM framework_epics")
        _ = cur.fetchone()[0]  # Just ensure it runs without errors

    finally:
        conn.close()
