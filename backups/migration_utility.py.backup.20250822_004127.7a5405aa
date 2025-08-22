#!/usr/bin/env python3
"""Migration utility script for database management.

🔧 USAGE:
  python migration_utility.py status          # Show migration status
  python migration_utility.py apply           # Apply pending migrations
  python migration_utility.py rollback <ver>  # Rollback specific version
  python migration_utility.py validate        # Validate schema
"""

import sys
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from migration import MigrationManager


def main():
    """Main CLI interface for migration management."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Connect to framework database
    db_path = "framework.db"
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    manager = MigrationManager(conn)
    
    try:
        if command == "status":
            status = manager.get_migration_status()
            print("📊 MIGRATION STATUS")
            print("=" * 30)
            print(f"Current Version: {status['current_version']}")
            print(f"Applied: {len(status['applied_migrations'])}")
            print(f"Pending: {len(status['pending_migrations'])}")
            if status['applied_migrations']:
                print(f"Applied Migrations: {', '.join(status['applied_migrations'])}")
            if status['pending_migrations']:
                print(f"Pending Migrations: {', '.join(status['pending_migrations'])}")
        
        elif command == "apply":
            print("🚀 Applying migrations...")
            applied = manager.apply_migrations()
            if applied:
                print(f"✅ Applied: {', '.join(applied)}")
            else:
                print("ℹ️  No pending migrations")
        
        elif command == "rollback":
            if len(sys.argv) < 3:
                print("❌ Usage: python migration_utility.py rollback <version>")
                sys.exit(1)
            version = sys.argv[2]
            print(f"🔄 Rolling back migration {version}...")
            manager.rollback_migration(version)
            print(f"✅ Rollback completed for {version}")
        
        elif command == "validate":
            print("🔍 Validating schema...")
            is_valid = manager.validate_schema()
            if is_valid:
                print("✅ Schema is valid")
            else:
                print("❌ Schema validation failed")
                sys.exit(1)
        
        else:
            print(f"❌ Unknown command: {command}")
            print(__doc__)
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()