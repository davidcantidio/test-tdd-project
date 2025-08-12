#!/usr/bin/env python3
"""
⚡ Framework Database Performance Benchmark

Tests database performance with realistic workloads and generates performance report.
"""

import sqlite3
import time
import json
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

class DatabaseBenchmark:
    def __init__(self, db_path="framework.db"):
        self.db_path = db_path
        self.conn = None
        self.results = {}
    
    def connect(self):
        """Connect to database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def time_operation(self, operation_name, operation_func, *args, **kwargs):
        """Time a database operation."""
        start_time = time.time()
        result = operation_func(*args, **kwargs)
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        self.results[operation_name] = duration_ms
        
        status = "✅" if duration_ms < 100 else "⚠️" if duration_ms < 500 else "❌"
        print(f"{status} {operation_name}: {duration_ms:.2f}ms")
        
        return result, duration_ms
    
    def setup_test_data(self):
        """Setup comprehensive test data."""
        print("🔄 Setting up test data...")
        
        cursor = self.conn.cursor()
        
        # Create test users
        test_users = []
        for i in range(50):
            cursor.execute("""
                INSERT INTO framework_users (username, email, github_username, total_points, current_level)
                VALUES (?, ?, ?, ?, ?)
            """, (f"user_{i}", f"user_{i}@test.com", f"gituser_{i}", random.randint(0, 5000), random.randint(1, 10)))
            test_users.append(cursor.lastrowid)
        
        # Create test epics
        test_epics = []
        for i in range(20):
            cursor.execute("""
                INSERT INTO framework_epics (epic_key, name, description, status, priority, created_by, assigned_to)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"EPIC_{i}",
                f"Test Epic {i}",
                f"Description for epic {i}",
                random.choice(['pending', 'in_progress', 'completed']),
                random.randint(1, 5),
                random.choice(test_users),
                random.choice(test_users)
            ))
            test_epics.append(cursor.lastrowid)
        
        # Create test tasks (bulk insert)
        task_data = []
        for i in range(1000):
            epic_id = random.choice(test_epics)
            user_id = random.choice(test_users)
            status = random.choice(['pending', 'in_progress', 'completed', 'blocked'])
            tdd_phase = random.choice(['analysis', 'red', 'green', 'refactor', 'review'])
            
            task_data.append((
                f"TASK_{i}",
                epic_id,
                f"Test Task {i}",
                f"Description for task {i}",
                tdd_phase,
                status,
                random.randint(30, 480),
                random.randint(0, 600) if status == 'completed' else 0,
                random.randint(1, 8),
                user_id,
                random.choice(test_users) if random.random() > 0.7 else None,
                random.randint(0, 500) if status == 'completed' else 0
            ))
        
        cursor.executemany("""
            INSERT INTO framework_tasks 
            (task_key, epic_id, title, description, tdd_phase, status, estimate_minutes, 
             actual_minutes, story_points, assigned_to, reviewer_id, points_earned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, task_data)
        
        # Create work sessions
        session_data = []
        for i in range(500):
            start_time = datetime.now() - timedelta(days=random.randint(0, 90))
            duration = random.randint(15, 240)
            
            session_data.append((
                random.randint(1, 1000),  # task_id
                random.choice(test_users),
                start_time.isoformat(),
                (start_time + timedelta(minutes=duration)).isoformat(),
                duration,
                random.choice(['work', 'break', 'meeting']),
                random.randint(5, 10),
                random.randint(0, 5),
                random.randint(5, 10),
                random.randint(5, 10)
            ))
        
        cursor.executemany("""
            INSERT INTO work_sessions 
            (task_id, user_id, start_time, end_time, duration_minutes, session_type,
             focus_score, interruptions_count, energy_level, mood_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, session_data)
        
        # Create user achievements
        achievement_data = []
        for user_id in test_users[:30]:  # Only some users have achievements
            num_achievements = random.randint(1, 5)
            user_achievements = random.sample(range(1, 11), num_achievements)
            
            for achievement_id in user_achievements:
                achievement_data.append((
                    user_id,
                    achievement_id,
                    (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                    random.choice(test_users[:100]) if len(test_users) >= 100 else random.choice(test_users),
                    None,  # epic_id
                    json.dumps({"achievement_level": random.randint(1, 3)}),
                    random.randint(50, 500)
                ))
        
        cursor.executemany("""
            INSERT OR IGNORE INTO user_achievements 
            (user_id, achievement_id, unlocked_at, unlocked_by_task_id, unlocked_by_epic_id, context_data, points_earned)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, achievement_data)
        
        self.conn.commit()
        print(f"✅ Test data created: {len(test_users)} users, {len(test_epics)} epics, 1000 tasks, 500 sessions")
        
        return test_users, test_epics
    
    def benchmark_basic_operations(self):
        """Benchmark basic CRUD operations."""
        print("\n🔧 Benchmarking Basic Operations...")
        
        cursor = self.conn.cursor()
        
        # Single record insert
        def insert_user():
            cursor.execute("""
                INSERT INTO framework_users (username, email, total_points)
                VALUES ('bench_user', 'bench@test.com', 100)
            """)
            self.conn.commit()
            return cursor.lastrowid
        
        user_id, _ = self.time_operation("Single User Insert", insert_user)
        
        # Single record select
        def select_user():
            cursor.execute("SELECT * FROM framework_users WHERE id = ?", (user_id,))
            return cursor.fetchone()
        
        self.time_operation("Single User Select", select_user)
        
        # Single record update
        def update_user():
            cursor.execute("""
                UPDATE framework_users 
                SET total_points = total_points + 50 
                WHERE id = ?
            """, (user_id,))
            self.conn.commit()
        
        self.time_operation("Single User Update", update_user)
        
        # Cleanup
        cursor.execute("DELETE FROM framework_users WHERE id = ?", (user_id,))
        self.conn.commit()
    
    def benchmark_complex_queries(self):
        """Benchmark complex analytical queries."""
        print("\n📊 Benchmarking Complex Queries...")
        
        cursor = self.conn.cursor()
        
        # User dashboard aggregation
        def user_dashboard_query():
            cursor.execute("""
                SELECT 
                    u.id,
                    u.username,
                    u.total_points,
                    COUNT(DISTINCT t.id) as total_tasks,
                    COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks,
                    COALESCE(AVG(ws.focus_score), 0) as avg_focus_score,
                    COUNT(DISTINCT ua.achievement_id) as achievements_count
                FROM framework_users u
                LEFT JOIN framework_tasks t ON u.id = t.assigned_to
                LEFT JOIN work_sessions ws ON u.id = ws.user_id
                LEFT JOIN user_achievements ua ON u.id = ua.user_id
                WHERE u.is_active = TRUE
                GROUP BY u.id, u.username, u.total_points
                ORDER BY u.total_points DESC
                LIMIT 20
            """)
            return cursor.fetchall()
        
        self.time_operation("User Dashboard Query", user_dashboard_query)
        
        # Epic progress analysis
        def epic_progress_query():
            cursor.execute("""
                SELECT 
                    e.epic_key,
                    e.name,
                    e.status,
                    COUNT(t.id) as total_tasks,
                    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
                    ROUND(
                        COUNT(CASE WHEN t.status = 'completed' THEN 1 END) * 100.0 / 
                        NULLIF(COUNT(t.id), 0), 2
                    ) as completion_percentage,
                    SUM(t.estimate_minutes) as total_estimated,
                    SUM(t.actual_minutes) as total_actual,
                    AVG(t.story_points) as avg_story_points
                FROM framework_epics e
                LEFT JOIN framework_tasks t ON e.id = t.epic_id
                GROUP BY e.id, e.epic_key, e.name, e.status
                ORDER BY completion_percentage DESC
            """)
            return cursor.fetchall()
        
        self.time_operation("Epic Progress Query", epic_progress_query)
        
        # Time tracking analysis
        def time_tracking_query():
            cursor.execute("""
                SELECT 
                    DATE(ws.start_time) as work_date,
                    COUNT(*) as session_count,
                    SUM(ws.duration_minutes) as total_minutes,
                    AVG(ws.focus_score) as avg_focus_score,
                    AVG(ws.interruptions_count) as avg_interruptions,
                    COUNT(DISTINCT ws.user_id) as active_users
                FROM work_sessions ws
                WHERE ws.start_time >= DATE('now', '-30 days')
                GROUP BY DATE(ws.start_time)
                ORDER BY work_date DESC
            """)
            return cursor.fetchall()
        
        self.time_operation("Time Tracking Analysis", time_tracking_query)
        
        # Achievement leaderboard
        def achievement_leaderboard():
            cursor.execute("""
                SELECT 
                    u.username,
                    u.total_points,
                    COUNT(ua.achievement_id) as achievement_count,
                    GROUP_CONCAT(at.name) as achievement_names,
                    MAX(us.current_count) as best_streak
                FROM framework_users u
                LEFT JOIN user_achievements ua ON u.id = ua.user_id
                LEFT JOIN achievement_types at ON ua.achievement_id = at.id
                LEFT JOIN user_streaks us ON u.id = us.user_id
                WHERE u.is_active = TRUE
                GROUP BY u.id, u.username, u.total_points
                HAVING achievement_count > 0
                ORDER BY u.total_points DESC, achievement_count DESC
                LIMIT 10
            """)
            return cursor.fetchall()
        
        self.time_operation("Achievement Leaderboard", achievement_leaderboard)
    
    def benchmark_bulk_operations(self):
        """Benchmark bulk operations."""
        print("\n📦 Benchmarking Bulk Operations...")
        
        cursor = self.conn.cursor()
        
        # Bulk task completion (simulates end-of-day processing)
        def bulk_task_completion():
            cursor.execute("""
                UPDATE framework_tasks 
                SET status = 'completed', 
                    completed_at = CURRENT_TIMESTAMP,
                    actual_minutes = estimate_minutes + CAST(RANDOM() * 60 AS INTEGER)
                WHERE status = 'in_progress' 
                AND id IN (SELECT id FROM framework_tasks WHERE status = 'in_progress' LIMIT 50)
            """)
            self.conn.commit()
            return cursor.rowcount
        
        updated_count, _ = self.time_operation("Bulk Task Completion (50 tasks)", bulk_task_completion)
        print(f"  📝 Updated {updated_count} tasks")
        
        # Bulk points recalculation
        def bulk_points_recalculation():
            cursor.execute("""
                UPDATE framework_users 
                SET total_points = (
                    SELECT COALESCE(SUM(t.points_earned), 0) 
                    FROM framework_tasks t 
                    WHERE t.assigned_to = framework_users.id 
                    AND t.status = 'completed'
                ),
                updated_at = CURRENT_TIMESTAMP
                WHERE id IN (SELECT id FROM framework_users LIMIT 20)
            """)
            self.conn.commit()
            return cursor.rowcount
        
        updated_users, _ = self.time_operation("Bulk Points Recalculation (20 users)", bulk_points_recalculation)
        print(f"  👥 Updated {updated_users} users")
    
    def benchmark_views_and_indexes(self):
        """Benchmark view performance and index usage."""
        print("\n👁️ Benchmarking Views and Indexes...")
        
        cursor = self.conn.cursor()
        
        # Test user dashboard view
        def dashboard_view_query():
            cursor.execute("SELECT * FROM user_dashboard ORDER BY total_points DESC LIMIT 10")
            return cursor.fetchall()
        
        self.time_operation("User Dashboard View", dashboard_view_query)
        
        # Test epic progress view
        def epic_progress_view_query():
            cursor.execute("SELECT * FROM epic_progress WHERE completion_percentage > 50 ORDER BY completion_percentage DESC")
            return cursor.fetchall()
        
        self.time_operation("Epic Progress View", epic_progress_view_query)
        
        # Test indexed query performance
        def indexed_user_tasks():
            cursor.execute("""
                SELECT * FROM framework_tasks 
                WHERE assigned_to = 1 AND status = 'completed'
                ORDER BY completed_at DESC
            """)
            return cursor.fetchall()
        
        self.time_operation("Indexed User Tasks Query", indexed_user_tasks)
        
        # Test session date range query (indexed)
        def indexed_session_query():
            cursor.execute("""
                SELECT * FROM work_sessions 
                WHERE user_id = 1 AND DATE(start_time) >= DATE('now', '-7 days')
                ORDER BY start_time DESC
            """)
            return cursor.fetchall()
        
        self.time_operation("Indexed Session Date Query", indexed_session_query)
    
    def cleanup_test_data(self):
        """Clean up test data."""
        print("\n🧹 Cleaning up test data...")
        
        cursor = self.conn.cursor()
        
        # Delete in reverse dependency order
        cursor.execute("DELETE FROM user_achievements WHERE user_id > 1")
        cursor.execute("DELETE FROM user_streaks WHERE user_id > 1")
        cursor.execute("DELETE FROM work_sessions WHERE user_id > 1")
        cursor.execute("DELETE FROM framework_tasks WHERE task_key LIKE 'TASK_%'")
        cursor.execute("DELETE FROM framework_epics WHERE epic_key LIKE 'EPIC_%'")
        cursor.execute("DELETE FROM framework_users WHERE username LIKE 'user_%'")
        
        self.conn.commit()
        print("✅ Test data cleaned up")
    
    def generate_report(self):
        """Generate performance report."""
        print("\n📋 Performance Report")
        print("=" * 60)
        
        # Categorize results
        categories = {
            "Basic Operations": ["Single User Insert", "Single User Select", "Single User Update"],
            "Complex Queries": ["User Dashboard Query", "Epic Progress Query", "Time Tracking Analysis", "Achievement Leaderboard"],
            "Bulk Operations": ["Bulk Task Completion (50 tasks)", "Bulk Points Recalculation (20 users)"],
            "Views & Indexes": ["User Dashboard View", "Epic Progress View", "Indexed User Tasks Query", "Indexed Session Date Query"]
        }
        
        overall_performance = []
        
        for category, operations in categories.items():
            print(f"\n📊 {category}:")
            category_times = []
            
            for operation in operations:
                if operation in self.results:
                    duration = self.results[operation]
                    category_times.append(duration)
                    overall_performance.append(duration)
                    
                    status_icon = "🟢" if duration < 50 else "🟡" if duration < 100 else "🔴"
                    print(f"  {status_icon} {operation}: {duration:.2f}ms")
            
            if category_times:
                avg_time = sum(category_times) / len(category_times)
                print(f"  📈 Category Average: {avg_time:.2f}ms")
        
        # Overall statistics
        if overall_performance:
            print(f"\n🎯 Overall Performance:")
            print(f"  📊 Total Operations: {len(overall_performance)}")
            print(f"  ⚡ Fastest: {min(overall_performance):.2f}ms")
            print(f"  🐌 Slowest: {max(overall_performance):.2f}ms")
            print(f"  📈 Average: {sum(overall_performance) / len(overall_performance):.2f}ms")
            
            # Performance grade
            avg_perf = sum(overall_performance) / len(overall_performance)
            if avg_perf < 50:
                grade = "A+ (Excellent)"
            elif avg_perf < 100:
                grade = "A (Very Good)"
            elif avg_perf < 200:
                grade = "B (Good)"
            elif avg_perf < 500:
                grade = "C (Fair)"
            else:
                grade = "D (Needs Optimization)"
            
            print(f"  🏆 Performance Grade: {grade}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        slow_operations = [op for op, time in self.results.items() if time > 200]
        
        if not slow_operations:
            print("  ✅ All operations performed well! No optimization needed.")
        else:
            print("  ⚠️ Consider optimizing these operations:")
            for op in slow_operations:
                print(f"    • {op} ({self.results[op]:.2f}ms)")
    
    def run_benchmark(self):
        """Run complete benchmark suite."""
        print("⚡ Starting Framework Database Performance Benchmark")
        print("=" * 60)
        
        if not self.connect():
            return False
        
        try:
            # Setup test data
            test_users, test_epics = self.setup_test_data()
            
            # Run benchmarks
            self.benchmark_basic_operations()
            self.benchmark_complex_queries()
            self.benchmark_bulk_operations()
            self.benchmark_views_and_indexes()
            
            # Generate report
            self.generate_report()
            
            # Cleanup
            self.cleanup_test_data()
            
        except Exception as e:
            print(f"❌ Benchmark failed: {e}")
            return False
        
        finally:
            if self.conn:
                self.conn.close()
        
        print(f"\n🎉 Benchmark completed successfully!")
        return True

if __name__ == "__main__":
    benchmark = DatabaseBenchmark()
    success = benchmark.run_benchmark()
    sys.exit(0 if success else 1)