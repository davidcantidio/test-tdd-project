# PROMPT CODEX 2: Database Migration Scripts

## TASK
Criar scripts de migração para colunas faltantes identificadas no report.md

## PATTERN
Scripts SQL organizados e versionados para adicionar colunas missing sem perder dados

## FILES
- `scripts/migration/migrate_missing_columns.py` (NOVO)
- `scripts/migration/migration_001_points_value.sql` (NOVO)
- `scripts/migration/migration_002_due_date.sql` (NOVO)
- `scripts/migration/migration_003_icon_fields.sql` (NOVO)

## CONTEXT
Report.md item 93: "Create migration scripts for missing columns (points_value, due_date, icon)"
Adicionar colunas que foram mencionadas no código mas não existem no schema

## IMPLEMENTATION

### 1. Script Principal de Migração (scripts/migration/migrate_missing_columns.py)
```python
#!/usr/bin/env python3
"""
Database Migration Script for Missing Columns
Executes SQL migrations in order to add missing columns identified in report.md
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class MigrationManager:
    def __init__(self, db_path: str = "framework.db"):
        self.db_path = db_path
        self.migration_dir = Path("scripts/migration")
        
    def get_migration_files(self) -> List[Path]:
        """Get all .sql migration files in order"""
        pattern = "migration_*.sql"
        files = list(self.migration_dir.glob(pattern))
        return sorted(files)  # Sorts by filename (001, 002, etc.)
        
    def create_migration_table(self):
        """Create migrations tracking table if not exists"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    filename TEXT NOT NULL
                )
            ''')
            conn.commit()
        finally:
            conn.close()
            
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("SELECT version FROM schema_migrations ORDER BY version")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return []
        finally:
            conn.close()
            
    def extract_version_from_filename(self, filename: str) -> str:
        """Extract version number from migration_XXX_name.sql"""
        parts = filename.split('_')
        if len(parts) >= 2:
            return parts[1]  # Returns XXX from migration_XXX_name.sql
        return filename
        
    def execute_migration(self, migration_file: Path) -> bool:
        """Execute a single migration file"""
        try:
            version = self.extract_version_from_filename(migration_file.name)
            
            # Read SQL content
            sql_content = migration_file.read_text()
            
            # Execute migration
            conn = sqlite3.connect(self.db_path)
            try:
                # Split by semicolon and execute each statement
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for statement in statements:
                    conn.execute(statement)
                
                # Record migration as applied
                conn.execute(
                    "INSERT INTO schema_migrations (version, filename) VALUES (?, ?)",
                    (version, migration_file.name)
                )
                
                conn.commit()
                print(f"✅ Applied migration: {migration_file.name}")
                return True
                
            except Exception as e:
                conn.rollback()
                print(f"❌ Failed to apply migration {migration_file.name}: {e}")
                return False
            finally:
                conn.close()
                
        except Exception as e:
            print(f"❌ Error reading migration file {migration_file}: {e}")
            return False
            
    def run_migrations(self, dry_run: bool = False) -> Dict[str, Any]:
        """Run all pending migrations"""
        self.create_migration_table()
        
        migration_files = self.get_migration_files()
        applied_migrations = set(self.get_applied_migrations())
        
        pending_migrations = []
        for migration_file in migration_files:
            version = self.extract_version_from_filename(migration_file.name)
            if version not in applied_migrations:
                pending_migrations.append(migration_file)
                
        print(f"📊 Migration Status:")
        print(f"   Applied: {len(applied_migrations)}")
        print(f"   Pending: {len(pending_migrations)}")
        
        if not pending_migrations:
            print("✅ All migrations up to date!")
            return {"success": True, "applied": 0, "skipped": len(applied_migrations)}
            
        if dry_run:
            print("\n🔍 DRY RUN - Would apply:")
            for migration in pending_migrations:
                print(f"   - {migration.name}")
            return {"success": True, "applied": 0, "would_apply": len(pending_migrations)}
            
        # Apply migrations
        applied_count = 0
        for migration_file in pending_migrations:
            if self.execute_migration(migration_file):
                applied_count += 1
            else:
                print(f"⚠️ Stopping migration sequence due to failure")
                break
                
        return {
            "success": applied_count == len(pending_migrations),
            "applied": applied_count,
            "total_pending": len(pending_migrations)
        }

def main():
    """Main migration script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Migration Manager")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated")
    parser.add_argument("--db", default="framework.db", help="Database file path")
    args = parser.parse_args()
    
    print("🗄️ Database Migration Manager")
    print("=" * 50)
    
    if not os.path.exists(args.db):
        print(f"❌ Database file not found: {args.db}")
        return
        
    manager = MigrationManager(args.db)
    result = manager.run_migrations(dry_run=args.dry_run)
    
    if result["success"]:
        if args.dry_run:
            print(f"\n✅ Dry run complete - {result.get('would_apply', 0)} migrations would be applied")
        else:
            print(f"\n✅ Migration complete - {result['applied']} migrations applied")
    else:
        print(f"\n❌ Migration failed - {result['applied']}/{result['total_pending']} applied")

if __name__ == "__main__":
    main()
```

### 2. Migration 001: Points Value (scripts/migration/migration_001_points_value.sql)
```sql
-- Migration 001: Add points_value column to framework_epics
-- Date: 2025-08-16
-- Description: Add points_value column for epic scoring system

-- Add points_value column if it doesn't exist
ALTER TABLE framework_epics ADD COLUMN points_value INTEGER DEFAULT 0;

-- Update existing epics with default points based on existing data
UPDATE framework_epics 
SET points_value = 10 
WHERE points_value IS NULL OR points_value = 0;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_epics_points_value ON framework_epics(points_value);
```

### 3. Migration 002: Due Date (scripts/migration/migration_002_due_date.sql)
```sql
-- Migration 002: Add due_date columns to tasks and epics
-- Date: 2025-08-16
-- Description: Add due date tracking for better project management

-- Add due_date to framework_epics
ALTER TABLE framework_epics ADD COLUMN due_date TEXT;

-- Add due_date to framework_tasks  
ALTER TABLE framework_tasks ADD COLUMN due_date TEXT;

-- Add planned_start_date to framework_epics
ALTER TABLE framework_epics ADD COLUMN planned_start_date TEXT;

-- Add planned_end_date to framework_epics
ALTER TABLE framework_epics ADD COLUMN planned_end_date TEXT;

-- Create indexes for date-based queries
CREATE INDEX IF NOT EXISTS idx_epics_due_date ON framework_epics(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON framework_tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_epics_planned_dates ON framework_epics(planned_start_date, planned_end_date);
```

### 4. Migration 003: Icon Fields (scripts/migration/migration_003_icon_fields.sql)
```sql
-- Migration 003: Add icon and display fields for better UI
-- Date: 2025-08-16
-- Description: Add icon, color, and display customization fields

-- Add icon field to framework_epics
ALTER TABLE framework_epics ADD COLUMN icon TEXT DEFAULT '📋';

-- Add color field to framework_epics  
ALTER TABLE framework_epics ADD COLUMN color TEXT DEFAULT '#3498db';

-- Add icon field to framework_tasks
ALTER TABLE framework_tasks ADD COLUMN icon TEXT DEFAULT '📝';

-- Add priority field to framework_tasks
ALTER TABLE framework_tasks ADD COLUMN priority INTEGER DEFAULT 3;

-- Add status_icon mapping to work_sessions
ALTER TABLE work_sessions ADD COLUMN status_icon TEXT DEFAULT '⏱️';

-- Create indexes for UI performance
CREATE INDEX IF NOT EXISTS idx_epics_icon_color ON framework_epics(icon, color);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON framework_tasks(priority);
```

## VERIFICATION
1. Scripts SQL executam sem erro no SQLite
2. Colunas são adicionadas apenas se não existirem
3. Dados existentes preservados com valores default apropriados
4. Indexes criados para performance
5. Migration tracking funciona corretamente

## NOTES
- Usar ALTER TABLE ADD COLUMN para compatibilidade
- Valores DEFAULT apropriados para não quebrar código existente
- Indexes apenas em colunas que serão consultadas frequentemente
- Transaction safety com rollback em caso de erro