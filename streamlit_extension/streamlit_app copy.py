#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 TDD Framework - Enhanced Streamlit Dashboard (Enterprise-Pragmatic)

Princípios:
- Resiliência: UI e serviços não derrubam a página.
- Simplicidade: sem overengineering, helpers mínimos e claros.
- Observabilidade leve: prints em debug, mensagens amigáveis em produção.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime

# --- Caminho do projeto -------------------------------------------------------
project_root = str(Path(__file__).parent.parent.resolve())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Streamlit (opcional) -----------------------------------------------------
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except Exception:
    st = None  # type: ignore
    STREAMLIT_AVAILABLE = False

def is_ui() -> bool:
    return STREAMLIT_AVAILABLE and st is not None

def safe_ui(fn: Callable[..., Any], *args, **kwargs) -> Any:
    """Executa uma operação de UI somente se Streamlit estiver disponível."""
    if not is_ui():
        return None
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        # Evita derrubar a página em erros de UI
        logging.info(f"⚠️ UI error in {getattr(fn, '__name__', 'unknown')}: {e}")
        return None

# --- Componentes (com fallbacks) ---------------------------------------------
try:
    from streamlit_extension.components.sidebar import render_sidebar  # type: ignore
    SIDEBAR_AVAILABLE = True
except Exception:
    SIDEBAR_AVAILABLE = False
    def render_sidebar() -> None:
        safe_ui(lambda: st.sidebar.warning("⚠️ Sidebar padrão indisponível (fallback)."))

try:
    from streamlit_extension.components.header import render_header  # type: ignore
    HEADER_AVAILABLE = True
except Exception:
    HEADER_AVAILABLE = False
    def render_header(now=None):
        safe_ui(lambda: st.markdown("# 🚀 TDD Framework"))

try:
    from streamlit_extension.components.timer import TimerComponent  # type: ignore
    TIMER_AVAILABLE = True
except Exception:
    TIMER_AVAILABLE = False
    class TimerComponent:  # fallback mínimo
        def render(self):
            safe_ui(lambda: st.info("⏱️ Timer indisponível (fallback)."))

try:
    from streamlit_extension.components.dashboard_widgets import (  # type: ignore
        WelcomeHeader, DailyStats, ProductivityHeatmap,
        ProgressRing, SparklineChart, AchievementCard,
        NotificationToast, QuickActionButton, NotificationData,
    )
    WIDGETS_AVAILABLE = True
except Exception:
    WIDGETS_AVAILABLE = False

    class WelcomeHeader:
        @staticmethod
        def render(username="User", **kwargs):
            safe_ui(lambda: st.markdown(f"### 👋 Bem-vindo, {username}!"))

    class DailyStats:
        @staticmethod
        def render(stats=None, **kwargs):
            safe_ui(lambda: st.write("📊 Estatísticas diárias indisponíveis."))

    class ProductivityHeatmap:
        @staticmethod
        def render(activity_data=None, **kwargs):
            safe_ui(lambda: st.write("🗓️ Heatmap indisponível."))

    def ProgressRing(*args, **kwargs):
        safe_ui(lambda: st.write("📈 Progresso indisponível."))

    def SparklineChart(*args, **kwargs):
        safe_ui(lambda: st.write("📉 Sparkline indisponível."))

    def AchievementCard(*args, **kwargs):
        safe_ui(lambda: st.write("🏆 Conquistas indisponíveis."))

    @dataclass
    class NotificationData:
        title: str = ""
        message: str = ""
        type: str = "info"
        timestamp: datetime = field(default_factory=datetime.now)

    class NotificationToast:
        @staticmethod
        def show(notification: Optional[NotificationData] = None, **kwargs):
            def _show():
                if notification and getattr(notification, "message", None):
                    st.info(f"🔔 {notification.message}")
                else:
                    st.info("🔔 Notificações indisponíveis.")
            safe_ui(_show)

    def QuickActionButton(*args, **kwargs):
        safe_ui(lambda: st.button("Ação"))

# --- Database / Serviços ------------------------------------------------------
try:
    from streamlit_extension.database.queries import (  # type: ignore
        list_epics, list_tasks, get_user_stats,
    )
    from streamlit_extension.database.health import check_health  # type: ignore
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False

    def list_epics() -> List[Dict[str, Any]]:  # type: ignore
        return []

    def list_tasks(epic_id: Any) -> List[Dict[str, Any]]:  # type: ignore
        return []

    def get_user_stats(*args, **kwargs) -> Dict[str, Any]:  # type: ignore
        return {}

    def check_health() -> Dict[str, Any]:  # type: ignore
        return {"status": "unknown"}

try:
    from streamlit_extension.config import load_config  # type: ignore
    CONFIG_AVAILABLE = True
except Exception:
    CONFIG_AVAILABLE = False
    def load_config() -> Any:
        # objeto simples com atributos esperados
        return type("Cfg", (), {"debug_mode": False, "app_name": "TDD Framework"})()

try:
    from streamlit_extension.utils.app_setup import (  # type: ignore
        setup_application, check_services_health,
    )
    SETUP_AVAILABLE = True
except Exception:
    SETUP_AVAILABLE = False
    def setup_application():
        return None
    def check_services_health() -> Dict[str, Any]:
        return {
            "database": {"status": "unknown", "message": ""},
            "services": {"status": "unknown", "message": ""},
            "overall": {"status": "unknown", "healthy": False},
        }

# --- Exception Handler --------------------------------------------------------
try:
    from streamlit_extension.utils.exception_handler import (  # type: ignore
        install_global_exception_handler, handle_streamlit_exceptions,
        streamlit_error_boundary, safe_streamlit_operation,
        show_error_dashboard, get_error_statistics,
    )
    EXC_AVAILABLE = True
except Exception:
    EXC_AVAILABLE = False

    def handle_streamlit_exceptions(show_error: bool = True, attempt_recovery: bool = True):
        def decorator(fn):  # passthrough
            return fn
        return decorator

    class streamlit_error_boundary:  # type: ignore
        def __init__(self, operation_name: str):
            self.name = operation_name
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False  # não suprime

    def safe_streamlit_operation(func: Callable[..., Any], *args,
                                 default_return=None, operation_name=None, label=None, **kwargs):
        """Execução protegida, ciente de headless/produção."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            cfg = getattr(st.session_state, 'config', None) if is_ui() else None
            is_dev = bool(getattr(cfg, 'debug_mode', False))
            context = {
                "operation": operation_name or getattr(func, "__name__", "unknown"),
                "label": label or "no_label",
                "error": f"{type(e).__name__}: {e}",
            }
            logging.info(f"🚨 OPERATION ERROR: {context}")
            if is_ui():
                if is_dev:
                    safe_ui(st.error, f"🛠️ **Debug Error** ({context['operation']}): {context['error']}")
                else:
                    op_disp = (operation_name or "operation").replace("_", " ").title()
                    safe_ui(st.warning, f"⚠️ {op_disp} temporarily unavailable. Please try again.")
            return default_return

    def install_global_exception_handler(): return None
    def show_error_dashboard(*args, **kwargs): safe_ui(st.error, "❌ Erro não tratado.")
    def get_error_statistics() -> Dict[str, Any]: return {}

# --- Página / Metadados -------------------------------------------------------
def _set_page_config_once():
    if not is_ui():
        return
    try:
        st.set_page_config(
            page_title="TDD Framework Dashboard",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                "Report a bug": "https://github.com/davidcantidio/test-tdd-project/issues",
                "About": """
                # TDD Framework - Advanced Dashboard
                - ⏱️ Timer com suporte a TDAH
                - 📋 Kanban de tarefas
                - 📊 Analytics e produtividade
                - 🎮 Gamification
                - 🐙 Integração GitHub
                **Version:** 1.3.3
                """,
            },
        )
    except Exception:
        # Já configurado em rerun ou em conflitos de set_page_config
        pass

if is_ui():
    _set_page_config_once()

# === CACHES ===================================================================
def cache_data(*dargs, **dkwargs):
    if is_ui() and hasattr(st, "cache_data"):
        return st.cache_data(*dargs, **dkwargs)
    def deco(fn): return fn
    return deco

def cache_resource(*dargs, **dkwargs):
    if is_ui() and hasattr(st, "cache_resource"):
        return st.cache_resource(*dargs, **dkwargs)
    def deco(fn): return fn
    return deco

def _clear_caches():
    if not is_ui():
        return
    try:
        if hasattr(st, "cache_data"):
            st.cache_data.clear()
        if hasattr(st, "cache_resource"):
            st.cache_resource.clear()
        cfg = st.session_state.get("config") if is_ui() else None
        if cfg and getattr(cfg, "debug_mode", False):
            logging.info("🧹 caches limpos")
    except Exception as e:
        logging.info(f"⚠️ erro ao limpar cache: {e}")

# === HELPERS DE NORMALIZAÇÃO ==================================================
def _ensure_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict) and "data" in value:
        data = value.get("data") or []
        return data if isinstance(data, list) else []
    return []

def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except Exception:
        return default


# === WRAPPERS DE DADOS ========================================================
@cache_data(ttl=30)
def fetch_user_stats(user_id: Optional[int] = None) -> Dict[str, Any]:
    def _call():
        try:
            if user_id is not None:
                return get_user_stats(user_id)  # type: ignore[call-arg]
        except TypeError:
            try:
                return get_user_stats(user_id=user_id)  # type: ignore[call-arg]
            except TypeError:
                pass
        return get_user_stats(user_id=1)  # último fallback
    return safe_streamlit_operation(_call, default_return={}, operation_name="user_stats")

@cache_data(ttl=30)
def fetch_epics() -> List[Dict[str, Any]]:
    result = safe_streamlit_operation(list_epics, default_return=[], operation_name="list_epics")  # type: ignore
    return _ensure_list(result)

@cache_data(ttl=30)
def fetch_tasks(epic_id: Any) -> List[Dict[str, Any]]:
    def _call():
        return list_tasks(epic_id)  # type: ignore
    result = safe_streamlit_operation(_call, default_return=[], operation_name=f"list_tasks_{epic_id}")
    return _ensure_list(result)

@cache_data(ttl=20)
def fetch_health() -> Dict[str, Any]:
    if SETUP_AVAILABLE:
        return check_services_health()
    return {
        "database": check_health(),
        "services": {"status": "unknown"},
        "overall": {"status": "unknown", "healthy": False},
    }

# === SESSÃO E ESTADO ==========================================================
@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def initialize_session_state():
    if not is_ui():
        return

    if EXC_AVAILABLE and not st.session_state.get("exception_handler_installed"):
        install_global_exception_handler()
        st.session_state.exception_handler_installed = True

    if CONFIG_AVAILABLE and "config" not in st.session_state:
        with streamlit_error_boundary("load_config"):
            st.session_state.config = load_config()

    # Serviços / DB
    if SETUP_AVAILABLE and not st.session_state.get("services_ready"):
        with streamlit_error_boundary("setup_application"):
            setup_application()
            st.session_state.services_ready = True

    # Timer
    if "timer" not in st.session_state:
        st.session_state.timer = TimerComponent()

    # Preferências
    if "show_debug_info" not in st.session_state:
        cfg = st.session_state.get("config", None)
        st.session_state.show_debug_info = bool(getattr(cfg, "debug_mode", False))

    # Navegação
    st.session_state.setdefault("current_page", "Dashboard")

    # Seleção padrão de épico
    epics = fetch_epics()
    default_epic_id = epics[0].get("id") if epics and isinstance(epics[0], dict) else None
    st.session_state.setdefault("selected_epic_id", default_epic_id)

    # Saúde/db
    st.session_state["health"] = fetch_health()

# === RENDER UI ================================================================
def render_topbar(user: Optional[Dict[str, Any]]):
    # Render main header
    render_header()
    
    # System status section
    col1, col2 = st.columns([0.75, 0.25])
    with col2:
        health = st.session_state.get("health", {}) or {}
        overall = health.get("overall", {}) or {}
        status = (overall.get("status") or "unknown").lower()
        healthy = bool(overall.get("healthy", False))
        badge = "🟢" if healthy else ("🟡" if status == "degraded" else "🔴")
        st.markdown(f"### {badge} Status: **{status.capitalize()}**")
        if st.button("🔄 Atualizar", use_container_width=True, key="btn_refresh_health"):
            _clear_caches()
            st.session_state["health"] = fetch_health()
            st.rerun()

def render_analytics_row(stats: Dict[str, Any]):
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        DailyStats.render(stats=stats or {})
    with c2:
        ProgressRing(
            value=_as_float(stats.get("weekly_completion"), 0.0),
            label="Conclusão da Semana",
        )
    with c3:
        SparklineChart(series=stats.get("focus_series") or [], title="Foco (7d)")

def render_heatmap_and_tasks(epics: List[Dict[str, Any]], selected_epic_id: Optional[Any]):
    left, right = st.columns([1.2, 1.0])
    with left:
        ProductivityHeatmap.render(activity_data={})
    with right:
        if not epics:
            st.info("Nenhum épico disponível.")
            return

        # Opções tolerantes a campos ausentes
        options_map: Dict[str, Any] = {}
        for e in epics:
            if not isinstance(e, dict):
                continue
            label = e.get("name") or f"Épico #{e.get('id', '?')}"
            options_map[label] = e.get("id")

        option_labels = list(options_map.keys())
        current_label = next(
            (lbl for lbl, _id in options_map.items() if _id == selected_epic_id),
            (option_labels[0] if option_labels else None),
        )
        idx = option_labels.index(current_label) if (current_label in option_labels) else 0

        chosen_label = st.selectbox(
            "Selecione um épico",
            option_labels,
            index=idx,
            key="selected_epic_label",
        )
        epic_id = options_map.get(chosen_label, selected_epic_id)
        st.session_state["selected_epic_id"] = epic_id

        with streamlit_error_boundary("load_tasks"):
            tasks = fetch_tasks(epic_id) if epic_id is not None else []

        st.markdown("#### Tarefas")
        if not tasks:
            st.caption("Nenhuma tarefa para este épico.")
        else:
            for t in tasks[:20]:
                title = t.get("title") or "(sem título)"
                status = t.get("status") or "todo"
                est = t.get("estimate_minutes")
                try:
                    est_str = f"{int(est)} min" if est is not None else "—"
                except Exception:
                    est_str = "—"
                st.write(f"- **{title}** · _{status}_ · ⏱ {est_str}")

def render_timer_and_notifications():
    c1, c2 = st.columns([0.65, 0.35])
    with c1:
        st.markdown("### ⏱️ Foco")
        st.session_state.timer.render()
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

def render_debug_panel():
    with st.expander("🛠️ Debug / Telemetria", expanded=False):
        st.json(
            {
                "health": st.session_state.get("health"),
                "error_stats": safe_streamlit_operation(get_error_statistics, default_return={}),  # type: ignore
            }
        )

# --- Auth (import por último) -------------------------------------------------
try:
    from streamlit_extension.utils.auth import (  # type: ignore
        render_login_page, get_authenticated_user, is_user_authenticated,
    )
    AUTH_AVAILABLE = True
except Exception:
    AUTH_AVAILABLE = False
    def is_user_authenticated() -> bool: return True
    def render_login_page(auth_manager=None):
        safe_ui(st.warning, "Auth indisponível; seguindo sem login.")
    def get_authenticated_user() -> Optional[Dict[str, Any]]:
        return {"name": "User", "email": "user@example.com"}

# --- Navigation System Import ------------------------------------------------
try:
    from streamlit_extension.pages import render_page, get_available_pages, PAGE_REGISTRY  # type: ignore
    PAGES_AVAILABLE = True
except Exception:
    PAGES_AVAILABLE = False
    def render_page(page_id: str): 
        safe_ui(st.error, f"Page '{page_id}' not available")
        return {"error": f"Page system not available"}
    def get_available_pages(): 
        return {}

# === NAVIGATION HANDLER =======================================================
def render_current_page(user: Dict[str, Any]):
    """Render the current page based on session state navigation."""
    current_page = st.session_state.get("current_page", "Dashboard")
    
    # DEBUG: Show current navigation state
    st.sidebar.write(f"🔍 DEBUG: Current page = {current_page}")
    st.sidebar.write(f"🔍 DEBUG: PAGES_AVAILABLE = {PAGES_AVAILABLE}")
    
    if current_page == "Dashboard":
        # Render default dashboard
        st.sidebar.write("🔍 DEBUG: Rendering Dashboard")
        render_dashboard_content(user)
    elif PAGES_AVAILABLE:
        # Use the pages system for CRUD pages
        page_id = current_page.lower()  # Convert "Clients" -> "clients"
        st.sidebar.write(f"🔍 DEBUG: Attempting to render page_id = {page_id}")
        
        with streamlit_error_boundary(f"render_page_{page_id}"):
            page_result = render_page(page_id)
            st.sidebar.write(f"🔍 DEBUG: Page result = {page_result}")
            
            if isinstance(page_result, dict) and "error" in page_result:
                st.error(f"❌ Error loading {current_page}: {page_result['error']}")
                st.info("Returning to Dashboard...")
                st.session_state.current_page = "Dashboard"
                if st.button("🔄 Return to Dashboard"):
                    st.rerun()
    else:
        # Fallback for unknown pages
        st.sidebar.write("🔍 DEBUG: Pages not available, showing fallback")
        st.error(f"❌ Page '{current_page}' is not available")
        st.info("Available pages: Dashboard")
        if st.button("🏠 Return to Dashboard"):
            st.session_state.current_page = "Dashboard"
            st.rerun()

def render_dashboard_content(user: Dict[str, Any]):
    """Render the default dashboard content."""
    # Linhas principais do dashboard
    with streamlit_error_boundary("analytics_row"):
        stats = fetch_user_stats(user.get("id") if isinstance(user, dict) else None)
        render_analytics_row(stats or {})

    with streamlit_error_boundary("heatmap_tasks"):
        epics = fetch_epics()
        render_heatmap_and_tasks(epics, st.session_state.get("selected_epic_id"))

    with streamlit_error_boundary("timer_notifications"):
        render_timer_and_notifications()

# === MAIN =====================================================================
@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def main():
    # Headless → smoke test e sair
    if not is_ui():
        logging.info("⚠️ Streamlit não disponível — headless smoke test:")
        if DB_AVAILABLE:
            try:
                logging.info(" - list_epics():", len(list_epics()))
                logging.info(" - health:", check_health())
            except Exception as e:
                logging.info(" - erro DB:", e)
        else:
            logging.info(" - DB indisponível")
        return

    # Inicialização
    initialize_session_state()

    # Auth gate
    if AUTH_AVAILABLE and not is_user_authenticated():
        try:
            render_login_page()
            return
        except TypeError:
            st.warning("⚠️ Authentication não está totalmente configurada. Continuando sem login.")

    user = safe_streamlit_operation(get_authenticated_user, default_return={}) if AUTH_AVAILABLE else {"name": "Dev"}

    # Sidebar with navigation
    with streamlit_error_boundary("sidebar"):
        safe_streamlit_operation(render_sidebar, default_return=None, operation_name="render_sidebar")  # type: ignore

    # Topbar + indicadores
    with streamlit_error_boundary("topbar"):
        render_topbar(user if isinstance(user, dict) else {"name": "Dev"})

    # Page routing - render current page based on navigation
    with streamlit_error_boundary("page_content"):
        render_current_page(user if isinstance(user, dict) else {"name": "Dev"})

    # Debug opcional
    if st.session_state.get("show_debug_info"):
        render_debug_panel()

if __name__ == "__main__":
    main()