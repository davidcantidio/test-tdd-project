#!/usr/bin/env python3
"""
🧪 Framework Database Integrity Test Suite

Comprehensive validation of database schema, constraints, triggers, and functionality.
"""

import sqlite3
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

class DatabaseIntegrityTester:
    def __init__(self, db_path="framework.db"):
        self.db_path = db_path
        self.conn = None
        self.tests_passed = 0
        self.tests_failed = 0
        self.error_log = []
    
    def connect(self):
        """Connect to database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return True
        except Exception as e:
            self.log_error(f"Database connection failed: {e}")
            return False
    
    def log_error(self, error):
        """Log test error."""
        self.error_log.append(error)
        print(f"❌ {error}")
    
    def log_success(self, message):
        """Log test success."""
        print(f"✅ {message}")
        self.tests_passed += 1
    
    def test_foreign_keys(self):
        """Test all foreign key constraints."""
        print("\n🔗 Testing Foreign Key Constraints...")
        
        cursor = self.conn.cursor()
        
        # Enable foreign key checking
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Test invalid epic reference in tasks
        try:
            cursor.execute("""
                INSERT INTO framework_tasks (task_key, epic_id, title, assigned_to) 
                VALUES ('test', 99999, 'Invalid Epic Test', 1)
            """)
            self.conn.rollback()
            self.log_error("Foreign key constraint not enforced (epic_id)")
            self.tests_failed += 1
        except sqlite3.IntegrityError:
            self.log_success("Epic ID foreign key constraint working")
        
        # Test invalid user reference
        try:
            cursor.execute("""
                INSERT INTO framework_tasks (task_key, epic_id, title, assigned_to) 
                VALUES ('test2', 1, 'Invalid User Test', 99999)
            """)
            self.conn.rollback()
            self.log_error("Foreign key constraint not enforced (assigned_to)")
            self.tests_failed += 1
        except sqlite3.IntegrityError:
            self.log_success("User ID foreign key constraint working")
        
        # Test achievement foreign keys
        try:
            cursor.execute("""
                INSERT INTO user_achievements (user_id, achievement_id) 
                VALUES (99999, 1)
            """)
            self.conn.rollback()
            self.log_error("Achievement user FK constraint not enforced")
            self.tests_failed += 1
        except sqlite3.IntegrityError:
            self.log_success("Achievement user FK constraint working")
    
    def test_unique_constraints(self):
        """Test unique constraints."""
        print("\n🔐 Testing Unique Constraints...")
        
        cursor = self.conn.cursor()
        
        # Test duplicate username
        try:
            cursor.execute("""
                INSERT INTO framework_users (username, email) 
                VALUES ('dev_user', 'another@example.com')
            """)
            self.conn.rollback()
            self.log_error("Username unique constraint not enforced")
            self.tests_failed += 1
        except sqlite3.IntegrityError:
            self.log_success("Username unique constraint working")
        
        # Test duplicate achievement unlock
        try:
            cursor.execute("""
                INSERT INTO user_achievements (user_id, achievement_id) 
                VALUES (1, 1)
            """)
            cursor.execute("""
                INSERT INTO user_achievements (user_id, achievement_id) 
                VALUES (1, 1)
            """)
            self.conn.rollback()
            self.log_error("Achievement unique constraint not enforced")
            self.tests_failed += 1
        except sqlite3.IntegrityError:
            self.log_success("Achievement unique constraint working")
    
    def test_check_constraints(self):
        """Test check constraints."""
        print("\n✅ Testing Check Constraints...")
        
        cursor = self.conn.cursor()
        
        # Test invalid TDD phase
        try:
            cursor.execute("""
                INSERT INTO framework_tasks (task_key, epic_id, title, tdd_phase) 
                VALUES ('test3', 1, 'Invalid Phase Test', 'invalid_phase')
            """)
            self.conn.rollback()
            self.log_error("TDD phase check constraint not enforced")
            self.tests_failed += 1
        except sqlite3.IntegrityError:
            self.log_success("TDD phase check constraint working")
    
    def test_triggers(self):
        """Test database triggers."""
        print("\n⚡ Testing Database Triggers...")
        
        cursor = self.conn.cursor()
        
        # Create test epic and task
        cursor.execute("""
            INSERT INTO framework_epics (epic_key, name, created_by, assigned_to) 
            VALUES ('TEST_EPIC', 'Test Epic', 1, 1)
        """)
        epic_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO framework_tasks (task_key, epic_id, title, assigned_to, story_points, difficulty_modifier) 
            VALUES ('TEST_TASK', ?, 'Test Task', 1, 3, 1.5)
        """, (epic_id,))
        task_id = cursor.lastrowid
        
        # Get initial user points
        cursor.execute("SELECT total_points FROM framework_users WHERE id = 1")
        initial_points = cursor.fetchone()[0]
        
        # Complete the task to trigger points calculation
        cursor.execute("""
            UPDATE framework_tasks 
            SET status = 'completed' 
            WHERE id = ?
        """, (task_id,))
        
        # Check if points were calculated and added
        cursor.execute("SELECT points_earned FROM framework_tasks WHERE id = ?", (task_id,))
        task_points = cursor.fetchone()[0]
        
        cursor.execute("SELECT total_points FROM framework_users WHERE id = 1")
        final_points = cursor.fetchone()[0]
        
        expected_points = 3 * 10 * 1.5  # story_points * base * difficulty_modifier
        
        if task_points == int(expected_points):
            self.log_success(f"Task points calculation trigger working ({task_points} points)")
        else:
            self.log_error(f"Task points calculation failed (expected {int(expected_points)}, got {task_points})")
            self.tests_failed += 1
        
        if final_points == initial_points + task_points:
            self.log_success(f"User points update trigger working (+{task_points} points)")
        else:
            self.log_error(f"User points update failed (expected +{task_points}, got +{final_points - initial_points})")
            self.tests_failed += 1
        
        # Check streak trigger
        cursor.execute("SELECT current_count FROM user_streaks WHERE user_id = 1 AND streak_type = 'daily_tasks'")
        streak_result = cursor.fetchone()
        
        if streak_result and streak_result[0] >= 1:
            self.log_success(f"Daily streak trigger working ({streak_result[0]} days)")
        else:
            self.log_error("Daily streak trigger not working")
            self.tests_failed += 1
        
        # Cleanup test data
        cursor.execute("DELETE FROM framework_tasks WHERE id = ?", (task_id,))
        cursor.execute("DELETE FROM framework_epics WHERE id = ?", (epic_id,))
        self.conn.commit()
    
    def test_views(self):
        """Test database views."""
        print("\n👁️ Testing Database Views...")
        
        cursor = self.conn.cursor()
        
        # Test user dashboard view
        cursor.execute("SELECT * FROM user_dashboard WHERE user_id = 1")
        dashboard = cursor.fetchone()
        
        if dashboard:
            self.log_success(f"User dashboard view working (user: {dashboard['username']})")
        else:
            self.log_error("User dashboard view not returning data")
            self.tests_failed += 1
        
        # Test epic progress view
        cursor.execute("SELECT COUNT(*) FROM epic_progress")
        epic_count = cursor.fetchone()[0]
        
        if epic_count >= 0:
            self.log_success(f"Epic progress view working ({epic_count} epics)")
        else:
            self.log_error("Epic progress view not working")
            self.tests_failed += 1
    
    def test_indexes(self):
        """Test database indexes."""
        print("\n🔍 Testing Database Indexes...")
        
        cursor = self.conn.cursor()
        
        # Get all custom indexes
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """)
        indexes = cursor.fetchall()
        
        expected_indexes = [
            'idx_tasks_user_status',
            'idx_tasks_epic_phase', 
            'idx_tasks_github',
            'idx_sessions_user_date',
            'idx_sessions_task_duration',
            'idx_epics_github',
            'idx_epics_status_priority',
            'idx_achievements_user',
            'idx_achievements_type',
            'idx_streaks_user_type',
            'idx_streaks_activity',
            'idx_sync_log_type_status',
            'idx_sync_log_date'
        ]
        
        actual_indexes = [idx[0] for idx in indexes]
        
        for expected in expected_indexes:
            if expected in actual_indexes:
                self.log_success(f"Index {expected} exists")
            else:
                self.log_error(f"Index {expected} missing")
                self.tests_failed += 1
    
    def test_data_integrity(self):
        """Test data integrity and initial data."""
        print("\n📊 Testing Data Integrity...")
        
        cursor = self.conn.cursor()
        
        # Test achievement types
        cursor.execute("SELECT COUNT(*) FROM achievement_types WHERE is_active = TRUE")
        active_achievements = cursor.fetchone()[0]
        
        if active_achievements >= 10:
            self.log_success(f"Achievement types loaded ({active_achievements} active)")
        else:
            self.log_error(f"Insufficient achievement types ({active_achievements} < 10)")
            self.tests_failed += 1
        
        # Test system settings
        cursor.execute("SELECT COUNT(*) FROM system_settings")
        settings_count = cursor.fetchone()[0]
        
        if settings_count >= 7:
            self.log_success(f"System settings loaded ({settings_count})")
        else:
            self.log_error(f"Insufficient system settings ({settings_count} < 7)")
            self.tests_failed += 1
        
        # Test default user
        cursor.execute("SELECT username FROM framework_users WHERE id = 1")
        user = cursor.fetchone()
        
        if user and user[0] == 'dev_user':
            self.log_success("Default user created correctly")
        else:
            self.log_error("Default user not created properly")
            self.tests_failed += 1
    
    def test_json_fields(self):
        """Test JSON field handling."""
        print("\n📋 Testing JSON Fields...")
        
        cursor = self.conn.cursor()
        
        # Test user preferences JSON
        test_preferences = {"theme": "dark", "notifications": True}
        cursor.execute("""
            UPDATE framework_users 
            SET preferences = ? 
            WHERE id = 1
        """, (json.dumps(test_preferences),))
        
        cursor.execute("SELECT preferences FROM framework_users WHERE id = 1")
        stored_prefs = cursor.fetchone()[0]
        
        try:
            parsed_prefs = json.loads(stored_prefs)
            if parsed_prefs == test_preferences:
                self.log_success("JSON preferences storage working")
            else:
                self.log_error("JSON preferences data mismatch")
                self.tests_failed += 1
        except json.JSONDecodeError:
            self.log_error("JSON preferences parsing failed")
            self.tests_failed += 1
        
        # Reset preferences
        cursor.execute("UPDATE framework_users SET preferences = NULL WHERE id = 1")
        self.conn.commit()
    
    def run_all_tests(self):
        """Run complete test suite."""
        print("🧪 Starting Framework Database Integrity Tests")
        print("=" * 60)
        
        if not self.connect():
            return False
        
        try:
            self.test_foreign_keys()
            self.test_unique_constraints()
            self.test_check_constraints()
            self.test_triggers()
            self.test_views()
            self.test_indexes()
            self.test_data_integrity()
            self.test_json_fields()
            
        except Exception as e:
            self.log_error(f"Unexpected error during testing: {e}")
            self.tests_failed += 1
        
        finally:
            if self.conn:
                self.conn.close()
        
        # Report results
        print("\n" + "=" * 60)
        print("🏁 Test Results Summary")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_failed}")
        print(f"📊 Success Rate: {(self.tests_passed / (self.tests_passed + self.tests_failed) * 100):.1f}%")
        
        if self.tests_failed > 0:
            print(f"\n❌ Failed Tests:")
            for error in self.error_log:
                print(f"  • {error}")
        
        return self.tests_failed == 0

if __name__ == "__main__":
    tester = DatabaseIntegrityTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All database integrity tests passed!")
    else:
        print(f"\n💥 {tester.tests_failed} test(s) failed!")
    
    sys.exit(0 if success else 1)