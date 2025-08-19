"""
👥 Client Management Page

Comprehensive client management interface with CRUD operations:
- Client overview with card-based visualization
- Filtering and pagination
- Create, edit, and delete clients
- Client details and contact management
- Business information tracking
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
    from streamlit_extension.utils.validators import validate_client_data, validate_email_uniqueness, validate_client_key_uniqueness
    from streamlit_extension.utils.security import (
        create_safe_client, sanitize_display, validate_form, check_rate_limit,
        security_manager
    )
    from streamlit_extension.config import load_config
    from streamlit_extension.config.constants import (
        StatusValues, ClientTiers, CompanySizes, ErrorMessages, UIConstants, FormFields
    )
    # Import authentication middleware
    from streamlit_extension.auth.middleware import init_protected_page
    DATABASE_UTILS_AVAILABLE = True
except ImportError:
    DATABASE_UTILS_AVAILABLE = False
    DatabaseManager = validate_client_data = load_config = None
    create_safe_client = sanitize_display = validate_form = None
    StatusValues = ClientTiers = CompanySizes = ErrorMessages = UIConstants = FormFields = None
    init_protected_page = None

from streamlit_extension.utils.exception_handler import (
    handle_streamlit_exceptions,
    streamlit_error_boundary,
    safe_streamlit_operation,
    get_error_statistics,
)


def render_client_card(client: Dict[str, Any], db_manager: DatabaseManager):
    """Render an individual client card."""
    if not STREAMLIT_AVAILABLE:
        return
    
    with st.container():
        # Card header with status indicator
        status_colors = {
            StatusValues.ACTIVE.value: UIConstants.ICON_ACTIVE,
            StatusValues.INACTIVE.value: UIConstants.ICON_INACTIVE,
            StatusValues.SUSPENDED.value: UIConstants.ICON_CANCELLED,
            StatusValues.ARCHIVED.value: UIConstants.ICON_UNKNOWN,
        }
        status_emoji = status_colors.get(
            client.get("status", StatusValues.ACTIVE.value), UIConstants.ICON_UNKNOWN
        )
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"### {status_emoji} {client['name']}")
            st.caption(f"**Key:** {client.get('client_key', 'N/A')} | **Tier:** {client.get('client_tier', 'standard').title()}")
        
        with col2:
            if st.button(UIConstants.EDIT_BUTTON, key=f"edit_client_{client['id']}", use_container_width=True):
                st.session_state[f"edit_client_{client['id']}"] = True
                st.rerun()

        with col3:
            if st.button(UIConstants.DELETE_BUTTON, key=f"delete_client_{client['id']}", use_container_width=True):
                st.session_state[f"delete_client_{client['id']}"] = True
                st.rerun()
        
        # Client details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if client.get('description'):
                safe_description = sanitize_display(client['description']) if sanitize_display else client['description']
                st.markdown(f"**Description:** {safe_description}")
            
            # Contact information
            if client.get('primary_contact_name') or client.get('primary_contact_email'):
                st.markdown("**Contact:**")
                if client.get('primary_contact_name'):
                    safe_name = sanitize_display(client['primary_contact_name']) if sanitize_display else client['primary_contact_name']
                    st.markdown(f"• **Name:** {safe_name}")
                if client.get('primary_contact_email'):
                    safe_email = sanitize_display(client['primary_contact_email']) if sanitize_display else client['primary_contact_email']
                    st.markdown(f"• **Email:** {safe_email}")
                if client.get('primary_contact_phone'):
                    safe_phone = sanitize_display(client['primary_contact_phone']) if sanitize_display else client['primary_contact_phone']
                    st.markdown(f"• **Phone:** {safe_phone}")
        
        with col2:
            # Business info
            if client.get('industry'):
                st.markdown(f"**Industry:** {client['industry']}")
            if client.get('company_size'):
                st.markdown(f"**Size:** {client['company_size']}")
            if client.get('hourly_rate'):
                st.markdown(f"**Rate:** R$ {client['hourly_rate']:.2f}/h")

            # Project count
            projects = safe_streamlit_operation(
                db_manager.get_projects,
                client_id=client['id'],
                include_inactive=True,
                default_return=[],
                operation_name="get_projects",
            )
            project_count = len(projects) if projects else 0
            st.metric("Projects", project_count)
        
        # Handle edit modal
        if st.session_state.get(f"edit_client_{client['id']}", False):
            render_edit_client_modal(client, db_manager)
        
        # Handle delete confirmation
        if st.session_state.get(f"delete_client_{client['id']}", False):
            render_delete_client_modal(client, db_manager)
        
        st.divider()


def render_edit_client_modal(client: Dict[str, Any], db_manager: DatabaseManager):
    """Render the edit client modal."""
    if not STREAMLIT_AVAILABLE:
        return
    
    with st.modal(f"Edit Client: {client['name']}", width="large"):
        with st.form(f"edit_client_form_{client['id']}"):
            st.markdown(f"### {UIConstants.ICON_TASK} Edit Client Information")
            
            # Generate CSRF token for form protection
            csrf_form_id = f"edit_client_form_{client['id']}"
            csrf_field = security_manager.get_csrf_form_field(csrf_form_id) if security_manager else None
            
            # Add hidden CSRF token field
            if csrf_field:
                csrf_token = st.text_input("csrf_token", value=csrf_field.get("token_value", ""), 
                                         type="password", label_visibility="hidden", key=f"csrf_edit_{client['id']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Basic Information")
                client_key = st.text_input("Client Key*", value=client.get('client_key', ''))
                name = st.text_input("Client Name*", value=client.get('name', ''))
                description = st.text_area("Description", value=client.get('description', ''))
                
                industry = st.text_input("Industry", value=client.get('industry', ''))
                company_size_options = CompanySizes.get_all_values()
                company_size_default = CompanySizes.get_default()
                company_size = st.selectbox("Company Size", 
                    options=company_size_options,
                    index=company_size_options.index(client.get('company_size', company_size_default))
                )
            
            with col2:
                st.markdown("#### Contact Information")
                primary_contact_name = st.text_input("Contact Name", value=client.get('primary_contact_name', ''))
                primary_contact_email = st.text_input("Contact Email*", value=client.get('primary_contact_email', ''))
                primary_contact_phone = st.text_input("Contact Phone", value=client.get('primary_contact_phone', ''))
                
                st.markdown("#### Business Settings")
                status_options = StatusValues.get_all_values()
                status = st.selectbox(
                    "Status",
                    options=status_options,
                    index=status_options.index(
                        client.get('status', StatusValues.ACTIVE.value)
                    ),
                )
                tier_options = ClientTiers.get_all_values()
                tier_default = ClientTiers.get_default()
                client_tier = st.selectbox("Client Tier",
                    options=tier_options,
                    index=tier_options.index(client.get('client_tier', tier_default))
                )
                hourly_rate = st.number_input("Hourly Rate (R$)", value=float(client.get('hourly_rate', 0.0)), min_value=0.0)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.form_submit_button(UIConstants.UPDATE_BUTTON + " Client", use_container_width=True):
                    # CSRF Protection
                    if csrf_field and security_manager:
                        csrf_token_value = st.session_state.get(f"csrf_edit_{client['id']}", "")
                        csrf_valid, csrf_error = security_manager.require_csrf_protection(
                            csrf_form_id, csrf_token_value
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
                        'client_key': client_key,
                        'name': name,
                        'description': description,
                        'industry': industry,
                        'company_size': company_size,
                        'primary_contact_name': primary_contact_name,
                        'primary_contact_email': primary_contact_email,
                        'primary_contact_phone': primary_contact_phone,
                        'status': status,
                        'client_tier': client_tier,
                        'hourly_rate': hourly_rate
                    }
                    
                    # Security validation
                    if validate_form:
                        security_valid, security_errors = validate_form(raw_data)
                        if not security_valid:
                            for error in security_errors:
                                st.error(f"🔒 Security: {error}")
                            return
                    
                    # Sanitize data for security
                    client_data = create_safe_client(raw_data) if create_safe_client else raw_data
                    
                    is_valid, errors = validate_client_data(client_data)
                    
                    if is_valid:
                        # Check uniqueness (excluding current client)
                        existing_clients_result = db_manager.get_clients(include_inactive=True)
                        existing_clients = existing_clients_result.get("data", []) if isinstance(existing_clients_result, dict) else []
                        
                        if not validate_email_uniqueness(primary_contact_email, existing_clients, client['id']):
                            st.error(UIConstants.ERROR_DUPLICATE)
                        elif not validate_client_key_uniqueness(client_key, existing_clients, client['id']):
                            st.error(UIConstants.ERROR_DUPLICATE)
                        else:
                            # Check rate limit for database write
                            db_rate_allowed, db_rate_error = check_rate_limit("db_write") if check_rate_limit else (True, None)
                            if not db_rate_allowed:
                                st.error(f"🚦 Database {db_rate_error}")
                                return
                            
                            # Update client
                            success = db_manager.update_client(client['id'], **client_data)
                            if success:
                                st.success(ErrorMessages.CLIENT_UPDATE_SUCCESS)
                                st.session_state[f"edit_client_{client['id']}"] = False
                                st.rerun()
                            else:
                                st.error(
                                    ErrorMessages.CLIENT_UPDATE_ERROR.format(
                                        error="Failed to update client"
                                    )
                                )
                    else:
                        for error in errors:
                            st.error(
                                ErrorMessages.CLIENT_UPDATE_ERROR.format(
                                    error=error
                                )
                            )
            
            with col2:
                if st.form_submit_button(UIConstants.CANCEL_BUTTON, use_container_width=True):
                    st.session_state[f"edit_client_{client['id']}"] = False
                    st.rerun()


def render_delete_client_modal(client: Dict[str, Any], db_manager: DatabaseManager):
    """Render the delete client confirmation modal."""
    if not STREAMLIT_AVAILABLE:
        return
    
    with st.modal(f"Delete Client: {client['name']}", width="medium"):
        st.markdown("### ⚠️ Confirm Deletion")
        st.warning(f"Are you sure you want to delete client **{client['name']}**?")
        
        # Show related projects warning
        projects = safe_streamlit_operation(
            db_manager.get_projects,
            client_id=client['id'],
            include_inactive=True,
            default_return=[],
            operation_name="get_projects",
        )
        if projects:
            st.error(f"⚠️ This client has {len(projects)} project(s). Deleting the client will affect these projects.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CSRF-protected delete form
            with st.form(f"delete_client_form_{client['id']}"):
                # Generate CSRF token for delete action
                delete_csrf_form_id = f"delete_client_form_{client['id']}"
                delete_csrf_field = security_manager.get_csrf_form_field(delete_csrf_form_id) if security_manager else None
                
                # Hidden CSRF token field
                if delete_csrf_field:
                    delete_csrf_token = st.text_input("delete_csrf_token", 
                                                    value=delete_csrf_field.get("token_value", ""), 
                                                    type="password", label_visibility="hidden", 
                                                    key=f"csrf_delete_{client['id']}")
                
                if st.form_submit_button(UIConstants.DELETE_BUTTON + " Client", use_container_width=True):
                    # CSRF Protection for delete
                    if delete_csrf_field and security_manager:
                        delete_csrf_token_value = st.session_state.get(f"csrf_delete_{client['id']}", "")
                        csrf_valid, csrf_error = security_manager.require_csrf_protection(
                            delete_csrf_form_id, delete_csrf_token_value
                        )
                        if not csrf_valid:
                            st.error(f"🔒 Security Error: {csrf_error}")
                            return
                    
                    # Check rate limit for database write
                    db_rate_allowed, db_rate_error = check_rate_limit("db_write") if check_rate_limit else (True, None)
                    if not db_rate_allowed:
                        st.error(f"🚦 Database {db_rate_error}")
                        return
                    
                    success = db_manager.delete_client(client['id'], soft_delete=True)
                    if success:
                        st.success(ErrorMessages.CLIENT_DELETE_SUCCESS)
                        st.session_state[f"delete_client_{client['id']}"] = False
                        st.rerun()
                    else:
                        st.error(
                            ErrorMessages.CLIENT_DELETE_ERROR.format(
                                error="Failed to delete client"
                            )
                        )
        
        with col2:
            if st.button(UIConstants.CANCEL_BUTTON, use_container_width=True):
                st.session_state[f"delete_client_{client['id']}"] = False
                st.rerun()


def render_create_client_form(db_manager: DatabaseManager):
    """Render the create new client form."""
    if not STREAMLIT_AVAILABLE:
        return
    
    with st.expander("➕ Create New Client", expanded=False):
        with st.form("create_client_form"):
            st.markdown(f"### {UIConstants.ICON_TASK} New Client Information")
            
            # Generate CSRF token for form protection
            csrf_form_id = "create_client_form"
            csrf_field = security_manager.get_csrf_form_field(csrf_form_id) if security_manager else None
            
            # Add hidden CSRF token field
            if csrf_field:
                csrf_token = st.text_input("csrf_token", value=csrf_field.get("token_value", ""), 
                                         type="password", label_visibility="hidden", key="csrf_create_client")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Basic Information")
                client_key = st.text_input("Client Key*", placeholder="e.g., client_xyz")
                name = st.text_input("Client Name*", placeholder="e.g., Company ABC")
                description = st.text_area("Description", placeholder="Brief description of the client...")
                
                industry = st.text_input("Industry", placeholder="e.g., Technology")
                company_size_options = CompanySizes.get_all_values()
                company_size = st.selectbox("Company Size", options=company_size_options)
            
            with col2:
                st.markdown("#### Contact Information")
                primary_contact_name = st.text_input("Contact Name", placeholder="e.g., John Doe")
                primary_contact_email = st.text_input("Contact Email*", placeholder="john@company.com")
                primary_contact_phone = st.text_input("Contact Phone", placeholder="+55 (11) 99999-9999")
                
                st.markdown("#### Business Settings")
                status_options = StatusValues.get_all_values()
                status = st.selectbox("Status", options=status_options, index=0)
                tier_options = ClientTiers.get_all_values()
                tier_default_index = tier_options.index(ClientTiers.get_default())
                client_tier = st.selectbox("Client Tier", options=tier_options, index=tier_default_index)
                hourly_rate = st.number_input("Hourly Rate (R$)", value=0.0, min_value=0.0)
            
            if st.form_submit_button(UIConstants.CREATE_BUTTON + " Client", use_container_width=True):
                # CSRF Protection
                if csrf_field and security_manager:
                    csrf_token_value = st.session_state.get("csrf_create_client", "")
                    csrf_valid, csrf_error = security_manager.require_csrf_protection(
                        csrf_form_id, csrf_token_value
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
                    'client_key': client_key,
                    'name': name,
                    'description': description,
                    'industry': industry,
                    'company_size': company_size,
                    'primary_contact_name': primary_contact_name,
                    'primary_contact_email': primary_contact_email,
                    'primary_contact_phone': primary_contact_phone,
                    'status': status,
                    'client_tier': client_tier,
                    'hourly_rate': hourly_rate
                }
                
                # Security validation
                if validate_form:
                    security_valid, security_errors = validate_form(raw_data)
                    if not security_valid:
                        for error in security_errors:
                            st.error(f"🔒 Security: {error}")
                        return
                
                # Sanitize data for security
                client_data = create_safe_client(raw_data) if create_safe_client else raw_data
                
                is_valid, errors = validate_client_data(client_data)
                
                if is_valid:
                    # Check uniqueness
                    existing_clients_result = db_manager.get_clients(include_inactive=True)
                    existing_clients = existing_clients_result.get("data", []) if isinstance(existing_clients_result, dict) else []
                    
                    if not validate_email_uniqueness(primary_contact_email, existing_clients):
                        st.error(UIConstants.ERROR_DUPLICATE)
                    elif not validate_client_key_uniqueness(client_key, existing_clients):
                        st.error(UIConstants.ERROR_DUPLICATE)
                    else:
                        # Check rate limit for database write
                        db_rate_allowed, db_rate_error = check_rate_limit("db_write") if check_rate_limit else (True, None)
                        if not db_rate_allowed:
                            st.error(f"🚦 Database {db_rate_error}")
                            return
                        
                        # Create client
                        client_id = db_manager.create_client(
                            client_key=client_key,
                            name=name,
                            description=description,
                            industry=industry,
                            company_size=company_size,
                            primary_contact_name=primary_contact_name,
                            primary_contact_email=primary_contact_email,
                            status=status,
                            client_tier=client_tier,
                            hourly_rate=hourly_rate
                        )
                        
                        if client_id:
                            st.success(ErrorMessages.CLIENT_CREATE_SUCCESS)
                            st.rerun()
                        else:
                            st.error(
                                ErrorMessages.CLIENT_CREATE_ERROR.format(
                                    error="Failed to create client"
                                )
                            )
                else:
                    for error in errors:
                        st.error(
                            ErrorMessages.LOADING_ERROR.format(
                                entity="client", error=error
                            )
                        )


@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def render_clients_page():
    """Render the main clients management page."""
    # Initialize page and validate dependencies
    init_result = _initialize_clients_page()
    if "error" in init_result:
        return init_result
    
    # Setup database connection
    db_manager = _setup_database_connection()
    if db_manager is None:
        return {"error": "database_setup_failed"}
    
    # Render filters and get filter values
    filter_values = _render_client_filters()
    
    # Render create client form
    render_create_client_form(db_manager)
    st.markdown("---")
    
    # Load and display clients
    return _load_and_display_clients(db_manager, filter_values)


def _initialize_clients_page():
    """Initialize page, check dependencies and authentication."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    if not DATABASE_UTILS_AVAILABLE:
        st.error(
            ErrorMessages.LOADING_ERROR.format(
                entity="database utilities", error="not available"
            )
        )
        return {"error": "Database utilities not available"}
    
    # TEMPORARY BYPASS FOR TESTING - Remove in production
    # Initialize protected page with authentication
    # current_user = init_protected_page("👥 Client Management")
    # if not current_user:
    #     return {"error": "Authentication required"}
    
    # Temporary mock user for testing
    from streamlit_extension.auth.user_model import User, UserRole
    current_user = User(
        id=1,
        username="test_user",
        email="test@example.com", 
        role=UserRole.ADMIN,
        is_active=True
    )
    st.title("👥 Client Management")
    st.warning("🧪 DEVELOPMENT MODE - Authentication bypassed")
    
    # Check rate limit for page load
    page_rate_allowed, page_rate_error = check_rate_limit("page_load") if check_rate_limit else (True, None)
    if not page_rate_allowed:
        st.error(f"🚦 {page_rate_error}")
        st.info("Please wait before reloading the page.")
        return {"error": "Rate limited"}
    
    st.markdown("Manage your clients, contacts, and business relationships")
    st.markdown("---")
    
    return {"status": "initialized"}


def _setup_database_connection():
    """Setup and return database manager instance."""
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
            return None

        db_manager = safe_streamlit_operation(
            DatabaseManager,
            str(config.get_database_path()),
            default_return=None,
            operation_name="database_manager_init",
        )
        if db_manager is None:
            st.error(
                ErrorMessages.LOADING_ERROR.format(
                    entity="database connection", error="failed"
                )
            )
            return None
        
        return db_manager


def _render_client_filters():
    """Render filter controls and return filter values."""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_name = st.text_input(
            f"{UIConstants.ICON_SEARCH} Search by name",
            placeholder="Type client name...",
        )
    
    with col2:
        status_filter_options = ["all"] + StatusValues.get_all_values()
        status_filter = st.selectbox(
            "Status Filter",
            options=status_filter_options,
            index=0,
        )
    
    with col3:
        if ClientTiers:
            tier_filter_options = ["all"] + ClientTiers.get_all_values()
        else:
            tier_filter_options = ["all", "basic", "standard", "premium", "enterprise"]
        tier_filter = st.selectbox("Tier Filter",
            options=tier_filter_options,
            index=0
        )
    
    return {
        "search_name": search_name,
        "status_filter": status_filter,
        "tier_filter": tier_filter
    }


def _load_and_display_clients(db_manager, filter_values):
    """Load clients from database, apply filters and display results."""
    with streamlit_error_boundary("client_loading"):
        # Check rate limit for database read
        db_read_allowed, db_read_error = check_rate_limit("db_read") if check_rate_limit else (True, None)
        if not db_read_allowed:
            st.error(f"🚦 Database {db_read_error}")
            return {"error": "Database rate limited"}

        # Load all clients
        clients_result = safe_streamlit_operation(
            db_manager.get_clients,
            include_inactive=True,
            default_return={},
            operation_name="get_clients",
        )
        all_clients = clients_result.get("data", []) if isinstance(clients_result, dict) else []

        if not all_clients:
            st.info(ErrorMessages.NO_ITEMS_FOUND.format(entity="clients"))
            return {"status": "no_clients"}

        # Apply filters
        filtered_clients = _apply_client_filters(all_clients, filter_values)
        
        # Display results
        return _display_client_results(clients_result, all_clients, filtered_clients, db_manager)


def _apply_client_filters(clients, filter_values):
    """Apply search and filter criteria to client list."""
    filtered_clients = clients
    
    # Apply name search filter
    if filter_values["search_name"]:
        search_term = filter_values["search_name"].lower()
        filtered_clients = [c for c in filtered_clients if search_term in c.get('name', '').lower()]
    
    # Apply status filter
    if filter_values["status_filter"] != "all":
        filtered_clients = [c for c in filtered_clients if c.get('status') == filter_values["status_filter"]]
    
    # Apply tier filter
    if filter_values["tier_filter"] != "all":
        filtered_clients = [c for c in filtered_clients if c.get('client_tier') == filter_values["tier_filter"]]
    
    return filtered_clients


def _display_client_results(clients_result, all_clients, filtered_clients, db_manager):
    """Display client results with count and debug info."""
    # Display results count
    total_count = clients_result.get("total", len(all_clients)) if isinstance(clients_result, dict) else len(all_clients)
    st.markdown(f"**Found {len(filtered_clients)} client(s) (of {total_count} total)**")

    if not filtered_clients:
        st.warning(ErrorMessages.NO_MATCHES_FILTER.format(entity="clients"))
        return {"status": "no_matches"}

    # Display client cards
    for client in filtered_clients:
        render_client_card(client, db_manager)

    # Optional debug information
    if st.session_state.get("show_debug_info", False):
        with st.expander("🔧 Error Statistics", expanded=False):
            st.json(get_error_statistics())

    return {"status": "success", "clients_count": len(filtered_clients)}


# Export the main function
__all__ = ["render_clients_page"]

# Execute when run as a Streamlit page
if __name__ == "__main__":
    if STREAMLIT_AVAILABLE:
        render_clients_page()

