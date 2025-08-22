#!/usr/bin/env python3
"""
🔄 MIGRAÇÃO REAL DOS DADOS JSON → SQLITE

Migra dados reais dos arquivos JSON para framework.db, 
substituindo os dados fake criados nos testes.
"""

import json
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

class JSONDataMigrator:
    def __init__(self, db_path="framework.db"):
        self.db_path = db_path
        self.conn = None
        self.migrated_epics = 0
        self.migrated_tasks = 0
        self.errors = []
        
    def connect(self):
        """Conecta ao banco de dados."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar ao banco: {e}")
            return False
    
    def cleanup_fake_data(self):
        """Remove dados fake criados pelos testes."""
        print("🧹 Removendo dados fake dos testes...")
        
        cursor = self.conn.cursor()
        
        try:
            # Remove dados de teste em ordem de dependência
            cursor.execute("DELETE FROM user_achievements WHERE user_id > 1")
            cursor.execute("DELETE FROM user_streaks WHERE user_id > 1") 
            cursor.execute("DELETE FROM work_sessions WHERE user_id > 1")
            cursor.execute("DELETE FROM framework_tasks WHERE task_key LIKE 'TASK_%' OR task_key LIKE 'CT_%'")
            cursor.execute("DELETE FROM framework_epics WHERE epic_key LIKE 'EPIC_%' OR epic_key LIKE 'COMPAT_TEST'")
            cursor.execute("DELETE FROM framework_users WHERE username LIKE 'user_%' OR username LIKE 'bench_%'")
            
            # Reseta auto increment
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('framework_epics', 'framework_tasks', 'framework_users')")
            
            self.conn.commit()
            print("✅ Dados fake removidos")
            
        except Exception as e:
            print(f"❌ Erro ao limpar dados fake: {e}")
            self.conn.rollback()
    
    def migrate_json_files(self):
        """Migra todos os arquivos JSON encontrados."""
        print("📂 Iniciando migração dos arquivos JSON...")
        
        epic_dir = Path("epics")
        if not epic_dir.exists():
            print("❌ Diretório epics/ não encontrado")
            return False
        
        json_files = list(epic_dir.glob("*.json"))
        print(f"📄 Encontrados {len(json_files)} arquivos JSON")
        
        for json_file in json_files:
            if self._is_template_file(json_file.name):
                print(f"⏭️ Pulando arquivo template: {json_file.name}")
                continue
                
            print(f"🔄 Migrando {json_file.name}...")
            self._migrate_single_file(json_file)
        
        return True
    
    def _is_template_file(self, filename):
        """Verifica se é arquivo template (não migrar)."""
        template_indicators = ['template', 'example', '_template']
        return any(indicator in filename.lower() for indicator in template_indicators)
    
    def _migrate_single_file(self, json_file):
        """Migra um único arquivo JSON."""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Detecta estrutura (nested vs flat)
            if 'epic' in data:
                epic_data = data['epic']
            else:
                epic_data = data
            
            # Migra épico
            epic_id = self._migrate_epic(epic_data, json_file.name)
            
            if epic_id:
                # Migra tasks do épico
                tasks = epic_data.get('tasks', [])
                for task in tasks:
                    self._migrate_task(task, epic_id, json_file.name)
                
                self.migrated_epics += 1
                print(f"  ✅ Épico migrado: {epic_data.get('name', 'Sem nome')} ({len(tasks)} tasks)")
            
        except Exception as e:
            error_msg = f"Erro ao migrar {json_file.name}: {e}"
            self.errors.append(error_msg)
            print(f"  ❌ {error_msg}")
    
    def _migrate_epic(self, epic_data, source_file):
        """Migra um épico para o banco."""
        cursor = self.conn.cursor()
        
        try:
            # Extrai dados do épico
            epic_key = str(epic_data.get('id', epic_data.get('epic_id', f"epic_{self.migrated_epics}")))
            name = epic_data.get('name', epic_data.get('title', 'Épico sem nome'))
            description = epic_data.get('summary', epic_data.get('description', ''))
            status = epic_data.get('status', 'pending')
            priority = epic_data.get('priority', 1)
            
            # Converte duration para dias
            duration_days = self._parse_duration(epic_data.get('duration', epic_data.get('duration_days')))
            
            # Campos de gamificação
            difficulty_level = epic_data.get('difficulty_level', 'medium')
            
            # Preserva dados complexos como JSON
            metadata = {
                'source_file': source_file,
                'goals': epic_data.get('goals', []),
                'definition_of_done': epic_data.get('definition_of_done', []),
                'labels': epic_data.get('labels', []),
                'automation_hooks': epic_data.get('automation_hooks', {}),
                'performance_constraints': epic_data.get('performance_constraints', {}),
                'quality_gates': epic_data.get('quality_gates', {}),
                'methodology': epic_data.get('methodology'),
                'tdd_enabled': epic_data.get('tdd_enabled', True)
            }
            
            # Insere épico
            cursor.execute("""
                INSERT INTO framework_epics (
                    epic_key, name, description, status, priority, duration_days,
                    difficulty_level, created_by, assigned_to, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, ?)
            """, (
                epic_key, name, description, status, priority, duration_days,
                difficulty_level, datetime.now().isoformat()
            ))
            
            epic_id = cursor.lastrowid
            
            # Salva metadata em system_settings
            cursor.execute("""
                INSERT OR REPLACE INTO system_settings (
                    category, setting_key, setting_value, setting_type, description
                ) VALUES (?, ?, ?, 'json', ?)
            """, (
                'epic_metadata', 
                f'epic_{epic_id}', 
                json.dumps(metadata, ensure_ascii=False),
                f'Metadata for epic {epic_key}'
            ))
            
            self.conn.commit()
            return epic_id
            
        except Exception as e:
            print(f"    ❌ Erro ao migrar épico: {e}")
            self.conn.rollback()
            return None
    
    def _migrate_task(self, task_data, epic_id, source_file):
        """Migra uma task para o banco."""
        cursor = self.conn.cursor()
        
        try:
            # Extrai dados da task
            task_key = str(task_data.get('id', f"task_{self.migrated_tasks}"))
            title = task_data.get('title', 'Task sem título')
            description = task_data.get('description', '')
            tdd_phase = task_data.get('tdd_phase', 'analysis')
            status = task_data.get('status', 'pending')
            
            # Tempos e estimativas
            estimate_minutes = self._parse_minutes(task_data.get('estimate_minutes', 60))
            actual_minutes = self._parse_minutes(task_data.get('actual_minutes', 0))
            story_points = task_data.get('story_points', 1)
            
            # Gamificação
            difficulty_modifier = task_data.get('difficulty_modifier', 1.0)
            
            # GitHub integration
            github_issue_number = task_data.get('github_issue_number')
            github_branch = task_data.get('github_branch')
            github_pr_number = task_data.get('github_pr_number')
            
            # Preserva dados complexos
            metadata = {
                'source_file': source_file,
                'acceptance_criteria': task_data.get('acceptance_criteria', []),
                'deliverables': task_data.get('deliverables', []),
                'dependencies': task_data.get('dependencies', []),
                'test_plan': task_data.get('test_plan', []),
                'test_specs': task_data.get('test_specs', []),
                'risk': task_data.get('risk'),
                'mitigation': task_data.get('mitigation'),
                'tdd_skip_reason': task_data.get('tdd_skip_reason'),
                'files_touched': task_data.get('files_touched', []),
                'branch': task_data.get('branch')
            }
            
            # Insere task
            cursor.execute("""
                INSERT INTO framework_tasks (
                    task_key, epic_id, title, description, tdd_phase, status,
                    estimate_minutes, actual_minutes, story_points, difficulty_modifier,
                    github_issue_number, github_branch, github_pr_number,
                    assigned_to, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                task_key, epic_id, title, description, tdd_phase, status,
                estimate_minutes, actual_minutes, story_points, difficulty_modifier,
                github_issue_number, github_branch, github_pr_number,
                datetime.now().isoformat()
            ))
            
            task_id = cursor.lastrowid
            
            # Salva metadata da task
            cursor.execute("""
                INSERT OR REPLACE INTO system_settings (
                    category, setting_key, setting_value, setting_type, description
                ) VALUES (?, ?, ?, 'json', ?)
            """, (
                'task_metadata',
                f'task_{task_id}',
                json.dumps(metadata, ensure_ascii=False),
                f'Metadata for task {task_key}'
            ))
            
            self.migrated_tasks += 1
            self.conn.commit()
            
        except Exception as e:
            print(f"    ❌ Erro ao migrar task {task_data.get('id', 'unknown')}: {e}")
            self.conn.rollback()
    
    def _parse_duration(self, duration_value):
        """Converte duration para dias."""
        if not duration_value:
            return None
        
        if isinstance(duration_value, (int, float)):
            return duration_value
        
        if isinstance(duration_value, str):
            # Extrai números da string
            import re
            numbers = re.findall(r'\d+', duration_value.lower())
            if numbers:
                days = int(numbers[0])
                if 'hour' in duration_value.lower() or 'hora' in duration_value.lower():
                    return round(days / 8, 1)  # Converte horas para dias
                return days
        
        return 1  # Default
    
    def _parse_minutes(self, time_value):
        """Converte tempo para minutos."""
        if not time_value:
            return 0
        
        if isinstance(time_value, (int, float)):
            return int(time_value)
        
        if isinstance(time_value, str):
            import re
            numbers = re.findall(r'\d+', time_value)
            if numbers:
                return int(numbers[0])
        
        return 0
    
    def validate_migration(self):
        """Valida a migração realizada."""
        print("\n🧪 Validando migração...")
        
        cursor = self.conn.cursor()
        
        # Conta registros migrados
        cursor.execute("SELECT COUNT(*) FROM framework_epics WHERE created_by = 1")
        epic_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM framework_tasks WHERE assigned_to = 1")
        task_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM system_settings WHERE category IN ('epic_metadata', 'task_metadata')")
        metadata_count = cursor.fetchone()[0]
        
        # Testa queries básicas
        cursor.execute("""
            SELECT e.epic_key, e.name, COUNT(t.id) as task_count
            FROM framework_epics e
            LEFT JOIN framework_tasks t ON e.id = t.epic_id
            WHERE e.created_by = 1
            GROUP BY e.id, e.epic_key, e.name
        """)
        epics_with_tasks = cursor.fetchall()
        
        print(f"✅ Épicos migrados: {epic_count}")
        print(f"✅ Tasks migradas: {task_count}")
        print(f"✅ Metadata records: {metadata_count}")
        
        print(f"\n📊 Épicos com tasks:")
        for epic in epics_with_tasks:
            print(f"  📋 {epic[1]} ({epic[0]}): {epic[2]} tasks")
        
        # Verifica integridade referencial
        cursor.execute("""
            SELECT COUNT(*) FROM framework_tasks t
            LEFT JOIN framework_epics e ON t.epic_id = e.id
            WHERE e.id IS NULL
        """)
        orphan_tasks = cursor.fetchone()[0]
        
        if orphan_tasks > 0:
            print(f"⚠️ {orphan_tasks} tasks órfãs encontradas")
        else:
            print("✅ Integridade referencial OK")
        
        return {
            'epics_migrated': epic_count,
            'tasks_migrated': task_count,
            'metadata_records': metadata_count,
            'orphan_tasks': orphan_tasks,
            'errors': len(self.errors)
        }
    
    def generate_migration_report(self, validation_results):
        """Gera relatório da migração."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'migration_summary': {
                'epics_migrated': self.migrated_epics,
                'tasks_migrated': self.migrated_tasks,
                'errors_count': len(self.errors),
                'errors': self.errors
            },
            'validation_results': validation_results,
            'status': 'SUCCESS' if len(self.errors) == 0 and validation_results['orphan_tasks'] == 0 else 'PARTIAL'
        }
        
        with open('real_data_migration_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Relatório salvo em real_data_migration_report.json")
        return report
    
    def run_migration(self):
        """Executa migração completa."""
        print("🔄 MIGRAÇÃO REAL DOS DADOS JSON → SQLITE")
        print("=" * 60)
        
        if not self.connect():
            return False
        
        try:
            # Limpa dados fake
            self.cleanup_fake_data()
            
            # Migra dados reais
            if not self.migrate_json_files():
                return False
            
            # Valida migração
            validation_results = self.validate_migration()
            
            # Gera relatório
            report = self.generate_migration_report(validation_results)
            
            print(f"\n🎯 MIGRAÇÃO CONCLUÍDA")
            print(f"Status: {report['status']}")
            print(f"Épicos: {self.migrated_epics}, Tasks: {self.migrated_tasks}")
            print(f"Erros: {len(self.errors)}")
            
            return report['status'] == 'SUCCESS'
            
        except Exception as e:
            print(f"❌ Erro durante migração: {e}")
            return False
        
        finally:
            if self.conn:
                self.conn.close()

def main():
    """Executa migração dos dados reais."""
    migrator = JSONDataMigrator()
    success = migrator.run_migration()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)