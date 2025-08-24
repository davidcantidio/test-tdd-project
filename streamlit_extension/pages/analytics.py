"""
📊 Analytics Page

HYBRID DATABASE STRATEGY:
- Use list_epics() from modular API (works)
- Use DatabaseManager for get_tasks() and complex ops (safe)
- Provide error handling and fallbacks
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Union
import logging
import streamlit as st

# HYBRID IMPORTS: Use best API for each operation
try:
    from streamlit_extension.database import list_epics  # Modular - confirmed working
except ImportError:
    list_epics = None  # Fallback handling

from streamlit_extension.utils.database import DatabaseManager  # Legacy - always works

def get_analytics_data() -> Dict[str, Any]:
    """Get analytics data using hybrid database approach"""
    db_manager = DatabaseManager()
    
    try:
        # Use modular API for operations that work
        if list_epics:
            epics = list_epics()
        else:
            # Fallback to legacy
            epics = db_manager.get_epics()
            
        # Use legacy for operations that don't work in modular API
        tasks = db_manager.get_tasks()  # SAFE: No epic_id required in legacy
        
        # Use legacy for complex analytics operations
        analytics = {}
        if hasattr(db_manager, 'get_analytics'):
            analytics = db_manager.get_analytics()
            
        user_stats = {}
        if hasattr(db_manager, 'get_user_stats'):
            user_stats = db_manager.get_user_stats()
            
        return {
            'epics': epics,
            'tasks': tasks,  
            'analytics': analytics,
            'user_stats': user_stats,
            'total_epics': len(epics),
            'total_tasks': len(tasks)
        }
        
    except Exception as e:
        logging.error(f"Analytics data error: {e}")
        # Full fallback to legacy
        return {
            'epics': db_manager.get_epics(),
            'tasks': db_manager.get_tasks(),
            'analytics': {},
            'user_stats': {},
            'total_epics': 0,
            'total_tasks': 0,
            'error': str(e)
        }

def render_analytics_page():
    """Render analytics page with hybrid database access"""
    st.title("📊 Analytics Dashboard")
    
    try:
        data = get_analytics_data()
        
        if 'error' in data:
            st.warning(f"Analytics running in fallback mode: {data['error']}")
        
        # Display metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Epics", data['total_epics'])
            if data['epics']:
                st.subheader("Recent Epics")
                for epic in data['epics'][:5]:  # Show first 5
                    epic_title = epic.get('title', epic.get('name', 'Unknown'))
                    st.write(f"• {epic_title}")
        
        with col2:
            st.metric("Total Tasks", data['total_tasks'])  
            if data['tasks']:
                st.subheader("Recent Tasks")
                for task in data['tasks'][:5]:  # Show first 5  
                    task_title = task.get('title', task.get('name', 'Unknown'))
                    st.write(f"• {task_title}")
        
        # Additional analytics if available
        if data['analytics']:
            st.subheader("📈 Analytics")
            st.json(data['analytics'])
            
        if data['user_stats']:
            st.subheader("👤 User Statistics")
            st.json(data['user_stats'])
            
    except Exception as e:
        st.error(f"Failed to load analytics: {str(e)}")
        st.info("Please check database connection and try again.")

if __name__ == "__main__":
    render_analytics_page()