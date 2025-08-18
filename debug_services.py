#!/usr/bin/env python3
"""
🔍 Debug Script - Service Container Investigation
Analyzes why services are registered but not created.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.resolve())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

def test_database_connection():
    """Test database layer connectivity"""
    print("🗄️ Testing Database Connection...")
    try:
        from streamlit_extension.database import get_connection, check_health
        conn = get_connection()
        if conn:
            print("✅ Database connection OK")
            try:
                conn.close()
            except:
                pass
        
        health = check_health()
        print(f"✅ Database health: {health}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_manager():
    """Test legacy DatabaseManager"""
    print("\n🏢 Testing DatabaseManager (Legacy)...")
    try:
        from streamlit_extension.utils.database import DatabaseManager
        dbm = DatabaseManager()
        print("✅ DatabaseManager created successfully")
        
        # Test basic functionality
        epics = dbm.get_epics()
        print(f"✅ DatabaseManager.get_epics() returned {len(epics)} items")
        return dbm
    except Exception as e:
        print(f"❌ DatabaseManager failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_service_container_creation(dbm):
    """Test Service Container initialization"""
    print("\n🏗️ Testing Service Container Creation...")
    try:
        from streamlit_extension.services.service_container import ServiceContainer
        
        # Test with legacy API
        container = ServiceContainer(db_manager=dbm, use_modular_api=False)
        container.initialize(lazy_loading=True)
        print("✅ ServiceContainer created with legacy API")
        
        status = container.get_service_status()
        print(f"📊 Container status: {status}")
        
        return container
    except Exception as e:
        print(f"❌ ServiceContainer creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_service_container_modular():
    """Test Service Container with modular API"""
    print("\n🏗️ Testing Service Container (Modular API)...")
    try:
        from streamlit_extension.services.service_container import ServiceContainer
        
        # Test with modular API  
        container = ServiceContainer(use_modular_api=True)
        container.initialize(lazy_loading=True)
        print("✅ ServiceContainer created with modular API")
        
        status = container.get_service_status()
        print(f"📊 Container status: {status}")
        
        return container
    except Exception as e:
        print(f"❌ ServiceContainer (modular) creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_service_instantiation(container):
    """Test actual service instantiation"""
    print("\n⚙️ Testing Service Instantiation...")
    
    services = ["client", "project", "epic", "task", "analytics", "timer"]
    for service_name in services:
        try:
            print(f"  📦 Testing {service_name} service...")
            if service_name == "client":
                service = container.get_client_service()
            elif service_name == "project":
                service = container.get_project_service()
            elif service_name == "epic":
                service = container.get_epic_service()
            elif service_name == "task":
                service = container.get_task_service()
            elif service_name == "analytics":
                service = container.get_analytics_service()
            elif service_name == "timer":
                service = container.get_timer_service()
            
            print(f"    ✅ {service_name} service created: {type(service).__name__}")
        except Exception as e:
            print(f"    ❌ {service_name} service failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Check final status
    final_status = container.get_service_status()
    print(f"\n📊 Final container status: {final_status}")

def test_app_setup():
    """Test the app_setup module functionality"""
    print("\n🚀 Testing App Setup Module...")
    try:
        from streamlit_extension.utils.app_setup import (
            get_database_manager, get_app_service_container, 
            check_services_health
        )
        
        print("  📦 Testing get_database_manager...")
        dbm = get_database_manager()
        print(f"    {'✅' if dbm else '❌'} DatabaseManager: {dbm}")
        
        print("  📦 Testing get_app_service_container...")  
        container = get_app_service_container()
        print(f"    {'✅' if container else '❌'} ServiceContainer: {container}")
        
        if container:
            status = container.get_service_status()
            print(f"    📊 Container status: {status}")
        
        print("  📦 Testing check_services_health...")
        health = check_services_health()
        print(f"    📊 Health report: {health}")
        
    except Exception as e:
        print(f"❌ App setup failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🔍 DEBUG SESSION - Service Container Investigation")
    print("=" * 60)
    
    # Test 1: Database connectivity
    db_ok = test_database_connection()
    
    # Test 2: DatabaseManager (legacy)
    dbm = test_database_manager() if db_ok else None
    
    # Test 3: Service Container with legacy API
    container_legacy = test_service_container_creation(dbm) if dbm else None
    
    # Test 4: Service Container with modular API
    container_modular = test_service_container_modular() if db_ok else None
    
    # Test 5: Service instantiation
    if container_legacy:
        print("\n🧪 Testing with LEGACY API container:")
        test_service_instantiation(container_legacy)
        
    if container_modular:
        print("\n🧪 Testing with MODULAR API container:")
        test_service_instantiation(container_modular)
    
    # Test 6: App setup module
    test_app_setup()
    
    print("\n" + "=" * 60)
    print("🎯 DEBUG SESSION COMPLETE")

if __name__ == "__main__":
    main()