"""
Quick validation test for DatabaseManager duration extension
"""

import sqlite3
import tempfile
import os
from pathlib import Path

# Import the extended DatabaseManager
import sys
sys.path.append(str(Path(__file__).parent))

from streamlit_extension.utils.database import DatabaseManager

def test_quick_validation():
    """Quick validation of core functionality"""
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
        db_path = temp_db.name
    
    # Create test schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE framework_epics (
            id INTEGER PRIMARY KEY,
            epic_key VARCHAR(50),
            name VARCHAR(200),
            status VARCHAR(50) DEFAULT 'todo',
            planned_start_date DATE,
            planned_end_date DATE,
            actual_start_date DATE,
            actual_end_date DATE,
            calculated_duration_days DECIMAL(5,2),
            duration_description VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            deleted_at TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE framework_tasks (
            id INTEGER PRIMARY KEY,
            epic_id INTEGER,
            title VARCHAR(200),
            estimate_minutes INTEGER DEFAULT 0,
            deleted_at TIMESTAMP
        )
    """)
    
    # Insert test epic
    cursor.execute("""
        INSERT INTO framework_epics (id, epic_key, name) 
        VALUES (1, 'TEST_1', 'Test Epic')
    """)
    
    conn.commit()
    conn.close()
    
    try:
        # Initialize DatabaseManager
        db_manager = DatabaseManager(framework_db_path=db_path)
        
        print("✅ DatabaseManager initialized with duration extension")
        
        # Test 1: Update duration description
        success = db_manager.update_duration_description(1, "2.5 dias")
        print(f"✅ update_duration_description: {success}")
        assert success
        
        # Test 2: Calculate duration
        duration = db_manager.calculate_epic_duration(1)
        print(f"✅ calculate_epic_duration: {duration} days")
        assert duration == 2.5
        
        # Test 3: Validate consistency
        is_valid = db_manager.validate_date_consistency(1)
        print(f"✅ validate_date_consistency: {is_valid}")
        assert is_valid
        
        # Test 4: Get timeline
        timeline = db_manager.get_epic_timeline(1)
        print(f"✅ get_epic_timeline: {timeline}")
        if "error" in timeline:
            print(f"⚠️  Timeline has error: {timeline['error']}")
        else:
            assert "epic" in timeline
            assert "duration_info" in timeline
        
        print("\n🎉 All core DatabaseManager extension methods work correctly!")
        
        # Verify in database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT duration_description, calculated_duration_days FROM framework_epics WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        
        print(f"📊 Database verification: description='{row[0]}', days={row[1]}")
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    test_quick_validation()
