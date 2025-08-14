#!/usr/bin/env python3
"""
🔍 FASE 7.2.4 - Comprehensive Data Integrity Validation

Testes completos de integridade para certificação do sistema:
1. Referential integrity validation
2. JSON field consistency  
3. Performance benchmarks
4. Bidirectional sync validation (DB → JSON)
5. Data consistency checks
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
import sys

# Add migration to path
sys.path.append(str(Path(__file__).parent / "migration"))

try:
    from bidirectional_sync import BidirectionalSyncEngine
    SYNC_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Sync engine not available: {e}")
    SYNC_ENGINE_AVAILABLE = False


class IntegrityValidator:
    """Comprehensive integrity validation for the epic-task system."""
    
    def __init__(self, db_path: str = "framework.db"):
        self.db_path = db_path
        self.results = {
            "referential_integrity": False,
            "json_consistency": False, 
            "performance_benchmarks": False,
            "bidirectional_sync": False,
            "data_consistency": False,
            "overall_status": False
        }
        
    def get_db_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def test_referential_integrity(self) -> bool:
        """Test foreign key relationships and constraints."""
        print("\n🔍 Testing Referential Integrity...")
        print("-" * 45)
        
        try:
            with self.get_db_connection() as conn:
                # Test 1: All tasks have valid epic_id references
                cursor = conn.execute("""
                    SELECT COUNT(*) as orphaned_tasks
                    FROM framework_tasks t
                    LEFT JOIN framework_epics e ON t.epic_id = e.id
                    WHERE e.id IS NULL AND t.status != 'deleted'
                """)
                orphaned_tasks = cursor.fetchone()['orphaned_tasks']
                
                if orphaned_tasks > 0:
                    print(f"❌ Found {orphaned_tasks} orphaned tasks without valid epic_id")
                    return False
                print(f"✅ No orphaned tasks found")
                
                # Test 2: Epic-task count consistency
                cursor = conn.execute("""
                    SELECT e.epic_key, e.name,
                           COUNT(t.id) as db_task_count
                    FROM framework_epics e
                    LEFT JOIN framework_tasks t ON e.id = t.epic_id
                    WHERE e.epic_key IN ('0.5', '2', '3', '4', '5', '6', '7', '8')
                    GROUP BY e.epic_key, e.name
                    ORDER BY e.epic_key
                """)
                
                epic_counts = {}
                for row in cursor:
                    epic_counts[row['epic_key']] = {
                        'name': row['name'],
                        'db_count': row['db_task_count']
                    }
                
                # Compare with JSON files
                json_dir = Path("epics/user_epics")
                for file_path in json_dir.glob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        epic_data = data.get('epic', data)
                        epic_key = epic_data.get('id', file_path.stem)
                        json_task_count = len(epic_data.get('tasks', []))
                        
                        if epic_key in epic_counts:
                            db_count = epic_counts[epic_key]['db_count']
                            if db_count != json_task_count:
                                print(f"❌ Task count mismatch for Epic {epic_key}: JSON={json_task_count}, DB={db_count}")
                                return False
                            print(f"✅ Epic {epic_key}: {db_count} tasks consistent")
                        
                    except Exception as e:
                        print(f"⚠️ Could not validate {file_path}: {e}")
                
                # Test 3: Required field validation
                cursor = conn.execute("""
                    SELECT COUNT(*) as missing_required
                    FROM framework_epics 
                    WHERE epic_key IS NULL OR epic_key = ''
                       OR name IS NULL OR name = ''
                """)
                missing_required = cursor.fetchone()['missing_required']
                
                if missing_required > 0:
                    print(f"❌ Found {missing_required} epics with missing required fields")
                    return False
                print(f"✅ All epics have required fields")
                
                return True
                
        except Exception as e:
            print(f"❌ Referential integrity test failed: {e}")
            return False
    
    def test_json_consistency(self) -> bool:
        """Test JSON field parsing and consistency."""
        print("\n🔍 Testing JSON Field Consistency...")
        print("-" * 42)
        
        try:
            with self.get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT epic_key, goals, definition_of_done, labels,
                           performance_constraints, quality_gates, automation_hooks
                    FROM framework_epics
                    WHERE epic_key IN ('0.5', '2', '3', '4', '5', '6', '7', '8')
                """)
                
                json_parse_errors = 0
                for row in cursor:
                    epic_key = row['epic_key']
                    
                    # Test each JSON field
                    json_fields = {
                        'goals': row['goals'],
                        'definition_of_done': row['definition_of_done'],
                        'labels': row['labels'],
                        'performance_constraints': row['performance_constraints'],
                        'quality_gates': row['quality_gates'],
                        'automation_hooks': row['automation_hooks']
                    }
                    
                    for field_name, field_value in json_fields.items():
                        if field_value:
                            try:
                                parsed = json.loads(field_value)
                                # Validate it's a proper data structure
                                if not isinstance(parsed, (list, dict)):
                                    print(f"❌ Epic {epic_key}.{field_name}: Invalid JSON structure type")
                                    json_parse_errors += 1
                            except json.JSONDecodeError as e:
                                print(f"❌ Epic {epic_key}.{field_name}: JSON parse error - {e}")
                                json_parse_errors += 1
                
                if json_parse_errors > 0:
                    print(f"❌ Found {json_parse_errors} JSON parsing errors")
                    return False
                
                print("✅ All JSON fields parse correctly")
                
                # Test task JSON fields
                cursor = conn.execute("""
                    SELECT task_key, epic_id,
                           test_specs, acceptance_criteria, deliverables,
                           files_touched, test_plan
                    FROM framework_tasks
                    WHERE epic_id IN (
                        SELECT id FROM framework_epics 
                        WHERE epic_key IN ('0.5', '2', '3', '4', '5', '6', '7', '8')
                    )
                    LIMIT 10
                """)
                
                task_parse_errors = 0
                for row in cursor:
                    task_key = row['task_key']
                    
                    task_json_fields = {
                        'test_specs': row['test_specs'],
                        'acceptance_criteria': row['acceptance_criteria'],
                        'deliverables': row['deliverables'],
                        'files_touched': row['files_touched'],
                        'test_plan': row['test_plan']
                    }
                    
                    for field_name, field_value in task_json_fields.items():
                        if field_value:
                            try:
                                parsed = json.loads(field_value)
                                if not isinstance(parsed, (list, dict)):
                                    task_parse_errors += 1
                            except json.JSONDecodeError:
                                task_parse_errors += 1
                
                if task_parse_errors > 0:
                    print(f"❌ Found {task_parse_errors} task JSON parsing errors")
                    return False
                
                print("✅ All task JSON fields parse correctly")
                return True
                
        except Exception as e:
            print(f"❌ JSON consistency test failed: {e}")
            return False
    
    def test_performance_benchmarks(self) -> bool:
        """Test query performance benchmarks."""
        print("\n🔍 Testing Performance Benchmarks...")
        print("-" * 40)
        
        try:
            with self.get_db_connection() as conn:
                # Test 1: Epic retrieval performance
                start_time = time.time()
                cursor = conn.execute("""
                    SELECT * FROM framework_epics 
                    WHERE epic_key IN ('0.5', '2', '3', '4', '5', '6', '7', '8')
                """)
                epics = cursor.fetchall()
                epic_query_time = time.time() - start_time
                
                if epic_query_time > 0.1:  # 100ms threshold
                    print(f"❌ Epic query too slow: {epic_query_time:.3f}s")
                    return False
                print(f"✅ Epic query performance: {epic_query_time:.3f}s")
                
                # Test 2: Task retrieval performance  
                start_time = time.time()
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM framework_tasks t
                    JOIN framework_epics e ON t.epic_id = e.id
                    WHERE e.epic_key IN ('0.5', '2', '3', '4', '5', '6', '7', '8')
                """)
                task_count = cursor.fetchone()[0]
                task_query_time = time.time() - start_time
                
                if task_query_time > 0.2:  # 200ms threshold
                    print(f"❌ Task count query too slow: {task_query_time:.3f}s")
                    return False
                print(f"✅ Task query performance: {task_query_time:.3f}s ({task_count} tasks)")
                
                # Test 3: Complex join performance
                start_time = time.time()
                cursor = conn.execute("""
                    SELECT e.epic_key, e.name, 
                           COUNT(t.id) as task_count,
                           AVG(t.estimate_minutes) as avg_estimate
                    FROM framework_epics e
                    LEFT JOIN framework_tasks t ON e.id = t.epic_id
                    WHERE e.epic_key IN ('0.5', '2', '3', '4', '5', '6', '7', '8')
                    GROUP BY e.epic_key, e.name
                """)
                join_results = cursor.fetchall()
                join_query_time = time.time() - start_time
                
                if join_query_time > 0.3:  # 300ms threshold
                    print(f"❌ Join query too slow: {join_query_time:.3f}s")
                    return False
                print(f"✅ Join query performance: {join_query_time:.3f}s")
                
                return True
                
        except Exception as e:
            print(f"❌ Performance benchmark failed: {e}")
            return False
    
    def test_bidirectional_sync(self) -> bool:
        """Test Database → JSON sync functionality."""
        print("\n🔍 Testing Bidirectional Sync (DB → JSON)...")
        print("-" * 47)
        
        if not SYNC_ENGINE_AVAILABLE:
            print("❌ Sync engine not available - skipping test")
            return False
        
        try:
            sync_engine = BidirectionalSyncEngine()
            
            # Test export of one epic back to JSON
            test_epic_key = "2"
            output_path = Path("test_export_epic_2.json")
            
            result = sync_engine.sync_db_to_json(test_epic_key, output_path)
            
            if not result.success:
                print(f"❌ DB to JSON sync failed: {', '.join(result.errors)}")
                return False
            
            print(f"✅ Successfully exported Epic {test_epic_key} to JSON")
            
            # Validate exported JSON structure
            if output_path.exists():
                with open(output_path, 'r', encoding='utf-8') as f:
                    exported_data = json.load(f)
                
                epic_data = exported_data.get('epic', {})
                
                # Check required fields
                required_fields = ['id', 'name', 'summary', 'tasks']
                missing_fields = [field for field in required_fields if field not in epic_data]
                
                if missing_fields:
                    print(f"❌ Exported JSON missing fields: {missing_fields}")
                    return False
                
                print(f"✅ Exported JSON has all required fields")
                print(f"✅ Exported {len(epic_data.get('tasks', []))} tasks")
                
                # Check for calculated fields
                calc_fields = epic_data.get('calculated_fields', {})
                if calc_fields:
                    print(f"✅ Calculated fields present: {len(calc_fields)} fields")
                
                # Clean up test file
                output_path.unlink()
                
                return True
            else:
                print("❌ Export file was not created")
                return False
                
        except Exception as e:
            print(f"❌ Bidirectional sync test failed: {e}")
            return False
    
    def test_data_consistency(self) -> bool:
        """Test overall data consistency and business rules."""
        print("\n🔍 Testing Data Consistency...")
        print("-" * 35)
        
        try:
            with self.get_db_connection() as conn:
                # Test 1: Planned dates consistency
                cursor = conn.execute("""
                    SELECT epic_key, planned_start_date, planned_end_date
                    FROM framework_epics
                    WHERE planned_start_date IS NOT NULL 
                      AND planned_end_date IS NOT NULL
                      AND epic_key IN ('0.5', '2', '3', '4', '5', '6', '7', '8')
                """)
                
                date_inconsistencies = 0
                for row in cursor:
                    epic_key = row['epic_key']
                    start_date = row['planned_start_date']
                    end_date = row['planned_end_date']
                    
                    if start_date > end_date:
                        print(f"❌ Epic {epic_key}: Start date after end date")
                        date_inconsistencies += 1
                
                if date_inconsistencies > 0:
                    print(f"❌ Found {date_inconsistencies} date inconsistencies")
                    return False
                print("✅ All planned dates are consistent")
                
                # Test 2: Task estimates reasonable
                cursor = conn.execute("""
                    SELECT COUNT(*) as unrealistic_tasks
                    FROM framework_tasks t
                    JOIN framework_epics e ON t.epic_id = e.id
                    WHERE e.epic_key IN ('0.5', '2', '3', '4', '5', '6', '7', '8')
                      AND (t.estimate_minutes < 5 OR t.estimate_minutes > 480)
                """)
                unrealistic_tasks = cursor.fetchone()['unrealistic_tasks']
                
                if unrealistic_tasks > 0:
                    print(f"⚠️ Found {unrealistic_tasks} tasks with unrealistic estimates")
                else:
                    print("✅ All task estimates are reasonable")
                
                # Test 3: Sync status consistency
                cursor = conn.execute("""
                    SELECT COUNT(*) as synced_epics
                    FROM framework_epics
                    WHERE sync_status = 'synced'
                      AND epic_key IN ('0.5', '2', '3', '4', '5', '6', '7', '8')
                """)
                synced_epics = cursor.fetchone()['synced_epics']
                
                if synced_epics != 8:  # We expect 8 newly synced epics
                    print(f"⚠️ Sync status inconsistent: {synced_epics}/8 marked as synced")
                else:
                    print("✅ All epics have correct sync status")
                
                return True
                
        except Exception as e:
            print(f"❌ Data consistency test failed: {e}")
            return False
    
    def run_comprehensive_validation(self) -> Dict[str, bool]:
        """Run all validation tests and return results."""
        print("🔍 COMPREHENSIVE DATA INTEGRITY VALIDATION")
        print("=" * 60)
        
        # Run all tests
        self.results["referential_integrity"] = self.test_referential_integrity()
        self.results["json_consistency"] = self.test_json_consistency()
        self.results["performance_benchmarks"] = self.test_performance_benchmarks()
        self.results["bidirectional_sync"] = self.test_bidirectional_sync()
        self.results["data_consistency"] = self.test_data_consistency()
        
        # Calculate overall status
        passed_tests = sum(1 for result in self.results.values() if result)
        total_tests = len(self.results) - 1  # Exclude overall_status
        
        self.results["overall_status"] = passed_tests == total_tests
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION RESULTS SUMMARY:")
        print("-" * 60)
        
        for test_name, result in self.results.items():
            if test_name != "overall_status":
                status = "✅ PASS" if result else "❌ FAIL"
                test_display = test_name.replace("_", " ").title()
                print(f"{test_display:30} {status}")
        
        print("-" * 60)
        overall_status = "✅ PASS" if self.results["overall_status"] else "❌ FAIL"
        print(f"{'Overall Status':30} {overall_status}")
        
        if self.results["overall_status"]:
            print("\n🎉 CERTIFICATION: System ready for production!")
        else:
            failed_tests = [name for name, result in self.results.items() 
                           if not result and name != "overall_status"]
            print(f"\n⚠️  ISSUES: Failed tests: {', '.join(failed_tests)}")
        
        return self.results


def main():
    """Run comprehensive integrity validation."""
    validator = IntegrityValidator()
    results = validator.run_comprehensive_validation()
    
    # Return appropriate exit code
    exit_code = 0 if results["overall_status"] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()