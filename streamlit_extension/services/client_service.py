"""
👥 Client Service Layer

Business logic for client management operations.
Implements complete CRUD operations with validation and business rules.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re

from .base import (
    BaseService, ServiceResult, ServiceError, ServiceErrorType,
    BaseRepository, PaginatedResult, FilterCriteria, SortCriteria
)
from ..utils.database import DatabaseManager
from ..config.constants import ValidationRules, ClientStatus


class ClientRepository(BaseRepository):
    """Repository for client data access operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
    
    def find_by_id(self, client_id: int) -> Optional[Dict[str, Any]]:
        """Find client by ID."""
        try:
            query = "SELECT * FROM framework_clients WHERE id = ?"
            result = self.db_manager.execute_query(query, (client_id,))
            return result[0] if result else None
        except Exception as e:
            self.db_manager.logger.error(f"Error finding client by ID {client_id}: {e}")
            return None
    
    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find client by email address."""
        try:
            query = "SELECT * FROM framework_clients WHERE email = ?"
            result = self.db_manager.execute_query(query, (email,))
            return result[0] if result else None
        except Exception as e:
            self.db_manager.logger.error(f"Error finding client by email {email}: {e}")
            return None
    
    def find_all(
        self, 
        filters: Optional[FilterCriteria] = None,
        sort: Optional[SortCriteria] = None,
        page: int = 1,
        page_size: int = 10
    ) -> PaginatedResult[Dict[str, Any]]:
        """Find all clients with filtering, sorting, and pagination."""
        try:
            # Build base query
            where_conditions = []
            params = []
            
            if filters:
                if filters.has('status'):
                    where_conditions.append("status = ?")
                    params.append(filters.get('status'))
                
                if filters.has('name'):
                    where_conditions.append("name LIKE ?")
                    params.append(f"%{filters.get('name')}%")
                
                if filters.has('email'):
                    where_conditions.append("email LIKE ?")
                    params.append(f"%{filters.get('email')}%")
                
                if filters.has('company'):
                    where_conditions.append("company LIKE ?")
                    params.append(f"%{filters.get('company')}%")
            
            # Build WHERE clause
            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Build ORDER BY clause - SECURITY FIX: Use whitelist for field names
            order_clause = ""
            if sort:
                # SECURITY: Whitelist allowed fields to prevent SQL injection
                allowed_fields = {'name', 'email', 'company', 'status', 'created_at', 'updated_at', 'id'}
                if sort.field in allowed_fields:
                    direction = 'ASC' if sort.ascending else 'DESC'
                    order_clause = f" ORDER BY {sort.field} {direction}"
                else:
                    # Log security violation and use default ordering
                    self._log_security_warning(f"Invalid sort field attempted: {sort.field}")
                    order_clause = " ORDER BY name ASC"  # Safe default
            
            # Count total records (usar alias para chave estável no resultado)
            # SECURITY FIX: Use string concatenation instead of f-strings for SQL
            count_query = "SELECT COUNT(*) AS total FROM framework_clients" + where_clause
            total_count = self.db_manager.execute_query(count_query, params)[0]['total']
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = (total_count + page_size - 1) // page_size
            
            # Get paginated results
            # SECURITY FIX: Build query safely without f-strings
            data_query = "SELECT * FROM framework_clients" + where_clause + order_clause + " LIMIT ? OFFSET ?"
            data_params = params + [page_size, offset]
            clients = self.db_manager.execute_query(data_query, data_params)
            
            return PaginatedResult(
                items=clients,
                total=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            self.db_manager.logger.error(f"Error finding clients: {e}")
            # Return empty result on error
            return PaginatedResult([], 0, page, page_size, 0)
    
    def create(self, client_data: Dict[str, Any]) -> Optional[int]:
        """Create new client and return the ID."""
        try:
            query = """
                INSERT INTO framework_clients (
                    name, email, phone, company, address, 
                    contact_person, status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                client_data['name'],
                client_data['email'],
                client_data.get('phone'),
                client_data.get('company'),
                client_data.get('address'),
                client_data.get('contact_person'),
                client_data.get('status', ClientStatus.ACTIVE.value),
                client_data.get('notes'),
                datetime.now()
            )
            
            return self.db_manager.execute_insert(query, params)
            
        except Exception as e:
            self.db_manager.logger.error(f"Error creating client: {e}")
            return None
    
    def update(self, client_id: int, client_data: Dict[str, Any]) -> bool:
        """Update existing client."""
        try:
            query = """
                UPDATE framework_clients SET
                    name = ?, email = ?, phone = ?, company = ?,
                    address = ?, contact_person = ?, status = ?,
                    notes = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                client_data['name'],
                client_data['email'],
                client_data.get('phone'),
                client_data.get('company'),
                client_data.get('address'),
                client_data.get('contact_person'),
                client_data.get('status', ClientStatus.ACTIVE.value),
                client_data.get('notes'),
                datetime.now(),
                client_id
            )
            
            affected_rows = self.db_manager.execute_update(query, params)
            return affected_rows > 0
            
        except Exception as e:
            self.db_manager.logger.error(f"Error updating client {client_id}: {e}")
            return False
    
    def delete(self, client_id: int) -> bool:
        """Delete client (soft delete by changing status)."""
        try:
            query = """
                UPDATE framework_clients SET
                    status = ?, updated_at = ?
                WHERE id = ?
            """
            params = (ClientStatus.INACTIVE.value, datetime.now(), client_id)
            
            affected_rows = self.db_manager.execute_update(query, params)
            return affected_rows > 0
            
        except Exception as e:
            self.db_manager.logger.error(f"Error deleting client {client_id}: {e}")
            return False
    
    def count_projects(self, client_id: int) -> int:
        """Count projects for a client."""
        try:
            query = "SELECT COUNT(*) FROM framework_projects WHERE client_id = ?"
            result = self.db_manager.execute_query(query, (client_id,))
            return result[0]['COUNT(*)'] if result else 0
        except Exception as e:
            self.db_manager.logger.error(f"Error counting projects for client {client_id}: {e}")
            return 0


class ClientService(BaseService):
    """Service for client business logic operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.repository = ClientRepository(db_manager)
        super().__init__(self.repository)
        
    def _log_security_warning(self, message: str) -> None:
        """Log security-related warnings."""
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"SECURITY: {message}")
    
    def validate_business_rules(self, data: Dict[str, Any]) -> List[ServiceError]:
        """Validate client-specific business rules."""
        errors = []
        
        # Email format validation
        if 'email' in data and data['email']:
            email_pattern = ValidationRules.EMAIL_PATTERN.value
            if not re.match(email_pattern, data['email']):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Invalid email format",
                    field="email"
                ))
        
        # Name length validation
        if 'name' in data and data['name']:
            if len(data['name']) > ValidationRules.MAX_NAME_LENGTH.value:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message=f"Name cannot exceed {ValidationRules.MAX_NAME_LENGTH.value} characters",
                    field="name"
                ))
        
        # Phone number format (if provided)
        if 'phone' in data and data['phone']:
            # Simple phone validation - can be enhanced
            phone_cleaned = re.sub(r'[^\d+()-\s]', '', data['phone'])
            if len(phone_cleaned) < 10:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Phone number appears to be invalid",
                    field="phone"
                ))
        
        # Status validation
        if 'status' in data and data['status']:
            valid_statuses = ClientStatus.get_all_values()
            if data['status'] not in valid_statuses:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message=f"Status must be one of: {', '.join(valid_statuses)}",
                    field="status"
                ))
        
        return errors
    
    def create_client(self, client_data: Dict[str, Any]) -> ServiceResult[int]:
        """
        Create a new client with validation.
        
        Args:
            client_data: Client information dictionary
            
        Returns:
            ServiceResult with client ID if successful
        """
        self.log_operation("create_client", client_data=client_data)
        
        # Validate required fields
        required_fields = ['name', 'email']
        validation_errors = self.validate_required_fields(client_data, required_fields)
        
        # Validate business rules
        business_errors = self.validate_business_rules(client_data)
        validation_errors.extend(business_errors)
        
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        # Check email uniqueness
        existing_client = self.repository.find_by_email(client_data['email'])
        if existing_client:
            return ServiceResult.business_rule_violation(
                f"Client with email '{client_data['email']}' already exists"
            )
        
        try:
            # Create client
            client_id = self.repository.create(client_data)
            
            if client_id:
                self.log_operation("create_client_success", client_id=client_id)
                return ServiceResult.ok(client_id)
            else:
                return self.handle_database_error("create_client", Exception("Failed to create client"))
                
        except Exception as e:
            return self.handle_database_error("create_client", e)
    
    def get_client(self, client_id: int) -> ServiceResult[Dict[str, Any]]:
        """
        Get client by ID.
        
        Args:
            client_id: Client ID
            
        Returns:
            ServiceResult with client data if found
        """
        self.log_operation("get_client", client_id=client_id)
        
        try:
            client = self.repository.find_by_id(client_id)
            
            if client:
                return ServiceResult.ok(client)
            else:
                return ServiceResult.not_found("Client", client_id)
                
        except Exception as e:
            return self.handle_database_error("get_client", e)
    
    def update_client(self, client_id: int, client_data: Dict[str, Any]) -> ServiceResult[bool]:
        """
        Update existing client.
        
        Args:
            client_id: Client ID
            client_data: Updated client information
            
        Returns:
            ServiceResult with success status
        """
        self.log_operation("update_client", client_id=client_id, client_data=client_data)
        
        # Check if client exists
        existing_client = self.repository.find_by_id(client_id)
        if not existing_client:
            return ServiceResult.not_found("Client", client_id)
        
        # Validate required fields
        required_fields = ['name', 'email']
        validation_errors = self.validate_required_fields(client_data, required_fields)
        
        # Validate business rules
        business_errors = self.validate_business_rules(client_data)
        validation_errors.extend(business_errors)
        
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        # Check email uniqueness (excluding current client)
        if 'email' in client_data:
            existing_email_client = self.repository.find_by_email(client_data['email'])
            if existing_email_client and existing_email_client['id'] != client_id:
                return ServiceResult.business_rule_violation(
                    f"Another client with email '{client_data['email']}' already exists"
                )
        
        try:
            # Update client
            success = self.repository.update(client_id, client_data)
            
            if success:
                self.log_operation("update_client_success", client_id=client_id)
                return ServiceResult.ok(True)
            else:
                return ServiceResult.business_rule_violation("Failed to update client")
                
        except Exception as e:
            return self.handle_database_error("update_client", e)
    
    def delete_client(self, client_id: int) -> ServiceResult[bool]:
        """
        Delete client (soft delete).
        
        Args:
            client_id: Client ID
            
        Returns:
            ServiceResult with success status
        """
        self.log_operation("delete_client", client_id=client_id)
        
        # Check if client exists
        existing_client = self.repository.find_by_id(client_id)
        if not existing_client:
            return ServiceResult.not_found("Client", client_id)
        
        # Check if client has active projects
        project_count = self.repository.count_projects(client_id)
        if project_count > 0:
            return ServiceResult.business_rule_violation(
                f"Cannot delete client with {project_count} active projects. "
                "Please delete or reassign projects first."
            )
        
        try:
            # Soft delete client
            success = self.repository.delete(client_id)
            
            if success:
                self.log_operation("delete_client_success", client_id=client_id)
                return ServiceResult.ok(True)
            else:
                return ServiceResult.business_rule_violation("Failed to delete client")
                
        except Exception as e:
            return self.handle_database_error("delete_client", e)
    
    def list_clients(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "name",
        sort_ascending: bool = True,
        page: int = 1,
        page_size: int = 10
    ) -> ServiceResult[PaginatedResult[Dict[str, Any]]]:
        """
        List clients with filtering, sorting, and pagination.
        
        Args:
            filters: Filter criteria dictionary
            sort_by: Field to sort by
            sort_ascending: Sort direction
            page: Page number (1-based)
            page_size: Items per page
            
        Returns:
            ServiceResult with paginated client list
        """
        self.log_operation("list_clients", filters=filters, sort_by=sort_by, page=page)
        
        try:
            # Validate pagination parameters
            if page < 1:
                return ServiceResult.validation_error("Page number must be >= 1", "page")
            
            if page_size < 1 or page_size > 100:
                return ServiceResult.validation_error(
                    "Page size must be between 1 and 100", "page_size"
                )
            
            # Create filter and sort criteria
            filter_criteria = FilterCriteria(**filters) if filters else None
            sort_criteria = SortCriteria(sort_by, sort_ascending)
            
            # Get paginated results
            result = self.repository.find_all(filter_criteria, sort_criteria, page, page_size)
            
            self.log_operation("list_clients_success", 
                             total_clients=result.total, 
                             page=page, 
                             returned_count=len(result.items))
            
            return ServiceResult.ok(result)
            
        except Exception as e:
            return self.handle_database_error("list_clients", e)
    
    def get_client_summary(self, client_id: int) -> ServiceResult[Dict[str, Any]]:
        """
        Get client summary with project count and other metrics.
        
        Args:
            client_id: Client ID
            
        Returns:
            ServiceResult with client summary data
        """
        self.log_operation("get_client_summary", client_id=client_id)
        
        try:
            # Get client data
            client_result = self.get_client(client_id)
            if not client_result.success:
                return client_result
            
            client = client_result.data
            
            # Get additional metrics
            project_count = self.repository.count_projects(client_id)
            
            # Build summary
            summary = {
                **client,
                'project_count': project_count,
                'has_projects': project_count > 0,
                'status_display': ClientStatus.get_display_name(client.get('status', 'active'))
            }
            
            return ServiceResult.ok(summary)
            
        except Exception as e:
            return self.handle_database_error("get_client_summary", e)
    
    def validate_client_data(self, client_data: Dict[str, Any]) -> ServiceResult[bool]:
        """
        Validate client data without creating/updating.
        
        Args:
            client_data: Client data to validate
            
        Returns:
            ServiceResult indicating if data is valid
        """
        # Validate required fields
        required_fields = ['name', 'email']
        validation_errors = self.validate_required_fields(client_data, required_fields)
        
        # Validate business rules
        business_errors = self.validate_business_rules(client_data)
        validation_errors.extend(business_errors)
        
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        return ServiceResult.ok(True)