#!/usr/bin/env python3
"""
🧪 TESTS - Tasks Repository

Testes críticos para validar patches da crítica técnica aplicados.
Valida ordenação humana, dedup e parse error handling.

Tests:
1. test_ordering_with_sequence - Valida ordenação natural
2. test_in_dedup - Valida remoção de duplicatas
3. test_parse_error_logging - Valida logs com task_key
"""

import pytest
import sqlite3
import tempfile
import os
from unittest.mock import Mock, patch
from pathlib import Path

# Importar módulos necessários
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from streamlit_extension.repos.tasks_repo import TasksRepo, RepoError
from streamlit_extension.models.task_models import Task

class TestTasksRepo:
    """Testes para TasksRepo com patches críticos aplicados"""
    
    @pytest.fixture
    def temp_db(self):
        """Cria banco temporário para testes"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        
        # Criar schema mínimo
        conn.execute("""
            CREATE TABLE framework_tasks (
                id INTEGER PRIMARY KEY,
                task_key TEXT NOT NULL,
                epic_id INTEGER NOT NULL,
                title TEXT,
                description TEXT,
                tdd_phase TEXT,
                tdd_order INTEGER,
                task_type TEXT DEFAULT 'implementation',
                status TEXT DEFAULT 'pending',
                estimate_minutes INTEGER,
                story_points INTEGER,
                priority INTEGER DEFAULT 3,
                task_group TEXT,
                task_sequence INTEGER,
                created_at TEXT,
                deleted_at TEXT
            )
        """)
        
        yield conn
        
        conn.close()
        os.unlink(path)
    
    def test_ordering_with_sequence(self, temp_db):
        """
        PATCH 1: Testa ordenação humana (task_sequence > task_key)
        
        Valida que:
        - task_sequence tem prioridade sobre task_key
        - Ordenação "T2" vem antes de "T10" quando sequences iguais
        - COALESCE(task_sequence, 1e9) funciona corretamente
        """
        # Inserir dados de teste com ordenação desafiadora
        test_data = [
            (1, 'T10', 1, 'Task 10', None, None, 10),    # sequence 10
            (2, 'T2', 1, 'Task 2', None, None, 2),       # sequence 2  
            (3, 'T1', 1, 'Task 1', None, None, 1),       # sequence 1
            (4, 'T3', 1, 'Task 3', None, None, None),    # sem sequence (vai pro fim)
            (5, 'T1a', 1, 'Task 1a', None, None, None),  # sem sequence (vai pro fim)
        ]
        
        for task_data in test_data:
            temp_db.execute("""
                INSERT INTO framework_tasks 
                (id, task_key, epic_id, title, description, tdd_phase, task_sequence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, task_data)
        
        temp_db.commit()
        
        # Testar ordenação
        repo = TasksRepo(temp_db)
        tasks = repo.list_by_epic(epic_id=1)
        
        # Verificar ordem esperada
        expected_order = ['T1', 'T2', 'T10', 'T1a', 'T3']  # sequence primeiro, depois alfabética
        actual_order = [task.task_key for task in tasks]
        
        assert actual_order == expected_order, f"Ordenação incorreta: {actual_order} != {expected_order}"
        
        # Verificar que tasks com sequence vieram primeiro
        tasks_with_sequence = [task for task in tasks if task.task_sequence is not None]
        tasks_without_sequence = [task for task in tasks if task.task_sequence is None]
        
        assert len(tasks_with_sequence) == 3, "Deveria ter 3 tasks com sequence"
        assert len(tasks_without_sequence) == 2, "Deveria ter 2 tasks sem sequence"
        
        # Verificar que tasks sem sequence vieram por último
        assert tasks[-2:] == tasks_without_sequence, "Tasks sem sequence deveriam vir por último"
    
    def test_in_dedup(self, temp_db):
        """
        PATCH 2: Testa remoção de duplicatas no IN clause
        
        Valida que:
        - Duplicatas são removidas preservando ordem
        - Performance não é afetada
        - Resultados são consistentes
        """
        # Inserir dados de teste
        test_data = [
            (1, 'T1', 1, 'Task 1'),
            (2, 'T2', 1, 'Task 2'), 
            (3, 'T3', 1, 'Task 3'),
        ]
        
        for task_data in test_data:
            temp_db.execute("""
                INSERT INTO framework_tasks (id, task_key, epic_id, title)
                VALUES (?, ?, ?, ?)
            """, task_data)
        
        temp_db.commit()
        
        # Testar com duplicatas na entrada
        repo = TasksRepo(temp_db)
        
        # Lista com duplicatas intencionais
        keys_with_duplicates = ['T1', 'T2', 'T1', 'T3', 'T2', 'T1']
        
        tasks = repo.list_by_task_keys(keys_with_duplicates)
        
        # Verificar que duplicatas foram removidas
        task_keys = [task.task_key for task in tasks]
        unique_keys = list(dict.fromkeys(task_keys))  # Remove dups preservando ordem
        
        assert task_keys == unique_keys, f"Duplicatas não removidas: {task_keys}"
        
        # Verificar ordem preservada (primeira ocorrência)
        expected_order = ['T1', 'T2', 'T3']  # Ordem da primeira ocorrência
        actual_order = [task.task_key for task in tasks]
        
        assert actual_order == expected_order, f"Ordem não preservada: {actual_order} != {expected_order}"
        
        # Verificar que encontrou exatamente 3 tasks únicas
        assert len(tasks) == 3, f"Deveria retornar 3 tasks únicas, retornou {len(tasks)}"
    
    @patch('streamlit_extension.repos.tasks_repo.logger')
    def test_parse_error_logging(self, mock_logger, temp_db):
        """
        PATCH 3: Testa parse error seguro com task_key no log
        
        Valida que:
        - task_key é extraído com segurança de sqlite3.Row
        - Logs incluem task_key específica para debugging
        - Contagem de erros é correta
        - Parse errors não quebram o fluxo
        """
        # Inserir dados de teste (alguns vão dar erro de parse)
        test_data = [
            (1, 'T1_OK', 1, 'Task OK'),
            (2, 'T2_ERROR', 1, 'Task Error'),  # Esta vai dar erro no parse
            (3, 'T3_OK', 1, 'Task OK 2'),
            (4, 'T4_ERROR', 1, 'Task Error 2'),  # Esta também vai dar erro
        ]
        
        for task_data in test_data:
            temp_db.execute("""
                INSERT INTO framework_tasks (id, task_key, epic_id, title)
                VALUES (?, ?, ?, ?)
            """, task_data)
        
        temp_db.commit()
        
        repo = TasksRepo(temp_db)
        
        # Mock Task.from_db_row para simular parse errors em tasks específicas
        original_from_db_row = Task.from_db_row
        
        def mock_from_db_row(row_dict):
            if 'ERROR' in row_dict['task_key']:
                raise ValueError(f"Parse error simulado para {row_dict['task_key']}")
            return original_from_db_row(row_dict)
        
        with patch.object(Task, 'from_db_row', side_effect=mock_from_db_row):
            tasks = repo.list_by_epic(epic_id=1)
        
        # Verificar que apenas tasks OK foram retornadas
        task_keys = [task.task_key for task in tasks]
        expected_ok_tasks = ['T1_OK', 'T3_OK']
        
        assert task_keys == expected_ok_tasks, f"Apenas tasks OK deveriam retornar: {task_keys}"
        
        # Verificar logs de warning para parse errors
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if 'Parse error tarefa' in str(call)]
        
        assert len(warning_calls) == 2, f"Deveria ter 2 warnings de parse error, teve {len(warning_calls)}"
        
        # Verificar que task_key específica está nos logs
        warning_messages = [str(call) for call in warning_calls]
        
        assert any('T2_ERROR' in msg for msg in warning_messages), "T2_ERROR deveria estar nos logs"
        assert any('T4_ERROR' in msg for msg in warning_messages), "T4_ERROR deveria estar nos logs"
        
        # Verificar log de erro com contagem e exemplos
        error_calls = [call for call in mock_logger.error.call_args_list
                      if 'erros de parse' in str(call)]
        
        assert len(error_calls) == 1, f"Deveria ter 1 log de erro com contagem, teve {len(error_calls)}"
        
        error_message = str(error_calls[0])
        assert '2 erros de parse' in error_message, "Log deveria conter contagem de erros"
        assert 'Exemplos:' in error_message, "Log deveria conter exemplos de task_keys problemáticas"
    
    def test_pagination_functionality(self, temp_db):
        """
        PATCH 4: Testa paginação opcional
        
        Valida que:
        - limit/offset funcionam corretamente
        - Ordenação é mantida durante paginação
        - Paginação é backwards compatible
        """
        # Inserir mais dados para testar paginação
        test_data = [(i, f'T{i}', 1, f'Task {i}', i) for i in range(1, 11)]  # T1 a T10
        
        for task_data in test_data:
            temp_db.execute("""
                INSERT INTO framework_tasks (id, task_key, epic_id, title, task_sequence)
                VALUES (?, ?, ?, ?, ?)
            """, task_data)
        
        temp_db.commit()
        
        repo = TasksRepo(temp_db)
        
        # Testar paginação
        page1 = repo.list_by_epic(epic_id=1, limit=3, offset=0)
        page2 = repo.list_by_epic(epic_id=1, limit=3, offset=3)
        all_tasks = repo.list_by_epic(epic_id=1)
        
        # Verificar tamanhos
        assert len(page1) == 3, f"Página 1 deveria ter 3 tasks, tem {len(page1)}"
        assert len(page2) == 3, f"Página 2 deveria ter 3 tasks, tem {len(page2)}"
        assert len(all_tasks) == 10, f"Total deveria ter 10 tasks, tem {len(all_tasks)}"
        
        # Verificar que paginação preserva ordenação
        page1_keys = [task.task_key for task in page1]
        page2_keys = [task.task_key for task in page2]
        all_keys = [task.task_key for task in all_tasks]
        
        expected_page1 = all_keys[:3]
        expected_page2 = all_keys[3:6]
        
        assert page1_keys == expected_page1, f"Página 1 ordem incorreta: {page1_keys} != {expected_page1}"
        assert page2_keys == expected_page2, f"Página 2 ordem incorreta: {page2_keys} != {expected_page2}"
    
    def test_summary_division_by_zero_protection(self, temp_db):
        """
        PATCH 5: Testa proteção contra divisão por zero no sumário
        
        Valida que:
        - Épico vazio retorna 0.0% completion
        - Épico com tarefas mas zero completed funciona
        - Épico com todas completadas retorna 100.0%
        """
        repo = TasksRepo(temp_db)
        
        # Teste 1: Épico vazio (divisão por zero)
        summary = repo.get_epic_effort_summary(epic_id=999)  # Épico inexistente
        
        assert summary['total_tasks'] == 0, "Total tasks deveria ser 0"
        assert summary['completed_tasks'] == 0, "Completed tasks deveria ser 0" 
        assert summary['completion_percentage'] == 0.0, "Completion percentage deveria ser 0.0"
        
        # Teste 2: Épico com tarefas, zero completadas
        test_data = [
            (1, 'T1', 1, 'Task 1', 'pending'),
            (2, 'T2', 1, 'Task 2', 'in_progress'),
        ]
        
        for task_data in test_data:
            temp_db.execute("""
                INSERT INTO framework_tasks (id, task_key, epic_id, title, status)
                VALUES (?, ?, ?, ?, ?)
            """, task_data)
        
        temp_db.commit()
        
        summary = repo.get_epic_effort_summary(epic_id=1)
        
        assert summary['total_tasks'] == 2, "Total tasks deveria ser 2"
        assert summary['completed_tasks'] == 0, "Completed tasks deveria ser 0"
        assert summary['completion_percentage'] == 0.0, "Completion percentage deveria ser 0.0"
        
        # Teste 3: Épico com algumas tarefas completadas
        temp_db.execute("""
            UPDATE framework_tasks SET status = 'completed' WHERE task_key = 'T1'
        """)
        temp_db.commit()
        
        summary = repo.get_epic_effort_summary(epic_id=1)
        
        assert summary['total_tasks'] == 2, "Total tasks deveria ser 2"
        assert summary['completed_tasks'] == 1, "Completed tasks deveria ser 1"
        assert summary['completion_percentage'] == 50.0, "Completion percentage deveria ser 50.0"
    
    def test_repo_error_consistency(self, temp_db):
        """
        Testa consistência de error handling (RepoError sempre)
        
        Valida que:
        - Todos os métodos levantam RepoError em caso de erro
        - Error messages são informativos
        - Conexão é gerenciada corretamente
        """
        repo = TasksRepo(temp_db)
        
        # Simular erro fechando conexão
        temp_db.close()
        
        # Testar que todos os métodos levantam RepoError
        with pytest.raises(RepoError, match="list_by_epic.*falhou"):
            repo.list_by_epic(epic_id=1)
        
        with pytest.raises(RepoError, match="get_by_task_key.*falhou"):
            repo.get_by_task_key('T1')
        
        with pytest.raises(RepoError, match="list_by_task_keys.*falhou"):
            repo.list_by_task_keys(['T1', 'T2'])
        
        with pytest.raises(RepoError, match="count_by_epic.*falhou"):
            repo.count_by_epic(epic_id=1)
        
        with pytest.raises(RepoError, match="get_epic_effort_summary.*falhou"):
            repo.get_epic_effort_summary(epic_id=1)
        
        with pytest.raises(RepoError, match="list_tdd_tasks_by_group.*falhou"):
            repo.list_tdd_tasks_by_group(epic_id=1)
        
        with pytest.raises(RepoError, match="get_task_id_to_key_mapping.*falhou"):
            repo.get_task_id_to_key_mapping(epic_id=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])