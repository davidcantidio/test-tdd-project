"""
📊 Gantt Chart Page

Visual project timeline and scheduling:
- Interactive Gantt chart visualization
- Epic and task timeline tracking
- Milestone and deadline management
- Progress tracking over time
- Resource allocation views
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# --- Path bootstrap (apenas para execução direta fora do Streamlit) -----------
sys.path.append(str(Path(__file__).resolve().parents[2]))

# --- Imports tolerantes --------------------------------------------------------
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False  # type: ignore
    st = None  # type: ignore

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.figure_factory as ff
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False  # type: ignore
    px = go = make_subplots = ff = None  # type: ignore

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False  # type: ignore
    pd = None  # type: ignore

# --- Dependências locais -------------------------------------------------------
try:
    # Config & DB (usar assinatura consistente com Analytics)
    from streamlit_extension.config import load_config
    from streamlit_extension.utils.database import DatabaseManager
    from streamlit_extension.utils.security import (
        check_rate_limit,  # pode ser None em fallback
    )
    from streamlit_extension.utils.exception_handler import (
        handle_streamlit_exceptions,
        streamlit_error_boundary,
        safe_streamlit_operation,
        get_error_statistics,
    )
    DB_STACK_AVAILABLE = True
except ImportError:
    load_config = DatabaseManager = None  # type: ignore
    handle_streamlit_exceptions = lambda **_: (  # type: ignore
        (lambda f: f) if STREAMLIT_AVAILABLE else (lambda f: f)
    )
    def streamlit_error_boundary(_name: str):  # type: ignore
        def _decorator(fn):
            def _inner(*a, **k):
                return fn(*a, **k)
            return _inner
        return _decorator
    def safe_streamlit_operation(fn, *a, default_return=None, **k):  # type: ignore
        try:
            return fn(*a, **k)
        except Exception:
            return default_return
    def get_error_statistics():  # type: ignore
        return {"errors": []}
    check_rate_limit = None  # type: ignore
    DB_STACK_AVAILABLE = False

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

# --- (Opcional) Gantt tracker especializado -----------------------------------
try:
    from gantt_tracker import GanttTracker  # type: ignore
    GANTT_TRACKER_AVAILABLE = True
except ImportError:
    GANTT_TRACKER_AVAILABLE = False
    GanttTracker = None  # type: ignore


# ==============================================================================
# Página
# ==============================================================================

@require_auth()
@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def render_gantt_page() -> Optional[Dict[str, Any]]:
    """Entrada principal da página Gantt."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}

    init_protected_page("📊 Gantt Chart - Project Timeline", layout="wide")
    st.title("📊 Gantt Chart - Project Timeline")
    st.markdown("---")

    if not _check_dependencies():
        return {"error": "Missing dependencies"}

    if not _check_rate_limit("page_load"):
        return {"error": "Rate limited"}

    db = _init_db()
    if not db:
        return {"error": "DB unavailable"}

    _render_sidebar()

    with streamlit_error_boundary("gantt_data_loading"):
        with st.spinner("Loading project data..."):
            data = _load_gantt_data(db)

    if not data or not data.get("tasks"):
        st.warning("📝 No project data available for timeline view.")
        _render_setup_help()
        return {"warning": "no_data"}

    with streamlit_error_boundary("gantt_chart_rendering"):
        _render_gantt(data)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        with streamlit_error_boundary("epic_timeline"):
            _render_epic_cards(data)
    with col2:
        with streamlit_error_boundary("milestones"):
            _render_milestones(data)

    with st.expander("📋 Detailed Timeline Data"):
        with streamlit_error_boundary("timeline_tables"):
            _render_tables(data)

    if st.session_state.get("show_debug_info", False):
        with st.expander("🔧 Error Statistics", expanded=False):
            st.json(get_error_statistics())
    return data


# ==============================================================================
# UI Helpers
# ==============================================================================

def _check_dependencies() -> bool:
    missing = []
    if not PLOTLY_AVAILABLE:
        missing.append("plotly")
    if not DB_STACK_AVAILABLE:
        missing.append("database utils")
    if missing:
        st.error(f"❌ Missing dependencies: {', '.join(missing)}")
        st.info("Install with: `pip install plotly pandas`")
        return False
    return True


def _check_rate_limit(bucket: str) -> bool:
    allowed, err = (check_rate_limit(bucket) if check_rate_limit else (True, None))
    if not allowed:
        st.error(f"🚦 {err}")
        st.info("Please wait before reloading the page.")
        return False
    return True


def _init_db() -> Optional[DatabaseManager]:  # type: ignore[name-defined]
    """Inicializa DatabaseManager com assinatura alinhada ao Analytics."""
    with streamlit_error_boundary("database_initialization"):
        cfg = safe_streamlit_operation(load_config, default_return=None, operation_name="load_config")
        if not cfg:
            st.error("❌ Configuration loading failed")
            return None
        db = safe_streamlit_operation(
            DatabaseManager,
            framework_db_path=str(cfg.get_database_path()),
            timer_db_path=str(cfg.get_timer_database_path()),
            default_return=None,
            operation_name="database_manager_init",
        )
        if not db:
            st.error("❌ Database connection failed")
        return db


def _render_sidebar() -> None:
    st.sidebar.markdown("## 📊 Chart Settings")

    st.session_state.gantt_view_mode = st.sidebar.selectbox(
        "View Mode", ["Epic View", "Task View", "Combined View"], index=2
    )

    st.sidebar.markdown("## 🎨 Display")
    st.session_state.gantt_show_progress = st.sidebar.checkbox(
        "Show Progress Bars", value=st.session_state.get("gantt_show_progress", True)
    )
    st.session_state.gantt_show_milestones = st.sidebar.checkbox(
        "Show Milestones", value=st.session_state.get("gantt_show_milestones", True)
    )
    st.session_state.gantt_color_by = st.sidebar.selectbox(
        "Color By", ["Epic", "Status", "TDD Phase", "Priority"], index=0
    )

    st.sidebar.markdown("## 📁 Grouping")
    st.session_state.gantt_group_by = st.sidebar.selectbox(
        "Group Tasks By", ["Epic", "Status", "TDD Phase", "None"], index=0
    )


# ==============================================================================
# Data
# ==============================================================================

def _load_gantt_data(db) -> Dict[str, Any]:
    """Carrega dados via GanttTracker (se disponível) ou via DB."""
    if GANTT_TRACKER_AVAILABLE:
        data = safe_streamlit_operation(lambda: GanttTracker().generate_gantt_data(), default_return=None)
        if data:
            return data
        st.warning("⚠️ Gantt tracker failed. Using database fallback.")

    if not _check_rate_limit("db_read"):
        return {"tasks": [], "epics": []}

    epics = db.get_epics()
    tasks = db.get_tasks()

    gantt_tasks: List[Dict[str, Any]] = []
    for t in tasks:
        start = _parse_date(t.get("created_at"))
        end = _parse_date(t.get("completed_at"))

        if not end:
            est = t.get("estimate_minutes", 60) or 60
            start = start or datetime.now()
            end = start + timedelta(minutes=est)

        gantt_tasks.append({
            "id": t.get("id"),
            "title": t.get("title", "Untitled Task"),
            "epic_name": t.get("epic_name", "No Epic"),
            "status": (t.get("status") or "todo").lower(),
            "tdd_phase": (t.get("tdd_phase") or "").lower(),
            "priority": t.get("priority", 2),
            "start_date": start,
            "end_date": end,
            "progress": _progress_from_status(t.get("status")),
            "estimate_minutes": t.get("estimate_minutes", 60),
            "description": t.get("description", ""),
        })

    gantt_epics: List[Dict[str, Any]] = []
    for e in epics:
        e_tasks = [x for x in gantt_tasks if x["epic_name"] == e.get("name")]
        if not e_tasks:
            continue

        e_start = min([x["start_date"] for x in e_tasks if x["start_date"]], default=datetime.now())
        e_end = max([x["end_date"] for x in e_tasks if x["end_date"]], default=datetime.now())

        gantt_epics.append({
            "id": e.get("id"),
            "name": e.get("name", "Untitled Epic"),
            "status": (e.get("status") or "planning").lower(),
            "start_date": e_start,
            "end_date": e_end,
            "progress": sum(x["progress"] for x in e_tasks) / max(len(e_tasks), 1),
            "points_earned": e.get("points_earned", 0),
            "task_count": len(e_tasks),
        })

    return {"tasks": gantt_tasks, "epics": gantt_epics, "generated_at": datetime.now()}


# ==============================================================================
# Render
# ==============================================================================

def _render_gantt(data: Dict[str, Any]) -> None:
    st.markdown("### 🗂️ Project Timeline")

    mode = st.session_state.get("gantt_view_mode", "Combined View")
    if mode == "Epic View":
        _render_epic_gantt(data["epics"])
    elif mode == "Task View":
        _render_task_gantt(data["tasks"])
    else:
        _render_combined_gantt(data)


def _render_epic_gantt(epics: List[Dict[str, Any]]) -> None:
    if not (epics and PLOTLY_AVAILABLE and PANDAS_AVAILABLE):
        st.info("No epic data available for timeline view")
        return

    df = pd.DataFrame([{
        "Task": e["name"],
        "Start": e["start_date"],
        "Finish": e["end_date"],
        "Resource": e["status"],
        "Progress": e["progress"],
        "Description": f"Tasks: {e['task_count']}, Points: {e['points_earned']}",
    } for e in epics])

    fig = safe_streamlit_operation(
        ff.create_gantt, df,
        colors=_status_colors(),
        index_col="Resource",
        show_colorbar=True,
        group_tasks=True,
        showgrid_x=True,
        showgrid_y=True,
        title="Epic Timeline",
        default_return=None,
    )
    if fig:
        fig.update_layout(
            height=max(400, len(epics) * 40),
            xaxis_title="Timeline",
            yaxis_title="Epics",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        _render_fallback_list(epics, "Epic")


def _render_task_gantt(tasks: List[Dict[str, Any]]) -> None:
    if not (tasks and PLOTLY_AVAILABLE and PANDAS_AVAILABLE):
        st.info("No task data available for timeline view")
        return

    recent = sorted(tasks, key=lambda x: x["start_date"], reverse=True)[:20]
    color_by = st.session_state.get("gantt_color_by", "Epic")
    key = color_by.lower().replace(" ", "_")

    df = pd.DataFrame([{
        "Task": (t["title"][:30] + "...") if len(t["title"]) > 30 else t["title"],
        "Start": t["start_date"],
        "Finish": t["end_date"],
        "Resource": str(t.get(key, "Unknown")),
        "Progress": t["progress"],
        "Description": f"Epic: {t['epic_name']}, Status: {t['status']}",
    } for t in recent])

    colors = _dynamic_colors([t.get(key, "Unknown") for t in recent])
    fig = safe_streamlit_operation(
        ff.create_gantt, df,
        colors=colors,
        index_col="Resource",
        show_colorbar=True,
        group_tasks=True,
        showgrid_x=True,
        showgrid_y=True,
        title=f"Task Timeline (Recent 20, Colored by {color_by})",
        default_return=None,
    )
    if fig:
        fig.update_layout(
            height=max(600, len(recent) * 25),
            xaxis_title="Timeline",
            yaxis_title="Tasks",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        _render_fallback_list(recent, "Task")


def _render_combined_gantt(data: Dict[str, Any]) -> None:
    if not (PLOTLY_AVAILABLE and PANDAS_AVAILABLE):
        st.info("Combined view requires Plotly + Pandas")
        return

    epics, tasks = data["epics"], data["tasks"]
    combined: List[Dict[str, Any]] = []

    for e in epics:
        combined.append({
            "Task": f"📊 {e['name']}",
            "Start": e["start_date"],
            "Finish": e["end_date"],
            "Resource": "Epic",
            "Progress": e["progress"],
            "Type": "Epic",
            "Description": f"{e['task_count']} tasks • {e['points_earned']} pts",
        })

    prio = [t for t in tasks if t["priority"] == 1 or t["status"] == "in_progress"]
    prio = sorted(prio, key=lambda x: (x["priority"], x["start_date"]))[:10]
    for t in prio:
        combined.append({
            "Task": f"   └─ {t['title'][:25]}{'...' if len(t['title']) > 25 else ''}",
            "Start": t["start_date"],
            "Finish": t["end_date"],
            "Resource": t["status"],
            "Progress": t["progress"],
            "Type": "Task",
            "Description": f"{t['epic_name']} • {t['status']}",
        })

    df = pd.DataFrame(combined)
    colors = {"Epic": "#1f77b4", "todo": "#ff7f0e", "in_progress": "#ffbb78", "completed": "#2ca02c"}

    fig = safe_streamlit_operation(
        ff.create_gantt, df,
        colors=colors,
        index_col="Resource",
        show_colorbar=True,
        group_tasks=True,
        showgrid_x=True,
        showgrid_y=True,
        title="Combined Project Timeline (Epics + Priority Tasks)",
        default_return=None,
    )
    if fig:
        fig.update_layout(
            height=max(500, len(combined) * 30),
            xaxis_title="Timeline",
            yaxis_title="Items",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        _render_fallback_combined(data)


def _render_epic_cards(data: Dict[str, Any]) -> None:
    st.markdown("### 📋 Epic Timeline Overview")
    epics = data.get("epics", [])
    if not epics:
        st.info("No epics available")
        return

    for e in epics[:5]:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{e['name']}**")
            st.progress(min(max(e["progress"] / 100, 0), 1))
            duration = e["end_date"] - e["start_date"]
            st.caption(f"Duration: {duration.days} days")
        with col2:
            st.metric("Progress", f"{e['progress']:.0f}%")
            st.caption(f"Status: {e['status']}")
        with col3:
            st.metric("Tasks", e["task_count"])
            st.metric("Points", e["points_earned"])


def _render_milestones(data: Dict[str, Any]) -> None:
    st.markdown("### 🎯 Milestones & Deadlines")
    items = []
    for e in data.get("epics", []):
        if e["status"] == "completed":
            items.append({"name": f"✅ {e['name']} Completed", "date": e["end_date"], "type": "done",
                          "description": f"{e['task_count']} tasks • {e['points_earned']} pts"})
        else:
            items.append({"name": f"🎯 {e['name']} Target", "date": e["end_date"], "type": "upcoming",
                          "description": "Target completion date"})
    items.sort(key=lambda x: x["date"])

    if not items:
        st.info("No milestones available")
        return

    today = datetime.now()
    for m in items[:8]:
        diff = (m["date"] - today).days
        status = "🟢" if diff < 0 else ("🟡" if diff == 0 else ("🔴" if diff <= 7 else "🔵"))
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"{status} **{m['name']}**")
            st.caption(m["description"])
        with col2:
            st.markdown(f"**{m['date'].strftime('%Y-%m-%d')}**")
            st.caption("Today" if diff == 0 else (f"In {diff} days" if diff > 0 else f"{abs(diff)} days ago"))


def _render_tables(data: Dict[str, Any]) -> None:
    tab1, tab2 = st.tabs(["📊 Epic Timeline", "📋 Task Timeline"])
    with tab1:
        epics = data.get("epics", [])
        if epics and PANDAS_AVAILABLE:
            df = pd.DataFrame([{
                "Epic": e["name"],
                "Status": e["status"],
                "Start": e["start_date"].strftime("%Y-%m-%d"),
                "End": e["end_date"].strftime("%Y-%m-%d"),
                "Progress": f"{e['progress']:.1f}%",
                "Tasks": e["task_count"],
                "Points": e["points_earned"],
            } for e in epics])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No epic timeline data available")
    with tab2:
        tasks = data.get("tasks", [])[:20]
        if tasks and PANDAS_AVAILABLE:
            df = pd.DataFrame([{
                "Task": t["title"],
                "Epic": t["epic_name"],
                "Status": t["status"],
                "TDD Phase": t["tdd_phase"] or "N/A",
                "Start": t["start_date"].strftime("%Y-%m-%d"),
                "End": t["end_date"].strftime("%Y-%m-%d"),
                "Progress": f"{t['progress']:.1f}%",
                "Estimate": f"{t['estimate_minutes']}min",
            } for t in tasks])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No task timeline data available")


def _render_setup_help() -> None:
    st.info(
        "📋 **Timeline Setup Help**\n\n"
        "To see project timelines, you need:\n"
        "1) Epics with tasks • 2) Tasks with creation dates • 3) Time estimates\n\n"
        "**Quick Start:** Create epics → add tasks → track with timer."
    )
    if st.button("🔄 Refresh Data"):
        if _check_rate_limit("form_submit"):
            st.rerun()


def _render_fallback_list(items: List[Dict[str, Any]], label: str) -> None:
    st.markdown(f"### 📋 {label} Timeline (Simplified)")
    for it in items[:10]:
        name = it.get("name", it.get("title", "Unknown"))
        start = it["start_date"].strftime("%Y-%m-%d")
        end = it["end_date"].strftime("%Y-%m-%d")
        progress = max(0.0, min(100.0, it.get("progress", 0.0)))
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**{name}**")
            st.progress(progress / 100)
        with col2:
            st.markdown(f"**Start:** {start}")
            st.markdown(f"**End:** {end}")
        with col3:
            st.metric("Progress", f"{progress:.0f}%")


def _render_fallback_combined(data: Dict[str, Any]) -> None:
    st.markdown("### 📊 Combined Timeline (Simplified)")
    st.markdown("#### 📊 Epics")
    for e in data.get("epics", [])[:3]:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{e['name']}**")
            st.progress(e["progress"] / 100)
        with col2:
            st.metric("Tasks", e["task_count"])
    st.markdown("#### 📋 Priority Tasks")
    for t in data.get("tasks", [])[:5]:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{t['title']}**")
            st.caption(f"Epic: {t['epic_name']}")
        with col2:
            st.metric("Status", t["status"])


# ==============================================================================
# Utilitários
# ==============================================================================

def _parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _progress_from_status(status: Optional[str]) -> float:
    s = (status or "todo").lower()
    if s == "completed":
        return 100.0
    if s == "in_progress":
        return 50.0
    return 0.0


def _status_colors() -> Dict[str, str]:
    return {
        "planning": "#FFA500",
        "active": "#1E90FF",
        "completed": "#32CD32",
        "on_hold": "#FFD700",
        "cancelled": "#DC143C",
        "todo": "#FF7F50",
        "in_progress": "#FFD700",
        "Epic": "#1f77b4",
    }


def _dynamic_colors(values: List[Any]) -> Dict[str, str]:
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
               "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]
    uniq = list(dict.fromkeys([str(v) for v in values]))  # preserva ordem
    return {val: palette[i % len(palette)] for i, val in enumerate(uniq)}


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":
    render_gantt_page()
