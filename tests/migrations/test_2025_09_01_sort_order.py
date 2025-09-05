# tests/migrations/test_2025_09_01_sort_order.py
import sqlite3
from pathlib import Path
import importlib.util, sys


def load_migration_module(path: Path):
    """
    Carrega a migration como módulo a partir do caminho do arquivo,
    permitindo chamar up(conn)/down(conn) diretamente no teste.
    """
    spec = importlib.util.spec_from_file_location("migration_mod", str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["migration_mod"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def create_min_schema(conn: sqlite3.Connection):
    """
    Cria um schema mínimo isolado para o teste (sem dependências do projeto).
    Inclui created_at para exercitar o caminho preferencial de inicialização.
    """
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
    """
    Cria dados de exemplo em dois projetos para validar a inicialização 0..N.
    """
    cur = conn.cursor()
    # project 1
    cur.execute("INSERT INTO framework_epics (project_id, name, created_at) VALUES (1, 'A', '2025-01-01T10:00:00Z');")
    cur.execute("INSERT INTO framework_epics (project_id, name, created_at) VALUES (1, 'B', '2025-01-01T11:00:00Z');")
    cur.execute("INSERT INTO framework_epics (project_id, name, created_at) VALUES (1, 'C', '2025-01-01T12:00:00Z');")
    # project 2
    cur.execute("INSERT INTO framework_epics (project_id, name, created_at) VALUES (2, 'X', '2025-01-02T09:00:00Z');")
    cur.execute("INSERT INTO framework_epics (project_id, name, created_at) VALUES (2, 'Y', '2025-01-02T10:00:00Z');")
    conn.commit()


def _col_names(conn: sqlite3.Connection, table: str):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]


def get_sort_orders(conn: sqlite3.Connection, project_id: int):
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, sort_order
          FROM framework_epics
         WHERE project_id = ?
         ORDER BY sort_order ASC, id ASC
    """, (project_id,))
    return cur.fetchall()


def test_migration_applies_and_initializes(tmp_path: Path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    try:
        create_min_schema(conn)
        seed_sample_data(conn)

        # Caminho da migration no repo
        mig_path = Path(__file__).parents[2] / "scripts" / "migration" / "m_2025_09_01_add_sort_order_epics.py"
        mod = load_migration_module(mig_path)

        # Executa UP diretamente na conexão do teste
        mod.up(conn)

        # Coluna existe
        assert "sort_order" in _col_names(conn, "framework_epics")

        # Inicialização 0..N por projeto
        p1 = get_sort_orders(conn, 1)
        p2 = get_sort_orders(conn, 2)
        assert [row[2] for row in p1] == [0, 1, 2]
        assert [row[2] for row in p2] == [0, 1]

        # Índice existe
        cur = conn.cursor()
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
        # Inserção sem sort_order → trigger deve atribuir MAX+1 no mesmo projeto
        cur.execute("INSERT INTO framework_epics (project_id, name, created_at) VALUES (1, 'D', '2025-01-01T13:00:00Z');")
        conn.commit()

        cur.execute("SELECT sort_order FROM framework_epics WHERE project_id = 1 AND name = 'D'")
        so = cur.fetchone()[0]
        assert so == 3  # MAX(0,1,2) + 1

        # Idempotência: rodar up() novamente não deve quebrar
        mod.up(conn)
        cur.execute("SELECT COUNT(*) FROM framework_epics")
        assert cur.fetchone()[0] >= 4
    finally:
        conn.close()
