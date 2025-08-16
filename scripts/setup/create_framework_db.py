#!/usr/bin/env python3
"""
🗄️ Framework Database Creator

Creates framework.db with complete schema and validates the creation.
"""

import sqlite3
import sys
from pathlib import Path

def create_framework_database():
    """Create framework.db with complete schema."""
    
    # Read the schema file
    schema_file = Path("framework_v3.sql")
    if not schema_file.exists():
        print("❌ Error: framework_v3.sql not found")
        return False
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    try:
        # Create database connection
        conn = sqlite3.connect('framework.db')
        cursor = conn.cursor()
        
        print("🗄️ Creating framework.db with complete schema...")
        
        # Execute schema
        cursor.executescript(schema_sql)
        
        # Validate creation by checking tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"✅ Database created successfully with {len(tables)} tables:")
        for table in tables:
            print(f"  📋 {table[0]}")
        
        # Validate views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = cursor.fetchall()
        
        print(f"✅ Created {len(views)} views:")
        for view in views:
            print(f"  👁️ {view[0]}")
        
        # Validate triggers
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        triggers = cursor.fetchall()
        
        print(f"✅ Created {len(triggers)} triggers:")
        for trigger in triggers:
            print(f"  ⚡ {trigger[0]}")
        
        # Validate indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = cursor.fetchall()
        
        print(f"✅ Created {len(indexes)} custom indexes:")
        for index in indexes:
            print(f"  🔍 {index[0]}")
        
        # Test basic queries
        print("\n🧪 Testing basic functionality...")
        
        # Test user dashboard view
        cursor.execute("SELECT COUNT(*) FROM user_dashboard")
        dashboard_count = cursor.fetchone()[0]
        print(f"  📊 User dashboard: {dashboard_count} users")
        
        # Test achievement types
        cursor.execute("SELECT COUNT(*) FROM achievement_types")
        achievements_count = cursor.fetchone()[0]
        print(f"  🏆 Achievement types: {achievements_count} configured")
        
        # Test system settings
        cursor.execute("SELECT COUNT(*) FROM system_settings")
        settings_count = cursor.fetchone()[0]
        print(f"  ⚙️ System settings: {settings_count} configured")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 Framework database created successfully!")
        print(f"📁 Database file: {Path('framework.db').absolute()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    success = create_framework_database()
    sys.exit(0 if success else 1)