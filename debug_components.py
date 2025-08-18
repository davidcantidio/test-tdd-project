#!/usr/bin/env python3
"""
🔍 Debug Script - Component Loading Investigation
Tests individual Streamlit components to identify which are failing.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.resolve())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

def test_database_queries():
    """Test database query functions"""
    print("🗄️ Testing Database Queries...")
    try:
        # Import app functions that fetch data
        from streamlit_extension.streamlit_app import (
            fetch_user_stats, fetch_epics, fetch_tasks, fetch_health
        )
        
        print("  📊 Testing fetch_user_stats...")
        stats = fetch_user_stats()
        print(f"    ✅ User stats: {type(stats)} with {len(stats) if isinstance(stats, dict) else 'N/A'} keys")
        
        print("  📋 Testing fetch_epics...")
        epics = fetch_epics()
        print(f"    ✅ Epics: {type(epics)} with {len(epics) if isinstance(epics, list) else 'N/A'} items")
        
        print("  📋 Testing fetch_tasks...")
        if epics and len(epics) > 0:
            epic_id = epics[0].get('id', 1)
            tasks = fetch_tasks(epic_id)
            print(f"    ✅ Tasks for epic {epic_id}: {type(tasks)} with {len(tasks) if isinstance(tasks, list) else 'N/A'} items")
        else:
            print("    ⚠️ No epics available to test tasks")
            
        print("  🏥 Testing fetch_health...")
        health = fetch_health()
        print(f"    ✅ Health: {health}")
        
        return True
    except Exception as e:
        print(f"❌ Database queries failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_components_import():
    """Test component imports"""
    print("\n🧩 Testing Component Imports...")
    
    components = {
        "sidebar": "streamlit_extension.components.sidebar.render_sidebar",
        "timer": "streamlit_extension.components.timer.TimerComponent", 
        "dashboard_widgets": "streamlit_extension.components.dashboard_widgets",
    }
    
    for name, import_path in components.items():
        try:
            print(f"  📦 Testing {name}...")
            module_path, class_name = import_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            component = getattr(module, class_name)
            print(f"    ✅ {name}: {component}")
        except Exception as e:
            print(f"    ❌ {name} failed: {e}")

def test_dashboard_widgets():
    """Test dashboard widget functions"""
    print("\n📊 Testing Dashboard Widgets...")
    
    widgets = [
        "WelcomeHeader", "DailyStats", "ProductivityHeatmap",
        "ProgressRing", "SparklineChart", "AchievementCard",
        "NotificationToast", "QuickActionButton"
    ]
    
    try:
        from streamlit_extension.streamlit_app import (
            WelcomeHeader, DailyStats, ProductivityHeatmap,
            ProgressRing, SparklineChart, AchievementCard,
            NotificationToast, QuickActionButton
        )
        
        for widget_name in widgets:
            try:
                print(f"  🎨 Testing {widget_name}...")
                widget = locals()[widget_name]
                print(f"    ✅ {widget_name}: {widget}")
            except KeyError:
                print(f"    ❌ {widget_name}: Not available")
            except Exception as e:
                print(f"    ❌ {widget_name} failed: {e}")
        
    except Exception as e:
        print(f"❌ Dashboard widgets import failed: {e}")

def test_render_functions():
    """Test individual render functions"""
    print("\n🎨 Testing Render Functions...")
    
    # Mock user and data for testing
    mock_user = {"name": "TestUser", "email": "test@example.com"}
    mock_stats = {"daily_tasks": 5, "weekly_completion": 0.8}
    mock_epics = [{"id": 1, "name": "Test Epic"}]
    
    try:
        from streamlit_extension.streamlit_app import (
            render_topbar, render_analytics_row, render_heatmap_and_tasks, 
            render_timer_and_notifications
        )
        
        print("  🎯 Testing render functions (import only)...")
        print(f"    ✅ render_topbar: {render_topbar}")
        print(f"    ✅ render_analytics_row: {render_analytics_row}")
        print(f"    ✅ render_heatmap_and_tasks: {render_heatmap_and_tasks}")
        print(f"    ✅ render_timer_and_notifications: {render_timer_and_notifications}")
        
    except Exception as e:
        print(f"❌ Render functions failed: {e}")
        import traceback
        traceback.print_exc()

def test_exception_handler():
    """Test exception handler functionality"""
    print("\n🛡️ Testing Exception Handler...")
    
    try:
        from streamlit_extension.streamlit_app import (
            streamlit_error_boundary, safe_streamlit_operation
        )
        
        print("  🔧 Testing streamlit_error_boundary...")
        with streamlit_error_boundary("test_operation"):
            print("    ✅ Error boundary context manager working")
            
        print("  🔧 Testing safe_streamlit_operation...")
        def test_func():
            return "test_result"
            
        result = safe_streamlit_operation(test_func, default_return="default")
        print(f"    ✅ Safe operation result: {result}")
        
    except Exception as e:
        print(f"❌ Exception handler failed: {e}")
        import traceback
        traceback.print_exc()

def test_app_setup():
    """Test app setup initialization"""
    print("\n🚀 Testing App Setup...")
    
    try:
        from streamlit_extension.streamlit_app import initialize_session_state
        
        print("  ⚙️ Testing initialize_session_state...")
        initialize_session_state()  # This should work without Streamlit
        print("    ✅ Session state initialization completed (no Streamlit)")
        
    except Exception as e:
        print(f"❌ App setup failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🔍 DEBUG SESSION - Component Loading Investigation")
    print("=" * 70)
    
    # Test 1: Database queries
    queries_ok = test_database_queries()
    
    # Test 2: Component imports
    test_components_import()
    
    # Test 3: Dashboard widgets
    test_dashboard_widgets()
    
    # Test 4: Render functions
    test_render_functions()
    
    # Test 5: Exception handler
    test_exception_handler()
    
    # Test 6: App setup
    test_app_setup()
    
    print("\n" + "=" * 70)
    print("🎯 COMPONENT DEBUG SESSION COMPLETE")

if __name__ == "__main__":
    main()