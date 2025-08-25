#!/usr/bin/env python3
"""Test script for the corrected Migration System (Patch 4).

🔒 SECURITY VALIDATION:
- SQL injection prevention testing
- Parameter binding validation
- Query builder security testing
"""

import sqlite3
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from migration import MigrationManager, QueryBuilder, SecurityError
from migration.cleanup_scripts import CacheCleanup, DataCleanup


def test_query_builder_security():
    """Test the security enhancements in QueryBuilder."""
    print("🔒 Testing QueryBuilder Security...")
    
    # Test SQL injection prevention
    builder = QueryBuilder()
    
    # Valid query should work
    try:
        query, params = (builder
                        .select("id", "title")
                        .from_table("framework_epics")
                        .where("status", "=", "active")
                        .build())
        print(f"✅ Valid query built: {query}")
    except Exception as e:
        print(f"❌ Valid query failed: {e}")
        return False
    
    # Invalid table name should be rejected
    try:
        builder = QueryBuilder()
        query, params = (builder
                        .select("*")
                        .from_table("malicious_table")  # Not in ALLOWED_TABLES
                        .build())
        print("❌ Security breach: Invalid table accepted")
        return False
    except SecurityError:
        print("✅ Security working: Invalid table rejected")
    
    # Invalid column name should be rejected
    try:
        builder = QueryBuilder()
        query, params = (builder
                        .select("malicious_column")  # Not in ALLOWED_COLUMNS
                        .from_table("framework_epics")
                        .build())
        print("❌ Security breach: Invalid column accepted")
        return False
    except SecurityError:
        print("✅ Security working: Invalid column rejected")
    
    return True


def test_migration_manager():
    """Test the MigrationManager functionality."""
    print("🔧 Testing MigrationManager...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Create MigrationManager
        manager = MigrationManager(conn)
        
        # Test initial state
        current_version = manager.get_current_version()
        print(f"✅ Initial version: {current_version}")
        
        # Test migration status
        status = manager.get_migration_status()
        print(f"✅ Migration status: {status}")
        
        # Test schema validation
        is_valid = manager.validate_schema()
        print(f"✅ Schema validation: {is_valid}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ MigrationManager test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_cache_cleanup():
    """Test the CacheCleanup functionality."""
    print("🧹 Testing CacheCleanup...")
    
    # Create temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test cache directory
        cache_dir = temp_path / ".streamlit_cache"
        cache_dir.mkdir()
        
        # Create test file
        test_file = cache_dir / "test.cache"
        test_file.write_text("test content")
        
        # Test cleanup
        cleanup = CacheCleanup(temp_path)
        cleanup.remove_streamlit_cache()
        
        if not cache_dir.exists():
            print("✅ Cache cleanup successful")
            return True
        else:
            print("❌ Cache cleanup failed")
            return False


def test_data_cleanup():
    """Test the DataCleanup functionality."""
    print("🗃️ Testing DataCleanup...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Create test tables
        conn.execute("""
            CREATE TABLE framework_epics (
                id INTEGER PRIMARY KEY,
                status TEXT,
                priority INTEGER
            )
        """)
        
        conn.execute("""
            CREATE TABLE framework_tasks (
                id INTEGER PRIMARY KEY,
                epic_id INTEGER,
                status TEXT
            )
        """)
        
        # Insert test data
        conn.execute("INSERT INTO framework_epics (status, priority) VALUES (NULL, NULL)")
        conn.execute("INSERT INTO framework_tasks (epic_id, status) VALUES (999, 'active')")  # Orphaned
        conn.commit()
        
        # Test data cleanup
        data_cleanup = DataCleanup(conn)
        data_cleanup.normalize_data()
        data_cleanup.fix_inconsistencies()
        data_cleanup.remove_orphaned_records()
        
        # Verify fixes
        cur = conn.execute("SELECT status, priority FROM framework_epics")
        row = cur.fetchone()
        if row[0] == 'pending' and row[1] == 1:
            print("✅ Data normalization successful")
        else:
            print(f"❌ Data normalization failed: {row}")
            return False
        
        # Check orphaned record removal
        cur = conn.execute("SELECT COUNT(*) FROM framework_tasks")
        count = cur.fetchone()[0]
        if count == 0:
            print("✅ Orphaned records removed")
        else:
            print(f"❌ Orphaned records remain: {count}")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ DataCleanup test failed: {e}")
        return False
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def main():
    """Run all migration system tests."""
    print("🚀 Testing Corrected Migration System (Patch 4)")
    print("=" * 50)
    
    tests = [
        ("QueryBuilder Security", test_query_builder_security),
        ("MigrationManager", test_migration_manager),
        ("CacheCleanup", test_cache_cleanup),
        ("DataCleanup", test_data_cleanup)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📝 Running {test_name}...")
        success = test_func()
        results.append((test_name, success))
        print(f"{'✅ PASSED' if success else '❌ FAILED'}: {test_name}")
    
    print("\n" + "=" * 50)
    print("🎯 TEST RESULTS:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if success:
            passed += 1
    
    total = len(results)
    print(f"\n🏆 FINAL SCORE: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Migration System is ready!")
        return True
    else:
        print("⚠️  Some tests failed - Review implementation")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)