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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    filename TEXT NOT NULL
                )
                """
            )
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
        parts = filename.split("_")
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
                statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

                for statement in statements:
                    conn.execute(statement)

                # Record migration as applied
                conn.execute(
                    "INSERT INTO schema_migrations (version, filename) VALUES (?, ?)",
                    (version, migration_file.name),
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
            "total_pending": len(pending_migrations),
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
            return
        print(f"\n✅ Migration complete - {result['applied']} migrations applied")
    else:
        print(f"\n❌ Migration failed - {result['applied']}/{result['total_pending']} applied")


if __name__ == "__main__":
    main()
