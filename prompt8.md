# PROMPT 8: Database Migration System

## 🎯 OBJETIVO
Implementar scripts de migração para resolver item do report.md: "Create migration scripts for missing columns (points_value, due_date, icon)."

## 📁 ARQUIVOS ALVO (SEM INTERSEÇÃO)
- `migrations/` (DIRETÓRIO NOVO)
- `migrations/001_add_missing_columns.sql` (NOVO)
- `migrations/002_create_indexes.sql` (NOVO)
- `migrations/003_data_cleanup.sql` (NOVO)
- `streamlit_extension/utils/migrator.py` (NOVO)
- `tests/test_migrations.py` (NOVO)

## 🚀 DELIVERABLES

### 1. Migration Scripts

#### `migrations/001_add_missing_columns.sql`
```sql
-- Migration: Add missing columns identified in report.md
-- Date: 2025-01-15
-- Description: Add points_value, due_date, icon columns to framework_epics table

-- Add points_value column for epic scoring
ALTER TABLE framework_epics 
ADD COLUMN points_value INTEGER DEFAULT 0;

-- Add due_date column for deadline tracking
ALTER TABLE framework_epics 
ADD COLUMN due_date TEXT;

-- Add icon column for visual identification
ALTER TABLE framework_epics 
ADD COLUMN icon TEXT DEFAULT '📋';

-- Update existing records with default values
UPDATE framework_epics 
SET points_value = COALESCE(points_earned, 0)
WHERE points_value IS NULL;

-- Add constraints
CREATE INDEX idx_epics_due_date ON framework_epics(due_date);
CREATE INDEX idx_epics_points_value ON framework_epics(points_value);
```

#### `migrations/002_create_indexes.sql`
```sql
-- Migration: Create performance indexes
-- Date: 2025-01-15
-- Description: Add indexes for heavy queries identified in report.md

-- Client search optimization
CREATE INDEX idx_clients_name_search ON framework_clients(name);
CREATE INDEX idx_clients_status_active ON framework_clients(status) WHERE status = 'active';

-- Project filtering optimization
CREATE INDEX idx_projects_client_status ON framework_projects(client_id, status);
CREATE INDEX idx_projects_created_date ON framework_projects(created_at);

-- Epic progress calculation optimization
CREATE INDEX idx_epics_project_status ON framework_epics(project_id, status);
CREATE INDEX idx_epics_progress_calc ON framework_epics(project_id, status, points_earned);

-- Task query optimization
CREATE INDEX idx_tasks_epic_status ON framework_tasks(epic_id, status);
CREATE INDEX idx_tasks_tdd_phase ON framework_tasks(tdd_phase, status);
```

#### `migrations/003_data_cleanup.sql`
```sql
-- Migration: Data cleanup and normalization
-- Date: 2025-01-15
-- Description: Clean up data inconsistencies

-- Normalize status values
UPDATE framework_clients SET status = 'active' WHERE status IN ('Active', 'ACTIVE');
UPDATE framework_projects SET status = 'active' WHERE status IN ('Active', 'ACTIVE');
UPDATE framework_epics SET status = 'active' WHERE status IN ('Active', 'ACTIVE');

-- Clean up null/empty values
UPDATE framework_epics SET icon = '📋' WHERE icon IS NULL OR icon = '';
UPDATE framework_tasks SET estimate_minutes = 60 WHERE estimate_minutes IS NULL OR estimate_minutes = 0;

-- Ensure referential integrity
DELETE FROM framework_projects WHERE client_id NOT IN (SELECT id FROM framework_clients);
DELETE FROM framework_epics WHERE project_id NOT IN (SELECT id FROM framework_projects);
DELETE FROM framework_tasks WHERE epic_id NOT IN (SELECT id FROM framework_epics);
```

### 2. Migration Manager (`streamlit_extension/utils/migrator.py`)

```python
"""
🔄 Database Migration System

Enterprise-grade migration management:
- Version tracking
- Rollback capabilities
- Dry-run mode
- Migration validation
- Backup before migration
- Progress tracking
"""

class Migration:
    """Individual migration representation."""
    def __init__(self, version, name, sql_file, description=""):
        self.version = version
        self.name = name
        self.sql_file = sql_file
        self.description = description
        self.executed_at = None
        self.rollback_sql = None

class MigrationManager:
    """Manages database migrations with version control."""
    
    def __init__(self, db_path, migrations_dir="migrations"):
        """Initialize migration manager."""
        
    def get_current_version(self):
        """Get current database schema version."""
        
    def get_pending_migrations(self):
        """Get list of pending migrations."""
        
    def get_applied_migrations(self):
        """Get list of applied migrations."""
        
    def validate_migration(self, migration):
        """Validate migration before execution."""
        
    def backup_database(self):
        """Create database backup before migration."""
        
    def execute_migration(self, migration, dry_run=False):
        """Execute single migration with validation."""
        
    def execute_pending_migrations(self, dry_run=False):
        """Execute all pending migrations."""
        
    def rollback_migration(self, target_version):
        """Rollback to specific version."""
        
    def generate_migration_report(self):
        """Generate migration status report."""
        
    def create_migration_table(self):
        """Create migrations tracking table."""
```

### 3. Test Suite (`tests/test_migrations.py`)

```python
"""Test database migration system."""

class TestMigrationManager:
    def test_migration_discovery(self):
        """Test migration file discovery."""
        
    def test_version_tracking(self):
        """Test migration version tracking."""
        
    def test_migration_execution(self):
        """Test migration execution with rollback."""
        
    def test_dry_run_mode(self):
        """Test dry-run migration execution."""
        
    def test_backup_creation(self):
        """Test database backup before migration."""
        
    def test_rollback_functionality(self):
        """Test migration rollback."""
```

## 🔧 REQUISITOS TÉCNICOS

1. **Version Control**: Track applied migrations
2. **Rollback Support**: Revert migrations safely
3. **Validation**: Pre-execution validation
4. **Backup**: Automatic backup before migration
5. **Dry Run**: Test mode without changes
6. **Reporting**: Migration status and history

## 📊 SUCCESS CRITERIA

- [ ] Missing columns (points_value, due_date, icon) adicionadas
- [ ] Performance indexes criados para queries pesadas
- [ ] Sistema de versionamento de migrations
- [ ] Backup automático antes de migrations
- [ ] Rollback functionality implementada
- [ ] Data cleanup e normalization executados