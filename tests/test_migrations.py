"""Test database migration system."""
import os
import sqlite3
import tempfile
import shutil
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from streamlit_extension.utils.migrator import MigrationManager


def _create_initial_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("CREATE TABLE framework_clients (id INTEGER PRIMARY KEY, name TEXT, status TEXT);")
    cur.execute(
        "CREATE TABLE framework_projects (id INTEGER PRIMARY KEY, client_id INTEGER, status TEXT, created_at TEXT);"
    )
    cur.execute(
        "CREATE TABLE framework_epics (id INTEGER PRIMARY KEY, project_id INTEGER, status TEXT, points_earned INTEGER);"
    )
    cur.execute(
        "CREATE TABLE framework_tasks (id INTEGER PRIMARY KEY, epic_id INTEGER, status TEXT, tdd_phase TEXT, estimate_minutes INTEGER);"
    )
    conn.commit()


class TestMigrationManager:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test.db")
        conn = sqlite3.connect(self.db_path)
        _create_initial_schema(conn)
        conn.close()
        # migrations directory relative to repo root
        self.migrations_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "migrations"))

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_migration_discovery(self):
        """Test migration file discovery."""
        manager = MigrationManager(self.db_path, migrations_dir=self.migrations_dir)
        pending = manager.get_pending_migrations()
        assert pending, "No migrations discovered"
        assert pending[0].version == 1

    def test_version_tracking(self):
        """Test migration version tracking."""
        manager = MigrationManager(self.db_path, migrations_dir=self.migrations_dir)
        manager.execute_pending_migrations()
        assert manager.get_current_version() >= 3

    def test_migration_execution(self):
        """Test migration execution with rollback."""
        manager = MigrationManager(self.db_path, migrations_dir=self.migrations_dir)
        manager.execute_pending_migrations()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(framework_epics)")
        columns = {row[1] for row in cur.fetchall()}
        conn.close()
        assert {"points_value", "due_date", "icon"}.issubset(columns)
        manager.rollback_migration(0)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(framework_epics)")
        columns = {row[1] for row in cur.fetchall()}
        conn.close()
        assert "points_value" not in columns

    def test_dry_run_mode(self):
        """Test dry-run migration execution."""
        manager = MigrationManager(self.db_path, migrations_dir=self.migrations_dir)
        manager.execute_pending_migrations(dry_run=True)
        assert manager.get_current_version() == 0

    def test_backup_creation(self):
        """Test database backup before migration."""
        manager = MigrationManager(self.db_path, migrations_dir=self.migrations_dir)
        manager.execute_pending_migrations()
        backups = [f for f in os.listdir(self.tmpdir) if f.startswith("test.db.backup")] 
        assert backups, "Backup not created"

    def test_rollback_functionality(self):
        """Test migration rollback."""
        manager = MigrationManager(self.db_path, migrations_dir=self.migrations_dir)
        manager.execute_pending_migrations()
        manager.rollback_migration(0)
        assert manager.get_current_version() == 0
