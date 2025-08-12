#!/usr/bin/env python3
"""
Script de validação pós-migração
Verifica integridade dos dados migrados
"""

import sqlite3
from typing import List, Dict, Any

class MigrationValidator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.validation_results = []
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def validate_record_counts(self):
        """Valida contagem de registros"""
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM framework_epics")
        epic_count = cursor.fetchone()['count']
        
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM framework_tasks")
        task_count = cursor.fetchone()['count']
        
        self.validation_results.append({
            'test': 'Record Counts',
            'status': 'PASS' if epic_count >= 5 and task_count >= 50 else 'FAIL',
            'details': f'Epics: {epic_count}, Tasks: {task_count}'
        })
    
    def validate_foreign_keys(self):
        """Valida integridade referencial"""
        cursor = self.conn.execute("""
            SELECT COUNT(*) as count 
            FROM framework_tasks t 
            LEFT JOIN framework_epics e ON t.epic_id = e.id 
            WHERE e.id IS NULL
        """)
        orphan_tasks = cursor.fetchone()['count']
        
        self.validation_results.append({
            'test': 'Foreign Key Integrity',
            'status': 'PASS' if orphan_tasks == 0 else 'FAIL',
            'details': f'Orphan tasks: {orphan_tasks}'
        })
    
    def validate_required_fields(self):
        """Valida campos obrigatórios"""
        tests = [
            ("Epic Names", "SELECT COUNT(*) FROM framework_epics WHERE name IS NULL OR name = ''"),
            ("Task Titles", "SELECT COUNT(*) FROM framework_tasks WHERE title IS NULL OR title = ''"),
            ("Epic Keys", "SELECT COUNT(*) FROM framework_epics WHERE epic_key IS NULL OR epic_key = ''"),
            ("Task Keys", "SELECT COUNT(*) FROM framework_tasks WHERE task_key IS NULL OR task_key = ''")
        ]
        
        for test_name, query in tests:
            cursor = self.conn.execute(query)
            null_count = cursor.fetchone()[0]
            
            self.validation_results.append({
                'test': f'Required Fields - {test_name}',
                'status': 'PASS' if null_count == 0 else 'FAIL',
                'details': f'Null/empty values: {null_count}'
            })
    
    def validate_data_types(self):
        """Valida tipos de dados"""
        cursor = self.conn.execute("""
            SELECT COUNT(*) FROM framework_tasks 
            WHERE estimate_minutes < 0 OR estimate_minutes > 10080
        """)
        invalid_estimates = cursor.fetchone()[0]
        
        cursor = self.conn.execute("""
            SELECT COUNT(*) FROM framework_tasks 
            WHERE tdd_phase NOT IN ('red', 'green', 'refactor', 'analysis')
        """)
        invalid_phases = cursor.fetchone()[0]
        
        self.validation_results.extend([
            {
                'test': 'Estimate Minutes Range',
                'status': 'PASS' if invalid_estimates == 0 else 'FAIL',
                'details': f'Invalid estimates: {invalid_estimates}'
            },
            {
                'test': 'TDD Phase Values',
                'status': 'PASS' if invalid_phases == 0 else 'FAIL',
                'details': f'Invalid phases: {invalid_phases}'
            }
        ])
    
    def run_validation(self) -> List[Dict[str, Any]]:
        """Executa todas as validações"""
        self.connect()
        
        self.validate_record_counts()
        self.validate_foreign_keys()
        self.validate_required_fields()
        self.validate_data_types()
        
        self.conn.close()
        
        return self.validation_results
    
    def print_report(self):
        """Imprime relatório de validação"""
        print("\n" + "="*60)
        print("RELATÓRIO DE VALIDAÇÃO PÓS-MIGRAÇÃO")
        print("="*60)
        
        passed = sum(1 for r in self.validation_results if r['status'] == 'PASS')
        total = len(self.validation_results)
        
        print(f"\nResultado Geral: {passed}/{total} testes passaram")
        
        for result in self.validation_results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_icon} {result['test']}: {result['details']}")
        
        if passed == total:
            print("\n✅ Migração validada com sucesso!")
        else:
            print(f"\n⚠️  {total - passed} teste(s) falharam. Revisar dados.")

if __name__ == "__main__":
    validator = MigrationValidator('framework.db')
    validator.run_validation()
    validator.print_report()
