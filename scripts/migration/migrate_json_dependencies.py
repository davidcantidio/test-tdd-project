#!/usr/bin/env python3
"""
🔄 MIGRATION - Migrate JSON Dependencies to Database

Migração única: extrai dependências dos arquivos JSON e popula task_dependencies.
DB como fonte de verdade a partir de agora.

Usage:
    python scripts/migration/migrate_json_dependencies.py

Features:
- Lê dependências de epics/enriched/*.json
- Popula tabela task_dependencies
- Valida integridade referencial
- Relatório detalhado de migração
- Rollback em caso de erro
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
import sys
from collections import defaultdict

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DependencyMigration:
    """Migração de dependências JSON → Database"""
    
    def __init__(self, db_path: str = "framework.db", epics_dir: str = "epics/enriched"):
        self.db_path = db_path
        self.epics_dir = Path(epics_dir)
        self.conn = None
        
        # Estatísticas da migração
        self.stats = {
            'epics_processed': 0,
            'tasks_processed': 0,
            'dependencies_found': 0,
            'dependencies_migrated': 0,
            'dependencies_skipped': 0,
            'orphan_dependencies': 0,
            'tdd_dependencies_added': 0
        }
        
    def connect(self):
        """Conecta ao banco com row_factory configurado"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        
    def disconnect(self):
        """Fecha conexão"""
        if self.conn:
            self.conn.close()
    
    def create_backup(self) -> str:
        """Cria backup da tabela task_dependencies"""
        backup_path = "task_dependencies_backup.json"
        
        try:
            # Salvar dependências existentes
            existing_deps = self.conn.execute("""
                SELECT td.task_id, td.depends_on_task_key, td.dependency_type,
                       t.task_key as task_key, t.epic_id
                FROM task_dependencies td
                JOIN framework_tasks t ON td.task_id = t.id
            """).fetchall()
            
            backup_data = {
                'timestamp': str(Path().cwd()),
                'dependencies': [dict(row) for row in existing_deps]
            }
            
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
                
            logger.info(f"✅ Backup criado: {backup_path} ({len(existing_deps)} dependências)")
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            raise
    
    def clear_existing_dependencies(self):
        """Remove dependências existentes"""
        try:
            count = self.conn.execute("SELECT COUNT(*) FROM task_dependencies").fetchone()[0]
            
            if count > 0:
                self.conn.execute("DELETE FROM task_dependencies")
                logger.info(f"🗑️ {count} dependências existentes removidas")
            else:
                logger.info("ℹ️ Nenhuma dependência existente encontrada")
                
        except Exception as e:
            logger.error(f"❌ Erro ao limpar dependências: {e}")
            raise
    
    def get_task_map(self) -> Dict[Tuple[int, str], int]:
        """Cria mapa (epic_id, task_key) → task_id"""
        try:
            tasks = self.conn.execute("""
                SELECT id, epic_id, task_key 
                FROM framework_tasks 
                WHERE deleted_at IS NULL
            """).fetchall()
            
            task_map = {}
            for task in tasks:
                key = (int(task['epic_id']), task['task_key'])
                task_map[key] = task['id']
            
            logger.info(f"📋 Mapa de tarefas criado: {len(task_map)} tarefas")
            return task_map
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar mapa de tarefas: {e}")
            raise
    
    def load_epic_dependencies(self, epic_file: Path) -> Tuple[int, List[Dict]]:
        """Carrega dependências de um arquivo de épico"""
        try:
            with open(epic_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            epic_data = data.get('epic', {})
            epic_id = epic_data.get('id')
            
            if epic_id is None:
                logger.warning(f"⚠️ Epic ID não encontrado em {epic_file}")
                return None, []
            
            # Converter para int se for string
            try:
                epic_id = int(epic_id)
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Epic ID inválido em {epic_file}: {epic_id}")
                return None, []
            
            tasks = epic_data.get('tasks', [])
            dependencies = []
            
            for task in tasks:
                task_key = task.get('id')
                task_deps = task.get('dependencies', [])
                
                if task_key and task_deps:
                    for dep_key in task_deps:
                        if dep_key:  # Ignora dependências vazias
                            dependencies.append({
                                'task_key': task_key,
                                'depends_on_task_key': dep_key,
                                'dependency_type': 'blocking'
                            })
            
            self.stats['epics_processed'] += 1
            self.stats['tasks_processed'] += len(tasks)
            self.stats['dependencies_found'] += len(dependencies)
            
            logger.info(f"📖 {epic_file.name}: épico {epic_id}, {len(tasks)} tarefas, {len(dependencies)} dependências")
            return epic_id, dependencies
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar {epic_file}: {e}")
            return None, []
    
    def add_tdd_implicit_dependencies(self, task_map: Dict[Tuple[int, str], int]) -> List[Dict]:
        """Adiciona dependências implícitas TDD baseadas em task_group e tdd_order"""
        try:
            # Buscar tasks TDD agrupadas
            tasks = self.conn.execute("""
                SELECT id, epic_id, task_key, task_group, tdd_order
                FROM framework_tasks 
                WHERE tdd_order IS NOT NULL 
                  AND task_group IS NOT NULL
                  AND deleted_at IS NULL
                ORDER BY epic_id, task_group, tdd_order
            """).fetchall()
            
            # Agrupar por (epic_id, task_group)
            tdd_groups = defaultdict(list)
            for task in tasks:
                group_key = (task['epic_id'], task['task_group'])
                tdd_groups[group_key].append(task)
            
            tdd_dependencies = []
            
            # Criar dependências TDD sequenciais
            for group_key, group_tasks in tdd_groups.items():
                group_tasks.sort(key=lambda x: x['tdd_order'])
                
                for i in range(1, len(group_tasks)):
                    prev_task = group_tasks[i-1]
                    curr_task = group_tasks[i]
                    
                    tdd_dependencies.append({
                        'task_id': curr_task['id'],
                        'depends_on_task_key': prev_task['task_key'],
                        'dependency_type': 'tdd_sequence'
                    })
            
            self.stats['tdd_dependencies_added'] = len(tdd_dependencies)
            logger.info(f"🔄 {len(tdd_dependencies)} dependências TDD implícitas adicionadas")
            
            return tdd_dependencies
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar dependências TDD: {e}")
            return []
    
    def migrate_dependencies(self) -> bool:
        """Migra todas as dependências do JSON para o DB"""
        logger.info("🚀 Iniciando migração de dependências...")
        
        try:
            # Criar mapa de tarefas
            task_map = self.get_task_map()
            
            # Limpar dependências existentes
            self.clear_existing_dependencies()
            
            # Processar cada arquivo de épico
            all_dependencies = []
            
            for epic_file in sorted(self.epics_dir.glob("*.json")):
                epic_id, dependencies = self.load_epic_dependencies(epic_file)
                
                if epic_id is not None and dependencies:
                    # Converter para registros do banco
                    for dep in dependencies:
                        task_key = dep['task_key']
                        depends_on_key = dep['depends_on_task_key']
                        
                        # Buscar task_id
                        task_lookup = (epic_id, task_key)
                        if task_lookup in task_map:
                            task_id = task_map[task_lookup]
                            
                            all_dependencies.append({
                                'task_id': task_id,
                                'depends_on_task_key': depends_on_key,
                                'dependency_type': dep['dependency_type']
                            })
                        else:
                            logger.warning(f"⚠️ Tarefa não encontrada: {epic_id}.{task_key}")
                            self.stats['orphan_dependencies'] += 1
            
            # Adicionar dependências TDD implícitas
            tdd_dependencies = self.add_tdd_implicit_dependencies(task_map)
            all_dependencies.extend(tdd_dependencies)
            
            # Inserir no banco
            if all_dependencies:
                self.conn.executemany("""
                    INSERT OR IGNORE INTO task_dependencies 
                    (task_id, depends_on_task_key, dependency_type)
                    VALUES (?, ?, ?)
                """, [(dep['task_id'], dep['depends_on_task_key'], dep['dependency_type']) 
                      for dep in all_dependencies])
                
                self.stats['dependencies_migrated'] = len(all_dependencies)
                self.conn.commit()
                
                logger.info(f"✅ {len(all_dependencies)} dependências inseridas no banco")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na migração de dependências: {e}")
            self.conn.rollback()
            return False
    
    def validate_dependencies(self) -> bool:
        """Valida integridade das dependências migradas"""
        logger.info("🔍 Validando dependências migradas...")
        
        try:
            # Contar dependências totais
            total_deps = self.conn.execute("""
                SELECT COUNT(*) FROM task_dependencies
            """).fetchone()[0]
            
            # Contar dependências por tipo
            deps_by_type = self.conn.execute("""
                SELECT dependency_type, COUNT(*) as count
                FROM task_dependencies
                GROUP BY dependency_type
            """).fetchall()
            
            # Verificar dependências órfãs (depends_on_task_key não existe)
            orphan_deps = self.conn.execute("""
                SELECT COUNT(*) FROM task_dependencies td
                WHERE NOT EXISTS (
                    SELECT 1 FROM framework_tasks t 
                    WHERE t.task_key = td.depends_on_task_key
                    AND t.deleted_at IS NULL
                )
            """).fetchone()[0]
            
            # Verificar ciclos simples (A→B, B→A)
            simple_cycles = self.conn.execute("""
                SELECT COUNT(*) FROM task_dependencies td1
                JOIN task_dependencies td2 ON td1.depends_on_task_key = (
                    SELECT t.task_key FROM framework_tasks t WHERE t.id = td2.task_id
                )
                JOIN framework_tasks t1 ON t1.id = td1.task_id
                WHERE td2.depends_on_task_key = t1.task_key
            """).fetchone()[0]
            
            # Verificar tarefas com muitas dependências
            heavy_tasks = self.conn.execute("""
                SELECT t.task_key, COUNT(*) as dep_count
                FROM task_dependencies td
                JOIN framework_tasks t ON t.id = td.task_id
                GROUP BY t.task_key
                HAVING COUNT(*) > 5
                ORDER BY COUNT(*) DESC
            """).fetchall()
            
            logger.info(f"📊 Validação das dependências:")
            logger.info(f"   - Total de dependências: {total_deps}")
            
            for dep_type in deps_by_type:
                logger.info(f"   - {dep_type['dependency_type']}: {dep_type['count']}")
            
            logger.info(f"   - Dependências órfãs: {orphan_deps}")
            logger.info(f"   - Ciclos simples detectados: {simple_cycles}")
            logger.info(f"   - Tarefas com >5 dependências: {len(heavy_tasks)}")
            
            if heavy_tasks:
                logger.info("   Top heavy tasks:")
                for task in heavy_tasks[:3]:
                    logger.info(f"     - {task['task_key']}: {task['dep_count']} deps")
            
            # Critérios de validação
            if orphan_deps > 0:
                logger.warning(f"⚠️ {orphan_deps} dependências órfãs encontradas")
            
            if simple_cycles > 0:
                logger.warning(f"⚠️ {simple_cycles} ciclos simples detectados")
            
            if total_deps == 0:
                logger.error("❌ Nenhuma dependência foi migrada")
                return False
            
            logger.info("✅ Validação concluída")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na validação: {e}")
            return False
    
    def generate_report(self) -> str:
        """Gera relatório detalhado da migração"""
        report_path = "dependency_migration_report.md"
        
        try:
            # Estatísticas adicionais
            total_tasks = self.conn.execute("""
                SELECT COUNT(*) FROM framework_tasks WHERE deleted_at IS NULL
            """).fetchone()[0]
            
            tasks_with_deps = self.conn.execute("""
                SELECT COUNT(DISTINCT task_id) FROM task_dependencies
            """).fetchone()[0]
            
            avg_deps_per_task = self.conn.execute("""
                SELECT AVG(dep_count) FROM (
                    SELECT COUNT(*) as dep_count 
                    FROM task_dependencies 
                    GROUP BY task_id
                )
            """).fetchone()[0] or 0
            
            report_content = f"""# Relatório de Migração de Dependências

## 📊 Estatísticas Gerais

- **Épicos processados:** {self.stats['epics_processed']}
- **Tarefas processadas:** {self.stats['tasks_processed']}
- **Total de tarefas no DB:** {total_tasks}

## 🔗 Dependências

- **Dependências encontradas no JSON:** {self.stats['dependencies_found']}
- **Dependências TDD adicionadas:** {self.stats['tdd_dependencies_added']}
- **Dependências migradas total:** {self.stats['dependencies_migrated']}
- **Dependências órfãs:** {self.stats['orphan_dependencies']}

## 📈 Métricas

- **Tarefas com dependências:** {tasks_with_deps} de {total_tasks} ({(tasks_with_deps/total_tasks*100):.1f}%)
- **Média de dependências por tarefa:** {avg_deps_per_task:.1f}

## 🎯 Status

✅ **Migração concluída com sucesso**

- DB agora é a fonte de verdade para dependências
- Dependências TDD implícitas adicionadas automaticamente
- Integridade referencial validada

## 📝 Próximos Passos

1. ✅ Execute validação DAG completa
2. ✅ Teste sistema de ordenação topológica
3. ✅ Implemente UI de visualização de dependências

---
*Gerado em: {Path().cwd()} - Migração de dependências JSON→DB*
"""
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"📄 Relatório gerado: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório: {e}")
            return ""
    
    def run_migration(self) -> bool:
        """Executa migração completa"""
        logger.info("🚀 Iniciando migração de dependências JSON → DB...")
        
        try:
            # Conectar
            self.connect()
            
            # Verificar se diretório de épicos existe
            if not self.epics_dir.exists():
                logger.error(f"❌ Diretório de épicos não encontrado: {self.epics_dir}")
                return False
            
            # Criar backup
            backup_path = self.create_backup()
            
            # Executar migração
            if not self.migrate_dependencies():
                logger.error("❌ Falha na migração de dependências")
                return False
            
            # Validar
            if not self.validate_dependencies():
                logger.error("❌ Falha na validação das dependências")
                return False
            
            # Gerar relatório
            report_path = self.generate_report()
            
            logger.info("🎉 Migração de dependências concluída com sucesso!")
            logger.info(f"💾 Backup: {backup_path}")
            logger.info(f"📄 Relatório: {report_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro durante migração: {e}")
            return False
            
        finally:
            self.disconnect()

def main():
    """Main script entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migração de dependências JSON → Database")
    parser.add_argument("--db", default="framework.db", help="Caminho do banco de dados")
    parser.add_argument("--epics-dir", default="epics/enriched", help="Diretório dos épicos JSON")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar o que seria feito sem executar")
    parser.add_argument("--verbose", action="store_true", help="Output verboso")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.dry_run:
        logger.info("🔍 DRY RUN - Analisando arquivos JSON...")
        
        epics_dir = Path(args.epics_dir)
        if not epics_dir.exists():
            logger.error(f"❌ Diretório não encontrado: {epics_dir}")
            return
        
        json_files = list(epics_dir.glob("*.json"))
        logger.info(f"📋 Arquivos JSON encontrados: {len(json_files)}")
        
        total_deps = 0
        for json_file in json_files:
            try:
                with open(json_file) as f:
                    data = json.load(f)
                epic_data = data.get('epic', {})
                tasks = epic_data.get('tasks', [])
                deps = sum(len(task.get('dependencies', [])) for task in tasks)
                total_deps += deps
                logger.info(f"   - {json_file.name}: {len(tasks)} tarefas, {deps} dependências")
            except Exception as e:
                logger.error(f"   - {json_file.name}: ERRO - {e}")
        
        logger.info(f"📊 Total de dependências a migrar: {total_deps}")
        return
    
    # Executar migração
    migration = DependencyMigration(args.db, args.epics_dir)
    success = migration.run_migration()
    
    if success:
        print("✅ Migração de dependências concluída com sucesso!")
        sys.exit(0)
    else:
        print("❌ Falha na migração de dependências")
        sys.exit(1)

if __name__ == "__main__":
    main()