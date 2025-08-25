"""
🏗️ Service Container

Clean Dependency Injection (DI) container for service management.
Pure modular architecture - no DatabaseManager dependencies.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, Type, TypeVar
import logging
import threading
from contextlib import contextmanager
from datetime import datetime

from .base import BaseService
from .project_service import ProjectService
from .epic_service import EpicService
from .task_service import TaskService
from .analytics_service import AnalyticsService
from .timer_service import TimerService

T = TypeVar("T", bound=BaseService)
logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Clean Dependency Injection container for business services.
    Manages service lifecycle and dependencies using modular architecture.
    """

    def __init__(self) -> None:
        self._services: Dict[Type[BaseService], BaseService] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(f"{__name__}.ServiceContainer")
        self._logger.debug("ServiceContainer initialized with modular architecture")

    # --- Core Service Registration ---

    def get_project_service(self) -> ProjectService:
        """Get or create ProjectService instance."""
        return self._get_or_create_service(ProjectService)

    def get_epic_service(self) -> EpicService:
        """Get or create EpicService instance."""
        return self._get_or_create_service(EpicService)

    def get_task_service(self) -> TaskService:
        """Get or create TaskService instance."""
        return self._get_or_create_service(TaskService)

    def get_analytics_service(self) -> AnalyticsService:
        """Get or create AnalyticsService instance."""
        return self._get_or_create_service(AnalyticsService)

    def get_timer_service(self) -> TimerService:
        """Get or create TimerService instance."""
        return self._get_or_create_service(TimerService)

    # --- Generic Service Management ---

    def _get_or_create_service(self, service_class: Type[T]) -> T:
        """Get existing service or create new instance."""
        with self._lock:
            if service_class not in self._services:
                try:
                    # All services now use modular architecture with no dependencies
                    service_instance = service_class()
                    self._services[service_class] = service_instance
                    self._logger.debug(f"Created new service instance: {service_class.__name__}")
                except Exception as e:
                    self._logger.error(f"Failed to create service {service_class.__name__}: {e}")
                    raise
            
            return self._services[service_class]

    def register_service(self, service_class: Type[T], instance: T) -> None:
        """Register a specific service instance."""
        with self._lock:
            self._services[service_class] = instance
            self._logger.debug(f"Registered service instance: {service_class.__name__}")

    def is_service_registered(self, service_class: Type[T]) -> bool:
        """Check if a service is already registered."""
        with self._lock:
            return service_class in self._services

    def clear_services(self) -> None:
        """Clear all registered services (useful for testing)."""
        with self._lock:
            self._services.clear()
            self._logger.debug("All services cleared from container")

    # --- Service Health Monitoring ---

    def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all registered services."""
        health_status = {}
        
        with self._lock:
            for service_class, service_instance in self._services.items():
                try:
                    # Basic health check - service exists and responds
                    service_name = service_class.__name__
                    health_status[service_name] = {
                        'status': 'healthy',
                        'instance_id': id(service_instance),
                        'created_at': getattr(service_instance, '_created_at', 'unknown'),
                        'class': service_class.__module__ + '.' + service_class.__name__
                    }
                except Exception as e:
                    health_status[service_class.__name__] = {
                        'status': 'unhealthy',
                        'error': str(e),
                        'instance_id': id(service_instance) if service_instance else None
                    }

        return {
            'container_status': 'healthy',
            'services_count': len(self._services),
            'services': health_status,
            'architecture': 'modular',
            'timestamp': datetime.now().isoformat()
        }

    # --- Context Management ---

    @contextmanager
    def service_scope(self):
        """Context manager for service scope management."""
        scope_services = {}
        try:
            # Store current services
            with self._lock:
                scope_services = self._services.copy()
            
            yield self
            
        finally:
            # Restore services (in case of exceptions)
            with self._lock:
                self._services = scope_services

    # --- Service Discovery ---

    def get_all_services(self) -> Dict[str, BaseService]:
        """Get all registered services by name."""
        with self._lock:
            return {cls.__name__: instance for cls, instance in self._services.items()}

    def get_service_by_name(self, service_name: str) -> Optional[BaseService]:
        """Get service by class name."""
        with self._lock:
            for service_class, service_instance in self._services.items():
                if service_class.__name__ == service_name:
                    return service_instance
            return None

    # --- Legacy Compatibility (Deprecated) ---

    def get_database_manager(self):
        """
        DEPRECATED: Legacy compatibility method.
        
        The modular architecture no longer uses DatabaseManager.
        This method is kept for backward compatibility but will raise an error.
        """
        self._logger.warning("get_database_manager() is deprecated - use modular database API instead")
        raise DeprecationWarning(
            "DatabaseManager is deprecated. "
            "Use streamlit_extension.database modules directly: "
            "queries, connection, transaction, etc."
        )

    # --- Performance Monitoring ---

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for service container."""
        metrics = {
            'services_registered': len(self._services),
            'memory_usage': self._calculate_memory_usage(),
            'service_types': [cls.__name__ for cls in self._services.keys()],
            'container_health': 'healthy',
            'architecture_type': 'modular'
        }
        
        return metrics

    def _calculate_memory_usage(self) -> Dict[str, int]:
        """Calculate approximate memory usage of services."""
        import sys
        
        memory_info = {}
        with self._lock:
            for service_class, service_instance in self._services.items():
                try:
                    memory_info[service_class.__name__] = sys.getsizeof(service_instance)
                except Exception:
                    memory_info[service_class.__name__] = 0
        
        return memory_info


# --- Global Container Instance ---

_container_instance: Optional[ServiceContainer] = None
_container_lock = threading.RLock()


def get_service_container() -> ServiceContainer:
    """Get or create global service container instance."""
    global _container_instance
    
    with _container_lock:
        if _container_instance is None:
            _container_instance = ServiceContainer()
            logger.debug("Global ServiceContainer instance created")
        
        return _container_instance


def reset_service_container() -> None:
    """Reset global service container (useful for testing)."""
    global _container_instance
    
    with _container_lock:
        _container_instance = None
        logger.debug("Global ServiceContainer instance reset")


# --- Convenience Functions ---

def get_project_service() -> ProjectService:
    """Convenience function to get ProjectService."""
    return get_service_container().get_project_service()


def get_epic_service() -> EpicService:
    """Convenience function to get EpicService."""
    return get_service_container().get_epic_service()


def get_task_service() -> TaskService:
    """Convenience function to get TaskService."""
    return get_service_container().get_task_service()


def get_analytics_service() -> AnalyticsService:
    """Convenience function to get AnalyticsService."""
    return get_service_container().get_analytics_service()


def get_timer_service() -> TimerService:
    """Convenience function to get TimerService."""
    return get_service_container().get_timer_service()


# --- Health Check Integration ---

def check_services_health() -> Dict[str, Any]:
    """Check health of all services in the container."""
    try:
        container = get_service_container()
        return container.get_service_health()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'container_status': 'unhealthy',
            'error': str(e),
            'services_count': 0,
            'architecture': 'modular'
        }


# --- Service Setup Integration ---

def get_app_service_container() -> ServiceContainer:
    """Get application service container with all services initialized."""
    container = get_service_container()
    
    # Pre-initialize all core services
    try:
        container.get_project_service()
        container.get_epic_service()
        container.get_task_service()
        container.get_analytics_service()
        container.get_timer_service()
        
        logger.info("All core services initialized successfully")
        return container
        
    except Exception as e:
        logger.error(f"Failed to initialize core services: {e}")
        raise RuntimeError(f"Service container initialization failed: {e}")