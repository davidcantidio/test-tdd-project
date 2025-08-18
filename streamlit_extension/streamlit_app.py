#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 TDD Framework - Enhanced Streamlit Dashboard (Refactor, Enterprise-Hardened)

Destaques:
- Setup e sessão idempotentes
- Auth opcional com “require login” antes de renderizar UI
- Seções encapsuladas com error boundaries
- Cache para queries (st.cache_data) e serviços (st.cache_resource)
- Indicadores de saúde (DB/Services) e botão de refresh
- Fallbacks explícitos e diagnósticos visuais
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# --- Caminho do projeto (garante precedência) --------------------------------
project_root = str(Path(__file__).parent.parent.resolve())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Streamlit (opcional) -----------------------------------------------------
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except Exception:
    STREAMLIT_AVAILABLE = False
    st = None  # type: ignore

# --- Flags de disponibilidade -------------------------------------------------
EXCEPTION_HANDLER_AVAILABLE = True
AUTH_AVAILABLE = True
COMPONENTS_AVAILABLE = True
DB_AVAILABLE = True
SETUP_AVAILABLE = True
CONFIG_AVAILABLE = True

# --- Components ---------------------------------------------------------------
try:
    from streamlit_extension.components.sidebar import render_sidebar  # type: ignore
except Exception:
    COMPONENTS_AVAILABLE = False

    def render_sidebar():
        if STREAMLIT_AVAILABLE:
            st.sidebar.warning("⚠️ Sidebar padrão indisponível (fallback).")

try:
    from streamlit_extension.components.timer import TimerComponent  # type: ignore
except Exception:
    COMPONENTS_AVAILABLE = False

    class TimerComponent:  # fallback mínimo
        def render(self):
            if STREAMLIT_AVAILABLE:
                st.info("⏱️ Timer indisponível (fallback).")

try:
    from streamlit_extension.components.dashboard_widgets import (  # type: ignore
        WelcomeHeader, DailyStats, ProductivityHeatmap,
        ProgressRing, SparklineChart, AchievementCard,
        NotificationToast, QuickActionButton,
    )
except Exception:
    COMPONENTS_AVAILABLE = False

    def WelcomeHeader(*args, **kwargs):
        if STREAMLIT_AVAILABLE:
            st.markdown("### 👋 Bem-vindo!")

    def DailyStats(*args, **kwargs):
        if STREAMLIT_AVAILABLE:
            st.write("📊 Estatísticas diárias indisponíveis.")

    def ProductivityHeatmap(*args, **kwargs):
        if STREAMLIT_AVAILABLE:
            st.write("🗓️ Heatmap indisponível.")

    def ProgressRing(*args, **kwargs):
        if STREAMLIT_AVAILABLE:
            st.write("📈 Progresso indisponível.")

    def SparklineChart(*args, **kwargs):
        if STREAMLIT_AVAILABLE:
            st.write("📉 Sparkline indisponível.")

    def AchievementCard(*args, **kwargs):
        if STREAMLIT_AVAILABLE:
            st.write("🏆 Conquistas indisponíveis.")

    class NotificationToast:
        @staticmethod
        def show(*args, **kwargs):
            if STREAMLIT_AVAILABLE:
                st.info("🔔 Notificações indisponíveis.")

    def QuickActionButton(*args, **kwargs):
        if STREAMLIT_AVAILABLE:
            st.button("Ação")

# --- Database (API modular) ---------------------------------------------------
try:
    # get_connection/transaction importados apenas se necessário futuramente
    from streamlit_extension.database.queries import (  # type: ignore
        list_epics, list_tasks, get_user_stats,
    )
    from streamlit_extension.database.health import check_health  # type: ignore
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

# --- Config -------------------------------------------------------------------
try:
    from streamlit_extension.config import load_config  # type: ignore
except Exception:
    CONFIG_AVAILABLE = False

    def load_config() -> Any:
        # objeto simples com atributos esperados
        return type("Cfg", (), {"debug_mode": False, "app_name": "TDD Framework"})()

# --- App setup / services -----------------------------------------------------
try:
    from streamlit_extension.utils.app_setup import (  # type: ignore
        setup_application, check_services_health,
    )
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

# --- Exception handler --------------------------------------------------------
try:
    from streamlit_extension.utils.exception_handler import (  # type: ignore
        install_global_exception_handler, handle_streamlit_exceptions,
        streamlit_error_boundary, safe_streamlit_operation,
        show_error_dashboard, get_error_statistics,
    )
except Exception:
    EXCEPTION_HANDLER_AVAILABLE = False

    def handle_streamlit_exceptions(show_error: bool = True, attempt_recovery: bool = True):
        def decorator(fn):
            return fn
        return decorator

    class streamlit_error_boundary:  # type: ignore
        def __init__(self, operation_name: str):
            self.name = operation_name

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def safe_streamlit_operation(func, *args, default_return=None, operation_name=None, label=None, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return default_return

    def install_global_exception_handler():
        return None

    def show_error_dashboard(*args, **kwargs):
        if STREAMLIT_AVAILABLE:
            st.error("❌ Erro não tratado.")

    def get_error_statistics() -> Dict[str, Any]:
        return {}

# --- Auth ---------------------------------------------------------------------
try:
    from streamlit_extension.utils.auth import (  # type: ignore
        render_login_page, get_authenticated_user, is_user_authenticated,
    )
except Exception:
    AUTH_AVAILABLE = False

    def is_user_authenticated() -> bool:
        return True

    def render_login_page(auth_manager=None):
        if STREAMLIT_AVAILABLE:
            st.warning("Auth indisponível; seguindo sem login.")

    def get_authenticated_user() -> Optional[Dict[str, Any]]:
        return {"name": "User", "email": "user@example.com"}

# --- Página / Metadados -------------------------------------------------------
if STREAMLIT_AVAILABLE:
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
            **Version:** 1.3.1
            """,
        },
    )

# === CACHES ===================================================================
def cache_data(*dargs, **dkwargs):
    if STREAMLIT_AVAILABLE and hasattr(st, "cache_data"):
        return st.cache_data(*dargs, **dkwargs)

    def deco(fn):
        return fn

    return deco

def cache_resource(*dargs, **dkwargs):
    if STREAMLIT_AVAILABLE and hasattr(st, "cache_resource"):
        return st.cache_resource(*dargs, **dkwargs)

    def deco(fn):
        return fn

    return deco

def _clear_caches():
    if not STREAMLIT_AVAILABLE:
        return
    try:
        if hasattr(st, "cache_data"):
            st.cache_data.clear()
        if hasattr(st, "cache_resource"):
            st.cache_resource.clear()
    except Exception:
        # evita quebrar UI ao limpar cache
        pass

# === WRAPPERS DE DADOS ========================================================
@cache_data(ttl=30)
def fetch_user_stats(user_id: Optional[int] = None) -> Dict[str, Any]:
    def _call():
        # Tenta com user_id, senão sem (compatibilidade de API)
        try:
            if user_id is not None:
                return get_user_stats(user_id)  # type: ignore
        except TypeError:
            pass
        return get_user_stats()  # type: ignore

    return safe_streamlit_operation(_call, default_return={}, operation_name="user_stats")  # type: ignore

@cache_data(ttl=30)
def fetch_epics() -> List[Dict[str, Any]]:
    def _call():
        return list_epics()  # type: ignore
    result = safe_streamlit_operation(_call, default_return=[], operation_name="list_epics")  # type: ignore
    # Normaliza: aceita {'data': [...]} ou [...]
    if isinstance(result, dict) and "data" in result:
        data = result.get("data") or []
        return data if isinstance(data, list) else []
    return result if isinstance(result, list) else []

@cache_data(ttl=30)
def fetch_tasks(epic_id: Any) -> List[Dict[str, Any]]:
    def _call():
        return list_tasks(epic_id)  # type: ignore
    result = safe_streamlit_operation(_call, default_return=[], operation_name=f"list_tasks_{epic_id}")  # type: ignore
    return result if isinstance(result, list) else []

@cache_data(ttl=20)
def fetch_health() -> Dict[str, Any]:
    # Usa health dos serviços quando disponível; fallback para health do DB
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
    if not STREAMLIT_AVAILABLE:
        return

    if EXCEPTION_HANDLER_AVAILABLE and not st.session_state.get("exception_handler_installed"):
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
def _greeting() -> str:
    h = datetime.now().hour
    if h < 12:
        return "Bom dia"
    if h < 18:
        return "Boa tarde"
    return "Boa noite"

def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except Exception:
        return default

def render_topbar(user: Optional[Dict[str, Any]]):
    col1, col2 = st.columns([0.75, 0.25])
    with col1:
        name = (user or {}).get("name") or "Dev"
        WelcomeHeader(
            title=f"{_greeting()}, {name} 👋",
            subtitle="Vamos acelerar seu fluxo de TDD hoje?",
        )
    with col2:
        health = st.session_state.get("health", {})
        overall = health.get("overall", {})
        status = (overall.get("status") or "unknown").lower()
        healthy = bool(overall.get("healthy", False))
        badge = "🟢" if healthy else ("🟡" if status == "degraded" else "🔴")
        st.markdown(f"### {badge} Status: **{status.capitalize()}**")
        if st.button("🔄 Atualizar", use_container_width=True):
            _clear_caches()
            st.session_state["health"] = fetch_health()
            st.rerun()

def render_analytics_row(stats: Dict[str, Any]):
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        DailyStats(data=stats or {})
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
        ProductivityHeatmap(data={"calendar": []})

    with right:
        if not epics:
            st.info("Nenhum épico disponível.")
            return

        # Monta opções de forma tolerante a campos ausentes
        options_map = {}
        for e in epics:
            if not isinstance(e, dict):
                continue
            label = e.get("name") or f"Epico #{e.get('id', '?')}"
            options_map[label] = e.get("id")

        chosen = st.selectbox("Selecione um épico", list(options_map.keys()))
        epic_id = options_map.get(chosen, selected_epic_id)
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
        NotificationToast.show(data=[])

def render_debug_panel():
    with st.expander("🛠️ Debug / Telemetria", expanded=False):
        st.json(
            {
                "health": st.session_state.get("health"),
                "error_stats": safe_streamlit_operation(get_error_statistics, default_return={}),  # type: ignore
            }
        )

# === MAIN =====================================================================
@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def main():
    # Headless → smoke test e sair
    if not STREAMLIT_AVAILABLE:
        print("⚠️ Streamlit não disponível — headless smoke test:")
        if DB_AVAILABLE:
            try:
                print(" - list_epics():", len(list_epics()))
                print(" - health:", check_health())
            except Exception as e:
                print(" - erro DB:", e)
        else:
            print(" - DB indisponível")
        return

    # Inicialização de sessão/serviços/config
    initialize_session_state()

    # Auth gate (se disponível)
    if AUTH_AVAILABLE and not is_user_authenticated():
        # Try to call render_login_page safely - auth may not be fully configured
        try:
            render_login_page()
            return  # Only return if login page was rendered successfully
        except TypeError:
            # Auth module exists but not configured, continue without auth
            st.warning("⚠️ Authentication not fully configured, continuing without login.")

    user = safe_streamlit_operation(get_authenticated_user, default_return={}) if AUTH_AVAILABLE else {"name": "Dev"}

    # Sidebar
    with streamlit_error_boundary("sidebar"):
        render_sidebar()

    # Topbar + indicadores
    with streamlit_error_boundary("topbar"):
        render_topbar(user)

    # Linhas principais
    with streamlit_error_boundary("analytics_row"):
        stats = fetch_user_stats(user.get("id") if isinstance(user, dict) else None)
        render_analytics_row(stats)

    with streamlit_error_boundary("heatmap_tasks"):
        epics = fetch_epics()
        render_heatmap_and_tasks(epics, st.session_state.get("selected_epic_id"))

    with streamlit_error_boundary("timer_notifications"):
        render_timer_and_notifications()

    # Debug opcional
    if st.session_state.get("show_debug_info"):
        render_debug_panel()

if __name__ == "__main__":
    main()
