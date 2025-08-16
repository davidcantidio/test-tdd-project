#!/usr/bin/env python3
"""
🏗️ Hierarchy Migration Script - Schema v6
Migrates database to Client → Project → Epic → Task hierarchy

Features:
- Applies schema_extensions_v6.sql
- Creates default client and project
- Migrates existing epics to new hierarchy
- Validates data integrity
- Provides rollback capability
"""

import sqlite3
import sys
import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def get_database_path() -> Path:
    """Get database path."""
    return project_root / "framework.db"

def backup_database() -> Path:
    """Create backup before migration."""
    db_path = get_database_path()
    backup_path = project_root / f"framework_backup_v6_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    print(f"📦 Creating backup: {backup_path.name}")
    
    # Copy database file
    import shutil
    shutil.copy2(db_path, backup_path)
    
    print(f"✅ Backup created successfully")
    return backup_path

def apply_schema_v6(conn: sqlite3.Connection) -> bool:
    """Apply schema extensions v6 if needed."""

    schema_path = project_root / "schema_extensions_v6.sql"

    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False

    try:
        cursor = conn.cursor()

        # Check if project_id column already exists
        cursor.execute("PRAGMA table_info(framework_epics)")
        columns = [row[1] for row in cursor.fetchall()]
        if "project_id" in columns:
            print("ℹ️  project_id column already exists - skipping schema application")
            return True

        print(f"📋 Applying schema v6: {schema_path.name}")

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Execute schema in transaction
        cursor.executescript(schema_sql)
        conn.commit()

        print(f"✅ Schema v6 applied successfully")
        return True

    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        conn.rollback()
        return False

def create_default_client(conn: sqlite3.Connection) -> Optional[int]:
    """Create default 'Internal Development' client."""
    
    print("👤 Creating default client: Internal Development")
    
    client_data = {
        'client_key': 'internal',
        'name': 'Internal Development',
        'description': 'Internal development projects and frameworks',
        'industry': 'Software Development',
        'company_size': 'startup',
        'primary_contact_name': 'Development Team',
        'primary_contact_email': 'dev@internal.com',
        'timezone': 'America/Sao_Paulo',
        'currency': 'BRL',
        'preferred_language': 'pt-BR',
        'preferences': json.dumps({
            'default_methodology': 'Test-Driven Development',
            'enable_gamification': True,
            'default_epic_duration_unit': 'dias'
        }),
        'hourly_rate': 150.00,
        'contract_type': 'time_and_materials',
        'status': 'active',
        'client_tier': 'internal',
        'priority_level': 10,
        'access_level': 'admin',
        'created_by': 1  # dev_user
    }
    
    try:
        cursor = conn.cursor()
        
        # Check if client already exists
        cursor.execute("SELECT id FROM framework_clients WHERE client_key = ?", (client_data['client_key'],))
        existing = cursor.fetchone()
        
        if existing:
            client_id = existing[0]
            print(f"✅ Client already exists with ID: {client_id}")
            return client_id
        
        # Insert new client
        placeholders = ', '.join(['?' for _ in client_data])
        columns = ', '.join(client_data.keys())
        
        cursor.execute(
            f"INSERT INTO framework_clients ({columns}) VALUES ({placeholders})",
            list(client_data.values())
        )
        
        client_id = cursor.lastrowid
        conn.commit()
        
        print(f"✅ Default client created with ID: {client_id}")
        return client_id
        
    except Exception as e:
        print(f"❌ Error creating default client: {e}")
        conn.rollback()
        return None

def create_default_project(conn: sqlite3.Connection, client_id: int) -> Optional[int]:
    """Create default 'TDD Framework' project."""
    
    print("📁 Creating default project: TDD Framework")
    
    project_data = {
        'client_id': client_id,
        'project_key': 'tdd_framework',
        'name': 'TDD Framework',
        'description': 'Reusable Test-Driven Development framework with Streamlit interface, gamification, and multi-user support',
        'summary': 'Complete TDD framework for efficient development workflow with time tracking, analytics, and GitHub integration',
        'project_type': 'development',
        'methodology': 'Test-Driven Development',
        'objectives': json.dumps([
            'Create reusable TDD development framework',
            'Implement comprehensive time tracking and analytics',
            'Provide gamification for TDAH support',
            'Enable multi-user collaboration',
            'Integrate with GitHub Projects V2'
        ]),
        'deliverables': json.dumps([
            'Streamlit web interface',
            'SQLite database with complete schema',
            'TDD methodology implementation',
            'Gamification system',
            'Analytics and reporting dashboard',
            'GitHub integration',
            'Documentation and usage guides'
        ]),
        'success_criteria': json.dumps([
            'All core features implemented and tested',
            'Performance targets met (queries < 10ms)',
            'Documentation complete and comprehensive',
            'User interface intuitive and responsive',
            'Database integrity maintained',
            'Security standards implemented'
        ]),
        'planned_start_date': '2025-08-01',
        'planned_end_date': '2025-08-31',
        'actual_start_date': '2025-08-01',
        'estimated_hours': 200,
        'actual_hours': 0,  # Will be calculated from work sessions
        'budget_amount': 30000.00,
        'budget_currency': 'BRL',
        'hourly_rate': 150.00,
        'status': 'active',
        'priority': 10,
        'health_status': 'green',
        'completion_percentage': 0,  # Will be calculated
        'project_manager_id': 1,  # dev_user
        'technical_lead_id': 1,  # dev_user
        'repository_url': 'https://github.com/davidcantidio/test-tdd-project',
        'visibility': 'public',
        'access_level': 'admin',
        'complexity_score': 8.5,
        'quality_score': 9.0,
        'custom_fields': json.dumps({
            'framework_version': '1.2.1',
            'target_audience': 'developers',
            'supported_languages': ['Python'],
            'dependencies': ['streamlit', 'sqlite3', 'plotly']
        }),
        'tags': json.dumps(['tdd', 'framework', 'streamlit', 'gamification', 'analytics']),
        'labels': json.dumps(['internal', 'framework', 'v1.2.1']),
        'created_by': 1  # dev_user
    }
    
    try:
        cursor = conn.cursor()
        
        # Check if project already exists
        cursor.execute("SELECT id FROM framework_projects WHERE client_id = ? AND project_key = ?", 
                      (client_id, project_data['project_key']))
        existing = cursor.fetchone()
        
        if existing:
            project_id = existing[0]
            print(f"✅ Project already exists with ID: {project_id}")
            return project_id
        
        # Insert new project
        placeholders = ', '.join(['?' for _ in project_data])
        columns = ', '.join(project_data.keys())
        
        cursor.execute(
            f"INSERT INTO framework_projects ({columns}) VALUES ({placeholders})",
            list(project_data.values())
        )
        
        project_id = cursor.lastrowid
        conn.commit()
        
        print(f"✅ Default project created with ID: {project_id}")
        return project_id
        
    except Exception as e:
        print(f"❌ Error creating default project: {e}")
        conn.rollback()
        return None

def migrate_existing_epics(conn: sqlite3.Connection, project_id: int) -> bool:
    """Migrate existing epics to the new project."""
    
    print("🔄 Migrating existing epics to default project")
    
    try:
        cursor = conn.cursor()
        
        # Get current epics without project_id
        cursor.execute("SELECT id, epic_key, name FROM framework_epics WHERE project_id IS NULL AND deleted_at IS NULL")
        epics = cursor.fetchall()
        
        if not epics:
            print("✅ No epics to migrate (all already have project_id)")
            return True
        
        print(f"📊 Found {len(epics)} epics to migrate")
        
        # Update epics with project_id
        cursor.execute(
            "UPDATE framework_epics SET project_id = ?, updated_at = CURRENT_TIMESTAMP WHERE project_id IS NULL AND deleted_at IS NULL",
            (project_id,)
        )
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        print(f"✅ Migrated {affected_rows} epics to project ID {project_id}")
        
        # List migrated epics
        for epic_id, epic_key, epic_name in epics:
            print(f"  📋 {epic_key}: {epic_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error migrating epics: {e}")
        conn.rollback()
        return False

def check_orphan_epics(conn: sqlite3.Connection) -> bool:
    """Ensure there are no epics referencing non-existent projects."""

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, epic_key, project_id
        FROM framework_epics
        WHERE project_id IS NOT NULL
          AND project_id NOT IN (SELECT id FROM framework_projects)
        """
    )
    orphans = cursor.fetchall()
    if orphans:
        print("❌ Found orphaned epics:")
        for oid, ekey, pid in orphans:
            print(f"   • Epic {ekey} (ID {oid}) references missing project {pid}")
        return False

    print("✅ No orphaned epics found")
    return True


def add_foreign_key_constraint(conn: sqlite3.Connection) -> bool:
    """Add foreign key constraint from epics to projects if missing."""

    print("🔗 Adding foreign key constraint: epics → projects")

    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_key_list(framework_epics)")
        fks = cursor.fetchall()
        project_fk_exists = any(fk[2] == 'framework_projects' and fk[3] == 'project_id' for fk in fks)

        if project_fk_exists:
            print("✅ Foreign key constraint already exists")
            return True

        # Recreate table with FK constraint
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='framework_epics'")
        create_sql = cursor.fetchone()[0]
        new_create_sql = create_sql.rstrip(')') + \
            ",\n    FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE ON UPDATE NO ACTION)"

        cursor.execute("PRAGMA foreign_keys=off")
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("ALTER TABLE framework_epics RENAME TO framework_epics_old")
        cursor.execute(new_create_sql.replace("framework_epics", "framework_epics_new", 1))
        cursor.execute("INSERT INTO framework_epics_new SELECT * FROM framework_epics_old")
        cursor.execute("DROP TABLE framework_epics_old")
        cursor.execute("ALTER TABLE framework_epics_new RENAME TO framework_epics")
        cursor.execute("COMMIT")
        cursor.execute("PRAGMA foreign_keys=on")

        print("✅ Foreign key constraint added successfully")
        return True

    except Exception as e:
        cursor.execute("ROLLBACK")
        cursor.execute("PRAGMA foreign_keys=on")
        print(f"❌ Error adding foreign key constraint: {e}")
        return False

def validate_migration(conn: sqlite3.Connection) -> bool:
    """Validate the migration was successful."""
    
    print("🔍 Validating migration integrity")
    
    try:
        cursor = conn.cursor()
        
        # Check client was created
        cursor.execute("SELECT COUNT(*) FROM framework_clients WHERE client_key = 'internal'")
        client_count = cursor.fetchone()[0]
        
        if client_count != 1:
            print(f"❌ Expected 1 internal client, found {client_count}")
            return False
        
        # Check project was created
        cursor.execute("SELECT COUNT(*) FROM framework_projects WHERE project_key = 'tdd_framework'")
        project_count = cursor.fetchone()[0]
        
        if project_count != 1:
            print(f"❌ Expected 1 TDD framework project, found {project_count}")
            return False
        
        # Check epics were migrated
        cursor.execute("SELECT COUNT(*) FROM framework_epics WHERE project_id IS NULL AND deleted_at IS NULL")
        orphaned_epics = cursor.fetchone()[0]
        
        if orphaned_epics > 0:
            print(f"❌ Found {orphaned_epics} epics without project_id")
            return False
        
        # Check hierarchy integrity
        cursor.execute("""
            SELECT COUNT(*) FROM framework_epics e
            JOIN framework_projects p ON e.project_id = p.id
            JOIN framework_clients c ON p.client_id = c.id
            WHERE e.deleted_at IS NULL AND p.deleted_at IS NULL AND c.deleted_at IS NULL
        """)
        valid_hierarchy_epics = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM framework_epics WHERE deleted_at IS NULL")
        total_epics = cursor.fetchone()[0]
        
        if valid_hierarchy_epics != total_epics:
            print(f"❌ Hierarchy integrity check failed: {valid_hierarchy_epics}/{total_epics} epics in valid hierarchy")
            return False
        
        # Check views are working
        cursor.execute("SELECT COUNT(*) FROM hierarchy_overview")
        hierarchy_rows = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM client_dashboard")
        client_dashboard_rows = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM project_dashboard")
        project_dashboard_rows = cursor.fetchone()[0]
        
        print(f"✅ Validation successful:")
        print(f"  👤 Clients: 1 (internal)")
        print(f"  📁 Projects: 1 (tdd_framework)")
        print(f"  📋 Epics in hierarchy: {valid_hierarchy_epics}")
        print(f"  📊 Hierarchy view rows: {hierarchy_rows}")
        print(f"  📈 Dashboard views working: client({client_dashboard_rows}), project({project_dashboard_rows})")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def update_project_completion(conn: sqlite3.Connection) -> bool:
    """Update project completion percentage based on epic progress."""
    
    print("📊 Calculating project completion percentage")
    
    try:
        cursor = conn.cursor()
        
        # Calculate completion for TDD Framework project
        cursor.execute("""
            UPDATE framework_projects 
            SET completion_percentage = (
                SELECT ROUND(
                    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(t.id), 0), 2
                )
                FROM framework_epics e
                LEFT JOIN framework_tasks t ON e.id = t.epic_id
                WHERE e.project_id = framework_projects.id AND e.deleted_at IS NULL
            ),
            actual_hours = (
                SELECT COALESCE(SUM(ws.duration_minutes), 0) / 60.0
                FROM framework_epics e
                LEFT JOIN framework_tasks t ON e.id = t.epic_id
                LEFT JOIN work_sessions ws ON t.id = ws.task_id
                WHERE e.project_id = framework_projects.id AND e.deleted_at IS NULL
            ),
            updated_at = CURRENT_TIMESTAMP
            WHERE project_key = 'tdd_framework'
        """)
        
        conn.commit()
        
        # Get updated values
        cursor.execute("""
            SELECT completion_percentage, actual_hours 
            FROM framework_projects 
            WHERE project_key = 'tdd_framework'
        """)
        result = cursor.fetchone()
        
        if result:
            completion, hours = result
            print(f"✅ Project completion updated: {completion}% complete, {hours:.1f}h logged")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating project completion: {e}")
        conn.rollback()
        return False

def main():
    """Main migration function."""
    
    print("🏗️  Database Hierarchy Migration v6")
    print("=" * 50)
    print("Migrating to: Client → Project → Epic → Task")
    print()
    
    # Backup database
    backup_path = backup_database()
    
    try:
        # Connect to database
        db_path = get_database_path()
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        
        print(f"🔌 Connected to database: {db_path}")
        
        # Step 1: Apply schema v6
        if not apply_schema_v6(conn):
            print("❌ Migration failed at schema application")
            return False
        
        # Step 2: Create default client
        client_id = create_default_client(conn)
        if not client_id:
            print("❌ Migration failed at client creation")
            return False
        
        # Step 3: Create default project
        project_id = create_default_project(conn, client_id)
        if not project_id:
            print("❌ Migration failed at project creation")
            return False
        
        # Step 4: Migrate existing epics
        if not migrate_existing_epics(conn, project_id):
            print("❌ Migration failed at epic migration")
            return False
        
        # Step 5: Check for orphaned epics
        if not check_orphan_epics(conn):
            print("❌ Migration aborted due to orphaned epics")
            return False

        # Step 6: Add foreign key constraint
        if not add_foreign_key_constraint(conn):
            print("❌ Migration failed at constraint creation")
            return False

        # Step 7: Update project completion
        if not update_project_completion(conn):
            print("❌ Migration failed at completion calculation")
            return False

        # Step 8: Validate migration
        if not validate_migration(conn):
            print("❌ Migration validation failed")
            return False
        
        conn.close()
        
        print()
        print("🎉 Migration completed successfully!")
        print("=" * 50)
        print("✅ Database hierarchy implemented: Client → Project → Epic → Task")
        print(f"✅ Backup saved: {backup_path.name}")
        print("✅ All existing data preserved and migrated")
        print("✅ New views and indexes created")
        print("✅ Data integrity validated")
        print()
        print("Next steps:")
        print("1. Update Streamlit interface to use hierarchy")
        print("2. Update DatabaseManager methods")
        print("3. Test the new interface")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print(f"🔙 Restore from backup: {backup_path}")
        return False

def create_rollback_script():
    """Create rollback script for safety."""
    
    rollback_script = """#!/usr/bin/env python3
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
"""
    
    rollback_path = project_root / "rollback_hierarchy_v6.py"
    with open(rollback_path, 'w', encoding='utf-8') as f:
        f.write(rollback_script)
    
    # Make executable
    import stat
    rollback_path.chmod(rollback_path.stat().st_mode | stat.S_IEXEC)
    
    print(f"📜 Rollback script created: {rollback_path.name}")

if __name__ == "__main__":
    # Create rollback script first
    create_rollback_script()
    
    # Run migration
    success = main()
    
    if not success:
        print("\n🔙 Run rollback_hierarchy_v6.py to restore database")
        sys.exit(1)