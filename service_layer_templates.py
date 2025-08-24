#!/usr/bin/env python3
"""
🔧 Service Layer Migration Templates (Step 3.2.1 - CORRECTED)

Complete template system for migrating Batch 2 files from DatabaseManager 
to Service Layer + Modular API architecture.

Usage:
    from service_layer_templates import SERVICE_LAYER_TEMPLATES
    template = SERVICE_LAYER_TEMPLATES['epic_operations']
    old_pattern = template['old']
    new_pattern = template['new']

Categories:
- Epic Operations: Complete Epic CRUD with service layer
- Task Operations: Hybrid approach (get_tasks legacy + create/update service)
- Core Database: Infrastructure files requiring architectural integration
- Performance: Performance testing and optimization files
- Testing: Test files requiring service layer integration
"""

# ===============================================================================
# COMPREHENSIVE SERVICE LAYER MIGRATION TEMPLATES
# ===============================================================================

SERVICE_LAYER_TEMPLATES = {
    
    # Template 1: Epic Operations (Complete Service Layer Migration)
    'epic_operations': {
        'old': '''from streamlit_extension.utils.database import DatabaseManager
db_manager = DatabaseManager()
epics = db_manager.get_epics()
new_epic = db_manager.create_epic(data)
epic = db_manager.update_epic(epic_id, data)
db_manager.delete_epic(epic_id)''',
        
        'new': '''from streamlit_extension.database import list_epics
from streamlit_extension.services import ServiceContainer
service_container = ServiceContainer()
epic_service = service_container.get_epic_service()

epics = list_epics()  # Modular API - fast and optimized
new_epic = epic_service.create(data)  # Service layer for CRUD
epic = epic_service.update(epic_id, data)
epic_service.delete(epic_id)''',
        
        'description': 'Complete migration to service layer for Epic operations',
        'complexity': 'MEDIUM',
        'files': ['streamlit_extension/database/seed.py']
    },
    
    # Template 2: Task Operations (Hybrid Approach)
    'task_operations': {
        'old': '''from streamlit_extension.utils.database import DatabaseManager
db_manager = DatabaseManager()
tasks = db_manager.get_tasks()
new_task = db_manager.create_task(data)
task = db_manager.update_task(task_id, data)''',
        
        'new': '''# HYBRID: Use legacy for get_tasks (broken in modular API)
from streamlit_extension.utils.database import DatabaseManager
from streamlit_extension.services import ServiceContainer
db_manager = DatabaseManager()
service_container = ServiceContainer()
task_service = service_container.get_task_service()

tasks = db_manager.get_tasks()  # Keep legacy - modular API broken
new_task = task_service.create(data)  # Service layer for CRUD
task = task_service.update(task_id, data)''',
        
        'description': 'Hybrid approach - legacy get_tasks + service layer CRUD',
        'complexity': 'MEDIUM',
        'files': ['streamlit_extension/models/database.py']
    },
    
    # Template 3: Core Database Infrastructure
    'core_database': {
        'old': '''from streamlit_extension.utils.database import DatabaseManager
db_manager = DatabaseManager()
connection = db_manager.get_connection()
db_manager.initialize_database()
db_manager.execute_migration(sql)''',
        
        'new': '''from streamlit_extension.database import get_connection
from streamlit_extension.database.schema import DatabaseSchema
from streamlit_extension.services import ServiceContainer

connection = get_connection()  # Direct modular API
schema_manager = DatabaseSchema()
schema_manager.initialize_database()
schema_manager.execute_migration(sql)

# Service container for complex operations
service_container = ServiceContainer()''',
        
        'description': 'Core database infrastructure with architectural integration',
        'complexity': 'HIGH',
        'files': ['streamlit_extension/database/connection.py']
    },
    
    # Template 4: Performance and Testing Files
    'performance': {
        'old': '''from streamlit_extension.utils.database import DatabaseManager
def performance_test():
    db_manager = DatabaseManager()
    # Performance testing with DatabaseManager
    results = db_manager.benchmark_operations()
    return results''',
        
        'new': '''from streamlit_extension.database import get_connection
from streamlit_extension.utils.performance_tester import PerformanceTester
from streamlit_extension.services import ServiceContainer

def performance_test():
    # Use direct connection for performance testing
    connection = get_connection()
    performance_tester = PerformanceTester(connection)
    
    # Service container for business logic testing
    service_container = ServiceContainer()
    
    # Combined performance testing
    results = performance_tester.benchmark_operations()
    service_results = performance_tester.benchmark_services(service_container)
    
    return {**results, **service_results}''',
        
        'description': 'Performance testing with both connection and service layer',
        'complexity': 'MEDIUM',
        'files': [
            'scripts/migration/add_performance_indexes.py',
            'streamlit_extension/utils/cached_database.py',
            'streamlit_extension/utils/performance_tester.py'
        ]
    },
    
    # Template 5: Test Files (Service Layer Integration)
    'testing': {
        'old': '''import unittest
from streamlit_extension.utils.database import DatabaseManager

class TestDatabaseOperations(unittest.TestCase):
    def setUp(self):
        self.db_manager = DatabaseManager()
    
    def test_epic_operations(self):
        epics = self.db_manager.get_epics()
        self.assertIsNotNone(epics)''',
        
        'new': '''import unittest
from streamlit_extension.database import list_epics
from streamlit_extension.services import ServiceContainer
from streamlit_extension.utils.database import DatabaseManager

class TestDatabaseOperations(unittest.TestCase):
    def setUp(self):
        # Service layer for business operations
        self.service_container = ServiceContainer()
        self.epic_service = self.service_container.get_epic_service()
        
        # Legacy for fallback/hybrid operations
        self.db_manager = DatabaseManager()
    
    def test_epic_operations(self):
        # Use modular API for simple operations
        epics = list_epics()
        self.assertIsNotNone(epics)
        
        # Use service layer for business logic
        epic_result = self.epic_service.get_all()
        self.assertTrue(epic_result.success)''',
        
        'description': 'Test files with service layer integration',
        'complexity': 'MEDIUM',
        'files': [
            'tests/test_security_scenarios.py',
            'tests/test_database_manager_duration_extension.py',
            'tests/test_migration_schemas.py',
            'scripts/testing/api_equivalence_validation.py'
        ]
    },
    
    # Template 6: Validation Framework
    'validation': {
        'old': '''from streamlit_extension.utils.database import DatabaseManager
def validate_database_integrity():
    db_manager = DatabaseManager()
    issues = []
    # Validation logic with DatabaseManager
    return issues''',
        
        'new': '''from streamlit_extension.database.health import DatabaseHealthChecker
from streamlit_extension.services import ServiceContainer
from streamlit_extension.utils.database import DatabaseManager

def validate_database_integrity():
    issues = []
    
    # Use health checker for infrastructure validation
    health_checker = DatabaseHealthChecker()
    infrastructure_issues = health_checker.check_all()
    issues.extend(infrastructure_issues)
    
    # Use service layer for business logic validation
    service_container = ServiceContainer()
    business_issues = service_container.validate_business_integrity()
    issues.extend(business_issues)
    
    # Keep legacy for complex validation not yet migrated
    db_manager = DatabaseManager()
    legacy_issues = db_manager.validate_complex_constraints()
    issues.extend(legacy_issues)
    
    return issues''',
        
        'description': 'Validation framework with multi-layer approach',
        'complexity': 'HIGH',
        'files': ['batch2_checkpoints.py', 'migration_validation.py']
    }
}

# ===============================================================================
# UTILITY FUNCTIONS FOR TEMPLATE APPLICATION
# ===============================================================================

def get_template_for_file(file_path: str) -> dict:
    """
    Get the most appropriate template for a specific file.
    
    Args:
        file_path: Path to the file being migrated
    
    Returns:
        Dictionary with template information
    """
    # Core database infrastructure files
    if any(core_file in file_path for core_file in [
        'database/connection.py', 'database/schema.py'
    ]):
        return SERVICE_LAYER_TEMPLATES['core_database']
    
    # Epic-related files
    if 'seed.py' in file_path or 'epic' in file_path.lower():
        return SERVICE_LAYER_TEMPLATES['epic_operations']
    
    # Task-related files
    if 'task' in file_path.lower() or 'models/database.py' in file_path:
        return SERVICE_LAYER_TEMPLATES['task_operations']
    
    # Performance files
    if any(perf_file in file_path for perf_file in [
        'performance', 'cached_database', 'benchmark', 'add_performance_indexes'
    ]):
        return SERVICE_LAYER_TEMPLATES['performance']
    
    # Test files
    if file_path.startswith('tests/') or 'test_' in file_path:
        return SERVICE_LAYER_TEMPLATES['testing']
    
    # Validation files
    if any(val_file in file_path for val_file in [
        'validation', 'checkpoints', 'batch2_checkpoints'
    ]):
        return SERVICE_LAYER_TEMPLATES['validation']
    
    # Default to task operations (hybrid approach)
    return SERVICE_LAYER_TEMPLATES['task_operations']

def list_batch2_files() -> list:
    """
    List all files that should be migrated in Batch 2.
    Based on migration_execution_plan.md categorization.
    """
    return [
        # Core Database Infrastructure (3 files)
        'streamlit_extension/database/connection.py',
        'streamlit_extension/database/seed.py', 
        'streamlit_extension/models/database.py',
        
        # Performance & Testing Infrastructure (7 files)
        'scripts/migration/add_performance_indexes.py',
        'streamlit_extension/utils/cached_database.py',
        'streamlit_extension/utils/performance_tester.py',
        'tests/test_security_scenarios.py',
        'tests/test_database_manager_duration_extension.py',
        'tests/test_migration_schemas.py',
        'scripts/testing/api_equivalence_validation.py',
        
        # Testing & Validation Framework (5 files)
        'batch2_checkpoints.py',
        'migration_validation.py',
        'rollback_manager.py',
        'test_migration_validation_integration.py',
        'comprehensive_integrity_test.py'
    ]

def generate_migration_guide() -> str:
    """Generate complete migration guide for Batch 2 files."""
    guide = """
# 🔧 Service Layer Migration Guide (Batch 2)

## Templates Available:
"""
    for template_name, template_info in SERVICE_LAYER_TEMPLATES.items():
        guide += f"""
### {template_name.title().replace('_', ' ')}
**Complexity:** {template_info['complexity']}
**Description:** {template_info['description']}
**Files:** {len(template_info.get('files', []))} files

**OLD Pattern:**
```python
{template_info['old']}
```

**NEW Pattern:**  
```python
{template_info['new']}
```
"""
    
    guide += f"""
## Batch 2 Files ({len(list_batch2_files())} total):
"""
    for file_path in list_batch2_files():
        template = get_template_for_file(file_path)
        template_name = [k for k, v in SERVICE_LAYER_TEMPLATES.items() if v == template][0]
        guide += f"- `{file_path}` → **{template_name}** template\n"
    
    return guide

# ===============================================================================
# CONFIGURATION AND CONSTANTS
# ===============================================================================

# Service Layer Configuration
SERVICE_LAYER_CONFIG = {
    'use_modular_api': True,
    'fallback_to_legacy': True,
    'enable_service_container': True,
    'validate_service_availability': True
}

# Migration Safety Constants
MIGRATION_SAFETY = {
    'create_backups': True,
    'validate_syntax': True,
    'test_imports': True,
    'rollback_on_failure': True
}

# Batch 2 File Categories
BATCH2_CATEGORIES = {
    'CORE_DB_INFRASTRUCTURE': 3,
    'PERFORMANCE_TESTING': 7, 
    'TESTING_VALIDATION': 5
}

if __name__ == "__main__":
    # Generate and print migration guide when run directly
    print(generate_migration_guide())
    print(f"\n✅ Templates loaded successfully!")
    print(f"📊 Available templates: {len(SERVICE_LAYER_TEMPLATES)}")
    print(f"📁 Files to migrate: {len(list_batch2_files())}")