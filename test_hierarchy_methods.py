#!/usr/bin/env python3
"""
🧪 Test Script for Hierarchy Methods - Schema v6
Tests the new Client → Project → Epic → Task hierarchy functionality

Features:
- Tests DatabaseManager hierarchy methods
- Validates data integrity
- Performance testing
- Creates sample data for demonstration
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import sqlite3
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import the DatabaseManager
try:
    from streamlit_extension.utils.database import DatabaseManager
    from streamlit_extension.config import load_config
    DATABASE_UTILS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Could not import database utilities: {e}")
    DATABASE_UTILS_AVAILABLE = False

def test_basic_connectivity():
    """Test basic database connectivity."""
    print("🔌 Testing basic database connectivity...")
    
    try:
        config = load_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
        
        health = db_manager.check_database_health()
        
        if health["framework_db_connected"]:
            print("✅ Framework database connected")
        else:
            print("❌ Framework database connection failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database connectivity test failed: {e}")
        return False

def test_hierarchy_methods():
    """Test the new hierarchy methods."""
    print("🏗️  Testing hierarchy methods...")
    
    try:
        config = load_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
        
        # Test 1: Get clients
        print("📊 Testing get_clients()...")
        clients = db_manager.get_clients()
        print(f"   Found {len(clients)} clients")
        
        if clients:
            client = clients[0]
            print(f"   First client: {client['name']} ({client['client_key']})")
        
        # Test 2: Get projects
        print("📁 Testing get_projects()...")
        projects = db_manager.get_projects()
        print(f"   Found {len(projects)} projects")
        
        if projects:
            project = projects[0]
            print(f"   First project: {project['name']} ({project['project_key']})")
            print(f"   Client: {project['client_name']}")
        
        # Test 3: Get epics with hierarchy
        print("📋 Testing get_epics_with_hierarchy()...")
        epics = db_manager.get_epics_with_hierarchy()
        print(f"   Found {len(epics)} epics with hierarchy")
        
        if epics:
            epic = epics[0]
            print(f"   First epic: {epic['name']} ({epic['epic_key']})")
            print(f"   Project: {epic.get('project_name', 'None')}")
            print(f"   Client: {epic.get('client_name', 'None')}")
        
        # Test 4: Get hierarchy overview
        print("🌐 Testing get_hierarchy_overview()...")
        overview = db_manager.get_hierarchy_overview()
        print(f"   Found {len(overview)} hierarchy records")
        
        if overview:
            record = overview[0]
            print(f"   Sample record: {record['client_name']} → {record['project_name']} → {record['epic_name']}")
            print(f"   Tasks: {record['completed_tasks']}/{record['total_tasks']} completed")
        
        # Test 5: Client dashboard
        print("📈 Testing get_client_dashboard()...")
        client_dashboard = db_manager.get_client_dashboard()
        print(f"   Found {len(client_dashboard)} client dashboard records")
        
        if client_dashboard:
            dashboard = client_dashboard[0]
            print(f"   Client: {dashboard['client_name']}")
            print(f"   Projects: {dashboard['total_projects']} total, {dashboard['active_projects']} active")
            print(f"   Tasks: {dashboard['completed_tasks']}/{dashboard['total_tasks']} completed")
        
        # Test 6: Project dashboard
        print("📊 Testing get_project_dashboard()...")
        project_dashboard = db_manager.get_project_dashboard()
        print(f"   Found {len(project_dashboard)} project dashboard records")
        
        if project_dashboard:
            dashboard = project_dashboard[0]
            print(f"   Project: {dashboard['project_name']} ({dashboard['client_name']})")
            print(f"   Completion: {dashboard['calculated_completion_percentage']}%")
            print(f"   Epics: {dashboard['completed_epics']}/{dashboard['total_epics']} completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Hierarchy methods test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_create_sample_client():
    """Test creating a sample client."""
    print("👤 Testing client creation...")
    
    try:
        config = load_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
        
        # Check if sample client already exists
        existing_client = db_manager.get_client_by_key("sample_corp")
        if existing_client:
            print("   Sample client already exists, skipping creation")
            return existing_client['id']
        
        # Create sample client
        client_id = db_manager.create_client(
            client_key="sample_corp",
            name="Sample Corporation",
            description="Sample client for testing hierarchy functionality",
            industry="Technology",
            company_size="enterprise",
            primary_contact_name="John Doe",
            primary_contact_email="john.doe@sample.com",
            hourly_rate=175.00,
            client_tier="premium",
            priority_level=8
        )
        
        if client_id:
            print(f"✅ Created sample client with ID: {client_id}")
            return client_id
        else:
            print("❌ Failed to create sample client")
            return None
            
    except Exception as e:
        print(f"❌ Client creation test failed: {e}")
        return None

def test_create_sample_project(client_id):
    """Test creating a sample project."""
    print("📁 Testing project creation...")
    
    try:
        config = load_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
        
        # Check if sample project already exists
        existing_project = db_manager.get_project_by_key(client_id, "web_platform")
        if existing_project:
            print("   Sample project already exists, skipping creation")
            return existing_project['id']
        
        # Create sample project
        project_id = db_manager.create_project(
            client_id=client_id,
            project_key="web_platform",
            name="Web Platform Development",
            description="Complete web platform development with modern stack",
            project_type="development",
            methodology="agile",
            status="active",
            priority=9,
            health_status="green",
            planned_start_date="2025-09-01",
            planned_end_date="2025-12-31",
            estimated_hours=500,
            budget_amount=87500.00,
            hourly_rate=175.00,
            repository_url="https://github.com/sample-corp/web-platform"
        )
        
        if project_id:
            print(f"✅ Created sample project with ID: {project_id}")
            return project_id
        else:
            print("❌ Failed to create sample project")
            return None
            
    except Exception as e:
        print(f"❌ Project creation test failed: {e}")
        return None

def test_performance_queries():
    """Test performance of hierarchy queries."""
    print("⚡ Testing query performance...")
    
    try:
        config = load_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
        
        import time
        
        # Test hierarchy overview performance
        start_time = time.time()
        overview = db_manager.get_hierarchy_overview()
        overview_time = (time.time() - start_time) * 1000
        
        # Test client dashboard performance
        start_time = time.time()
        client_dashboard = db_manager.get_client_dashboard()
        client_time = (time.time() - start_time) * 1000
        
        # Test project dashboard performance
        start_time = time.time()
        project_dashboard = db_manager.get_project_dashboard()
        project_time = (time.time() - start_time) * 1000
        
        # Test epics with hierarchy performance
        start_time = time.time()
        epics = db_manager.get_epics_with_hierarchy()
        epics_time = (time.time() - start_time) * 1000
        
        print(f"   📊 Hierarchy overview: {overview_time:.2f}ms ({len(overview)} records)")
        print(f"   👤 Client dashboard: {client_time:.2f}ms ({len(client_dashboard)} records)")
        print(f"   📁 Project dashboard: {project_time:.2f}ms ({len(project_dashboard)} records)")
        print(f"   📋 Epics with hierarchy: {epics_time:.2f}ms ({len(epics)} records)")
        
        # Check performance targets (should be < 100ms each)
        performance_ok = all([
            overview_time < 100,
            client_time < 100,
            project_time < 100,
            epics_time < 100
        ])
        
        if performance_ok:
            print("✅ All queries meet performance targets (< 100ms)")
        else:
            print("⚠️  Some queries exceed performance targets")
        
        return performance_ok
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def test_data_integrity():
    """Test data integrity after hierarchy implementation."""
    print("🔍 Testing data integrity...")
    
    try:
        config = load_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
        
        # Test 1: All epics should have a project_id
        epics = db_manager.get_epics()
        epics_without_project = [e for e in epics if not e.get('project_id')]
        
        if epics_without_project:
            print(f"❌ Found {len(epics_without_project)} epics without project_id")
            return False
        else:
            print(f"✅ All {len(epics)} epics have project_id")
        
        # Test 2: All projects should have a client_id  
        projects = db_manager.get_projects()
        projects_without_client = [p for p in projects if not p.get('client_id')]
        
        if projects_without_client:
            print(f"❌ Found {len(projects_without_client)} projects without client_id")
            return False
        else:
            print(f"✅ All {len(projects)} projects have client_id")
        
        # Test 3: Hierarchy should be complete (no orphaned records)
        hierarchy = db_manager.get_hierarchy_overview()
        hierarchy_with_nulls = [h for h in hierarchy if not all([
            h.get('client_id'), h.get('project_id'), h.get('epic_id')
        ])]
        
        if hierarchy_with_nulls:
            print(f"❌ Found {len(hierarchy_with_nulls)} incomplete hierarchy records")
            return False
        else:
            print(f"✅ All {len(hierarchy)} hierarchy records are complete")
        
        # Test 4: Task counts should be consistent
        total_tasks_from_hierarchy = sum(h.get('total_tasks', 0) for h in hierarchy)
        all_tasks = db_manager.get_tasks()
        actual_task_count = len(all_tasks)
        
        if total_tasks_from_hierarchy != actual_task_count:
            print(f"❌ Task count mismatch: hierarchy({total_tasks_from_hierarchy}) vs actual({actual_task_count})")
            return False
        else:
            print(f"✅ Task counts consistent: {actual_task_count} tasks")
        
        return True
        
    except Exception as e:
        print(f"❌ Data integrity test failed: {e}")
        return False


def test_foreign_key_constraints():
    """Validate foreign key enforcement for hierarchy tables."""
    print("🛡️ Testing foreign key constraints...")

    try:
        config = load_config()

        # Work on a temporary copy of the database to avoid altering production data
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            shutil.copy2(config.get_database_path(), tmp.name)
            conn = sqlite3.connect(tmp.name)
            conn.execute("PRAGMA foreign_keys = ON")
            cur = conn.cursor()

            # Invalid project_id for epic
            try:
                cur.execute(
                    "INSERT INTO framework_epics (epic_key, name, description, project_id) VALUES (?, ?, ?, ?)",
                    ("fk_test_epic", "FK Test Epic", "Should fail", 99999)
                )
                conn.commit()
                print("   ❌ Epic insert with invalid project_id succeeded")
                return False
            except sqlite3.IntegrityError:
                print("   ✅ Epic insert with invalid project_id failed")

            # Invalid client_id for project
            try:
                cur.execute(
                    "INSERT INTO framework_projects (client_id, project_key, name) VALUES (?, ?, ?)",
                    (99999, "fk_test_project", "FK Test Project")
                )
                conn.commit()
                print("   ❌ Project insert with invalid client_id succeeded")
                return False
            except sqlite3.IntegrityError:
                print("   ✅ Project insert with invalid client_id failed")

            # Invalid epic_id for task
            try:
                cur.execute(
                    "INSERT INTO framework_tasks (task_key, epic_id, title, tdd_phase) VALUES (?, ?, ?, 'analysis')",
                    ("fk_test_task", 99999, "FK Test Task")
                )
                conn.commit()
                print("   ❌ Task insert with invalid epic_id succeeded")
                return False
            except sqlite3.IntegrityError:
                print("   ✅ Task insert with invalid epic_id failed")

            # Cascade delete: deleting project removes epics
            cur.execute("INSERT INTO framework_clients (client_key, name) VALUES (?, ?)", ("fk_temp_client", "FK Temp Client"))
            client_id = cur.lastrowid
            cur.execute(
                "INSERT INTO framework_projects (client_id, project_key, name) VALUES (?, ?, ?)",
                (client_id, "fk_temp_project", "FK Temp Project")
            )
            project_id = cur.lastrowid
            cur.execute(
                "INSERT INTO framework_epics (epic_key, name, project_id) VALUES (?, ?, ?)",
                ("fk_temp_epic", "FK Temp Epic", project_id)
            )
            conn.commit()

            cur.execute("DELETE FROM framework_projects WHERE id = ?", (project_id,))
            conn.commit()

            cur.execute("SELECT id FROM framework_epics WHERE epic_key = 'fk_temp_epic'")
            if cur.fetchone() is None:
                print("   ✅ Cascade delete enforced (project → epics)")
            else:
                print("   ❌ Cascade delete failed")
                return False

            conn.close()

        return True

    except Exception as e:
        print(f"❌ Foreign key constraint test failed: {e}")
        return False

def print_hierarchy_summary():
    """Print a summary of the current hierarchy."""
    print("📋 Current Hierarchy Summary")
    print("=" * 50)
    
    try:
        config = load_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
        
        # Get clients
        clients = db_manager.get_clients()
        print(f"👤 Clients: {len(clients)}")
        
        for client in clients:
            print(f"   • {client['name']} ({client['client_key']}) - {client['status']}")
            
            # Get projects for this client
            projects = db_manager.get_projects(client_id=client['id'])
            print(f"     📁 Projects: {len(projects)}")
            
            for project in projects:
                print(f"       • {project['name']} ({project['project_key']}) - {project['status']}")
                
                # Get epics for this project
                epics = db_manager.get_epics_with_hierarchy(project_id=project['id'])
                print(f"         📋 Epics: {len(epics)}")
                
                for epic in epics[:3]:  # Show first 3 epics
                    tasks = db_manager.get_tasks(epic_id=epic['id'])
                    completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
                    print(f"           • {epic['name']} ({epic['epic_key']}) - {completed_tasks}/{len(tasks)} tasks")
                
                if len(epics) > 3:
                    print(f"           ... and {len(epics) - 3} more epics")
        
        print("=" * 50)
        
        # Summary statistics
        dashboard = db_manager.get_client_dashboard()
        if dashboard:
            client_stats = dashboard[0]
            print(f"📊 Total Statistics:")
            print(f"   Projects: {client_stats['total_projects']} ({client_stats['active_projects']} active)")
            print(f"   Epics: {client_stats['total_epics']} ({client_stats['active_epics']} active)")
            print(f"   Tasks: {client_stats['completed_tasks']}/{client_stats['total_tasks']} completed")
            print(f"   Budget: R$ {client_stats['total_budget']:,.2f}")
            print(f"   Hours: {client_stats['total_hours_logged']:.1f}h logged")
        
    except Exception as e:
        print(f"❌ Could not generate hierarchy summary: {e}")

def main():
    """Main test function."""
    print("🧪 Testing Hierarchy Implementation - Schema v6")
    print("=" * 60)
    
    if not DATABASE_UTILS_AVAILABLE:
        print("❌ Database utilities not available")
        return False
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Basic connectivity
    total_tests += 1
    if test_basic_connectivity():
        tests_passed += 1
    print()
    
    # Test 2: Hierarchy methods
    total_tests += 1
    if test_hierarchy_methods():
        tests_passed += 1
    print()
    
    # Test 3: Create sample client
    total_tests += 1
    client_id = test_create_sample_client()
    if client_id:
        tests_passed += 1
    print()
    
    # Test 4: Create sample project (only if client creation succeeded)
    if client_id:
        total_tests += 1
        project_id = test_create_sample_project(client_id)
        if project_id:
            tests_passed += 1
        print()
    
    # Test 5: Performance testing
    total_tests += 1
    if test_performance_queries():
        tests_passed += 1
    print()
    
    # Test 6: Foreign key constraints
    total_tests += 1
    if test_foreign_key_constraints():
        tests_passed += 1
    print()

    # Test 7: Data integrity
    total_tests += 1
    if test_data_integrity():
        tests_passed += 1
    print()

    # Print hierarchy summary
    print_hierarchy_summary()
    print()

    # Final results
    print("🎯 Test Results")
    print("=" * 60)
    print(f"✅ Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Hierarchy implementation is working correctly.")
        print()
        print("✅ Ready for Streamlit interface updates")
        print("✅ Performance targets met")
        print("✅ Data integrity validated")
        return True
    else:
        print(f"❌ {total_tests - tests_passed} tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)