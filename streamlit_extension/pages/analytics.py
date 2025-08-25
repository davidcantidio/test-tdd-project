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

# Migrated to modular database API
from streamlit_extension.database import queries

def get_analytics_data() -> Dict[str, Any]:
    """Get analytics data using modular database API."""
    
    try:
        # Use modular queries for all data operations
        epics = queries.list_epics()
        tasks = queries.list_all_tasks()
        
        # Get user statistics using optimized query
        user_stats = queries.get_user_stats_optimized(user_id=1)
        
        # Calculate analytics from the retrieved data
        analytics = {
            'total_epics': len(epics),
            'total_tasks': len(tasks),
            'completed_tasks': len([t for t in tasks if t.get('status') == 'completed']),
            'active_tasks': len([t for t in tasks if t.get('status') == 'active']),
            'epics_by_status': {},
            'tasks_by_tdd_phase': {}
        }
        
        # Calculate epics by status
        for epic in epics:
            status = epic.get('status', 'unknown')
            analytics['epics_by_status'][status] = analytics['epics_by_status'].get(status, 0) + 1
        
        # Calculate tasks by TDD phase
        for task in tasks:
            phase = task.get('tdd_phase', 'unknown')
            analytics['tasks_by_tdd_phase'][phase] = analytics['tasks_by_tdd_phase'].get(phase, 0) + 1
        
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
        return {
            'epics': [],
            'tasks': [],
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