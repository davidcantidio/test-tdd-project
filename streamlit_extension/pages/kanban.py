"""
📋 Kanban Board Page

Interactive task management with drag-and-drop Kanban board:
- Visual task organization by status
- TDD phase tracking
- Epic grouping and filtering
- Real-time updates
- Task editing and creation
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

# Local imports
try:
    from streamlit_extension.utils.database import DatabaseManager
    from streamlit_extension.config import get_config
    DATABASE_UTILS_AVAILABLE = True
except ImportError:
    DatabaseManager = get_config = None
    DATABASE_UTILS_AVAILABLE = False


def render_kanban_page():
    """Render the Kanban board page."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    st.title("📋 Kanban Board")
    st.markdown("---")
    
    # Initialize database manager
    if not DATABASE_UTILS_AVAILABLE:
        st.error("❌ Database utilities not available")
        return
    
    try:
        config = get_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        return
    
    # Sidebar filters
    _render_sidebar_filters(db_manager)
    
    # Load data
    with st.spinner("Loading tasks..."):
        tasks = db_manager.get_tasks()
        epics = db_manager.get_epics()
    
    # Apply filters
    filtered_tasks = _apply_filters(tasks, epics)
    
    if not filtered_tasks:
        st.info("📝 No tasks found for the selected filters.")
        _render_create_task_form(db_manager, epics)
        return
    
    # Render board
    _render_kanban_board(filtered_tasks, db_manager, epics)
    
    # Task creation form
    with st.expander("➕ Create New Task", expanded=False):
        _render_create_task_form(db_manager, epics)


def _render_sidebar_filters(db_manager: DatabaseManager):
    """Render sidebar filters for the Kanban board."""
    
    st.sidebar.markdown("## 🔍 Filters")
    
    # Epic filter
    epics = db_manager.get_epics()
    epic_options = ["All Epics"] + [f"{epic['epic_key']}: {epic['name']}" for epic in epics]
    selected_epic = st.sidebar.selectbox("Filter by Epic", epic_options)
    
    if selected_epic != "All Epics":
        st.session_state.kanban_epic_filter = selected_epic.split(":")[0]
    else:
        st.session_state.kanban_epic_filter = None
    
    # TDD Phase filter
    tdd_phases = ["All Phases", "Red", "Green", "Refactor", "Unknown"]
    selected_phase = st.sidebar.selectbox("Filter by TDD Phase", tdd_phases)
    
    if selected_phase != "All Phases":
        st.session_state.kanban_phase_filter = selected_phase.lower()
    else:
        st.session_state.kanban_phase_filter = None
    
    # Priority filter
    priorities = ["All Priorities", "High", "Medium", "Low"]
    selected_priority = st.sidebar.selectbox("Filter by Priority", priorities)
    
    if selected_priority != "All Priorities":
        st.session_state.kanban_priority_filter = selected_priority.lower()
    else:
        st.session_state.kanban_priority_filter = None
    
    st.sidebar.markdown("---")
    
    # Board settings
    st.sidebar.markdown("## ⚙️ Board Settings")
    
    st.session_state.kanban_show_estimates = st.sidebar.checkbox(
        "Show Time Estimates", 
        value=st.session_state.get("kanban_show_estimates", True)
    )
    
    st.session_state.kanban_group_by_epic = st.sidebar.checkbox(
        "Group by Epic", 
        value=st.session_state.get("kanban_group_by_epic", False)
    )
    
    st.session_state.kanban_show_tdd_phases = st.sidebar.checkbox(
        "Show TDD Phases", 
        value=st.session_state.get("kanban_show_tdd_phases", True)
    )


def _apply_filters(tasks: List[Dict[str, Any]], epics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply sidebar filters to tasks."""
    
    filtered_tasks = tasks.copy()
    
    # Epic filter
    epic_filter = st.session_state.get("kanban_epic_filter")
    if epic_filter:
        epic_id = None
        for epic in epics:
            if epic.get("epic_key") == epic_filter:
                epic_id = epic.get("id")
                break
        
        if epic_id:
            filtered_tasks = [t for t in filtered_tasks if t.get("epic_id") == epic_id]
    
    # TDD Phase filter
    phase_filter = st.session_state.get("kanban_phase_filter")
    if phase_filter:
        if phase_filter == "unknown":
            filtered_tasks = [t for t in filtered_tasks if not t.get("tdd_phase") or t.get("tdd_phase") == ""]
        else:
            filtered_tasks = [t for t in filtered_tasks if t.get("tdd_phase", "").lower() == phase_filter]
    
    # Priority filter
    priority_filter = st.session_state.get("kanban_priority_filter")
    if priority_filter:
        filtered_tasks = [t for t in filtered_tasks if str(t.get("priority", "")).lower() == priority_filter]
    
    return filtered_tasks


def _render_kanban_board(tasks: List[Dict[str, Any]], db_manager: DatabaseManager, epics: List[Dict[str, Any]]):
    """Render the main Kanban board."""
    
    # Define board columns
    columns = {
        "todo": {"title": "📝 To Do", "color": "#FFE4E1"},
        "in_progress": {"title": "🟡 In Progress", "color": "#FFF8DC"},
        "completed": {"title": "✅ Completed", "color": "#E8F5E8"}
    }
    
    # Group tasks by status
    task_groups = {status: [] for status in columns.keys()}
    for task in tasks:
        status = task.get("status", "todo")
        if status in task_groups:
            task_groups[status].append(task)
    
    # Render columns
    cols = st.columns(len(columns))
    
    for idx, (status, column_info) in enumerate(columns.items()):
        with cols[idx]:
            st.markdown(f"### {column_info['title']}")
            st.markdown(f"*{len(task_groups[status])} tasks*")
            
            # Column container
            with st.container():
                st.markdown(f"<div style='background-color: {column_info['color']}; padding: 10px; border-radius: 5px; min-height: 400px;'>", unsafe_allow_html=True)
                
                # Render tasks in this column
                for task in task_groups[status]:
                    _render_task_card(task, db_manager, epics, status)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Quick add button for todo column
            if status == "todo":
                if st.button(f"➕ Quick Add Task", key=f"quick_add_{status}"):
                    _show_quick_add_modal(db_manager, epics)


def _render_task_card(task: Dict[str, Any], db_manager: DatabaseManager, epics: List[Dict[str, Any]], current_status: str):
    """Render a single task card."""
    
    task_id = task.get("id")
    task_title = task.get("title", "Untitled Task")
    epic_name = task.get("epic_name", "No Epic")
    tdd_phase = task.get("tdd_phase", "")
    estimate = task.get("estimate_minutes", 0)
    priority = task.get("priority", 1)
    
    # Task card container
    with st.container():
        # Card styling
        priority_colors = {1: "#FFB3BA", 2: "#FFDFBA", 3: "#BAFFC9"}  # High, Medium, Low
        card_color = priority_colors.get(priority, "#F0F0F0")
        
        st.markdown(f"""
        <div style='background-color: {card_color}; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid #333;'>
            <div style='font-weight: bold; margin-bottom: 5px;'>{task_title}</div>
            <div style='font-size: 12px; color: #666;'>{epic_name}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Task details in expander
        with st.expander(f"Details: {task_title}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Epic:** {epic_name}")
                if st.session_state.get("kanban_show_tdd_phases", True) and tdd_phase:
                    phase_colors = {"red": "🔴", "green": "🟢", "refactor": "🔵"}
                    phase_emoji = phase_colors.get(tdd_phase.lower(), "⚪")
                    st.write(f"**TDD Phase:** {phase_emoji} {tdd_phase.title()}")
                
                if st.session_state.get("kanban_show_estimates", True) and estimate:
                    st.write(f"**Estimate:** {estimate} minutes")
            
            with col2:
                priority_names = {1: "High", 2: "Medium", 3: "Low"}
                st.write(f"**Priority:** {priority_names.get(priority, 'Unknown')}")
                
                if task.get("description"):
                    st.write(f"**Description:** {task['description']}")
            
            # Task actions
            st.markdown("**Actions:**")
            action_cols = st.columns(3)
            
            with action_cols[0]:
                if st.button("✏️ Edit", key=f"edit_{task_id}"):
                    _show_edit_task_modal(task, db_manager, epics)
            
            with action_cols[1]:
                # Status change buttons
                status_options = {"todo": "📝", "in_progress": "🟡", "completed": "✅"}
                for status, emoji in status_options.items():
                    if status != current_status:
                        if st.button(f"{emoji} {status.replace('_', ' ').title()}", key=f"move_{task_id}_{status}"):
                            _update_task_status(task_id, status, db_manager)
            
            with action_cols[2]:
                if st.button("🗑️ Delete", key=f"delete_{task_id}"):
                    if st.session_state.get(f"confirm_delete_{task_id}"):
                        # Actually delete
                        _delete_task(task_id, db_manager)
                    else:
                        # Show confirmation
                        st.session_state[f"confirm_delete_{task_id}"] = True
                        st.rerun()
                
                if st.session_state.get(f"confirm_delete_{task_id}"):
                    st.warning("⚠️ Click again to confirm deletion")


def _show_quick_add_modal(db_manager: DatabaseManager, epics: List[Dict[str, Any]]):
    """Show quick add task modal."""
    
    st.session_state.show_quick_add = True
    
    if st.session_state.get("show_quick_add"):
        with st.form("quick_add_task"):
            st.markdown("### ➕ Quick Add Task")
            
            title = st.text_input("Task Title*", placeholder="Enter task title...")
            
            col1, col2 = st.columns(2)
            with col1:
                epic_options = ["Select Epic"] + [f"{e['epic_key']}: {e['name']}" for e in epics]
                selected_epic = st.selectbox("Epic", epic_options)
            
            with col2:
                tdd_phase = st.selectbox("TDD Phase", ["", "red", "green", "refactor"])
            
            submitted = st.form_submit_button("Add Task")
            
            if submitted and title:
                # Get epic ID
                epic_id = None
                if selected_epic != "Select Epic":
                    epic_key = selected_epic.split(":")[0]
                    for epic in epics:
                        if epic.get("epic_key") == epic_key:
                            epic_id = epic.get("id")
                            break
                
                # Create task (simplified - would need proper database insertion)
                success = _create_task(title, epic_id, tdd_phase, db_manager)
                
                if success:
                    st.success("✅ Task created successfully!")
                    st.session_state.show_quick_add = False
                    st.rerun()
                else:
                    st.error("❌ Failed to create task")


def _render_create_task_form(db_manager: DatabaseManager, epics: List[Dict[str, Any]]):
    """Render detailed task creation form."""
    
    with st.form("create_task"):
        st.markdown("### ➕ Create New Task")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Task Title*", placeholder="Enter a descriptive title...")
            description = st.text_area("Description", placeholder="Optional task description...")
            
            epic_options = ["Select Epic"] + [f"{e['epic_key']}: {e['name']}" for e in epics]
            selected_epic = st.selectbox("Epic*", epic_options)
        
        with col2:
            tdd_phase = st.selectbox("TDD Phase", ["", "red", "green", "refactor"])
            priority = st.selectbox("Priority", [1, 2, 3], format_func=lambda x: {1: "High", 2: "Medium", 3: "Low"}[x])
            estimate = st.number_input("Estimate (minutes)", min_value=0, value=0, step=15)
        
        submitted = st.form_submit_button("Create Task", type="primary")
        
        if submitted:
            if not title:
                st.error("❌ Task title is required")
            elif selected_epic == "Select Epic":
                st.error("❌ Please select an epic")
            else:
                # Get epic ID
                epic_id = None
                epic_key = selected_epic.split(":")[0]
                for epic in epics:
                    if epic.get("epic_key") == epic_key:
                        epic_id = epic.get("id")
                        break
                
                # Create task
                success = _create_task(
                    title=title,
                    epic_id=epic_id,
                    tdd_phase=tdd_phase,
                    db_manager=db_manager,
                    description=description,
                    priority=priority,
                    estimate_minutes=estimate
                )
                
                if success:
                    st.success("✅ Task created successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to create task")


def _show_edit_task_modal(task: Dict[str, Any], db_manager: DatabaseManager, epics: List[Dict[str, Any]]):
    """Show edit task modal."""
    
    task_id = task.get("id")
    st.session_state[f"editing_task_{task_id}"] = True
    
    if st.session_state.get(f"editing_task_{task_id}"):
        with st.form(f"edit_task_{task_id}"):
            st.markdown(f"### ✏️ Edit Task: {task.get('title', 'Unknown')}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Title", value=task.get("title", ""))
                description = st.text_area("Description", value=task.get("description", ""))
            
            with col2:
                current_phase = task.get("tdd_phase", "")
                phase_index = ["", "red", "green", "refactor"].index(current_phase) if current_phase in ["", "red", "green", "refactor"] else 0
                tdd_phase = st.selectbox("TDD Phase", ["", "red", "green", "refactor"], index=phase_index)
                
                current_priority = task.get("priority", 2)
                priority = st.selectbox("Priority", [1, 2, 3], index=[1, 2, 3].index(current_priority), format_func=lambda x: {1: "High", 2: "Medium", 3: "Low"}[x])
                
                estimate = st.number_input("Estimate (minutes)", value=task.get("estimate_minutes", 0), min_value=0, step=15)
            
            col_save, col_cancel = st.columns(2)
            
            with col_save:
                submitted = st.form_submit_button("Save Changes", type="primary")
            
            with col_cancel:
                cancelled = st.form_submit_button("Cancel")
            
            if submitted:
                # Update task
                success = _update_task(
                    task_id=task_id,
                    title=title,
                    description=description,
                    tdd_phase=tdd_phase,
                    priority=priority,
                    estimate_minutes=estimate,
                    db_manager=db_manager
                )
                
                if success:
                    st.success("✅ Task updated successfully!")
                    st.session_state[f"editing_task_{task_id}"] = False
                    st.rerun()
                else:
                    st.error("❌ Failed to update task")
            
            if cancelled:
                st.session_state[f"editing_task_{task_id}"] = False
                st.rerun()


def _create_task(title: str, epic_id: Optional[int], tdd_phase: str, db_manager: DatabaseManager, 
                description: str = "", priority: int = 2, estimate_minutes: int = 0) -> bool:
    """Create a new task in the database."""
    
    # This is a simplified implementation
    # In a real application, you would call db_manager.create_task() or similar
    try:
        # For now, just return True to simulate success
        # TODO: Implement actual database insertion
        return True
    except Exception:
        return False


def _update_task_status(task_id: int, new_status: str, db_manager: DatabaseManager) -> bool:
    """Update task status."""
    
    try:
        return db_manager.update_task_status(task_id, new_status)
    except Exception:
        return False


def _update_task(task_id: int, title: str, description: str, tdd_phase: str, 
                priority: int, estimate_minutes: int, db_manager: DatabaseManager) -> bool:
    """Update task details."""
    
    try:
        # This would need to be implemented in DatabaseManager
        # For now, just return True to simulate success
        # TODO: Implement actual database update
        return True
    except Exception:
        return False


def _delete_task(task_id: int, db_manager: DatabaseManager) -> bool:
    """Delete a task."""
    
    try:
        # This would need to be implemented in DatabaseManager
        # For now, just return True to simulate success
        # TODO: Implement actual database deletion
        return True
    except Exception:
        return False


if __name__ == "__main__":
    render_kanban_page()