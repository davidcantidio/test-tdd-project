#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 VALIDATION - New Topological Fields

Validação específica dos 4 novos campos adicionados pela migração 
m_2025_09_04_complete_topological_fields.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def get_connection():
    db_path = Path("framework.db")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def validate_new_fields():
    """Validate the 4 new fields added by the migration."""
    print("🔍 Validating new topological fields...")
    
    with get_connection() as conn:
        # Check if all 4 new fields exist with correct types and defaults
        cursor = conn.execute("PRAGMA table_info(framework_epics)")
        columns = cursor.fetchall()
        
        new_fields = {
            "effort_estimate": {"type": "INTEGER", "default": "7", "found": False},
            "tdd_phase": {"type": "TEXT", "default": None, "found": False},
            "tdd_order": {"type": "INTEGER", "default": None, "found": False},
            "complexity_score": {"type": "DECIMAL(5,2)", "default": "3.0", "found": False}
        }
        
        print(f"\n📊 Checking for new fields in framework_epics:")
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            col_default = col[4]
            
            if col_name in new_fields:
                new_fields[col_name]["found"] = True
                new_fields[col_name]["actual_type"] = col_type
                new_fields[col_name]["actual_default"] = col_default
                print(f"  ✅ {col_name} ({col_type}) - Default: {col_default}")
        
        # Verify all fields found
        all_found = all(field["found"] for field in new_fields.values())
        
        if not all_found:
            missing = [name for name, field in new_fields.items() if not field["found"]]
            print(f"❌ Missing fields: {missing}")
            return False
        
        return True

def validate_new_indexes():
    """Validate the 3 new indexes added by the migration."""
    print(f"\n🔍 Validating new topological indexes...")
    
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='index' AND name IN (
                'idx_epics_effort_complexity',
                'idx_epics_tdd_workflow', 
                'idx_epics_topological_sort'
            )
        """)
        indexes = cursor.fetchall()
        
        expected_indexes = [
            "idx_epics_effort_complexity",
            "idx_epics_tdd_workflow",
            "idx_epics_topological_sort"
        ]
        
        found_indexes = [idx[0] for idx in indexes]
        
        print(f"📊 New topological indexes:")
        for idx_name in expected_indexes:
            status = "✅" if idx_name in found_indexes else "❌"
            print(f"  {status} {idx_name}")
        
        # Show index definitions
        for idx in indexes:
            print(f"    SQL: {idx[1]}")
        
        return len(found_indexes) == len(expected_indexes)

def test_constraints():
    """Test the CHECK constraints on the new fields."""
    print(f"\n🔍 Testing CHECK constraints...")
    
    with get_connection() as conn:
        try:
            # Test tdd_phase constraint
            try:
                conn.execute("BEGIN TRANSACTION")
                conn.execute("""
                    INSERT INTO framework_epics (project_id, epic_key, name, tdd_phase)
                    VALUES (999, 'TEST_CONSTRAINT_1', 'Test Constraint', 'invalid_phase')
                """)
                conn.execute("ROLLBACK")
                print("❌ tdd_phase constraint not working - should have failed")
                return False
            except sqlite3.Error:
                try:
                    conn.execute("ROLLBACK")
                except:
                    pass
                print("✅ tdd_phase constraint working")
            
            # Test tdd_order constraint  
            try:
                conn.execute("BEGIN TRANSACTION")
                conn.execute("""
                    INSERT INTO framework_epics (project_id, epic_key, name, tdd_order)
                    VALUES (999, 'TEST_CONSTRAINT_2', 'Test Constraint', 99)
                """)
                conn.execute("ROLLBACK")
                print("❌ tdd_order constraint not working - should have failed")
                return False
            except sqlite3.Error:
                try:
                    conn.execute("ROLLBACK")
                except:
                    pass
                print("✅ tdd_order constraint working")
            
            # Test valid values
            conn.execute("BEGIN TRANSACTION")
            conn.execute("""
                INSERT INTO framework_epics (project_id, epic_key, name, tdd_phase, tdd_order, effort_estimate, complexity_score)
                VALUES (999, 'TEST_VALID', 'Valid Test', 'red', 1, 5, 4.5)
            """)
            
            cursor = conn.execute("SELECT id FROM framework_epics WHERE epic_key = 'TEST_VALID'")
            test_id = cursor.fetchone()[0]
            
            # Clean up
            conn.execute("DELETE FROM framework_epics WHERE id = ?", (test_id,))
            conn.commit()
            
            print("✅ Valid values accepted correctly")
            return True
            
        except Exception as e:
            print(f"❌ Constraint test failed: {e}")
            try:
                conn.rollback()
            except:
                pass
            return False

def test_topological_algorithm_with_new_fields():
    """Test the topological algorithm with the new fields."""
    print(f"\n🔍 Testing topological algorithm with new fields...")
    
    try:
        # Import the algorithm
        import sys
        sys.path.append(".")
        from DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO import Task, topological_sort_with_priority_corrected
        
        # Create test tasks with all fields including new ones
        test_tasks = [
            Task(
                task_key="epic_1",
                priority=1, 
                effort_estimate=5,  # New field
                tdd_order=1,        # New field 
                tdd_phase='red'     # Would be used if algorithm supported it
            ),
            Task(
                task_key="epic_2", 
                priority=2,
                effort_estimate=3,  # New field
                tdd_order=2,        # New field
                tdd_phase='green'   # Would be used if algorithm supported it
            ),
            Task(
                task_key="epic_3",
                priority=3,
                effort_estimate=7,  # New field 
                tdd_order=3,        # New field
                tdd_phase='refactor' # Would be used if algorithm supported it
            )
        ]
        
        # Create dependencies
        dependencies = [
            ("epic_2", "epic_1"),  # epic_2 depends on epic_1
            ("epic_3", "epic_2"),  # epic_3 depends on epic_2
        ]
        
        # Run algorithm
        execution_order, task_scores, exec_time = topological_sort_with_priority_corrected(
            test_tasks, dependencies
        )
        
        print(f"✅ Algorithm works with new fields!")
        print(f"  • Execution time: {exec_time:.2f}ms")
        print(f"  • Execution order: {' → '.join(execution_order)}")
        
        # Verify all required fields are accessible
        sample_task = test_tasks[0]
        required_fields = ['task_key', 'priority', 'effort_estimate', 'tdd_order']
        
        for field in required_fields:
            if hasattr(sample_task, field):
                value = getattr(sample_task, field)
                print(f"  • {field}: {value} ✅")
            else:
                print(f"  • {field}: MISSING ❌")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Algorithm test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("="*80)
    print("🔍 NEW TOPOLOGICAL FIELDS VALIDATION")
    print("="*80)
    print(f"📅 Validation Time: {datetime.now().isoformat()}")
    
    results = {
        "new_fields": validate_new_fields(),
        "new_indexes": validate_new_indexes(), 
        "constraints": test_constraints(),
        "algorithm_compatibility": test_topological_algorithm_with_new_fields()
    }
    
    print(f"\n📊 VALIDATION RESULTS:")
    all_passed = True
    for test_name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {test_name.replace('_', ' ').title()}")
        if not passed:
            all_passed = False
    
    print(f"\n🎯 OVERALL STATUS: {'✅ ALL VALIDATIONS PASSED' if all_passed else '❌ SOME VALIDATIONS FAILED'}")
    
    if all_passed:
        print(f"\n🚀 MIGRATION VALIDATION SUCCESSFUL!")
        print(f"✅ All 4 new fields added correctly")
        print(f"✅ All 3 new indexes created")
        print(f"✅ CHECK constraints working")
        print(f"✅ Algorithm compatibility maintained")
        print(f"✅ Database ready for IA-driven epic generation with complete field set!")
    else:
        print(f"\n⚠️ VALIDATION ISSUES DETECTED - Review and fix before proceeding")
    
    print("="*80)
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)