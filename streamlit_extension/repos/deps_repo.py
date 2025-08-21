#!/usr/bin/env python3
"""
🔧 REPOS - Dependencies Repository

Repository pattern para acesso a dados de dependências entre tarefas.
Implementação limpa seguindo os mesmos padrões do tasks_repo.py.

Usage:
    from streamlit_extension.repos import DepsRepo, RepoError
    
    repo = DepsRepo(connection)
    deps = repo.list_by_epic(epic_id=1)
    
Features:
- ✅ JOIN para trazer dependent_task_key (simplifica adjacency building)
- ✅ Error handling consistente (RepoError)
- ✅ Performance otimizada (BASE_FIELDS, chunking)
- ✅ Parse error seguro com contexto
- ✅ Paginação opcional
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
import logging

from ..models.task_models import TaskDependency
from ..utils.db import dict_rows
from .tasks_repo import RepoError
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


logger = logging.getLogger(__name__)

# 🔧 DRY: Campos base alinhados com TaskDependency dataclass + dependent_task_key
DEPS_BASE_FIELDS = """
    td.id, td.task_id, td.depends_on_task_key,
    td.depends_on_task_id, td.dependency_type,
    td.created_at, td.updated_at,
    ft.task_key as dependent_task_key
"""

class DepsRepo:
    # Delegation to DepsRepoDataaccess
    def __init__(self):
        self._depsrepodataaccess = DepsRepoDataaccess()
    # Delegation to DepsRepoLogging
    def __init__(self):
        self._depsrepologging = DepsRepoLogging()
    # Delegation to DepsRepoErrorhandling
    def __init__(self):
        self._depsrepoerrorhandling = DepsRepoErrorhandling()
    # Delegation to DepsRepoNetworking
    def __init__(self):
        self._depsreponetworking = DepsRepoNetworking()
    # Delegation to DepsRepoCalculation
    def __init__(self):
        self._depsrepocalculation = DepsRepoCalculation()
    # Delegation to DepsRepoFormatting
    def __init__(self):
        self._depsrepoformatting = DepsRepoFormatting()
    # Delegation to DepsRepoBusinesslogic
    def __init__(self):
        self._depsrepobusinesslogic = DepsRepoBusinesslogic()
    # Delegation to DepsRepoValidation
    def __init__(self):
        self._depsrepovalidation = DepsRepoValidation()
    """Repository para operações CRUD de dependências entre tarefas"""
    
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
    ) -> List[TaskDependency]:
        """
        Lista todas as dependências das tarefas de um épico.
        
        Args:
            epic_id: ID do épico
            limit: Número máximo de dependências (None = todas)
            offset: Número de dependências para pular
            
        Returns:
            Lista de dependências ordenadas por ID
            
        Raises:
            RepoError: Em caso de erro na query ou parsing
        """
        base_sql = f"""
            SELECT {DEPS_BASE_FIELDS}
            FROM task_dependencies td
            JOIN framework_tasks ft ON td.task_id = ft.id
            WHERE ft.epic_id = ?
            ORDER BY td.id
        """
        
        # Paginação opcional
        sql = base_sql + (" LIMIT ? OFFSET ?" if limit is not None else "")
        params = (epic_id,) if limit is None else (epic_id, limit, offset)
        
        try:
            with dict_rows(self.conn):
                rows = self.conn.execute(sql, params).fetchall()
            
            dependencies = []
            parse_errors = 0
            error_examples = []
            
            for row in rows:
                try:
                    # Converter row para dict e criar TaskDependency
                    row_dict = dict(row)
                    # dependent_task_key não faz parte do TaskDependency model,
                    # mas é útil para building adjacency graphs
                    dep = TaskDependency.from_db_row(row_dict)
                    
                    # Adicionar dependent_task_key como atributo extra se necessário
                    dep.dependent_task_key = row_dict.get('dependent_task_key')
                    
                    dependencies.append(dep)
                except Exception as e:
                    # Parse error seguro
                    row_dict = dict(row)
                    dep_id = row_dict.get('id', 'unknown')
                    depends_on = row_dict.get('depends_on_task_key', 'unknown')
                    logger.warning(f"Parse error dependência {dep_id} ({depends_on}): {e}", exc_info=True)
                    
                    parse_errors += 1
                    if len(error_examples) < 3:
                        error_examples.append(f"{dep_id}({depends_on})")
            
            if parse_errors > 0:
                examples_str = ", ".join(error_examples)
                logger.error(f"list_by_epic({epic_id}): {parse_errors} erros de parse. Exemplos: {examples_str}")
            
            logger.info(f"Carregadas {len(dependencies)} dependências do épico {epic_id}")
            return dependencies
            
        except Exception as e:
            raise RepoError(f"list_by_epic({epic_id}) falhou: {e}") from e
    
    def list_by_task_id(self, task_id: int) -> List[TaskDependency]:
        """
        Lista dependências de uma tarefa específica.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Lista de dependências da tarefa
            
        Raises:
            RepoError: Em caso de erro na query
        """
        sql = f"""
            SELECT {DEPS_BASE_FIELDS}
            FROM task_dependencies td
            JOIN framework_tasks ft ON td.task_id = ft.id
            WHERE td.task_id = ?
            ORDER BY td.id
        """
        
        try:
            with dict_rows(self.conn):
                rows = self.conn.execute(sql, (task_id,)).fetchall()
            
            dependencies = []
            parse_errors = 0
            
            for row in rows:
                try:
                    row_dict = dict(row)
                    dep = TaskDependency.from_db_row(row_dict)
                    dep.dependent_task_key = row_dict.get('dependent_task_key')
                    dependencies.append(dep)
                except Exception as e:
                    row_dict = dict(row)
                    dep_id = row_dict.get('id', 'unknown')
                    logger.warning(f"Parse error dependência {dep_id}: {e}", exc_info=True)
                    parse_errors += 1
            
            if parse_errors > 0:
                logger.error(f"list_by_task_id({task_id}): {parse_errors} erros de parse")
            
            return dependencies
            
        except Exception as e:
            raise RepoError(f"list_by_task_id({task_id}) falhou: {e}") from e
    
    def list_by_depends_on_task_key(self, depends_on_task_key: str) -> List[TaskDependency]:
        """
        Lista todas as tarefas que dependem de uma tarefa específica.
        
        Args:
            depends_on_task_key: Task key da qual outras dependem
            
        Returns:
            Lista de dependências que apontam para esta tarefa
            
        Raises:
            RepoError: Em caso de erro na query
        """
        sql = f"""
            SELECT {DEPS_BASE_FIELDS}
            FROM task_dependencies td
            JOIN framework_tasks ft ON td.task_id = ft.id
            WHERE td.depends_on_task_key = ?
            ORDER BY td.id
        """
        
        try:
            with dict_rows(self.conn):
                rows = self.conn.execute(sql, (depends_on_task_key,)).fetchall()
            
            dependencies = []
            parse_errors = 0
            
            for row in rows:
                try:
                    row_dict = dict(row)
                    dep = TaskDependency.from_db_row(row_dict)
                    dep.dependent_task_key = row_dict.get('dependent_task_key')
                    dependencies.append(dep)
                except Exception as e:
                    row_dict = dict(row)
                    dep_id = row_dict.get('id', 'unknown')
                    logger.warning(f"Parse error dependência {dep_id}: {e}", exc_info=True)
                    parse_errors += 1
            
            if parse_errors > 0:
                logger.error(f"list_by_depends_on_task_key({depends_on_task_key}): {parse_errors} erros de parse")
            
            return dependencies
            
        except Exception as e:
            raise RepoError(f"list_by_depends_on_task_key({depends_on_task_key}) falhou: {e}") from e
    
    def get_epic_dependency_summary(self, epic_id: int) -> Dict[str, Any]:
        """
        Retorna sumário de dependências do épico.
        
        Args:
            epic_id: ID do épico
            
        Returns:
            Dict com métricas de dependências
            
        Raises:
            RepoError: Em caso de erro na query
        """
        sql = """
            SELECT 
                COUNT(*) as total_dependencies,
                COUNT(DISTINCT td.task_id) as tasks_with_dependencies,
                COUNT(DISTINCT td.depends_on_task_key) as tasks_as_prerequisites,
                SUM(CASE WHEN td.dependency_type = 'blocking' THEN 1 ELSE 0 END) as blocking_dependencies,
                SUM(CASE WHEN td.dependency_type = 'tdd_sequence' THEN 1 ELSE 0 END) as tdd_dependencies,
                AVG(deps_per_task.dep_count) as avg_dependencies_per_task
            FROM task_dependencies td
            JOIN framework_tasks ft ON td.task_id = ft.id
            LEFT JOIN (
                SELECT task_id, COUNT(*) as dep_count
                FROM task_dependencies td2
                JOIN framework_tasks ft2 ON td2.task_id = ft2.id
                WHERE ft2.epic_id = ?
                GROUP BY task_id
            ) deps_per_task ON td.task_id = deps_per_task.task_id
            WHERE ft.epic_id = ?
        """
        
        try:
            with dict_rows(self.conn):
                row = self.conn.execute(sql, (epic_id, epic_id)).fetchone()
            
            if row:
                return {
                    'total_dependencies': row['total_dependencies'] or 0,
                    'tasks_with_dependencies': row['tasks_with_dependencies'] or 0,
                    'tasks_as_prerequisites': row['tasks_as_prerequisites'] or 0,
                    'blocking_dependencies': row['blocking_dependencies'] or 0,
                    'tdd_dependencies': row['tdd_dependencies'] or 0,
                    'avg_dependencies_per_task': round(row['avg_dependencies_per_task'] or 0.0, 1)
                }
            
            # Fallback para épico sem dependências
            return {
                'total_dependencies': 0,
                'tasks_with_dependencies': 0,
                'tasks_as_prerequisites': 0,
                'blocking_dependencies': 0,
                'tdd_dependencies': 0,
                'avg_dependencies_per_task': 0.0
            }
            
        except Exception as e:
            raise RepoError(f"get_epic_dependency_summary({epic_id}) falhou: {e}") from e
    
    def count_by_epic(self, epic_id: int) -> int:
        """
        Conta número de dependências no épico.
        
        Args:
            epic_id: ID do épico
            
        Returns:
            Número de dependências
            
        Raises:
            RepoError: Em caso de erro na query
        """
        sql = """
            SELECT COUNT(*) as count
            FROM task_dependencies td
            JOIN framework_tasks ft ON td.task_id = ft.id
            WHERE ft.epic_id = ?
        """
        
        try:
            with dict_rows(self.conn):
                row = self.conn.execute(sql, (epic_id,)).fetchone()
            
            return row['count'] if row else 0
            
        except Exception as e:
            raise RepoError(f"count_by_epic({epic_id}) falhou: {e}") from e
    
    def validate_epic_references(self, epic_id: int) -> Dict[str, Any]:
        """
        Valida integridade referencial das dependências do épico.
        
        Args:
            epic_id: ID do épico
            
        Returns:
            Dict com resultados da validação
            
        Raises:
            RepoError: Em caso de erro na query
        """
        # Buscar dependências órfãs (depends_on_task_key não existe)
        orphan_sql = """
            SELECT DISTINCT td.depends_on_task_key
            FROM task_dependencies td
            JOIN framework_tasks ft ON td.task_id = ft.id
            LEFT JOIN framework_tasks ft_dep ON td.depends_on_task_key = ft_dep.task_key 
                AND ft_dep.deleted_at IS NULL
            WHERE ft.epic_id = ? AND ft_dep.task_key IS NULL
        """
        
        # Buscar self-references (tarefa depende de si mesma)
        self_ref_sql = """
            SELECT td.id, td.depends_on_task_key, ft.task_key
            FROM task_dependencies td
            JOIN framework_tasks ft ON td.task_id = ft.id
            WHERE ft.epic_id = ? AND td.depends_on_task_key = ft.task_key
        """
        
        try:
            with dict_rows(self.conn):
                # Verificar órfãs
                orphan_rows = self.conn.execute(orphan_sql, (epic_id,)).fetchall()
                orphan_keys = [row['depends_on_task_key'] for row in orphan_rows]
                
                # Verificar self-references
                self_ref_rows = self.conn.execute(self_ref_sql, (epic_id,)).fetchall()
                self_refs = [
                    {'id': row['id'], 'task_key': row['task_key']}
                    for row in self_ref_rows
                ]
                
                return {
                    'orphan_dependencies': orphan_keys,
                    'self_references': self_refs,
                    'orphan_count': len(orphan_keys),
                    'self_ref_count': len(self_refs),
                    'has_issues': len(orphan_keys) > 0 or len(self_refs) > 0
                }
            
        except Exception as e:
            raise RepoError(f"validate_epic_references({epic_id}) falhou: {e}") from e