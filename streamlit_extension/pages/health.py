"""
🏥 Health Check Endpoint Page

Provides:
- REST-like health endpoint for orchestration
- Detailed health dashboard for administrators
- Real-time component monitoring
- Health history and trends
"""

from __future__ import annotations

from typing import Dict

from streamlit_extension.utils.health_check import HealthChecker
from streamlit_extension.utils.exception_handler import handle_streamlit_exceptions

# Authentication middleware
try:
    from streamlit_extension.auth.middleware import init_protected_page
except ImportError:
    init_protected_page = None

_health_checker = HealthChecker()


def get_health_json() -> Dict[str, object]:
    """Return JSON health status for API consumption."""

    return _health_checker.get_health_endpoint_response()


@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def render_health_endpoint() -> None:  # pragma: no cover - requires streamlit
    """Render health check endpoint for monitoring tools."""

    import streamlit as st
    
    # Initialize protected page with authentication
    current_user = init_protected_page("🏥 Health Check")
    if not current_user:
        st.error("Authentication required")
        return

    st.json(get_health_json())


@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def render_health_dashboard() -> None:  # pragma: no cover - requires streamlit
    """Render detailed health dashboard for administrators."""

    import streamlit as st
    
    # Initialize protected page with authentication
    current_user = init_protected_page("🏥 Health Dashboard")
    if not current_user:
        st.error("Authentication required")
        return

    st.title("Health Dashboard")
    data = get_health_json()
    for component in data["components"]:
        st.subheader(component["name"])
        st.write(component)
