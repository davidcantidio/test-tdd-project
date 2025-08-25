"""
📁 Project Management Page

Comprehensive project management interface with CRUD operations:
- Project overview with card-based visualization
- Search and pagination
- Create, edit, and delete projects (via wizard/actions)
- Status and progress monitoring
"""

from __future__ import annotations

from typing import Dict, Any, List, Tuple, Union, Optional
import logging

import streamlit as st

# ===== Project imports (no sys.path hacks) =====
# --- Autenticação -------------------------------------------------------------
# Import absoluto (corrige erro crítico do relatório):
try:
    from streamlit_extension.auth.middleware import init_protected_page, require_auth
except ImportError:
    # Fallback seguro em desenvolvimento: mantém página acessível
    def init_protected_page(title: str, *, layout: str = "wide") -> None:
        st.set_page_config(page_title=title, layout=layout)

    def require_auth(role: Optional[str] = None):  # type: ignore
        def _decorator(fn):
            def _inner(*args, **kwargs):
                # Em produção real, este fallback não deve ser usado.
                return fn(*args, **kwargs)
            return _inner
        return _decorator

from streamlit_extension.auth.user_model import User
from streamlit_extension.utils.exception_handler import (
    handle_streamlit_exceptions,
    streamlit_error_boundary,
)
# Migrated to modular database API
from streamlit_extension.utils.security import sanitize_display, check_rate_limit
from streamlit_extension.config import load_config
from streamlit_extension.config.constants import StatusValues, ErrorMessages, UIConstants
from streamlit_extension.utils.app_setup import STREAMLIT_AVAILABLE

logger = logging.getLogger(__name__)


# ============================================================================ #
# Small helpers
# ============================================================================ #

def _normalize_db_list_result(result: Union[List[dict], Dict[str, Any], None]) -> List[dict]:
    """Accept both raw list or {'data': [...]} shapes defensively."""
    if result is None:
        return []
    if isinstance(result, dict):
        data = result.get("data")
        return data if isinstance(data, list) else []
    if isinstance(result, list):
        return result
    return []


def _apply_filters(
    projects: List[dict],
    search_name: str,
    status_filter: str,
) -> List[dict]:
    filtered = projects

    # name search (plain lower matching; sanitize only on display)
    if search_name:
        q = search_name.strip().lower()
        filtered = [p for p in filtered if q in str(p.get("name", "")).lower()]

    if status_filter != "all":
        filtered = [p for p in filtered if p.get("status") == status_filter]

    return filtered


def _paginate(items: List[Any], page_size: int, page_index: int) -> Tuple[List[Any], int]:
    total = len(items)
    start = page_index * page_size
    end = start + page_size
    return items[start:end], total


def _status_emoji(status: str) -> str:
    mapping = {
        'planning': '🟡',
        'in_progress': '🔵',
        'completed': '🟢',
        'on_hold': '🟠',
        'cancelled': '🔴'
    }
    return mapping.get(status, '⚪')


def _health_emoji(health: str) -> str:
    return '🟢' if health == 'green' else '🟡' if health == 'yellow' else '🔴'


def render_simple_project_card(project: Dict[str, Any]) -> None:
    """Render a simple, modern project card (display is sanitized)."""
    safe_project_name = sanitize_display(project.get('name', 'Unnamed')) if sanitize_display else project.get('name', 'Unnamed')

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

        with col1:
            st.markdown(f"### 📁 {safe_project_name}")
            if project.get('description'):
                desc = project['description']
                safe_desc = sanitize_display(desc) if sanitize_display else desc
                st.markdown(f"**Description:** {safe_desc[:160]}{'...' if len(desc) > 160 else ''}")

        with col2:
            status = str(project.get('status', 'unknown'))
            health = str(project.get('health_status', 'green'))
            st.markdown(f"**Status:** {_status_emoji(status)} {status.replace('_',' ').title()}")
            st.markdown(f"**Health:** {_health_emoji(health)} {health.title()}")

        with col3:
            if project.get('completion_percentage') is not None:
                try:
                    progress = float(project['completion_percentage'])
                    st.metric("Progress", f"{progress:.1f}%")
                except (TypeError, ValueError):
                    st.metric("Progress", "—")

        with col4:
            st.markdown("**Actions:**")
            edit_clicked = st.button("✏️ Edit", key=f"edit_{project.get('id')}", use_container_width=True)
            delete_clicked = st.button("🗑️ Delete", key=f"delete_{project.get('id')}", use_container_width=True)

            # Navigation / intents (delete flow deve ocorrer em página/endpoint próprio com CSRF)
            if edit_clicked:
                st.session_state["selected_project_id"] = project.get("id")
                from streamlit_extension.utils.session_manager import set_current_page
                set_current_page("projeto_wizard")
                st.rerun()

            if delete_clicked:
                st.session_state["delete_project_id"] = project.get("id")
                from streamlit_extension.utils.session_manager import set_current_page
                set_current_page("project_delete_confirm")
                st.rerun()


def render_wizard_call_to_action() -> None:
    """Render the wizard call-to-action section."""
    st.markdown("### 🚀 Criar Novo Projeto")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
**Experimente nosso Wizard Completo com IA!**

✨ **Visão** → objetivos e escopo  
🎯 **Épicos** → funcionalidades principais  
📖 **Stories** → user stories com story points  
✅ **Tasks** → tarefas com milestones  
👁️ **Preview** → backlog e cronograma  
"""
        )
        if st.button(
            "🚀 Criar Projeto com Wizard IA",
            type="primary",
            use_container_width=True,
            help="Wizard completo: Visão → Épicos → Stories → Tasks → Preview",
        ):
            from streamlit_extension.utils.session_manager import set_current_page
            set_current_page("projeto_wizard")
            st.rerun()
    st.markdown("---")


# ============================================================================ #
# Main Page
# ============================================================================ #

@require_auth()  # Protege a página; em dev, o fallback acima permite acesso
@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def render_projects_page() -> Dict[str, Any]:
    """Render the main projects management page with auth, filters and pagination."""
    # Configure page layout first
    st.set_page_config(
        page_title=UIConstants.PROJECTS_PAGE_TITLE or "📁 Project Management",
        layout="wide"
    )
    init_protected_page(UIConstants.PROJECTS_PAGE_TITLE or "📁 Project Management")

    # --- Rate limit (por página) ---
    allowed, msg = check_rate_limit("projects_page_load") if check_rate_limit else (True, None)
    if not allowed:
        st.error(f"🚦 {msg}")
        st.info("Please wait before reloading the page.")
        return {"error": "Rate limited"}

    # --- Title/intro ---
    st.title(f"{UIConstants.ICON_PROJECTS} Project Management")
    st.markdown("Manage your projects, timelines, and deliverables")
    st.markdown("---")

    # --- DB init (modular API) ---
    try:
        from streamlit_extension.database import queries
        # Using modular database API instead of DatabaseManager
    except Exception as e:
        logger.exception("Database module import error: %s", e)
        st.error(ErrorMessages.LOADING_ERROR.format(entity="database module", error=e))
        return {"error": f"Database module import error: {e}"}

    # --- Filters ---
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        search_name = st.text_input(
            f"{UIConstants.ICON_SEARCH} Search by name",
            placeholder="Type project name...",
        )
    with col2:
        status_options = [
            "all",
            StatusValues.PLANNING.value,
            StatusValues.IN_PROGRESS.value,
            StatusValues.COMPLETED.value,
            StatusValues.ON_HOLD.value,
            StatusValues.CANCELLED.value,
        ]
        status_filter = st.selectbox("Status Filter", options=status_options, index=0)
    with col3:
        page_size = st.selectbox("Page Size", options=[5, 10, 20, 50], index=1)

    # CTA
    render_wizard_call_to_action()

    # --- Projects load ---
    with streamlit_error_boundary("loading_projects"):
        # rate limit para leitura de DB
        ok_db, err_db = check_rate_limit("projects_db_read") if check_rate_limit else (True, None)
        if not ok_db:
            st.error(f"🚦 Database {err_db}")
            return {"error": "Database rate limited"}

        try:
            # Using modular query instead of legacy DatabaseManager
            projects_result = queries.list_all_projects()  # Equivalent to get_projects(include_inactive=True)
            all_projects = _normalize_db_list_result(projects_result)
        except Exception as e:
            logger.exception("Error loading projects: %s", e)
            st.error(ErrorMessages.PROJECT_LOAD_ERROR.format(error=e))
            return {"error": ErrorMessages.PROJECT_LOAD_ERROR.format(error=e)}

    if not all_projects:
        st.info(ErrorMessages.NO_ITEMS_FOUND.format(entity="projects"))
        return {"status": "no_projects"}

    # --- Filtering ---
    filtered_projects = _apply_filters(all_projects, search_name, status_filter)

    # --- Pagination controls ---
    total_filtered = len(filtered_projects)
    pages = max(1, (total_filtered + page_size - 1) // page_size)
    page_idx = st.number_input("Page", min_value=1, max_value=pages, value=1, step=1) - 1
    page_items, _ = _paginate(filtered_projects, page_size, page_idx)

    st.markdown(f"**Found {total_filtered} project(s)** — showing page {page_idx + 1}/{pages}")
    if not page_items:
        st.warning(ErrorMessages.NO_MATCHES_FILTER.format(entity="projects"))
        return {"status": "no_matches"}

    # --- Render list (safe boundary per card) ---
    for project in page_items:
        with streamlit_error_boundary(f"rendering_project_{project.get('id', 'unknown')}"):
            render_simple_project_card(project)

    return {"status": "success", "projects_count": total_filtered, "page": page_idx + 1, "page_size": page_size}


__all__ = ["render_projects_page"]


if __name__ == "__main__":
    if STREAMLIT_AVAILABLE:
        render_projects_page()
