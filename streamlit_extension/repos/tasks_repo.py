#!/usr/bin/env python3
"""
🔧 REPOS - Tasks Repository

Repository pattern com patches críticos aplicados.
Implementação production-ready baseada na crítica técnica.

Usage:
    from streamlit_extension.repos.tasks_repo import TasksRepo, RepoError
    
    repo = TasksRepo(connection)
    tasks = repo.list_by_epic(epic_id=1, limit=100)
    
Features:
- ✅ Ordenação humana (task_sequence > task_key)
- ✅ Dedup no IN (remove duplicatas preservando ordem)
- ✅ Parse error seguro (task_key sempre disponível)
- ✅ Paginação opcional (limit/offset)
- ✅ Sumário robusto (divisão por zero protegida)
- ✅ Error handling consistente (RepoError)
- ✅ Performance otimizada (BASE_FIELDS, chunking)
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from collections import defaultdict
import logging

from ..models.task_models import Task, TaskModelError
from ..utils.db import dict_rows

logger = logging.getLogger(__name__)

# 🔧 DRY: Campos base alinhados com Task dataclass
BASE_FIELDS = """
    id, task_key, epic_id, title, description,
    tdd_phase, tdd_order, task_type, status,
    estimate_minutes, story_points, priority,
    task_group, task_sequence, created_at
"""

class RepoError(TaskModelError):
    """Exception específica para erros de repository"""
    pass

class TasksRepo:
    """Repository para operações CRUD de tarefas com patches críticos"""
    
    def __init__(self, connection):
        """
        Args:
            connection: SQLite connection object
        """
        self.conn = connection
    
    def list_by_epic(
        self, 
        epic_id: int, 
        limit: Optional[int] = None, 
        offset: int = 0
    ) -> List[Task]:
        """
        Lista tarefas de um épico com ordenação humana e paginação.
        
        PATCH 1: Ordenação humana (task_sequence > task_key)
        PATCH 4: Paginação opcional (limit/offset)
        
        Args:
            epic_id: ID do épico
            limit: Número máximo de tarefas (None = todas)
            offset: Número de tarefas para pular (paginação)
            
        Returns:
            Lista de tarefas ordenadas naturalmente
            
        Raises:
            RepoError: Em caso de erro na query ou parsing
        """
        base_sql = f"""
            SELECT {BASE_FIELDS} 
            FROM framework_tasks 
            WHERE epic_id = ? AND deleted_at IS NULL
            ORDER BY COALESCE(task_sequence, 1e9), task_key
        """
        
        # PATCH 4: Paginação opcional
        sql = base_sql + (" LIMIT ? OFFSET ?" if limit is not None else "")
        params = (epic_id,) if limit is None else (epic_id, limit, offset)
        
        try:
            with dict_rows(self.conn):
                rows = self.conn.execute(sql, params).fetchall()
            
            tasks = []
            parse_errors = 0
            error_examples = []
            
            for row in rows:
                try:
                    task = Task.from_db_row(dict(row))
                    tasks.append(task)
                except Exception as e:
                    # PATCH 3: task_key seguro em parse errors
                    row_dict = dict(row)
                    task_key = row_dict.get('task_key', 'unknown')
                    logger.warning(f"Parse error tarefa {task_key}: {e}")
                    
                    parse_errors += 1
                    if len(error_examples) < 3:  # Até 3 exemplos para debugging
                        error_examples.append(task_key)
            
            if parse_errors > 0:
                examples_str = ", ".join(error_examples)
                logger.error(f"list_by_epic({epic_id}): {parse_errors} erros de parse. Exemplos: {examples_str}")
            
            logger.info(f"Carregadas {len(tasks)} tarefas do épico {epic_id}")
            return tasks
            
        except Exception as e:
            raise RepoError(f"list_by_epic({epic_id}) falhou: {e}") from e
    
    def get_by_task_key(self, task_key: str) -> Optional[Task]:
        """
        Busca tarefa por task_key.
        
        Args:
            task_key: Chave única da tarefa
            
        Returns:
            Task object ou None se não encontrada
            
        Raises:
            RepoError: Em caso de erro na query
        """
        sql = f"""
            SELECT {BASE_FIELDS} 
            FROM framework_tasks 
            WHERE task_key = ? AND deleted_at IS NULL
        """
        
        try:
            with dict_rows(self.conn):
                row = self.conn.execute(sql, (task_key,)).fetchone()
            
            if row:
                return Task.from_db_row(dict(row))
            return None
            
        except Exception as e:
            raise RepoError(f"get_by_task_key({task_key}) falhou: {e}") from e
    
    def list_by_task_keys(self, task_keys: List[str]) -> List[Task]:
        """
        Lista tarefas por múltiplas task_keys com dedup e chunking.
        
        PATCH 2: Dedup no IN (remove duplicatas preservando ordem)
        
        Args:
            task_keys: Lista de chaves de tarefas
            
        Returns:
            Lista de tarefas encontradas (sem duplicatas)
            
        Raises:
            RepoError: Em caso de erro na query
        """
        if not task_keys:
            return []
        
        # PATCH 2: Remove duplicatas preservando ordem
        seen = set()
        unique_keys = []
        for key in task_keys:
            if key not in seen:
                seen.add(key)
                unique_keys.append(key)
        
        CHUNK_SIZE = 900  # SQLite limit ~999 parâmetros
        tasks = []
        parse_errors = 0
        error_examples = []
        
        try:
            with dict_rows(self.conn):
                for i in range(0, len(unique_keys), CHUNK_SIZE):
                    chunk = unique_keys[i:i + CHUNK_SIZE]
                    placeholders = ",".join("?" * len(chunk))
                    
                    sql = f"""
                        SELECT {BASE_FIELDS} 
                        FROM framework_tasks 
                        WHERE task_key IN ({placeholders}) AND deleted_at IS NULL
                        ORDER BY COALESCE(task_sequence, 1e9), task_key
                    """
                    
                    rows = self.conn.execute(sql, chunk).fetchall()
                    
                    for row in rows:
                        try:
                            task = Task.from_db_row(dict(row))
                            tasks.append(task)
                        except Exception as e:
                            # PATCH 3: task_key seguro em parse errors
                            row_dict = dict(row)
                            task_key = row_dict.get('task_key', 'unknown')
                            logger.warning(f"Parse error tarefa {task_key}: {e}")
                            
                            parse_errors += 1
                            if len(error_examples) < 3:
                                error_examples.append(task_key)
            
            if parse_errors > 0:
                examples_str = ", ".join(error_examples)
                logger.error(f"list_by_task_keys({len(task_keys)} keys): {parse_errors} erros de parse. Exemplos: {examples_str}")
            
            return tasks
            
        except Exception as e:
            raise RepoError(f"list_by_task_keys({len(task_keys)} keys) falhou: {e}") from e
    
    def list_tdd_tasks_by_group(self, epic_id: int) -> Dict[str, List[Task]]:
        """
        Lista tarefas TDD agrupadas por task_group com ordenação natural.
        
        Args:
            epic_id: ID do épico
            
        Returns:
            Dict {task_group: [tasks]} ordenadas por tdd_order
            
        Raises:
            RepoError: Em caso de erro na query
        """
        sql = f"""
            SELECT {BASE_FIELDS}
            FROM framework_tasks
            WHERE epic_id = ? AND deleted_at IS NULL
              AND task_group IS NOT NULL AND tdd_order IS NOT NULL
            ORDER BY task_group, tdd_order
        """
        
        try:
            with dict_rows(self.conn):
                rows = self.conn.execute(sql, (epic_id,)).fetchall()
            
            groups = defaultdict(list)
            parse_errors = 0
            error_examples = []
            
            for row in rows:
                try:
                    task = Task.from_db_row(dict(row))
                    groups[task.task_group].append(task)
                except Exception as e:
                    # PATCH 3: task_key seguro em parse errors
                    row_dict = dict(row)
                    task_key = row_dict.get('task_key', 'unknown')
                    logger.warning(f"Parse error tarefa TDD {task_key}: {e}")
                    
                    parse_errors += 1
                    if len(error_examples) < 3:
                        error_examples.append(task_key)
            
            # Garantir ordenação por tdd_order (reforço da ORDER BY)
            for group in groups:
                groups[group].sort(key=lambda t: t.tdd_order or 0)
            
            if parse_errors > 0:
                examples_str = ", ".join(error_examples)
                logger.error(f"list_tdd_tasks_by_group({epic_id}): {parse_errors} erros de parse. Exemplos: {examples_str}")
            
            logger.info(f"Carregados {len(groups)} grupos TDD do épico {epic_id}")
            return dict(groups)
            
        except Exception as e:
            raise RepoError(f"list_tdd_tasks_by_group({epic_id}) falhou: {e}") from e
    
    def get_task_id_to_key_mapping(self, epic_id: int) -> Dict[int, str]:
        """
        Retorna mapeamento task_id -> task_key para épico.
        
        Args:
            epic_id: ID do épico
            
        Returns:
            Dict {task_id: task_key}
            
        Raises:
            RepoError: Em caso de erro na query
        """
        sql = """
            SELECT id, task_key
            FROM framework_tasks 
            WHERE epic_id = ? AND deleted_at IS NULL
        """
        
        try:
            with dict_rows(self.conn):
                rows = self.conn.execute(sql, (epic_id,)).fetchall()
            
            mapping = {}
            for row in rows:
                mapping[row['id']] = row['task_key']
            
            return mapping
            
        except Exception as e:
            raise RepoError(f"get_task_id_to_key_mapping({epic_id}) falhou: {e}") from e
    
    def count_by_epic(self, epic_id: int) -> int:
        """
        Conta número de tarefas ativas no épico.
        
        Args:
            epic_id: ID do épico
            
        Returns:
            Número de tarefas
            
        Raises:
            RepoError: Em caso de erro na query
        """
        sql = """
            SELECT COUNT(*) as count
            FROM framework_tasks 
            WHERE epic_id = ? AND deleted_at IS NULL
        """
        
        try:
            with dict_rows(self.conn):
                row = self.conn.execute(sql, (epic_id,)).fetchone()
            
            return row['count'] if row else 0
            
        except Exception as e:
            raise RepoError(f"count_by_epic({epic_id}) falhou: {e}") from e
    
    def get_epic_effort_summary(self, epic_id: int) -> Dict[str, Any]:
        """
        Retorna sumário de esforço do épico com proteção contra divisão por zero.
        
        PATCH 5: Sumário robusto (divisão por zero protegida)
        
        Args:
            epic_id: ID do épico
            
        Returns:
            Dict com métricas de esforço
            
        Raises:
            RepoError: Em caso de erro na query
        """
        sql = """
            SELECT 
                COUNT(*) as total_tasks,
                COALESCE(SUM(estimate_minutes), 0) as total_estimate_minutes,
                COALESCE(SUM(story_points), 0) as total_story_points,
                AVG(COALESCE(priority, 3)) as avg_priority,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN tdd_order IS NOT NULL THEN 1 ELSE 0 END) as tdd_tasks
            FROM framework_tasks 
            WHERE epic_id = ? AND deleted_at IS NULL
        """
        
        try:
            with dict_rows(self.conn):
                row = self.conn.execute(sql, (epic_id,)).fetchone()
            
            if row:
                total_tasks = row['total_tasks'] or 0
                completed_tasks = row['completed_tasks'] or 0
                
                # PATCH 5: Proteção contra divisão por zero
                completion_percentage = round(
                    (completed_tasks / total_tasks * 100), 1
                ) if total_tasks > 0 else 0.0
                
                return {
                    'total_tasks': total_tasks,
                    'total_estimate_minutes': row['total_estimate_minutes'] or 0,
                    'total_story_points': row['total_story_points'] or 0,
                    'avg_priority': round(row['avg_priority'] or 3.0, 1),
                    'completed_tasks': completed_tasks,
                    'tdd_tasks': row['tdd_tasks'] or 0,
                    'completion_percentage': completion_percentage
                }
            
            # Fallback para épico vazio
            return {
                'total_tasks': 0,
                'total_estimate_minutes': 0,
                'total_story_points': 0,
                'avg_priority': 3.0,
                'completed_tasks': 0,
                'tdd_tasks': 0,
                'completion_percentage': 0.0
            }
            
        except Exception as e:
            raise RepoError(f"get_epic_effort_summary({epic_id}) falhou: {e}") from e