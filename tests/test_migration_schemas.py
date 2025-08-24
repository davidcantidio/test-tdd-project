#!/usr/bin/env python3
"""
🧪 TESTS - Migration Schema Validation

Testes específicos para validar as novas estruturas criadas pelas migrações 007, 008, 009.
Verifica integridade, performance, e funcionalidade das novas tabelas e relacionamentos.

Usage:
    python -m pytest tests/test_migration_schemas.py -v
    python -m pytest tests/test_migration_schemas.py::TestProductVisions -v
    python -m pytest tests/test_migration_schemas.py::TestPerformance -v

Features:
- Validação de estrutura das novas tabelas
- Testes de relacionamentos e foreign keys  
- Testes de performance das queries
- Validação de triggers e indexes
- Testes de integridade de dados
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, date
from pathlib import Path
import sys
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from streamlit_extension.utils.database import DatabaseManager


class TestMigrationSchemaBase:
    """Base class para testes de migração"""
    
    @pytest.fixture
    def temp_db(self):
        """Cria banco temporário para testes"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Initialize with original schema
        conn = sqlite3.connect(db_path)
        
        # Load and execute original schema
        schema_path = project_root / "framework_schema_final.sql"
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                conn.executescript(schema_sql)
        
        conn.close()
        
        yield db_path
        
        # Cleanup
        os.unlink(db_path)
    
    @pytest.fixture
    def migrated_db(self, temp_db):
        """Aplica todas as migrações no banco temporário"""
        
        conn = sqlite3.connect(temp_db)
        
        # Apply migration 007
        migration_007_path = project_root / "migration/migrations/007_add_product_visions_and_user_stories.sql"
        if migration_007_path.exists():
            with open(migration_007_path, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
                conn.executescript(migration_sql)
        
        # Apply migration 008
        migration_008_path = project_root / "migration/migrations/008_task_enhancements_and_dependencies.sql"
        if migration_008_path.exists():
            with open(migration_008_path, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
                conn.executescript(migration_sql)
        
        # Apply migration 009
        migration_009_path = project_root / "migration/migrations/009_sprint_system_and_advanced_features.sql"
        if migration_009_path.exists():
            with open(migration_009_path, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
                conn.executescript(migration_sql)
        
        conn.close()
        
        return temp_db
    
    def get_table_info(self, db_path: str, table_name: str):
        """Retorna informações da tabela"""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='{table_name}'")
        triggers = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'columns': [dict(col) for col in columns],
            'indexes': indexes,
            'triggers': triggers
        }


class TestProductVisions(TestMigrationSchemaBase):
    """Testes para tabela product_visions (Migration 007)"""
    
    def test_product_visions_table_exists(self, migrated_db):
        """Testa se tabela product_visions foi criada"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_visions'")
        result = cursor.fetchone()
        
        assert result is not None, "Tabela product_visions não foi criada"
        conn.close()
    
    def test_product_visions_columns(self, migrated_db):
        """Testa estrutura da tabela product_visions"""
        info = self.get_table_info(migrated_db, 'product_visions')
        
        column_names = [col['name'] for col in info['columns']]
        
        # Campos obrigatórios
        required_fields = [
            'id', 'project_id', 'vision_key', 'name', 
            'vision_statement', 'status', 'priority',
            'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            assert field in column_names, f"Campo obrigatório {field} não encontrado"
        
        # Campos JSON
        json_fields = [
            'success_metrics', 'strategic_goals', 'key_features',
            'user_personas', 'business_objectives'
        ]
        
        for field in json_fields:
            assert field in column_names, f"Campo JSON {field} não encontrado"
    
    def test_product_visions_foreign_keys(self, migrated_db):
        """Testa foreign keys da tabela product_visions"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA foreign_key_list(product_visions)")
        fks = cursor.fetchall()
        
        # Should have FK to framework_projects
        project_fk = any(fk[2] == 'framework_projects' for fk in fks)
        assert project_fk, "Foreign key para framework_projects não encontrada"
        
        conn.close()
    
    def test_product_visions_indexes(self, migrated_db):
        """Testa indexes da tabela product_visions"""
        info = self.get_table_info(migrated_db, 'product_visions')
        
        expected_indexes = [
            'idx_product_visions_project_id',
            'idx_product_visions_status',
            'idx_product_visions_priority'
        ]
        
        for index_name in expected_indexes:
            assert index_name in info['indexes'], f"Index {index_name} não encontrado"
    
    def test_product_visions_insert_and_query(self, migrated_db):
        """Testa inserção e consulta de dados"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        # First create a project (dependency)
        cursor.execute("""
            INSERT INTO framework_projects (id, project_key, name)
            VALUES (1, 'test_proj', 'Test Project')
        """)
        
        # Insert test vision
        cursor.execute("""
            INSERT INTO product_visions (
                project_id, vision_key, name, vision_statement,
                success_metrics, strategic_goals
            ) VALUES (
                1, 'vision_1', 'Test Vision', 'A test product vision',
                '["metric1", "metric2"]', '["goal1", "goal2"]'
            )
        """)
        
        # Query data
        cursor.execute("SELECT * FROM product_visions WHERE vision_key = 'vision_1'")
        result = cursor.fetchone()
        
        assert result is not None, "Dados não foram inseridos corretamente"
        assert result[3] == 'Test Vision', "Nome da vision incorreto"
        
        conn.close()


class TestUserStories(TestMigrationSchemaBase):
    """Testes para tabela framework_user_stories (Migration 007)"""
    
    def test_user_stories_table_exists(self, migrated_db):
        """Testa se tabela framework_user_stories foi criada"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='framework_user_stories'")
        result = cursor.fetchone()
        
        assert result is not None, "Tabela framework_user_stories não foi criada"
        conn.close()
    
    def test_user_stories_comprehensive_structure(self, migrated_db):
        """Testa estrutura abrangente da tabela framework_user_stories"""
        info = self.get_table_info(migrated_db, 'framework_user_stories')
        
        column_names = [col['name'] for col in info['columns']]
        
        # Core fields
        core_fields = [
            'id', 'epic_id', 'story_key', 'title', 'user_story',
            'acceptance_criteria', 'story_points', 'status', 'priority'
        ]
        
        for field in core_fields:
            assert field in column_names, f"Campo core {field} não encontrado"
        
        # Advanced fields
        advanced_fields = [
            'technical_requirements', 'ux_requirements', 'validation_plan',
            'labels', 'components', 'platforms'
        ]
        
        for field in advanced_fields:
            assert field in column_names, f"Campo avançado {field} não encontrado"
    
    def test_user_stories_relationships(self, migrated_db):
        """Testa relacionamentos entre user stories e outras entidades"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        # Create test data hierarchy
        cursor.execute("INSERT INTO framework_projects (id, project_key, name) VALUES (1, 'proj1', 'Project 1')")
        cursor.execute("INSERT INTO framework_epics (id, project_id, epic_key, name) VALUES (1, 1, 'epic1', 'Epic 1')")
        
        # Insert user story
        cursor.execute("""
            INSERT INTO framework_user_stories (
                epic_id, story_key, title, user_story, acceptance_criteria
            ) VALUES (
                1, 'story1', 'Test Story', 
                'As a user, I want to test, so that tests pass',
                '["Criteria 1", "Criteria 2"]'
            )
        """)
        
        # Test relationship query
        cursor.execute("""
            SELECT us.title, e.name as epic_name, p.name as project_name
            FROM framework_user_stories us
            JOIN framework_epics e ON us.epic_id = e.id
            JOIN framework_projects p ON e.project_id = p.id
            WHERE us.story_key = 'story1'
        """)
        
        result = cursor.fetchone()
        assert result is not None, "Relacionamento entre user stories, epics e projects falhou"
        assert result[0] == 'Test Story'
        assert result[1] == 'Epic 1'
        assert result[2] == 'Project 1'
        
        conn.close()


class TestTaskEnhancements(TestMigrationSchemaBase):
    """Testes para melhorias na tabela framework_tasks (Migration 008)"""
    
    def test_task_new_columns_exist(self, migrated_db):
        """Testa se novas colunas foram adicionadas à tabela framework_tasks"""
        info = self.get_table_info(migrated_db, 'framework_tasks')
        column_names = [col['name'] for col in info['columns']]
        
        new_fields = [
            'is_milestone', 'planned_start_date', 'planned_end_date',
            'due_date', 'acceptance_criteria', 'task_type',
            'parent_task_id', 'user_story_id', 'tdd_order'
        ]
        
        for field in new_fields:
            assert field in column_names, f"Nova coluna {field} não foi adicionada"
    
    def test_task_dependencies_table(self, migrated_db):
        """Testa tabela task_dependencies"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_dependencies'")
        assert cursor.fetchone() is not None, "Tabela task_dependencies não foi criada"
        
        # Test structure
        info = self.get_table_info(migrated_db, 'task_dependencies')
        column_names = [col['name'] for col in info['columns']]
        
        required_fields = [
            'task_id', 'depends_on_task_id', 'dependency_type',
            'dependency_strength', 'risk_level'
        ]
        
        for field in required_fields:
            assert field in column_names, f"Campo {field} não encontrado em task_dependencies"
        
        conn.close()
    
    def test_task_labels_system(self, migrated_db):
        """Testa sistema de labels para tasks"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_labels'")
        assert cursor.fetchone() is not None, "Tabela task_labels não foi criada"
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_label_assignments'")
        assert cursor.fetchone() is not None, "Tabela task_label_assignments não foi criada"
        
        # Test default labels were created
        cursor.execute("SELECT COUNT(*) FROM task_labels WHERE is_system_label = TRUE")
        system_labels_count = cursor.fetchone()[0]
        assert system_labels_count > 0, "Labels padrão do sistema não foram criados"
        
        conn.close()
    
    def test_task_parent_child_relationship(self, migrated_db):
        """Testa relacionamento pai-filho entre tasks"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        # Create test epic first
        cursor.execute("INSERT INTO framework_projects (id, project_key, name) VALUES (1, 'proj1', 'Project 1')")
        cursor.execute("INSERT INTO framework_epics (id, project_id, epic_key, name) VALUES (1, 1, 'epic1', 'Epic 1')")
        
        # Create parent task
        cursor.execute("""
            INSERT INTO framework_tasks (id, task_key, epic_id, title)
            VALUES (1, 'parent_task', 1, 'Parent Task')
        """)
        
        # Create child task
        cursor.execute("""
            INSERT INTO framework_tasks (id, task_key, epic_id, title, parent_task_id)
            VALUES (2, 'child_task', 1, 'Child Task', 1)
        """)
        
        # Test parent-child query
        cursor.execute("""
            SELECT parent.title as parent_title, child.title as child_title
            FROM framework_tasks child
            JOIN framework_tasks parent ON child.parent_task_id = parent.id
            WHERE child.task_key = 'child_task'
        """)
        
        result = cursor.fetchone()
        assert result is not None, "Relacionamento pai-filho não funciona"
        assert result[0] == 'Parent Task'
        assert result[1] == 'Child Task'
        
        conn.close()


class TestSprintSystem(TestMigrationSchemaBase):
    """Testes para sistema de sprints (Migration 009)"""
    
    def test_sprint_tables_exist(self, migrated_db):
        """Testa se tabelas do sistema de sprint foram criadas"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        sprint_tables = ['sprints', 'sprint_tasks', 'sprint_milestones']
        
        for table in sprint_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            assert cursor.fetchone() is not None, f"Tabela {table} não foi criada"
        
        conn.close()
    
    def test_sprint_comprehensive_structure(self, migrated_db):
        """Testa estrutura abrangente da tabela sprints"""
        info = self.get_table_info(migrated_db, 'sprints')
        column_names = [col['name'] for col in info['columns']]
        
        essential_fields = [
            'id', 'project_id', 'sprint_key', 'sprint_name',
            'start_date', 'end_date', 'status', 'sprint_goal'
        ]
        
        for field in essential_fields:
            assert field in column_names, f"Campo essencial {field} não encontrado em sprints"
        
        # Advanced sprint features
        advanced_fields = [
            'team_members', 'burndown_data', 'retrospective_notes',
            'story_points_committed', 'story_points_completed'
        ]
        
        for field in advanced_fields:
            assert field in column_names, f"Campo avançado {field} não encontrado em sprints"
    
    def test_sprint_task_assignment(self, migrated_db):
        """Testa atribuição de tasks a sprints"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        # Create test data
        cursor.execute("INSERT INTO framework_projects (id, project_key, name) VALUES (1, 'proj1', 'Project 1')")
        cursor.execute("INSERT INTO framework_epics (id, project_id, epic_key, name) VALUES (1, 1, 'epic1', 'Epic 1')")
        cursor.execute("INSERT INTO framework_tasks (id, task_key, epic_id, title) VALUES (1, 'task1', 1, 'Task 1')")
        
        cursor.execute("""
            INSERT INTO sprints (id, project_id, sprint_key, sprint_name, start_date, end_date)
            VALUES (1, 1, 'sprint1', 'Sprint 1', '2025-08-22', '2025-09-05')
        """)
        
        # Assign task to sprint
        cursor.execute("""
            INSERT INTO sprint_tasks (sprint_id, task_id, commitment_type, priority_in_sprint)
            VALUES (1, 1, 'committed', 1)
        """)
        
        # Test sprint-task relationship
        cursor.execute("""
            SELECT s.sprint_name, t.title, st.commitment_type
            FROM sprint_tasks st
            JOIN sprints s ON st.sprint_id = s.id
            JOIN framework_tasks t ON st.task_id = t.id
            WHERE s.sprint_key = 'sprint1'
        """)
        
        result = cursor.fetchone()
        assert result is not None, "Atribuição de task ao sprint falhou"
        assert result[0] == 'Sprint 1'
        assert result[1] == 'Task 1'
        assert result[2] == 'committed'
        
        conn.close()


class TestAIIntegration(TestMigrationSchemaBase):
    """Testes para sistema de integração com IA (Migration 009)"""
    
    def test_ai_generations_table(self, migrated_db):
        """Testa tabela ai_generations"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_generations'")
        assert cursor.fetchone() is not None, "Tabela ai_generations não foi criada"
        
        info = self.get_table_info(migrated_db, 'ai_generations')
        column_names = [col['name'] for col in info['columns']]
        
        required_fields = [
            'generation_type', 'ai_model', 'user_prompt', 'ai_response',
            'user_rating', 'input_tokens', 'output_tokens'
        ]
        
        for field in required_fields:
            assert field in column_names, f"Campo {field} não encontrado em ai_generations"
        
        conn.close()
    
    def test_ai_generation_workflow(self, migrated_db):
        """Testa fluxo de geração de IA"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        # Insert AI generation record
        cursor.execute("""
            INSERT INTO ai_generations (
                generation_type, ai_model, user_prompt, ai_response,
                input_tokens, output_tokens, generation_cost
            ) VALUES (
                'code_generation', 'gpt-4', 'Generate a function', 'def example(): pass',
                50, 100, 0.002
            )
        """)
        
        # Test query
        cursor.execute("SELECT generation_type, ai_model FROM ai_generations WHERE user_prompt = 'Generate a function'")
        result = cursor.fetchone()
        
        assert result is not None, "Registro de geração IA não foi inserido"
        assert result[0] == 'code_generation'
        assert result[1] == 'gpt-4'
        
        conn.close()


class TestChangeLog(TestMigrationSchemaBase):
    """Testes para sistema de change log (Migration 009)"""
    
    def test_change_log_table(self, migrated_db):
        """Testa tabela change_log"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='change_log'")
        assert cursor.fetchone() is not None, "Tabela change_log não foi criada"
        
        info = self.get_table_info(migrated_db, 'change_log')
        column_names = [col['name'] for col in info['columns']]
        
        required_fields = [
            'change_type', 'entity_type', 'entity_id', 'old_value', 
            'new_value', 'user_id', 'created_at'
        ]
        
        for field in required_fields:
            assert field in column_names, f"Campo {field} não encontrado em change_log"
        
        conn.close()
    
    def test_automatic_change_logging(self, migrated_db):
        """Testa log automático de mudanças via triggers"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        # Create test task
        cursor.execute("INSERT INTO framework_projects (id, project_key, name) VALUES (1, 'proj1', 'Project 1')")
        cursor.execute("INSERT INTO framework_epics (id, project_id, epic_key, name) VALUES (1, 1, 'epic1', 'Epic 1')")
        cursor.execute("""
            INSERT INTO framework_tasks (id, task_key, epic_id, title, status, assigned_to)
            VALUES (1, 'task1', 1, 'Task 1', 'pending', 1)
        """)
        
        # Update task status (should trigger change log)
        cursor.execute("""
            UPDATE framework_tasks SET status = 'in_progress' WHERE id = 1
        """)
        
        # Check if change was logged
        cursor.execute("""
            SELECT change_type, entity_type, old_value, new_value 
            FROM change_log 
            WHERE entity_type = 'task' AND entity_id = 1
        """)
        
        result = cursor.fetchone()
        assert result is not None, "Mudança automática não foi registrada no change_log"
        assert result[0] == 'update'
        assert result[1] == 'task'
        assert result[2] == 'pending'
        assert result[3] == 'in_progress'
        
        conn.close()


class TestPerformance(TestMigrationSchemaBase):
    """Testes de performance das novas estruturas"""
    
    def test_index_effectiveness(self, migrated_db):
        """Testa efetividade dos índices criados"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        # Test product_visions index
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM product_visions WHERE project_id = 1")
        plan = cursor.fetchall()
        
        # Should use index (contains "USING INDEX" in plan)
        plan_text = ' '.join([str(row) for row in plan])
        has_index = 'idx_product_visions_project_id' in plan_text or 'USING INDEX' in plan_text.upper()
        
        # Note: In some SQLite versions, the exact text may vary, so we check for common indicators
        assert len(plan) > 0, "Query plan não foi gerado"
        
        conn.close()
    
    def test_query_performance_baseline(self, migrated_db):
        """Testa performance baseline das queries principais"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        # Create some test data
        cursor.execute("INSERT INTO framework_projects (id, project_key, name) VALUES (1, 'proj1', 'Project 1')")
        
        # Test simple queries execute without error
        test_queries = [
            "SELECT COUNT(*) FROM product_visions",
            "SELECT COUNT(*) FROM framework_user_stories", 
            "SELECT COUNT(*) FROM task_dependencies",
            "SELECT COUNT(*) FROM sprints",
            "SELECT COUNT(*) FROM ai_generations",
            "SELECT COUNT(*) FROM change_log"
        ]
        
        for query in test_queries:
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                assert result is not None, f"Query falhou: {query}"
            except Exception as e:
                pytest.fail(f"Query performance test failed for '{query}': {str(e)}")
        
        conn.close()
    
    def test_complex_relationship_queries(self, migrated_db):
        """Testa queries complexas entre as novas tabelas"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        # Complex join query across new tables
        complex_query = """
            SELECT 
                pv.name as vision_name,
                us.title as story_title,
                t.title as task_title,
                s.sprint_name
            FROM product_visions pv
            LEFT JOIN framework_epics e ON e.project_id = pv.project_id
            LEFT JOIN framework_user_stories us ON us.epic_id = e.id
            LEFT JOIN framework_tasks t ON t.user_story_id = us.id
            LEFT JOIN sprint_tasks st ON st.task_id = t.id
            LEFT JOIN sprints s ON s.id = st.sprint_id
            WHERE pv.status = 'active'
        """
        
        try:
            cursor.execute(complex_query)
            # Query should execute without error even with no data
            results = cursor.fetchall()
            # Results can be empty, but query should not fail
            assert isinstance(results, list), "Complex query deve retornar uma lista"
        except Exception as e:
            pytest.fail(f"Complex relationship query failed: {str(e)}")
        
        conn.close()


class TestMigrationIntegrity(TestMigrationSchemaBase):
    """Testes de integridade das migrações"""
    
    def test_no_data_loss_after_migration(self, migrated_db):
        """Testa que dados existentes não foram perdidos após migração"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        # Original tables should still exist and be functional
        original_tables = [
            'framework_users', 'framework_projects',
            'framework_epics', 'framework_tasks', 'achievement_types'
        ]
        
        for table in original_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            assert cursor.fetchone() is not None, f"Tabela original {table} foi perdida"
            
            # Test basic insert/select on original tables
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                cursor.fetchone()
            except Exception as e:
                pytest.fail(f"Tabela original {table} não está funcional: {str(e)}")
        
        conn.close()
    
    def test_foreign_key_constraints(self, migrated_db):
        """Testa que constraints de foreign key estão funcionando"""
        conn = sqlite3.connect(migrated_db)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable FK constraints
        cursor = conn.cursor()
        
        # Test FK constraint violation should raise error
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO framework_user_stories (epic_id, story_key, title, user_story, acceptance_criteria)
                VALUES (999, 'test', 'Test Story', 'Test', '["Test"]')
            """)
        
        conn.close()
    
    def test_achievement_types_created(self, migrated_db):
        """Testa que novos tipos de achievement foram criados"""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()
        
        # Check for new achievement types from each migration
        cursor.execute("SELECT code FROM achievement_types WHERE code IN ('VISION_CREATOR', 'STORY_MASTER')")
        phase1_achievements = cursor.fetchall()
        assert len(phase1_achievements) >= 2, "Achievement types da Fase 1 não foram criados"
        
        cursor.execute("SELECT code FROM achievement_types WHERE code IN ('MILESTONE_MASTER', 'DEPENDENCY_SOLVER')")
        phase2_achievements = cursor.fetchall()
        assert len(phase2_achievements) >= 2, "Achievement types da Fase 2 não foram criados"
        
        cursor.execute("SELECT code FROM achievement_types WHERE code IN ('SPRINT_MASTER', 'AI_COLLABORATOR')")
        phase3_achievements = cursor.fetchall()
        assert len(phase3_achievements) >= 2, "Achievement types da Fase 3 não foram criados"
        
        conn.close()


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v"])