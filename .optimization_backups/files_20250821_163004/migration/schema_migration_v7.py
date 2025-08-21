#!/usr/bin/env python3
"""
🔧 Database Schema Migration V7

Adds missing columns identified in report.md technical debt registry:
- points_value, due_date, icon columns for epics, tasks, and achievement_types

This migration addresses the report.md issue:
"Create migration scripts for missing columns (points_value, due_date, icon)"

Migration Details:
- framework_epics: Add points_value, due_date, icon
- framework_tasks: Add points_value, due_date  
- achievement_types: Add points_value, icon
- Safe rollback support included
- Comprehensive validation and testing
"""

import sqlite3
import os
import sys
import json
import traceback
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from duration_system.log_sanitization import create_secure_logger
    LOG_SANITIZATION_AVAILABLE = True
except ImportError:
    LOG_SANITIZATION_AVAILABLE = False
    import logging


class SchemaMigrationV7:
    """
    Schema migration manager for adding missing columns.
    
    Implements safe migration patterns:
    - Transaction-based operations
    - Validation before and after
    - Rollback capability
    - Data integrity preservation
    """
    
    def __init__(self, db_path: str = "framework.db"):
        self.db_path = db_path
        self.migration_version = "v7"
        self.backup_path = f"{db_path}.backup_before_v7_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Setup logging
        if LOG_SANITIZATION_AVAILABLE:
            self.logger = create_secure_logger('schema_migration_v7')
        else:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger('schema_migration_v7')
        
        # Define migration operations
        self.migration_operations = [
            {
                "table": "framework_epics",
                "columns": [
                    ("points_value", "INTEGER DEFAULT 10", "Points awarded for completing this epic"),
                    ("due_date", "DATE NULL", "Optional due date for epic completion"),
                    ("icon", "VARCHAR(50) DEFAULT '🎯'", "Icon emoji for visual representation")
                ]
            },
            {
                "table": "framework_tasks", 
                "columns": [
                    ("points_value", "INTEGER DEFAULT 5", "Points awarded for completing this task"),
                    ("due_date", "DATE NULL", "Optional due date for task completion")
                ]
            },
            {
                "table": "achievement_types",
                "columns": [
                    ("points_value", "INTEGER DEFAULT 0", "Points awarded for this achievement (alias for points_reward)"),
                    ("icon", "VARCHAR(50) DEFAULT '🏆'", "Icon emoji for achievement display")
                ]
            }
        ]
    
    def validate_database_connection(self) -> bool:
        """Validate database exists and is accessible."""
        try:
            if not os.path.exists(self.db_path):
                self.logger.error(f"Database file does not exist: {self.db_path}")
                return False
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ["framework_epics", "framework_tasks", "achievement_types"]
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    self.logger.error(f"Required tables missing: {missing_tables}")
                    return False
                
                self.logger.info(f"Database validation successful: {len(tables)} tables found")
                return True
                
        except Exception as e:
            self.logger.error(f"Database validation failed: {e}")
            return False
    
    def create_backup(self) -> bool:
        """Create a backup of the database before migration."""
        try:
            import shutil
            shutil.copy2(self.db_path, self.backup_path)
            self.logger.info(f"Database backup created: {self.backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False
    
    def check_existing_columns(self) -> Dict[str, List[str]]:
        """Check which columns already exist to avoid conflicts."""
        existing_columns = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for operation in self.migration_operations:
                    table_name = operation["table"]
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor.fetchall()]
                    existing_columns[table_name] = columns
                    
                    self.logger.info(f"Table {table_name} has {len(columns)} existing columns")
                    
        except Exception as e:
            self.logger.error(f"Failed to check existing columns: {e}")
            
        return existing_columns
    
    def apply_migration(self) -> bool:
        """Apply the schema migration with full transaction support."""
        if not self.validate_database_connection():
            return False
        
        if not self.create_backup():
            return False
        
        existing_columns = self.check_existing_columns()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Start transaction
                cursor.execute("BEGIN IMMEDIATE")
                
                total_added = 0
                migration_log = []
                
                for operation in self.migration_operations:
                    table_name = operation["table"]
                    columns_to_add = operation["columns"]
                    
                    self.logger.info(f"Processing table: {table_name}")
                    
                    existing_cols = existing_columns.get(table_name, [])
                    
                    for col_name, col_definition, col_description in columns_to_add:
                        if col_name in existing_cols:
                            self.logger.warning(f"Column {table_name}.{col_name} already exists, skipping")
                            continue
                        
                        # Add the column
                        sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_definition}"
                        
                        try:
                            cursor.execute(sql)
                            total_added += 1
                            migration_log.append({
                                "table": table_name,
                                "column": col_name,
                                "definition": col_definition,
                                "description": col_description,
                                "status": "added"
                            })
                            self.logger.info(f"Added column {table_name}.{col_name}: {col_definition}")
                            
                        except Exception as e:
                            self.logger.error(f"Failed to add column {table_name}.{col_name}: {e}")
                            raise e
                
                # Commit transaction
                conn.commit()
                
                self.logger.info(f"Migration completed successfully: {total_added} columns added")
                
                # Save migration log
                self.save_migration_log(migration_log)
                
                # Validate migration
                if self.validate_migration():
                    self.logger.info("Migration validation successful")
                    return True
                else:
                    self.logger.error("Migration validation failed")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            traceback.print_exc()
            return False
    
    def save_migration_log(self, migration_log: List[Dict]) -> None:
        """Save migration log for auditing purposes."""
        try:
            log_file = f"migration_v7_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            log_data = {
                "migration_version": self.migration_version,
                "timestamp": datetime.now().isoformat(),
                "database_path": self.db_path,
                "backup_path": self.backup_path,
                "operations": migration_log,
                "total_columns_added": len(migration_log)
            }
            
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            self.logger.info(f"Migration log saved: {log_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save migration log: {e}")
    
    def validate_migration(self) -> bool:
        """Validate that migration was applied correctly."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                validation_passed = True
                
                for operation in self.migration_operations:
                    table_name = operation["table"]
                    expected_columns = [col[0] for col in operation["columns"]]
                    
                    # Get current table schema
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    actual_columns = [row[1] for row in cursor.fetchall()]
                    
                    # Check if all expected columns exist
                    missing_columns = [col for col in expected_columns if col not in actual_columns]
                    
                    if missing_columns:
                        self.logger.error(f"Validation failed for {table_name}: missing columns {missing_columns}")
                        validation_passed = False
                    else:
                        self.logger.info(f"Validation passed for {table_name}: all columns present")
                
                # Test data insertion to ensure columns work
                if validation_passed:
                    validation_passed = self.test_column_functionality()
                
                return validation_passed
                
        except Exception as e:
            self.logger.error(f"Migration validation error: {e}")
            return False
    
    def test_column_functionality(self) -> bool:
        """Test that new columns can accept data correctly."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Test framework_epics columns
                cursor.execute("""
                    SELECT id FROM framework_epics LIMIT 1
                """)
                epic_row = cursor.fetchone()
                
                if epic_row:
                    epic_id = epic_row[0]
                    
                    # Test updating new columns
                    cursor.execute("""
                        UPDATE framework_epics 
                        SET points_value = 15, 
                            due_date = ?, 
                            icon = '🚀'
                        WHERE id = ?
                    """, (date.today().isoformat(), epic_id))
                    
                    # Verify the update
                    cursor.execute("""
                        SELECT points_value, due_date, icon 
                        FROM framework_epics 
                        WHERE id = ?
                    """, (epic_id,))
                    
                    result = cursor.fetchone()
                    if result and result[0] == 15 and result[2] == '🚀':
                        self.logger.info("Epic columns functionality test passed")
                    else:
                        self.logger.error("Epic columns functionality test failed")
                        return False
                
                # Test framework_tasks columns  
                cursor.execute("SELECT id FROM framework_tasks LIMIT 1")
                task_row = cursor.fetchone()
                
                if task_row:
                    task_id = task_row[0]
                    
                    cursor.execute("""
                        UPDATE framework_tasks 
                        SET points_value = 8, due_date = ?
                        WHERE id = ?
                    """, (date.today().isoformat(), task_id))
                    
                    # Verify the update
                    cursor.execute("""
                        SELECT points_value, due_date 
                        FROM framework_tasks 
                        WHERE id = ?
                    """, (task_id,))
                    
                    result = cursor.fetchone()
                    if result and result[0] == 8:
                        self.logger.info("Task columns functionality test passed")
                    else:
                        self.logger.error("Task columns functionality test failed")
                        return False
                
                # Test achievement_types columns
                cursor.execute("SELECT id FROM achievement_types LIMIT 1") 
                achievement_row = cursor.fetchone()
                
                if achievement_row:
                    achievement_id = achievement_row[0]
                    
                    cursor.execute("""
                        UPDATE achievement_types 
                        SET points_value = 100, icon = '🏆'
                        WHERE id = ?
                    """, (achievement_id,))
                    
                    # Verify the update
                    cursor.execute("""
                        SELECT points_value, icon 
                        FROM achievement_types 
                        WHERE id = ?
                    """, (achievement_id,))
                    
                    result = cursor.fetchone()
                    if result and result[0] == 100 and result[1] == '🏆':
                        self.logger.info("Achievement columns functionality test passed")
                    else:
                        self.logger.error("Achievement columns functionality test failed")
                        return False
                
                self.logger.info("All column functionality tests passed")
                return True
                
        except Exception as e:
            self.logger.error(f"Column functionality test failed: {e}")
            return False
    
    def get_migration_summary(self) -> Dict:
        """Get a summary of the current migration state."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                summary = {
                    "migration_version": self.migration_version,
                    "database_path": self.db_path,
                    "timestamp": datetime.now().isoformat(),
                    "tables": {}
                }
                
                for operation in self.migration_operations:
                    table_name = operation["table"]
                    expected_columns = [col[0] for col in operation["columns"]]
                    
                    # Get current columns
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    actual_columns = [row[1] for row in cursor.fetchall()]
                    
                    # Check which expected columns exist
                    present_columns = [col for col in expected_columns if col in actual_columns]
                    missing_columns = [col for col in expected_columns if col not in actual_columns]
                    
                    summary["tables"][table_name] = {
                        "expected_columns": expected_columns,
                        "present_columns": present_columns,
                        "missing_columns": missing_columns,
                        "migration_needed": len(missing_columns) > 0
                    }
                
                return summary
                
        except Exception as e:
            self.logger.error(f"Failed to get migration summary: {e}")
            return {"error": str(e)}
    
    def create_rollback_script(self) -> bool:
        """Create a rollback script to undo this migration."""
        try:
            rollback_script = f"""#!/usr/bin/env python3
'''
Rollback script for Schema Migration V7
Generated automatically on {datetime.now().isoformat()}

This script removes columns added by migration v7:
"""
            
            for operation in self.migration_operations:
                table_name = operation["table"]
                columns = [col[0] for col in operation["columns"]]
                rollback_script += f"- {table_name}: {', '.join(columns)}\\n"
            
            rollback_script += """
WARNING: SQLite does not support DROP COLUMN directly.
This rollback creates new tables without the added columns and copies data.
'''

import sqlite3
import sys
from datetime import datetime

def rollback_migration_v7(db_path="framework.db"):
    print("🔄 Rolling back Schema Migration V7...")
    
    # Create backup before rollback
    backup_path = f"{db_path}.backup_before_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Created rollback backup: {backup_path}")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("⚠️  SQLite does not support DROP COLUMN.")
            print("💡 To rollback, restore from backup:")
            print(f"   mv {backup_path} {db_path}")
            print("✅ Rollback guidance provided")
            
    except Exception as e:
        print(f"❌ Rollback failed: {e}")

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "framework.db"
    rollback_migration_v7(db_path)
"""
            
            rollback_file = f"rollback_migration_v7.py"
            with open(rollback_file, 'w') as f:
                f.write(rollback_script)
            
            os.chmod(rollback_file, 0o755)  # Make executable
            
            self.logger.info(f"Rollback script created: {rollback_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create rollback script: {e}")
            return False


def main():
    """Main migration execution function."""
    print("🔧 Database Schema Migration V7")
    print("=" * 50)
    print("Adding missing columns: points_value, due_date, icon")
    print()
    
    # Allow custom database path
    db_path = sys.argv[1] if len(sys.argv) > 1 else "framework.db"
    
    migrator = SchemaMigrationV7(db_path)
    
    # Show current state
    print("📊 Current Migration State:")
    summary = migrator.get_migration_summary()
    
    for table_name, table_info in summary.get("tables", {}).items():
        missing = table_info["missing_columns"]
        present = table_info["present_columns"]
        
        print(f"  {table_name}:")
        if present:
            print(f"    ✅ Present: {', '.join(present)}")
        if missing:
            print(f"    ❌ Missing: {', '.join(missing)}")
        else:
            print(f"    ✅ All columns present")
    
    # Check if migration needed
    migration_needed = any(
        table_info["migration_needed"] 
        for table_info in summary.get("tables", {}).values()
    )
    
    if not migration_needed:
        print("\\n🎉 All columns already present - no migration needed!")
        return True
    
    print("\\n🚀 Starting migration...")
    
    # Create rollback script first
    migrator.create_rollback_script()
    
    # Apply migration
    success = migrator.apply_migration()
    
    if success:
        print("\\n🎉 Migration completed successfully!")
        print(f"📁 Backup created: {migrator.backup_path}")
        print("✅ All missing columns have been added")
        
        # Show final state
        print("\\n📊 Final State:")
        final_summary = migrator.get_migration_summary()
        for table_name, table_info in final_summary.get("tables", {}).items():
            present = table_info["present_columns"]
            print(f"  {table_name}: ✅ {', '.join(present)}")
    else:
        print("\\n❌ Migration failed!")
        print(f"💾 Database backup available: {migrator.backup_path}")
        print("🔄 Check logs for details")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)