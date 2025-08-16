#!/usr/bin/env python3
'''
🔙 Rollback Script for Hierarchy Migration v6
Restores database to pre-v6 state
'''

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

def rollback_to_backup():
    project_root = Path(__file__).parent
    db_path = project_root / "framework.db"
    
    # Find latest backup
    backups = list(project_root.glob("framework_backup_v6_*.db"))
    if not backups:
        print("❌ No v6 backups found")
        return False
    
    latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
    
    print(f"🔙 Rolling back to: {latest_backup.name}")
    
    # Create rollback backup
    rollback_backup = project_root / f"framework_before_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(db_path, rollback_backup)
    
    # Restore from backup
    shutil.copy2(latest_backup, db_path)
    
    print(f"✅ Database rolled back successfully")
    print(f"📦 Pre-rollback backup: {rollback_backup.name}")
    
    return True

if __name__ == "__main__":
    rollback_to_backup()
