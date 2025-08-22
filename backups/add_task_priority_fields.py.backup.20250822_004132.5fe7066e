#!/usr/bin/env python3
"""
🔧 MIGRATION - Add Task Priority Fields

Adiciona campos necessários para sistema de ordenação topológica e priorização.
Verifica existência antes de adicionar (SQLite safe).

Usage:
    python scripts/migration/add_task_priority_fields.py

Features:
- Verificação de campos existentes antes de adicionar
- Migração de dados existentes (tdd_phase → tdd_order)
- Criação de índices otimizados
- Rollback seguro em caso de erro
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskFieldsMigration:
    """Migração para adicionar campos de priorização de tarefas"""
    
    def __init__(self, db_path: str = "framework.db"):
        self.db_path = db_path
        self.conn = None
        self.backup_conn = None
        
    def connect(self):
        """Conecta ao banco com row_factory configurado"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        
    def disconnect(self):
        """Fecha conexões"""
        if self.conn:
            self.conn.close()
        if self.backup_conn:
            self.backup_conn.close()
            
    def create_backup(self) -> str:
        """Cria backup do banco antes da migração"""
        backup_path = f"framework_backup_before_priority_migration.db"
        
        try:
            # Criar backup usando SQLite backup API
            backup_conn = sqlite3.connect(backup_path)
            self.conn.backup(backup_conn)
            backup_conn.close()
            
            logger.info(f"✅ Backup criado: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            raise
    
    def check_column_exists(self, table: str, column: str) -> bool:
        """Verifica se coluna existe na tabela"""
        try:
            cursor = self.conn.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            return column in columns
        except Exception as e:
            logger.error(f"❌ Erro ao verificar coluna {column}: {e}")
            return False
    
    def get_table_info(self, table: str) -> List[Dict]:
        """Retorna informações das colunas da tabela"""
        cursor = self.conn.execute(f"PRAGMA table_info({table})")
        return [dict(row) for row in cursor.fetchall()]
    
    def add_new_columns(self):
        """Adiciona novas colunas necessárias"""
        table = "framework_tasks"
        
        new_columns = [
            ("tdd_order", "INTEGER DEFAULT NULL"),
            ("task_type", "VARCHAR(20) DEFAULT 'implementation'"),
            ("priority", "INTEGER DEFAULT 3"),
            ("task_group", "VARCHAR(50) DEFAULT NULL"),
            ("task_sequence", "INTEGER DEFAULT NULL"),
        ]
        
        for column_name, column_def in new_columns:
            if not self.check_column_exists(table, column_name):
                try:
                    sql = f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}"
                    self.conn.execute(sql)
                    logger.info(f"✅ Coluna adicionada: {column_name}")
                except Exception as e:
                    logger.error(f"❌ Erro ao adicionar coluna {column_name}: {e}")
                    raise
            else:
                logger.info(f"ℹ️ Coluna {column_name} já existe")
    
    def migrate_existing_data(self):
        """Migra dados existentes para novos campos"""
        logger.info("📊 Migrando dados existentes...")
        
        # Mapear tdd_phase para tdd_order
        tdd_phase_mapping = {
            'red': 1,
            'green': 2, 
            'refactor': 3,
            'analysis': None  # analysis não é fase TDD
        }
        
        try:
            # Atualizar tdd_order baseado em tdd_phase
            for phase, order in tdd_phase_mapping.items():
                if order is not None:
                    self.conn.execute("""
                        UPDATE framework_tasks 
                        SET tdd_order = ? 
                        WHERE tdd_phase = ? AND tdd_order IS NULL
                    """, (order, phase))
                    
                    count = self.conn.execute("""
                        SELECT COUNT(*) FROM framework_tasks 
                        WHERE tdd_phase = ? AND tdd_order = ?
                    """, (phase, order)).fetchone()[0]
                    
                    logger.info(f"✅ {count} tarefas migradas: {phase} → tdd_order={order}")
            
            # Separar task_type de tdd_phase
            # Tasks de análise
            self.conn.execute("""
                UPDATE framework_tasks 
                SET task_type = 'analysis' 
                WHERE tdd_phase = 'analysis' OR tdd_skip_reason IS NOT NULL
            """)
            
            analysis_count = self.conn.execute("""
                SELECT COUNT(*) FROM framework_tasks WHERE task_type = 'analysis'
            """).fetchone()[0]
            logger.info(f"✅ {analysis_count} tarefas marcadas como 'analysis'")
            
            # Extrair task_group do task_key (pattern: "1.1b" from "1.1b.1")
            tasks = self.conn.execute("""
                SELECT id, task_key FROM framework_tasks WHERE task_group IS NULL
            """).fetchall()
            
            for task in tasks:
                task_key = task['task_key']
                # Extrair grupo: "1.1b.1" → "1.1b", "0.3.1" → "0.3"
                parts = task_key.split('.')
                if len(parts) >= 2:
                    if parts[-1].isdigit():  # Último é número (sequência)
                        task_group = '.'.join(parts[:-1])
                        task_sequence = int(parts[-1])
                    else:  # Não tem sequência numérica
                        task_group = task_key
                        task_sequence = 1
                        
                    self.conn.execute("""
                        UPDATE framework_tasks 
                        SET task_group = ?, task_sequence = ?
                        WHERE id = ?
                    """, (task_group, task_sequence, task['id']))
            
            group_count = self.conn.execute("""
                SELECT COUNT(*) FROM framework_tasks WHERE task_group IS NOT NULL
            """).fetchone()[0]
            logger.info(f"✅ {group_count} tarefas com task_group extraído")
            
            self.conn.commit()
            logger.info("✅ Migração de dados concluída")
            
        except Exception as e:
            logger.error(f"❌ Erro na migração de dados: {e}")
            self.conn.rollback()
            raise
    
    def create_indexes(self):
        """Cria índices otimizados para queries de dependência"""
        indexes = [
            ("idx_tasks_epic_key", "framework_tasks", ["epic_id", "task_key"]),
            ("idx_tasks_group_seq", "framework_tasks", ["task_group", "task_sequence"]),
            ("idx_tasks_tdd_order", "framework_tasks", ["tdd_order"]),
            ("idx_tasks_priority", "framework_tasks", ["priority"]),
            ("idx_td_task", "task_dependencies", ["task_id"]),
            ("idx_td_depkey", "task_dependencies", ["depends_on_task_key"]),
        ]
        
        for index_name, table, columns in indexes:
            try:
                columns_str = ", ".join(columns)
                sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({columns_str})"
                self.conn.execute(sql)
                logger.info(f"✅ Índice criado: {index_name}")
            except Exception as e:
                logger.error(f"❌ Erro ao criar índice {index_name}: {e}")
                raise
        
        self.conn.commit()
    
    def validate_migration(self) -> bool:
        """Valida se a migração foi bem-sucedida"""
        logger.info("🔍 Validando migração...")
        
        try:
            # Verificar se todas as colunas foram criadas
            required_columns = ["tdd_order", "task_type", "priority", "task_group", "task_sequence"]
            for column in required_columns:
                if not self.check_column_exists("framework_tasks", column):
                    logger.error(f"❌ Coluna {column} não foi criada")
                    return False
            
            # Verificar se dados foram migrados
            tdd_order_count = self.conn.execute("""
                SELECT COUNT(*) FROM framework_tasks WHERE tdd_order IS NOT NULL
            """).fetchone()[0]
            
            analysis_count = self.conn.execute("""
                SELECT COUNT(*) FROM framework_tasks WHERE task_type = 'analysis'
            """).fetchone()[0]
            
            group_count = self.conn.execute("""
                SELECT COUNT(*) FROM framework_tasks WHERE task_group IS NOT NULL
            """).fetchone()[0]
            
            logger.info(f"📊 Estatísticas da migração:")
            logger.info(f"   - Tarefas com tdd_order: {tdd_order_count}")
            logger.info(f"   - Tarefas tipo analysis: {analysis_count}")
            logger.info(f"   - Tarefas com task_group: {group_count}")
            
            # Verificar índices
            indexes = self.conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%'
            """).fetchall()
            
            logger.info(f"   - Índices criados: {len(indexes)}")
            
            logger.info("✅ Migração validada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na validação: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Executa migração completa"""
        logger.info("🚀 Iniciando migração dos campos de priorização...")
        
        try:
            # Conectar
            self.connect()
            
            # Criar backup
            backup_path = self.create_backup()
            
            # Executar migração
            logger.info("📝 Adicionando novas colunas...")
            self.add_new_columns()
            
            logger.info("📊 Migrando dados existentes...")
            self.migrate_existing_data()
            
            logger.info("📈 Criando índices otimizados...")
            self.create_indexes()
            
            # Validar
            if self.validate_migration():
                logger.info("🎉 Migração concluída com sucesso!")
                logger.info(f"💾 Backup disponível em: {backup_path}")
                return True
            else:
                logger.error("❌ Falha na validação da migração")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro durante migração: {e}")
            logger.error("🔄 Execute rollback manual se necessário")
            return False
            
        finally:
            self.disconnect()

def main():
    """Main script entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migração dos campos de priorização de tarefas")
    parser.add_argument("--db", default="framework.db", help="Caminho do banco de dados")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar o que seria feito sem executar")
    parser.add_argument("--verbose", action="store_true", help="Output verboso")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.dry_run:
        logger.info("🔍 DRY RUN - Verificando estado atual...")
        migration = TaskFieldsMigration(args.db)
        migration.connect()
        
        # Verificar colunas existentes
        table_info = migration.get_table_info("framework_tasks")
        existing_columns = [col['name'] for col in table_info]
        
        required_columns = ["tdd_order", "task_type", "priority", "task_group", "task_sequence"]
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        logger.info(f"📋 Colunas existentes: {existing_columns}")
        logger.info(f"📋 Colunas faltando: {missing_columns}")
        
        if missing_columns:
            logger.info("🔧 Migração necessária")
        else:
            logger.info("✅ Todas as colunas já existem")
            
        migration.disconnect()
        return
    
    # Executar migração
    migration = TaskFieldsMigration(args.db)
    success = migration.run_migration()
    
    if success:
        print("✅ Migração concluída com sucesso!")
        sys.exit(0)
    else:
        print("❌ Falha na migração")
        sys.exit(1)

if __name__ == "__main__":
    main()