#!/usr/bin/env python3
"""
🔍 Debug Script - UI Error Investigation
Simulates the main UI flow to identify specific failing components.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.resolve())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

def simulate_main_flow():
    """Simulate the main() function flow without Streamlit"""
    print("🎯 Simulating main() application flow...")
    
    try:
        # Import main components
        from streamlit_extension.streamlit_app import (
            initialize_session_state, fetch_user_stats, fetch_epics, 
            fetch_tasks, fetch_health, render_topbar, render_analytics_row,
            render_heatmap_and_tasks, render_timer_and_notifications
        )
        
        print("✅ Main components imported successfully")
        
        # Test 1: Session initialization
        print("\n1️⃣ Testing initialize_session_state...")
        try:
            initialize_session_state()
            print("    ✅ Session state initialized")
        except Exception as e:
            print(f"    ❌ Session state failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: Data fetching
        print("\n2️⃣ Testing data fetching...")
        try:
            stats = fetch_user_stats()
            print(f"    📊 User stats: {len(stats) if isinstance(stats, dict) else 'invalid'} keys")
            
            epics = fetch_epics()
            print(f"    📋 Epics: {len(epics) if hasattr(epics, '__len__') else 'invalid'} items")
            
            health = fetch_health()
            print(f"    🏥 Health: {health.get('overall', {}).get('status', 'unknown')}")
            
            if epics and hasattr(epics, '__len__') and len(epics) > 0:
                # Try to get first epic ID - handle both dict and list formats
                if isinstance(epics, list) and len(epics) > 0:
                    epic_id = epics[0].get('id', 1) if isinstance(epics[0], dict) else 1
                elif isinstance(epics, dict):
                    epic_id = 1  # fallback
                else:
                    epic_id = 1
                    
                tasks = fetch_tasks(epic_id)
                print(f"    📋 Tasks for epic {epic_id}: {len(tasks) if hasattr(tasks, '__len__') else 'invalid'} items")
            
        except Exception as e:
            print(f"    ❌ Data fetching failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 3: Component rendering (dry run)
        print("\n3️⃣ Testing component render functions...")
        
        mock_user = {"name": "TestUser", "email": "test@example.com"}
        
        try:
            print("    🎨 Testing render functions (import validation)...")
            print(f"    ✅ render_topbar: {callable(render_topbar)}")
            print(f"    ✅ render_analytics_row: {callable(render_analytics_row)}")
            print(f"    ✅ render_heatmap_and_tasks: {callable(render_heatmap_and_tasks)}")
            print(f"    ✅ render_timer_and_notifications: {callable(render_timer_and_notifications)}")
            
        except Exception as e:
            print(f"    ❌ Render function validation failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Main flow simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_error_patterns():
    """Check for common error patterns in the codebase"""
    print("\n🔍 Checking for common error patterns...")
    
    try:
        # Import exception handler to check error statistics
        from streamlit_extension.utils.exception_handler import get_error_statistics
        
        error_stats = get_error_statistics()
        print(f"📊 Error statistics: {error_stats}")
        
    except Exception as e:
        print(f"❌ Error statistics check failed: {e}")
    
    # Check for validation errors
    try:
        print("\n🔧 Testing common validation scenarios...")
        
        # Test form validation
        from streamlit_extension.utils.validation import validate_form
        
        # Test empty form data
        empty_data = {}
        valid, errors = validate_form(empty_data, required_fields=["name", "email"])
        print(f"    📝 Empty form validation: valid={valid}, errors={len(errors) if errors else 0}")
        
        # Test valid form data  
        valid_data = {"name": "Test", "email": "test@example.com"}
        valid, errors = validate_form(valid_data, required_fields=["name", "email"])
        print(f"    📝 Valid form validation: valid={valid}, errors={len(errors) if errors else 0}")
        
    except Exception as e:
        print(f"❌ Validation check failed: {e}")

def inspect_streamlit_errors():
    """Inspect specific Streamlit-related errors"""
    print("\n🎛️ Inspecting Streamlit-specific issues...")
    
    try:
        # Test session state access without Streamlit
        print("    📍 Testing session state patterns...")
        
        # This should fail gracefully
        try:
            import streamlit as st
            if hasattr(st, 'session_state'):
                print("    ✅ Streamlit session_state available")
            else:
                print("    ⚠️ Streamlit session_state not available")
        except Exception as e:
            print(f"    ❌ Streamlit import/access failed: {e}")
        
    except Exception as e:
        print(f"❌ Streamlit inspection failed: {e}")

def check_component_dependencies():
    """Check if all component dependencies are available"""
    print("\n🧩 Checking component dependencies...")
    
    components_to_test = [
        ("sidebar", "streamlit_extension.components.sidebar"),
        ("timer", "streamlit_extension.components.timer"), 
        ("dashboard_widgets", "streamlit_extension.components.dashboard_widgets"),
        ("form_components", "streamlit_extension.components.form_components"),
    ]
    
    for name, module_path in components_to_test:
        try:
            module = __import__(module_path, fromlist=[''])
            print(f"    ✅ {name}: Available")
            
            # Check specific classes/functions
            if name == "dashboard_widgets":
                classes = ["WelcomeHeader", "DailyStats", "ProductivityHeatmap", "ProgressRing"]
                for cls_name in classes:
                    if hasattr(module, cls_name):
                        print(f"        ✅ {cls_name}: Available")
                    else:
                        print(f"        ❌ {cls_name}: Missing")
                        
        except Exception as e:
            print(f"    ❌ {name}: Failed - {e}")

def main():
    print("🔍 DEBUG SESSION - UI Error Investigation")
    print("=" * 60)
    
    # Test 1: Main application flow
    main_ok = simulate_main_flow()
    
    # Test 2: Error patterns
    check_error_patterns()
    
    # Test 3: Streamlit-specific issues
    inspect_streamlit_errors()
    
    # Test 4: Component dependencies
    check_component_dependencies()
    
    print("\n" + "=" * 60)
    print("🎯 UI ERROR INVESTIGATION COMPLETE")
    
    if main_ok:
        print("✅ Main flow simulation passed - issue may be Streamlit-specific")
    else:
        print("❌ Main flow simulation failed - fundamental component issues")

if __name__ == "__main__":
    main()