import sqlite3
from pathlib import Path

from tdd_core.domain.entities.product_vision import ProductVision
from tdd_core.infrastructure.repositories import ProductVisionRepository


def _apply_migration_012(conn: sqlite3.Connection) -> None:
    sql_path = Path("migration/migrations/012_enhance_product_visions_add_fields.sql")
    script = sql_path.read_text(encoding="utf-8")
    conn.executescript(script)


def _create_minimal_projects(conn: sqlite3.Connection) -> None:
    # Minimal projects table to satisfy FK (test-only)
    conn.execute("CREATE TABLE IF NOT EXISTS framework_projects (id INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO framework_projects (id) VALUES (1)")
    conn.commit()


def test_product_vision_repository_round_trip():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    _create_minimal_projects(conn)
    # Create baseline product_visions compatible with migration 012 INSERT step
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS product_visions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            vision_statement TEXT NOT NULL,
            problem_statement TEXT,
            target_audience TEXT,
            value_proposition TEXT,
            constraints TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT,
            updated_by TEXT,
            version INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',
            notes TEXT,
            extra_metadata TEXT,
            FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE
        );
        """
    )
    _apply_migration_012(conn)

    repo = ProductVisionRepository(conn)

    pv = ProductVision(
        name="TDD Framework",
        vision_statement="Revolucionar desenvolvimento com TDD",
        target_user="Desenvolvedores",
        user_problem="Complexidade em testes",
        expected_benefits="Qualidade e produtividade",
        product_description="Framework completo TDD",
        success_metrics="98% cobertura, zero bugs",
        tech_requirements="Python 3.11+, SQLite",
        non_functional_requirements="Performance <1ms",
        compliance_requirements="GDPR, SOC2",
        risks="Curva de aprendizado",
        assumptions="Equipe experiente",
        must_have="Persistência explícita sem JSON solto",
        cannot_have="Campos genéricos sem semântica",
        deliverables="API, CLI, Web",
        market_opportunity="10M desenvolvedores",
    )

    assert pv.is_valid(), "Entidade deve ser válida antes de persistir"

    saved = repo.create(project_id=1, vision=pv)
    assert saved.id is not None
    assert saved.name == pv.name
    assert saved.must_have == pv.must_have
    assert saved.cannot_have == pv.cannot_have

    # Update path
    saved.must_have = "Requisitos claros e auditáveis"
    updated = repo.update(saved)
    assert updated.must_have == "Requisitos claros e auditáveis"

    # Retrieve by id
    fetched = repo.get_by_id(updated.id)
    assert fetched is not None
    assert fetched.name == pv.name
    assert fetched.cannot_have == pv.cannot_have

    # Delete
    ok = repo.delete(updated.id)
    assert ok is True
    assert repo.get_by_id(updated.id) is None
