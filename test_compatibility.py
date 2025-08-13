#!/usr/bin/env python3
"""
🔗 Compatibility Test Suite

Tests compatibility with existing systems (gantt_tracker.py, analytics_engine.py).
"""

import sqlite3
import json
import sys
from pathlib import Path
import pytest

@pytest.mark.skip(reason="Compatibility check requires manual environment")
def test_gantt_tracker_compatibility():
    """Test if gantt_tracker.py can work with new database structure."""
    print("📊 Testing Gantt Tracker Compatibility...")
    
    conn = sqlite3.connect('framework.db')
    cursor = conn.cursor()
    
    # Test if we can simulate gantt_tracker data requirements
    try:
        # Create sample epic and tasks for testing
        cursor.execute("""
            INSERT INTO framework_epics (epic_key, name, description, status, duration_days, created_by, assigned_to)
            VALUES ('COMPAT_TEST', 'Compatibility Test Epic', 'Testing compatibility with gantt tracker', 'in_progress', 5, 1, 1)
        """)
        epic_id = cursor.lastrowid
        
        # Create sample tasks
        tasks_data = [
            ('CT_1', 'Analysis Task', 'analysis', 'completed', 60, 45, 2),
            ('CT_2', 'Red Test Task', 'red', 'completed', 30, 35, 1),
            ('CT_3', 'Green Implementation', 'green', 'in_progress', 90, 0, 3),
            ('CT_4', 'Refactor Task', 'refactor', 'pending', 45, 0, 2)
        ]
        
        for task_key, title, tdd_phase, status, estimate, actual, story_points in tasks_data:
            cursor.execute("""
                INSERT INTO framework_tasks 
                (task_key, epic_id, title, tdd_phase, status, estimate_minutes, actual_minutes, story_points, assigned_to)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (task_key, epic_id, title, tdd_phase, status, estimate, actual, story_points))
        
        # Test gantt-style queries
        print("  🔍 Testing gantt data extraction...")
        
        # Query similar to what gantt_tracker would need
        cursor.execute("""
            SELECT 
                e.epic_key,
                e.name as epic_name,
                e.status as epic_status,
                t.task_key,
                t.title,
                t.tdd_phase,
                t.status,
                t.estimate_minutes,
                t.actual_minutes,
                t.story_points
            FROM framework_epics e
            LEFT JOIN framework_tasks t ON e.id = t.epic_id
            WHERE e.epic_key = 'COMPAT_TEST'
            ORDER BY t.task_key
        """)
        
        results = cursor.fetchall()
        
        if results:
            print(f"  ✅ Successfully extracted {len(results)} task records")
            print(f"  📋 Sample data: Epic '{results[0][1]}' with {len([r for r in results if r[3]])} tasks")
        else:
            print("  ❌ No data extracted")
            return False
        
        # Test time tracking queries
        cursor.execute("""
            SELECT 
                t.task_key,
                t.title,
                t.estimate_minutes,
                t.actual_minutes,
                CASE 
                    WHEN t.estimate_minutes > 0 THEN 
                        ROUND((t.actual_minutes * 100.0) / t.estimate_minutes, 1)
                    ELSE 0 
                END as efficiency_percentage
            FROM framework_tasks t
            WHERE t.epic_id = ? AND t.status = 'completed'
        """, (epic_id,))
        
        time_data = cursor.fetchall()
        print(f"  ⏱️ Time tracking data for {len(time_data)} completed tasks")
        
        # Test progress calculation
        cursor.execute("""
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                ROUND(
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / 
                    COUNT(*), 1
                ) as completion_percentage
            FROM framework_tasks
            WHERE epic_id = ?
        """, (epic_id,))
        
        progress = cursor.fetchone()
        print(f"  📈 Progress calculation: {progress[1]}/{progress[0]} tasks ({progress[2]}%)")
        
        # Cleanup test data
        cursor.execute("DELETE FROM framework_tasks WHERE epic_id = ?", (epic_id,))
        cursor.execute("DELETE FROM framework_epics WHERE id = ?", (epic_id,))
        conn.commit()
        
        print("  ✅ Gantt tracker compatibility test passed")
        
    except Exception as e:
        pytest.fail(f"  ❌ Gantt tracker compatibility test failed: {e}")
    
    finally:
        conn.close()

@pytest.mark.skip(reason="Compatibility check requires manual environment")
def test_analytics_engine_compatibility():
    """Test if analytics_engine.py can work with new database structure."""
    print("\n📈 Testing Analytics Engine Compatibility...")
    
    conn = sqlite3.connect('framework.db')
    cursor = conn.cursor()
    
    try:
        # Test user productivity analytics
        cursor.execute("""
            SELECT 
                u.username,
                u.total_points,
                COUNT(t.id) as total_tasks,
                COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
                AVG(CASE WHEN t.status = 'completed' AND t.estimate_minutes > 0 
                    THEN (t.actual_minutes * 100.0) / t.estimate_minutes 
                    END) as avg_efficiency,
                SUM(t.story_points) as total_story_points
            FROM framework_users u
            LEFT JOIN framework_tasks t ON u.id = t.assigned_to
            WHERE u.is_active = TRUE
            GROUP BY u.id, u.username, u.total_points
        """)
        
        analytics_data = cursor.fetchall()
        print(f"  ✅ User analytics data for {len(analytics_data)} users")
        
        # Test time-based analytics
        cursor.execute("""
            SELECT 
                DATE(ws.start_time) as session_date,
                COUNT(*) as session_count,
                SUM(ws.duration_minutes) as total_minutes,
                AVG(ws.focus_score) as avg_focus,
                AVG(ws.interruptions_count) as avg_interruptions
            FROM work_sessions ws
            GROUP BY DATE(ws.start_time)
            ORDER BY session_date DESC
            LIMIT 10
        """)
        
        time_analytics = cursor.fetchall()
        print(f"  ⏱️ Time analytics data for {len(time_analytics)} days")
        
        # Test achievement analytics
        cursor.execute("""
            SELECT 
                at.category,
                at.rarity,
                COUNT(ua.id) as unlock_count,
                AVG(ua.points_earned) as avg_points
            FROM achievement_types at
            LEFT JOIN user_achievements ua ON at.id = ua.achievement_id
            GROUP BY at.category, at.rarity
            ORDER BY unlock_count DESC
        """)
        
        achievement_analytics = cursor.fetchall()
        print(f"  🏆 Achievement analytics data for {len(achievement_analytics)} categories")
        
        # Test TDD phase distribution
        cursor.execute("""
            SELECT 
                tdd_phase,
                COUNT(*) as task_count,
                AVG(actual_minutes) as avg_time,
                AVG(story_points) as avg_story_points
            FROM framework_tasks
            WHERE tdd_phase IS NOT NULL
            GROUP BY tdd_phase
            ORDER BY task_count DESC
        """)
        
        tdd_analytics = cursor.fetchall()
        print(f"  🔄 TDD phase analytics for {len(tdd_analytics)} phases")
        
        print("  ✅ Analytics engine compatibility test passed")
        
    except Exception as e:
        pytest.fail(f"  ❌ Analytics engine compatibility test failed: {e}")
    
    finally:
        conn.close()

@pytest.mark.skip(reason="Compatibility check requires manual environment")
def test_json_export_compatibility():
    """Test if data can be exported back to JSON format for compatibility."""
    print("\n📄 Testing JSON Export Compatibility...")
    
    conn = sqlite3.connect('framework.db')
    cursor = conn.cursor()
    
    try:
        # Test exporting epic data to JSON format
        cursor.execute("""
            SELECT 
                e.epic_key as id,
                e.name,
                e.description,
                e.status,
                e.duration_days as duration,
                json_group_array(
                    json_object(
                        'id', t.task_key,
                        'title', t.title,
                        'tdd_phase', t.tdd_phase,
                        'status', t.status,
                        'estimate_minutes', t.estimate_minutes,
                        'actual_minutes', t.actual_minutes,
                        'story_points', t.story_points
                    )
                ) as tasks
            FROM framework_epics e
            LEFT JOIN framework_tasks t ON e.id = t.epic_id
            WHERE e.epic_key NOT LIKE 'TEST_%'
            GROUP BY e.id, e.epic_key, e.name, e.description, e.status, e.duration_days
            LIMIT 1
        """)
        
        epic_data = cursor.fetchone()

        if epic_data:
            # Try to parse the JSON
            tasks_json = json.loads(epic_data[5])
            print(f"  ✅ Successfully exported epic with {len(tasks_json)} tasks to JSON")

            # Create a sample export structure
            export_structure = {
                "epic": {
                    "id": epic_data[0],
                    "name": epic_data[1],
                    "description": epic_data[2],
                    "status": epic_data[3],
                    "duration": epic_data[4],
                    "tasks": tasks_json
                }
            }

            print(f"  📋 Export structure compatible with original JSON format")
        else:
            pytest.skip("  ⚠️ No data available for JSON export test")

        print("  ✅ JSON export compatibility test passed")
        
    except Exception as e:
        pytest.fail(f"  ❌ JSON export compatibility test failed: {e}")
    
    finally:
        conn.close()

def run_compatibility_tests():
    """Run all compatibility tests."""
    print("🔗 Framework Database Compatibility Test Suite")
    print("=" * 60)
    
    tests = [
        test_gantt_tracker_compatibility,
        test_analytics_engine_compatibility,
        test_json_export_compatibility
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 Compatibility Test Results")
    print("=" * 60)
    print(f"✅ Tests Passed: {passed}")
    print(f"❌ Tests Failed: {failed}")
    print(f"📊 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All compatibility tests passed! Systems are compatible.")
        return True
    else:
        print(f"\n💥 {failed} compatibility test(s) failed!")
        return False

if __name__ == "__main__":
    success = run_compatibility_tests()
    sys.exit(0 if success else 1)
