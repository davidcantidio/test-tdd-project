# streamlit_extension/pages/analytics.py
"""
📊 Analytics Dashboard Page (refatorado)

Exibe métricas e análises para TDD:
- Produtividade, foco e tendências
- Insights específicos para TDAH
- Progresso por épico e tarefas
- Export CSV/JSON/Excel

Correções aplicadas:
- Remoção de sys.path hack
- Decorators no‑op seguros quando ausentes (evita crash em import)
- Normalização de user_stats (dict/list → dict)
- Filtros aplicados em memória em optimize_database_queries
- Tema gráfico por sidebar (chart_settings.theme)
- Padrões de auth e init_protected_page consistentes
"""

from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from collections.abc import Mapping

# --- Graceful imports ---------------------------------------------------------
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None  # type: ignore

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    px = go = make_subplots = None  # type: ignore

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None  # type: ignore

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

# Local imports
try:
    from streamlit_extension.utils.database import DatabaseManager
    from streamlit_extension.utils.security import (
        create_safe_client, sanitize_display, validate_form, check_rate_limit,
        security_manager,
    )
    from streamlit_extension.utils.exception_handler import (
        handle_streamlit_exceptions, streamlit_error_boundary, safe_streamlit_operation,
    )
    from streamlit_extension.config import load_config
    DATABASE_UTILS_AVAILABLE = True
except ImportError:
    DatabaseManager = load_config = None  # type: ignore
    create_safe_client = sanitize_display = validate_form = None  # type: ignore
    check_rate_limit = security_manager = None  # type: ignore

    # Fallbacks seguros: no-op decorators/utilitários
    def handle_streamlit_exceptions(*args, **kwargs):  # type: ignore
        def _wrap(func):
            return func
        return _wrap

    def streamlit_error_boundary(*args, **kwargs):  # type: ignore
        def _wrap(func):
            return func
        return _wrap

    def safe_streamlit_operation(func):  # type: ignore
        return func

    DATABASE_UTILS_AVAILABLE = False

try:
    from tdah_tools.analytics_engine import AnalyticsEngine, TDDAHAnalytics
    ANALYTICS_ENGINE_AVAILABLE = True
except ImportError:
    AnalyticsEngine = TDDAHAnalytics = None  # type: ignore
    ANALYTICS_ENGINE_AVAILABLE = False

# Performance utils
try:
    import functools
    import hashlib
    PERFORMANCE_UTILS_AVAILABLE = True
except ImportError:
    functools = hashlib = None  # type: ignore
    PERFORMANCE_UTILS_AVAILABLE = False


# ==============================
#   Cache & Performance Helpers
# ==============================

class AnalyticsCache:
    """Simple in-memory cache for analytics data with TTL support."""
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.default_ttl = 300  # 5 minutes

    def get_cache_key(self, *args, **kwargs) -> Optional[str]:
        if not PERFORMANCE_UTILS_AVAILABLE:
            return None
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.sha256(key_data.encode()).hexdigest()  # type: ignore

    def get(self, key: Optional[str], ttl: Optional[int] = None):
        if not key or key not in self.cache:
            return None
        ttl = ttl or self.default_ttl
        cache_time = self.cache_timestamps.get(key, 0)
        if time.time() - cache_time > ttl:
            self.cache.pop(key, None)
            self.cache_timestamps.pop(key, None)
            return None
        return self.cache[key]

    def set(self, key: Optional[str], value: Any) -> None:
        if not key:
            return
        self.cache[key] = value
        self.cache_timestamps[key] = time.time()

    def clear(self) -> None:
        self.cache.clear()
        self.cache_timestamps.clear()

    def size(self) -> int:
        return len(self.cache)


_analytics_cache = AnalyticsCache()


def performance_monitor(func):
    """Decorator to monitor function performance."""
    if not PERFORMANCE_UTILS_AVAILABLE:
        return func

    @functools.wraps(func)  # type: ignore
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        if STREAMLIT_AVAILABLE:
            if 'performance_metrics' not in st.session_state:
                st.session_state.performance_metrics = {}
            st.session_state.performance_metrics[func.__name__] = {
                'execution_time': execution_time,
                'timestamp': time.time(),
            }
        return result
    return wrapper


def cached_analytics_data(ttl=300):
    """Decorator for caching analytics data with configurable TTL."""
    def decorator(func):
        if not PERFORMANCE_UTILS_AVAILABLE:
            return func

        @functools.wraps(func)  # type: ignore
        def wrapper(*args, **kwargs):
            # Disable cache via settings
            if STREAMLIT_AVAILABLE and hasattr(st.session_state, 'performance_settings') and \
               not st.session_state.performance_settings.get('use_cache', True):
                return func(*args, **kwargs)

            cache_key = _analytics_cache.get_cache_key(func.__name__, *args, **kwargs)
            cached_result = _analytics_cache.get(cache_key, ttl)
            if cached_result is not None:
                return cached_result

            result = func(*args, **kwargs)
            _analytics_cache.set(cache_key, result)
            return result
        return wrapper
    return decorator


# ==============================
#   Data Access & Optimization
# ==============================

def _ensure_dict_list(data: Any) -> List[Dict[str, Any]]:
    """Ensure an iterable contains only dictionaries."""
    if not data:
        return []
    try:
        iterable = data if isinstance(data, list) else list(data)
    except Exception:
        iterable = []
    normalized: List[Dict[str, Any]] = []
    for item in iterable:
        if isinstance(item, dict):
            normalized.append(item)
        elif hasattr(item, "_asdict"):
            normalized.append(item._asdict())
        elif is_dataclass(item):
            normalized.append(asdict(item))
        elif isinstance(item, Mapping):
            normalized.append(dict(item))
        elif hasattr(item, "__dict__"):
            normalized.append(vars(item))
        elif isinstance(item, tuple):
            normalized.append({f"field_{i}": v for i, v in enumerate(item)})
    return normalized

def _normalize_user_stats(raw_stats: Any) -> Dict[str, Any]:
    """Normaliza user_stats para dict, evitando erros do tipo 'List argument must consist only of dictionaries'."""
    if isinstance(raw_stats, dict):
        return raw_stats
    if isinstance(raw_stats, list) and raw_stats:
        item = raw_stats[0]
        if isinstance(item, dict):
            return item
        if hasattr(item, "_asdict"):
            return item._asdict()
        if is_dataclass(item):
            return asdict(item)
        if isinstance(item, Mapping):
            return dict(item)
        if hasattr(item, "__dict__"):
            return vars(item)
    return {}

def optimize_database_queries(db_manager: "DatabaseManager", days: int, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Consulta dados em batches e aplica filtros em memória (até termos suporte nativo)."""
    try:
        query_results: Dict[str, Any] = {}

        if STREAMLIT_AVAILABLE:
            spinner_ctx = st.spinner("Optimizing data queries...")
        else:
            # Dummy context manager
            class _NullCtx:
                def __enter__(self): return None
                def __exit__(self, exc_type, exc, tb): return False
            spinner_ctx = _NullCtx()

        with spinner_ctx:
            # --- Sessions -----------------------------------------------------
            sessions = _ensure_dict_list(
                db_manager.get_timer_sessions(days)  # type: ignore[arg-type]
            )
            if filters:
                fr = filters.get("focus_range")
                if fr and fr != (1, 10):
                    mn, mx = fr
                    sessions = [s for s in sessions if (s.get("focus_rating") is None or mn <= s.get("focus_rating", 0) <= mx)]
                stypes = filters.get("selected_session_types")
                if stypes:
                    allowed = set(stypes)
                    sessions = [s for s in sessions if s.get("session_type") in allowed]
            query_results["timer_sessions"] = sessions

            # --- Tasks / Epics ------------------------------------------------
            tasks = _ensure_dict_list(db_manager.get_tasks())
            epics = _ensure_dict_list(db_manager.get_epics())
            if filters:
                selected_epics = set(filters.get("selected_epics") or [])
                if selected_epics:
                    tasks = [t for t in tasks if t.get("epic_name") in selected_epics]
                    epics = [e for e in epics if e.get("name") in selected_epics]
                tdd = set(filters.get("selected_tdd_phases") or [])
                if tdd:
                    tasks = [t for t in tasks if t.get("tdd_phase") in tdd]
            query_results["tasks"] = tasks
            query_results["epics"] = epics

            # --- User Stats ---------------------------------------------------
            raw_stats = db_manager.get_user_stats()
            query_results["user_stats"] = _normalize_user_stats(raw_stats)

        return query_results

    except Exception as e:
        if STREAMLIT_AVAILABLE:
            st.error(f"Database query optimization failed: {e}")
        return {
            "timer_sessions": _ensure_dict_list(db_manager.get_timer_sessions(days)),  # type: ignore[arg-type]
            "tasks": _ensure_dict_list(db_manager.get_tasks()),
            "epics": _ensure_dict_list(db_manager.get_epics()),
            "user_stats": _normalize_user_stats(db_manager.get_user_stats()),
        }


# ==============================
#   Página principal (render)
# ==============================

def _apply_chart_theme(fig) -> None:
    """Aplica template de tema se definido via sidebar."""
    if not STREAMLIT_AVAILABLE:
        return
    template = getattr(st.session_state, "chart_settings", {}).get("theme", None)
    if template:
        fig.update_layout(template=template)

@require_auth()  # Protege a página; em dev, o fallback acima permite acesso
@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def render_analytics_page():
    """Main analytics page with modular architecture."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}

    init_protected_page("📊 Analytics Dashboard", layout="wide")

    if not _check_rate_limit():
        return {"error": "Rate limited"}

    st.title("📊 Analytics Dashboard")
    st.markdown("---")

    if not _check_dependencies():
        return

    db_manager, analytics_engine = _initialize_analytics_engine()
    if not db_manager:
        return

    filters = _render_analytics_filters(db_manager)
    analytics_data = _fetch_analytics_data(db_manager, analytics_engine, filters)
    if not analytics_data:
        st.warning("📝 No data available for the selected time range.")
        return

    _render_analytics_header(analytics_data)
    _render_analytics_tabs(analytics_data)
    _render_analytics_footer(analytics_data)


def _check_rate_limit() -> bool:
    page_rate_allowed, page_rate_error = check_rate_limit("page_load") if check_rate_limit else (True, None)
    if not page_rate_allowed:
        st.error(f"🚦 {page_rate_error}")
        st.info("Please wait before reloading the page.")
        return False
    return True


def _check_dependencies() -> bool:
    missing_deps = []
    if not PLOTLY_AVAILABLE:
        missing_deps.append("plotly")
    if not PANDAS_AVAILABLE:
        missing_deps.append("pandas")
    if not DATABASE_UTILS_AVAILABLE:
        missing_deps.append("database utilities")
    if missing_deps:
        st.error(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        st.info("Install with: `pip install plotly pandas`")
        return False
    return True


def _initialize_analytics_engine():
    try:
        config = load_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path()),
        )
        if ANALYTICS_ENGINE_AVAILABLE:
            analytics_engine = TDDAHAnalytics(db_path=str(config.get_timer_database_path()))  # type: ignore[arg-type]
            st.sidebar.success("🧠 Advanced analytics enabled")
        else:
            analytics_engine = None
            st.sidebar.warning("⚠️ Basic analytics mode (install pandas, plotly for full features)")
        return db_manager, analytics_engine
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        return None, None


# ==============================
#   Sidebar & Filtros
# ==============================

def _render_analytics_filters(db_manager: "DatabaseManager") -> Dict[str, Any]:
    days = _render_time_range_selector()
    filters = _render_advanced_filters(db_manager, days)
    _render_sidebar_utilities()
    return filters


def _render_time_range_selector() -> int:
    st.sidebar.markdown("## 📅 Time Range")
    time_options = {
        "Today": 1,
        "Last 3 days": 3,
        "Last 7 days": 7,
        "Last 14 days": 14,
        "Last 30 days": 30,
        "Last 90 days": 90,
        "Last 6 months": 180,
        "Last year": 365,
        "All time": 9999,
        "Custom range": 0,
    }
    selected_range = st.sidebar.selectbox("Select time range", list(time_options.keys()), index=2)
    if selected_range == "Custom range":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("From", value=datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("To", value=datetime.now())
        days = (end_date - start_date).days + 1
        st.sidebar.caption(f"Period: {days} days")
    else:
        days = time_options[selected_range]
    return days


def _render_advanced_filters(db_manager: "DatabaseManager", days: int) -> Dict[str, Any]:
    st.sidebar.markdown("## 🔍 Advanced Filters")

    selected_epics: List[str] = []
    if st.sidebar.checkbox("Filter by Epic", value=False):
        try:
            all_epics = db_manager.get_epics()
            epic_names = [epic.get("name", "Unknown") for epic in all_epics]
            selected_epics = st.sidebar.multiselect("Select Epics", epic_names)
        except Exception:
            st.sidebar.warning("Could not load epics")

    focus_range = (1, 10)
    if st.sidebar.checkbox("Filter by Focus Level", value=False):
        focus_range = st.sidebar.slider("Focus Rating Range", min_value=1, max_value=10, value=(1, 10), step=1)

    selected_tdd_phases: List[str] = []
    if st.sidebar.checkbox("Filter by TDD Phase", value=False):
        tdd_phases = ["red", "green", "refactor"]
        selected_tdd_phases = st.sidebar.multiselect("Select TDD Phases", tdd_phases)

    selected_session_types: List[str] = []
    if st.sidebar.checkbox("Filter by Session Type", value=False):
        session_types = ["focus_session", "short_break", "long_break", "custom"]
        selected_session_types = st.sidebar.multiselect("Select Session Types", session_types)

    filters = {
        "days": days,
        "selected_epics": selected_epics,
        "focus_range": focus_range,
        "selected_tdd_phases": selected_tdd_phases,
        "selected_session_types": selected_session_types,
    }
    st.session_state.analytics_filters = filters
    return filters


def _render_sidebar_utilities():
    st.sidebar.markdown("## ⚡ Interactive Controls")
    auto_refresh = st.sidebar.checkbox("Auto-refresh every minute", value=False)
    if auto_refresh:
        if "refresh_counter" not in st.session_state:
            st.session_state.refresh_counter = 0
        if time.time() - st.session_state.get("last_refresh", 0) > 60:
            st.session_state.last_refresh = time.time()
            st.session_state.refresh_counter += 1
            st.sidebar.caption(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")
            time.sleep(1)
            st.rerun()

    if st.sidebar.button("🔄 Refresh Data", type="primary"):
        st.rerun()

    st.sidebar.markdown("## 📊 Export Options")
    export_format = st.sidebar.selectbox("Export Format", ["CSV", "JSON", "Excel"], help="Choose format for exporting analytics data")
    if st.sidebar.button("📥 Export Data"):
        _export_analytics_data(getattr(st.session_state, 'last_analytics', {}), export_format)

    st.sidebar.markdown("## 📈 Chart Settings")
    chart_theme = st.sidebar.selectbox("Chart Theme", ["plotly", "plotly_white", "plotly_dark", "presentation"], index=0)
    show_animations = st.sidebar.checkbox("Chart Animations", value=True)
    show_tooltips = st.sidebar.checkbox("Enhanced Tooltips", value=True)
    st.session_state.chart_settings = {"theme": chart_theme, "animations": show_animations, "tooltips": show_tooltips}

    st.sidebar.markdown("## ⚙️ Performance")
    use_cache = st.sidebar.checkbox("Use Data Caching", value=True, help="Cache data for faster loading")
    chart_quality = st.sidebar.selectbox("Chart Quality", ["High", "Medium", "Fast"], index=1)
    st.session_state.performance_settings = {"use_cache": use_cache, "chart_quality": chart_quality}

    if st.sidebar.checkbox("Show Performance Metrics", value=False):
        _render_performance_metrics()


# ==============================
#   Data Fetch + Header/Tabs
# ==============================

def _fetch_analytics_data(db_manager: "DatabaseManager", analytics_engine: Any, filters: Dict[str, Any]) -> Dict[str, Any]:
    days = filters.get("days", 7)
    with st.spinner("Loading analytics data..."):
        if analytics_engine:
            data = _get_enhanced_analytics_data(analytics_engine, db_manager, days)
        else:
            data = _get_analytics_data(db_manager, days)
        if filters:
            data = _apply_data_filters(data, filters)
    st.session_state.last_analytics = data
    return data


def _render_analytics_header(analytics_data: Dict[str, Any]):
    filters = getattr(st.session_state, "analytics_filters", {})
    active_filters = []
    if filters.get("selected_epics"):
        active_filters.append(f"Epics: {len(filters['selected_epics'])}")
    if filters.get("focus_range") and filters.get("focus_range") != (1, 10):
        active_filters.append(f"Focus: {filters['focus_range'][0]}-{filters['focus_range'][1]}")
    if filters.get("selected_tdd_phases"):
        active_filters.append(f"TDD: {len(filters['selected_tdd_phases'])}")
    if filters.get("selected_session_types"):
        active_filters.append(f"Sessions: {len(filters['selected_session_types'])}")
    if active_filters:
        st.info(f"🔍 **Active filters:** {' | '.join(active_filters)}")
    _render_overview_metrics(analytics_data)
    st.markdown("---")


def _render_analytics_tabs(analytics_data: Dict[str, Any]):
    col1, col2 = st.columns(2)
    with col1:
        _render_productivity_chart(analytics_data)
        _render_tdd_phase_distribution(analytics_data)
    with col2:
        _render_focus_time_chart(analytics_data)
        _render_epic_progress_chart(analytics_data)
    st.markdown("---")
    _render_tdah_insights(analytics_data)
    st.markdown("---")


def _render_analytics_footer(analytics_data: Dict[str, Any]):
    with st.expander("📋 Detailed Data"):
        _render_detailed_tables(analytics_data)


# ==============================
#   Enhanced & Basic Data
# ==============================

@cached_analytics_data(ttl=300)
@performance_monitor
def _get_enhanced_analytics_data(analytics_engine: Any, db_manager: "DatabaseManager", days: int) -> Dict[str, Any]:
    try:
        productivity_metrics = analytics_engine.generate_productivity_metrics(days)  # type: ignore[attr-defined]
        time_patterns = analytics_engine.analyze_time_patterns(days)  # type: ignore[attr-defined]
        session_data = analytics_engine.load_session_data(days)  # type: ignore[attr-defined]
        basic_data = _get_analytics_data(db_manager, days)
        enhanced_data = {
            **basic_data,
            "productivity_metrics": productivity_metrics,
            "time_patterns": time_patterns,
            "session_data": session_data,
            "analytics_engine_enabled": True,
        }
        return enhanced_data
    except Exception as e:
        st.warning(f"⚠️ Analytics engine error, falling back to basic mode: {e}")
        return _get_analytics_data(db_manager, days)


@cached_analytics_data(ttl=180)
@performance_monitor
def _get_analytics_data(db_manager: "DatabaseManager", days: int) -> Dict[str, Any]:
    filters = getattr(st.session_state, 'analytics_filters', {})
    query_results = optimize_database_queries(db_manager, days, filters)

    timer_sessions = query_results.get("timer_sessions", [])
    epics = query_results.get("epics", [])
    tasks = query_results.get("tasks", [])
    user_stats = query_results.get("user_stats", {})

    total_focus_time = sum(s.get("planned_duration_minutes", 0) for s in timer_sessions)
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]

    focus_ratings = [s.get("focus_rating") for s in timer_sessions if s.get("focus_rating")]
    avg_focus = sum(focus_ratings) / len(focus_ratings) if focus_ratings else 0

    daily_data = _calculate_daily_metrics(timer_sessions, tasks)

    return {
        "period_days": days,
        "total_sessions": len(timer_sessions),
        "total_focus_time": total_focus_time,
        "completed_tasks": len(completed_tasks),
        "average_focus_rating": avg_focus,
        "total_points": user_stats.get("total_points", 0),
        "active_epics": len([e for e in epics if e.get("status") == "active"]),
        "timer_sessions": timer_sessions,
        "epics": epics,
        "tasks": tasks,
        "daily_metrics": daily_data,
    }


def _calculate_daily_metrics(timer_sessions: List[Dict], tasks: List[Dict]) -> List[Dict]:
    daily_data = defaultdict(lambda: {
        "date": "",
        "focus_minutes": 0,
        "sessions": 0,
        "tasks_completed": 0,
        "avg_focus_rating": 0,
        "interruptions": 0,
    })

    for session in timer_sessions:
        if not session.get("started_at"):
            continue
        try:
            date_str = session["started_at"][:10]
            dd = daily_data[date_str]
            dd["date"] = date_str
            dd["focus_minutes"] += session.get("planned_duration_minutes", 0)
            dd["sessions"] += 1
            dd["interruptions"] += session.get("interruptions_count", 0)
            if session.get("focus_rating"):
                current_avg = dd["avg_focus_rating"]
                sessions_count = dd["sessions"]
                dd["avg_focus_rating"] = ((current_avg * (sessions_count - 1)) + session["focus_rating"]) / sessions_count
        except (KeyError, IndexError, ValueError):
            continue

    for task in tasks:
        if task.get("status") == "completed" and task.get("completed_at"):
            try:
                date_str = task["completed_at"][:10]
                if date_str in daily_data:
                    daily_data[date_str]["tasks_completed"] += 1
            except (KeyError, IndexError):
                continue

    return list(daily_data.values())


# ==============================
#   Overview & Charts
# ==============================

def _render_overview_metrics(analytics_data: Dict[str, Any]):
    col1, col2, col3, col4 = st.columns(4)

    engine_enabled = analytics_data.get("analytics_engine_enabled", False)
    productivity_metrics = analytics_data.get("productivity_metrics", {})

    with col1:
        if engine_enabled and productivity_metrics:
            total_time = productivity_metrics.get("total_focus_time_minutes", 0)
            efficiency_score = productivity_metrics.get("focus_efficiency_score", 0)
            delta_text = f"Efficiency: {efficiency_score:.1f}%" if efficiency_score > 0 else None
        else:
            total_time = analytics_data.get("total_focus_time", 0)
            delta_text = f"{analytics_data.get('total_sessions', 0)} sessions"
        hours = total_time // 60
        minutes = total_time % 60
        st.metric("🕐 Total Focus Time", f"{hours}h {minutes}m", delta_text)

    with col2:
        if engine_enabled and productivity_metrics:
            completed = productivity_metrics.get("tasks_completed", analytics_data.get("completed_tasks", 0))
            velocity = productivity_metrics.get("daily_velocity", 0)
            delta_text = f"Velocity: {velocity:.1f}/day" if velocity > 0 else None
        else:
            completed = analytics_data.get("completed_tasks", 0)
            avg_per_day = completed / analytics_data.get("period_days", 1) if completed > 0 else 0
            delta_text = f"{avg_per_day:.1f}/day avg"
        st.metric("✅ Tasks Completed", completed, delta_text)

    with col3:
        if engine_enabled and productivity_metrics:
            focus_rating = productivity_metrics.get("average_focus_rating", 0)
            focus_trend = productivity_metrics.get("focus_trend", "stable")
            trend_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(focus_trend, "➡️")
            delta_text = f"{trend_emoji} {focus_trend}"
        else:
            focus_rating = analytics_data.get("average_focus_rating", 0)
            delta_text = "TDAH metric"
        st.metric("🎯 Avg Focus Rating", f"{focus_rating:.1f}/10", delta_text)

    with col4:
        if engine_enabled and productivity_metrics:
            points = productivity_metrics.get("total_points", analytics_data.get("total_points", 0))
            streak = productivity_metrics.get("current_streak", 0)
            delta_text = f"🔥 {streak} day streak" if streak > 1 else f"{analytics_data.get('active_epics', 0)} active epics"
        else:
            points = analytics_data.get("total_points", 0)
            delta_text = f"{analytics_data.get('active_epics', 0)} active epics"
        st.metric("🌟 Total Points", f"{points:,}", delta_text)


def _render_productivity_chart(analytics_data: Dict[str, Any]):
    if not PLOTLY_AVAILABLE:
        st.warning("Charts require plotly installation")
        return
    st.markdown("### 📈 Daily Productivity")
    chart_data = _process_productivity_data(analytics_data)
    if chart_data.get("df") is None:
        st.info("No productivity data available")
        return
    config = {"enhanced_height": 600, "basic_height": 400}
    _display_productivity_charts(chart_data, config)
    _display_productivity_metrics(chart_data)


def _process_productivity_data(analytics_data: Dict[str, Any]) -> Dict[str, Any]:
    engine_enabled = analytics_data.get("analytics_engine_enabled", False)
    productivity_metrics = analytics_data.get("productivity_metrics", {})
    if engine_enabled and productivity_metrics:
        daily_productivity = productivity_metrics.get("daily_productivity", []) or analytics_data.get("daily_metrics", [])
        if daily_productivity and PANDAS_AVAILABLE:
            df_data = []
            for day_data in daily_productivity:
                df_data.append({
                    "date": day_data.get("date", ""),
                    "focus_minutes": day_data.get("focus_minutes", day_data.get("total_focus_time", 0)),
                    "tasks_completed": day_data.get("tasks_completed", 0),
                    "productivity_score": day_data.get("productivity_score", 0),
                    "focus_efficiency": day_data.get("focus_efficiency", 0),
                    "avg_focus_rating": day_data.get("avg_focus_rating", 0),
                })
            df = pd.DataFrame(df_data).sort_values("date")
            return {"df": df, "insights": productivity_metrics.get("insights", []), "enhanced": True}
        return {"df": None, "insights": [], "enhanced": True}

    daily_metrics = analytics_data.get("daily_metrics", [])
    if daily_metrics and PANDAS_AVAILABLE:
        df = pd.DataFrame(sorted(daily_metrics, key=lambda x: x["date"]))
        return {"df": df, "insights": [], "enhanced": False}
    return {"df": None, "insights": [], "enhanced": False}


def _display_productivity_metrics(chart_data: Dict[str, Any]):
    insights = chart_data.get("insights", [])
    if insights:
        st.markdown("#### 💡 Productivity Insights")
        for insight in insights[:3]:
            st.info(f"• {insight}")


def _display_productivity_charts(chart_data: Dict[str, Any], config: Dict[str, Any]):
    df = chart_data.get("df")
    if df is None:
        return

    if chart_data.get("enhanced"):
        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=["Focus Time & Tasks Completed", "Productivity Score & Focus Efficiency"],
            specs=[[{"secondary_y": True}], [{"secondary_y": True}]],
            vertical_spacing=0.12,
        )
        fig.add_trace(go.Bar(x=df["date"], y=df["focus_minutes"], name="Focus Minutes", marker_color="lightblue", opacity=0.7), row=1, col=1, secondary_y=False)
        fig.add_trace(go.Scatter(x=df["date"], y=df["tasks_completed"], mode="lines+markers", name="Tasks Completed", line=dict(color="orange", width=2), marker=dict(size=6)), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(x=df["date"], y=df["productivity_score"], mode="lines+markers", name="Productivity Score", line=dict(color="green", width=3), marker=dict(size=8)), row=2, col=1, secondary_y=False)
        fig.add_trace(go.Scatter(x=df["date"], y=df["focus_efficiency"], mode="lines+markers", name="Focus Efficiency %", line=dict(color="purple", width=2, dash="dash"), marker=dict(size=6)), row=2, col=1, secondary_y=True)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Focus Minutes", row=1, col=1, secondary_y=False)
        fig.update_yaxes(title_text="Tasks Completed", row=1, col=1, secondary_y=True)
        fig.update_yaxes(title_text="Productivity Score", row=2, col=1, secondary_y=False)
        fig.update_yaxes(title_text="Focus Efficiency %", row=2, col=1, secondary_y=True)
        fig.update_layout(height=config["enhanced_height"], showlegend=True, title=None)
        _apply_chart_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=df["date"], y=df["focus_minutes"], name="Focus Minutes", marker_color="lightblue", opacity=0.7), secondary_y=False)
        fig.add_trace(go.Scatter(x=df["date"], y=df["tasks_completed"], mode="lines+markers", name="Tasks Completed", line=dict(color="orange", width=2), marker=dict(size=6)), secondary_y=True)
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Focus Minutes", secondary_y=False)
        fig.update_yaxes(title_text="Tasks Completed", secondary_y=True)
        fig.update_layout(height=config["basic_height"], showlegend=True, title=None)
        _apply_chart_theme(fig)
        st.plotly_chart(fig, use_container_width=True)


def _render_focus_time_chart(analytics_data: Dict[str, Any]):
    if not PLOTLY_AVAILABLE:
        st.warning("Charts require plotly installation")
        return
    st.markdown("### ⏱️ Focus Time Analysis")
    focus_data = _aggregate_focus_time_data(analytics_data)
    if not focus_data:
        st.info("No timer sessions available")
        return
    _render_focus_trends(focus_data)
    _render_focus_summary(focus_data)
    _render_focus_patterns(focus_data)


def _aggregate_focus_time_data(analytics_data: Dict[str, Any]) -> Dict[str, Any]:
    engine_enabled = analytics_data.get("analytics_engine_enabled", False)
    time_patterns = analytics_data.get("time_patterns", {})
    if engine_enabled and time_patterns:
        hourly_focus = time_patterns.get("hourly_focus_distribution", {})
        peak_hours = time_patterns.get("peak_productivity_hours", [])
        focus_quality_by_hour = time_patterns.get("focus_quality_by_hour", {})
        hours = list(range(24))
        minutes = [hourly_focus.get(str(h), 0) for h in hours]
        focus_quality = [focus_quality_by_hour.get(str(h), 0) for h in hours]
        total_focus_time = sum(minutes)
        avg_session_quality = sum(focus_quality) / len([q for q in focus_quality if q > 0]) if any(focus_quality) else 0
        return {
            "type": "enhanced",
            "hours": hours,
            "minutes": minutes,
            "focus_quality": focus_quality,
            "peak_hours": peak_hours,
            "patterns": time_patterns.get("patterns", []),
            "total_focus_time": total_focus_time,
            "avg_session_quality": avg_session_quality,
        }

    # Basic fallback
    timer_sessions = analytics_data.get("timer_sessions", [])
    if not timer_sessions:
        return {}
    hourly_data = defaultdict(int)
    for session in timer_sessions:
        if session.get("started_at"):
            try:
                if "T" in session["started_at"]:
                    hour = int(session["started_at"].split("T")[1][:2])
                else:
                    hour = int(session["started_at"].split(" ")[1][:2])
                hourly_data[hour] += session.get("planned_duration_minutes", 0)
            except (ValueError, IndexError):
                continue
    hours = list(range(24))
    minutes = [hourly_data.get(h, 0) for h in hours]
    return {"type": "basic", "hours": hours, "minutes": minutes}


def _render_focus_summary(focus_data: Dict[str, Any]):
    if focus_data.get("type") != "enhanced":
        return
    peak_hours = focus_data.get("peak_hours", [])
    if peak_hours:
        peak_times = ", ".join([f"{h}:00" for h in peak_hours[:3]])
        st.success(f"🌟 **Peak Hours:** {peak_times}")
    st.info(f"⏱️ **Total Focus:** {focus_data.get('total_focus_time', 0):.0f} minutes")
    st.info(f"🎯 **Avg Quality:** {focus_data.get('avg_session_quality', 0):.1f}/10")


def _render_focus_trends(focus_data: Dict[str, Any]):
    hours = focus_data.get("hours", [])
    minutes = focus_data.get("minutes", [])
    if focus_data.get("type") == "enhanced":
        focus_quality = focus_data.get("focus_quality", [])
        peak_hours = focus_data.get("peak_hours", [])
        fig = make_subplots(rows=2, cols=1, subplot_titles=["Focus Time by Hour", "Focus Quality by Hour"], vertical_spacing=0.15)
        colors = ['rgba(255, 99, 132, 0.8)' if h in peak_hours else 'rgba(54, 162, 235, 0.6)' for h in hours]
        fig.add_trace(go.Bar(x=hours, y=minutes, name="Focus Minutes", marker_color=colors, text=[f"{m:.0f}min" if m > 0 else "" for m in minutes], textposition="outside"), row=1, col=1)
        fig.add_trace(go.Scatter(x=hours, y=focus_quality, mode="lines+markers", name="Focus Quality", line=dict(color="green", width=3), marker=dict(size=8, color=focus_quality, colorscale="RdYlGn", cmin=0, cmax=10)), row=2, col=1)
        fig.update_xaxes(title_text="Hour of Day", row=2, col=1, dtick=2)
        fig.update_yaxes(title_text="Minutes", row=1, col=1)
        fig.update_yaxes(title_text="Quality (1-10)", row=2, col=1, range=[0, 10])
        fig.update_layout(height=500, showlegend=False, title=None)
        _apply_chart_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig = px.bar(x=hours, y=minutes, title="Focus Time by Hour of Day", labels={"x": "Hour", "y": "Minutes"}, color=minutes, color_continuous_scale="Blues")
        fig.update_layout(height=400, showlegend=False)
        _apply_chart_theme(fig)
        st.plotly_chart(fig, use_container_width=True)


def _render_focus_patterns(focus_data: Dict[str, Any]):
    if focus_data.get("type") != "enhanced":
        return
    patterns = focus_data.get("patterns", [])
    if patterns:
        st.markdown("**💡 Time Insights:**")
        for pattern in patterns[:3]:
            st.markdown(f"• {pattern}")


def _render_tdd_phase_distribution(analytics_data: Dict[str, Any]):
    if not PLOTLY_AVAILABLE:
        st.warning("Charts require plotly installation")
        return
    tdd_data = _calculate_tdd_metrics(analytics_data)
    if not tdd_data.get("phase_counts"):
        st.info("No task data available")
        return
    st.markdown("### 🔴🟢🔵 TDD Phase Distribution")
    _render_tdd_phase_chart(tdd_data)


def _calculate_tdd_metrics(analytics_data: Dict[str, Any]) -> Dict[str, Any]:
    tasks = analytics_data.get("tasks", [])
    phase_counts = {"red": 0, "green": 0, "refactor": 0, "unknown": 0}
    for task in tasks:
        phase = task.get("tdd_phase") or "unknown"
        phase = phase.lower() if isinstance(phase, str) else "unknown"
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
    return {"phase_counts": {k: v for k, v in phase_counts.items() if v > 0}}


def _render_tdd_phase_chart(tdd_data: Dict[str, Any]):
    phase_counts = tdd_data.get("phase_counts", {})
    if not phase_counts:
        return
    colors = {"red": "#FF6B6B", "green": "#51CF66", "refactor": "#339AF0", "unknown": "#ADB5BD"}
    fig = px.pie(values=list(phase_counts.values()), names=list(phase_counts.keys()), title="Tasks by TDD Phase", color_discrete_map=colors)
    fig.update_layout(height=400)
    _apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_epic_progress_chart(analytics_data: Dict[str, Any]):
    if not PLOTLY_AVAILABLE:
        st.warning("Charts require plotly installation")
        return
    st.markdown("### 📊 Epic Progress")
    progress_data = _calculate_epic_progress(analytics_data)
    if not progress_data:
        _render_basic_epic_progress(analytics_data)
        return
    _render_progress_charts(progress_data)
    _render_progress_details(progress_data)


def _calculate_epic_progress(analytics_data: Dict[str, Any]) -> Dict[str, Any]:
    engine_enabled = analytics_data.get("analytics_engine_enabled", False)
    productivity_metrics = analytics_data.get("productivity_metrics", {})
    if engine_enabled and productivity_metrics:
        epic_analysis = productivity_metrics.get("epic_analysis", {})
        epic_performance = epic_analysis.get("epic_performance", [])
        if epic_performance and PANDAS_AVAILABLE:
            df = pd.DataFrame(epic_performance)
            return {"df": df, "analysis": epic_analysis}
    return {}


def _render_progress_charts(progress_data: Dict[str, Any]):
    df = progress_data.get("df")
    if df is None:
        return
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["Points Earned by Epic", "Epic Velocity (Tasks/Week)", "Epic Efficiency Score", "Progress vs Target"],
        specs=[[{"type": "bar"}, {"type": "bar"}], [{"type": "scatter"}, {"type": "bar"}]],
    )
    x_epic = df["epic_name"] if "epic_name" in df.columns else df.get("name", [])
    fig.add_trace(go.Bar(x=x_epic, y=df["points_earned"] if "points_earned" in df.columns else df.get("points", []), name="Points", marker_color="lightblue"), row=1, col=1)
    if "velocity" in df.columns:
        fig.add_trace(go.Bar(x=x_epic, y=df["velocity"], name="Velocity", marker_color="orange"), row=1, col=2)
    if "efficiency_score" in df.columns:
        fig.add_trace(go.Scatter(x=x_epic, y=df["efficiency_score"], mode="markers+lines", name="Efficiency", marker=dict(size=10, color=df["efficiency_score"], colorscale="RdYlGn", cmin=0, cmax=100)), row=2, col=1)
    if "progress_percentage" in df.columns:
        fig.add_trace(go.Bar(x=x_epic, y=df["progress_percentage"], name="Actual Progress", marker_color="lightgreen", opacity=0.7), row=2, col=2)
        if "target_percentage" in df.columns:
            fig.add_trace(go.Scatter(x=x_epic, y=df["target_percentage"], mode="markers+lines", name="Target", line=dict(color="red", dash="dash", width=2), marker=dict(size=8, color="red")), row=2, col=2)
    fig.update_layout(height=600, showlegend=False)
    fig.update_xaxes(tickangle=-45)
    fig.update_yaxes(title_text="Points", row=1, col=1)
    fig.update_yaxes(title_text="Tasks/Week", row=1, col=2)
    fig.update_yaxes(title_text="Efficiency %", range=[0, 100], row=2, col=1)
    fig.update_yaxes(title_text="Progress %", range=[0, 100], row=2, col=2)
    _apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_progress_details(progress_data: Dict[str, Any]):
    df = progress_data.get("df")
    if df is None or len(df) == 0:
        return
    col1, col2, col3 = st.columns(3)
    with col1:
        if "velocity" in df.columns:
            top_velocity_epic = df.loc[df["velocity"].idxmax()]
            epic_name = top_velocity_epic.get("epic_name", top_velocity_epic.get("name", "Unknown"))
            st.success(f"🚀 **Fastest Epic:** {epic_name}")
            st.caption(f"Velocity: {top_velocity_epic['velocity']:.1f} tasks/week")
    with col2:
        if "efficiency_score" in df.columns:
            most_efficient_epic = df.loc[df["efficiency_score"].idxmax()]
            epic_name = most_efficient_epic.get("epic_name", most_efficient_epic.get("name", "Unknown"))
            st.success(f"⚙️ **Most Efficient:** {epic_name}")
            st.caption(f"Efficiency: {most_efficient_epic['efficiency_score']:.1f}%")
    with col3:
        points_col = "points_earned" if "points_earned" in df.columns else ("points" if "points" in df.columns else None)
        total_points = df[points_col].sum() if points_col else 0
        avg_progress = df["progress_percentage"].mean() if "progress_percentage" in df.columns else 0
        st.metric("Total Points", f"{total_points:,}", f"Avg Progress: {avg_progress:.1f}%")


def _render_basic_epic_progress(analytics_data: Dict[str, Any]):
    epics = analytics_data.get("epics", [])
    if not epics:
        st.info("No epic data available")
        return
    epic_progress = []
    for epic in epics[:10]:
        epic_name = epic.get("name", "Unknown")
        points = epic.get("points_earned", epic.get("points", 0))
        status = epic.get("status", "unknown")
        epic_progress.append({"epic": epic_name, "points": points, "status": status})

    if epic_progress and PANDAS_AVAILABLE:
        df = pd.DataFrame(epic_progress)
        fig = px.bar(df, x="epic", y="points", color="status", title="Points by Epic", labels={"epic": "Epic", "points": "Points Earned"})
        fig.update_layout(height=400, xaxis_tickangle=-45)
        _apply_chart_theme(fig)
        st.plotly_chart(fig, use_container_width=True)


# ==============================
#   TDAH Insights
# ==============================

def _render_tdah_insights(analytics_data: Dict[str, Any]):
    st.markdown("### 🧠 TDAH Insights")

    engine_enabled = analytics_data.get("analytics_engine_enabled", False)
    session_data = analytics_data.get("session_data", {})
    time_patterns = analytics_data.get("time_patterns", {})
    productivity_metrics = analytics_data.get("productivity_metrics", {})

    if engine_enabled and session_data:
        tdah_metrics = session_data.get("tdah_metrics", {})
        focus_patterns = session_data.get("focus_patterns", {})
        interruption_analysis = session_data.get("interruption_analysis", {})
        energy_patterns = session_data.get("energy_patterns", {})

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_interruptions = interruption_analysis.get("average_per_session", 0)
            interruption_trend = interruption_analysis.get("trend", "stable")
            trend_color = "red" if interruption_trend == "increasing" else "green" if interruption_trend == "decreasing" else "blue"
            st.metric("🚫 Avg Interruptions", f"{avg_interruptions:.1f}", f"{interruption_trend}", delta_color=trend_color)

        with col2:
            avg_energy = energy_patterns.get("average_level", 0)
            energy_consistency = energy_patterns.get("consistency_score", 0)
            st.metric("⚡ Energy Level", f"{avg_energy:.1f}/10", f"Consistency: {energy_consistency:.0f}%")

        with col3:
            focus_sustainability = focus_patterns.get("sustainability_score", 0)
            optimal_session_length = focus_patterns.get("optimal_duration", 0)
            st.metric("🎯 Focus Sustainability", f"{focus_sustainability:.0f}%", f"Optimal: {optimal_session_length}min")

        with col4:
            adaptation_score = tdah_metrics.get("adaptation_score", 0)
            improvement_trend = tdah_metrics.get("improvement_trend", "stable")
            st.metric("🧠 TDAH Adaptation", f"{adaptation_score:.0f}%", improvement_trend)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📈 Focus Patterns")
            focus_distribution = focus_patterns.get("quality_distribution", {})
            if focus_distribution and PLOTLY_AVAILABLE:
                labels = list(focus_distribution.keys())
                values = list(focus_distribution.values())
                fig = px.pie(values=values, names=labels, title="Focus Quality Distribution", color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_layout(height=300)
                _apply_chart_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

            best_times = focus_patterns.get("best_performance_times", [])
            if best_times:
                st.success(f"🌟 **Best focus times:** {', '.join(best_times)}")

        with col2:
            st.markdown("#### 💡 Personalized Recommendations")
            recommendations = tdah_metrics.get("recommendations", [])
            if recommendations:
                for rec in recommendations[:5]:
                    priority = rec.get("priority", "medium")
                    emoji = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
                    st.markdown(f"{emoji} **{rec.get('title', 'Recommendation')}**")
                    st.caption(rec.get('description', ''))
            else:
                st.info("Keep tracking sessions to get personalized recommendations!")

        if energy_patterns and focus_patterns:
            st.markdown("#### ⚡ Energy vs Focus Correlation")
            correlation_data = session_data.get("energy_focus_correlation", {})
            correlation_score = correlation_data.get("correlation_coefficient", 0)
            if abs(correlation_score) > 0.3:
                if correlation_score > 0:
                    st.success(f"📈 Strong positive correlation ({correlation_score:.2f}) - Higher energy = better focus")
                else:
                    st.warning(f"📉 Negative correlation ({correlation_score:.2f}) - Consider fatigue management")
            else:
                st.info(f"➡️ Weak correlation ({correlation_score:.2f}) - Energy and focus vary independently")

    else:
        timer_sessions = analytics_data.get("timer_sessions", [])
        if not timer_sessions:
            st.info("No TDAH data available")
            return

        col1, col2 = st.columns(2)
        with col1:
            total_interruptions = sum(s.get("interruptions_count", 0) for s in timer_sessions)
            avg_interruptions = total_interruptions / len(timer_sessions) if timer_sessions else 0
            st.metric("🚫 Total Interruptions", total_interruptions, f"{avg_interruptions:.1f} avg/session")

            energy_levels = [s.get("energy_level") for s in timer_sessions if s.get("energy_level")]
            if energy_levels:
                avg_energy = sum(energy_levels) / len(energy_levels)
                st.metric("⚡ Avg Energy Level", f"{avg_energy:.1f}/10", f"Based on {len(energy_levels)} sessions")

        with col2:
            focus_ratings = [s.get("focus_rating") for s in timer_sessions if s.get("focus_rating")]
            if focus_ratings and PLOTLY_AVAILABLE:
                fig = px.histogram(x=focus_ratings, nbins=10, title="Focus Rating Distribution", labels={"x": "Focus Rating (1-10)", "y": "Sessions"}, color_discrete_sequence=["lightcoral"])
                fig.update_layout(height=300)
                _apply_chart_theme(fig)
                st.plotly_chart(fig, use_container_width=True)


# ==============================
#   Detailed Tables & Export
# ==============================

def _render_detailed_tables(analytics_data: Dict[str, Any]):
    tab1, tab2, tab3 = st.tabs(["📅 Daily Metrics", "⏱️ Recent Sessions", "📋 Task Details"])

    with tab1:
        daily_metrics = _ensure_dict_list(analytics_data.get("daily_metrics", []))
        if daily_metrics and PANDAS_AVAILABLE:
            df = pd.DataFrame(daily_metrics).sort_values("date", ascending=False)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No daily metrics available")

    with tab2:
        timer_sessions = _ensure_dict_list(analytics_data.get("timer_sessions", []))
        if timer_sessions:
            recent_sessions = timer_sessions[:10]
            session_data = [{
                "Date": s.get("started_at", "")[:16],
                "Duration": f"{s.get('planned_duration_minutes', 0)}min",
                "Focus": f"{s.get('focus_rating', 'N/A')}/10",
                "Interruptions": s.get('interruptions_count', 0),
                "Task": s.get('task_reference', 'N/A'),
            } for s in recent_sessions]
            if PANDAS_AVAILABLE:
                st.dataframe(pd.DataFrame(session_data), use_container_width=True)
            else:
                for session in session_data[:5]:
                    st.json(session)
        else:
            st.info("No timer sessions available")

    with tab3:
        tasks = _ensure_dict_list(analytics_data.get("tasks", []))
        if tasks:
            rows = [{
                "Title": t.get("title", "Unknown"),
                "Status": t.get("status", "unknown"),
                "TDD Phase": t.get("tdd_phase", "unknown"),
                "Epic": t.get("epic_name", "Unknown"),
                "Estimate": f"{t.get('estimate_minutes', 0)}min",
            } for t in tasks[:20]]
            if PANDAS_AVAILABLE:
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
            else:
                for row in rows[:5]:
                    st.json(row)
        else:
            st.info("No task data available")


def _export_analytics_data(analytics_data: Dict[str, Any], export_format: str):
    try:
        import io
        import json

        filename = f"tdd_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "period_days": analytics_data.get("period_days", 0),
            "overview_metrics": {
                "total_focus_time": analytics_data.get("total_focus_time", 0),
                "total_sessions": analytics_data.get("total_sessions", 0),
                "completed_tasks": analytics_data.get("completed_tasks", 0),
                "average_focus_rating": analytics_data.get("average_focus_rating", 0),
                "total_points": analytics_data.get("total_points", 0),
            },
            "daily_metrics": analytics_data.get("daily_metrics", []),
            "timer_sessions": analytics_data.get("timer_sessions", []),
            "tasks": analytics_data.get("tasks", []),
            "epics": analytics_data.get("epics", []),
        }

        if analytics_data.get("analytics_engine_enabled"):
            export_data["enhanced_metrics"] = {
                "productivity_metrics": analytics_data.get("productivity_metrics", {}),
                "time_patterns": analytics_data.get("time_patterns", {}),
                "session_data": analytics_data.get("session_data", {}),
            }

        if export_format == "JSON":
            json_data = json.dumps(export_data, indent=2, default=str)
            st.download_button("📥 Download JSON", data=json_data, file_name=f"{filename}.json", mime="application/json")

        elif export_format == "CSV" and PANDAS_AVAILABLE:
            if export_data["daily_metrics"]:
                df = pd.DataFrame(export_data["daily_metrics"])
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                st.download_button("📥 Download CSV", data=csv_buffer.getvalue(), file_name=f"{filename}.csv", mime="text/csv")
            else:
                st.warning("No daily metrics available for CSV export")

        elif export_format == "Excel" and PANDAS_AVAILABLE:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                pd.DataFrame([export_data["overview_metrics"]]).to_excel(writer, sheet_name='Overview', index=False)
                if export_data["daily_metrics"]:
                    pd.DataFrame(export_data["daily_metrics"]).to_excel(writer, sheet_name='Daily_Metrics', index=False)
                if export_data["timer_sessions"]:
                    pd.DataFrame(export_data["timer_sessions"]).to_excel(writer, sheet_name='Sessions', index=False)
                if export_data["tasks"]:
                    pd.DataFrame(export_data["tasks"]).to_excel(writer, sheet_name='Tasks', index=False)
                if export_data["epics"]:
                    pd.DataFrame(export_data["epics"]).to_excel(writer, sheet_name='Epics', index=False)

            st.download_button("📥 Download Excel", data=buffer.getvalue(), file_name=f"{filename}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.success(f"✅ Export ready! Download your {export_format} file above.")
    except Exception as e:
        st.error(f"❌ Export failed: {e}")


# ==============================
#   Filters & Recalc
# ==============================

def _apply_data_filters(data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
    if not filters:
        return data

    filtered = dict(data)

    if filters.get("selected_epics"):
        selected_epics = set(filters["selected_epics"])
        if "tasks" in filtered:
            filtered["tasks"] = [t for t in filtered["tasks"] if t.get("epic_name") in selected_epics]
        if "epics" in filtered:
            filtered["epics"] = [e for e in filtered["epics"] if e.get("name") in selected_epics]

    if filters.get("focus_range") and filters["focus_range"] != (1, 10):
        mn, mx = filters["focus_range"]
        if "timer_sessions" in filtered:
            filtered["timer_sessions"] = [
                s for s in filtered["timer_sessions"]
                if (s.get("focus_rating") is None or mn <= s.get("focus_rating", 0) <= mx)
            ]

    if filters.get("selected_tdd_phases"):
        selected = set(filters["selected_tdd_phases"])
        if "tasks" in filtered:
            filtered["tasks"] = [t for t in filtered["tasks"] if t.get("tdd_phase") in selected]

    if filters.get("selected_session_types"):
        selected = set(filters["selected_session_types"])
        if "timer_sessions" in filtered:
            filtered["timer_sessions"] = [s for s in filtered["timer_sessions"] if s.get("session_type") in selected]

    return _recalculate_metrics(filtered)


def _recalculate_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    timer_sessions = data.get("timer_sessions", [])
    tasks = data.get("tasks", [])

    data["total_sessions"] = len(timer_sessions)
    data["total_focus_time"] = sum(s.get("planned_duration_minutes", 0) for s in timer_sessions)
    data["completed_tasks"] = len([t for t in tasks if t.get("status") == "completed"])

    focus_ratings = [s.get("focus_rating") for s in timer_sessions if s.get("focus_rating")]
    data["average_focus_rating"] = sum(focus_ratings) / len(focus_ratings) if focus_ratings else 0

    data["daily_metrics"] = _calculate_daily_metrics(timer_sessions, tasks)
    return data


# ==============================
#   Performance Monitor (sidebar)
# ==============================

def _render_performance_metrics():
    st.sidebar.markdown("### ⚡ Performance Monitor")
    cache_size = _analytics_cache.size()
    st.sidebar.metric("Cache Size", f"{cache_size} items")

    if hasattr(st.session_state, 'performance_metrics') and st.session_state.performance_metrics:
        metrics = st.session_state.performance_metrics
        st.sidebar.markdown("**Function Performance:**")
        for func_name, data in metrics.items():
            exec_time = data.get('execution_time', 0)
            status = "🟢" if exec_time < 0.1 else ("🟡" if exec_time < 0.5 else "🔴")
            st.sidebar.caption(f"{status} {func_name}: {exec_time:.3f}s")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🗑️ Clear Cache", key="clear_cache"):
            _analytics_cache.clear()
            st.sidebar.success("Cache cleared")
    with col2:
        if st.button("🔄 Refresh", key="perf_refresh"):
            st.rerun()

    if cache_size == 0:
        st.sidebar.info("💡 **Tip:** Enable caching for faster performance")

    chart_quality = getattr(st.session_state, 'performance_settings', {}).get('chart_quality', 'Medium')
    use_cache = getattr(st.session_state, 'performance_settings', {}).get('use_cache', True)

    optimization_score = 0
    if use_cache:
        optimization_score += 50
    if chart_quality == "Fast":
        optimization_score += 30
    elif chart_quality == "Medium":
        optimization_score += 20
    if cache_size > 0:
        optimization_score += 20

    st.sidebar.progress(optimization_score / 100)
    st.sidebar.caption(f"Optimization: {optimization_score}%")


# ==============================
#   Entrypoint
# ==============================

if __name__ == "__main__":
    render_analytics_page()
else:
    render_analytics_page()
