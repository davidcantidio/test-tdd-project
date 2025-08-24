"""
🏗️ Service Layer Package

Service layer implementation for TDD Framework that separates business logic
from presentation layer. Addresses report.md requirement:
"Implement service layer for DB separation"

This package provides:
- Business logic abstraction
- Repository pattern for data access
- Dependency injection for testing
- Result pattern for error handling
- Transaction management
"""

from .base import BaseService, ServiceResult, ServiceError
from .project_service import ProjectService
from .epic_service import EpicService
from .task_service import TaskService
from .analytics_service import AnalyticsService
from .timer_service import TimerService
from .service_container import (
    ServiceContainer,
    initialize_service_container,
    get_service_container,
    shutdown_service_container,
    get_project_service,
    get_epic_service,
    get_task_service,
    get_analytics_service,
    get_timer_service,
    check_service_health
)

__all__ = [
    # Base classes
    'BaseService', 'ServiceResult', 'ServiceError',
    
    # Service implementations
    'ProjectService', 'EpicService', 'TaskService',
    'AnalyticsService', 'TimerService',
    
    # Service container
    'ServiceContainer', 'initialize_service_container', 'get_service_container', 'shutdown_service_container',
    
    # Service accessors
    'get_project_service', 'get_epic_service', 
    'get_task_service', 'get_analytics_service', 'get_timer_service',
    
    # Utilities
    'check_service_health'
]