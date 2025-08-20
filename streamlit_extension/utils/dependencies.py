"""
🔗 Centralized Dependency Management

Eliminates Import Hell anti-pattern by providing a single source of truth for optional dependencies.
Replaces scattered try/except import blocks throughout the codebase.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DependencyStatus(Enum):
    """Status of a dependency."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass
class DependencyInfo:
    """Information about a dependency."""
    name: str
    module: Optional[Any]
    status: DependencyStatus
    error_message: Optional[str] = None
    fallback_available: bool = False


class DependencyManager:
    """Centralized manager for optional dependencies."""
    
    def __init__(self):
        self._dependencies: Dict[str, DependencyInfo] = {}
        self._initialize_dependencies()
    
    def _initialize_dependencies(self) -> None:
        """Initialize all known dependencies."""
        
        # Core dependencies
        self._register_dependency("streamlit", ["streamlit"], fallback_available=True)
        self._register_dependency("pandas", ["pandas"], fallback_available=False)
        self._register_dependency("plotly", ["plotly.express", "plotly.graph_objects"], fallback_available=False)
        
        # SQLAlchemy
        self._register_dependency("sqlalchemy", ["sqlalchemy"], fallback_available=True)
        
        # Analytics
        self._register_dependency("analytics_engine", ["tdah_tools.analytics_engine"], fallback_available=True)
        
        # Caching
        self._register_dependency("redis", ["redis"], fallback_available=True)
        
        # Configuration  
        self._register_dependency("timezone_utils", ["..config.streamlit_config"], fallback_available=True)
        self._register_dependency("duration_system", ["duration_system.duration_calculator"], fallback_available=True)
        
        # Themes
        self._register_dependency("themes", ["..config.themes"], fallback_available=True)
        
        # Cache system
        self._register_dependency("cache_system", ["..utils.cache"], fallback_available=True)
        
        # Auth system
        self._register_dependency("auth_system", ["..auth"], fallback_available=True)
        
        # Security
        self._register_dependency("security_manager", ["..utils.security"], fallback_available=True)
        
    def _register_dependency(
        self, 
        name: str, 
        import_paths: List[str], 
        fallback_available: bool = False
    ) -> None:
        """Register a dependency with multiple possible import paths."""
        
        module = None
        status = DependencyStatus.UNAVAILABLE
        error_message = None
        
        for import_path in import_paths:
            try:
                module = self._import_module(import_path)
                status = DependencyStatus.AVAILABLE
                logger.debug(f"Dependency '{name}' loaded successfully from '{import_path}'")
                break
            except ImportError as e:
                error_message = str(e)
                logger.debug(f"Failed to import '{import_path}' for dependency '{name}': {e}")
                continue
        
        if status == DependencyStatus.UNAVAILABLE:
            logger.info(f"Dependency '{name}' is not available. Fallback: {fallback_available}")
        
        self._dependencies[name] = DependencyInfo(
            name=name,
            module=module,
            status=status,
            error_message=error_message,
            fallback_available=fallback_available
        )
    
    def _import_module(self, import_path: str) -> Any:
        """Import a module from the given path."""
        if import_path.startswith(".."):
            # Handle relative imports
            module_name = import_path[2:].replace(".", "_")
            # This is a simplified approach - in practice you'd handle relative imports properly
            exec(f"from {import_path} import *")
            return True
        else:
            return __import__(import_path, fromlist=[''])
    
    def is_available(self, dependency_name: str) -> bool:
        """Check if a dependency is available."""
        dep = self._dependencies.get(dependency_name)
        return dep is not None and dep.status == DependencyStatus.AVAILABLE
    
    def get_module(self, dependency_name: str) -> Optional[Any]:
        """Get the module for a dependency."""
        dep = self._dependencies.get(dependency_name)
        return dep.module if dep and dep.status == DependencyStatus.AVAILABLE else None
    
    def has_fallback(self, dependency_name: str) -> bool:
        """Check if a dependency has fallback functionality."""
        dep = self._dependencies.get(dependency_name)
        return dep is not None and dep.fallback_available
    
    def get_dependency_info(self, dependency_name: str) -> Optional[DependencyInfo]:
        """Get full information about a dependency."""
        return self._dependencies.get(dependency_name)
    
    def list_dependencies(self) -> Dict[str, DependencyInfo]:
        """List all registered dependencies."""
        return self._dependencies.copy()
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get a comprehensive status report of all dependencies."""
        available = []
        unavailable = []
        with_fallback = []
        
        for name, info in self._dependencies.items():
            if info.status == DependencyStatus.AVAILABLE:
                available.append(name)
            else:
                unavailable.append(name)
                if info.fallback_available:
                    with_fallback.append(name)
        
        return {
            "total_dependencies": len(self._dependencies),
            "available": available,
            "unavailable": unavailable,
            "unavailable_with_fallback": with_fallback,
            "availability_rate": len(available) / len(self._dependencies) * 100
        }


# Global dependency manager instance
_dependency_manager: Optional[DependencyManager] = None


def get_dependency_manager() -> DependencyManager:
    """Get the global dependency manager instance."""
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = DependencyManager()
    return _dependency_manager


# Convenience functions for backward compatibility
def is_available(dependency_name: str) -> bool:
    """Check if a dependency is available."""
    return get_dependency_manager().is_available(dependency_name)


def get_module(dependency_name: str) -> Optional[Any]:
    """Get the module for a dependency."""
    return get_dependency_manager().get_module(dependency_name)


def has_fallback(dependency_name: str) -> bool:
    """Check if a dependency has fallback functionality."""
    return get_dependency_manager().has_fallback(dependency_name)


# Specific dependency checkers (for migration convenience)
def streamlit_available() -> bool:
    """Check if Streamlit is available."""
    return is_available("streamlit")


def pandas_available() -> bool:
    """Check if Pandas is available."""
    return is_available("pandas")


def plotly_available() -> bool:
    """Check if Plotly is available."""
    return is_available("plotly")


def sqlalchemy_available() -> bool:
    """Check if SQLAlchemy is available."""
    return is_available("sqlalchemy")


def analytics_engine_available() -> bool:
    """Check if Analytics Engine is available."""
    return is_available("analytics_engine")


def redis_available() -> bool:
    """Check if Redis is available."""
    return is_available("redis")


# Import Hell Elimination - Safe Import Wrappers
def safe_import_streamlit():
    """Safe import of Streamlit with fallback."""
    manager = get_dependency_manager()
    if manager.is_available("streamlit"):
        return manager.get_module("streamlit")
    else:
        logger.warning("Streamlit not available, using fallback")
        return None


def safe_import_pandas():
    """Safe import of Pandas with fallback."""
    manager = get_dependency_manager()
    if manager.is_available("pandas"):
        return manager.get_module("pandas")
    else:
        logger.warning("Pandas not available, operations will be limited")
        return None


def safe_import_plotly():
    """Safe import of Plotly with fallback."""
    manager = get_dependency_manager()
    if manager.is_available("plotly"):
        return manager.get_module("plotly")
    else:
        logger.warning("Plotly not available, charts will be disabled")
        return None


# Exception for dependency errors
class DependencyError(Exception):
    """Raised when a required dependency is not available."""
    
    def __init__(self, dependency_name: str, message: str = None):
        self.dependency_name = dependency_name
        if message is None:
            message = f"Required dependency '{dependency_name}' is not available"
        super().__init__(message)


def require_dependency(dependency_name: str) -> Any:
    """Require a dependency to be available, raise exception if not."""
    manager = get_dependency_manager()
    if not manager.is_available(dependency_name):
        dep_info = manager.get_dependency_info(dependency_name)
        error_msg = f"Required dependency '{dependency_name}' is not available"
        if dep_info and dep_info.error_message:
            error_msg += f": {dep_info.error_message}"
        raise DependencyError(dependency_name, error_msg)
    
    return manager.get_module(dependency_name)


# Exports
__all__ = [
    "DependencyManager",
    "DependencyInfo", 
    "DependencyStatus",
    "DependencyError",
    "get_dependency_manager",
    "is_available",
    "get_module", 
    "has_fallback",
    "require_dependency",
    "streamlit_available",
    "pandas_available",
    "plotly_available",
    "sqlalchemy_available",
    "analytics_engine_available",
    "redis_available",
    "safe_import_streamlit",
    "safe_import_pandas", 
    "safe_import_plotly",
]