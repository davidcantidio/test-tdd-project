"""
Dependency Injection System
Provides IoC container for DatabaseManager and other services
"""

import threading
import inspect
from typing import Any, Callable, Dict, Type, TypeVar, Optional, Union
from functools import wraps
from contextlib import contextmanager

T = TypeVar('T')

class DependencyContainer:
    """IoC container for dependency injection"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._scoped: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._scope_stack = []
    
    def register_singleton(self, interface: Type[T], implementation: Union[Type[T], Callable[[], T]], name: str = None) -> None:
        """Register a singleton service"""
        service_name = name or interface.__name__
        
        with self._lock:
            if callable(implementation) and not inspect.isclass(implementation):
                # Factory function
                self._factories[service_name] = implementation
            else:
                # Class constructor
                self._factories[service_name] = implementation
            
            self._services[service_name] = 'singleton'
    
    def register_transient(self, interface: Type[T], implementation: Union[Type[T], Callable[[], T]], name: str = None) -> None:
        """Register a transient service (new instance each time)"""
        service_name = name or interface.__name__
        
        with self._lock:
            if callable(implementation) and not inspect.isclass(implementation):
                self._factories[service_name] = implementation
            else:
                self._factories[service_name] = implementation
            
            self._services[service_name] = 'transient'
    
    def register_scoped(self, interface: Type[T], implementation: Union[Type[T], Callable[[], T]], name: str = None) -> None:
        """Register a scoped service (one instance per scope)"""
        service_name = name or interface.__name__
        
        with self._lock:
            if callable(implementation) and not inspect.isclass(implementation):
                self._factories[service_name] = implementation
            else:
                self._factories[service_name] = implementation
            
            self._services[service_name] = 'scoped'
    
    def get(self, interface: Type[T], name: str = None) -> T:
        """Get service instance"""
        service_name = name or interface.__name__
        
        with self._lock:
            if service_name not in self._services:
                raise ValueError(f"Service {service_name} not registered")
            
            service_type = self._services[service_name]
            factory = self._factories[service_name]
            
            if service_type == 'singleton':
                if service_name not in self._singletons:
                    self._singletons[service_name] = self._create_instance(factory)
                return self._singletons[service_name]
            
            elif service_type == 'scoped':
                scope_id = id(self._scope_stack[-1]) if self._scope_stack else 'default'
                scoped_key = f"{service_name}_{scope_id}"
                
                if scoped_key not in self._scoped:
                    self._scoped[scoped_key] = self._create_instance(factory)
                return self._scoped[scoped_key]
            
            else:  # transient
                return self._create_instance(factory)
    
    def _create_instance(self, factory: Callable) -> Any:
        """Create service instance with dependency injection"""
        if inspect.isclass(factory):
            # Class constructor - check for dependencies
            sig = inspect.signature(factory.__init__)
            kwargs = {}
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                if param.annotation != inspect.Parameter.empty:
                    # Try to resolve dependency
                    try:
                        kwargs[param_name] = self.get(param.annotation)
                    except ValueError:
                        # Dependency not registered, use default if available
                        if param.default != inspect.Parameter.empty:
                            kwargs[param_name] = param.default
                        else:
                            raise ValueError(f"Cannot resolve dependency {param.annotation} for {factory}")
            
            return factory(**kwargs)
        else:
            # Factory function
            return factory()
    
    @contextmanager
    def scope(self):
        """Create a dependency scope"""
        scope_obj = object()
        self._scope_stack.append(scope_obj)
        
        try:
            yield
        finally:
            self._scope_stack.pop()
            
            # Cleanup scoped instances
            scope_id = id(scope_obj)
            keys_to_remove = [key for key in self._scoped.keys() if key.endswith(f"_{scope_id}")]
            for key in keys_to_remove:
                del self._scoped[key]
    
    def clear(self) -> None:
        """Clear all registered services"""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()
            self._scoped.clear()

# Global container instance
container = DependencyContainer()

# Decorators for easy registration
def singleton(interface: Type = None, name: str = None):
    """Decorator to register class as singleton"""
    def decorator(cls):
        service_interface = interface or cls
        container.register_singleton(service_interface, cls, name)
        return cls
    return decorator

def transient(interface: Type = None, name: str = None):
    """Decorator to register class as transient"""
    def decorator(cls):
        service_interface = interface or cls
        container.register_transient(service_interface, cls, name)
        return cls
    return decorator

def scoped(interface: Type = None, name: str = None):
    """Decorator to register class as scoped"""
    def decorator(cls):
        service_interface = interface or cls
        container.register_scoped(service_interface, cls, name)
        return cls
    return decorator

def inject(func: Callable) -> Callable:
    """Decorator to inject dependencies into function parameters"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        
        for param_name, param in sig.parameters.items():
            if param_name not in kwargs and param.annotation != inspect.Parameter.empty:
                try:
                    kwargs[param_name] = container.get(param.annotation)
                except ValueError:
                    # Dependency not available, use default if provided
                    if param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
        
        return func(*args, **kwargs)
    
    return wrapper

# Convenience functions
def get_service(interface: Type[T], name: str = None) -> T:
    """Get service from container"""
    return container.get(interface, name)

def with_scope():
    """Context manager for dependency scope"""
    return container.scope()

# Integration with existing DatabaseManager
def setup_database_injection():
    """Setup dependency injection for database services"""
    from .database import DatabaseManager
    
    # Register DatabaseManager as singleton
    container.register_singleton(DatabaseManager, DatabaseManager)
    
    # Register health monitoring
    try:
        from ..endpoints.health_monitoring import HealthMonitor
        container.register_singleton(HealthMonitor, HealthMonitor)
    except ImportError:
        pass
    
    # Register connection resilience
    try:
        from .connection_resilience import DatabaseResilience
        container.register_singleton(DatabaseResilience, DatabaseResilience)
    except ImportError:
        pass

# Example usage classes
@singleton()
class ConfigurationService:
    """Configuration service example"""
    
    def __init__(self):
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration"""
        self.config = {
            'database_url': 'framework.db',
            'log_level': 'INFO',
            'cache_enabled': True
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

@scoped()  
class RequestContextService:
    """Request context service example"""
    
    def __init__(self):
        self.request_id = None
        self.user_id = None
        self.start_time = None
    
    def set_context(self, request_id: str, user_id: str = None):
        self.request_id = request_id
        self.user_id = user_id
        import time
        self.start_time = time.time()

# Initialize dependency injection
def initialize_dependencies():
    """Initialize all dependency registrations"""
    setup_database_injection()
    
    # Register configuration service
    container.register_singleton(ConfigurationService, ConfigurationService)
    
    # Register request context service
    container.register_scoped(RequestContextService, RequestContextService)