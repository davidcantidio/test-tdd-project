"""
Test suite for Duration System Extension (FASE 2.3) - Migrated to Modular API

Tests the four duration system methods using modular database API:
- calculate_epic_duration()
- update_duration_description()
- get_epic_timeline()
- validate_date_consistency()

Target: ≥95% code coverage for new methods
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from datetime import date, datetime
from unittest.mock import patch, MagicMock

# Import modular database API components
import sys
sys.path.append(str(Path(__file__).parent.parent))

# Modular database imports - complete migration from DatabaseManager
from streamlit_extension.database import (
    get_connection, transaction, list_epics, list_tasks,
    execute_cached_query, get_connection_context,
    create_tables, get_health_status
)
from streamlit_extension.services import ServiceContainer

# Duration System implementation using modular API
class DurationSystemModular:
    """Duration system implementation using modular database API."""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection_context = get_connection_context(db_path)
    
    def calculate_epic_duration(self, epic_id: int) -> float:
        """Calculate epic duration using modular API."""
        try:
            with get_connection() as conn:
                # First try calculated_duration_days field
                result = execute_cached_query(
                    "SELECT calculated_duration_days FROM framework_epics WHERE id = ?",
                    (epic_id,), conn
                )
                if result and result[0][0] is not None:
                    return float(result[0][0])
                
                # Try actual dates
                result = execute_cached_query(
                    "SELECT actual_start_date, actual_end_date FROM framework_epics WHERE id = ?",
                    (epic_id,), conn
                )
                if result and result[0][0] and result[0][1]:
                    from datetime import datetime
                    start = datetime.strptime(result[0][0], '%Y-%m-%d')
                    end = datetime.strptime(result[0][1], '%Y-%m-%d')
                    return float((end - start).days)
                
                # Try planned dates
                result = execute_cached_query(
                    "SELECT planned_start_date, planned_end_date FROM framework_epics WHERE id = ?",
                    (epic_id,), conn
                )
                if result and result[0][0] and result[0][1]:
                    from datetime import datetime
                    start = datetime.strptime(result[0][0], '%Y-%m-%d')
                    end = datetime.strptime(result[0][1], '%Y-%m-%d')
                    return float((end - start).days)
                
                # Calculate from tasks
                return self._calculate_epic_duration_from_tasks(epic_id)
                
        except Exception:
            return 0.0
    
    def update_duration_description(self, epic_id: int, description: str) -> bool:
        """Update duration description using modular API."""
        try:
            # Parse duration from description
            import re
            if "semana" in description:
                match = re.search(r'([0-9.]+)\s*semana', description)
                if match:
                    days = float(match.group(1)) * 7
                else:
                    return False
            elif "dia" in description:
                match = re.search(r'([0-9.]+)\s*dia', description)
                if match:
                    days = float(match.group(1))
                else:
                    return False
            else:
                return False
                
            with transaction() as conn:
                cursor = conn.execute(
                    "UPDATE framework_epics SET duration_description = ?, calculated_duration_days = ? WHERE id = ?",
                    (description, days, epic_id)
                )
                return cursor.rowcount > 0
                
        except Exception:
            return False
    
    def get_epic_timeline(self, epic_id: int) -> dict:
        """Get epic timeline using modular API."""
        try:
            with get_connection() as conn:
                # Get epic data
                epic_result = execute_cached_query(
                    """SELECT name, calculated_duration_days, duration_description,
                              planned_start_date, planned_end_date,
                              actual_start_date, actual_end_date
                       FROM framework_epics WHERE id = ?""",
                    (epic_id,), conn
                )
                
                if not epic_result:
                    return {"error": f"Epic {epic_id} not found"}
                
                epic_data = epic_result[0]
                
                # Get tasks
                tasks = self._get_epic_task_timeline(epic_id)
                
                # Validate dates
                is_valid = self.validate_date_consistency(epic_id)
                warnings = []
                if not is_valid:
                    warnings.append("Date consistency issues detected")
                
                return {
                    "epic": {
                        "name": epic_data[0],
                        "calculated_duration_days": epic_data[1]
                    },
                    "validation": {
                        "is_valid": is_valid,
                        "warnings": warnings
                    },
                    "duration_info": {
                        "calculated_days": epic_data[1],
                        "description": epic_data[2]
                    },
                    "dates": {
                        "planned_start": epic_data[3],
                        "planned_end": epic_data[4],
                        "actual_start": epic_data[5],
                        "actual_end": epic_data[6]
                    },
                    "status_info": {},
                    "tasks": tasks
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    def validate_date_consistency(self, epic_id: int) -> bool:
        """Validate date consistency using modular API."""
        try:
            with get_connection() as conn:
                result = execute_cached_query(
                    """SELECT planned_start_date, planned_end_date,
                              actual_start_date, actual_end_date
                       FROM framework_epics WHERE id = ?""",
                    (epic_id,), conn
                )
                
                if not result:
                    return False
                    
                dates = result[0]
                
                # Check planned dates
                if dates[0] and dates[1]:
                    if dates[0] > dates[1]:
                        return False
                
                # Check actual dates
                if dates[2] and dates[3]:
                    if dates[2] > dates[3]:
                        return False
                
                return True
                
        except Exception:
            return False
    
    def _calculate_epic_duration_from_tasks(self, epic_id: int) -> float:
        """Calculate duration from task estimates using modular API."""
        try:
            with get_connection() as conn:
                result = execute_cached_query(
                    "SELECT SUM(estimate_minutes) FROM framework_tasks WHERE epic_id = ? AND deleted_at IS NULL",
                    (epic_id,), conn
                )
                
                if result and result[0][0]:
                    total_minutes = result[0][0]
                    # Convert to days (8 hours = 1 day)
                    return float(total_minutes / (8 * 60))
                    
                return 0.0
                
        except Exception:
            return 0.0
    
    def _get_epic_task_timeline(self, epic_id: int) -> list:
        """Get epic task timeline using modular API."""
        try:
            with get_connection() as conn:
                result = execute_cached_query(
                    """SELECT title, priority, status, tdd_phase
                       FROM framework_tasks 
                       WHERE epic_id = ? AND deleted_at IS NULL
                       ORDER BY priority ASC""",
                    (epic_id,), conn
                )
                
                return [{"title": row[0], "priority": row[1], "status": row[2], "tdd_phase": row[3]} 
                       for row in result]
                
        except Exception:
            return []


class TestDatabaseManagerDurationExtension:
    """Test suite for duration system extension using modular API"""
    
    # TODO: Consider extracting this block into a separate method
    # TODO: Consider extracting this block into a separate method
    def setup_method(self):
        """Setup test database and manager for each test"""
        # Create temporary databases
        self.temp_framework_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_timer_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        
        self.framework_db_path = self.temp_framework_db.name
        self.timer_db_path = self.temp_timer_db.name
        
        # Close file handles to allow database connections
        self.temp_framework_db.close()
        self.temp_timer_db.close()
        
        # Create basic schema
        self._setup_test_schema()
        
        # Initialize modular database context
        self.connection_context = get_connection_context(self.framework_db_path)
        self.db_connection_path = self.framework_db_path
        # Create duration system functions using modular API
        self.duration_system = DurationSystemModular(self.framework_db_path)
    
    def teardown_method(self):
        """Cleanup temporary databases after each test"""
        for db_path in [self.framework_db_path, self.timer_db_path]:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
# TODO: Consider extracting this block into a separate method
    
# TODO: Consider extracting this block into a separate method
    
    def _setup_test_schema(self):
        """Create test database schema with duration system fields"""
        conn = sqlite3.connect(self.framework_db_path)
        cursor = conn.cursor()
        
        # Create framework_epics table with duration system fields
        cursor.execute("""
            CREATE TABLE framework_epics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                epic_key VARCHAR(50) UNIQUE,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'todo',
                planned_start_date DATE,
                planned_end_date DATE,
                actual_start_date DATE,
                actual_end_date DATE,
                calculated_duration_days DECIMAL(5,2),
                duration_description VARCHAR(50),
                points_earned INTEGER DEFAULT 0,
                difficulty_level INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                deleted_at TIMESTAMP
            )
        """)
        
        # Create framework_tasks table
        cursor.execute("""
            CREATE TABLE framework_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                epic_id INTEGER,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'todo',
                tdd_phase VARCHAR(20),
                priority INTEGER DEFAULT 2,
                estimate_minutes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                deleted_at TIMESTAMP,
                FOREIGN KEY (epic_id) REFERENCES framework_epics(id)
            )
        """)
        
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        conn.commit()
        conn.close()
    
    def _insert_test_epic(self, epic_id=1, epic_key="TEST_1", name="Test Epic",
                         planned_start=None, planned_end=None,
                         actual_start=None, actual_end=None,
                         calculated_duration=None, duration_description=None):
        """Insert test epic data"""
        conn = sqlite3.connect(self.framework_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO framework_epics
            (id, epic_key, name, planned_start_date, planned_end_date,
             actual_start_date, actual_end_date, calculated_duration_days,
             duration_description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (epic_id, epic_key, name, planned_start, planned_end,
              actual_start, actual_end, calculated_duration, duration_description))
        
# TODO: Consider extracting this block into a separate method
        
# TODO: Consider extracting this block into a separate method
        
        conn.commit()
        conn.close()
    
    def _insert_test_tasks(self, epic_id=1, task_count=3, estimate_minutes=120):
        """Insert test tasks for an epic"""
        conn = sqlite3.connect(self.framework_db_path)
        cursor = conn.cursor()
        
        for i in range(task_count):
            cursor.execute("""
                INSERT INTO framework_tasks 
                (epic_id, title, estimate_minutes)
                VALUES (?, ?, ?)
            """, (epic_id, f"Task {i+1}", estimate_minutes))
        
        conn.commit()
        conn.close()
    
    # ==================================================================================
    # CALCULATE_EPIC_DURATION TESTS
    # ==================================================================================
    
    def test_calculate_epic_duration_from_calculated_field(self):
        """Test using existing calculated_duration_days field"""
        self._insert_test_epic(
            epic_id=1,
            calculated_duration=5.5
        )
        
        duration = self.duration_system.calculate_epic_duration(1)
        assert duration == 5.5
    
    def test_calculate_epic_duration_from_actual_dates(self):
        """Test calculating from actual start/end dates"""
        self._insert_test_epic(
            epic_id=1,
            actual_start="2025-08-13",
            actual_end="2025-08-18"  # 5 days duration
        )
        
        duration = self.duration_system.calculate_epic_duration(1)
        assert duration == 5.0
    
    def test_calculate_epic_duration_from_planned_dates(self):
        """Test calculating from planned start/end dates"""
        self._insert_test_epic(
            epic_id=1,
            planned_start="2025-08-13",
            planned_end="2025-08-16"  # 3 days duration
        )
        
        duration = self.duration_system.calculate_epic_duration(1)
        assert duration == 3.0
    
    def test_calculate_epic_duration_from_tasks(self):
        """Test calculating from task estimates when no dates available"""
        self._insert_test_epic(epic_id=1)
        self._insert_test_tasks(epic_id=1, task_count=4, estimate_minutes=120)
        # 4 tasks × 120 minutes = 480 minutes = 8 hours = 1 day
        
        duration = self.duration_system.calculate_epic_duration(1)
        assert duration == 1.0
    
    def test_calculate_epic_duration_nonexistent_epic(self):
        """Test calculating duration for non-existent epic"""
        duration = self.duration_system.calculate_epic_duration(999)
        assert duration == 0.0
    
    def test_calculate_epic_duration_no_duration_system(self):
        """Test behavior when duration system is not available"""
        with patch('streamlit_extension.utils.database.DURATION_SYSTEM_AVAILABLE', False):
            duration = self.duration_system.calculate_epic_duration(1)
            # TODO: Consider extracting this block into a separate method
            # TODO: Consider extracting this block into a separate method
            assert duration == 0.0
    
    # ==================================================================================
    # UPDATE_DURATION_DESCRIPTION TESTS
    # ==================================================================================
    
    def test_update_duration_description_valid_format(self):
        """Test updating duration description with valid format"""
        self._insert_test_epic(epic_id=1)
        
        success = self.duration_system.update_duration_description(1, "2.5 dias")
        assert success is True
        
        # Verify update in database
        conn = sqlite3.connect(self.framework_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT duration_description, calculated_duration_days
            FROM framework_epics WHERE id = ?
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        """, (1,))
        row = cursor.fetchone()
        conn.close()
        
        assert row[0] == "2.5 dias"
        assert row[1] == 2.5
    
    def test_update_duration_description_semanas_format(self):
        """Test updating with weeks format"""
        self._insert_test_epic(epic_id=1)
        
        success = self.duration_system.update_duration_description(1, "1 semana")
        assert success is True
        
        # Verify conversion to days
        conn = sqlite3.connect(self.framework_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT calculated_duration_days FROM framework_epics WHERE id = ?", (1,))
        duration_days = cursor.fetchone()[0]
        conn.close()
        
        assert duration_days == 7.0
    
    def test_update_duration_description_invalid_format(self):
        """Test updating with invalid duration format"""
        self._insert_test_epic(epic_id=1)
        
        success = self.duration_system.update_duration_description(1, "invalid duration")
        assert success is False
    
    def test_update_duration_description_no_duration_system(self):
        """Test behavior when duration system is not available"""
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        with patch('streamlit_extension.utils.database.DURATION_SYSTEM_AVAILABLE', False):
            success = self.duration_system.update_duration_description(1, "2 dias")
            assert success is False
    
    # ==================================================================================
    # GET_EPIC_TIMELINE TESTS
    # ==================================================================================
    
    def test_get_epic_timeline_complete_data(self):
        """Test getting timeline for epic with complete data"""
        self._insert_test_epic(
            epic_id=1,
            name="Complete Epic",
            planned_start="2025-08-13",
            planned_end="2025-08-18",
            actual_start="2025-08-14",
            actual_end="2025-08-19",
            calculated_duration=5.0,
            duration_description="1 semana"
        )
        self._insert_test_tasks(epic_id=1, task_count=2)
        
        timeline = self.duration_system.get_epic_timeline(1)
        
        assert "epic" in timeline
        assert "validation" in timeline
        assert "duration_info" in timeline
        assert "dates" in timeline
        assert "status_info" in timeline
        assert "tasks" in timeline
        
        # Check epic data
        assert timeline["epic"]["name"] == "Complete Epic"
        assert timeline["epic"]["calculated_duration_days"] == 5.0
        
        # Check duration info
        assert timeline["duration_info"]["calculated_days"] == 5.0
        assert timeline["duration_info"]["description"] == "1 semana"
        
        # Check dates
        assert timeline["dates"]["planned_start"] == "2025-08-13"
        assert timeline["dates"]["actual_end"] == "2025-08-19"
        
        # Check tasks
        assert len(timeline["tasks"]) == 2
    
    def test_get_epic_timeline_validation_warnings(self):
        """Test timeline with date consistency warnings"""
        # Epic with mismatched duration
        self._insert_test_epic(
            epic_id=1,
            planned_start="2025-08-13",
            planned_end="2025-08-15",  # 2 days
            calculated_duration=5.0  # But says 5 days
        )
        
        timeline = self.duration_system.get_epic_timeline(1)
        
        assert timeline["validation"]["is_valid"] is True  # Still valid
        assert len(timeline["validation"]["warnings"]) > 0  # But has warnings
    
    def test_get_epic_timeline_nonexistent_epic(self):
        """Test getting timeline for non-existent epic"""
        timeline = self.duration_system.get_epic_timeline(999)
        
        assert "error" in timeline
        assert "Epic 999 not found" in timeline["error"]
    
    def test_get_epic_timeline_no_duration_system(self):
        """Test behavior when duration system is not available"""
        with patch('streamlit_extension.utils.database.DURATION_SYSTEM_AVAILABLE', False):
            timeline = self.duration_system.get_epic_timeline(1)
            assert timeline["error"] == "Duration system not available"
    
    # ==================================================================================
    # VALIDATE_DATE_CONSISTENCY TESTS
    # ==================================================================================
    
    def test_validate_date_consistency_valid_dates(self):
        """Test validation with consistent dates"""
        self._insert_test_epic(
            epic_id=1,
            planned_start="2025-08-13",
            planned_end="2025-08-18",
            calculated_duration=5.0
        )
        
        is_valid = self.duration_system.validate_date_consistency(1)
        assert is_valid is True
    
    def test_validate_date_consistency_invalid_order(self):
        """Test validation with invalid date order"""
        self._insert_test_epic(
            epic_id=1,
            planned_start="2025-08-18",
            planned_end="2025-08-13"  # End before start
        )
        
        is_valid = self.duration_system.validate_date_consistency(1)
        assert is_valid is False
    
    def test_validate_date_consistency_no_dates(self):
        """Test validation with no dates (should be valid)"""
        self._insert_test_epic(epic_id=1)
        
        is_valid = self.duration_system.validate_date_consistency(1)
        assert is_valid is True  # No dates to validate = valid
    
    def test_validate_date_consistency_nonexistent_epic(self):
        """Test validation for non-existent epic"""
        is_valid = self.duration_system.validate_date_consistency(999)
        assert is_valid is False
    
    def test_validate_date_consistency_no_duration_system(self):
        """Test behavior when duration system is not available"""
        with patch('streamlit_extension.utils.database.DURATION_SYSTEM_AVAILABLE', False):
            is_valid = self.duration_system.validate_date_consistency(1)
            assert is_valid is False
    
    # ==================================================================================
    # HELPER METHODS TESTS
    # ==================================================================================
    
    def test_calculate_epic_duration_from_tasks_basic(self):
        """Test helper method for calculating duration from tasks"""
        self._insert_test_epic(epic_id=1)
        self._insert_test_tasks(epic_id=1, task_count=3, estimate_minutes=160)
        # 3 tasks × 160 minutes = 480 minutes = 8 hours = 1 day
        
        duration = self.duration_system._calculate_epic_duration_from_tasks(1)
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        assert duration == 1.0
    
    def test_calculate_epic_duration_from_tasks_no_tasks(self):
        """Test helper method with no tasks"""
        self._insert_test_epic(epic_id=1)
        
        duration = self.duration_system._calculate_epic_duration_from_tasks(1)
        assert duration == 0.0
    
    def test_calculate_epic_duration_from_tasks_deleted_tasks(self):
        """Test helper method ignoring deleted tasks"""
        self._insert_test_epic(epic_id=1)
        
        # Insert task and then mark as deleted
        conn = sqlite3.connect(self.framework_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            # TODO: Consider extracting this block into a separate method
            # TODO: Consider extracting this block into a separate method
            INSERT INTO framework_tasks
            (epic_id, title, estimate_minutes, deleted_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (1, "Deleted Task", 480))  # 1 day worth
        conn.commit()
        conn.close()
        
        duration = self.duration_system._calculate_epic_duration_from_tasks(1)
        assert duration == 0.0  # Deleted tasks ignored
    
    def test_get_epic_task_timeline_basic(self):
        """Test helper method for getting epic task timeline"""
        self._insert_test_epic(epic_id=1)
        
        # Insert tasks with different priorities
        conn = sqlite3.connect(self.framework_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO framework_tasks
            (epic_id, title, priority, status, tdd_phase)
            VALUES (?, ?, ?, ?, ?)
        """, (1, "High Priority Task", 1, "completed", "refactor"))
        cursor.execute("""
            INSERT INTO framework_tasks
            (epic_id, title, priority, status, tdd_phase)
            VALUES (?, ?, ?, ?, ?)
        """, (1, "Low Priority Task", 3, "todo", "red"))
        conn.commit()
        conn.close()
        
        tasks = self.duration_system._get_epic_task_timeline(1)
        
        assert len(tasks) == 2
        assert tasks[0]["title"] == "High Priority Task"  # Should be first (priority 1)
        assert tasks[0]["status"] == "completed"
        assert tasks[1]["title"] == "Low Priority Task"  # Should be second (priority 3)
    
    # TODO: Consider extracting this block into a separate method
    # TODO: Consider extracting this block into a separate method
    def test_get_epic_task_timeline_no_tasks(self):
        """Test helper method with no tasks"""
        self._insert_test_epic(epic_id=1)
        
        tasks = self.duration_system._get_epic_task_timeline(1)
        assert tasks == []
    
    # ==================================================================================
    # INTEGRATION TESTS
    # ==================================================================================
    
    def test_duration_system_integration_full_workflow(self):
        """Test complete workflow with all duration system methods"""
        # 1. Create epic
        self._insert_test_epic(epic_id=1, name="Integration Test Epic")
        
        # 2. Update duration description
        success = self.duration_system.update_duration_description(1, "1.5 semanas")
        assert success is True
        
        # 3. Calculate duration (should use calculated field now)
        duration = self.duration_system.calculate_epic_duration(1)
        assert duration == 10.5  # 1.5 weeks = 10.5 days
        
        # 4. Add dates for timeline
        conn = sqlite3.connect(self.framework_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE framework_epics
            SET planned_start_date = ?, planned_end_date = ?
            WHERE id = ?
        """, ("2025-08-13", "2025-08-25", 1))  # ~12 days
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        conn.commit()
        conn.close()
        
        # 5. Get timeline (should show duration mismatch warning)
        timeline = self.duration_system.get_epic_timeline(1)
        assert timeline["duration_info"]["calculated_days"] == 10.5
        assert len(timeline["validation"]["warnings"]) > 0  # Duration mismatch
        
        # 6. Validate consistency (should be valid but with warnings)
        is_valid = self.duration_system.validate_date_consistency(1)
        assert is_valid is True
    
    def test_real_epic_data_compatibility(self):
        """Test compatibility with real epic data patterns"""
        # Test patterns from actual epic files
        epic_patterns = [
            ("1.5 dias", 1.5),
            ("2 dias", 2.0),
            ("5 dias", 5.0),
            ("1 semana", 7.0),
            ("4 dias", 4.0)
        ]
        
        for i, (duration_desc, expected_days) in enumerate(epic_patterns, 1):
            self._insert_test_epic(epic_id=i, epic_key=f"TEST_{i}", name=f"Epic {i}")
            
            # Update duration description
            success = self.duration_system.update_duration_description(i, duration_desc)
            assert success is True
            
# TODO: Consider extracting this block into a separate method
            
# TODO: Consider extracting this block into a separate method
            
            # Verify calculation
            calculated = self.duration_system.calculate_epic_duration(i)
            assert calculated == expected_days, f"Failed for pattern: {duration_desc}"
            
            # Verify timeline
            timeline = self.duration_system.get_epic_timeline(i)
            assert timeline["duration_info"]["calculated_days"] == expected_days
    
    # ==================================================================================
    # ERROR HANDLING TESTS
    # ==================================================================================
    
    def test_database_connection_error_handling(self):
        """Test graceful error handling with database connection issues"""
        # Use invalid database path
        bad_duration_system = DurationSystemModular("/nonexistent/path.db")
        
        # Should return default values instead of crashing
        duration = bad_duration_system.calculate_epic_duration(1)
        assert duration == 0.0
        
        success = bad_duration_system.update_duration_description(1, "1 dia")
        assert success is False
        
        timeline = bad_duration_system.get_epic_timeline(1)
        assert "error" in timeline
        
        is_valid = bad_duration_system.validate_date_consistency(1)
        assert is_valid is False
    
    def test_malformed_data_handling(self):
        """Test handling of malformed data in database"""
        # Insert epic with malformed date
        conn = sqlite3.connect(self.framework_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO framework_epics
            (id, epic_key, name, planned_start_date, planned_end_date)
            VALUES (?, ?, ?, ?, ?)
        """, (1, "TEST_1", "Test Epic", "invalid-date", "2025-08-18"))
        conn.commit()
        conn.close()
        
        # Should handle gracefully
        is_valid = self.duration_system.validate_date_consistency(1)
        assert is_valid is False  # Invalid due to malformed data
        
        timeline = self.duration_system.get_epic_timeline(1)
        assert "error" in timeline or timeline["validation"]["is_valid"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])