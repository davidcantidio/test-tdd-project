#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 TDD Framework - Enhanced Streamlit Dashboard (Refactor)

Destaques:
- Setup e sessão idempotentes
- Auth opcional com “require login” antes de renderizar UI
- Seções encapsuladas com error boundaries
- Cache para queries (st.cache_data) e serviços (st.cache_resource)
- Indicadores de saúde (DB/Services) e botão de refresh
- Fallbacks seguros quando módulos opcionais não estão disponíveis
"""

from __future__ import annotations

import sys
import time
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

# --- Imports granulares com fallbacks -----------------------------------------
EXCEPTION_HANDLER_AVAILABLE = True
AUTH_AVAILABLE = True
COMPONENTS_AVAILABLE = True
DB_AVAILABLE = True
SETUP_AVAILABLE = True
CONFIG_AVAILABLE = True

# Components
try:
    from streamlit_extension.components.sidebar import render_sidebar  # type: ignore
except Exception:
    COMPONENTS_AVAILABLE = False
    def render_sidebar():  # fallback mínimo
        pass

try:
    from streamlit_extension.components.timer import TimerComponent  # type: ignore
except Exception:
    COMPONENTS_AVAILABLE = False
    class TimerComponent:  # fallback mínimo
        def render(self):
            if STREAMLIT_AVAILABLE:
                st.info("⏱️ Timer indisponível.")

try:
    from streamlit_extension.components.dashboard_widgets import (  # type: ignore
        WelcomeHeader, DailyStats, ProductivityHeatmap,
        ProgressRing, SparklineChart, AchievementCard,
        NotificationToast, NotificationData, QuickActionButton,
    )
except Exception:
    COMPONENTS_AVAILABLE = False
    # Fallbacks simples (não quebram)
    def WelcomeHeader(*args, **kwargs):
        if STREAMLIT_AVAILABLE: st.markdown("### 👋 Bem-vindo!")

    def DailyStats(*args, **kwargs):
        if STREAMLIT_AVAILABLE: st.write("📊 Estatísticas diárias indisponíveis.")

    def ProductivityHeatmap(*args, **kwargs):
        if STREAMLIT_AVAILABLE: st.write("🗓️ Heatmap indisponível.")

    def ProgressRing(*args, **kwargs):
        if STREAMLIT_AVAILABLE: st.write("📈 Progresso indisponível.")

    def SparklineChart(*args, **kwargs):
        if STREAMLIT_AVAILABLE: st.write("📉 Sparkline indisponível.")

    def AchievementCard(*args, **kwargs):
        if STREAMLIT_AVAILABLE: st.write("🏆 Conquistas indisponíveis.")

    class NotificationToast:
        @staticmethod
        def show(*args, **kwargs):
            if STREAMLIT_AVAILABLE: st.info("🔔 Notificações indisponíveis.")

    class NotificationData:
        pass

    def QuickActionButton(*args, **kwargs):
        if STREAMLIT_AVAILABLE: st.button("Ação")

# Database (API modular)
try:
    from streamlit_extension.database import get_connection, transaction  # type: ignore
    from streamlit_extension.database.queries import (  # type: ignore
        list_epics, list_tasks, get_user_stats,
    )
    from streamlit_extension.database.health import check_health  # type: ignore
except Exception:
    DB_AVAILABLE = False
    def list_epics() -> List[Dict[str, Any]]: return []
    def list_tasks(epic_id: int) -> List[Dict[str, Any]]: return []
    def get_user_stats() -> Dict[str, Any]: return {}
    def check_health() -> Dict[str, Any]: return {"status": "unknown"}

# Config
try:
    from streamlit_extension.config import load_config  # type: ignore
except Exception:
    CONFIG_AVAILABLE = False
    def load_config() -> Any:
        return type("Cfg", (), {"debug_mode": False, "app_name": "TDD Framework"})()

# App setup / services
try:
    from streamlit_extension.utils.app_setup import (  # type: ignore
        setup_application, get_session_services, check_services_health,
        get_client_service, get_project_service, get_analytics_service,
    )
except Exception:
    SETUP_AVAILABLE = False
    def setup_application(): pass
    def get_session_services() -> Tuple[None, None]: return (None, None)
    def check_services_health() -> Dict[str, Any]:
        return {"database": {"status":"unknown","message":""},
                "services": {"status":"unknown","message":""},
                "overall": {"status":"unknown","healthy": False}}
    def get_client_service(): return None
    def get_project_service(): return None
    def get_analytics_service(): return None

# Exception handler
try:
    from streamlit_extension.utils.exception_handler import (  # type: ignore
        install_global_exception_handler, handle_streamlit_exceptions,
        streamlit_error_boundary, safe_streamlit_operation,
        show_error_dashboard, get_error_statistics,
    )
except Exception:
    EXCEPTION_HANDLER_AVAILABLE = False

    def handle_streamlit_exceptions(show_error=True, attempt_recovery=True):
        def decorator(fn): return fn
        return decorator

    class streamlit_error_boundary:  # type: ignore
        def __init__(self, operation_name: str): self.name = operation_name
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False

    def safe_streamlit_operation(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return kwargs.get("default_return")

    def install_global_exception_handler(): pass
    def show_error_dashboard(*args, **kwargs): 
        if STREAMLIT_AVAILABLE: st.error("❌ Erro não tratado.")
    def get_error_statistics() -> Dict[str, Any]: return {}

# Auth
try:
    from streamlit_extension.utils.auth import (  # type: ignore
        GoogleOAuthManager, render_login_page,
        get_authenticated_user, is_user_authenticated,
    )
except Exception:
    AUTH_AVAILABLE = False
    def is_user_authenticated() -> bool: return True
    def render_login_page(): 
        if STREAMLIT_AVAILABLE: st.warning("Auth indisponível; seguindo sem login.")
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
            **Version:** 1.3.0
            """,
        },
    )

# === CACHES ===================================================================
def cache_data(*dargs, **dkwargs):
    if STREAMLIT_AVAILABLE and hasattr(st, "cache_data"):
        return st.cache_data(*dargs, **dkwargs)
    # Fallback no-op
    def deco(fn): return fn
    return deco

def cache_resource(*dargs, **dkwargs):
    if STREAMLIT_AVAILABLE and hasattr(st, "cache_resource"):
        return st.cache_resource(*dargs, **dkwargs)
    def deco(fn): return fn
    return deco

@cache_data(ttl=30)
def fetch_user_stats() -> Dict[str, Any]:
    return safe_streamlit_operation(get_user_stats, default_return={}, label="user_stats")  # type: ignore

@cache_data(ttl=30)
def fetch_epics() -> List[Dict[str, Any]]:
    return safe_streamlit_operation(list_epics, default_return=[], label="list_epics")  # type: ignore

@cache_data(ttl=30)
def fetch_tasks(epic_id: int) -> List[Dict[str, Any]]:
    return safe_streamlit_operation(lambda: list_tasks(epic_id), default_return=[], label=f"list_tasks_{epic_id}")  # type: ignore

@cache_data(ttl=20)
def fetch_health() -> Dict[str, Any]:
    # Usa health dos serviços quando disponível; fallback para health do DB
    if SETUP_AVAILABLE:
        return check_services_health()
    return {"database": check_health(), "services": {"status": "unknown"}, "overall": {"status": "unknown", "healthy": False}}

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

    # Serviços / DB (usa utilitário centralizado)
    if SETUP_AVAILABLE and not st.session_state.get("services_ready"):
        with streamlit_error_boundary("setup_application"):
            setup_application()
            st.session_state.services_ready = True

    # Timer
    if "timer" not in st.session_state:
        st.session_state.timer = TimerComponent()

    # Preferências
    if "show_debug_info" not in st.session_state:
        st.session_state.show_debug_info = bool(getattr(st.session_state.get("config", None), "debug_mode", False))

    # Navegação
    st.session_state.setdefault("current_page", "Dashboard")

    # Seleção padrão de épico
    eps = fetch_epics()
    default_epic_id = eps[0]["id"] if eps else None
    st.session_state.setdefault("selected_epic_id", default_epic_id)

    # Saúde/db
    st.session_state["health"] = fetch_health()

# === RENDER UI ================================================================
def _greeting() -> str:
    h = datetime.now().hour
    if h < 12: return "Bom dia"
    if h < 18: return "Boa tarde"
    return "Boa noite"

def render_topbar(user: Optional[Dict[str, Any]]):
    col1, col2 = st.columns([0.75, 0.25])
    with col1:
        WelcomeHeader(title=f"{_greeting()}, {user.get('name', 'Dev') if user else 'Dev'} 👋", subtitle="Vamos acelerar seu fluxo de TDD hoje?")
    with col2:
        health = st.session_state.get("health", {})
        overall = health.get("overall", {})
        status = overall.get("status", "unknown")
        healthy = overall.get("healthy", False)
        badge = "🟢" if healthy else ("🟡" if status == "degraded" else "🔴")
        st.markdown(f"### {badge} Status: **{status.capitalize()}**")
        if st.button("🔄 Atualizar", use_container_width=True):
            # limpa caches e reavalia
            try:
                if hasattr(st, "cache_data"): st.cache_data.clear()
                if hasattr(st, "cache_resource"): st.cache_resource.clear()
            except Exception:
                pass
            st.session_state["health"] = fetch_health()
            st.rerun()

def render_analytics_row(stats: Dict[str, Any]):
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        DailyStats(data=stats or {})
    with c2:
        # Exemplo de cartão de progresso (pode usar dados reais)
        ProgressRing(value=float(stats.get("weekly_completion", 0.0)), label="Conclusão da Semana")
    with c3:
        SparklineChart(series=stats.get("focus_series", []), title="Foco (7d)")

def render_heatmap_and_tasks(epics: List[Dict[str, Any]], selected_epic_id: Optional[int]):
    left, right = st.columns([1.2, 1.0])
    with left:
        ProductivityHeatmap(data={"calendar": st.session_state.get("config", None) and []})
    with right:
        if not epics:
            st.info("Nenhum épico disponível.")
            return
        options = {e["name"]: e["id"] for e in epics}
        label = "Selecione um épico"
        chosen = st.selectbox(label, list(options.keys()))
        epic_id = options.get(chosen, selected_epic_id)
        st.session_state["selected_epic_id"] = epic_id

        with streamlit_error_boundary("load_tasks"):
            tasks = fetch_tasks(epic_id) if epic_id else []
        st.markdown("#### Tarefas")
        if not tasks:
            st.caption("Nenhuma tarefa para este épico.")
        else:
            for t in tasks[:20]:
                st.write(f"- **{t.get('title','(sem título)')}** · _{t.get('status','todo')}_ · ⏱ {t.get('estimate_minutes',0)} min")

def render_timer_and_notifications():
    c1, c2 = st.columns([0.65, 0.35])
    with c1:
        st.markdown("### ⏱️ Foco")
        st.session_state.timer.render()
    with c2:
        st.markdown("### 🔔 Notificações")
        NotificationToast.show(data=[])  # integre seu provedor de notificações aqui

def render_debug_panel():
    with st.expander("🛠️ Debug / Telemetria", expanded=False):
        st.json({
            "health": st.session_state.get("health"),
            "error_stats": safe_streamlit_operation(get_error_statistics, default_return={}),  # type: ignore
        })

# === MAIN =====================================================================
@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def main():
    # Headless → smoke test e sair
    if not STREAMLIT_AVAILABLE:
        print("⚠️ Streamlit não disponível — headless smoke test:")
        print(" - list_epics():", len(list_epics()) if DB_AVAILABLE else "(db indisponível)")
        print(" - health:", check_health() if DB_AVAILABLE else "(db indisponível)")
        return

    # Inicialização de sessão/serviços/config
    initialize_session_state()

    # Auth gate (se disponível)
    if AUTH_AVAILABLE and not is_user_authenticated():
        render_login_page()
        return
    user = safe_streamlit_operation(get_authenticated_user, default_return={}) if AUTH_AVAILABLE else {"name": "Dev"}

    # Sidebar
    with streamlit_error_boundary("sidebar"):
        render_sidebar()

    # Topbar + indicadores
    with streamlit_error_boundary("topbar"):
        render_topbar(user)

    # Linhas principais
    with streamlit_error_boundary("analytics_row"):
        stats = fetch_user_stats()
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
