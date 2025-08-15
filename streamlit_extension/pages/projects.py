"""
📁 Project Management Page

Comprehensive project management interface with CRUD operations:
- Project overview with card-based visualization
- Client filtering and pagination
- Create, edit, and delete projects
- Project timeline and budget tracking
- Status and progress monitoring
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, date

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
    from streamlit_extension.utils.validators import validate_project_data, validate_project_key_uniqueness
    from streamlit_extension.utils.auth import require_authentication
    from streamlit_extension.utils.security import (
        create_safe_project, sanitize_display, validate_form, check_rate_limit,
        security_manager
    )
    from streamlit_extension.config import load_config
    DATABASE_UTILS_AVAILABLE = True
except ImportError:
    DATABASE_UTILS_AVAILABLE = False
    DatabaseManager = validate_project_data = load_config = None
    create_safe_project = sanitize_display = validate_form = None


def render_project_card(project: Dict[str, Any], db_manager: DatabaseManager, clients_map: Dict[int, str]):
    """Render an individual project card."""
    if not STREAMLIT_AVAILABLE:
        return
    
    with st.container():
        # Card header with status indicator
        status_colors = {
            "planning": "🟡",
            "in_progress": "🟢", 
            "completed": "✅",
            "on_hold": "⏸️",
            "cancelled": "🔴"
        }
        status_emoji = status_colors.get(project.get("status", "planning"), "⚪")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            client_name = clients_map.get(project.get('client_id'), 'Unknown Client')
            st.markdown(f"### {status_emoji} {project['name']}")
            st.caption(f"**Client:** {client_name} | **Key:** {project.get('project_key', 'N/A')}")
        
        with col2:
            if st.button("✏️ Edit", key=f"edit_project_{project['id']}", use_container_width=True):
                st.session_state[f"edit_project_{project['id']}"] = True
                st.rerun()
        
        with col3:
            if st.button("🗑️ Delete", key=f"delete_project_{project['id']}", use_container_width=True):
                st.session_state[f"delete_project_{project['id']}"] = True
                st.rerun()
        
        # Project details
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if project.get('description'):
                safe_description = sanitize_display(project['description']) if sanitize_display else project['description']
                st.markdown(f"**Description:** {safe_description}")
            
            # Project info
            if project.get('project_type'):
                st.markdown(f"**Type:** {project['project_type'].title()}")
            if project.get('methodology'):
                st.markdown(f"**Methodology:** {project['methodology'].title()}")
        
        with col2:
            # Timeline
            st.markdown("**Timeline:**")
            if project.get('planned_start_date'):
                start_date = project['planned_start_date']
                if isinstance(start_date, str):
                    start_date = start_date[:10]  # Get date part
                st.markdown(f"• **Start:** {start_date}")
            
            if project.get('planned_end_date'):
                end_date = project['planned_end_date']
                if isinstance(end_date, str):
                    end_date = end_date[:10]  # Get date part
                st.markdown(f"• **End:** {end_date}")
            
            # Progress
            completion = project.get('completion_percentage', 0)
            st.progress(completion / 100)
            st.caption(f"Progress: {completion:.1f}%")
        
        with col3:
            # Budget and metrics
            if project.get('budget_amount'):
                currency = project.get('budget_currency', 'BRL')
                st.metric("Budget", f"{currency} {project['budget_amount']:,.2f}")
            
            if project.get('estimated_hours'):
                st.metric("Est. Hours", f"{project['estimated_hours']:.1f}h")
            
            # Health status
            health_colors = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
            health = project.get('health_status', 'green')
            health_emoji = health_colors.get(health, "⚪")
            st.markdown(f"**Health:** {health_emoji} {health.title()}")
        
        # Handle edit modal
        if st.session_state.get(f"edit_project_{project['id']}", False):
            render_edit_project_modal(project, db_manager, clients_map)
        
        # Handle delete confirmation
        if st.session_state.get(f"delete_project_{project['id']}", False):
            render_delete_project_modal(project, db_manager, clients_map)
        
        st.divider()


def render_edit_project_modal(project: Dict[str, Any], db_manager: DatabaseManager, clients_map: Dict[int, str]):
    """Render the edit project modal."""
    if not STREAMLIT_AVAILABLE:
        return
    
    with st.modal(f"Edit Project: {project['name']}", width="large"):
        with st.form(f"edit_project_form_{project['id']}"):
            st.markdown("### 📝 Edit Project Information")
            
            # Generate CSRF token for form protection
            csrf_form_id = f"edit_project_form_{project['id']}"
            csrf_field = security_manager.get_csrf_form_field(csrf_form_id) if security_manager else None
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Basic Information")
                
                # Client selection
                clients = [(id, name) for id, name in clients_map.items()]
                client_options = [name for _, name in clients]
                current_client_index = 0
                for i, (id, _) in enumerate(clients):
                    if id == project.get('client_id'):
                        current_client_index = i
                        break
                
                selected_client = st.selectbox("Client*", options=client_options, index=current_client_index)
                selected_client_id = next(id for id, name in clients if name == selected_client)
                
                project_key = st.text_input("Project Key*", value=project.get('project_key', ''))
                name = st.text_input("Project Name*", value=project.get('name', ''))
                description = st.text_area("Description", value=project.get('description', ''))
                
                project_type = st.selectbox("Project Type", 
                    options=["development", "maintenance", "consulting", "research", "support"],
                    index=["development", "maintenance", "consulting", "research", "support"].index(project.get('project_type', 'development'))
                )
                methodology = st.selectbox("Methodology",
                    options=["agile", "waterfall", "kanban", "scrum", "lean", "hybrid"],
                    index=["agile", "waterfall", "kanban", "scrum", "lean", "hybrid"].index(project.get('methodology', 'agile'))
                )
            
            with col2:
                st.markdown("#### Timeline & Budget")
                
                # Dates
                start_date = project.get('planned_start_date')
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
                elif start_date is None:
                    start_date = date.today()
                
                end_date = project.get('planned_end_date')
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date()
                elif end_date is None:
                    end_date = date.today()
                
                planned_start_date = st.date_input("Planned Start Date*", value=start_date)
                planned_end_date = st.date_input("Planned End Date*", value=end_date)
                
                # Budget
                budget_amount = st.number_input("Budget Amount", value=float(project.get('budget_amount', 0.0)), min_value=0.0)
                budget_currency = st.selectbox("Currency", options=["BRL", "USD", "EUR"], 
                    index=["BRL", "USD", "EUR"].index(project.get('budget_currency', 'BRL')))
                estimated_hours = st.number_input("Estimated Hours", value=float(project.get('estimated_hours', 0.0)), min_value=0.0)
                
                # Status
                status = st.selectbox("Status*", 
                    options=["planning", "in_progress", "completed", "on_hold", "cancelled"],
                    index=["planning", "in_progress", "completed", "on_hold", "cancelled"].index(project.get('status', 'planning'))
                )
                
                health_status = st.selectbox("Health Status",
                    options=["green", "yellow", "red"],
                    index=["green", "yellow", "red"].index(project.get('health_status', 'green'))
                )
                
                completion_percentage = st.slider("Completion %", 0.0, 100.0, float(project.get('completion_percentage', 0.0)))
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.form_submit_button("💾 Update Project", use_container_width=True):
                    # CSRF Protection
                    if csrf_field and security_manager:
                        csrf_valid, csrf_error = security_manager.require_csrf_protection(
                            csrf_form_id, csrf_field.get("token_value")
                        )
                        if not csrf_valid:
                            st.error(f"🔒 Security Error: {csrf_error}")
                            return
                    
                    # Check rate limit for form submission
                    rate_allowed, rate_error = check_rate_limit("form_submit") if check_rate_limit else (True, None)
                    if not rate_allowed:
                        st.error(f"🚦 {rate_error}")
                        return
                    
                    # Create raw data
                    raw_data = {
                        'client_id': selected_client_id,
                        'project_key': project_key,
                        'name': name,
                        'description': description,
                        'project_type': project_type,
                        'methodology': methodology,
                        'planned_start_date': planned_start_date.isoformat(),
                        'planned_end_date': planned_end_date.isoformat(),
                        'budget_amount': budget_amount,
                        'budget_currency': budget_currency,
                        'estimated_hours': estimated_hours,
                        'status': status,
                        'health_status': health_status,
                        'completion_percentage': completion_percentage
                    }
                    
                    # Security validation
                    if validate_form:
                        security_valid, security_errors = validate_form(raw_data)
                        if not security_valid:
                            for error in security_errors:
                                st.error(f"🔒 Security: {error}")
                            return
                    
                    # Sanitize data for security
                    project_data = create_safe_project(raw_data) if create_safe_project else raw_data
                    
                    is_valid, errors = validate_project_data(project_data)
                    
                    if is_valid:
                        # Check uniqueness (excluding current project)
                        existing_projects = db_manager.get_projects(include_inactive=True)
                        
                        if not validate_project_key_uniqueness(project_key, selected_client_id, existing_projects, project['id']):
                            st.error("❌ Project key already exists for this client")
                        else:
                            # Check rate limit for database write
                            db_rate_allowed, db_rate_error = check_rate_limit("db_write") if check_rate_limit else (True, None)
                            if not db_rate_allowed:
                                st.error(f"🚦 Database {db_rate_error}")
                                return
                            
                            # Update project
                            success = db_manager.update_project(project['id'], **project_data)
                            if success:
                                st.success("✅ Project updated successfully!")
                                st.session_state[f"edit_project_{project['id']}"] = False
                                st.rerun()
                            else:
                                st.error("❌ Failed to update project")
                    else:
                        for error in errors:
                            st.error(f"❌ {error}")
            
            with col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state[f"edit_project_{project['id']}"] = False
                    st.rerun()


def render_delete_project_modal(project: Dict[str, Any], db_manager: DatabaseManager, clients_map: Dict[int, str]):
    """Render the delete project confirmation modal."""
    if not STREAMLIT_AVAILABLE:
        return
    
    with st.modal(f"Delete Project: {project['name']}", width="medium"):
        st.markdown("### ⚠️ Confirm Deletion")
        client_name = clients_map.get(project.get('client_id'), 'Unknown Client')
        st.warning(f"Are you sure you want to delete project **{project['name']}** from client **{client_name}**?")
        
        # Show related epics warning
        try:
            epics = db_manager.get_epics()
            project_epics = [e for e in epics if e.get('project_id') == project['id']]
            if project_epics:
                st.error(f"⚠️ This project has {len(project_epics)} epic(s). Deleting the project will affect these epics.")
        except:
            pass
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Delete Project", use_container_width=True):
                success = db_manager.delete_project(project['id'], soft_delete=True)
                if success:
                    st.success("✅ Project deleted successfully!")
                    st.session_state[f"delete_project_{project['id']}"] = False
                    st.rerun()
                else:
                    st.error("❌ Failed to delete project")
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state[f"delete_project_{project['id']}"] = False
                st.rerun()


def render_create_project_form(db_manager: DatabaseManager, clients_map: Dict[int, str]):
    """Render the create new project form."""
    if not STREAMLIT_AVAILABLE:
        return
    
    with st.expander("➕ Create New Project", expanded=False):
        with st.form("create_project_form"):
            st.markdown("### 📝 New Project Information")
            
            # Generate CSRF token for form protection
            csrf_form_id = "create_project_form"
            csrf_field = security_manager.get_csrf_form_field(csrf_form_id) if security_manager else None
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Basic Information")
                
                # Client selection
                if not clients_map:
                    st.error("❌ No clients available. Please create a client first.")
                    return
                
                client_options = list(clients_map.values())
                selected_client_name = st.selectbox("Client*", options=client_options)
                selected_client_id = next(id for id, name in clients_map.items() if name == selected_client_name)
                
                project_key = st.text_input("Project Key*", placeholder="e.g., project_abc")
                name = st.text_input("Project Name*", placeholder="e.g., Website Development")
                description = st.text_area("Description", placeholder="Brief description of the project...")
                
                project_type = st.selectbox("Project Type", 
                    options=["development", "maintenance", "consulting", "research", "support"],
                    index=0
                )
                methodology = st.selectbox("Methodology",
                    options=["agile", "waterfall", "kanban", "scrum", "lean", "hybrid"],
                    index=0
                )
            
            with col2:
                st.markdown("#### Timeline & Budget")
                
                planned_start_date = st.date_input("Planned Start Date*", value=date.today())
                planned_end_date = st.date_input("Planned End Date*", value=date.today())
                
                budget_amount = st.number_input("Budget Amount", value=0.0, min_value=0.0)
                budget_currency = st.selectbox("Currency", options=["BRL", "USD", "EUR"], index=0)
                estimated_hours = st.number_input("Estimated Hours", value=0.0, min_value=0.0)
                
                status = st.selectbox("Status*", 
                    options=["planning", "in_progress", "completed", "on_hold", "cancelled"],
                    index=0
                )
                
                health_status = st.selectbox("Health Status",
                    options=["green", "yellow", "red"],
                    index=0
                )
            
            if st.form_submit_button("🚀 Create Project", use_container_width=True):
                # CSRF Protection
                if csrf_field and security_manager:
                    csrf_valid, csrf_error = security_manager.require_csrf_protection(
                        csrf_form_id, csrf_field.get("token_value")
                    )
                    if not csrf_valid:
                        st.error(f"🔒 Security Error: {csrf_error}")
                        return
                
                # Check rate limit for form submission
                rate_allowed, rate_error = check_rate_limit("form_submit") if check_rate_limit else (True, None)
                if not rate_allowed:
                    st.error(f"🚦 {rate_error}")
                    return
                
                # Create raw data
                raw_data = {
                    'client_id': selected_client_id,
                    'project_key': project_key,
                    'name': name,
                    'description': description,
                    'project_type': project_type,
                    'methodology': methodology,
                    'planned_start_date': planned_start_date.isoformat(),
                    'planned_end_date': planned_end_date.isoformat(),
                    'budget_amount': budget_amount,
                    'budget_currency': budget_currency,
                    'estimated_hours': estimated_hours,
                    'status': status,
                    'health_status': health_status,
                    'completion_percentage': 0.0
                }
                
                # Security validation
                if validate_form:
                    security_valid, security_errors = validate_form(raw_data)
                    if not security_valid:
                        for error in security_errors:
                            st.error(f"🔒 Security: {error}")
                        return
                
                # Sanitize data for security
                project_data = create_safe_project(raw_data) if create_safe_project else raw_data
                
                is_valid, errors = validate_project_data(project_data)
                
                if is_valid:
                    # Check uniqueness
                    existing_projects = db_manager.get_projects(include_inactive=True)
                    
                    if not validate_project_key_uniqueness(project_key, selected_client_id, existing_projects):
                        st.error("❌ Project key already exists for this client")
                    else:
                        # Check rate limit for database write
                        db_rate_allowed, db_rate_error = check_rate_limit("db_write") if check_rate_limit else (True, None)
                        if not db_rate_allowed:
                            st.error(f"🚦 Database {db_rate_error}")
                            return
                        
                        # Create project
                        project_id = db_manager.create_project(
                            client_id=selected_client_id,
                            project_key=project_key,
                            name=name,
                            description=description,
                            project_type=project_type,
                            methodology=methodology
                        )
                        
                        if project_id:
                            # Update additional fields
                            additional_fields = {
                                'planned_start_date': planned_start_date.isoformat(),
                                'planned_end_date': planned_end_date.isoformat(),
                                'budget_amount': budget_amount,
                                'budget_currency': budget_currency,
                                'estimated_hours': estimated_hours,
                                'status': status,
                                'health_status': health_status
                            }
                            db_manager.update_project(project_id, **additional_fields)
                            
                            st.success("✅ Project created successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to create project")
                else:
                    for error in errors:
                        st.error(f"❌ {error}")


@require_authentication
def render_projects_page():
    """Render the main projects management page."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    if not DATABASE_UTILS_AVAILABLE:
        st.error("❌ Database utilities not available")
        return {"error": "Database utilities not available"}
    
    # Check rate limit for page load
    page_rate_allowed, page_rate_error = check_rate_limit("page_load") if check_rate_limit else (True, None)
    if not page_rate_allowed:
        st.error(f"🚦 {page_rate_error}")
        st.info("Please wait before reloading the page.")
        return {"error": "Rate limited"}
    
    st.title("📁 Project Management")
    st.markdown("Manage your projects, timelines, and deliverables")
    st.markdown("---")
    
    # Initialize database manager
    try:
        config = load_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        return {"error": f"Database connection error: {e}"}
    
    # Get clients for mapping
    try:
        clients_result = db_manager.get_clients(include_inactive=False)
        clients = clients_result.get("data", []) if isinstance(clients_result, dict) else []
        clients_map = {client['id']: client['name'] for client in clients} if clients else {}
        
        if not clients_map:
            st.warning("⚠️ No active clients found. Please create clients first before creating projects.")
            return {"status": "no_clients"}
    
    except Exception as e:
        st.error(f"❌ Error loading clients: {e}")
        return {"error": f"Error loading clients: {e}"}
    
    # Filters and search
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_name = st.text_input("🔍 Search by name", placeholder="Type project name...")
    
    with col2:
        status_filter = st.selectbox("Status Filter", 
            options=["all", "planning", "in_progress", "completed", "on_hold", "cancelled"],
            index=0
        )
    
    with col3:
        client_filter = st.selectbox("Client Filter",
            options=["all"] + list(clients_map.values()),
            index=0
        )
    
    # Create new project form
    render_create_project_form(db_manager, clients_map)
    
    st.markdown("---")
    
    # Get projects with filters
    try:
        # Check rate limit for database read
        db_read_allowed, db_read_error = check_rate_limit("db_read") if check_rate_limit else (True, None)
        if not db_read_allowed:
            st.error(f"🚦 Database {db_read_error}")
            return {"error": "Database rate limited"}
        
        all_projects = db_manager.get_projects(include_inactive=True)
        
        if not all_projects:
            st.info("📝 No projects found. Create your first project using the form above!")
            return {"status": "no_projects"}
        
        # Apply filters
        filtered_projects = all_projects
        
        if search_name:
            filtered_projects = [p for p in filtered_projects if search_name.lower() in p.get('name', '').lower()]
        
        if status_filter != "all":
            filtered_projects = [p for p in filtered_projects if p.get('status') == status_filter]
        
        if client_filter != "all":
            client_id = next((id for id, name in clients_map.items() if name == client_filter), None)
            if client_id:
                filtered_projects = [p for p in filtered_projects if p.get('client_id') == client_id]
        
        # Display results count
        st.markdown(f"**Found {len(filtered_projects)} project(s)**")
        
        if not filtered_projects:
            st.warning("🔍 No projects match your current filters.")
            return {"status": "no_matches"}
        
        # Display projects
        for project in filtered_projects:
            render_project_card(project, db_manager, clients_map)
    
    except Exception as e:
        st.error(f"❌ Error loading projects: {e}")
        return {"error": f"Error loading projects: {e}"}
    
    return {"status": "success", "projects_count": len(filtered_projects)}


# Export the main function
__all__ = ["render_projects_page"]

# Execute when run as a Streamlit page
if __name__ == "__main__":
    if STREAMLIT_AVAILABLE:
        render_projects_page()

