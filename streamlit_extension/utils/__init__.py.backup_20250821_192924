"""Utility functions for Streamlit extension."""

from .database import DatabaseManager
from .validators import validate_config
from .load_tester import LoadTester
from .metrics_collector import MetricsCollector
from .performance_monitor import PerformanceMonitor
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


__all__ = [
    "DatabaseManager",
    "validate_config",
    "LoadTester",
    "MetricsCollector",
    "PerformanceMonitor",
]

# Guarda de import opcional para ambientes de teste sem todos os módulos
# (evita ImportError imediato ao importar o pacote).