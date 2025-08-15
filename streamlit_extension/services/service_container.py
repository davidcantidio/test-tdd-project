"""
🏗️ Service Container

Dependency injection container for managing service instances.
Provides centralized service creation and lifecycle management.
"""

from typing import Dict, Any, Optional, Type, TypeVar
import logging
from contextlib import contextmanager

from .base import BaseService
from .client_service import ClientService
from .project_service import ProjectService
from .epic_service import EpicService
from .task_service import TaskService
from .analytics_service import AnalyticsService
from .timer_service import TimerService
from ..utils.database import DatabaseManager

# Type variable for service types
T = TypeVar('T', bound=BaseService)


class ServiceError(Exception):
    """Exception raised by service container operations."""
    pass


class ServiceContainer:
    """
    Dependency injection container for managing service instances.
    
    Provides singleton service instances and manages their lifecycle.
    Supports both eager and lazy initialization of services.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize service container.
        
        Args:
            db_manager: Database manager instance to inject into services
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Service registry
        self._services: Dict[str, BaseService] = {}
        self._service_classes: Dict[str, Type[BaseService]] = {
            'client': ClientService,
            'project': ProjectService,
            'epic': EpicService,
            'task': TaskService,
            'analytics': AnalyticsService,
            'timer': TimerService,
        }
        
        # Configuration
        self._lazy_loading = True
        self._initialized = False
    
    def initialize(self, lazy_loading: bool = True) -> None:
        """
        Initialize the service container.
        
        Args:
            lazy_loading: If True, services are created on-demand. 
                         If False, all services are created immediately.
        """
        self._lazy_loading = lazy_loading
        
        if not lazy_loading:
            # Eagerly initialize all services
            for service_name in self._service_classes.keys():
                self._create_service(service_name)
        
        self._initialized = True
        self.logger.info(f"Service container initialized (lazy_loading={lazy_loading})")
    
    def get_client_service(self) -> ClientService:
        """Get the client service instance."""
        return self._get_service('client', ClientService)
    
    def get_project_service(self) -> ProjectService:
        """Get the project service instance."""
        return self._get_service('project', ProjectService)
    
    def get_epic_service(self) -> EpicService:
        """Get the epic service instance."""
        return self._get_service('epic', EpicService)
    
    def get_task_service(self) -> TaskService:
        """Get the task service instance."""
        return self._get_service('task', TaskService)
    
    def get_analytics_service(self) -> AnalyticsService:
        """Get the analytics service instance."""
        return self._get_service('analytics', AnalyticsService)
    
    def get_timer_service(self) -> TimerService:
        """Get the timer service instance."""
        return self._get_service('timer', TimerService)
    
    def get_service(self, service_name: str) -> BaseService:
        """
        Get a service by name.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            Service instance
            
        Raises:
            ServiceError: If service name is not recognized
        """
        if service_name not in self._service_classes:
            raise ServiceError(f"Unknown service: {service_name}")
        
        return self._get_service(service_name, self._service_classes[service_name])
    
    def register_service(self, service_name: str, service_class: Type[BaseService]) -> None:
        """
        Register a new service class.
        
        Args:
            service_name: Name to register the service under
            service_class: Service class to register
        """
        self._service_classes[service_name] = service_class
        
        # If not lazy loading and already initialized, create the service immediately
        if not self._lazy_loading and self._initialized:
            self._create_service(service_name)
        
        self.logger.info(f"Registered service: {service_name} -> {service_class.__name__}")
    
    def has_service(self, service_name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            True if service is registered, False otherwise
        """
        return service_name in self._service_classes
    
    def list_services(self) -> Dict[str, str]:
        """
        List all registered services.
        
        Returns:
            Dictionary mapping service names to class names
        """
        return {
            name: cls.__name__ 
            for name, cls in self._service_classes.items()
        }
    
    def is_service_created(self, service_name: str) -> bool:
        """
        Check if a service instance has been created.
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            True if service instance exists, False otherwise
        """
        return service_name in self._services
    
    def clear_service(self, service_name: str) -> None:
        """
        Clear a service instance (will be recreated on next access).
        
        Args:
            service_name: Name of the service to clear
        """
        if service_name in self._services:
            del self._services[service_name]
            self.logger.info(f"Cleared service instance: {service_name}")
    
    def clear_all_services(self) -> None:
        """Clear all service instances."""
        service_names = list(self._services.keys())
        self._services.clear()
        self.logger.info(f"Cleared all service instances: {service_names}")
    
    def shutdown(self) -> None:
        """Shutdown the service container and cleanup resources."""
        self.clear_all_services()
        self._initialized = False
        self.logger.info("Service container shutdown")
    
    @contextmanager
    def transaction_scope(self):
        """
        Context manager for transactional operations across multiple services.
        
        This ensures all service operations within the scope use the same
        database transaction context.
        """
        # Note: Actual transaction implementation would depend on the database manager
        # For now, this is a placeholder for future transaction management
        try:
            yield self
        except Exception as e:
            # In a real implementation, this would rollback the transaction
            self.logger.error(f"Transaction scope error: {e}")
            raise
    
    def validate_services(self) -> Dict[str, bool]:
        """
        Validate all registered services can be created successfully.
        
        Returns:
            Dictionary mapping service names to validation results
        """
        results = {}
        
        for service_name in self._service_classes.keys():
            try:
                # Try to create the service
                service = self._create_service(service_name, validate_only=True)
                results[service_name] = True
                self.logger.debug(f"Service validation passed: {service_name}")
            except Exception as e:
                results[service_name] = False
                self.logger.error(f"Service validation failed: {service_name} - {e}")
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get status information about the service container.
        
        Returns:
            Dictionary with container status information
        """
        return {
            'initialized': self._initialized,
            'lazy_loading': self._lazy_loading,
            'registered_services': list(self._service_classes.keys()),
            'created_services': list(self._services.keys()),
            'service_count': len(self._service_classes),
            'created_count': len(self._services)
        }
    
    def _get_service(self, service_name: str, service_class: Type[T]) -> T:
        """
        Get or create a service instance.
        
        Args:
            service_name: Name of the service
            service_class: Expected service class type
            
        Returns:
            Service instance
        """
        if service_name not in self._services:
            if not self._initialized:
                raise ServiceError("Service container not initialized. Call initialize() first.")
            
            self._services[service_name] = self._create_service(service_name)
        
        service = self._services[service_name]
        
        # Type check for safety
        if not isinstance(service, service_class):
            raise ServiceError(
                f"Service type mismatch: expected {service_class.__name__}, "
                f"got {type(service).__name__}"
            )
        
        return service
    
    def _create_service(self, service_name: str, validate_only: bool = False) -> BaseService:
        """
        Create a new service instance.
        
        Args:
            service_name: Name of the service to create
            validate_only: If True, don't store the service instance
            
        Returns:
            New service instance
            
        Raises:
            ServiceError: If service cannot be created
        """
        if service_name not in self._service_classes:
            raise ServiceError(f"Unknown service: {service_name}")
        
        service_class = self._service_classes[service_name]
        
        try:
            # Create service with database manager dependency
            service = service_class(self.db_manager)
            
            if not validate_only:
                self.logger.debug(f"Created service: {service_name} -> {service_class.__name__}")
            
            return service
            
        except Exception as e:
            raise ServiceError(f"Failed to create service {service_name}: {e}") from e


# Global service container instance
_service_container: Optional[ServiceContainer] = None


def get_service_container() -> ServiceContainer:
    """
    Get the global service container instance.
    
    Returns:
        Global service container
        
    Raises:
        ServiceError: If container not initialized
    """
    global _service_container
    
    if _service_container is None:
        raise ServiceError(
            "Service container not initialized. Call initialize_service_container() first."
        )
    
    return _service_container


def initialize_service_container(db_manager: DatabaseManager, lazy_loading: bool = True) -> ServiceContainer:
    """
    Initialize the global service container.
    
    Args:
        db_manager: Database manager instance
        lazy_loading: Whether to use lazy loading for services
        
    Returns:
        Initialized service container
    """
    global _service_container
    
    if _service_container is not None:
        _service_container.shutdown()
    
    _service_container = ServiceContainer(db_manager)
    _service_container.initialize(lazy_loading)
    
    return _service_container


def shutdown_service_container() -> None:
    """Shutdown the global service container."""
    global _service_container
    
    if _service_container is not None:
        _service_container.shutdown()
        _service_container = None


# Convenience functions for accessing services
def get_client_service() -> ClientService:
    """Get the client service from the global container."""
    return get_service_container().get_client_service()


def get_project_service() -> ProjectService:
    """Get the project service from the global container."""
    return get_service_container().get_project_service()


def get_epic_service() -> EpicService:
    """Get the epic service from the global container."""
    return get_service_container().get_epic_service()


def get_task_service() -> TaskService:
    """Get the task service from the global container."""
    return get_service_container().get_task_service()


def get_analytics_service() -> AnalyticsService:
    """Get the analytics service from the global container."""
    return get_service_container().get_analytics_service()


def get_timer_service() -> TimerService:
    """Get the timer service from the global container."""
    return get_service_container().get_timer_service()


# Context managers for service operations
@contextmanager
def service_transaction():
    """Context manager for transactional service operations."""
    container = get_service_container()
    with container.transaction_scope():
        yield container


# Service health check functions
def check_service_health() -> Dict[str, Any]:
    """
    Perform health check on all services.
    
    Returns:
        Health status for all services
    """
    try:
        container = get_service_container()
        
        # Validate all services
        validation_results = container.validate_services()
        
        # Get container status
        status = container.get_service_status()
        
        # Overall health
        all_healthy = all(validation_results.values())
        
        return {
            'overall_health': 'healthy' if all_healthy else 'unhealthy',
            'container_status': status,
            'service_validation': validation_results,
            'timestamp': logging.Formatter().formatTime(logging.LogRecord(
                '', 0, '', 0, '', (), None
            ))
        }
        
    except Exception as e:
        return {
            'overall_health': 'error',
            'error': str(e),
            'timestamp': logging.Formatter().formatTime(logging.LogRecord(
                '', 0, '', 0, '', (), None
            ))
        }


# Example usage and testing functions
def example_service_usage():
    """Example of how to use the service container."""
    # This would typically be done in your application startup
    from ..utils.database import DatabaseManager
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Initialize service container
    container = initialize_service_container(db_manager, lazy_loading=True)
    
    # Use services
    try:
        # Get services
        client_service = get_client_service()
        project_service = get_project_service()
        epic_service = get_epic_service()
        task_service = get_task_service()
        analytics_service = get_analytics_service()
        timer_service = get_timer_service()
        
        # Example operations
        clients_result = client_service.list_clients()
        if clients_result.success:
            print(f"Found {clients_result.data.total} clients")
        
        # Example analytics
        dashboard_result = analytics_service.get_dashboard_summary()
        if dashboard_result.success:
            print(f"Dashboard generated with {dashboard_result.data['overview']['total_projects']} projects")
        
        # Example timer
        active_session_result = timer_service.get_active_session()
        if active_session_result.success and active_session_result.data:
            print(f"Active session: {active_session_result.data['elapsed_minutes']} minutes elapsed")
        
        # Use transaction scope for related operations
        with service_transaction() as container:
            # Perform multiple related operations
            pass
            
    finally:
        # Cleanup
        shutdown_service_container()


if __name__ == "__main__":
    # Run example if this file is executed directly
    example_service_usage()