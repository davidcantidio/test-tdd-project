# scripts/migration/m_2025_09_04_complete_topological_fields.py
from __future__ import annotations
import sqlite3

try:
    from scripts.migration.migration_utility import register  # type: ignore
except Exception:
    def register(name, up, down):
        globals()["_MIGRATION_NAME"] = name
        globals()["_MIGRATION_UP"] = up
        globals()["_MIGRATION_DOWN"] = down

MIGRATION_NAME = "2025_09_04_complete_topological_fields_for_ia_epics"


def _col_exists(cur: sqlite3.Cursor, table: str, col: str) -> bool:
    """Check if column exists in table."""
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())


def _index_exists(cur: sqlite3.Cursor, index_name: str) -> bool:
    """Check if index exists."""
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
    return cur.fetchone() is not None


def up(conn: sqlite3.Connection) -> None:
    """
    Adiciona os 4 campos faltantes necessários para compatibilidade completa 
    com DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO.py:
    
    - effort_estimate: Estimativa de esforço em dias
    - tdd_phase: Fase do workflow TDD
    - tdd_order: Ordem de prioridade TDD (1=RED, 2=GREEN, 3=REFACTOR)
    - complexity_score: Score de complexidade (1.0-5.0)
    
    Plus índices otimizados para performance das operações topológicas.
    """
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON;")

    # 1) Campos necessários para o algoritmo topológico
    
    # effort_estimate: Usado pelo algoritmo para cálculos de densidade de valor
    if not _col_exists(cur, "framework_epics", "effort_estimate"):
        cur.execute("ALTER TABLE framework_epics ADD COLUMN effort_estimate INTEGER DEFAULT 7;")
        print("✅ Added effort_estimate column")
    
    # tdd_phase: Workflow TDD phases
    if not _col_exists(cur, "framework_epics", "tdd_phase"):
        cur.execute("""
            ALTER TABLE framework_epics ADD COLUMN tdd_phase TEXT 
            CHECK(tdd_phase IN ('analysis', 'red', 'green', 'refactor', 'review'));
        """)
        print("✅ Added tdd_phase column with constraints")
    
    # tdd_order: Priorização TDD (RED > GREEN > REFACTOR)
    if not _col_exists(cur, "framework_epics", "tdd_order"):
        cur.execute("""
            ALTER TABLE framework_epics ADD COLUMN tdd_order INTEGER 
            CHECK(tdd_order IN (1, 2, 3));
        """)
        print("✅ Added tdd_order column with constraints")
    
    # complexity_score: Score de complexidade para o algoritmo
    if not _col_exists(cur, "framework_epics", "complexity_score"):
        cur.execute("ALTER TABLE framework_epics ADD COLUMN complexity_score DECIMAL(5,2) DEFAULT 3.0;")
        print("✅ Added complexity_score column")

    # 2) Índices de performance para operações topológicas
    
    # Índice para queries combinadas de esforço/complexidade
    if not _index_exists(cur, "idx_epics_effort_complexity"):
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_epics_effort_complexity 
            ON framework_epics(effort_estimate, complexity_score);
        """)
        print("✅ Created idx_epics_effort_complexity index")
    
    # Índice para queries de workflow TDD
    if not _index_exists(cur, "idx_epics_tdd_workflow"):
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_epics_tdd_workflow 
            ON framework_epics(tdd_phase, tdd_order);
        """)
        print("✅ Created idx_epics_tdd_workflow index")
    
    # Índice para ordenação topológica otimizada
    if not _index_exists(cur, "idx_epics_topological_sort"):
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_epics_topological_sort 
            ON framework_epics(project_id, sort_order, complexity_score);
        """)
        print("✅ Created idx_epics_topological_sort index")

    # 3) Inicializar dados existentes com valores inteligentes
    
    # Inicializar effort_estimate baseado em duration_days se existir
    cur.execute("""
        UPDATE framework_epics 
        SET effort_estimate = CASE 
            WHEN duration_days IS NOT NULL AND duration_days > 0 THEN duration_days
            WHEN estimated_hours IS NOT NULL THEN CAST(estimated_hours / 8.0 AS INTEGER)
            ELSE 7
        END
        WHERE effort_estimate IS NULL;
    """)
    
    # Inicializar complexity_score baseado em número de tasks (se aplicável no futuro)
    cur.execute("""
        UPDATE framework_epics 
        SET complexity_score = CASE 
            WHEN priority = 1 THEN 4.5  -- Critical = high complexity
            WHEN priority = 2 THEN 3.5  -- High priority
            WHEN priority = 3 THEN 3.0  -- Medium (default)
            WHEN priority = 4 THEN 2.5  -- Lower priority
            WHEN priority = 5 THEN 2.0  -- Lowest priority
            ELSE 3.0
        END
        WHERE complexity_score = 3.0;  -- Only update defaults
    """)
    
    print("✅ Initialized existing data with intelligent defaults")

    conn.commit()
    print("🎯 Migration m_2025_09_04_complete_topological_fields completed successfully!")


def down(conn: sqlite3.Connection) -> None:
    """
    Rollback migration. 
    SQLite não suporta DROP COLUMN de forma estável, então removemos apenas índices.
    """
    cur = conn.cursor()
    
    # Remove índices criados
    cur.execute("DROP INDEX IF EXISTS idx_epics_effort_complexity;")
    cur.execute("DROP INDEX IF EXISTS idx_epics_tdd_workflow;")
    cur.execute("DROP INDEX IF EXISTS idx_epics_topological_sort;")
    
    print("🔙 Removed topological performance indexes")
    print("⚠️ Note: SQLite doesn't support DROP COLUMN - columns remain but indexes removed")
    
    conn.commit()


register(MIGRATION_NAME, up, down)