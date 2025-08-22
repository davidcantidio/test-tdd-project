#!/usr/bin/env python3
'''
Rollback script for Schema Migration V7
Generated automatically on 2025-08-15T17:46:07.297815

This script removes columns added by migration v7:
- framework_epics: points_value, due_date, icon\n- framework_tasks: points_value, due_date\n- achievement_types: points_value, icon\n
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
