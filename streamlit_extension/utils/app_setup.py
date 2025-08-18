#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Application Setup Utilities

Centraliza setup/boot do app Streamlit:
- Inicialização do container de serviços
- Checagem/saúde do banco (API modular)
- Estado de sessão Streamlit (quando disponível)
- Limpeza controlada de recursos

Compatível com:
- API modular de banco (streamlit_extension.database.*)
- DatabaseManager legado (streamlit_extension.utils.database.DatabaseManager) para o ServiceContainer
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar
from threading import Lock

# Streamlit (opcional)
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except Exception:
    st = None  # type: ignore
    STREAMLIT_AVAILABLE = False

# Banco (API modular)
# Mantém o consumo da API modular criada no refactor (get_connection, transaction, check_health)
from ..database import get_connection, transaction, check_health  # type: ignore

# Services
from ..services import (  # type: ignore
    ServiceContainer,
    initialize_service_container,
    shutdown_service_container,
    ServiceError,
)

# Para health detalhado de serviços (se disponível)
try:
    from ..services.service_container import check_service_health  # type: ignore
except Exception:  # pragma: no cover - ambiente mínimo
    check_service_health = None  # type: ignore

# DatabaseManager legado: usado APENAS para compor o ServiceContainer (até migração completa)
try:
    from ..utils.database import DatabaseManager  # type: ignore
except Exception as _e:  # pragma: no cover
    DatabaseManager = None  # type: ignore

# --------------------------------------------------------------------------------------
# Logging idempotente
# --------------------------------------------------------------------------------------
_logger = logging.getLogger(__name__)
if not _logger.handlers:
    # Não sobrescreve config global se já existir
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

# --------------------------------------------------------------------------------------
# Tipagem utilitária
# --------------------------------------------------------------------------------------
T = TypeVar("T")

def _is_streamlit():  # micro helper para legibilidade
    return STREAMLIT_AVAILABLE and st is not None

# --------------------------------------------------------------------------------------
# Safe op wrapper (genérico e tipado)
# --------------------------------------------------------------------------------------
def safe_streamlit_operation(
    func: Callable[[], T],
    default_return: Optional[T] = None,
    *,
    operation_name: str = "operation",
) -> Optional[T]:
    try:
        return func()
    except Exception as e:  # pragma: no cover
        _logger.error("safe_streamlit_operation(%s) failed: %s", operation_name, e, exc_info=True)
        if _is_streamlit():
            try:
                st.error(f"❌ Falha em {operation_name}: {e}")
            except Exception:
                pass
        return default_return

# --------------------------------------------------------------------------------------
# Singleton(s) thread-safe
# --------------------------------------------------------------------------------------
_db_lock = Lock()
_container_lock = Lock()

_db_manager_singleton: Optional["DatabaseManager"] = None
_service_container_singleton: Optional["ServiceContainer"] = None

def get_database_manager(force_new: bool = False) -> Optional["DatabaseManager"]:
    """
    Retorna (ou cria) instância do DatabaseManager legado.
    Usado apenas para inicializar o ServiceContainer enquanto serviços dependem dele.
    """
    global _db_manager_singleton

    if DatabaseManager is None:
        _logger.warning("DatabaseManager legado indisponível; serviços podem não inicializar.")
        return None

    with _db_lock:
        if _db_manager_singleton is None or force_new:
            try:
                _db_manager_singleton = DatabaseManager()  # type: ignore[call-arg]
                _logger.info("DatabaseManager (legado) inicializado.")
            except Exception as e:  # pragma: no cover
                _logger.error("Falha ao criar DatabaseManager: %s", e, exc_info=True)
                _db_manager_singleton = None
        return _db_manager_singleton

def _create_service_container(dbm: Optional["DatabaseManager"]) -> Optional["ServiceContainer"]:
    if not dbm:
        return None
    try:
        container = initialize_service_container(db_manager=dbm, lazy_loading=True)
        _logger.info("ServiceContainer inicializado com sucesso.")
        return container
    except Exception as e:  # pragma: no cover
        _logger.error("Falha ao inicializar ServiceContainer: %s", e, exc_info=True)
        if _is_streamlit():
            st.error(f"❌ Service initialization failed: {e}")
        return None

def get_app_service_container(force_new: bool = False) -> Optional["ServiceContainer"]:
    """
    Retorna (ou cria) o container de serviços.
    Usa cache global thread-safe e, se disponível, cache do Streamlit para estabilidade em reruns.
    """
    global _service_container_singleton

    # Se rodando em Streamlit, usamos cache_resource para estabilidade entre reruns.
    if _is_streamlit():
        @st.cache_resource(show_spinner=False)  # type: ignore
        def _cached_container(_: int) -> Optional["ServiceContainer"]:
            # param dummy (_) impede colisão de cache se force_new
            dbm = get_database_manager(force_new=False)
            return _create_service_container(dbm)
        if force_new:
            # invalida o cache (mudando a "chave" dummy)
            return _cached_container(id(object()))
        return _cached_container(0)

    # Ambiente sem Streamlit → usa singleton manual
    with _container_lock:
        if _service_container_singleton is None or force_new:
            dbm = get_database_manager(force_new=force_new)
            _service_container_singleton = _create_service_container(dbm)
        return _service_container_singleton

# --------------------------------------------------------------------------------------
# Checagens de saúde
# --------------------------------------------------------------------------------------
@dataclass
class HealthSection:
    status: str
    message: str = ""
    data: Dict[str, Any] | None = None

@dataclass
class HealthReport:
    database: HealthSection
    services: HealthSection
    overall: Dict[str, Any]

def check_database_connection() -> bool:
    """
    Verifica conexão via API modular (preferencial).
    """
    try:
        conn = get_connection()
        if conn:
            try:
                conn.close()
            except Exception:
                pass
            _logger.info("Database connection verificada (API modular).")
            return True
    except Exception as e:  # pragma: no cover
        _logger.error("Database connection check falhou: %s", e, exc_info=True)
        if _is_streamlit():
            st.error(f"❌ Database connection failed: {e}")
    return False

def check_services_health() -> Dict[str, Any]:
    """
    Health combinado do sistema (DB + Services). Estrutura estável para UI/JSON.
    """
    db_section = HealthSection(status="unknown")
    svc_section = HealthSection(status="unknown")

    # DB health (API modular de saúde)
    try:
        db_health = safe_streamlit_operation(lambda: check_health(), default_return=None, operation_name="db_health")  # type: ignore
        if db_health and isinstance(db_health, dict):
            status = str(db_health.get("status", "unknown"))
            db_section = HealthSection(status="healthy" if status.lower() in {"ok", "healthy", "pass"} else status, data=db_health)
        else:
            # fallback: ping
            ok = check_database_connection()
            db_section = HealthSection(status="healthy" if ok else "error", message="Ping fallback")
    except Exception as e:  # pragma: no cover
        db_section = HealthSection(status="error", message=str(e))

    # Services health
    try:
        container = get_app_service_container()
        if container is None:
            svc_section = HealthSection(status="error", message="Service container indisponível")
        else:
            if check_service_health:
                svc_raw = safe_streamlit_operation(check_service_health, default_return={}, operation_name="service_health") or {}
                overall = str(svc_raw.get("overall_health", "")).lower()
                svc_section = HealthSection(
                    status="healthy" if overall in {"ok", "healthy"} else (overall or "degraded"),
                    data=svc_raw if svc_raw else None,
                    message="" if overall in {"ok", "healthy"} else str(svc_raw.get("error", "Service issues detected")),
                )
            else:
                # fallback simples se função utilitária não existir
                svc_section = HealthSection(status="healthy", message="Container ativo (checagem básica)")
    except Exception as e:  # pragma: no cover
        svc_section = HealthSection(status="error", message=str(e))

    overall_ok = (db_section.status == "healthy") and (svc_section.status == "healthy")
    overall = {"status": "healthy" if overall_ok else "degraded", "healthy": overall_ok}

    return {
        "database": db_section.__dict__,
        "services": svc_section.__dict__,
        "overall": overall,
    }

# --------------------------------------------------------------------------------------
# Sessão Streamlit (opcional)
# --------------------------------------------------------------------------------------
def initialize_streamlit_session() -> None:
    """
    Prepara st.session_state e inicializa serviços quando necessário.
    Chamar cedo no ciclo do app.
    """
    if not _is_streamlit():
        return

    ss = st.session_state
    ss.setdefault("services_initialized", False)
    ss.setdefault("db_manager", None)
    ss.setdefault("service_container", None)

    if not ss.services_initialized:
        with st.spinner("🔧 Inicializando serviços da aplicação..."):
            dbm = get_database_manager()
            if dbm is None:
                st.error("❌ Falha ao inicializar DatabaseManager (legado).")
                return

            ss.db_manager = dbm
            container = get_app_service_container()
            if container:
                ss.service_container = container
                ss.services_initialized = True
                _logger.info("Serviços da sessão Streamlit inicializados.")
            else:
                st.error("❌ Falha ao inicializar ServiceContainer.")

def get_session_services() -> Tuple[Optional["DatabaseManager"], Optional["ServiceContainer"]]:
    """
    Retorna (DatabaseManager legado, ServiceContainer) a partir da sessão Streamlit.
    Em ambientes sem Streamlit, retorna valores globais.
    """
    if _is_streamlit():
        if not st.session_state.get("services_initialized", False):
            initialize_streamlit_session()
        return st.session_state.get("db_manager"), st.session_state.get("service_container")

    # Sem Streamlit: tenta usar singletons
    return get_database_manager(), get_app_service_container()

# --------------------------------------------------------------------------------------
# Ciclo de vida / limpeza
# --------------------------------------------------------------------------------------
def cleanup_application() -> None:
    """
    Libera recursos do app. Chamar no shutdown.
    - Encerra ServiceContainer
    - Solta referências a singletons
    - Limpa session_state (se existir)
    """
    global _service_container_singleton, _db_manager_singleton

    try:
        if _service_container_singleton:
            shutdown_service_container()
            _service_container_singleton = None

        _db_manager_singleton = None  # se precisar, feche conexões no DatabaseManager ao migrar

        if _is_streamlit() and hasattr(st, "session_state"):
            for key in ("db_manager", "service_container", "services_initialized"):
                if key in st.session_state:
                    del st.session_state[key]

        _logger.info("Cleanup concluído.")
    except Exception as e:  # pragma: no cover
        _logger.error("Erro no cleanup: %s", e, exc_info=True)

# --------------------------------------------------------------------------------------
# Setup “one-shot” do app
# --------------------------------------------------------------------------------------
def setup_application() -> None:
    """
    Ponto único de setup para a aplicação Streamlit.
    - Inicializa sessão/serviços
    - Exibe status de saúde
    """
    if not _is_streamlit():
        _logger.warning("Streamlit indisponível - setup de UI ignorado.")
        return

    try:
        initialize_streamlit_session()
        health = check_services_health()

        if not health.get("overall", {}).get("healthy", False):
            st.error("⚠️ Serviços não estão totalmente operacionais.")
            with st.expander("🔍 Detalhes de Saúde", expanded=False):
                st.json(health)
        else:
            _logger.info("Setup da aplicação concluído com sucesso.")
    except Exception as e:  # pragma: no cover
        _logger.error("Application setup failed: %s", e, exc_info=True)
        st.error(f"❌ Application setup failed: {e}")

# --------------------------------------------------------------------------------------
# Acessores convenientes de serviços
# --------------------------------------------------------------------------------------
def _get_container() -> Optional["ServiceContainer"]:
    _, container = get_session_services()
    return container

def get_client_service():
    c = _get_container()
    return c.get_client_service() if c else None

def get_project_service():
    c = _get_container()
    return c.get_project_service() if c else None

def get_epic_service():
    c = _get_container()
    return c.get_epic_service() if c else None

def get_task_service():
    c = _get_container()
    return c.get_task_service() if c else None

def get_analytics_service():
    c = _get_container()
    return c.get_analytics_service() if c else None

def get_timer_service():
    c = _get_container()
    return c.get_timer_service() if c else None

# --------------------------------------------------------------------------------------
# Dev / testes locais
# --------------------------------------------------------------------------------------
def reset_services(force: bool = False) -> None:
    """
    Reinicia todos os serviços (útil p/ desenvolvimento).
    """
    if not force:
        _logger.warning("reset_services solicitado; use force=True para confirmar.")
        return

    _logger.info("Reiniciando serviços...")
    cleanup_application()
    # Recria singletons sob demanda
    if _is_streamlit():
        st.session_state.services_initialized = False
        initialize_streamlit_session()

if __name__ == "__main__":
    # Smoke tests de linha de comando (sem Streamlit)
    print("🧪 Teste rápido - application_setup")
    ok_db = check_database_connection()
    print(f"DB ping: {'✅' if ok_db else '❌'}")

    container = get_app_service_container()
    print(f"ServiceContainer: {'✅' if container else '❌'}")

    health = check_services_health()
    print(f"Overall health: {'✅' if health.get('overall', {}).get('healthy') else '❌'}")
