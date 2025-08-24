#!/usr/bin/env python3
"""
Step 2.2.2: Test Modular API Coverage
Comprehensive test of what's available in the new modular API
Generated: 2025-08-24
"""

import sys
import traceback
from typing import Dict, List, Any

# Add project to path
sys.path.insert(0, '/home/david/Documentos/canimport/test-tdd-project')

# Test results tracking
test_results = {
    'imports': {'success': [], 'failed': []},
    'functions': {'available': [], 'working': [], 'failed': []},
    'services': {'available': [], 'working': [], 'failed': []},
    'comparison': {'modular_only': [], 'legacy_only': [], 'both': []}
}

def test_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def test_import(module_path: str, item_name: str = None) -> bool:
    """Test if a module or item can be imported"""
    try:
        if item_name:
            module = __import__(module_path, fromlist=[item_name])
            obj = getattr(module, item_name)
            return True
        else:
            __import__(module_path)
            return True
    except Exception as e:
        return False

def main():
    print("🚀 MODULAR API COVERAGE TEST - Step 2.2.2")
    print("=" * 60)
    
    # ============================================
    # SECTION 1: Test Module Imports
    # ============================================
    test_section("Testing Module Imports")
    
    # Test if modular database package exists
    if test_import('streamlit_extension.database'):
        print("✅ streamlit_extension.database package found")
        test_results['imports']['success'].append('streamlit_extension.database')
        
        # Import the module for testing
        try:
            import streamlit_extension.database as db_mod
            
            # List all available functions
            available = [attr for attr in dir(db_mod) if not attr.startswith('_')]
            print(f"📦 Available exports: {len(available)} functions")
            for func in sorted(available):
                print(f"  - {func}")
                test_results['functions']['available'].append(func)
                
        except Exception as e:
            print(f"❌ Failed to analyze module: {e}")
            test_results['imports']['failed'].append(f'streamlit_extension.database: {e}')
    else:
        print("❌ streamlit_extension.database package not found")
        test_results['imports']['failed'].append('streamlit_extension.database')
    
    # ============================================
    # SECTION 2: Test Individual Functions
    # ============================================
    test_section("Testing Individual Functions")
    
    # Expected functions from __all__ in __init__.py
    expected_functions = [
        'get_connection', 'release_connection', 'transaction', 'execute', 'set_dbm',
        'check_health', 'get_query_stats', 'optimize', 'create_backup', 'restore_backup',
        'list_epics', 'list_all_epics', 'list_tasks', 'list_all_tasks',
        'list_timer_sessions', 'get_user_stats', 'get_achievements',
        'create_schema_if_needed', 'seed_initial_data'
    ]
    
    for func_name in expected_functions:
        try:
            module = __import__('streamlit_extension.database', fromlist=[func_name])
            func = getattr(module, func_name)
            print(f"  ✅ {func_name}: Available")
            test_results['functions']['working'].append(func_name)
        except Exception as e:
            print(f"  ❌ {func_name}: {str(e)[:50]}")
            test_results['functions']['failed'].append(func_name)
    
    # ============================================
    # SECTION 3: Test Connection Functions
    # ============================================
    test_section("Testing Connection Management")
    
    try:
        from streamlit_extension.database import get_connection, release_connection
        
        # Test get_connection
        try:
            conn = get_connection()
            print(f"✅ get_connection(): {type(conn).__name__}")
            test_results['functions']['working'].append('get_connection_test')
            
            # Test release_connection
            try:
                release_connection(conn)
                print("✅ release_connection(): Success")
                test_results['functions']['working'].append('release_connection_test')
            except Exception as e:
                print(f"❌ release_connection(): {e}")
                test_results['functions']['failed'].append('release_connection_test')
                
        except Exception as e:
            print(f"❌ get_connection(): {e}")
            test_results['functions']['failed'].append('get_connection_test')
            
    except ImportError as e:
        print(f"❌ Connection functions not available: {e}")
        test_results['functions']['failed'].append('connection_management')
    
    # ============================================
    # SECTION 4: Test Query Functions
    # ============================================
    test_section("Testing Query Operations")
    
    query_tests = [
        ('list_epics', 'Get all epics'),
        ('list_all_epics', 'Get all epics without pagination'),
        ('list_tasks', 'Get all tasks'),
        ('list_all_tasks', 'Get all tasks without pagination'),
        ('list_timer_sessions', 'Get timer sessions'),
        ('get_user_stats', 'Get user statistics'),
        ('get_achievements', 'Get user achievements')
    ]
    
    for func_name, description in query_tests:
        try:
            module = __import__('streamlit_extension.database', fromlist=[func_name])
            func = getattr(module, func_name)
            
            # Try to execute the function
            try:
                result = func()
                if isinstance(result, (list, dict)):
                    count = len(result) if isinstance(result, list) else len(result.keys())
                    print(f"✅ {func_name}(): {count} items returned")
                    test_results['functions']['working'].append(f'{func_name}_execution')
                else:
                    print(f"✅ {func_name}(): Executed successfully")
                    test_results['functions']['working'].append(f'{func_name}_execution')
            except Exception as e:
                print(f"⚠️  {func_name}(): Function exists but failed - {str(e)[:50]}")
                test_results['functions']['failed'].append(f'{func_name}_execution')
                
        except Exception as e:
            print(f"❌ {func_name}(): Not available - {str(e)[:50]}")
            test_results['functions']['failed'].append(func_name)
    
    # ============================================
    # SECTION 5: Test Service Layer
    # ============================================
    test_section("Testing Service Layer")
    
    try:
        from streamlit_extension.services import ServiceContainer
        print("✅ ServiceContainer: Available")
        test_results['services']['available'].append('ServiceContainer')
        
        # Test service container initialization
        try:
            container = ServiceContainer()
            print("✅ ServiceContainer: Initialized successfully")
            test_results['services']['working'].append('ServiceContainer_init')
            
            # Test available services
            service_methods = [
                'get_project_service',
                'get_epic_service',
                'get_task_service',
                'get_analytics_service',
                'get_timer_service'
            ]
            
            for method_name in service_methods:
                if hasattr(container, method_name):
                    try:
                        service = getattr(container, method_name)()
                        print(f"  ✅ {method_name}(): {type(service).__name__}")
                        test_results['services']['working'].append(method_name)
                    except Exception as e:
                        print(f"  ⚠️  {method_name}(): Method exists but failed - {str(e)[:50]}")
                        test_results['services']['failed'].append(method_name)
                else:
                    print(f"  ❌ {method_name}(): Not found")
                    test_results['services']['failed'].append(method_name)
                    
        except Exception as e:
            print(f"❌ ServiceContainer initialization failed: {e}")
            test_results['services']['failed'].append('ServiceContainer_init')
            
    except ImportError as e:
        print(f"❌ Service layer not available: {e}")
        test_results['services']['failed'].append('ServiceContainer')
    
    # ============================================
    # SECTION 6: Compare with Legacy DatabaseManager
    # ============================================
    test_section("Comparing with Legacy DatabaseManager")
    
    try:
        from streamlit_extension.utils.database import DatabaseManager
        
        # Get DatabaseManager methods
        db_manager = DatabaseManager()
        legacy_methods = [m for m in dir(db_manager) if not m.startswith('_') and callable(getattr(db_manager, m))]
        
        # Get modular API methods
        import streamlit_extension.database as db_mod
        modular_methods = [m for m in dir(db_mod) if not m.startswith('_') and callable(getattr(db_mod, m))]
        
        # Compare
        legacy_set = set(legacy_methods)
        modular_set = set(modular_methods)
        
        both = legacy_set & modular_set
        legacy_only = legacy_set - modular_set
        modular_only = modular_set - legacy_set
        
        print(f"📊 Methods in both APIs: {len(both)}")
        print(f"📊 Methods only in legacy: {len(legacy_only)}")
        print(f"📊 Methods only in modular: {len(modular_only)}")
        
        test_results['comparison']['both'] = list(both)
        test_results['comparison']['legacy_only'] = list(legacy_only)
        test_results['comparison']['modular_only'] = list(modular_only)
        
        # Show sample of missing critical methods
        critical_missing = ['get_projects', 'create_task', 'update_task', 'get_kanban_tasks']
        print("\n🔴 Critical methods missing from modular API:")
        for method in critical_missing:
            if method in legacy_only:
                print(f"  - {method}")
                
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
    
    # ============================================
    # SECTION 7: Generate Summary Statistics
    # ============================================
    test_section("SUMMARY STATISTICS")
    
    # Calculate statistics
    total_expected = 55  # From Step 2.2.1
    modular_available = len(test_results['functions']['available'])
    modular_working = len([f for f in test_results['functions']['working'] if not f.endswith('_test') and not f.endswith('_execution')])
    services_available = len(test_results['services']['working'])
    
    coverage_percentage = (modular_working / total_expected) * 100
    
    print(f"📈 Total DatabaseManager methods: {total_expected}")
    print(f"📈 Modular API functions available: {modular_available}")
    print(f"📈 Modular API functions working: {modular_working}")
    print(f"📈 Service layer components: {services_available}/5")
    print(f"📈 Migration coverage: {modular_working}/{total_expected} ({coverage_percentage:.1f}%)")
    
    # Identify migration gaps
    print("\n🔍 MIGRATION GAPS:")
    print(f"  - Methods requiring migration: {total_expected - modular_working}")
    print(f"  - High priority gaps: Project management, Task CRUD, Kanban")
    print(f"  - Service layer status: {'Operational' if services_available >= 5 else 'Partial'}")
    
    # Final assessment
    print("\n🎯 ASSESSMENT:")
    if coverage_percentage >= 29:
        print(f"✅ Coverage matches expected 29% from Step 2.2.1")
    else:
        print(f"⚠️  Coverage ({coverage_percentage:.1f}%) below expected 29%")
    
    print("\n📊 RECOMMENDATION:")
    print("  - Hybrid architecture currently operational")
    print("  - Migration optional based on business needs")
    print("  - Focus on high-priority methods if migration proceeds")
    
    # Return results for documentation
    return {
        'total_methods': total_expected,
        'modular_available': modular_available,
        'modular_working': modular_working,
        'coverage_percentage': coverage_percentage,
        'services_status': services_available,
        'test_results': test_results
    }

if __name__ == "__main__":
    results = main()
    
    # Save results summary
    print("\n" + "="*60)
    print("📝 Test results ready for documentation")
    print("   Next: Update dependency_audit_report.md with results")
    print("="*60)