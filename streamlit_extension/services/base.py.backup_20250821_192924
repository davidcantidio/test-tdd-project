"""
🏗️ Service Layer Base Classes

Base infrastructure for service layer pattern implementation.
Provides common patterns and utilities for all services.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Generic, TypeVar, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from contextlib import contextmanager
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole

# Type variable for generic result types
T = TypeVar('T')

logger = logging.getLogger(__name__)


class ServiceErrorType(Enum):
    """Types of service errors."""
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"
    DATABASE_ERROR = "database_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    INTERNAL_ERROR = "internal_error"


@dataclass
class ServiceError:
    """Represents an error that occurred in a service operation."""
    error_type: ServiceErrorType
    message: str
    details: Optional[Dict[str, Any]] = None
    field: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.error_type.value}: {self.message}"


@dataclass
class ServiceResult(Generic[T]):
    """
    Result wrapper for service operations using Result pattern.
    
    Encapsulates both success and error cases to enable clean error handling
    without exceptions in business logic.
    """
    success: bool
    data: Optional[T] = None
    errors: List[ServiceError] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @classmethod
    def ok(cls, data: T) -> 'ServiceResult[T]':
        """Create a successful result."""
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: ServiceError) -> 'ServiceResult[T]':
        """Create a failed result with single error."""
        return cls(success=False, errors=[error])
    
    @classmethod
    def fail_multiple(cls, errors: List[ServiceError]) -> 'ServiceResult[T]':
        """Create a failed result with multiple errors."""
        return cls(success=False, errors=errors)
    
    @classmethod
    def validation_error(cls, message: str, field: Optional[str] = None) -> 'ServiceResult[T]':
        """Create a validation error result."""
        error = ServiceError(
            error_type=ServiceErrorType.VALIDATION_ERROR,
            message=message,
            field=field
        )
        return cls.fail(error)
    
    @classmethod
    def not_found(cls, entity: str, identifier: Any) -> 'ServiceResult[T]':
        """Create a not found error result."""
        error = ServiceError(
            error_type=ServiceErrorType.NOT_FOUND,
            message=f"{entity} not found: {identifier}"
        )
        return cls.fail(error)
    
    @classmethod
    def business_rule_violation(cls, message: str, details: Optional[Dict[str, Any]] = None) -> 'ServiceResult[T]':
        """Create a business rule violation error."""
        error = ServiceError(
            error_type=ServiceErrorType.BUSINESS_RULE_VIOLATION,
            message=message,
            details=details
        )
        return cls.fail(error)
    
    def add_error(self, error: ServiceError) -> None:
        """Add an error to the result."""
        self.success = False
        self.errors.append(error)
    
    def get_error_messages(self) -> List[str]:
        """Get all error messages as a list of strings."""
        return [str(error) for error in self.errors]
    
    def get_first_error(self) -> Optional[ServiceError]:
        """Get the first error if any."""
        return self.errors[0] if self.errors else None


class BaseRepository(ABC):
    """
    Base class for repository pattern implementation.
    
    Repositories encapsulate data access logic and provide a clean interface
    for services to interact with data storage.
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        try:
            # Start transaction (implementation depends on database manager)
            yield
            # Commit if no exception
        except Exception as e:
            # Rollback on exception
            logger.error(f"Transaction failed: {e}")
            raise


class BaseService(ABC):
    """
    Base class for all service implementations.
    
    Services contain business logic and coordinate between repositories,
    external services, and other components to fulfill business requirements.
    """
    
    def __init__(self, repository: Optional[BaseRepository] = None):
        self.repository = repository
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def log_operation(self, operation: str, **kwargs) -> None:
        """Log service operations for audit and debugging."""
        self.logger.info(f"Service operation: {operation}", extra=kwargs)
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> List[ServiceError]:
        """Validate that required fields are present and not empty."""
        errors = []
        
        for field in required_fields:
            if field not in data:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message=f"Required field '{field}' is missing",
                    field=field
                ))
            elif not data[field] or (isinstance(data[field], str) and not data[field].strip()):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message=f"Required field '{field}' cannot be empty",
                    field=field
                ))
        
        return errors
    
    def validate_business_rules(self, data: Dict[str, Any]) -> List[ServiceError]:
        """
        Validate business-specific rules. Override in subclasses.
        
        Args:
            data: Data to validate
            
        Returns:
            List of validation errors
        """
        return []
    
    def handle_database_error(self, operation: str, error: Exception) -> ServiceResult[Any]:
        """Handle database errors with consistent error mapping."""
        self.logger.error(f"Database error in {operation}: {error}")
        
        service_error = ServiceError(
            error_type=ServiceErrorType.DATABASE_ERROR,
            message=f"Database operation failed: {operation}",
            details={"original_error": str(error)}
        )
        
        return ServiceResult.fail(service_error)


class PaginatedResult(Generic[T]):
    """Result wrapper for paginated data."""
    
    def __init__(
        self,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
        total_pages: int
    ):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = total_pages
    
    @property
    def has_next(self) -> bool:
        """Check if there are more pages."""
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Check if there are previous pages."""
        return self.page > 1


class FilterCriteria:
    """Represents filtering criteria for queries."""
    
    def __init__(self, **filters):
        self.filters = filters
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get filter value by key."""
        return self.filters.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if filter exists."""
        return key in self.filters and self.filters[key] is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.filters.copy()


class SortCriteria:
    """Represents sorting criteria for queries."""
    
    def __init__(self, field: str, ascending: bool = True):
        self.field = field
        self.ascending = ascending
    
    def __str__(self) -> str:
        direction = "ASC" if self.ascending else "DESC"
        return f"{self.field} {direction}"


# Utility functions for service layer
@require_auth()
def create_success_result(data: T) -> ServiceResult[T]:
    """Utility function to create successful result."""
    return ServiceResult.ok(data)
@require_auth()
def create_error_result(error_type: ServiceErrorType, message: str, **kwargs) -> ServiceResult[Any]:
    """Utility function to create error result."""
    error = ServiceError(error_type=error_type, message=message, **kwargs)
    return ServiceResult.fail(error)


def combine_results(*results: ServiceResult) -> ServiceResult[List[Any]]:
    """
    Combine multiple service results into one.
    
    If any result failed, return a failed result with all errors.
    If all succeeded, return success with all data.
    """
    all_errors = []
    all_data = []
    
    for result in results:
        if not result.success:
            all_errors.extend(result.errors)
        else:
            all_data.append(result.data)
    
    if all_errors:
        return ServiceResult.fail_multiple(all_errors)
    else:
        return ServiceResult.ok(all_data)