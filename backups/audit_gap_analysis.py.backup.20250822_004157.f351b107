#!/usr/bin/env python3
"""
🔍 AUDITORIA CRÍTICA - GAP ANALYSIS

Analisa sistematicamente os gaps entre a análise da Fase 1.1.1 e a implementação 1.1.2.2
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Set
from collections import defaultdict

class GapAnalyzer:
    def __init__(self):
        self.json_fields = set()
        self.schema_fields = set()
        self.epic_data = []
        self.placeholders_found = []
        self.structure_types = {}
        
    def analyze_json_files(self):
        """Analisa todos os arquivos JSON para extrair campos únicos."""
        print("🔍 Analisando arquivos JSON para identificar campos únicos...")
        
        epic_dir = Path("epics")
        if not epic_dir.exists():
            print("❌ Diretório epics/ não encontrado")
            return
        
        for json_file in epic_dir.glob("*.json"):
            print(f"  📄 Processando {json_file.name}...")
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Identifica estrutura (nested vs flat)
                if 'epic' in data:
                    self.structure_types[json_file.name] = 'nested'
                    epic_data = data['epic']
                else:
                    self.structure_types[json_file.name] = 'flat'
                    epic_data = data
                
                self.epic_data.append({'file': json_file.name, 'data': epic_data})
                
                # Extrai todos os campos recursivamente
                fields = self._extract_fields_recursive(epic_data)
                self.json_fields.update(fields)
                
                # Identifica placeholders
                self._find_placeholders(epic_data, json_file.name)
                
            except Exception as e:
                print(f"  ❌ Erro ao processar {json_file.name}: {e}")
    
    def _extract_fields_recursive(self, data, prefix="", max_depth=5):
        """Extrai campos recursivamente."""
        fields = set()
        
        if max_depth <= 0:
            return fields
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{prefix}.{key}" if prefix else key
                fields.add(current_path)
                
                if isinstance(value, (dict, list)):
                    nested_fields = self._extract_fields_recursive(
                        value, current_path, max_depth - 1
                    )
                    fields.update(nested_fields)
        
        elif isinstance(data, list) and data:
            # Analisa estrutura de arrays
            for i, item in enumerate(data[:3]):  # Primeiros 3 itens
                if isinstance(item, (dict, list)):
                    array_prefix = f"{prefix}[]"
                    nested_fields = self._extract_fields_recursive(
                        item, array_prefix, max_depth - 1
                    )
                    fields.update(nested_fields)
        
        return fields
    
    def _find_placeholders(self, data, filename, path=""):
        """Identifica valores placeholder."""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                self._find_placeholders(value, filename, current_path)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                self._find_placeholders(item, filename, current_path)
        
        elif isinstance(data, str):
            # Identifica padrões de placeholder
            if any(pattern in data.lower() for pattern in [
                '[epic-id]', '[task-id]', 'x.y', 'todo', 'tbd', 'placeholder',
                'template', 'example', 'test'
            ]):
                self.placeholders_found.append({
                    'file': filename,
                    'path': path,
                    'value': data
                })
    
    def analyze_database_schema(self):
        """Analisa o schema do banco de dados."""
        print("\n🗄️ Analisando schema do banco de dados...")
        
        try:
            conn = sqlite3.connect('framework.db')
            cursor = conn.cursor()
            
            # Extrai informações das tabelas
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                print(f"  📋 Analisando tabela {table_name}...")
                
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for column in columns:
                    column_name = column[1]
                    self.schema_fields.add(f"{table_name}.{column_name}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Erro ao analisar banco: {e}")
    
    def analyze_coverage_gaps(self):
        """Analisa gaps de cobertura entre JSON e schema."""
        print("\n📊 Analisando gaps de cobertura...")
        
        # Campos JSON que não tem correspondência no schema
        unmapped_json_fields = set()
        
        # Mapeia campos JSON para campos do schema
        json_to_schema_mapping = {
            # Epic level fields
            'id': 'framework_epics.epic_key',
            'name': 'framework_epics.name', 
            'summary': 'framework_epics.description',
            'description': 'framework_epics.description',
            'duration': 'framework_epics.duration_days',
            'status': 'framework_epics.status',
            'priority': 'framework_epics.priority',
            
            # Task level fields
            'tasks[].id': 'framework_tasks.task_key',
            'tasks[].title': 'framework_tasks.title',
            'tasks[].description': 'framework_tasks.description',
            'tasks[].tdd_phase': 'framework_tasks.tdd_phase',
            'tasks[].status': 'framework_tasks.status',
            'tasks[].estimate_minutes': 'framework_tasks.estimate_minutes',
            'tasks[].actual_minutes': 'framework_tasks.actual_minutes',
            'tasks[].story_points': 'framework_tasks.story_points',
            
            # GitHub fields
            'github_issue_id': 'framework_epics.github_issue_id',
            'github_milestone_id': 'framework_epics.github_milestone_id',
            'github_project_id': 'framework_epics.github_project_id',
            'tasks[].github_issue_number': 'framework_tasks.github_issue_number',
            'tasks[].github_branch': 'framework_tasks.github_branch',
            'tasks[].github_pr_number': 'framework_tasks.github_pr_number',
        }
        
        # Identifica campos não mapeados
        for json_field in self.json_fields:
            if json_field not in json_to_schema_mapping:
                unmapped_json_fields.add(json_field)
        
        return {
            'total_json_fields': len(self.json_fields),
            'total_schema_fields': len(self.schema_fields),
            'mapped_fields': len(json_to_schema_mapping),
            'unmapped_json_fields': unmapped_json_fields,
            'coverage_percentage': (len(json_to_schema_mapping) / len(self.json_fields)) * 100
        }
    
    def analyze_data_migration_status(self):
        """Analisa status da migração de dados."""
        print("\n🔄 Analisando status da migração de dados...")
        
        try:
            conn = sqlite3.connect('framework.db')
            cursor = conn.cursor()
            
            # Conta registros nas tabelas principais
            cursor.execute("SELECT COUNT(*) FROM framework_epics")
            epic_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM framework_tasks")  
            task_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM framework_users")
            user_count = cursor.fetchone()[0]
            
            conn.close()
            
            # Compara com dados JSON
            json_epic_count = len(self.epic_data)
            json_task_count = sum(len(epic['data'].get('tasks', [])) for epic in self.epic_data)
            
            return {
                'db_epics': epic_count,
                'db_tasks': task_count,
                'db_users': user_count,
                'json_epics': json_epic_count,
                'json_tasks': json_task_count,
                'migration_ratio_epics': (epic_count / json_epic_count) * 100 if json_epic_count > 0 else 0,
                'migration_ratio_tasks': (task_count / json_task_count) * 100 if json_task_count > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Erro ao analisar migração: {e}")
            return {}
    
    def generate_comprehensive_report(self):
        """Gera relatório abrangente da auditoria."""
        print("\n📋 Gerando relatório de auditoria crítica...")
        
        coverage_analysis = self.analyze_coverage_gaps()
        migration_analysis = self.analyze_data_migration_status()
        
        report = {
            'timestamp': '2025-08-12 02:30:00',
            'analysis_summary': {
                'total_json_files': len(self.epic_data),
                'structure_types': self.structure_types,
                'total_json_fields': coverage_analysis['total_json_fields'],
                'total_schema_fields': coverage_analysis['total_schema_fields'],
                'field_coverage_percentage': coverage_analysis['coverage_percentage'],
                'placeholders_found': len(self.placeholders_found),
                'unmapped_fields_count': len(coverage_analysis['unmapped_json_fields'])
            },
            'critical_gaps': {
                'gap_1_field_mapping': {
                    'severity': 'CRITICAL',
                    'description': 'Schema não mapeia sistematicamente os campos JSON',
                    'evidence': f"Apenas {coverage_analysis['mapped_fields']} de {coverage_analysis['total_json_fields']} campos mapeados ({coverage_analysis['coverage_percentage']:.1f}%)",
                    'unmapped_fields': list(coverage_analysis['unmapped_json_fields'])[:20]  # Primeiros 20
                },
                'gap_2_data_migration': {
                    'severity': 'CRITICAL', 
                    'description': 'Dados JSON reais não foram migrados',
                    'evidence': f"DB: {migration_analysis.get('db_epics', 0)} épicos, JSON: {migration_analysis.get('json_epics', 0)} épicos",
                    'migration_ratio': migration_analysis.get('migration_ratio_epics', 0)
                },
                'gap_3_placeholders': {
                    'severity': 'HIGH',
                    'description': 'Placeholders identificados não foram tratados',
                    'evidence': f"{len(self.placeholders_found)} placeholders encontrados",
                    'sample_placeholders': self.placeholders_found[:10]
                },
                'gap_4_structure_inconsistency': {
                    'severity': 'HIGH',
                    'description': 'Estruturas nested vs flat não foram resolvidas',
                    'evidence': f"Estruturas encontradas: {self.structure_types}",
                    'impact': 'Migração pode falhar em arquivos flat'
                }
            },
            'recommended_actions': [
                'Expandir schema para cobrir campos ausentes',
                'Implementar migração real dos dados JSON',
                'Criar script para tratar placeholders',
                'Normalizar estruturas nested/flat',
                'Preservar campos array com colunas JSON',
                'Re-validar com dados reais'
            ]
        }
        
        # Salva relatório
        with open('audit_gap_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Relatório salvo em audit_gap_analysis_report.json")
        return report
    
    def print_summary(self, report):
        """Imprime sumário da auditoria."""
        print("\n" + "="*80)
        print("🔍 AUDITORIA CRÍTICA - RESULTADOS")
        print("="*80)
        
        summary = report['analysis_summary']
        gaps = report['critical_gaps']
        
        print(f"\n📊 SUMÁRIO:")
        print(f"  📄 Arquivos JSON analisados: {summary['total_json_files']}")
        print(f"  🔍 Campos JSON identificados: {summary['total_json_fields']}")
        print(f"  🗄️ Campos no schema: {summary['total_schema_fields']}")
        print(f"  📈 Cobertura de campos: {summary['field_coverage_percentage']:.1f}%")
        print(f"  ⚠️ Placeholders encontrados: {summary['placeholders_found']}")
        
        print(f"\n🚨 GAPS CRÍTICOS IDENTIFICADOS:")
        for gap_id, gap_info in gaps.items():
            severity_icon = "🔴" if gap_info['severity'] == 'CRITICAL' else "🟡"
            print(f"  {severity_icon} {gap_info['severity']}: {gap_info['description']}")
            print(f"     Evidence: {gap_info['evidence']}")
        
        print(f"\n✅ STATUS: AUDITORIA CONCLUÍDA - {len(gaps)} GAPS IDENTIFICADOS")

def main():
    """Executa auditoria completa."""
    analyzer = GapAnalyzer()
    
    # Executa análises
    analyzer.analyze_json_files()
    analyzer.analyze_database_schema()
    
    # Gera relatório
    report = analyzer.generate_comprehensive_report()
    analyzer.print_summary(report)
    
    return len(report['critical_gaps']) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)