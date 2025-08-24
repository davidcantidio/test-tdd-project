#!/usr/bin/env python3
"""
Phase 1 Validation Script
Tests all fixed files and basic system functionality
"""

import sys
import os
import traceback

# Add project to path
project_path = '/home/david/Documentos/canimport/test-tdd-project'
sys.path.insert(0, project_path)

def test_file_import(module_path, description):
    """Test if a file can be imported without errors"""
    print(f"\n🧪 Testing {description}...")
    try:
        module = __import__(module_path, fromlist=[''])
        print(f"✅ {description}: Import successful")
        return True
    except Exception as e:
        print(f"❌ {description}: Import failed")
        print(f"   Error: {str(e)}")
        return False

def test_function_call(module_path, function_name, description):
    """Test if a specific function can be called"""
    print(f"\n🔧 Testing {description}...")
    try:
        module = __import__(module_path, fromlist=[function_name])
        func = getattr(module, function_name)
        result = func()
        print(f"✅ {description}: Success")
        if isinstance(result, dict):
            print(f"   Data: {len(result)} items")
        return True
    except Exception as e:
        print(f"❌ {description}: Function test failed")
        print(f"   Error: {str(e)}")
        return False

def main():
    print("🚀 Phase 1 Validation Starting...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 0
    
    # Test file imports
    import_tests = [
        ("streamlit_extension.pages.analytics", "Analytics page import"),
        ("streamlit_extension.pages.gantt", "Gantt page import"),
        ("streamlit_extension.pages.settings", "Settings page import"),
    ]
    
    for module_path, description in import_tests:
        total_tests += 1
        if test_file_import(module_path, description):
            success_count += 1
    
    # Test function calls
    function_tests = [
        ("streamlit_extension.pages.analytics", "get_analytics_data", "Analytics data function"),
        ("streamlit_extension.pages.gantt", "get_gantt_data", "Gantt data function"), 
        ("streamlit_extension.pages.settings", "render_settings_page", "Settings render function"),
    ]
    
    for module_path, func_name, description in function_tests:
        total_tests += 1
        if test_function_call(module_path, func_name, description):
            success_count += 1
    
    # Test legacy DatabaseManager still works
    print(f"\n🗄️ Testing legacy DatabaseManager...")
    try:
        from streamlit_extension.utils.database import DatabaseManager
        db_manager = DatabaseManager()
        epics = db_manager.get_epics()
        tasks = db_manager.get_tasks()
        print(f"✅ Legacy DatabaseManager: {len(epics)} epics, {len(tasks)} tasks")
        success_count += 1
        total_tests += 1
    except Exception as e:
        print(f"❌ Legacy DatabaseManager failed: {e}")
        total_tests += 1
    
    # Final results
    print("\n" + "=" * 50)
    print(f"🎯 PHASE 1 VALIDATION RESULTS")
    print(f"   Passed: {success_count}/{total_tests}")
    print(f"   Success Rate: {success_count/total_tests*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 PHASE 1: SUCCESS - All emergency fixes working")
        return True
    else:
        print("❌ PHASE 1: FAILED - Some issues remain")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)