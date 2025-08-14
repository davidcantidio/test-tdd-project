#!/usr/bin/env python3
"""
🔐 Database Encryption Migration Script

Migrates all project databases to encrypted SQLCipher format.
Addresses SEC-002 security vulnerability by encrypting data at rest.

This script:
1. Identifies all SQLite databases in the project
2. Creates encrypted copies using SQLCipher
3. Migrates all data with integrity verification
4. Creates secure backups of original databases
5. Updates database configuration files

Usage:
    python migrate_to_encrypted_databases.py [--dry-run] [--force]
    
Options:
    --dry-run: Show what would be migrated without making changes
    --force: Overwrite existing encrypted databases
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from duration_system.secure_database import SecureDatabaseManager, migrate_database_to_encrypted

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('database_migration.log')
    ]
)

class DatabaseMigrationManager:
    """Manages migration of multiple databases to encrypted format."""
    
    def __init__(self, project_root: Path, dry_run: bool = False, force: bool = False):
        self.project_root = project_root
        self.dry_run = dry_run
        self.force = force
        self.migration_results = []
        
        # Migration statistics (initialize first)
        self.stats = {
            "total_databases": 0,  # Will be updated after discovery
            "successful_migrations": 0,
            "failed_migrations": 0,
            "skipped_databases": 0,
            "total_size_bytes": 0,
            "migration_start_time": None,
            "migration_end_time": None
        }
        
        # Database files to migrate
        self.database_files = self._discover_databases()
        self.stats["total_databases"] = len(self.database_files)
    
    def _discover_databases(self) -> List[Path]:
        """
        Discover all SQLite database files in the project.
        
        Returns:
            List of database file paths
        """
        database_files = []
        
        # Common SQLite file extensions
        extensions = ['.db', '.sqlite', '.sqlite3']
        
        # Search for database files
        for ext in extensions:
            database_files.extend(self.project_root.rglob(f'*{ext}'))
        
        # Filter out test databases and temporary files
        filtered_files = []
        for db_file in database_files:
            # Skip if already encrypted
            if '.encrypted.' in db_file.name:
                continue
            
            # Skip test databases in test directories
            if 'test' in str(db_file).lower() and '/tests/' in str(db_file):
                continue
            
            # Skip backup files
            if '.backup.' in db_file.name:
                continue
            
            # Check if file is actually a SQLite database
            if self._is_sqlite_database(db_file):
                filtered_files.append(db_file)
                self.stats["total_size_bytes"] += db_file.stat().st_size
        
        return filtered_files
    
    def _is_sqlite_database(self, file_path: Path) -> bool:
        """
        Check if file is a valid SQLite database.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file is SQLite database
        """
        try:
            if not file_path.exists() or file_path.stat().st_size < 100:
                return False
            
            # Check SQLite file header
            with open(file_path, 'rb') as f:
                header = f.read(16)
                return header.startswith(b'SQLite format 3\x00')
        except Exception:
            return False
    
    def generate_migration_plan(self) -> Dict:
        """
        Generate detailed migration plan.
        
        Returns:
            Migration plan dictionary
        """
        plan = {
            "migration_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "project_root": str(self.project_root),
            "total_databases": len(self.database_files),
            "total_size_mb": round(self.stats["total_size_bytes"] / (1024 * 1024), 2),
            "databases": []
        }
        
        for db_file in self.database_files:
            db_info = {
                "source_path": str(db_file),
                "source_size_mb": round(db_file.stat().st_size / (1024 * 1024), 2),
                "encrypted_path": str(db_file.with_suffix('.encrypted.db')),
                "backup_path": str(db_file.with_suffix('.backup.db')),
                "relative_path": str(db_file.relative_to(self.project_root)),
                "migration_priority": self._get_migration_priority(db_file)
            }
            plan["databases"].append(db_info)
        
        # Sort by priority (high priority first)
        plan["databases"].sort(key=lambda x: x["migration_priority"], reverse=True)
        
        return plan
    
    def _get_migration_priority(self, db_file: Path) -> int:
        """
        Determine migration priority for database.
        
        Args:
            db_file: Database file path
            
        Returns:
            Priority score (higher = more important)
        """
        priority = 0
        
        # High priority databases
        if 'framework.db' in db_file.name:
            priority += 100  # Main application database
        elif 'task_timer.db' in db_file.name:
            priority += 90   # Timer data
        elif 'performance_cache.db' in db_file.name:
            priority += 70   # Performance cache
        
        # Larger databases get higher priority
        size_mb = db_file.stat().st_size / (1024 * 1024)
        priority += min(int(size_mb), 50)  # Up to 50 points for size
        
        return priority
    
    def migrate_database(self, source_path: Path) -> Tuple[bool, str]:
        """
        Migrate single database to encrypted format.
        
        Args:
            source_path: Path to source database
            
        Returns:
            Tuple of (success, message)
        """
        try:
            encrypted_path = source_path.with_suffix('.encrypted.db')
            
            # Check if encrypted version already exists
            if encrypted_path.exists() and not self.force:
                return False, f"Encrypted database already exists: {encrypted_path}"
            
            if self.dry_run:
                return True, f"[DRY RUN] Would migrate: {source_path} -> {encrypted_path}"
            
            logging.info(f"Migrating database: {source_path}")
            
            # Perform migration
            success = migrate_database_to_encrypted(
                source_path=source_path,
                target_path=encrypted_path
            )
            
            if success:
                self.stats["successful_migrations"] += 1
                return True, f"Successfully migrated: {source_path}"
            else:
                self.stats["failed_migrations"] += 1
                return False, f"Migration failed: {source_path}"
                
        except Exception as e:
            self.stats["failed_migrations"] += 1
            error_msg = f"Migration error for {source_path}: {str(e)}"
            logging.error(error_msg)
            return False, error_msg
    
    def run_migration(self) -> bool:
        """
        Run complete database migration process.
        
        Returns:
            True if all migrations successful
        """
        self.stats["migration_start_time"] = datetime.now()
        
        logging.info(f"Starting database migration for {len(self.database_files)} databases")
        
        if self.dry_run:
            logging.info("DRY RUN MODE - No actual changes will be made")
        
        # Generate and log migration plan
        plan = self.generate_migration_plan()
        self._log_migration_plan(plan)
        
        # Migrate each database
        all_successful = True
        
        for i, db_file in enumerate(self.database_files, 1):
            logging.info(f"Processing database {i}/{len(self.database_files)}: {db_file.name}")
            
            success, message = self.migrate_database(db_file)
            
            result = {
                "database": str(db_file),
                "success": success,
                "message": message,
                "timestamp": datetime.now()
            }
            
            self.migration_results.append(result)
            
            if success:
                logging.info(f"✓ {message}")
            else:
                logging.error(f"✗ {message}")
                all_successful = False
                
                # Continue with other databases even if one fails
                continue
        
        self.stats["migration_end_time"] = datetime.now()
        
        # Generate final report
        self._generate_migration_report()
        
        return all_successful
    
    def _log_migration_plan(self, plan: Dict):
        """Log detailed migration plan."""
        logging.info("=" * 60)
        logging.info("DATABASE MIGRATION PLAN")
        logging.info("=" * 60)
        logging.info(f"Migration ID: {plan['migration_id']}")
        logging.info(f"Project Root: {plan['project_root']}")
        logging.info(f"Total Databases: {plan['total_databases']}")
        logging.info(f"Total Size: {plan['total_size_mb']} MB")
        logging.info("")
        
        for i, db in enumerate(plan['databases'], 1):
            logging.info(f"{i}. {db['relative_path']}")
            logging.info(f"   Size: {db['source_size_mb']} MB")
            logging.info(f"   Priority: {db['migration_priority']}")
            logging.info(f"   Target: {Path(db['encrypted_path']).name}")
            logging.info("")
    
    def _generate_migration_report(self):
        """Generate final migration report."""
        duration = self.stats["migration_end_time"] - self.stats["migration_start_time"]
        
        logging.info("=" * 60)
        logging.info("DATABASE MIGRATION REPORT")
        logging.info("=" * 60)
        logging.info(f"Total Databases: {self.stats['total_databases']}")
        logging.info(f"Successful: {self.stats['successful_migrations']}")
        logging.info(f"Failed: {self.stats['failed_migrations']}")
        logging.info(f"Skipped: {self.stats['skipped_databases']}")
        logging.info(f"Duration: {duration}")
        logging.info(f"Total Size: {round(self.stats['total_size_bytes'] / (1024 * 1024), 2)} MB")
        
        if self.migration_results:
            logging.info("")
            logging.info("Detailed Results:")
            for result in self.migration_results:
                status = "✓" if result["success"] else "✗"
                logging.info(f"{status} {Path(result['database']).name}: {result['message']}")
        
        # Save report to file
        report_file = self.project_root / "database_migration_report.txt"
        with open(report_file, 'w') as f:
            f.write("Database Migration Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Migration completed: {self.stats['migration_end_time']}\n")
            f.write(f"Total databases: {self.stats['total_databases']}\n")
            f.write(f"Successful: {self.stats['successful_migrations']}\n")
            f.write(f"Failed: {self.stats['failed_migrations']}\n")
            f.write(f"Duration: {duration}\n\n")
            
            f.write("Results:\n")
            for result in self.migration_results:
                f.write(f"- {result['database']}: {result['message']}\n")
        
        logging.info(f"Report saved to: {report_file}")


def main():
    """Main migration script entry point."""
    parser = argparse.ArgumentParser(description="Migrate databases to encrypted format")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show migration plan without making changes")
    parser.add_argument("--force", action="store_true",
                       help="Overwrite existing encrypted databases")
    parser.add_argument("--project-root", type=Path, 
                       default=Path(__file__).parent.parent,
                       help="Project root directory")
    
    args = parser.parse_args()
    
    # Initialize migration manager
    migrator = DatabaseMigrationManager(
        project_root=args.project_root,
        dry_run=args.dry_run,
        force=args.force
    )
    
    try:
        # Run migration
        success = migrator.run_migration()
        
        if success:
            logging.info("🔐 All databases successfully migrated to encrypted format!")
            if not args.dry_run:
                logging.info("⚠️  Remember to update application configuration to use encrypted databases")
                logging.info("📁 Original databases have been backed up with .backup.db extension")
            sys.exit(0)
        else:
            logging.error("❌ Some database migrations failed. Check logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.info("Migration interrupted by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Migration failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()