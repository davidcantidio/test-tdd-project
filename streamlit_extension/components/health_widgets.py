"""
🏥 Health & Status Widgets

Health monitoring UI components for system status display.
UI-only pattern with graceful fallbacks when health services are unavailable.
"""

from typing import Dict, Any, Optional

# Graceful streamlit import
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

# Safe imports for health data sources
try:
    from ..database.health import check_health
    DATABASE_HEALTH_AVAILABLE = True
except ImportError:
    DATABASE_HEALTH_AVAILABLE = False
    def check_health() -> Dict[str, Any]:
        return {"status": "unknown"}

try:
    from ..utils.app_setup import check_services_health
    SERVICES_HEALTH_AVAILABLE = True
except ImportError:
    SERVICES_HEALTH_AVAILABLE = False
    def check_services_health() -> Dict[str, Any]:
        return {"overall": {"status": "unknown", "healthy": False}}

# Safe import for status components
try:
    from .status_components import StatusBadge, StatusConfig
    STATUS_COMPONENTS_AVAILABLE = True
except ImportError:
    STATUS_COMPONENTS_AVAILABLE = False
    StatusBadge = None
    StatusConfig = None

def get_status_badge(status: str, healthy: bool) -> str:
    if healthy:
        return "🟢"
    return "🟡" if status == "degraded" else "🔴"

def fetch_health() -> Dict[str, Any]:
    """
    Fetch health status from available sources.
    Uses same logic as streamlit_app.fetch_health() - UI-only, no reimplementation.
    """
    try:
        if SERVICES_HEALTH_AVAILABLE:
            return check_services_health()
        return {
            "database": check_health(),
            "services": {"status": "unknown"},
            "overall": {"status": "unknown", "healthy": False},
        }
    except Exception:
        return {
            "database": {"status": "unknown"},
            "services": {"status": "unknown"},
            "overall": {"status": "unknown", "healthy": False},
        }

def render_status_badge(health: Dict[str, Any]) -> None:
    """Render main health status badge with emoji and text."""
    if not STREAMLIT_AVAILABLE:
        return

    try:
        overall = health.get("overall", {}) or {}
        status = (overall.get("status") or "unknown").lower()
        healthy = bool(overall.get("healthy", False))

        badge = get_status_badge(status, healthy)
        st.markdown(f"### {badge} Status: **{status.capitalize()}**")
    except Exception:
        st.markdown("### 🔴 Status: **Unknown**")

def render_refresh_button() -> bool:
    """
    Render refresh button for health data.
    Returns True if button was clicked.
    """
    if not STREAMLIT_AVAILABLE:
        return False

    try:
        return st.button("🔄 Atualizar", use_container_width=True, key="btn_refresh_health")
    except Exception:
        return False

def clear_health_cache() -> None:
    """Clear health-related caches using same logic as streamlit_app._clear_caches()."""
    if not STREAMLIT_AVAILABLE:
        return

    try:
        if hasattr(st, "cache_data"):
            st.cache_data.clear()
        if hasattr(st, "cache_resource"):
            st.cache_resource.clear()

        st.session_state["health"] = fetch_health()

        cfg = st.session_state.get("config") if STREAMLIT_AVAILABLE else None
        if cfg and getattr(cfg, "debug_mode", False):
            logging.info("🩹 health caches cleared")

    except Exception as e:
        logging.info(f"⚠️ error clearing health cache: {e}")
        try:
            st.session_state["health"] = fetch_health()
        except Exception:
            st.session_state["health"] = {
                "overall": {"status": "unknown", "healthy": False}
            }

def render_detailed_metrics(health: Dict[str, Any]) -> None:
    """
    Render detailed health metrics (optional expansion).
    Currently renders basic database and services status.
    """
    if not STREAMLIT_AVAILABLE:
        return

    try:
        with st.expander("📊 Detailed Health Metrics", expanded=False):
            db_status = health.get("database", {})
            if db_status.get("status"):
                db_emoji = "🟢" if db_status.get("status") == "healthy" else "🔴"
                st.markdown(f"{db_emoji} **Database**: {db_status.get('status', 'unknown').capitalize()}")

            services_status = health.get("services", {})
            if services_status.get("status"):
                svc_emoji = "🟢" if services_status.get("status") == "healthy" else "🔴"
                st.markdown(f"{svc_emoji} **Services**: {services_status.get('status', 'unknown').capitalize()}")

            with st.expander("🔍 Raw Health Data", expanded=False):
                st.json(health)

    except Exception:
        st.info("Detailed metrics temporarily unavailable")

def render_health_section(show_detailed: bool = False) -> None:
    """
    Main health section renderer - UI only with graceful fallbacks.

    Args:
        show_detailed: Whether to show detailed metrics expansion
    """
    if not STREAMLIT_AVAILABLE:
        return

    try:
        health = st.session_state.get("health") or fetch_health()
        st.session_state["health"] = health

        render_status_badge(health)

        if render_refresh_button():
            clear_health_cache()
            st.rerun()

        if show_detailed:
            render_detailed_metrics(health)

    except Exception as e:
        st.info("Health temporarily unavailable")
        if st.session_state.get("show_debug_info", False):
            st.error(f"Health widget error: {str(e)}")

# Backward compatibility aliases
render_system_status = render_health_section
get_health_status = fetch_health