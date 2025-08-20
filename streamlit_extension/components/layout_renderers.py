"""
🎨 Layout Renderers

Layout composition and rendering functions for complex UI sections.
Handles orchestration of multiple components and layout logic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

# Safe streamlit import
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

# Component imports with fallbacks
try:
    from .header import render_header
    HEADER_AVAILABLE = True
except ImportError:
    HEADER_AVAILABLE = False
    def render_header(now=None):
        if STREAMLIT_AVAILABLE:
            st.markdown("# 🚀 TDD Framework")

try:
    from .health_widgets import render_health_section
    HEALTH_WIDGETS_AVAILABLE = True
except ImportError:
    HEALTH_WIDGETS_AVAILABLE = False
    def render_health_section():
        if STREAMLIT_AVAILABLE:
            st.info("Health temporarily unavailable")

try:
    from .timer import TimerComponent
    TIMER_AVAILABLE = True
except ImportError:
    TIMER_AVAILABLE = False
    class TimerComponent:
        def render(self):
            if STREAMLIT_AVAILABLE:
                st.info("⏱️ Timer indisponível (fallback).")

try:
    from .dashboard_widgets import ProductivityHeatmap, NotificationToast
    from .fallback_components import NotificationData
    WIDGETS_AVAILABLE = True
except ImportError:
    WIDGETS_AVAILABLE = False
    
    class ProductivityHeatmap:
        @staticmethod
        def render(activity_data=None, **kwargs):
            if STREAMLIT_AVAILABLE:
                st.write("🗓️ Heatmap indisponível.")
    
    class NotificationToast:
        @staticmethod
        def show(notification=None, **kwargs):
            if STREAMLIT_AVAILABLE:
                st.info("🔔 Notificações indisponíveis.")
    
    class NotificationData:
        def __init__(self, title="", message="", type="info", timestamp=None):
            self.title = title
            self.message = message
            self.type = type
            self.timestamp = timestamp or datetime.now()

# Data providers
try:
    from .data_providers import fetch_tasks
    DATA_PROVIDERS_AVAILABLE = True
except ImportError:
    DATA_PROVIDERS_AVAILABLE = False
    def fetch_tasks(epic_id: Any) -> List[Dict[str, Any]]:
        return []

# Exception handling
try:
    from ..utils.exception_handler import streamlit_error_boundary
    EXCEPTION_HANDLER_AVAILABLE = True
except ImportError:
    EXCEPTION_HANDLER_AVAILABLE = False
    
    class streamlit_error_boundary:
        def __init__(self, operation_name: str):
            self.name = operation_name
        def __enter__(self): 
            return self
        def __exit__(self, exc_type, exc, tb): 
            return False

logger = logging.getLogger(__name__)

# === LAYOUT RENDERERS =========================================================

def render_topbar(user: Optional[Dict[str, Any]]) -> None:
    """
    Render the top bar with header and system status.
    
    Args:
        user: Current user information dict
    """
    if not STREAMLIT_AVAILABLE:
        return
    
    try:
        # Render main header
        render_header()
        
        # System status section with columns
        col1, col2 = st.columns([0.75, 0.25])
        with col2:
            render_health_section()
    
    except Exception as e:
        logger.error(f"Error rendering topbar: {e}")
        if STREAMLIT_AVAILABLE:
            st.error("⚠️ Topbar temporarily unavailable")

def render_heatmap_and_tasks(epics: List[Dict[str, Any]], selected_epic_id: Optional[Any]) -> None:
    """
    Render productivity heatmap and task selection interface.
    
    Args:
        epics: List of available epics
        selected_epic_id: Currently selected epic ID
    """
    if not STREAMLIT_AVAILABLE:
        return
    
    try:
        left, right = st.columns([1.2, 1.0])
        
        # Left column: Productivity heatmap
        with left:
            ProductivityHeatmap.render(activity_data={})
        
        # Right column: Epic selection and tasks
        with right:
            _render_epic_selection_and_tasks(epics, selected_epic_id)
    
    except Exception as e:
        logger.error(f"Error rendering heatmap and tasks: {e}")
        if STREAMLIT_AVAILABLE:
            st.error("⚠️ Heatmap and tasks temporarily unavailable")

def _render_epic_selection_and_tasks(epics: List[Dict[str, Any]], selected_epic_id: Optional[Any]) -> None:
    """
    Internal function to render epic selection dropdown and task list.
    
    Args:
        epics: List of available epics
        selected_epic_id: Currently selected epic ID
    """
    if not epics:
        st.info("Nenhum épico disponível.")
        return

    # Build epic options map (tolerant to missing fields)
    options_map: Dict[str, Any] = {}
    for e in epics:
        if not isinstance(e, dict):
            continue
        label = e.get("name") or f"Épico #{e.get('id', '?')}"
        options_map[label] = e.get("id")

    option_labels = list(options_map.keys())
    if not option_labels:
        st.info("Nenhum épico válido encontrado.")
        return

    # Find current selection
    current_label = next(
        (lbl for lbl, _id in options_map.items() if _id == selected_epic_id),
        (option_labels[0] if option_labels else None),
    )
    idx = option_labels.index(current_label) if (current_label in option_labels) else 0

    # Epic selection dropdown
    chosen_label = st.selectbox(
        "Selecione um épico",
        option_labels,
        index=idx,
        key="selected_epic_label",
    )
    
    epic_id = options_map.get(chosen_label, selected_epic_id)
    # Import session manager function to avoid direct access
    from ..utils.session_manager import set_session_value
    set_session_value("selected_epic_id", epic_id)

    # Load and display tasks
    with streamlit_error_boundary("load_tasks"):
        tasks = fetch_tasks(epic_id) if epic_id is not None else []

    _render_task_list(tasks)

def _render_task_list(tasks: List[Dict[str, Any]]) -> None:
    """
    Render the task list for the selected epic.
    
    Args:
        tasks: List of tasks to display
    """
    st.markdown("#### Tarefas")
    
    if not tasks:
        st.caption("Nenhuma tarefa para este épico.")
        return

    # Display up to 20 tasks
    for t in tasks[:20]:
        title = t.get("title") or "(sem título)"
        status = t.get("status") or "todo"
        est = t.get("estimate_minutes")
        
        # Format estimate safely
        try:
            est_str = f"{int(est)} min" if est is not None else "—"
        except (ValueError, TypeError):
            est_str = "—"
        
        st.write(f"- **{title}** · _{status}_ · ⏱ {est_str}")

def render_timer_and_notifications() -> None:
    """
    Render timer component and notifications section in two columns.
    """
    if not STREAMLIT_AVAILABLE:
        return
    
    try:
        c1, c2 = st.columns([0.65, 0.35])
        
        # Left column: Timer
        with c1:
            st.markdown("### ⏱️ Foco")
            from ..utils.session_manager import get_session_value, set_session_value
            timer = get_session_value("timer")
            if timer and hasattr(timer, "render"):
                timer.render()
            else:
                # Fallback timer creation
                timer = TimerComponent()
                set_session_value("timer", timer)
                timer.render()
        
        # Right column: Notifications
        with c2:
            st.markdown("### 🔔 Notificações")
            NotificationToast.show(
                NotificationData(
                    title="Notifications",
                    message="No new notifications",
                    type="info",
                    timestamp=datetime.now(),
                )
            )
    
    except Exception as e:
        logger.error(f"Error rendering timer and notifications: {e}")
        if STREAMLIT_AVAILABLE:
            st.error("⚠️ Timer and notifications temporarily unavailable")

# === LAYOUT UTILITIES =========================================================

def create_two_column_layout(left_ratio: float = 0.5) -> tuple:
    """
    Create a two-column layout with specified ratio.
    
    Args:
        left_ratio: Ratio for left column (0.0 to 1.0)
    
    Returns:
        Tuple of (left_column, right_column)
    """
    if not STREAMLIT_AVAILABLE:
        return None, None
    
    right_ratio = 1.0 - left_ratio
    return st.columns([left_ratio, right_ratio])

def create_three_column_layout(ratios: List[float] = None) -> tuple:
    """
    Create a three-column layout with specified ratios.
    
    Args:
        ratios: List of ratios for columns, defaults to [1/3, 1/3, 1/3]
    
    Returns:
        Tuple of (col1, col2, col3)
    """
    if not STREAMLIT_AVAILABLE:
        return None, None, None
    
    if ratios is None:
        ratios = [1/3, 1/3, 1/3]
    
    return st.columns(ratios)

def render_section_header(title: str, icon: str = "", help_text: str = None) -> None:
    """
    Render a standardized section header.
    
    Args:
        title: Section title
        icon: Optional icon emoji
        help_text: Optional help text tooltip
    """
    if not STREAMLIT_AVAILABLE:
        return
    
    header_text = f"{icon} {title}" if icon else title
    
    if help_text:
        st.markdown(f"### {header_text}", help=help_text)
    else:
        st.markdown(f"### {header_text}")

def render_info_card(title: str, content: str, type: str = "info") -> None:
    """
    Render an information card with specified type.
    
    Args:
        title: Card title
        content: Card content
        type: Card type ("info", "success", "warning", "error")
    """
    if not STREAMLIT_AVAILABLE:
        return
    
    if type == "success":
        st.success(f"**{title}**\n\n{content}")
    elif type == "warning":
        st.warning(f"**{title}**\n\n{content}")
    elif type == "error":
        st.error(f"**{title}**\n\n{content}")
    else:
        st.info(f"**{title}**\n\n{content}")

# === LAYOUT HEALTH CHECK ======================================================

def check_layout_renderer_health() -> Dict[str, Any]:
    """Check health of layout renderer dependencies."""
    return {
        "streamlit_available": STREAMLIT_AVAILABLE,
        "header_available": HEADER_AVAILABLE,
        "health_widgets_available": HEALTH_WIDGETS_AVAILABLE,
        "timer_available": TIMER_AVAILABLE,
        "widgets_available": WIDGETS_AVAILABLE,
        "data_providers_available": DATA_PROVIDERS_AVAILABLE,
        "exception_handler_available": EXCEPTION_HANDLER_AVAILABLE,
        "status": "healthy" if all([
            STREAMLIT_AVAILABLE,
            HEADER_AVAILABLE,
            HEALTH_WIDGETS_AVAILABLE,
            DATA_PROVIDERS_AVAILABLE
        ]) else "degraded"
    }

# === EXPORTS ==================================================================

__all__ = [
    # Main layout renderers
    "render_topbar",
    "render_heatmap_and_tasks", 
    "render_timer_and_notifications",
    
    # Layout utilities
    "create_two_column_layout",
    "create_three_column_layout",
    "render_section_header",
    "render_info_card",
    
    # Health check
    "check_layout_renderer_health",
]