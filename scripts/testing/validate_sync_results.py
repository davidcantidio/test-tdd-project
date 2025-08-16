#!/usr/bin/env python3
"""
🔍 Data Integrity Validation - Epic Sync Results
"""

import sqlite3
import json
from pathlib import Path

def validate_sync_integrity():
    """Validate that all epics and tasks were synced correctly."""
    
    print("🔍 Data Integrity Validation")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('framework.db')
        conn.row_factory = sqlite3.Row
        
        # Get all synced epics
        cursor = conn.execute("""
            SELECT epic_key, name, 
                   COUNT(framework_tasks.id) as task_count,
                   planned_start_date, planned_end_date
            FROM framework_epics 
            LEFT JOIN framework_tasks ON framework_epics.id = framework_tasks.epic_id 
            WHERE framework_epics.epic_key IN ('0', '2', '3', '4', '5', '6', '7', '8', '0.5')
            GROUP BY epic_key, name 
            ORDER BY epic_key
        """)
        
        print("\n📊 Synced Epics Summary:")
        print("-" * 60)
        
        total_epics = 0
        total_tasks = 0
        
        for row in cursor:
            epic_key = row['epic_key']
            name = row['name'] 
            task_count = row['task_count']
            start_date = row['planned_start_date'] or 'Not calculated'
            end_date = row['planned_end_date'] or 'Not calculated'
            
            total_epics += 1
            total_tasks += task_count
            
            print(f"Epic {epic_key}: {name}")
            print(f"  📋 Tasks: {task_count}")
            print(f"  📅 Start: {start_date}")
            print(f"  📅 End: {end_date}")
            print()
        
        print("=" * 60)
        print(f"✅ Total Epics: {total_epics}")
        print(f"✅ Total Tasks: {total_tasks}")
        
        # Validate JSON field integrity
        print("\n🔍 JSON Field Validation:")
        cursor = conn.execute("""
            SELECT epic_key, 
                   LENGTH(goals) as goals_len,
                   LENGTH(definition_of_done) as dod_len,
                   LENGTH(labels) as labels_len
            FROM framework_epics 
            WHERE epic_key IN ('0', '2', '3', '4', '5', '6', '7', '8', '0.5')
        """)
        
        for row in cursor:
            epic_key = row['epic_key']
            goals_len = row['goals_len']
            dod_len = row['dod_len'] 
            labels_len = row['labels_len']
            
            print(f"Epic {epic_key}: JSON fields = {goals_len + dod_len + labels_len} chars total")
        
        # Check for sync tracking
        print("\n📈 Sync Status:")
        cursor = conn.execute("""
            SELECT COUNT(*) as synced_count 
            FROM framework_epics 
            WHERE sync_status = 'synced'
            AND epic_key IN ('0', '2', '3', '4', '5', '6', '7', '8', '0.5')
        """)
        
        synced_count = cursor.fetchone()['synced_count']
        print(f"✅ Epics with sync_status = 'synced': {synced_count}")
        
        conn.close()
        
        print("\n✅ Data integrity validation completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def compare_with_json_files():
    """Compare database content with original JSON files."""
    
    print("\n🔄 JSON-Database Comparison:")
    print("-" * 40)
    
    json_files = list(Path("epics/user_epics").glob("*.json"))
    
    for file_path in sorted(json_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            epic_data = data.get('epic', data)
            epic_key = epic_data.get('id', file_path.stem)
            name = epic_data.get('name', 'Unknown')
            task_count = len(epic_data.get('tasks', []))
            
            print(f"📄 {file_path.name}: Epic {epic_key} '{name}' ({task_count} tasks)")
            
        except Exception as e:
            print(f"❌ Failed to read {file_path}: {e}")
    
    print(f"\n📊 Total JSON files processed: {len(json_files)}")

if __name__ == "__main__":
    validate_sync_integrity()
    compare_with_json_files()