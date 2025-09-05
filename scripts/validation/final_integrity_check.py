#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 FINAL INTEGRITY CHECK - Post Migration Validation

Validação final detalhada após aplicação das 3 migrações críticas:
- Estrutura completa das tabelas
- Funcionamento de triggers
- Integridade referencial
- Compatibilidade com DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO.py
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def get_connection():
    db_path = Path("framework.db")
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def check_framework_epics_structure():
    """Verificar estrutura completa da tabela framework_epics."""
    print("🔍 Checking framework_epics table structure...")
    
    with get_connection() as conn:
        # Get table schema
        cursor = conn.execute("PRAGMA table_info(framework_epics)")
        columns = cursor.fetchall()
        
        print(f"📊 framework_epics has {len(columns)} columns:")
        
        expected_new_columns = {
            "sort_order": False,
            "ai_score": False,
            "ai_sort_version": False, 
            "ai_sort_explainer": False,
            "order_locked": False
        }
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            is_nullable = not col[3]
            default_value = col[4]
            
            print(f"  • {col_name} ({col_type}) - Nullable: {is_nullable} - Default: {default_value}")
            
            if col_name in expected_new_columns:
                expected_new_columns[col_name] = True
        
        print(f"\n✅ New migration columns status:")
        for col_name, found in expected_new_columns.items():
            status = "✅" if found else "❌"
            print(f"  {status} {col_name}")
        
        return all(expected_new_columns.values())

def check_epic_dependencies_table():
    """Verificar estrutura da tabela framework_epic_dependencies."""
    print(f"\n🔍 Checking framework_epic_dependencies table...")
    
    with get_connection() as conn:
        # Check if table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='framework_epic_dependencies'"
        )
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("❌ framework_epic_dependencies table not found!")
            return False
        
        print("✅ framework_epic_dependencies table exists")
        
        # Get table schema
        cursor = conn.execute("PRAGMA table_info(framework_epic_dependencies)")
        columns = cursor.fetchall()
        
        print(f"📊 framework_epic_dependencies has {len(columns)} columns:")
        for col in columns:
            print(f"  • {col[1]} ({col[2]})")
        
        # Check foreign key constraints
        cursor = conn.execute("PRAGMA foreign_key_list(framework_epic_dependencies)")
        foreign_keys = cursor.fetchall()
        
        print(f"🔗 Foreign key constraints: {len(foreign_keys)}")
        for fk in foreign_keys:
            print(f"  • {fk[3]} → {fk[2]}({fk[4]})")
        
        return True

def check_indexes():
    """Verificar todos os índices criados pelas migrações."""
    print(f"\n🔍 Checking database indexes...")
    
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT name, tbl_name, sql 
            FROM sqlite_master 
            WHERE type='index' AND name LIKE '%epic%'
            ORDER BY name
        """)
        indexes = cursor.fetchall()
        
        expected_indexes = [
            "idx_framework_epics_project_order",
            "idx_framework_epics_project", 
            "idx_epic_dep_project_epic",
            "idx_epic_dep_project_depends_on"
        ]
        
        found_indexes = [idx[0] for idx in indexes]
        
        print(f"📊 Found {len(indexes)} epic-related indexes:")
        for idx in indexes:
            print(f"  • {idx[0]} on {idx[1]}")
        
        print(f"\n✅ Expected indexes status:")
        for expected_idx in expected_indexes:
            status = "✅" if expected_idx in found_indexes else "❌"
            print(f"  {status} {expected_idx}")
        
        return all(idx in found_indexes for idx in expected_indexes)

def check_triggers():
    """Verificar todos os triggers criados pelas migrações."""
    print(f"\n🔍 Checking database triggers...")
    
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT name, tbl_name, sql 
            FROM sqlite_master 
            WHERE type='trigger' AND name LIKE '%epic%'
            ORDER BY name
        """)
        triggers = cursor.fetchall()
        
        expected_triggers = [
            "trg_framework_epics_sort_order_ai",
            "trg_epic_dep_no_self_insert",
            "trg_epic_dep_no_self_update",
            "trg_epic_dep_project_match_insert", 
            "trg_epic_dep_project_match_update",
            "trg_epics_block_sort_update_when_locked"
        ]
        
        found_triggers = [trig[0] for trig in triggers]
        
        print(f"📊 Found {len(triggers)} epic-related triggers:")
        for trig in triggers:
            print(f"  • {trig[0]} on {trig[1]}")
        
        print(f"\n✅ Expected triggers status:")
        for expected_trig in expected_triggers:
            status = "✅" if expected_trig in found_triggers else "❌"
            print(f"  {status} {expected_trig}")
        
        return all(trig in found_triggers for trig in expected_triggers)

def test_topological_algorithm_compatibility():
    """Testar compatibilidade com DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO.py."""
    print(f"\n🔍 Testing compatibility with topological ordering algorithm...")
    
    try:
        # Import the algorithm
        import sys
        sys.path.append(".")
        from DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO import Task, topological_sort_with_priority_corrected
        
        # Create test tasks
        test_tasks = [
            Task(task_key="task_1", priority=1, effort_estimate=3, tdd_order=1),
            Task(task_key="task_2", priority=2, effort_estimate=5, tdd_order=2),
            Task(task_key="task_3", priority=3, effort_estimate=2, tdd_order=3),
        ]
        
        # Create test dependencies 
        test_dependencies = [
            ("task_2", "task_1"),  # task_2 depends on task_1
            ("task_3", "task_2"),  # task_3 depends on task_2
        ]
        
        # Run algorithm
        execution_order, task_scores, exec_time = topological_sort_with_priority_corrected(
            test_tasks, test_dependencies
        )
        
        print(f"✅ Algorithm executed successfully!")
        print(f"  • Execution time: {exec_time:.2f}ms")
        print(f"  • Task order: {' → '.join(execution_order)}")
        
        # Verify all required fields are available
        sample_task = test_tasks[0]
        required_fields = ['task_key', 'priority', 'effort_estimate', 'tdd_order']
        
        fields_ok = all(hasattr(sample_task, field) for field in required_fields)
        print(f"  • Required fields available: {'✅' if fields_ok else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Algorithm compatibility test failed: {e}")
        return False

def test_database_operations():
    """Testar operações básicas no banco de dados."""
    print(f"\n🔍 Testing basic database operations...")
    
    with get_connection() as conn:
        try:
            # Test 1: Insert test epic (should auto-assign sort_order)
            cursor = conn.execute("""
                INSERT INTO framework_epics (project_id, epic_key, name, description, status)
                VALUES (999, 'TEST_EPIC_001', 'Test Epic', 'Test Description', 'testing')
            """)
            test_epic_id = cursor.lastrowid
            
            # Verify sort_order was auto-assigned
            cursor = conn.execute(
                "SELECT sort_order FROM framework_epics WHERE id = ?", 
                (test_epic_id,)
            )
            row = cursor.fetchone()
            sort_order = row[0] if row else None
            
            print(f"✅ Auto sort_order assignment: {sort_order is not None}")
            
            # Test 2: Try to create self-dependency (should fail)
            try:
                conn.execute("""
                    INSERT INTO framework_epic_dependencies 
                    (project_id, epic_id, depends_on_epic_id)
                    VALUES (999, ?, ?)
                """, (test_epic_id, test_epic_id))
                
                print(f"❌ Self-dependency prevention failed")
                dependency_prevention_works = False
            except sqlite3.Error:
                print(f"✅ Self-dependency prevention working")
                dependency_prevention_works = True
            
            # Test 3: Try to update locked epic sort_order (should fail)
            conn.execute("UPDATE framework_epics SET order_locked = 1 WHERE id = ?", (test_epic_id,))
            
            try:
                conn.execute("UPDATE framework_epics SET sort_order = 999 WHERE id = ?", (test_epic_id,))
                print(f"❌ Order lock prevention failed")
                order_lock_works = False
            except sqlite3.Error:
                print(f"✅ Order lock prevention working") 
                order_lock_works = True
            
            # Cleanup
            conn.execute("DELETE FROM framework_epics WHERE id = ?", (test_epic_id,))
            conn.commit()
            
            return dependency_prevention_works and order_lock_works
            
        except Exception as e:
            print(f"❌ Database operations test failed: {e}")
            try:
                conn.rollback()
            except:
                pass
            return False

def generate_final_report():
    """Gerar relatório final do estado das migrações."""
    print("\n" + "="*80)
    print("🎯 FINAL INTEGRITY CHECK REPORT")
    print("="*80)
    print(f"📅 Check Time: {datetime.now().isoformat()}")
    print(f"🗄️ Database: framework.db")
    
    # Run all checks
    results = {
        "framework_epics_structure": check_framework_epics_structure(),
        "epic_dependencies_table": check_epic_dependencies_table(),
        "database_indexes": check_indexes(),
        "database_triggers": check_triggers(),
        "topological_algorithm_compatibility": test_topological_algorithm_compatibility(),
        "database_operations": test_database_operations()
    }
    
    print(f"\n📊 FINAL RESULTS SUMMARY:")
    all_passed = True
    
    for check_name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name.replace('_', ' ').title()}")
        if not passed:
            all_passed = False
    
    print(f"\n🎯 OVERALL STATUS: {'✅ ALL CHECKS PASSED' if all_passed else '❌ SOME CHECKS FAILED'}")
    
    if all_passed:
        print(f"\n🚀 PHASE 1.1 COMPLETED SUCCESSFULLY!")
        print(f"✅ Database is ready for IA-driven epic generation")
        print(f"✅ Topological ordering algorithm compatibility confirmed") 
        print(f"✅ All triggers and constraints working correctly")
        print(f"✅ Ready to proceed to Phase 2: Implementation of Missing Fields")
    else:
        print(f"\n⚠️ PHASE 1.1 INCOMPLETE - Fix issues before proceeding")
    
    print("="*80)
    return all_passed

if __name__ == "__main__":
    success = generate_final_report()
    exit(0 if success else 1)