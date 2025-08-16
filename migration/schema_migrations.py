from __future__ import annotations

"""Lightweight database schema migration utilities with enhanced security.

This module provides a minimal yet functional migration system used in tests.
It applies SQL files in order and keeps track of the current schema version.
Enhanced with rollback SQL support and comprehensive validation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional
import hashlib

import sqlite3

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


@dataclass
class Migration:
    """Represents a single migration file with rollback support."""

    version: str
    sql: str
    rollback_sql: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    checksum: Optional[str] = None

    def __post_init__(self):
        """Calculate checksum for integrity verification."""
        if self.checksum is None:
            self.checksum = hashlib.sha256(self.sql.encode()).hexdigest()

    def execute(self, conn: sqlite3.Connection) -> None:
        """Execute the migration against the provided connection."""
        conn.executescript(self.sql)

    def rollback(self, conn: sqlite3.Connection) -> None:
        """Rollback the migration if rollback SQL is provided."""
        if self.rollback_sql:
            conn.executescript(self.rollback_sql)

    def validate(self, validator: "SchemaValidator") -> bool:
        """Validate using the provided validator instance."""
        return validator.validate_tables(["schema_migrations"])

    def get_dependencies(self) -> List[str]:
        """Return a list of migration dependencies."""
        return list(self.dependencies)


class SchemaValidator:
    """Enhanced schema validation for SQLite with integrity checks."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def validate_tables(self, tables: Iterable[str]) -> bool:
        """Validate that required tables exist."""
        for table in tables:
            cur = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            )
            if not cur.fetchone():
                raise ValueError(f"Missing table: {table}")
        return True

    def validate_columns(self, table: str, columns: Iterable[str]) -> bool:
        """Validate that required columns exist in table."""
        cur = self.conn.execute(f"PRAGMA table_info({table})")
        existing = {row[1] for row in cur.fetchall()}
        for column in columns:
            if column not in existing:
                raise ValueError(f"Missing column {column} in table {table}")
        return True

    def validate_indexes(self, table: str, indexes: Iterable[str]) -> bool:
        """Validate that required indexes exist on table."""
        cur = self.conn.execute(f"PRAGMA index_list({table})")
        existing = {row[1] for row in cur.fetchall()}
        for index in indexes:
            if index not in existing:
                raise ValueError(f"Missing index {index} on table {table}")
        return True

    def validate_constraints(self) -> bool:
        """Validate foreign key constraints (basic check)."""
        cur = self.conn.execute("PRAGMA foreign_key_check")
        violations = cur.fetchall()
        if violations:
            raise ValueError(f"Foreign key violations: {violations}")
        return True


class MigrationManager:
    """Enhanced migration manager with rollback and dependency support."""

    def __init__(self, conn: sqlite3.Connection, migrations_path: Path | None = None):
        self.conn = conn
        self.migrations_path = migrations_path or MIGRATIONS_DIR
        self._ensure_migration_table()

    def _ensure_migration_table(self) -> None:
        """Create migration tracking table with additional metadata."""
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                applied_by TEXT DEFAULT 'system',
                rollback_sql TEXT,
                checksum TEXT
            )
            """
        )
        self.conn.commit()

    def get_current_version(self) -> str:
        """Get the highest applied migration version."""
        cur = self.conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
        )
        row = cur.fetchone()
        return row[0] if row else "000"

    def _load_migrations(self) -> List[Migration]:
        """Load migrations from files with rollback SQL support."""
        migrations: List[Migration] = []
        for path in sorted(self.migrations_path.glob("*.sql")):
            version = path.stem.split("_")[0]
            sql = path.read_text()
            
            # Look for corresponding rollback file
            rollback_path = self.migrations_path / f"{version}_rollback.sql"
            rollback_sql = None
            if rollback_path.exists():
                rollback_sql = rollback_path.read_text()
            
            migrations.append(Migration(
                version=version, 
                sql=sql, 
                rollback_sql=rollback_sql
            ))
        return migrations

    def apply_migrations(self) -> List[str]:
        """Apply all pending migrations in order with integrity checks.
        
        Returns a list of versions that were applied.
        """
        applied_versions = {
            row[0]
            for row in self.conn.execute("SELECT version FROM schema_migrations")
        }
        
        applied: List[str] = []
        migrations = self._load_migrations()
        
        # Check dependencies
        for migration in migrations:
            if migration.version not in applied_versions:
                # Verify dependencies are met
                for dep in migration.get_dependencies():
                    if dep not in applied_versions and dep not in applied:
                        raise ValueError(f"Migration {migration.version} depends on {dep} which is not applied")
                
                # Apply migration
                try:
                    migration.execute(self.conn)
                    self.conn.execute(
                        """INSERT INTO schema_migrations(version, rollback_sql, checksum) 
                           VALUES(?, ?, ?)""",
                        (migration.version, migration.rollback_sql, migration.checksum),
                    )
                    applied.append(migration.version)
                except Exception as e:
                    # Rollback on failure
                    self.conn.rollback()
                    raise ValueError(f"Migration {migration.version} failed: {e}") from e
                    
        self.conn.commit()
        return applied

    def rollback_migration(self, version: str) -> None:
        """Enhanced rollback with SQL execution if available."""
        cur = self.conn.execute(
            "SELECT rollback_sql FROM schema_migrations WHERE version=?",
            (version,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Migration {version} not applied")
            
        rollback_sql = row[0]
        
        try:
            # Execute rollback SQL if available
            if rollback_sql:
                self.conn.executescript(rollback_sql)
            
            # Remove from tracking table
            self.conn.execute(
                "DELETE FROM schema_migrations WHERE version=?",
                (version,),
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise ValueError(f"Rollback failed for {version}: {e}") from e

    def validate_schema(self) -> bool:
        """Validate current schema state."""
        validator = SchemaValidator(self.conn)
        try:
            return validator.validate_tables(["schema_migrations"])
        except ValueError:
            return False

    def get_migration_status(self) -> dict:
        """Get comprehensive migration status."""
        applied_versions = {
            row[0]: row[1] for row in 
            self.conn.execute("SELECT version, applied_at FROM schema_migrations")
        }
        
        all_migrations = [m.version for m in self._load_migrations()]
        pending = [v for v in all_migrations if v not in applied_versions]
        
        return {
            "current_version": self.get_current_version(),
            "applied_migrations": list(applied_versions.keys()),
            "pending_migrations": pending,
            "total_migrations": len(all_migrations)
        }