import sqlite3

from tdd_core.infrastructure.repositories import (
    ProductVisionRepository,
    EpicRepository,
    TaskRepository,
    UserStoryRepository,
)
from tdd_core.infrastructure.mappers import UserStoryMapper, TaskMapper
from tdd_core.domain.entities import ProductVision, Epic, Task, UserStory


def _setup_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        -- Projects
        CREATE TABLE IF NOT EXISTS framework_projects (
            id INTEGER PRIMARY KEY,
            project_key TEXT,
            name TEXT
        );
        INSERT INTO framework_projects (id, project_key, name) VALUES (1, 'PRJ-001', 'E-commerce Platform');

        -- Product Visions (explicit columns per migration 012)
        CREATE TABLE IF NOT EXISTS product_visions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            vision_statement TEXT NOT NULL,
            problem_statement TEXT,
            target_audience TEXT,
            value_proposition TEXT,
            product_description TEXT,
            success_metrics TEXT,
            tech_requirements TEXT,
            non_functional_requirements TEXT,
            compliance_requirements TEXT,
            risks TEXT,
            assumptions TEXT,
            deliverables TEXT,
            market_opportunity TEXT,
            must_have TEXT,
            cannot_have TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT,
            updated_by TEXT,
            version INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',
            notes TEXT,
            FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE
        );

        -- Epics
        CREATE TABLE IF NOT EXISTS framework_epics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            product_vision_id INTEGER,
            epic_key TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 3,
            ai_generated INTEGER DEFAULT 0,
            ai_confidence REAL DEFAULT 0.0,
            complexity_score REAL DEFAULT 3.0,
            effort_estimate INTEGER DEFAULT 5,
            sort_order INTEGER DEFAULT 0,
            unblock_potential INTEGER DEFAULT 0,
            critical_path_weight REAL DEFAULT 0.0,
            tdd_phase TEXT DEFAULT 'analysis',
            tdd_order INTEGER DEFAULT 1,
            business_value INTEGER DEFAULT 5,
            risk_mitigation INTEGER DEFAULT 5,
            strategic_alignment INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP NULL,
            completed_at TIMESTAMP NULL,
            FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE,
            FOREIGN KEY (product_vision_id) REFERENCES product_visions(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS framework_epic_dependencies (
            epic_id INTEGER,
            depends_on_key TEXT
        );

        -- User Stories
        CREATE TABLE IF NOT EXISTS framework_user_stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epic_id INTEGER NOT NULL,
            story_key TEXT NOT NULL,
            title TEXT NOT NULL,
            user_story TEXT NOT NULL,
            acceptance_criteria TEXT NOT NULL,
            status TEXT DEFAULT 'backlog',
            workflow_stage TEXT DEFAULT 'discovery',
            story_points INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (epic_id) REFERENCES framework_epics(id) ON DELETE CASCADE
        );

        -- Tasks
        CREATE TABLE IF NOT EXISTS framework_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_key TEXT NOT NULL,
            epic_id INTEGER NOT NULL,
            user_story_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            tdd_phase TEXT,
            status TEXT DEFAULT 'todo',
            estimate_minutes INTEGER,
            actual_minutes INTEGER,
            story_points INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (epic_id) REFERENCES framework_epics(id) ON DELETE CASCADE,
            FOREIGN KEY (user_story_id) REFERENCES framework_user_stories(id) ON DELETE SET NULL
        );
        """
    )


def test_domain_relationships_mock_dump():
    conn = sqlite3.connect(":memory:")
    _setup_schema(conn)

    pv_repo = ProductVisionRepository(conn)
    epic_repo = EpicRepository(conn)
    us_repo = UserStoryRepository(conn)
    task_repo = TaskRepository(conn)

    # Create Product Vision for project 1
    pv = ProductVision(
        name="E-commerce Vision",
        vision_statement="Facilitar compras online com experiência impecável",
        target_user="Consumidores digitais",
        user_problem="Processo de compra confuso e lento",
        expected_benefits="Conversão maior e fidelização",
        product_description="Plataforma moderna com foco em performance",
        success_metrics="Conversão > 3%",
        tech_requirements="Python, SQLite, Cache",
        non_functional_requirements="p95 < 200ms",
        compliance_requirements="LGPD, PCI-DSS",
        risks="Fraude, indisponibilidade",
        assumptions="Tráfego crescente",
        must_have="Checkout em 1 passo",
        cannot_have="Campos desnecessários no fluxo",
        deliverables="API, Web, Docs",
        market_opportunity="Varejo online crescente",
    )
    pv_saved = pv_repo.create(project_id=1, vision=pv)

    # Create Epics
    epic_foundation = Epic(
        project_id=1,
        key="EP-FOUND",
        name="Fundação",
        description="Infraestrutura e base do projeto",
        ai_generated=False,
        effort_estimate=5,
    )
    epic_checkout = Epic(
        project_id=1,
        key="EP-CHECKOUT",
        name="Checkout",
        description="Fluxo de compra em 1 passo",
        ai_generated=True,
        ai_confidence=0.9,
        effort_estimate=8,
    )
    epic_checkout.epic_dependencies = ["EP-FOUND"]

    # Vincular epics à Product Vision
    epic_foundation.product_vision_id = pv_saved.id
    epic_checkout.product_vision_id = pv_saved.id
    e1 = epic_repo.create(epic_foundation)
    e2 = epic_repo.create(epic_checkout)

    # Create User Stories tied to epics
    us1 = UserStory(
        epic_id=e1.id,
        key="US-INFRA-001",
        title="Provisionar ambiente",
        narrative="Como devops, quero provisionar infraestrutura",
        acceptance_criteria=["Scripts IaC", "Ambiente replicável"],
    )
    us2 = UserStory(
        epic_id=e2.id,
        key="US-CHK-001",
        title="Checkout 1 passo",
        narrative="Como comprador, quero finalizar compra em 1 passo",
        acceptance_criteria=["Resumo do pedido", "Pagamento em 1 tela"],
    )
    us1_saved = us_repo.create(us1)
    us2_saved = us_repo.create(us2)

    # Create Tasks tied to epics
    t1 = Task(
        epic_id=e1.id,
        key="TASK-INFRA-SETUP",
        name="Setup CI",
        description="Configurar pipeline CI",
        tdd_status="red",
        estimated_duration=60,
    )
    t2 = Task(
        epic_id=e2.id,
        key="TASK-CHECKOUT-UI",
        name="Implementar UI",
        description="Criar tela de checkout",
        tdd_status="green",
        estimated_duration=120,
    )
    # Vincular tasks às user stories
    t1.user_story_id = us1_saved.id
    t2.user_story_id = us2_saved.id
    t1_saved = task_repo.create(t1)
    t2_saved = task_repo.create(t2)

    # Assertions for relationships
    assert pv_saved is not None and pv_saved.is_valid()
    assert e1.project_id == 1 and e2.project_id == 1
    assert e1.product_vision_id == pv_saved.id and e2.product_vision_id == pv_saved.id
    assert us1_saved.epic_id == e1.id and us2_saved.epic_id == e2.id
    assert t1_saved.epic_id == e1.id and t2_saved.epic_id == e2.id
    assert t1_saved.user_story_id == us1_saved.id and t2_saved.user_story_id == us2_saved.id
    assert e2.has_dependencies() and "EP-FOUND" in e2.epic_dependencies

    # Dump relationships to screen (completo e formatado)
    import json

    def row_to_dict(row):
        return {k: row[k] for k in row.keys()} if hasattr(row, "keys") else {}

    dump = {}
    proj = conn.execute(
        "SELECT * FROM framework_projects WHERE id = 1"
    ).fetchone()
    dump["project"] = row_to_dict(proj)

    pv_row = conn.execute(
        "SELECT * FROM product_visions WHERE project_id = 1 ORDER BY id DESC LIMIT 1"
    ).fetchone()
    dump["product_vision"] = row_to_dict(pv_row)

    # Epics pertencentes a esta product vision
    epics = conn.execute(
        "SELECT * FROM framework_epics WHERE product_vision_id = ? ORDER BY id",
        (pv_row["id"],),
    ).fetchall()
    epics_dump = []
    for er in epics:
        e_dict = row_to_dict(er)
        deps = conn.execute(
            "SELECT depends_on_key FROM framework_epic_dependencies WHERE epic_id = ?",
            (er["id"],),
        ).fetchall()
        e_dict["dependencies"] = [d[0] for d in deps]

        # User Stories e Tasks aninhadas por user_story_id
        us_rows = conn.execute(
            "SELECT * FROM framework_user_stories WHERE epic_id = ? ORDER BY id",
            (er["id"],),
        ).fetchall()
        us_dump = []
        for usr in us_rows:
            us_dict = row_to_dict(usr)
            # Parse JSON textual de acceptance_criteria para lista, para melhor legibilidade
            try:
                import json as _json
                ac = usr["acceptance_criteria"]
                us_dict["acceptance_criteria"] = _json.loads(ac) if ac else []
            except Exception:
                pass
            task_rows = conn.execute(
                "SELECT * FROM framework_tasks WHERE user_story_id = ? ORDER BY id",
                (usr["id"],),
            ).fetchall()
            us_dict["tasks"] = [row_to_dict(r) for r in task_rows]
            us_dump.append(us_dict)
        e_dict["user_stories"] = us_dump

        epics_dump.append(e_dict)

    dump["epics"] = epics_dump

    print("\n=== DOMAIN RELATIONSHIP FULL DUMP (JSON) ===")
    print(json.dumps(dump, ensure_ascii=False, indent=2))
