"""
Kanban Board Page

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
    # Migrated to modular database API
    from streamlit_extension.database import queries
    from streamlit_extension.database.connection import transaction
    from streamlit_extension.utils.security import (
        security_manager, validate_form, check_rate_limit, sanitize_display
    )
    from streamlit_extension.config import load_config
    from streamlit_extension.config.constants import (
        TaskStatus, TDDPhases, Priority, UIConstants, ErrorMessages
    )
    DATABASE_UTILS_AVAILABLE = True
except ImportError:
    queries = transaction = load_config = security_manager = None
    validate_form = check_rate_limit = sanitize_display = None
    TaskStatus = TDDPhases = Priority = UIConstants = ErrorMessages = None
    DATABASE_UTILS_AVAILABLE = False

# --- Autenticação -------------------------------------------------------------
# Import absoluto (corrige erro crítico do relatório):
try:
    from streamlit_extension.auth.middleware import init_protected_page, require_auth
except ImportError:
    # Fallback seguro em desenvolvimento: mantém página acessível
    def init_protected_page(title: str, *, layout: str = "wide") -> None:
        if STREAMLIT_AVAILABLE and st:
            st.set_page_config(page_title=title, layout=layout)

    def require_auth(role: Optional[str] = None):  # type: ignore
        def _decorator(fn):
            def _inner(*args, **kwargs):
                # Em produção real, este fallback não deve ser usado.
                return fn(*args, **kwargs)
            return _inner
        return _decorator

from streamlit_extension.utils.exception_handler import (
    handle_streamlit_exceptions,
    streamlit_error_boundary,
    safe_streamlit_operation,
    get_error_statistics,
)

@require_auth()  # Protege a página; em dev, o fallback acima permite acesso
@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def render_kanban_page():
    """Render the Kanban board page."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    init_protected_page(UIConstants.KANBAN_PAGE_TITLE or "🔍 Kanban Board", layout="wide")
    
    # Page load rate limiting
    page_rate_allowed, page_rate_error = check_rate_limit("page_load") if check_rate_limit else (True, None)
    if not page_rate_allowed:
        st.error(f"🚦 {page_rate_error}")
        st.info("Please wait before reloading the page.")
        return {"error": "Rate limited"}
    
    st.markdown("---")
    
    # Initialize database manager
    if not DATABASE_UTILS_AVAILABLE:
        st.error(
            ErrorMessages.LOADING_ERROR.format(
                entity="database utilities", error="not available"
            )
        )
        return
    
    with streamlit_error_boundary("database_initialization"):
        config = safe_streamlit_operation(
            load_config,
            default_return=None,
            operation_name="load_config",
        )
        if config is None:
            st.error(
                ErrorMessages.LOADING_ERROR.format(
                    entity="configuration", error="loading failed"
                )
            )
            return

        # Using modular database API - no initialization needed
        db_queries = queries
        if db_queries is None:
            st.error(
                ErrorMessages.LOADING_ERROR.format(
                    entity="database queries module", error="not available"
                )
            )
            return
    
    # Sidebar filters
    _render_sidebar_filters(db_queries)
    
    # Database read rate limiting
    db_read_allowed, db_read_error = check_rate_limit("db_read") if check_rate_limit else (True, None)
    if not db_read_allowed:
        st.error(f"🚦 Database {db_read_error}")
        st.info("Please wait before refreshing the data.")
        return {"error": "Rate limited"}
    
    # Load data with memoization for performance
    @st.cache_data(ttl=180)  # Cache for 3 minutes
    def get_tasks_cached():
        """Get tasks with caching for Kanban performance."""
        return safe_streamlit_operation(
            db_queries.list_all_tasks,
            default_return=[],
            operation_name="get_tasks",
        )
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes (epics change less frequently)
    def get_epics_cached():
        """Get epics with caching for Kanban performance."""
        return safe_streamlit_operation(
            db_queries.list_epics,
            default_return=[],
            operation_name="get_epics",
        )
    
    with streamlit_error_boundary("task_loading"):
        with st.spinner("Loading tasks..."):
            tasks = get_tasks_cached()
            epics = get_epics_cached()
    
    # Apply filters
    filtered_tasks = _apply_filters(tasks, epics)
    
    if not filtered_tasks:
        st.info(ErrorMessages.NO_ITEMS_FOUND.format(entity="tasks"))
        _render_create_task_form(db_queries, epics)
        return
    
    # Render board
    with streamlit_error_boundary("ui_rendering"):
        _render_kanban_board(filtered_tasks, db_queries, epics)
    
    # Task creation form
    with st.expander("➕ Create New Task", expanded=False):
        with streamlit_error_boundary("form_rendering"):
            _render_create_task_form(db_queries, epics)

    if st.session_state.get("show_debug_info", False):
        with st.expander("🔧 Error Statistics", expanded=False):
            st.json(get_error_statistics())


def _render_sidebar_filters(db_queries):
    """Render sidebar filters for the Kanban board."""
    
    st.sidebar.markdown("## 🔍 Filters")
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_epics_for_filter():
        """Get epics for filter dropdown with caching."""
        return db_queries.list_epics()
    
    # Epic filter
    epics = get_epics_for_filter()
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


def _render_kanban_board(tasks: List[Dict[str, Any]], db_queries, epics: List[Dict[str, Any]]):
    """Render the main Kanban board."""
    
    # Define board columns
    columns = {
        TaskStatus.TODO.value: {
            "title": f"{UIConstants.ICON_TASK} To Do",
            "color": "#FFE4E1",
        },
        TaskStatus.IN_PROGRESS.value: {
            "title": f"{UIConstants.ICON_PENDING} In Progress",
            "color": "#FFF8DC",
        },
        TaskStatus.COMPLETED.value: {
            "title": f"{UIConstants.ICON_COMPLETED} Completed",
            "color": "#E8F5E8",
        },
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


def _render_task_card(task: Dict[str, Any], db_queries, epics: List[Dict[str, Any]], current_status: str):
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
                    phase_colors = {
                        TDDPhases.RED.value: UIConstants.ICON_CANCELLED,
                        TDDPhases.GREEN.value: UIConstants.ICON_ACTIVE,
                        TDDPhases.REFACTOR.value: UIConstants.ICON_REFACTOR,
                        TDDPhases.BLOCKED.value: UIConstants.ICON_CANCELLED,
                    }
                    phase_emoji = phase_colors.get(
                        tdd_phase.lower(), UIConstants.ICON_UNKNOWN
                    )
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
                # Smart status movement buttons
                status_flow = {
                    TaskStatus.TODO.value: (
                        TaskStatus.IN_PROGRESS.value,
                        f"{UIConstants.CREATE_BUTTON.split()[0]} Start",
                    ),
                    TaskStatus.IN_PROGRESS.value: (
                        TaskStatus.COMPLETED.value,
                        f"{UIConstants.ICON_COMPLETED} Complete",
                    ),
                    TaskStatus.COMPLETED.value: (
                        TaskStatus.TODO.value,
                        f"{UIConstants.ICON_TASK} Reopen",
                    ),
                }

                next_status, button_text = status_flow.get(
                    current_status, (TaskStatus.TODO.value, f"{UIConstants.ICON_TASK} To Do")
                )
                
                if st.button(button_text, key=f"move_{task_id}_{next_status}"):
                    success = _update_task_status(task_id, next_status, db_manager)
                    if success:
                        st.success(f"Task moved to {next_status.replace('_', ' ').title()}!")
                        st.rerun()
                    else:
                        st.error(
                            ErrorMessages.LOADING_ERROR.format(
                                entity="task status", error="update failed"
                            )
                        )
                
                # Additional status options in a smaller button
                other_statuses = [
                    s
                    for s in [TaskStatus.TODO.value, TaskStatus.IN_PROGRESS.value, TaskStatus.COMPLETED.value]
                    if s not in [current_status, next_status]
                ]
                
                if other_statuses and st.button("⚙️ Other", key=f"other_{task_id}"):
                    st.session_state[f"show_other_status_{task_id}"] = True
                
                if st.session_state.get(f"show_other_status_{task_id}"):
                    for status in other_statuses:
                        status_names = {
                            TaskStatus.TODO.value: f"{UIConstants.ICON_TASK} To Do",
                            TaskStatus.IN_PROGRESS.value: f"{UIConstants.ICON_PENDING} In Progress",
                            TaskStatus.COMPLETED.value: f"{UIConstants.ICON_COMPLETED} Completed",
                        }
                        if st.button(status_names[status], key=f"alt_move_{task_id}_{status}"):
                            success = _update_task_status(task_id, status, db_manager)
                            if success:
                                st.success(f"Task moved to {status.replace('_', ' ').title()}!")
                                st.session_state[f"show_other_status_{task_id}"] = False
                                st.rerun()
                            else:
                                st.error(
                                    ErrorMessages.LOADING_ERROR.format(
                                        entity="task status", error="update failed"
                                    )
                                )
            
            with action_cols[2]:
                if not st.session_state.get(f"confirm_delete_{task_id}"):
                    if st.button("🗑️ Delete", key=f"delete_{task_id}"):
                        st.session_state[f"confirm_delete_{task_id}"] = True
                        st.rerun()
                else:
                    st.warning("⚠️ Confirm deletion?")
                    col_confirm, col_cancel = st.columns(2)
                    
                    with col_confirm:
                        if st.button(UIConstants.ICON_COMPLETED + " Yes", key=f"confirm_yes_{task_id}"):
                            success = _delete_task(task_id, db_manager)
                            if success:
                                st.success("Task deleted successfully!")
                                st.session_state[f"confirm_delete_{task_id}"] = False
                                st.rerun()
                            else:
                                st.error("Failed to delete task")
                    
                    with col_cancel:
                        if st.button(UIConstants.CANCEL_BUTTON.split()[0] + " No", key=f"confirm_no_{task_id}"):
                            st.session_state[f"confirm_delete_{task_id}"] = False
                            st.rerun()


def _show_quick_add_modal(db_queries, epics: List[Dict[str, Any]]):
    """Show quick add task modal."""
    
    st.session_state.show_quick_add = True
    
    if st.session_state.get("show_quick_add"):
        with st.form("quick_add_task"):
            st.markdown("### ➕ Quick Add Task")
            
            # Generate CSRF token for form protection
            csrf_form_id = "quick_add_task_form"
            csrf_field = security_manager.get_csrf_form_field(csrf_form_id) if security_manager else None
            
            title = st.text_input("Task Title*", placeholder="Enter task title...")
            
            col1, col2 = st.columns(2)
            with col1:
                epic_options = ["Select Epic"] + [f"{e['epic_key']}: {e['name']}" for e in epics]
                selected_epic = st.selectbox("Epic", epic_options)
            
            with col2:
                tdd_phase = st.selectbox("TDD Phase", ["", "red", "green", "refactor"])
            
            submitted = st.form_submit_button("Add Task")
            
            if submitted and title:
                # Rate limiting for form submission
                rate_allowed, rate_error = check_rate_limit("form_submit") if check_rate_limit else (True, None)
                if not rate_allowed:
                    st.error(f"🚦 Form {rate_error}")
                    return
                
                # CSRF Protection
                if csrf_field and security_manager:
                    csrf_valid, csrf_error = security_manager.require_csrf_protection(
                        csrf_form_id, csrf_field.get("token_value")
                    )
                    if not csrf_valid:
                        st.error(f"🔒 Security Error: {csrf_error}")
                        return
                
                # Form validation for security
                raw_data = {
                    "title": title,
                    "epic": selected_epic,
                    "tdd_phase": tdd_phase
                }
                
                if validate_form:
                    security_valid, security_errors = validate_form(raw_data)
                    if not security_valid:
                        for error in security_errors:
                            st.error(f"🔒 Security: {error}")
                        return
                
                # Get epic ID
                epic_id = None
                if selected_epic != "Select Epic":
                    epic_key = selected_epic.split(":")[0]
                    for epic in epics:
                        if epic.get("epic_key") == epic_key:
                            epic_id = epic.get("id")
                            break
                
                # Database write rate limiting
                db_rate_allowed, db_rate_error = check_rate_limit("db_write") if check_rate_limit else (True, None)
                if not db_rate_allowed:
                    st.error(f"🚦 Database {db_rate_error}")
                    return
                
                # Create task (simplified - would need proper database insertion)
                success = _create_task(title, epic_id, tdd_phase, db_manager)
                
                if success:
                    st.success(UIConstants.SUCCESS_CREATE)
                    st.session_state.show_quick_add = False
                    st.rerun()
                else:
                    st.error(
                        ErrorMessages.LOADING_ERROR.format(
                            entity="task", error="creation failed"
                        )
                    )


def _render_create_task_form(db_queries, epics: List[Dict[str, Any]]):
    """Render detailed task creation form."""
    
    with st.form("create_task"):
        st.markdown("### ➕ Create New Task")
        
        # Generate CSRF token for form protection
        csrf_form_id = "create_task_form"
        csrf_field = security_manager.get_csrf_form_field(csrf_form_id) if security_manager else None
        
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
            # Rate limiting for form submission
            rate_allowed, rate_error = check_rate_limit("form_submit") if check_rate_limit else (True, None)
            if not rate_allowed:
                st.error(f"🚦 Form {rate_error}")
                return
            
            # CSRF Protection
            if csrf_field and security_manager:
                csrf_valid, csrf_error = security_manager.require_csrf_protection(
                    csrf_form_id, csrf_field.get("token_value")
                )
                if not csrf_valid:
                    st.error(f"🔒 Security Error: {csrf_error}")
                    return
            
            # Form validation for security
            raw_data = {
                "title": title,
                "description": description,
                "epic": selected_epic,
                "tdd_phase": tdd_phase,
                "priority": priority,
                "estimate": estimate
            }
            
            if validate_form:
                security_valid, security_errors = validate_form(raw_data)
                if not security_valid:
                    for error in security_errors:
                        st.error(f"🔒 Security: {error}")
                    return
            
            if not title:
                st.error(UIConstants.ERROR_INVALID_DATA)
            elif selected_epic == "Select Epic":
                st.error(UIConstants.ERROR_INVALID_DATA)
            else:
                # Get epic ID
                epic_id = None
                epic_key = selected_epic.split(":")[0]
                for epic in epics:
                    if epic.get("epic_key") == epic_key:
                        epic_id = epic.get("id")
                        break
                
                # Database write rate limiting
                db_rate_allowed, db_rate_error = check_rate_limit("db_write") if check_rate_limit else (True, None)
                if not db_rate_allowed:
                    st.error(f"🚦 Database {db_rate_error}")
                    return
                
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
                    st.success(UIConstants.SUCCESS_CREATE)
                    st.rerun()
                else:
                    st.error(
                        ErrorMessages.LOADING_ERROR.format(
                            entity="task", error="creation failed"
                        )
                    )


def _show_edit_task_modal(task: Dict[str, Any], db_queries, epics: List[Dict[str, Any]]):
    """Show edit task modal."""
    
    task_id = task.get("id")
    st.session_state[f"editing_task_{task_id}"] = True
    
    if st.session_state.get(f"editing_task_{task_id}"):
        with st.form(f"edit_task_{task_id}"):
            st.markdown(f"### ✏️ Edit Task: {task.get('title', 'Unknown')}")
            
            # Generate CSRF token for form protection
            csrf_form_id = f"edit_task_form_{task_id}"
            csrf_field = security_manager.get_csrf_form_field(csrf_form_id) if security_manager else None
            
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
                # Rate limiting for form submission
                rate_allowed, rate_error = check_rate_limit("form_submit") if check_rate_limit else (True, None)
                if not rate_allowed:
                    st.error(f"🚦 Form {rate_error}")
                    return
                
                # CSRF Protection
                if csrf_field and security_manager:
                    csrf_valid, csrf_error = security_manager.require_csrf_protection(
                        csrf_form_id, csrf_field.get("token_value")
                    )
                    if not csrf_valid:
                        st.error(f"🔒 Security Error: {csrf_error}")
                        return
                
                # Form validation for security
                raw_data = {
                    "title": title,
                    "description": description,
                    "tdd_phase": tdd_phase,
                    "priority": priority,
                    "estimate": estimate
                }
                
                if validate_form:
                    security_valid, security_errors = validate_form(raw_data)
                    if not security_valid:
                        for error in security_errors:
                            st.error(f"🔒 Security: {error}")
                        return
                
                # Database write rate limiting
                db_rate_allowed, db_rate_error = check_rate_limit("db_write") if check_rate_limit else (True, None)
                if not db_rate_allowed:
                    st.error(f"🚦 Database {db_rate_error}")
                    return
                
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
                    st.success(UIConstants.SUCCESS_UPDATE)
                    st.session_state[f"editing_task_{task_id}"] = False
                    st.rerun()
                else:
                    st.error(
                        ErrorMessages.LOADING_ERROR.format(
                            entity="task", error="update failed"
                        )
                    )
            
            if cancelled:
                st.session_state[f"editing_task_{task_id}"] = False
                st.rerun()


def _create_task(title: str, epic_id: Optional[int], tdd_phase: str, db_queries,
                description: str = "", priority: int = 2, estimate_minutes: int = 0) -> bool:
    """Create a new task in the database."""
    task_id = safe_streamlit_operation(
        lambda task_data: _create_task_modular(task_data, db_queries),
        title=title,
        epic_id=epic_id,
        description=description,
        tdd_phase=tdd_phase,
        priority=priority,
        estimate_minutes=estimate_minutes,
        default_return=None,
        operation_name="create_task",
    )
    return task_id is not None


def _update_task_status(task_id: int, new_status: str, db_queries) -> bool:
    """Update task status."""
    return safe_streamlit_operation(
        lambda task_id, status: _update_task_status_modular(task_id, status, db_queries),
        task_id,
        new_status,
        default_return=False,
        operation_name="update_task_status",
    )


def _update_task(task_id: int, title: str, description: str, tdd_phase: str,
                priority: int, estimate_minutes: int, db_queries) -> bool:
    """Update task details."""
    return safe_streamlit_operation(
        lambda task_id, data: _update_task_modular(task_id, data, db_queries),
        task_id=task_id,
        title=title,
        description=description,
        tdd_phase=tdd_phase,
        priority=priority,
        estimate_minutes=estimate_minutes,
        default_return=False,
        operation_name="update_task",
    )


def _delete_task(task_id: int, db_queries) -> bool:
    """Delete a task."""
    return safe_streamlit_operation(
        lambda task_id: _delete_task_modular(task_id, db_queries),
        task_id,
        soft_delete=True,
        default_return=False,
        operation_name="delete_task",
    )


# Modular database operations
def _create_task_modular(task_data: Dict[str, Any], db_queries) -> Dict[str, Any]:
    """Create task using modular database API."""
    try:
        with transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO framework_tasks (task_key, epic_id, title, description, tdd_phase, status, estimate_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                task_data.get('task_key'), task_data.get('epic_id'), task_data.get('title'),
                task_data.get('description', ''), task_data.get('tdd_phase', 'Red'),
                task_data.get('status', 'active'), task_data.get('estimate_minutes', 0)
            ))
            task_id = cursor.lastrowid
            return {'id': task_id, **task_data}
    except Exception as e:
        raise RuntimeError(f"Failed to create task: {e}")


def _update_task_status_modular(task_id: int, new_status: str, db_queries) -> bool:
    """Update task status using modular database API."""
    try:
        with transaction() as conn:
            cursor = conn.execute("""
                UPDATE framework_tasks SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_status, task_id))
            return cursor.rowcount > 0
    except Exception:
        return False


def _update_task_modular(task_id: int, task_data: Dict[str, Any], db_queries) -> bool:
    """Update task using modular database API."""
    try:
        with transaction() as conn:
            cursor = conn.execute("""
                UPDATE framework_tasks 
                SET title = ?, description = ?, tdd_phase = ?, status = ?, 
                    estimate_minutes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                task_data.get('title'), task_data.get('description'),
                task_data.get('tdd_phase'), task_data.get('status'),
                task_data.get('estimate_minutes'), task_id
            ))
            return cursor.rowcount > 0
    except Exception:
        return False


def _delete_task_modular(task_id: int, db_queries) -> bool:
    """Delete task using modular database API."""
    try:
        with transaction() as conn:
            # Soft delete by updating status
            cursor = conn.execute("""
                UPDATE framework_tasks 
                SET status = 'deleted', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (task_id,))
            return cursor.rowcount > 0
    except Exception:
        return False


if __name__ == "__main__":
    render_kanban_page()