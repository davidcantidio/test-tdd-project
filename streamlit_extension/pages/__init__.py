"""
📄 Pages Package - Streamlit Extension

Multi-page navigation system for TDD Framework:
- Analytics dashboard with productivity metrics
- Interactive Kanban board for task management
- Gantt chart timeline visualization
- Dedicated timer interface with TDAH support
- Comprehensive settings and configuration
"""

from importlib import import_module
from streamlit_extension.utils.exception_handler import (
    handle_streamlit_exceptions,
    streamlit_error_boundary,
    safe_streamlit_operation,
    get_error_statistics,
)


def _import_page(module_name: str, func_name: str):
    module = safe_streamlit_operation(
        import_module,
        f"{__name__}.{module_name}",
        default_return=None,
        operation_name=f"import_{module_name}",
    )
    if module and hasattr(module, func_name):
        return getattr(module, func_name), True
    return None, False


render_analytics_page, ANALYTICS_AVAILABLE = _import_page("analytics", "render_analytics_page")
render_kanban_page, KANBAN_AVAILABLE = _import_page("kanban", "render_kanban_page")
render_gantt_page, GANTT_AVAILABLE = _import_page("gantt", "render_gantt_page")
render_timer_page, TIMER_AVAILABLE = _import_page("timer", "render_timer_page")
render_settings_page, SETTINGS_AVAILABLE = _import_page("settings", "render_settings_page")
render_clients_page, CLIENTS_AVAILABLE = _import_page("clients", "render_clients_page")
render_projects_page, PROJECTS_AVAILABLE = _import_page("projects", "render_projects_page")


# Page registry for navigation
PAGE_REGISTRY = {
    "dashboard": {
        "title": "🏠 Dashboard",
        "icon": "🏠",
        "description": "Main overview with key metrics",
        "render_func": None,  # Rendered in main app
        "available": True
    },
    "analytics": {
        "title": "📈 Analytics",
        "icon": "📈",
        "description": "Productivity analytics and insights",
        "render_func": render_analytics_page,
        "available": ANALYTICS_AVAILABLE
    },
    "kanban": {
        "title": "📋 Kanban Board",
        "icon": "📋",
        "description": "Interactive task management",
        "render_func": render_kanban_page,
        "available": KANBAN_AVAILABLE
    },
    "gantt": {
        "title": "📊 Gantt Chart",
        "icon": "📊",
        "description": "Project timeline visualization",
        "render_func": render_gantt_page,
        "available": GANTT_AVAILABLE
    },
    "timer": {
        "title": "⏱️ Focus Timer",
        "icon": "⏱️",
        "description": "TDAH-optimized focus sessions",
        "render_func": render_timer_page,
        "available": TIMER_AVAILABLE
    },
    "settings": {
        "title": "⚙️ Settings",
        "icon": "⚙️",
        "description": "Configuration and preferences",
        "render_func": render_settings_page,
        "available": SETTINGS_AVAILABLE
    },
    "clients": {
        "title": "👥 Clients",
        "icon": "👥",
        "description": "Client management and contacts",
        "render_func": render_clients_page,
        "available": CLIENTS_AVAILABLE
    },
    "projects": {
        "title": "📁 Projects",
        "icon": "📁",
        "description": "Project management and tracking",
        "render_func": render_projects_page,
        "available": PROJECTS_AVAILABLE
    }
}


def get_available_pages():
    """Get list of available pages for navigation."""
    return {
        page_id: page_info 
        for page_id, page_info in PAGE_REGISTRY.items() 
        if page_info["available"]
    }


def render_page(page_id: str):
    """Render a specific page by ID."""
    if page_id not in PAGE_REGISTRY:
        return {"error": f"Unknown page: {page_id}"}
    
    page_info = PAGE_REGISTRY[page_id]
    
    if not page_info["available"]:
        return {"error": f"Page '{page_id}' is not available"}
    
    render_func = page_info["render_func"]
    if render_func:
        return render_func()
    else:
        return {"error": f"No render function for page: {page_id}"}


__all__ = [
    "render_analytics_page",
    "render_kanban_page", 
    "render_gantt_page",
    "render_timer_page",
    "render_settings_page",
    "render_clients_page",
    "render_projects_page",
    "PAGE_REGISTRY",
    "get_available_pages",
    "render_page",
    "ANALYTICS_AVAILABLE",
    "KANBAN_AVAILABLE",
    "GANTT_AVAILABLE", 
    "TIMER_AVAILABLE",
    "SETTINGS_AVAILABLE",
    "CLIENTS_AVAILABLE",
    "PROJECTS_AVAILABLE"
]