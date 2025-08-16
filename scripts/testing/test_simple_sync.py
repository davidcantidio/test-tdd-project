#!/usr/bin/env python3
"""
🧪 Simple Sync Test - Debug database lock issues
"""

import json
import sqlite3
import sys
from pathlib import Path

def test_simple_epic_insert():
    """Test simple epic insertion without complex operations."""
    
    # Load one epic
    epic_file = Path("epics/user_epics/epico_0.json")
    if not epic_file.exists():
        print("❌ Epic file not found")
        return False
        
    with open(epic_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    epic_data = data.get('epic', data)
    epic_key = epic_data.get('id', 'test')
    
    print(f"🔄 Testing simple insert for epic: {epic_key}")
    
    try:
        # Simple connection with WAL mode
        conn = sqlite3.connect('framework.db', timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=10000")
        
        # Check if epic already exists
        cursor = conn.execute(
            "SELECT COUNT(*) FROM framework_epics WHERE epic_key = ?", 
            (epic_key,)
        )
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"✅ Epic {epic_key} already exists in database")
        else:
            # Insert simple epic record
            conn.execute("""
                INSERT INTO framework_epics (
                    epic_key, name, summary, created_at, updated_at
                ) VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """, (
                epic_key,
                epic_data.get('name', 'Test Epic'),
                epic_data.get('summary', 'Test Summary')
            ))
            conn.commit()
            print(f"✅ Successfully inserted epic {epic_key}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Simple sync failed: {e}")
        return False

def test_connection_pool():
    """Test the fixed connection pool."""
    try:
        sys.path.append('.')
        from duration_system.database_transactions import DatabaseConnectionPool
        
        print("🔄 Testing connection pool...")
        
        pool = DatabaseConnectionPool('framework.db', max_connections=2, connection_timeout=5.0)
        
        with pool.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM framework_epics")
            count = cursor.fetchone()[0]
            print(f"✅ Connection pool works - {count} epics in database")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection pool test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Simple Database Sync Test")
    print("=" * 50)
    
    # Test 1: Basic connection
    print("\n📋 Test 1: Basic Connection")
    try:
        conn = sqlite3.connect('framework.db', timeout=2.0)
        conn.execute("SELECT 1")
        conn.close()
        print("✅ Basic connection works")
    except Exception as e:
        print(f"❌ Basic connection failed: {e}")
    
    # Test 2: Connection pool
    print("\n📋 Test 2: Connection Pool")
    test_connection_pool()
    
    # Test 3: Simple sync
    print("\n📋 Test 3: Simple Epic Insert")
    test_simple_epic_insert()
    
    print("\n✅ Test completed")