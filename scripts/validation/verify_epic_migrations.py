#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 EPIC MIGRATIONS VERIFICATION SCRIPT

Verifica o estado completo das 3 migrações críticas para framework_epics:
- m_2025_09_01: sort_order + triggers
- m_2025_09_02: epic_dependencies table
- m_2025_09_03: AI audit fields + locks

Usage:
    python scripts/validation/verify_epic_migrations.py [--execute-missing] [--detailed-report]
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class EpicMigrationsVerifier:
    """Comprehensive verification of epic-related database migrations."""
    
    def __init__(self, db_path: str = "framework.db"):
        self.db_path = db_path
        self.full_db_path = project_root / db_path
        self.results = {
            "verification_timestamp": datetime.now().isoformat(),
            "database_path": str(self.full_db_path),
            "migrations_status": {},
            "overall_status": "unknown",
            "issues_found": [],
            "recommendations": [],
            "ready_for_next_phase": False
        }
        
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration."""
        if not self.full_db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.full_db_path}")
            
        conn = sqlite3.connect(str(self.full_db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def verify_column_exists(self, conn: sqlite3.Connection, table: str, column: str) -> bool:
        """Check if column exists in table."""
        cursor = conn.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        return column in columns
    
    def verify_index_exists(self, conn: sqlite3.Connection, index_name: str) -> bool:
        """Check if index exists."""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?", 
            (index_name,)
        )
        return cursor.fetchone() is not None
    
    def verify_trigger_exists(self, conn: sqlite3.Connection, trigger_name: str) -> bool:
        """Check if trigger exists."""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND name=?", 
            (trigger_name,)
        )
        return cursor.fetchone() is not None
        
    def verify_table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        """Check if table exists."""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
            (table_name,)
        )
        return cursor.fetchone() is not None

    def test_trigger_functionality(self, conn: sqlite3.Connection, trigger_test: str, expected_failure: bool = True) -> bool:
        """Test if trigger works by executing a test query."""
        try:
            conn.execute("BEGIN TRANSACTION")
            conn.execute(trigger_test)
            conn.execute("ROLLBACK")
            
            # If we expected failure but got success, trigger isn't working
            if expected_failure:
                return False
            return True
            
        except sqlite3.Error:
            conn.execute("ROLLBACK") 
            # If we expected failure and got it, trigger is working
            if expected_failure:
                return True
            return False
    
    def verify_migration_01_sort_order(self) -> Dict[str, Any]:
        """Verify m_2025_09_01: sort_order migration."""
        logging.info("🔍 Verifying m_2025_09_01: sort_order migration...")
        
        result = {
            "status": "unknown",
            "elements": {},
            "functional_tests": {},
            "issues": []
        }
        
        try:
            with self.get_connection() as conn:
                # Check sort_order column
                result["elements"]["sort_order_column"] = self.verify_column_exists(
                    conn, "framework_epics", "sort_order"
                )
                
                # Check indexes
                result["elements"]["project_order_index"] = self.verify_index_exists(
                    conn, "idx_framework_epics_project_order"
                )
                result["elements"]["project_index"] = self.verify_index_exists(
                    conn, "idx_framework_epics_project"
                )
                
                # Check trigger
                result["elements"]["sort_order_trigger"] = self.verify_trigger_exists(
                    conn, "trg_framework_epics_sort_order_ai"
                )
                
                # Functional tests
                if result["elements"]["sort_order_column"]:
                    # Check if existing data has been initialized
                    cursor = conn.execute(
                        "SELECT COUNT(*) as total, COUNT(sort_order) as initialized FROM framework_epics"
                    )
                    row = cursor.fetchone()
                    total = row[0]
                    initialized = row[1]
                    
                    result["functional_tests"]["existing_data_initialized"] = (
                        total == 0 or initialized == total
                    )
                    result["functional_tests"]["data_stats"] = {
                        "total_epics": total,
                        "initialized_epics": initialized
                    }
                
                # Overall status
                all_elements = all(result["elements"].values())
                all_functional = all(result["functional_tests"].values()) if result["functional_tests"] else True
                
                if all_elements and all_functional:
                    result["status"] = "completed"
                elif any(result["elements"].values()):
                    result["status"] = "partial"
                    result["issues"].append("Migration partially applied - some elements missing")
                else:
                    result["status"] = "missing"
                    result["issues"].append("Migration not applied")
                    
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Error verifying migration: {str(e)}")
            logging.error(f"Error verifying m_2025_09_01: {e}")
        
        return result
    
    def verify_migration_02_dependencies(self) -> Dict[str, Any]:
        """Verify m_2025_09_02: epic_dependencies migration."""
        logging.info("🔍 Verifying m_2025_09_02: epic_dependencies migration...")
        
        result = {
            "status": "unknown",
            "elements": {},
            "functional_tests": {},
            "issues": []
        }
        
        try:
            with self.get_connection() as conn:
                # Check dependencies table
                result["elements"]["dependencies_table"] = self.verify_table_exists(
                    conn, "framework_epic_dependencies"
                )
                
                if result["elements"]["dependencies_table"]:
                    # Check indexes
                    result["elements"]["epic_index"] = self.verify_index_exists(
                        conn, "idx_epic_dep_project_epic"
                    )
                    result["elements"]["depends_on_index"] = self.verify_index_exists(
                        conn, "idx_epic_dep_project_depends_on"
                    )
                    
                    # Check triggers
                    triggers = [
                        "trg_epic_dep_no_self_insert",
                        "trg_epic_dep_no_self_update", 
                        "trg_epic_dep_project_match_insert",
                        "trg_epic_dep_project_match_update"
                    ]
                    
                    result["elements"]["integrity_triggers"] = []
                    for trigger in triggers:
                        exists = self.verify_trigger_exists(conn, trigger)
                        result["elements"]["integrity_triggers"].append(exists)
                    
                    # Functional tests - test self-dependency prevention
                    # First, create a test epic if none exist
                    cursor = conn.execute("SELECT id FROM framework_epics LIMIT 1")
                    epic_row = cursor.fetchone()
                    
                    if epic_row:
                        epic_id = epic_row[0]
                        
                        # Test self-dependency prevention (should fail)
                        test_query = f"""
                            INSERT INTO framework_epic_dependencies 
                            (project_id, epic_id, depends_on_epic_id) 
                            VALUES (1, {epic_id}, {epic_id})
                        """
                        result["functional_tests"]["prevents_self_dependency"] = self.test_trigger_functionality(
                            conn, test_query, expected_failure=True
                        )
                    else:
                        result["functional_tests"]["prevents_self_dependency"] = None
                        result["issues"].append("No epics available to test trigger functionality")
                
                # Overall status
                all_elements = all([
                    result["elements"].get("dependencies_table", False),
                    result["elements"].get("epic_index", False),
                    result["elements"].get("depends_on_index", False),
                    all(result["elements"].get("integrity_triggers", [False]))
                ])
                
                all_functional = all(
                    v for v in result["functional_tests"].values() if v is not None
                ) if result["functional_tests"] else True
                
                if all_elements and all_functional:
                    result["status"] = "completed"
                elif any([
                    result["elements"].get("dependencies_table", False),
                    any(result["elements"].get("integrity_triggers", [False]))
                ]):
                    result["status"] = "partial"
                    result["issues"].append("Migration partially applied")
                else:
                    result["status"] = "missing"
                    result["issues"].append("Migration not applied")
                    
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Error verifying migration: {str(e)}")
            logging.error(f"Error verifying m_2025_09_02: {e}")
        
        return result
    
    def verify_migration_03_ai_audit(self) -> Dict[str, Any]:
        """Verify m_2025_09_03: AI audit fields migration."""
        logging.info("🔍 Verifying m_2025_09_03: AI audit fields migration...")
        
        result = {
            "status": "unknown", 
            "elements": {},
            "functional_tests": {},
            "issues": []
        }
        
        try:
            with self.get_connection() as conn:
                # Check AI audit columns
                ai_columns = ["ai_score", "ai_sort_version", "ai_sort_explainer", "order_locked"]
                result["elements"]["ai_audit_columns"] = []
                
                for column in ai_columns:
                    exists = self.verify_column_exists(conn, "framework_epics", column)
                    result["elements"]["ai_audit_columns"].append(exists)
                
                # Check lock trigger
                result["elements"]["lock_trigger"] = self.verify_trigger_exists(
                    conn, "trg_epics_block_sort_update_when_locked"
                )
                
                # Functional tests - test order lock functionality
                if all(result["elements"]["ai_audit_columns"]) and result["elements"]["lock_trigger"]:
                    # Get an epic to test with
                    cursor = conn.execute("SELECT id FROM framework_epics LIMIT 1")
                    epic_row = cursor.fetchone()
                    
                    if epic_row:
                        epic_id = epic_row[0]
                        
                        # Test: lock epic and try to change sort_order (should fail)
                        test_setup = f"UPDATE framework_epics SET order_locked = 1 WHERE id = {epic_id}"
                        test_query = f"UPDATE framework_epics SET sort_order = 999 WHERE id = {epic_id}"
                        
                        # Setup the lock
                        conn.execute("BEGIN TRANSACTION")
                        conn.execute(test_setup)
                        
                        # Test if locked update fails
                        try:
                            conn.execute(test_query)
                            # If we got here, the trigger didn't work
                            result["functional_tests"]["prevents_locked_updates"] = False
                            conn.execute("ROLLBACK")
                        except sqlite3.Error:
                            # Expected failure - trigger is working
                            result["functional_tests"]["prevents_locked_updates"] = True
                            try:
                                conn.execute("ROLLBACK")
                            except:
                                pass  # Transaction may already be rolled back
                    else:
                        result["functional_tests"]["prevents_locked_updates"] = None
                        result["issues"].append("No epics available to test lock trigger")
                
                # Overall status
                all_columns = all(result["elements"]["ai_audit_columns"])
                trigger_exists = result["elements"]["lock_trigger"]
                all_functional = all(
                    v for v in result["functional_tests"].values() if v is not None
                ) if result["functional_tests"] else True
                
                if all_columns and trigger_exists and all_functional:
                    result["status"] = "completed"
                elif any(result["elements"]["ai_audit_columns"]) or trigger_exists:
                    result["status"] = "partial"
                    result["issues"].append("Migration partially applied")
                else:
                    result["status"] = "missing"
                    result["issues"].append("Migration not applied")
                    
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Error verifying migration: {str(e)}")
            logging.error(f"Error verifying m_2025_09_03: {e}")
        
        return result
    
    def verify_migration_04_topological_fields(self) -> Dict[str, Any]:
        """Verify m_2025_09_04: topological fields migration."""
        logging.info("🔍 Verifying m_2025_09_04: topological fields migration...")
        
        result = {
            "status": "unknown",
            "elements": {},
            "functional_tests": {},
            "issues": []
        }
        
        try:
            with self.get_connection() as conn:
                # Check topological fields
                topological_fields = ["effort_estimate", "tdd_phase", "tdd_order", "complexity_score"]
                result["elements"]["topological_fields"] = []
                
                for field in topological_fields:
                    exists = self.verify_column_exists(conn, "framework_epics", field)
                    result["elements"]["topological_fields"].append(exists)
                
                # Check topological indexes
                topological_indexes = [
                    "idx_epics_effort_complexity",
                    "idx_epics_tdd_workflow", 
                    "idx_epics_topological_sort"
                ]
                result["elements"]["topological_indexes"] = []
                
                for index in topological_indexes:
                    exists = self.verify_index_exists(conn, index)
                    result["elements"]["topological_indexes"].append(exists)
                
                # Functional tests - test constraints
                if all(result["elements"]["topological_fields"]):
                    # Test tdd_phase constraint (should fail with invalid value)
                    test_query = """
                        INSERT INTO framework_epics (project_id, epic_key, name, tdd_phase)
                        VALUES (999, 'TEST_CONSTRAINT', 'Test', 'invalid_phase')
                    """
                    result["functional_tests"]["tdd_phase_constraint"] = self.test_trigger_functionality(
                        conn, test_query, expected_failure=True
                    )
                    
                    # Test tdd_order constraint (should fail with invalid value)  
                    test_query = """
                        INSERT INTO framework_epics (project_id, epic_key, name, tdd_order)
                        VALUES (999, 'TEST_CONSTRAINT_2', 'Test', 99)
                    """
                    result["functional_tests"]["tdd_order_constraint"] = self.test_trigger_functionality(
                        conn, test_query, expected_failure=True
                    )
                
                # Overall status
                all_fields = all(result["elements"]["topological_fields"])
                all_indexes = all(result["elements"]["topological_indexes"])
                all_functional = all(
                    v for v in result["functional_tests"].values() if v is not None
                ) if result["functional_tests"] else True
                
                if all_fields and all_indexes and all_functional:
                    result["status"] = "completed"
                elif any(result["elements"]["topological_fields"]) or any(result["elements"]["topological_indexes"]):
                    result["status"] = "partial"
                    result["issues"].append("Migration partially applied")
                else:
                    result["status"] = "missing"
                    result["issues"].append("Migration not applied")
                    
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Error verifying migration: {str(e)}")
            logging.error(f"Error verifying m_2025_09_04: {e}")
        
        return result
    
    def execute_missing_migration(self, migration_name: str) -> bool:
        """Execute a missing migration by importing and running it."""
        try:
            # Map migration keys to actual file names
            migration_files = {
                "m_2025_09_01": "m_2025_09_01_add_sort_order_epics.py",
                "m_2025_09_02": "m_2025_09_02_create_epic_dependencies.py", 
                "m_2025_09_03": "m_2025_09_03_epics_order_lock_audit.py",
                "m_2025_09_04": "m_2025_09_04_complete_topological_fields.py"
            }
            
            migration_filename = migration_files.get(migration_name)
            if not migration_filename:
                logging.error(f"Unknown migration: {migration_name}")
                return False
                
            migration_path = project_root / "scripts" / "migration" / migration_filename
            if not migration_path.exists():
                logging.error(f"Migration file not found: {migration_path}")
                return False
            
            # Import migration module dynamically
            import importlib.util
            spec = importlib.util.spec_from_file_location("migration", migration_path)
            migration_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration_module)
            
            # Execute migration
            with self.get_connection() as conn:
                migration_module.up(conn)
                logging.info(f"✅ Successfully executed {migration_name}")
                return True
                
        except Exception as e:
            logging.error(f"❌ Failed to execute {migration_name}: {e}")
            return False
    
    def run_complete_verification(self, execute_missing: bool = False) -> Dict[str, Any]:
        """Run complete verification of all migrations."""
        logging.info("🚀 Starting complete epic migrations verification...")
        
        # Verify each migration
        self.results["migrations_status"]["m_2025_09_01"] = self.verify_migration_01_sort_order()
        self.results["migrations_status"]["m_2025_09_02"] = self.verify_migration_02_dependencies()
        self.results["migrations_status"]["m_2025_09_03"] = self.verify_migration_03_ai_audit()
        self.results["migrations_status"]["m_2025_09_04"] = self.verify_migration_04_topological_fields()
        
        # Execute missing migrations if requested
        if execute_missing:
            logging.info("🔧 Executing missing migrations...")
            
            for migration_key, migration_result in self.results["migrations_status"].items():
                if migration_result["status"] in ["missing", "partial"]:
                    logging.info(f"Executing missing migration: {migration_key}")
                    success = self.execute_missing_migration(migration_key)
                    
                    if success:
                        # Re-verify after execution
                        if migration_key == "m_2025_09_01":
                            self.results["migrations_status"][migration_key] = self.verify_migration_01_sort_order()
                        elif migration_key == "m_2025_09_02":
                            self.results["migrations_status"][migration_key] = self.verify_migration_02_dependencies()
                        elif migration_key == "m_2025_09_03":
                            self.results["migrations_status"][migration_key] = self.verify_migration_03_ai_audit()
                        elif migration_key == "m_2025_09_04":
                            self.results["migrations_status"][migration_key] = self.verify_migration_04_topological_fields()
        
        # Analyze overall results
        self._analyze_overall_status()
        
        return self.results
    
    def _analyze_overall_status(self):
        """Analyze overall status and generate recommendations."""
        completed_count = 0
        partial_count = 0
        missing_count = 0
        error_count = 0
        
        for migration_result in self.results["migrations_status"].values():
            status = migration_result["status"]
            if status == "completed":
                completed_count += 1
            elif status == "partial":
                partial_count += 1
            elif status == "missing":
                missing_count += 1
            elif status == "error":
                error_count += 1
            
            # Collect issues
            if migration_result.get("issues"):
                self.results["issues_found"].extend(migration_result["issues"])
        
        # Determine overall status
        if completed_count == 4:
            self.results["overall_status"] = "all_completed"
            self.results["ready_for_next_phase"] = True
            self.results["recommendations"].append("✅ All migrations completed successfully. Ready for next phase.")
        elif error_count > 0:
            self.results["overall_status"] = "has_errors"
            self.results["ready_for_next_phase"] = False
            self.results["recommendations"].append("❌ Migration errors detected. Fix errors before proceeding.")
        elif missing_count > 0 or partial_count > 0:
            self.results["overall_status"] = "incomplete"
            self.results["ready_for_next_phase"] = False
            self.results["recommendations"].append("⚠️ Some migrations incomplete. Execute missing migrations.")
            self.results["recommendations"].append("Run with --execute-missing flag to auto-fix.")
        
        # Add specific recommendations
        if partial_count > 0:
            self.results["recommendations"].append("🔧 Partial migrations detected - may need manual intervention.")
        
        if missing_count == 4:
            self.results["recommendations"].append("🆕 No migrations applied yet - this appears to be initial setup.")
    
    def print_detailed_report(self):
        """Print detailed verification report."""
        print("\n" + "="*80)
        print("🔍 EPIC MIGRATIONS VERIFICATION REPORT")
        print("="*80)
        print(f"📅 Verification Time: {self.results['verification_timestamp']}")
        print(f"🗄️ Database Path: {self.results['database_path']}")
        print(f"📊 Overall Status: {self.results['overall_status'].upper()}")
        print(f"✅ Ready for Next Phase: {self.results['ready_for_next_phase']}")
        
        print(f"\n📋 MIGRATION STATUS SUMMARY:")
        for migration_key, result in self.results["migrations_status"].items():
            status_emoji = {
                "completed": "✅",
                "partial": "⚠️", 
                "missing": "❌",
                "error": "💥",
                "unknown": "❓"
            }.get(result["status"], "❓")
            
            print(f"  {status_emoji} {migration_key}: {result['status'].upper()}")
        
        print(f"\n🔍 DETAILED ANALYSIS:")
        for migration_key, result in self.results["migrations_status"].items():
            print(f"\n--- {migration_key} ---")
            print(f"Status: {result['status']}")
            
            if result.get("elements"):
                print("Elements:")
                for element, status in result["elements"].items():
                    status_str = "✅" if status else "❌"
                    if isinstance(status, list):
                        all_good = all(status)
                        status_str = "✅" if all_good else f"⚠️ ({sum(status)}/{len(status)})"
                    print(f"  {status_str} {element}")
            
            if result.get("functional_tests"):
                print("Functional Tests:")
                for test, status in result["functional_tests"].items():
                    if status is None:
                        status_str = "⏭️"
                    else:
                        status_str = "✅" if status else "❌"
                    print(f"  {status_str} {test}")
            
            if result.get("issues"):
                print("Issues:")
                for issue in result["issues"]:
                    print(f"  ⚠️ {issue}")
        
        if self.results["issues_found"]:
            print(f"\n🚨 ISSUES FOUND:")
            for issue in self.results["issues_found"]:
                print(f"  • {issue}")
        
        if self.results["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in self.results["recommendations"]:
                print(f"  • {rec}")
        
        print("\n" + "="*80)


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify epic migrations status")
    parser.add_argument("--execute-missing", action="store_true", 
                       help="Execute missing migrations automatically")
    parser.add_argument("--detailed-report", action="store_true", default=True,
                       help="Print detailed verification report")
    parser.add_argument("--save-report", type=str, 
                       help="Save report to JSON file")
    parser.add_argument("--db-path", type=str, default="framework.db",
                       help="Path to database file")
    
    args = parser.parse_args()
    
    try:
        # Initialize verifier
        verifier = EpicMigrationsVerifier(db_path=args.db_path)
        
        # Run verification
        results = verifier.run_complete_verification(execute_missing=args.execute_missing)
        
        # Print report
        if args.detailed_report:
            verifier.print_detailed_report()
        
        # Save report if requested
        if args.save_report:
            with open(args.save_report, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Report saved to: {args.save_report}")
        
        # Exit with appropriate code
        if results["ready_for_next_phase"]:
            print(f"\n🎯 SUCCESS: All migrations verified. Ready to proceed to next phase!")
            sys.exit(0)
        else:
            print(f"\n⚠️ ATTENTION: Issues found. Address before proceeding.")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"💥 Fatal error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()