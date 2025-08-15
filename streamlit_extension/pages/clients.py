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
    from streamlit_extension.config import load_config
    DATABASE_UTILS_AVAILABLE = True
except ImportError:
    DATABASE_UTILS_AVAILABLE = False
    DatabaseManager = validate_client_data = load_config = None


def render_client_card(client: Dict[str, Any], db_manager: DatabaseManager):
    """Render an individual client card."""
    if not STREAMLIT_AVAILABLE:
        return
    
    with st.container():
        # Card header with status indicator
        status_colors = {
            "active": "🟢",
            "inactive": "🟡", 
            "suspended": "🔴",
            "archived": "⚫"
        }
        status_emoji = status_colors.get(client.get("status", "active"), "⚪")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"### {status_emoji} {client['name']}")
            st.caption(f"**Key:** {client.get('client_key', 'N/A')} | **Tier:** {client.get('client_tier', 'standard').title()}")
        
        with col2:
            if st.button("✏️ Edit", key=f"edit_client_{client['id']}", use_container_width=True):
                st.session_state[f"edit_client_{client['id']}"] = True
                st.rerun()
        
        with col3:
            if st.button("🗑️ Delete", key=f"delete_client_{client['id']}", use_container_width=True):
                st.session_state[f"delete_client_{client['id']}"] = True
                st.rerun()
        
        # Client details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if client.get('description'):
                st.markdown(f"**Description:** {client['description']}")
            
            # Contact information
            if client.get('primary_contact_name') or client.get('primary_contact_email'):
                st.markdown("**Contact:**")
                if client.get('primary_contact_name'):
                    st.markdown(f"• **Name:** {client['primary_contact_name']}")
                if client.get('primary_contact_email'):
                    st.markdown(f"• **Email:** {client['primary_contact_email']}")
                if client.get('primary_contact_phone'):
                    st.markdown(f"• **Phone:** {client['primary_contact_phone']}")
        
        with col2:
            # Business info
            if client.get('industry'):
                st.markdown(f"**Industry:** {client['industry']}")
            if client.get('company_size'):
                st.markdown(f"**Size:** {client['company_size']}")
            if client.get('hourly_rate'):
                st.markdown(f"**Rate:** R$ {client['hourly_rate']:.2f}/h")
            
            # Project count
            try:
                projects = db_manager.get_projects(client_id=client['id'], include_inactive=True)
                project_count = len(projects) if projects else 0
                st.metric("Projects", project_count)
            except:
                st.metric("Projects", "Error")
        
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
            st.markdown("### 📝 Edit Client Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Basic Information")
                client_key = st.text_input("Client Key*", value=client.get('client_key', ''))
                name = st.text_input("Client Name*", value=client.get('name', ''))
                description = st.text_area("Description", value=client.get('description', ''))
                
                industry = st.text_input("Industry", value=client.get('industry', ''))
                company_size = st.selectbox("Company Size", 
                    options=["startup", "small", "medium", "large", "enterprise"],
                    index=["startup", "small", "medium", "large", "enterprise"].index(client.get('company_size', 'startup'))
                )
            
            with col2:
                st.markdown("#### Contact Information")
                primary_contact_name = st.text_input("Contact Name", value=client.get('primary_contact_name', ''))
                primary_contact_email = st.text_input("Contact Email*", value=client.get('primary_contact_email', ''))
                primary_contact_phone = st.text_input("Contact Phone", value=client.get('primary_contact_phone', ''))
                
                st.markdown("#### Business Settings")
                status = st.selectbox("Status", 
                    options=["active", "inactive", "suspended", "archived"],
                    index=["active", "inactive", "suspended", "archived"].index(client.get('status', 'active'))
                )
                client_tier = st.selectbox("Client Tier",
                    options=["basic", "standard", "premium", "enterprise"],
                    index=["basic", "standard", "premium", "enterprise"].index(client.get('client_tier', 'standard'))
                )
                hourly_rate = st.number_input("Hourly Rate (R$)", value=float(client.get('hourly_rate', 0.0)), min_value=0.0)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.form_submit_button("💾 Update Client", use_container_width=True):
                    # Validate data
                    client_data = {
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
                    
                    is_valid, errors = validate_client_data(client_data)
                    
                    if is_valid:
                        # Check uniqueness (excluding current client)
                        existing_clients_result = db_manager.get_clients(include_inactive=True)
                        existing_clients = existing_clients_result.get("data", []) if isinstance(existing_clients_result, dict) else []
                        
                        if not validate_email_uniqueness(primary_contact_email, existing_clients, client['id']):
                            st.error("❌ Email already exists for another client")
                        elif not validate_client_key_uniqueness(client_key, existing_clients, client['id']):
                            st.error("❌ Client key already exists")
                        else:
                            # Update client
                            success = db_manager.update_client(client['id'], **client_data)
                            if success:
                                st.success("✅ Client updated successfully!")
                                st.session_state[f"edit_client_{client['id']}"] = False
                                st.rerun()
                            else:
                                st.error("❌ Failed to update client")
                    else:
                        for error in errors:
                            st.error(f"❌ {error}")
            
            with col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
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
        try:
            projects = db_manager.get_projects(client_id=client['id'], include_inactive=True)
            if projects:
                st.error(f"⚠️ This client has {len(projects)} project(s). Deleting the client will affect these projects.")
        except:
            pass
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Delete Client", use_container_width=True):
                success = db_manager.delete_client(client['id'], soft_delete=True)
                if success:
                    st.success("✅ Client deleted successfully!")
                    st.session_state[f"delete_client_{client['id']}"] = False
                    st.rerun()
                else:
                    st.error("❌ Failed to delete client")
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state[f"delete_client_{client['id']}"] = False
                st.rerun()


def render_create_client_form(db_manager: DatabaseManager):
    """Render the create new client form."""
    if not STREAMLIT_AVAILABLE:
        return
    
    with st.expander("➕ Create New Client", expanded=False):
        with st.form("create_client_form"):
            st.markdown("### 📝 New Client Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Basic Information")
                client_key = st.text_input("Client Key*", placeholder="e.g., client_xyz")
                name = st.text_input("Client Name*", placeholder="e.g., Company ABC")
                description = st.text_area("Description", placeholder="Brief description of the client...")
                
                industry = st.text_input("Industry", placeholder="e.g., Technology")
                company_size = st.selectbox("Company Size", options=["startup", "small", "medium", "large", "enterprise"])
            
            with col2:
                st.markdown("#### Contact Information")
                primary_contact_name = st.text_input("Contact Name", placeholder="e.g., John Doe")
                primary_contact_email = st.text_input("Contact Email*", placeholder="john@company.com")
                primary_contact_phone = st.text_input("Contact Phone", placeholder="+55 (11) 99999-9999")
                
                st.markdown("#### Business Settings")
                status = st.selectbox("Status", options=["active", "inactive", "suspended", "archived"], index=0)
                client_tier = st.selectbox("Client Tier", options=["basic", "standard", "premium", "enterprise"], index=1)
                hourly_rate = st.number_input("Hourly Rate (R$)", value=0.0, min_value=0.0)
            
            if st.form_submit_button("🚀 Create Client", use_container_width=True):
                # Validate data
                client_data = {
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
                
                is_valid, errors = validate_client_data(client_data)
                
                if is_valid:
                    # Check uniqueness
                    existing_clients_result = db_manager.get_clients(include_inactive=True)
                    existing_clients = existing_clients_result.get("data", []) if isinstance(existing_clients_result, dict) else []
                    
                    if not validate_email_uniqueness(primary_contact_email, existing_clients):
                        st.error("❌ Email already exists for another client")
                    elif not validate_client_key_uniqueness(client_key, existing_clients):
                        st.error("❌ Client key already exists")
                    else:
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
                            st.success("✅ Client created successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to create client")
                else:
                    for error in errors:
                        st.error(f"❌ {error}")


def render_clients_page():
    """Render the main clients management page."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    if not DATABASE_UTILS_AVAILABLE:
        st.error("❌ Database utilities not available")
        return {"error": "Database utilities not available"}
    
    st.title("👥 Client Management")
    st.markdown("Manage your clients, contacts, and business relationships")
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
    
    # Filters and search
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_name = st.text_input("🔍 Search by name", placeholder="Type client name...")
    
    with col2:
        status_filter = st.selectbox("Status Filter", 
            options=["all", "active", "inactive", "suspended", "archived"],
            index=0
        )
    
    with col3:
        tier_filter = st.selectbox("Tier Filter",
            options=["all", "basic", "standard", "premium", "enterprise"],
            index=0
        )
    
    # Create new client form
    render_create_client_form(db_manager)
    
    st.markdown("---")
    
    # Get clients with filters
    try:
        clients_result = db_manager.get_clients(include_inactive=True)
        all_clients = clients_result.get("data", []) if isinstance(clients_result, dict) else []
        
        if not all_clients:
            st.info("📝 No clients found. Create your first client using the form above!")
            return {"status": "no_clients"}
        
        # Apply filters
        filtered_clients = all_clients
        
        if search_name:
            filtered_clients = [c for c in filtered_clients if search_name.lower() in c.get('name', '').lower()]
        
        if status_filter != "all":
            filtered_clients = [c for c in filtered_clients if c.get('status') == status_filter]
        
        if tier_filter != "all":
            filtered_clients = [c for c in filtered_clients if c.get('client_tier') == tier_filter]
        
        # Display results count
        total_count = clients_result.get("total", len(all_clients)) if isinstance(clients_result, dict) else len(all_clients)
        st.markdown(f"**Found {len(filtered_clients)} client(s) (of {total_count} total)**")
        
        if not filtered_clients:
            st.warning("🔍 No clients match your current filters.")
            return {"status": "no_matches"}
        
        # Display clients
        for client in filtered_clients:
            render_client_card(client, db_manager)
    
    except Exception as e:
        st.error(f"❌ Error loading clients: {e}")
        return {"error": f"Error loading clients: {e}"}
    
    return {"status": "success", "clients_count": len(filtered_clients)}


# Export the main function
__all__ = ["render_clients_page"]

# Execute when run as a Streamlit page
if __name__ == "__main__" or True:  # Always execute for Streamlit multipage
    if STREAMLIT_AVAILABLE:
        render_clients_page()