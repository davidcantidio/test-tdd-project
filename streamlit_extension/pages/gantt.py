"""
📅 Gantt Chart Page

SAFE LEGACY DATABASE ACCESS:
- Uses proven DatabaseManager for all operations
- No experimental modular API usage
- Guaranteed compatibility
"""

from __future__ import annotations  
from typing import Dict, Any, List, Optional
import logging
import streamlit as st

# SAFE IMPORT: Use only proven legacy API
from streamlit_extension.utils.database import DatabaseManager

def get_gantt_data() -> Dict[str, Any]:
    """Get Gantt data using safe legacy database access"""
    db_manager = DatabaseManager()
    
    try:
        epics = db_manager.get_epics()
        tasks = db_manager.get_tasks()
        
        return {
            'epics': epics,
            'tasks': tasks,
            'success': True
        }
        
    except Exception as e:
        logging.error(f"Gantt data error: {e}")
        return {
            'epics': [],
            'tasks': [], 
            'success': False,
            'error': str(e)
        }

def render_gantt_page():
    """Render Gantt chart page with safe database access"""
    st.title("📅 Gantt Chart")
    
    data = get_gantt_data()
    
    if not data['success']:
        st.error(f"Failed to load Gantt data: {data.get('error', 'Unknown error')}")
        return
    
    st.info(f"Loaded {len(data['epics'])} epics and {len(data['tasks'])} tasks")
    
    # Display epics in a simple timeline format
    if data['epics']:
        st.subheader("📋 Epics Timeline")
        for epic in data['epics']:
            epic_title = epic.get('title', epic.get('name', 'Unknown Epic'))
            epic_status = epic.get('status', 'Unknown')
            st.write(f"**{epic_title}** - Status: {epic_status}")
    
    # Display tasks grouped by epic
    if data['tasks']:
        st.subheader("📝 Tasks Overview") 
        task_count_by_status = {}
        for task in data['tasks']:
            status = task.get('status', 'Unknown')
            task_count_by_status[status] = task_count_by_status.get(status, 0) + 1
        
        for status, count in task_count_by_status.items():
            st.metric(f"Tasks - {status}", count)

if __name__ == "__main__":
    render_gantt_page()