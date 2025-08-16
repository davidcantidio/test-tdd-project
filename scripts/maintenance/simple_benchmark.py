#!/usr/bin/env python3
"""
⚡ Simple Database Performance Test

Basic performance validation for framework database.
"""

import sqlite3
import time
import sys

def time_query(conn, name, query, params=None):
    """Time a single query."""
    cursor = conn.cursor()
    start_time = time.time()
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    result = cursor.fetchall()
    end_time = time.time()
    
    duration_ms = (end_time - start_time) * 1000
    status = "✅" if duration_ms < 50 else "⚠️" if duration_ms < 100 else "❌"
    
    print(f"{status} {name}: {duration_ms:.2f}ms ({len(result)} records)")
    return duration_ms

def run_simple_benchmark():
    """Run simple performance tests."""
    print("⚡ Simple Database Performance Test")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('framework.db')
        
        # Basic queries
        print("\n🔧 Basic Operations:")
        time_query(conn, "Count Users", "SELECT COUNT(*) FROM framework_users")
        time_query(conn, "Count Epics", "SELECT COUNT(*) FROM framework_epics") 
        time_query(conn, "Count Tasks", "SELECT COUNT(*) FROM framework_tasks")
        time_query(conn, "Count Sessions", "SELECT COUNT(*) FROM work_sessions")
        
        # Simple selects
        print("\n📊 Simple Queries:")
        time_query(conn, "Get All Users", "SELECT * FROM framework_users LIMIT 10")
        time_query(conn, "User Dashboard View", "SELECT * FROM user_dashboard LIMIT 5")
        time_query(conn, "Epic Progress View", "SELECT * FROM epic_progress LIMIT 5")
        
        # Indexed queries
        print("\n🔍 Indexed Queries:")
        time_query(conn, "Tasks by User", 
                  "SELECT * FROM framework_tasks WHERE assigned_to = 1 LIMIT 10")
        time_query(conn, "Tasks by Status", 
                  "SELECT * FROM framework_tasks WHERE status = 'completed' LIMIT 10")
        
        # Achievement queries
        print("\n🏆 Achievement Queries:")
        time_query(conn, "Achievement Types", "SELECT * FROM achievement_types")
        time_query(conn, "User Achievements", "SELECT * FROM user_achievements LIMIT 10")
        
        # System queries
        print("\n⚙️ System Queries:")
        time_query(conn, "System Settings", "SELECT * FROM system_settings")
        time_query(conn, "Database Info", 
                  "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view')")
        
        conn.close()
        print("\n✅ Simple benchmark completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return False

if __name__ == "__main__":
    success = run_simple_benchmark()
    sys.exit(0 if success else 1)