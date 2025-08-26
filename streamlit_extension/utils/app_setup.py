#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Application Setup Utilities

Core functions for TDD Framework application setup:
- Service initialization (thread-safe + Streamlit cache)
- Database and service health checks  
- Application lifecycle and cleanup
- Headless execution support (without Streamlit)

Compatible with:
- Modular database API (streamlit_extension.database.*) [preferred]
- Legacy DatabaseManager for ServiceContainer initialization

Environment variables:
- TDD_DISABLE_SERVICES=1 → disables service initialization
"""

from __future__ import annotations

import atexit
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar
from threading import Lock

# ======================================================================================
# Streamlit (optional)
# ======================================================================================
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except Exception:  # pragma: no cover - headless/test environments
    st = None  # type: ignore
    STREAMLIT_AVAILABLE = False

# ======================================================================================
# Database (modular API) - preferred refactor
# ======================================================================================
try:
    from ..database import get_connection, check_health  # type: ignore
    MODULAR_DB_AVAILABLE = True
except Exception:  # pragma: no cover
    get_connection = None  # type: ignore
    check_health = None  # type: ignore
    MODULAR_DB_AVAILABLE = False

# ======================================================================================
# Services
# ======================================================================================
from ..services import (  # type: ignore
    ServiceContainer,
    initialize_service_container,
    shutdown_service_container,
)

# For detailed service health (if available)
try:
    from ..services.service_container import check_services_health as check_service_health  # type: ignore
except Exception:  # pragma: no cover - minimal environment
    check_service_health = None  # type: ignore

# Legacy DatabaseManager: DEPRECATED - Phase 4.2 Clean Architecture Complete
# DatabaseManager is no longer needed - services use modular database API directly
DatabaseManager = None  # type: ignore
DATABASE_UTILS_AVAILABLE = False

# ======================================================================================
# Exports
# ======================================================================================
__all__ = [
    "setup_application",
    "initialize_streamlit_session",
    "get_session_services",
    "get_app_service_container",
    "get_database_manager",
    "check_services_health",
    "check_database_connection",
    "cleanup_application",
    "reset_services",
    "get_project_service",
    "get_epic_service",
    "get_task_service",
    "get_analytics_service",
    "get_timer_service",
    "STREAMLIT_AVAILABLE",
    "DATABASE_UTILS_AVAILABLE",
]

# ======================================================================================
# Logging setup
# ======================================================================================
_logger = logging.getLogger(__name__)
if not _logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    _logger.addHandler(logging.NullHandler())

# ======================================================================================
# Configuration
# ======================================================================================
DISABLE_SERVICES = os.getenv("TDD_DISABLE_SERVICES", "0") in {"1", "true", "True"}

# ======================================================================================
# Utility types
# ======================================================================================
T = TypeVar("T")

def _is_streamlit() -> bool:
    return STREAMLIT_AVAILABLE and st is not None

# ======================================================================================
# Safe operation wrapper
# ======================================================================================
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
                st.error(f"❌ Failed in {operation_name}: {e}")
            except Exception:
                pass
        return default_return

# ======================================================================================
# Thread-safe singletons
# ======================================================================================
_db_lock = Lock()
_container_lock = Lock()

_db_manager_singleton: Optional["DatabaseManager"] = None
_service_container_singleton: Optional["ServiceContainer"] = None

def get_database_manager(force_new: bool = False) -> Optional["DatabaseManager"]:
    """
    DEPRECATED - Phase 4.2 Clean Architecture Complete.
    DatabaseManager is no longer used. Services use modular database API directly.
    This function now always returns None for backward compatibility.
    """
    _logger.debug("DatabaseManager is deprecated - services use modular database API")
    return None

def _create_service_container(dbm: Optional["DatabaseManager"] = None) -> Optional["ServiceContainer"]:
    """
    Create ServiceContainer using modular database API.
    The dbm parameter is kept for backward compatibility but is no longer used.
    """
    if DISABLE_SERVICES:
        _logger.warning("Services disabled by TDD_DISABLE_SERVICES.")
        return None
    
    try:
        # Services now use modular database API directly - no DatabaseManager needed
        container = initialize_service_container(db_manager=None, lazy_loading=True)
        _logger.info("ServiceContainer initialized successfully with modular architecture.")
        return container
    except Exception as e:  # pragma: no cover
        _logger.error("Failed to initialize ServiceContainer: %s", e, exc_info=True)
        if _is_streamlit():
            st.error(f"❌ Service initialization failed: {e}")
        return None

def _cache_key_for_container(force_new: bool) -> int:
    """
    Generates stable cache key for container.
    - 0: normal
    - timestamp-like int: when force_new=True
    """
    return 0 if not force_new else int(time.time() * 1000)

def get_app_service_container(force_new: bool = False) -> Optional["ServiceContainer"]:
    """
    Returns (or creates) the service container.
    Uses thread-safe global cache and, if available, Streamlit cache for stability across reruns.
    """
    global _service_container_singleton

    # If running in Streamlit, use cache_resource for stability between reruns
    if _is_streamlit():
        @st.cache_resource(show_spinner=False)  # type: ignore
        def _cached_container(_key: int) -> Optional["ServiceContainer"]:
            # Services use modular database API directly - no DatabaseManager needed
            return _create_service_container(None)

        return _cached_container(_cache_key_for_container(force_new))

    # Environment without Streamlit → use manual singleton
    with _container_lock:
        if _service_container_singleton is None or force_new:
            # Services use modular database API directly - no DatabaseManager needed
            _service_container_singleton = _create_service_container(None)
        return _service_container_singleton

# ======================================================================================
# Health checks
# ======================================================================================
@dataclass
class HealthSection:
    status: str
    message: str = ""
    data: Dict[str, Any] | None = None

def _normalize_status(value: str) -> str:
    v = value.lower().strip()
    if v in {"ok", "healthy", "pass"}:
        return "healthy"
    if v in {"error", "fail", "failed"}:
        return "error"
    if v in {"degraded", "warn", "warning"}:
        return "degraded"
    return "unknown"

def check_database_connection() -> bool:
    """
    Verify connection via modular API (preferred).
    """
    if not MODULAR_DB_AVAILABLE or get_connection is None:
        _logger.warning("Modular DB API unavailable; skipping ping.")
        return False
    try:
        conn = get_connection()
        if conn and hasattr(conn, "close"):
            try:
                conn.close()
            except Exception:
                pass
            _logger.info("Database connection verified (modular API).")
            return True
    except Exception as e:  # pragma: no cover
        _logger.error("Database connection check failed: %s", e, exc_info=True)
        if _is_streamlit():
            try:
                st.error(f"❌ Database connection failed: {e}")
            except Exception:
                pass
    return False

def check_services_health() -> Dict[str, Any]:
    """
    Combined system health (DB + Services). Stable structure for UI/JSON.
    """
    db_section = HealthSection(status="unknown")
    svc_section = HealthSection(status="unknown")

    # DB health (modular health API)
    try:
        db_health: Optional[Dict[str, Any]] = None
        if MODULAR_DB_AVAILABLE and check_health is not None:
            db_health = safe_streamlit_operation(
                lambda: check_health(),  # type: ignore
                default_return=None,
                operation_name="db_health",
            )
        if db_health and isinstance(db_health, dict):
            status = _normalize_status(str(db_health.get("status", "")))
            if status == "unknown":
                # Interpret legacy payloads - ESSENTIAL FIX
                framework_ok = bool(db_health.get("framework_db_connected", False))
                timer_ok = bool(db_health.get("timer_db_connected", False))
                if framework_ok and timer_ok:
                    db_section = HealthSection(status="healthy", data=db_health, message="Database connections verified")
                elif framework_ok:
                    db_section = HealthSection(status="degraded", data=db_health, message="Framework DB OK, Timer DB issues")
                else:
                    db_section = HealthSection(status="error", data=db_health, message="Framework DB connection failed")
            else:
                db_section = HealthSection(status=status, data=db_health)
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
            if DISABLE_SERVICES:
                svc_section = HealthSection(status="degraded", message="Services disabled by configuration")
            else:
                svc_section = HealthSection(status="error", message="Service container unavailable")
        else:
            if check_service_health:
                # Some versions require passing the container
                def _svc_call() -> Dict[str, Any]:
                    try:
                        return check_service_health(container)  # type: ignore
                    except TypeError:
                        return check_service_health()  # type: ignore
                svc_raw = safe_streamlit_operation(_svc_call, default_return={}, operation_name="service_health") or {}
                overall = _normalize_status(str(svc_raw.get("overall_health", "")))
                message = "" if overall == "healthy" else str(svc_raw.get("error", "Service issues detected"))
                svc_section = HealthSection(status=overall if overall != "unknown" else "healthy", data=svc_raw or \
                    None, message=message)
            else:
                svc_section = HealthSection(status="healthy", message="Container active (basic check)")
    except Exception as e:  # pragma: no cover
        svc_section = HealthSection(status="error", message=str(e))

    overall_ok = (db_section.status == "healthy") and (svc_section.status == "healthy")
    overall = {"status": "healthy" if overall_ok else "degraded", "healthy": overall_ok}

    return {
        "database": db_section.__dict__,
        "services": svc_section.__dict__,
        "overall": overall,
    }

# ======================================================================================
# Streamlit session (optional)
# ======================================================================================
def initialize_streamlit_session() -> None:
    """
    Prepare st.session_state and initialize services when necessary.
    Call early in the app cycle.
    """
    if not _is_streamlit():
        return

    ss = st.session_state
    ss.setdefault("services_initialized", False)
    ss.setdefault("db_manager", None)
    ss.setdefault("service_container", None)

    if ss.services_initialized:
        return

    with st.spinner("🔧 Initializing application services..."):
        # Skip DatabaseManager - services use modular database API directly
        ss.db_manager = None  # Legacy compatibility - always None in Phase 4.2
        
        container = get_app_service_container()
        if container or DISABLE_SERVICES:
            ss.service_container = container
            ss.services_initialized = True
            _logger.info("Streamlit session services initialized with modular architecture.")
        else:
            st.error("❌ Failed to initialize ServiceContainer.")

def get_session_services() -> Tuple[Optional["DatabaseManager"], Optional["ServiceContainer"]]:
    """
    Returns (DatabaseManager legacy, ServiceContainer) from Streamlit session.
    DatabaseManager is always None in Phase 4.2 Clean Architecture.
    In environments without Streamlit, returns global values.
    """
    if _is_streamlit():
        if not st.session_state.get("services_initialized", False):
            initialize_streamlit_session()
        return None, st.session_state.get("service_container")

    # Without Streamlit: DatabaseManager is always None, return ServiceContainer
    return None, get_app_service_container()

# ======================================================================================
# Lifecycle / cleanup
# ======================================================================================
def cleanup_application() -> None:
    """
    Release app resources. Call on shutdown.
    - Shut down ServiceContainer
    - Drop singleton references
    - Clear session_state (if exists)
    """
    global _service_container_singleton, _db_manager_singleton

    try:
        try:
            shutdown_service_container()
        except Exception:
            pass
        _service_container_singleton = None
        _db_manager_singleton = None

        if _is_streamlit() and hasattr(st, "session_state"):
            for key in ("db_manager", "service_container", "services_initialized"):
                if key in st.session_state:
                    del st.session_state[key]

        _logger.info("Cleanup completed.")
    except Exception as e:  # pragma: no cover
        _logger.error("Error in cleanup: %s", e, exc_info=True)

def _cleanup_private_db_singletons() -> None:
    """
    Fallback to close remaining private instances in internal modules.
    Maintained for compatibility during transition. Does not fail shutdown.
    """
    closed_any = False
    try:
        from streamlit_extension.database.queries import _DBM_INSTANCE as _Q_DBM  # type: ignore
        if _Q_DBM is not None and hasattr(_Q_DBM, "close"):
            _Q_DBM.close()
            closed_any = True
    except Exception:
        pass
    try:
        from streamlit_extension.database.schema import _DBM_INSTANCE as _S_DBM  # type: ignore
        if _S_DBM is not None and hasattr(_S_DBM, "close"):
            _S_DBM.close()
            closed_any = True
    except Exception:
        pass
    try:
        from streamlit_extension.database.connection import _DBM_INSTANCE as _C_DBM  # type: ignore
        if _C_DBM is not None and hasattr(_C_DBM, "close"):
            _C_DBM.close()
            closed_any = True
    except Exception:
        pass
    if closed_any:
        _logger.info("Database resources cleaned up (fallback).")

def _atexit_handler() -> None:
    try:
        cleanup_application()
    finally:
        _cleanup_private_db_singletons()

atexit.register(_atexit_handler)

# ======================================================================================
# App "one-shot" setup
# ======================================================================================
def setup_application() -> None:
    """
    Single setup entry point for Streamlit application.
    - Initialize session/services
    - Display health status
    """
    if not _is_streamlit():
        _logger.warning("Streamlit unavailable - UI setup ignored.")
        return

    try:
        initialize_streamlit_session()
        health = check_services_health()

        if not health.get("overall", {}).get("healthy", False):
            st.error("⚠️ Services are not fully operational.")
            with st.expander("🔍 Health Details", expanded=False):
                st.json(health)
        else:
            _logger.info("Application setup completed successfully.")
    except Exception as e:  # pragma: no cover
        _logger.error("Application setup failed: %s", e, exc_info=True)
        st.error(f"❌ Application setup failed: {e}")

# ======================================================================================
# Convenient service accessors
# ======================================================================================
def _get_container() -> Optional["ServiceContainer"]:
    _, container = get_session_services()
    return container


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

# ======================================================================================
# Dev / local testing
# ======================================================================================
def reset_services(force: bool = False) -> None:
    """
    Restart all services (useful for development).
    In Streamlit, invalidates resource cache by switching key.
    """
    if not force:
        _logger.warning("reset_services requested; use force=True to confirm.")
        return

    _logger.info("Restarting services...")
    cleanup_application()
    # Recreate singletons on demand
    if _is_streamlit():
        st.session_state["services_initialized"] = False
        initialize_streamlit_session()

# ======================================================================================
# Main (smoke test)
# ======================================================================================
if __name__ == "__main__":
    logging.info("🧪 Quick test - application_setup")
    ok_db = check_database_connection()
    logging.info(f"DB ping: {'✅' if ok_db else '❌'}")

    container = get_app_service_container()
    logging.info(f"ServiceContainer: {'✅' if container else '❌'}")

    health = check_services_health()
    logging.info(f"Overall health: {'✅' if health.get('overall', {}).get('healthy') else '❌'}")
