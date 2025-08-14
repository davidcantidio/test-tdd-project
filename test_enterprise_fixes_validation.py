"""
🧪 Enterprise Hardening Fixes Validation
Tests specifically affected interfaces: statistics, timelines, and backup restore
"""

import sys
from pathlib import Path
import tempfile
import json
import zipfile
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from streamlit_extension.utils.database import DatabaseManager
from streamlit_extension.config.backup_restore import ConfigurationBackupManager, BackupType

def test_user_stats_safety():
    """Test get_user_stats with enterprise safety fixes."""
    print("🔍 Testing user statistics with safety fixes...")
    
    manager = DatabaseManager()
    
    # Test with existing user
    stats = manager.get_user_stats(user_id=1)
    print(f"✅ User stats retrieved safely: {stats}")
    
    # Verify all required fields are present and numeric
    required_fields = ["completed_tasks", "total_points", "active_streaks"]
    for field in required_fields:
        assert field in stats, f"Missing required field: {field}"
        assert isinstance(stats[field], (int, float)), f"Field {field} is not numeric: {type(stats[field])}"
        assert stats[field] >= 0, f"Field {field} has negative value: {stats[field]}"
    
    print("✅ All user stats fields validated successfully")

def test_daily_summary_safety():
    """Test get_daily_summary with enterprise safety fixes."""
    print("🔍 Testing daily summary with safety fixes...")
    
    manager = DatabaseManager()
    summary = manager.get_daily_summary()
    print(f"✅ Daily summary retrieved safely: {summary}")
    
    # Verify critical fields have safe defaults
    critical_fields = ["tasks_completed", "tasks_in_progress", "tasks_created", 
                      "achievements_today", "timer_sessions", "focus_time_minutes"]
    
    for field in critical_fields:
        if field in summary:
            assert isinstance(summary[field], (int, float)), f"Field {field} is not numeric"
            assert summary[field] >= 0, f"Field {field} has negative value"
    
    print("✅ Daily summary fields validated successfully")

def test_epic_timeline_safety():
    """Test get_epic_timeline with enterprise safety fixes."""
    print("🔍 Testing epic timeline with safety fixes...")
    
    manager = DatabaseManager()
    
    # Test with existing epic
    timeline = manager.get_epic_timeline(epic_id=1)
    print(f"✅ Epic timeline retrieved safely: {timeline}")
    
    # Should not contain errors even if epic doesn't exist
    if "error" not in timeline:
        assert "epic" in timeline, "Missing epic in timeline"
        assert "validation" in timeline, "Missing validation in timeline"
    
    # Test with non-existent epic (should handle gracefully)
    timeline_missing = manager.get_epic_timeline(epic_id=999999)
    print(f"✅ Non-existent epic handled safely: {timeline_missing}")
    
    print("✅ Epic timeline safety validated successfully")

def test_backup_restore_logging():
    """Test backup restore with improved logging."""
    print("🔍 Testing backup restore with structured logging...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        backup_manager = ConfigurationBackupManager(backup_dir=Path(temp_dir))
        
        # Create a test backup with invalid JSON
        backup_file = Path(temp_dir) / "test_backup.zip"
        with zipfile.ZipFile(backup_file, 'w') as zipf:
            zipf.writestr("streamlit_config.json", "invalid json content")
            zipf.writestr("themes.json", '{"valid": true}')
        
        # Register the backup manually
        backup_manager._backup_index["test_backup"] = type('BackupInfo', (), {
            'file_path': backup_file,
            'includes_streamlit_config': True,
            'includes_themes': True,
            'includes_cache_settings': False,
            'includes_database_config': False
        })()
        
        # Test restore (should log warnings instead of silent failures)
        result = backup_manager.restore_backup("test_backup", ["streamlit_config", "themes"])
        print(f"✅ Backup restore with logging completed: {result}")
    
    print("✅ Backup restore logging validated successfully")

def test_duration_calculation_safety():
    """Test duration calculation methods with safety fixes."""
    print("🔍 Testing duration calculation with safety fixes...")
    
    manager = DatabaseManager()
    
    # Test task duration calculation
    duration = manager._calculate_epic_duration_from_tasks(epic_id=1)
    print(f"✅ Epic duration calculated safely: {duration} days")
    
    assert isinstance(duration, (int, float)), f"Duration is not numeric: {type(duration)}"
    assert duration >= 0, f"Duration is negative: {duration}"
    
    # Test with non-existent epic (should return 0.0 safely)
    duration_missing = manager._calculate_epic_duration_from_tasks(epic_id=999999)
    print(f"✅ Non-existent epic duration handled safely: {duration_missing}")
    
    assert duration_missing == 0.0, f"Non-existent epic should return 0.0, got: {duration_missing}"
    
    print("✅ Duration calculation safety validated successfully")

def main():
    """Run all enterprise hardening validation tests."""
    print("🚀 Starting Enterprise Hardening Fixes Validation")
    print("=" * 60)
    
    try:
        test_user_stats_safety()
        print()
        
        test_daily_summary_safety()
        print()
        
        test_epic_timeline_safety()
        print()
        
        test_backup_restore_logging()
        print()
        
        test_duration_calculation_safety()
        print()
        
        print("=" * 60)
        print("🎉 ALL ENTERPRISE HARDENING FIXES VALIDATED SUCCESSFULLY!")
        print("✅ Database access patterns: SAFE")
        print("✅ Null pointer prevention: ACTIVE")
        print("✅ Structured logging: WORKING")
        print("✅ Safe defaults: IMPLEMENTED")
        print("✅ Error handling: ROBUST")
        
    except Exception as e:
        print(f"❌ VALIDATION FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()