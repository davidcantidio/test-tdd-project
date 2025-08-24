#!/usr/bin/env python3
"""
🗃️ MIGRATION - Performance Indexes

Adiciona índices críticos para performance das queries do repository.
Implementação baseada nas recomendações da crítica técnica.

Usage:
    python scripts/migration/add_performance_indexes.py
    
Indexes Added:
- framework_tasks(epic_id, task_key) - composto para queries principais
- framework_tasks(task_key) - único para lookups diretos
- task_dependencies(task_id) - para resolver dependências
- task_dependencies(depends_on_task_key) - para buscar dependentes

Performance Impact:
- Queries 10-100x mais rápidas para épicos grandes
- Eliminação de table scans
- Otimização das JOINs
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path

# Adicionar caminho do projeto
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Legacy import - keeping for hybrid compatibility
from streamlit_extension.utils.database import DatabaseManager  # Legacy compatibility
from streamlit_extension.database import list_epics, list_tasks  # noqa: F401
from streamlit_extension.services import ServiceContainer
# New modular imports for performance
from streamlit_extension.database import get_connection

# Service layer setup for future compatibility
# service_container = ServiceContainer()
# performance_service = service_container.get_performance_service()

logger = logging.getLogger(__name__)

def setup_logging():
    """Configura logging para migração"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def check_index_exists(conn, index_name: str) -> bool:
    """
    Verifica se índice já existe.
    
    Args:
        conn: Database connection
        index_name: Nome do índice
        
    Returns:
        True se índice existe
    """
    query = """
        SELECT name FROM sqlite_master 
        WHERE type='index' AND name=?
    """
    
    result = conn.execute(query, (index_name,)).fetchone()
    return result is not None

def add_performance_indexes(db_manager: DatabaseManager) -> dict:
    """
    Adiciona todos os índices de performance.
    
    Args:
        db_manager: DatabaseManager instance
        
    Returns:
        Dict com resultados da migração
    """
    indexes_to_create = [
        {
            'name': 'idx_tasks_epic_key_composite',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_tasks_epic_key_composite 
                ON framework_tasks(epic_id, task_key)
            ''',
            'description': 'Índice composto para queries por épico'
        },
        {
            'name': 'idx_tasks_key_unique',
            'sql': '''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_key_unique 
                ON framework_tasks(task_key)
            ''',
            'description': 'Índice único para lookups diretos por task_key'
        },
        {
            'name': 'idx_tasks_sequence_order',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_tasks_sequence_order 
                ON framework_tasks(epic_id, task_sequence, task_key)
            ''',
            'description': 'Índice para ordenação humana'
        },
        {
            'name': 'idx_tasks_tdd_groups',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_tasks_tdd_groups 
                ON framework_tasks(epic_id, task_group, tdd_order)
            ''',
            'description': 'Índice para queries de grupos TDD'
        },
        {
            'name': 'idx_td_task_id',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_td_task_id 
                ON task_dependencies(task_id)
            ''',
            'description': 'Índice para dependências por task_id'
        },
        {
            'name': 'idx_td_depends_on_key',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_td_depends_on_key 
                ON task_dependencies(depends_on_task_key)
            ''',
            'description': 'Índice para buscar dependentes de uma tarefa'
        },
        {
            'name': 'idx_tasks_status_filter',
            'sql': '''
                CREATE INDEX IF NOT EXISTS idx_tasks_status_filter 
                ON framework_tasks(epic_id, deleted_at, status)
            ''',
            'description': 'Índice para filtros de status'
        }
    ]
    
    results = {
        'created': [],
        'skipped': [],
        'errors': []
    }
    
    try:
        with get_connection() as conn:  # Direct modular API
            for index_config in indexes_to_create:
                index_name = index_config['name']
                
                logger.info(f"Verificando índice: {index_name}")
                
                # Verificar se já existe
                if check_index_exists(conn, index_name):
                    logger.info(f"  ✓ Índice {index_name} já existe - pulando")
                    results['skipped'].append({
                        'name': index_name,
                        'reason': 'já existe'
                    })
                    continue
                
                # Criar índice
                try:
                    logger.info(f"  📊 Criando índice: {index_name}")
                    logger.info(f"     {index_config['description']}")
                    
                    conn.execute(index_config['sql'])
                    
                    logger.info(f"  ✅ Índice {index_name} criado com sucesso")
                    results['created'].append({
                        'name': index_name,
                        'description': index_config['description']
                    })
                    
                except sqlite3.Error as e:
                    error_msg = f"Erro ao criar índice {index_name}: {e}"
                    logger.error(f"  ❌ {error_msg}")
                    results['errors'].append({
                        'name': index_name,
                        'error': str(e)
                    })
            
            # Commit todas as mudanças
            conn.commit()
            logger.info("✅ Migração de índices concluída com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro durante migração: {e}")
        results['errors'].append({
            'name': 'migration_error',
            'error': str(e)
        })
    
    return results

def analyze_query_performance(db_manager: DatabaseManager):
    """
    Analisa performance das queries principais após criação dos índices.
    
    Args:
        db_manager: DatabaseManager instance
    """
    performance_queries = [
        {
            'name': 'list_by_epic',
            'sql': '''
                EXPLAIN QUERY PLAN
                SELECT id, task_key, epic_id, title, description,
                       tdd_phase, tdd_order, task_type, status,
                       estimate_minutes, story_points, priority,
                       task_group, task_sequence, created_at
                FROM framework_tasks 
                WHERE epic_id = 1 AND deleted_at IS NULL
                ORDER BY COALESCE(task_sequence, 1e9), task_key
            '''
        },
        {
            'name': 'get_by_task_key',
            'sql': '''
                EXPLAIN QUERY PLAN
                SELECT id, task_key, epic_id, title
                FROM framework_tasks 
                WHERE task_key = 'T1.1' AND deleted_at IS NULL
            '''
        },
        {
            'name': 'dependencies_by_epic',
            'sql': '''
                EXPLAIN QUERY PLAN
                SELECT td.id, td.task_id, td.depends_on_task_key,
                       ft.task_key as dependent_task_key
                FROM task_dependencies td
                JOIN framework_tasks ft ON td.task_id = ft.id
                WHERE ft.epic_id = 1
            '''
        }
    ]
    
    logger.info("\n📊 Análise de Performance das Queries:")
    logger.info("=" * 50)
    
    try:
        with get_connection() as conn:  # Direct modular API
            for query_config in performance_queries:
                logger.info(f"\n🔍 Query: {query_config['name']}")
                logger.info("-" * 30)
                
                rows = conn.execute(query_config['sql']).fetchall()
                
                for row in rows:
                    # SQLite EXPLAIN QUERY PLAN retorna: id, parent, notused, detail
                    detail = row[3] if len(row) > 3 else str(row)
                    logger.info(f"  {detail}")
                    
                    # Verificar se está usando índices
                    if 'USING INDEX' in detail:
                        logger.info(f"  ✅ Usando índice otimizado")
                    elif 'SCAN TABLE' in detail:
                        logger.warning(f"  ⚠️ Table scan detectado")
    
    except Exception as e:
        logger.error(f"❌ Erro na análise de performance: {e}")

def main():
    """Função principal da migração"""
    setup_logging()
    
    logger.info("🗃️ Iniciando migração de índices de performance")
    logger.info("=" * 50)
    
    # Configurar caminho do banco
    db_path = project_root / "framework.db"
    
    if not db_path.exists():
        logger.error(f"❌ Banco de dados não encontrado: {db_path}")
        sys.exit(1)
    
    # Executar migração com conexão SQLite direta primeiro
    try:
        # Usar conexão SQLite direta para simplificar
        conn = sqlite3.connect(str(db_path))
        
        results = {
            'created': [],
            'skipped': [],
            'errors': []
        }
        
        indexes_to_create = [
            {
                'name': 'idx_tasks_epic_key_composite',
                'sql': '''
                    CREATE INDEX IF NOT EXISTS idx_tasks_epic_key_composite 
                    ON framework_tasks(epic_id, task_key)
                ''',
                'description': 'Índice composto para queries por épico'
            },
            {
                'name': 'idx_tasks_key_unique',
                'sql': '''
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_key_unique 
                    ON framework_tasks(task_key)
                ''',
                'description': 'Índice único para lookups diretos por task_key'
            },
            {
                'name': 'idx_tasks_sequence_order',
                'sql': '''
                    CREATE INDEX IF NOT EXISTS idx_tasks_sequence_order 
                    ON framework_tasks(epic_id, task_sequence, task_key)
                ''',
                'description': 'Índice para ordenação humana'
            },
            {
                'name': 'idx_td_task_id',
                'sql': '''
                    CREATE INDEX IF NOT EXISTS idx_td_task_id 
                    ON task_dependencies(task_id)
                ''',
                'description': 'Índice para dependências por task_id'
            },
            {
                'name': 'idx_td_depends_on_key',
                'sql': '''
                    CREATE INDEX IF NOT EXISTS idx_td_depends_on_key 
                    ON task_dependencies(depends_on_task_key)
                ''',
                'description': 'Índice para buscar dependentes de uma tarefa'
            }
        ]
        
        # Criar índices
        for index_config in indexes_to_create:
            index_name = index_config['name']
            
            logger.info(f"Verificando índice: {index_name}")
            
            # Verificar se já existe
            if check_index_exists(conn, index_name):
                logger.info(f"  ✓ Índice {index_name} já existe - pulando")
                results['skipped'].append({
                    'name': index_name,
                    'reason': 'já existe'
                })
                continue
            
            # Criar índice
            try:
                logger.info(f"  📊 Criando índice: {index_name}")
                logger.info(f"     {index_config['description']}")
                
                conn.execute(index_config['sql'])
                
                logger.info(f"  ✅ Índice {index_name} criado com sucesso")
                results['created'].append({
                    'name': index_name,
                    'description': index_config['description']
                })
                
            except sqlite3.Error as e:
                error_msg = f"Erro ao criar índice {index_name}: {e}"
                logger.error(f"  ❌ {error_msg}")
                results['errors'].append({
                    'name': index_name,
                    'error': str(e)
                })
        
        # Commit mudanças
        conn.commit()
        conn.close()
        
        # Relatório de resultados
        logger.info("\n📋 Relatório da Migração:")
        logger.info("=" * 30)
        
        if results['created']:
            logger.info(f"✅ Índices criados: {len(results['created'])}")
            for item in results['created']:
                logger.info(f"  - {item['name']}: {item['description']}")
        
        if results['skipped']:
            logger.info(f"⏭️ Índices pulados: {len(results['skipped'])}")
            for item in results['skipped']:
                logger.info(f"  - {item['name']}: {item['reason']}")
        
        if results['errors']:
            logger.error(f"❌ Erros: {len(results['errors'])}")
            for item in results['errors']:
                logger.error(f"  - {item['name']}: {item['error']}")
        
        logger.info(f"\n🎯 Migração concluída!")
        
        # Status final
        if results['errors']:
            logger.error("⚠️ Migração concluída com erros")
            sys.exit(1)
        else:
            logger.info("✅ Migração concluída com sucesso")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"❌ Erro fatal na migração: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
