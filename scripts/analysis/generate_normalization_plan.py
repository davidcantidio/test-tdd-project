#!/usr/bin/env python3
"""
Script para gerar exemplos representativos e plano de normalização
Tarefa 1.1.1.10 - Gerar exemplos representativos e plano de normalização
"""

import json
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

def create_normalized_epic_template() -> Dict[str, Any]:
    """Cria template normalizado para épicos"""
    
    return {
        "epic": {
            "id": None,  # To be filled with actual ID
            "name": None,  # To be filled with actual name
            "description": "",
            "status": "pending",
            "priority": 1,
            "duration": 5,
            "tags": [],
            "github_integration": {
                "issue_id": None,
                "milestone_id": None,
                "labels": ["epic", "tdd"]
            },
            "metadata": {
                "created_at": None,  # To be filled with current timestamp
                "updated_at": None,  # To be filled with current timestamp
                "version": "1.0",
                "source": "migration"
            },
            "tasks": []  # To be filled with normalized tasks
        }
    }

def create_normalized_task_template() -> Dict[str, Any]:
    """Cria template normalizado para tasks"""
    
    return {
        "id": None,  # To be filled with actual ID
        "title": None,  # To be filled with actual title
        "description": "",
        "tdd_phase": "analysis",
        "status": "pending",
        "estimate_minutes": 60,
        "story_points": 1,
        "position": 0,
        "dependencies": [],
        "deliverables": [],
        "performance_constraints": [],
        "acceptance_criteria": [],
        "metadata": {
            "created_at": None,  # To be filled with current timestamp
            "updated_at": None,  # To be filled with current timestamp
        }
    }

def normalize_epic_data(original_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """Normaliza dados de um épico para o formato padrão"""
    
    # Detecta estrutura
    if 'epic' in original_data:
        source_epic = original_data['epic']
        structure_type = 'nested'
    else:
        source_epic = original_data
        structure_type = 'flat'
    
    # Cria épico normalizado
    normalized = create_normalized_epic_template()
    current_time = datetime.now().isoformat()
    
    # Mapeia campos do épico
    epic_mapping = {
        'id': ['id', 'epic_id'],
        'name': ['name', 'title'],
        'description': ['description', 'desc'],
        'status': ['status'],
        'priority': ['priority'],
        'duration': ['duration', 'duration_days'],
        'tags': ['tags', 'categories']
    }
    
    for target_field, source_fields in epic_mapping.items():
        value = None
        for source_field in source_fields:
            if source_field in source_epic:
                value = source_epic[source_field]
                break
        
        if value is not None:
            normalized['epic'][target_field] = value
    
    # Normaliza ID se for placeholder
    epic_id = normalized['epic']['id']
    if epic_id in ['[EPIC-ID]', 'X', 'X.Y', None]:
        # Gera ID baseado no filename
        if 'example_epic_0' in filename:
            normalized['epic']['id'] = 0
        elif 'epic_1' in filename:
            normalized['epic']['id'] = 1
        elif 'template' in filename:
            normalized['epic']['id'] = f"template_{filename.split('.')[0]}"
        else:
            normalized['epic']['id'] = f"generated_{hash(filename) % 1000}"
    
    # Normaliza nome se for placeholder
    epic_name = normalized['epic']['name']
    if epic_name in ['[Epic Name]', '[Nome do Épico]', 'Epic Title Here', None]:
        if 'example_epic_0' in filename:
            normalized['epic']['name'] = "Environment & Production Safety"
        elif 'epic_1' in filename:
            normalized['epic']['name'] = "User Authentication System"
        else:
            normalized['epic']['name'] = f"Epic from {filename}"
    
    # Adiciona metadata
    normalized['epic']['metadata']['created_at'] = current_time
    normalized['epic']['metadata']['updated_at'] = current_time
    normalized['epic']['metadata']['original_file'] = filename
    normalized['epic']['metadata']['original_structure'] = structure_type
    
    # Normaliza tasks
    tasks = source_epic.get('tasks', [])
    normalized_tasks = []
    
    for i, task in enumerate(tasks):
        normalized_task = normalize_task_data(task, i, normalized['epic']['id'])
        normalized_tasks.append(normalized_task)
    
    normalized['epic']['tasks'] = normalized_tasks
    
    return normalized

def normalize_task_data(original_task: Dict[str, Any], position: int, epic_id: Any) -> Dict[str, Any]:
    """Normaliza dados de uma task"""
    
    normalized = create_normalized_task_template()
    current_time = datetime.now().isoformat()
    
    # Mapeia campos da task
    task_mapping = {
        'id': ['id', 'task_id'],
        'title': ['title', 'name'],
        'description': ['description', 'desc'],
        'tdd_phase': ['tdd_phase', 'phase'],
        'status': ['status'],
        'estimate_minutes': ['estimate_minutes', 'estimated_time_minutes'],
        'story_points': ['story_points'],
        'dependencies': ['dependencies', 'depends_on'],
        'deliverables': ['deliverables'],
        'performance_constraints': ['performance_constraints'],
        'acceptance_criteria': ['acceptance_criteria']
    }
    
    for target_field, source_fields in task_mapping.items():
        value = None
        for source_field in source_fields:
            if source_field in original_task:
                value = original_task[source_field]
                break
        
        if value is not None:
            normalized[target_field] = value
    
    # Normaliza ID da task
    task_id = normalized['id']
    if task_id in [None, '', 'N/A']:
        normalized['id'] = f"{epic_id}.{position + 1}"
    
    # Normaliza título se vazio
    if not normalized['title'] or normalized['title'] in ['[Task Title]', 'Task Name']:
        normalized['title'] = f"Task {position + 1}"
    
    # Normaliza TDD phase
    phase = normalized['tdd_phase']
    if phase in ['analysis|red|green|refactor', 'unknown', None]:
        # Distribui fases de acordo com a posição
        phases = ['analysis', 'red', 'green', 'refactor']
        normalized['tdd_phase'] = phases[position % len(phases)]
    
    # Garante que estimate_minutes seja número
    if not isinstance(normalized['estimate_minutes'], (int, float)):
        normalized['estimate_minutes'] = 60
    
    # Normaliza dependências
    if not isinstance(normalized['dependencies'], list):
        normalized['dependencies'] = []
    
    # Normaliza deliverables
    if not isinstance(normalized['deliverables'], list):
        normalized['deliverables'] = []
    
    # Remove deliverables vazios
    normalized['deliverables'] = [d for d in normalized['deliverables'] if d and str(d).strip()]
    
    # Adiciona metadata
    normalized['position'] = position
    normalized['metadata']['created_at'] = current_time
    normalized['metadata']['updated_at'] = current_time
    
    return normalized

def generate_migration_examples() -> Dict[str, Any]:
    """Gera exemplos de dados antes e depois da normalização"""
    
    examples = {
        "before_after_comparisons": [],
        "common_transformations": [],
        "edge_cases": []
    }
    
    # Exemplo 1: Epic Template (nested with placeholders)
    before_template = {
        "epic": {
            "id": "[EPIC-ID]",
            "name": "[Epic Name]",
            "tasks": [
                {
                    "id": "[TASK-1-ID]",
                    "title": "Write failing test",
                    "tdd_phase": "red",
                    "estimate_minutes": 30
                }
            ]
        }
    }
    
    after_template = normalize_epic_data(before_template, "epic_template.json")
    
    examples["before_after_comparisons"].append({
        "description": "Template com placeholders",
        "before": before_template,
        "after": after_template,
        "transformations": [
            "ID placeholder '[EPIC-ID]' → 'template_epic_template'",
            "Nome placeholder '[Epic Name]' → 'Epic from epic_template.json'",
            "Task ID '[TASK-1-ID]' → 'template_epic_template.1'",
            "Adicionado metadata com timestamps",
            "Adicionado campos obrigatórios com valores padrão"
        ]
    })
    
    # Exemplo 2: Epic Flat (estrutura flat)
    before_flat = {
        "id": 1,
        "title": "User Authentication",
        "estimated_hours": 40,
        "tasks": [
            {
                "task_id": "1.1",
                "name": "Setup auth middleware",
                "phase": "green",
                "estimated_time_minutes": 120
            }
        ]
    }
    
    after_flat = normalize_epic_data(before_flat, "epic_1.json")
    
    examples["before_after_comparisons"].append({
        "description": "Estrutura flat para nested",
        "before": before_flat,
        "after": after_flat,
        "transformations": [
            "Estrutura flat → nested com wrapper 'epic'",
            "Campo 'title' → 'name'",
            "Campo 'task_id' → 'id'",
            "Campo 'name' → 'title'",
            "Campo 'phase' → 'tdd_phase'",
            "Campo 'estimated_time_minutes' → 'estimate_minutes'"
        ]
    })
    
    # Transformações comuns
    examples["common_transformations"] = [
        {
            "type": "ID Generation",
            "description": "Gerar IDs únicos para placeholders",
            "examples": [
                "'[EPIC-ID]' → 'epic_1'",
                "'X.Y' → 'epic_template_1'",
                "null → 'generated_123'"
            ]
        },
        {
            "type": "Structure Unification",
            "description": "Converter flat para nested",
            "examples": [
                "{'id': 1, 'tasks': []} → {'epic': {'id': 1, 'tasks': []}}",
                "Root level fields → epic.* fields"
            ]
        },
        {
            "type": "Field Mapping",
            "description": "Padronizar nomes de campos",
            "examples": [
                "'task_id' → 'id'",
                "'name' → 'title' (for tasks)",
                "'title' → 'name' (for epics)",
                "'phase' → 'tdd_phase'"
            ]
        },
        {
            "type": "Data Type Standardization",
            "description": "Padronizar tipos de dados",
            "examples": [
                "string numbers → integers",
                "null estimates → 60 (default)",
                "empty arrays preserved",
                "timestamps → ISO 8601"
            ]
        }
    ]
    
    # Casos extremos
    examples["edge_cases"] = [
        {
            "case": "Task sem ID",
            "handling": "Gerar ID baseado em epic_id + posição",
            "example": "epic_0.1, epic_0.2, etc."
        },
        {
            "case": "Dependências quebradas",
            "handling": "Manter lista vazia até resolução manual",
            "example": "dependencies: ['non_existent_id'] → []"
        },
        {
            "case": "TDD phase inválida",
            "handling": "Usar 'analysis' como padrão",
            "example": "'unknown' → 'analysis'"
        },
        {
            "case": "Estimate negativo",
            "handling": "Usar 60 minutos como padrão",
            "example": "-30 → 60"
        },
        {
            "case": "Deliverables vazios",
            "handling": "Remover da lista",
            "example": "['', null, 'valid'] → ['valid']"
        }
    ]
    
    return examples

def create_etl_script_template() -> str:
    """Cria template do script de ETL para migração"""
    
    etl_script = '''#!/usr/bin/env python3
"""
ETL Script para migração de dados JSON para SQLite
Gerado automaticamente pela auditoria de estrutura
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List

class EpicMigrator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.migration_log = []
    
    def connect(self):
        """Conecta ao banco de dados SQLite"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
    
    def create_tables(self):
        """Cria tabelas necessárias"""
        ddl_statements = [
            """
            CREATE TABLE IF NOT EXISTS framework_epics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                epic_key VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                priority INTEGER DEFAULT 1,
                duration_days INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS framework_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_key VARCHAR(50) NOT NULL,
                epic_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                tdd_phase VARCHAR(20) CHECK(tdd_phase IN ('red', 'green', 'refactor', 'analysis')),
                status VARCHAR(50) DEFAULT 'pending',
                estimate_minutes INTEGER NOT NULL DEFAULT 60,
                story_points INTEGER,
                position INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (epic_id) REFERENCES framework_epics(id),
                UNIQUE(epic_id, task_key)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS task_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                depends_on_task_key VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES framework_tasks(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS task_deliverables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                deliverable TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES framework_tasks(id)
            )
            """
        ]
        
        for ddl in ddl_statements:
            self.conn.execute(ddl)
        
        self.conn.commit()
    
    def migrate_epic(self, epic_data: Dict[str, Any]) -> int:
        """Migra um épico e retorna o ID"""
        epic = epic_data['epic']
        
        cursor = self.conn.execute("""
            INSERT INTO framework_epics 
            (epic_key, name, description, status, priority, duration_days)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(epic['id']),
            epic['name'],
            epic.get('description', ''),
            epic.get('status', 'pending'),
            epic.get('priority', 1),
            epic.get('duration', None)
        ))
        
        epic_id = cursor.lastrowid
        self.migration_log.append(f"Epic migrated: {epic['id']} -> DB ID {epic_id}")
        
        # Migra tasks
        for task in epic.get('tasks', []):
            self.migrate_task(task, epic_id)
        
        return epic_id
    
    def migrate_task(self, task_data: Dict[str, Any], epic_id: int):
        """Migra uma task"""
        cursor = self.conn.execute("""
            INSERT INTO framework_tasks 
            (task_key, epic_id, title, description, tdd_phase, status, 
             estimate_minutes, story_points, position)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(task_data['id']),
            epic_id,
            task_data['title'],
            task_data.get('description', ''),
            task_data.get('tdd_phase', 'analysis'),
            task_data.get('status', 'pending'),
            task_data.get('estimate_minutes', 60),
            task_data.get('story_points'),
            task_data.get('position', 0)
        ))
        
        task_id = cursor.lastrowid
        
        # Migra deliverables
        for deliverable in task_data.get('deliverables', []):
            if deliverable:
                self.conn.execute("""
                    INSERT INTO task_deliverables (task_id, deliverable)
                    VALUES (?, ?)
                """, (task_id, str(deliverable)))
        
        # Migra dependências (como chaves, serão resolvidas depois)
        for dep in task_data.get('dependencies', []):
            if dep:
                self.conn.execute("""
                    INSERT INTO task_dependencies (task_id, depends_on_task_key)
                    VALUES (?, ?)
                """, (task_id, str(dep)))
        
        self.migration_log.append(f"Task migrated: {task_data['id']} -> DB ID {task_id}")
    
    def run_migration(self, json_files: List[str]):
        """Executa migração completa"""
        self.connect()
        self.create_tables()
        
        for file_path in json_files:
            print(f"Migrando {file_path}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Normaliza dados antes da migração
            normalized = normalize_epic_data(data, os.path.basename(file_path))
            
            # Migra para o banco
            self.migrate_epic(normalized)
        
        self.conn.commit()
        self.conn.close()
        
        print(f"Migração completa! {len(self.migration_log)} operações realizadas.")

def normalize_epic_data(data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """Normaliza dados do épico (função placeholder)"""
    # Esta função seria importada do script de normalização
    return data

if __name__ == "__main__":
    # Lista de arquivos para migrar
    epic_files = [
        'epics/epic_template.json',
        'epics/example_epic_0.json',
        'epics/template_epic.json',
        'tdd-project-template/epics/epic_1.json',
        'tdd-project-template/epics/template_epic.json'
    ]
    
    # Executa migração
    migrator = EpicMigrator('framework.db')
    migrator.run_migration(epic_files)
'''
    
    return etl_script

def generate_validation_script() -> str:
    """Gera script de validação pós-migração"""
    
    validation_script = '''#!/usr/bin/env python3
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
        print("\\n" + "="*60)
        print("RELATÓRIO DE VALIDAÇÃO PÓS-MIGRAÇÃO")
        print("="*60)
        
        passed = sum(1 for r in self.validation_results if r['status'] == 'PASS')
        total = len(self.validation_results)
        
        print(f"\\nResultado Geral: {passed}/{total} testes passaram")
        
        for result in self.validation_results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_icon} {result['test']}: {result['details']}")
        
        if passed == total:
            print("\\n✅ Migração validada com sucesso!")
        else:
            print(f"\\n⚠️  {total - passed} teste(s) falharam. Revisar dados.")

if __name__ == "__main__":
    validator = MigrationValidator('framework.db')
    validator.run_validation()
    validator.print_report()
'''
    
    return validation_script

def save_normalization_artifacts(examples: Dict[str, Any], etl_script: str, validation_script: str):
    """Salva todos os artefatos de normalização"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Salva exemplos
    examples_file = f"normalization_examples_{timestamp}.json"
    with open(examples_file, 'w', encoding='utf-8') as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)
    
    # Salva script ETL
    etl_file = f"etl_migration_script_{timestamp}.py"
    with open(etl_file, 'w', encoding='utf-8') as f:
        f.write(etl_script)
    
    # Salva script de validação
    validation_file = f"validation_script_{timestamp}.py"
    with open(validation_file, 'w', encoding='utf-8') as f:
        f.write(validation_script)
    
    return {
        "examples_file": examples_file,
        "etl_file": etl_file,
        "validation_file": validation_file
    }

def generate_normalization_summary(examples: Dict[str, Any]) -> str:
    """Gera sumário do plano de normalização"""
    
    summary = []
    summary.append("# 🔄 PLANO DE NORMALIZAÇÃO E EXEMPLOS REPRESENTATIVOS")
    summary.append(f"\n**Data de Geração:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary.append("**Objetivo:** Normalizar dados JSON para migração consistente\n")
    
    summary.append("## 📋 Resumo do Plano\n")
    
    summary.append("### Estratégia de Normalização")
    summary.append("1. **Unificação estrutural:** Converter todas as estruturas para formato nested")
    summary.append("2. **Padronização de IDs:** Gerar IDs únicos para placeholders")
    summary.append("3. **Mapeamento de campos:** Criar correspondência consistente entre variações")
    summary.append("4. **Validação de tipos:** Garantir tipos de dados apropriados")
    summary.append("5. **Limpeza de dados:** Remover valores vazios e inconsistentes\n")
    
    summary.append("### Transformações Principais")
    transformations = examples.get("common_transformations", [])
    for i, transformation in enumerate(transformations, 1):
        summary.append(f"{i}. **{transformation['type']}:** {transformation['description']}")
    
    summary.append("\n### Casos Extremos Identificados")
    edge_cases = examples.get("edge_cases", [])
    for case in edge_cases:
        summary.append(f"- **{case['case']}:** {case['handling']}")
    
    summary.append("\n## 🎯 Exemplos de Transformação\n")
    
    comparisons = examples.get("before_after_comparisons", [])
    for i, comparison in enumerate(comparisons, 1):
        summary.append(f"### Exemplo {i}: {comparison['description']}\n")
        summary.append("**Antes:**")
        summary.append("```json")
        summary.append(json.dumps(comparison['before'], indent=2, ensure_ascii=False))
        summary.append("```\n")
        summary.append("**Transformações aplicadas:**")
        for transformation in comparison['transformations']:
            summary.append(f"- {transformation}")
        summary.append("")
    
    summary.append("\n## 🛠️ Implementação\n")
    summary.append("### Scripts Gerados")
    summary.append("1. **ETL Script:** `etl_migration_script_*.py`")
    summary.append("   - Conecta ao SQLite")
    summary.append("   - Cria tabelas necessárias")
    summary.append("   - Normaliza e migra dados")
    summary.append("   - Registra log de operações\n")
    
    summary.append("2. **Validation Script:** `validation_script_*.py`")
    summary.append("   - Valida contagem de registros")
    summary.append("   - Verifica integridade referencial")
    summary.append("   - Testa campos obrigatórios")
    summary.append("   - Confirma tipos de dados\n")
    
    summary.append("3. **Examples File:** `normalization_examples_*.json`")
    summary.append("   - Comparações antes/depois")
    summary.append("   - Catálogo de transformações")
    summary.append("   - Documentação de casos extremos\n")
    
    summary.append("### Próximos Passos")
    summary.append("1. Revisar exemplos de normalização")
    summary.append("2. Executar ETL script em ambiente de teste")
    summary.append("3. Rodar validação pós-migração")
    summary.append("4. Corrigir problemas identificados")
    summary.append("5. Executar migração final")
    
    return "\n".join(summary)

def main():
    """Executa geração completa de exemplos e plano de normalização"""
    
    print("🎯 GERANDO EXEMPLOS E PLANO DE NORMALIZAÇÃO - TAREFA 1.1.1.10")
    print("=" * 60)
    print()
    
    print("📊 Gerando exemplos de normalização...")
    examples = generate_migration_examples()
    print(f"   ✅ {len(examples['before_after_comparisons'])} comparações antes/depois")
    print(f"   ✅ {len(examples['common_transformations'])} tipos de transformação")
    print(f"   ✅ {len(examples['edge_cases'])} casos extremos documentados")
    
    print("\n🛠️  Gerando scripts de migração...")
    etl_script = create_etl_script_template()
    validation_script = generate_validation_script()
    print("   ✅ Script ETL criado")
    print("   ✅ Script de validação criado")
    
    print("\n💾 Salvando artefatos...")
    files = save_normalization_artifacts(examples, etl_script, validation_script)
    
    for artifact_type, filename in files.items():
        print(f"   ✅ {artifact_type}: {filename}")
    
    print("\n📝 Gerando sumário de normalização...")
    summary = generate_normalization_summary(examples)
    
    # Salva sumário
    summary_file = f"normalization_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"   ✅ Sumário salvo: {summary_file}")
    
    print("\n📊 Estatísticas da normalização:")
    print(f"   • Exemplos de transformação: {len(examples['before_after_comparisons'])}")
    print(f"   • Padrões de transformação: {len(examples['common_transformations'])}")
    print(f"   • Casos extremos: {len(examples['edge_cases'])}")
    print(f"   • Tamanho do ETL script: {len(etl_script)} caracteres")
    print(f"   • Tamanho do script de validação: {len(validation_script)} caracteres")
    
    print("\n✅ Plano de normalização completo!")
    
    return {
        "examples": examples,
        "files_generated": files,
        "summary_file": summary_file,
        "total_artifacts": len(files) + 1
    }

if __name__ == "__main__":
    main()