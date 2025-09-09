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
from .config_loader_base import ConfigLoaderBase, ConfigResult
from .prompt_template_loader import PromptTemplateLoader
from .domain_lexicon_loader import DomainLexiconLoader
from .service_container import (
    ServiceContainer,
    get_service_container,
    reset_service_container,
    initialize_service_container,
    shutdown_service_container,
    get_project_service,
    get_epic_service,
    get_task_service,
    get_analytics_service,
    get_timer_service,
    check_services_health,
    get_app_service_container,
    get_priority_settings_repository
)

__all__ = [
    # Base classes
    'BaseService', 'ServiceResult', 'ServiceError',
    
    # Service implementations
    'ProjectService', 'EpicService', 'TaskService',
    'AnalyticsService', 'TimerService',
    
    # Configuration loaders (História 2.2)
    'ConfigLoaderBase', 'ConfigResult', 'PromptTemplateLoader', 'DomainLexiconLoader',
    
    # Service container
    'ServiceContainer', 'get_service_container', 'reset_service_container', 
    'initialize_service_container', 'shutdown_service_container', 'get_app_service_container',
    
    # Service accessors
    'get_project_service', 'get_epic_service', 
    'get_task_service', 'get_analytics_service', 'get_timer_service',
    'get_priority_settings_repository',
    
    # Utilities
    'check_services_health'
]
