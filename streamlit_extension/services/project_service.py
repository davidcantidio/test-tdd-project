"""
📁 Project Service Layer

Business logic for project management operations.
Implements complete CRUD operations with validation.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
import re

from .base import (
    BaseService, ServiceResult, ServiceError, ServiceErrorType,
    BaseRepository, PaginatedResult, FilterCriteria, SortCriteria
)
from ..utils.database import DatabaseManager
from ..config.constants import ValidationRules, ProjectStatus


class ProjectRepository(BaseRepository):
    # Delegation to ProjectRepositoryDataaccess
    def __init__(self):
        self._projectrepositorydataaccess = ProjectRepositoryDataaccess()
    # Delegation to ProjectRepositoryLogging
    def __init__(self):
        self._projectrepositorylogging = ProjectRepositoryLogging()
    # Delegation to ProjectRepositoryErrorhandling
    def __init__(self):
        self._projectrepositoryerrorhandling = ProjectRepositoryErrorhandling()
    # Delegation to ProjectRepositoryFormatting
    def __init__(self):
        self._projectrepositoryformatting = ProjectRepositoryFormatting()
    # Delegation to ProjectRepositoryNetworking
    def __init__(self):
        self._projectrepositorynetworking = ProjectRepositoryNetworking()
    # Delegation to ProjectRepositoryCalculation
    def __init__(self):
        self._projectrepositorycalculation = ProjectRepositoryCalculation()
    """Repository for project data access operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
    
    def find_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Find project by ID."""
        try:
            query = """
                SELECT p.*
                FROM framework_projects p
                WHERE p.id = ?
            """
            result = self.db_manager.execute_query(query, (project_id,))
            return result[0] if result else None
        except Exception as e:
            self.db_manager.logger.error(f"Error finding project by ID {project_id}: {e}")
            return None
    
    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find project by name."""
        try:
            query = "SELECT * FROM framework_projects WHERE name = ?"
            result = self.db_manager.execute_query(query, (name,))
            return result[0] if result else None
        except Exception as e:
            self.db_manager.logger.error(f"Error finding project by name {name}: {e}")
            return None
    
    def find_all(
        self, 
        filters: Optional[FilterCriteria] = None,
        sort: Optional[SortCriteria] = None,
        page: int = 1,
        page_size: int = 10
    ) -> PaginatedResult[Dict[str, Any]]:
        """Find all projects with filtering, sorting, and pagination."""
        try:
            # Build base query
            base_query = """
                SELECT p.*
                FROM framework_projects p
            """
            
            where_conditions = []
            params = []
            
            if filters:
                if filters.has('status'):
                    where_conditions.append("p.status = ?")
                    params.append(filters.get('status'))
                
                if filters.has('name'):
                    where_conditions.append("p.name LIKE ?")
                    params.append(f"%{filters.get('name')}%")
                
                if filters.has('budget_min'):
                    where_conditions.append("p.budget >= ?")
                    params.append(filters.get('budget_min'))
                
                if filters.has('budget_max'):
                    where_conditions.append("p.budget <= ?")
                    params.append(filters.get('budget_max'))
                
                if filters.has('start_date_from'):
                    where_conditions.append("p.start_date >= ?")
                    params.append(filters.get('start_date_from'))
                
                if filters.has('end_date_to'):
                    where_conditions.append("p.end_date <= ?")
                    params.append(filters.get('end_date_to'))
            
            # Build WHERE clause
            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Build ORDER BY clause
            order_clause = ""
            if sort:
                # Map sort fields to qualified column names
                sort_field = sort.field
                if sort_field in ['name', 'status', 'start_date', 'end_date', 'budget']:
                    sort_field = f"p.{sort_field}"
                
                order_clause = f" ORDER BY {sort_field} {'ASC' if sort.ascending else 'DESC'}"
            
            # Count total records
            # Count total records (usar alias para chave estável no resultado)
            count_query = f"""
                SELECT COUNT(*) AS total
                FROM framework_projects p
                {where_clause}
            """
            total_count = self.db_manager.execute_query(count_query, params)[0]['total']
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = (total_count + page_size - 1) // page_size
            
            # Get paginated results
            data_query = f"{base_query}{where_clause}{order_clause} LIMIT ? OFFSET ?"
            data_params = params + [page_size, offset]
            projects = self.db_manager.execute_query(data_query, data_params)
            
            return PaginatedResult(
                items=projects,
                total=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            self.db_manager.logger.error(f"Error finding projects: {e}")
            return PaginatedResult([], 0, page, page_size, 0)
    
    def find_all_projects(self) -> List[Dict[str, Any]]:
        """Find all projects."""
        try:
            query = "SELECT * FROM framework_projects ORDER BY created_at DESC"
            return self.db_manager.execute_query(query)
        except Exception as e:
            self.db_manager.logger.error(f"Error finding projects: {e}")
            return []
    
    def create(self, project_data: Dict[str, Any]) -> Optional[int]:
        """Create new project and return the ID."""
        try:
            query = """
                INSERT INTO framework_projects (
                    name, description, status, start_date, end_date,
                    budget, team_members, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                project_data['name'],
                project_data.get('description'),
                project_data.get('status', ProjectStatus.PLANNING.value),
                project_data.get('start_date'),
                project_data.get('end_date'),
                project_data.get('budget'),
                project_data.get('team_members'),
                project_data.get('notes'),
                datetime.now()
            )
            
            return self.db_manager.execute_insert(query, params)
            
        except Exception as e:
            self.db_manager.logger.error(f"Error creating project: {e}")
            return None
    
    def update(self, project_id: int, project_data: Dict[str, Any]) -> bool:
        """Update existing project."""
        try:
            query = """
                UPDATE framework_projects SET
                    name = ?, description = ?, status = ?,
                    start_date = ?, end_date = ?, budget = ?, team_members = ?,
                    notes = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                project_data['name'],
                project_data.get('description'),
                project_data.get('status', ProjectStatus.PLANNING.value),
                project_data.get('start_date'),
                project_data.get('end_date'),
                project_data.get('budget'),
                project_data.get('team_members'),
                project_data.get('notes'),
                datetime.now(),
                project_id
            )
            
            affected_rows = self.db_manager.execute_update(query, params)
            return affected_rows > 0
            
        except Exception as e:
            self.db_manager.logger.error(f"Error updating project {project_id}: {e}")
            return False
    
    def delete(self, project_id: int) -> bool:
        """Delete project (soft delete by changing status)."""
        try:
            query = """
                UPDATE framework_projects SET
                    status = ?, updated_at = ?
                WHERE id = ?
            """
            params = (ProjectStatus.CANCELLED.value, datetime.now(), project_id)
            
            affected_rows = self.db_manager.execute_update(query, params)
            return affected_rows > 0
            
        except Exception as e:
            self.db_manager.logger.error(f"Error deleting project {project_id}: {e}")
            return False
    
    def count_epics(self, project_id: int) -> int:
        """Count epics for a project."""
        try:
            query = "SELECT COUNT(*) FROM framework_epics WHERE project_id = ?"
            result = self.db_manager.execute_query(query, (project_id,))
            return result[0]['COUNT(*)'] if result else 0
        except Exception as e:
            self.db_manager.logger.error(f"Error counting epics for project {project_id}: {e}")
            return 0
    
    def get_project_metrics(self, project_id: int) -> Dict[str, Any]:
        """Get project metrics (epics, tasks, progress)."""
        try:
            # Count epics by status
            epic_query = """
                SELECT status, COUNT(*) as count
                FROM framework_epics
                WHERE project_id = ?
                GROUP BY status
            """
            epic_counts = self.db_manager.execute_query(epic_query, (project_id,))
            
            # Count tasks by status
            task_query = """
                SELECT t.status, COUNT(*) as count
                FROM framework_tasks t
                JOIN framework_epics e ON t.epic_id = e.id
                WHERE e.project_id = ?
                GROUP BY t.status
            """
            task_counts = self.db_manager.execute_query(task_query, (project_id,))
            
            # Calculate progress (completed tasks / total tasks)
            total_tasks = sum(row['count'] for row in task_counts)
            completed_tasks = sum(row['count'] for row in task_counts if row['status'] == 'completed')
            progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                'epic_counts': {row['status']: row['count'] for row in epic_counts},
                'task_counts': {row['status']: row['count'] for row in task_counts},
                'total_epics': sum(row['count'] for row in epic_counts),
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'progress_percentage': round(progress, 2)
            }
            
        except Exception as e:
            self.db_manager.logger.error(f"Error getting project metrics for {project_id}: {e}")
            return {
                'epic_counts': {},
                'task_counts': {},
                'total_epics': 0,
                'total_tasks': 0,
                'completed_tasks': 0,
                'progress_percentage': 0
            }
    


class ProjectService(BaseService):
    """Service for project business logic operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.repository = ProjectRepository(db_manager)
        super().__init__(self.repository)
    
    def validate_business_rules(self, data: Dict[str, Any]) -> List[ServiceError]:
        """Validate project-specific business rules."""
        errors = []
        
        # Name length validation
        if 'name' in data and data['name']:
            if len(data['name']) > ValidationRules.MAX_NAME_LENGTH.value:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message=f"Name cannot exceed {ValidationRules.MAX_NAME_LENGTH.value} characters",
                    field="name"
                ))
        
        # Budget validation
        if 'budget' in data and data['budget'] is not None:
            try:
                budget = float(data['budget'])
                if budget < 0:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Budget cannot be negative",
                        field="budget"
                    ))
                elif budget > 10000000:  # 10 million limit
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Budget cannot exceed $10,000,000",
                        field="budget"
                    ))
            except (ValueError, TypeError):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Budget must be a valid number",
                    field="budget"
                ))
        
        # Date validation
        if 'start_date' in data and 'end_date' in data:
            start_date = data['start_date']
            end_date = data['end_date']
            
            if start_date and end_date:
                # Convert string dates to date objects if needed
                if isinstance(start_date, str):
                    try:
                        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(ServiceError(
                            error_type=ServiceErrorType.VALIDATION_ERROR,
                            message="Invalid start date format (use YYYY-MM-DD)",
                            field="start_date"
                        ))
                        start_date = None
                
                if isinstance(end_date, str):
                    try:
                        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(ServiceError(
                            error_type=ServiceErrorType.VALIDATION_ERROR,
                            message="Invalid end date format (use YYYY-MM-DD)",
                            field="end_date"
                        ))
                        end_date = None
                
                # Check if end date is after start date
                if start_date and end_date and end_date <= start_date:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="End date must be after start date",
                        field="end_date"
                    ))
        
        # Status validation
        if 'status' in data and data['status']:
            valid_statuses = ProjectStatus.get_all_values()
            if data['status'] not in valid_statuses:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message=f"Status must be one of: {', '.join(valid_statuses)}",
                    field="status"
                ))
        
        # Team members validation (JSON string)
        if 'team_members' in data and data['team_members']:
            if isinstance(data['team_members'], str):
                try:
                    import json
                    json.loads(data['team_members'])
                except json.JSONDecodeError:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Team members must be valid JSON",
                        field="team_members"
                    ))
        
        return errors
    
    def create_project(self, project_data: Dict[str, Any]) -> ServiceResult[int]:
        """
        Create a new project with validation.
        
        Args:
            project_data: Project information dictionary
            
        Returns:
            ServiceResult with project ID if successful
        """
        self.log_operation("create_project", project_data=project_data)
        
        # Validate required fields
        required_fields = ['name']
        validation_errors = self.validate_required_fields(project_data, required_fields)
        
        # Validate business rules
        business_errors = self.validate_business_rules(project_data)
        validation_errors.extend(business_errors)
        
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        # Check project name uniqueness
        existing_project = self.repository.find_by_name(project_data['name'])
        if existing_project:
            return ServiceResult.business_rule_violation(
                f"Project '{project_data['name']}' already exists"
            )
        
        try:
            # Create project
            project_id = self.repository.create(project_data)
            
            if project_id:
                self.log_operation("create_project_success", project_id=project_id)
                return ServiceResult.ok(project_id)
            else:
                return self.handle_database_error("create_project", Exception("Failed to create project"))
                
        except Exception as e:
            return self.handle_database_error("create_project", e)
    
    def get_project(self, project_id: int) -> ServiceResult[Dict[str, Any]]:
        """
        Get project by ID.

        Args:
            project_id: Project ID

        Returns:
            ServiceResult with project data if found
        """
        self.log_operation("get_project", project_id=project_id)
        
        try:
            project = self.repository.find_by_id(project_id)
            
            if project:
                return ServiceResult.ok(project)
            else:
                return ServiceResult.not_found("Project", project_id)
                
        except Exception as e:
            return self.handle_database_error("get_project", e)
    
    def update_project(self, project_id: int, project_data: Dict[str, Any]) -> ServiceResult[bool]:
        """
        Update existing project.
        
        Args:
            project_id: Project ID
            project_data: Updated project information
            
        Returns:
            ServiceResult with success status
        """
        self.log_operation("update_project", project_id=project_id, project_data=project_data)
        
        # Check if project exists
        existing_project = self.repository.find_by_id(project_id)
        if not existing_project:
            return ServiceResult.not_found("Project", project_id)
        
        # Validate required fields
        required_fields = ['name']
        validation_errors = self.validate_required_fields(project_data, required_fields)
        
        # Validate business rules
        business_errors = self.validate_business_rules(project_data)
        validation_errors.extend(business_errors)
        
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        # Check project name uniqueness (excluding current project)
        existing_name_project = self.repository.find_by_name(project_data['name'])
        if existing_name_project and existing_name_project['id'] != project_id:
            return ServiceResult.business_rule_violation(
                f"Another project named '{project_data['name']}' already exists"
            )
        
        try:
            # Update project
            success = self.repository.update(project_id, project_data)
            
            if success:
                self.log_operation("update_project_success", project_id=project_id)
                return ServiceResult.ok(True)
            else:
                return ServiceResult.business_rule_violation("Failed to update project")
                
        except Exception as e:
            return self.handle_database_error("update_project", e)
    
    def delete_project(self, project_id: int) -> ServiceResult[bool]:
        """
        Delete project (soft delete).
        
        Args:
            project_id: Project ID
            
        Returns:
            ServiceResult with success status
        """
        self.log_operation("delete_project", project_id=project_id)
        
        # Check if project exists
        existing_project = self.repository.find_by_id(project_id)
        if not existing_project:
            return ServiceResult.not_found("Project", project_id)
        
        # Check if project has epics
        epic_count = self.repository.count_epics(project_id)
        if epic_count > 0:
            return ServiceResult.business_rule_violation(
                f"Cannot delete project with {epic_count} epics. "
                "Please delete or reassign epics first."
            )
        
        try:
            # Soft delete project
            success = self.repository.delete(project_id)
            
            if success:
                self.log_operation("delete_project_success", project_id=project_id)
                return ServiceResult.ok(True)
            else:
                return ServiceResult.business_rule_violation("Failed to delete project")
                
        except Exception as e:
            return self.handle_database_error("delete_project", e)
    
    def list_projects(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "name",
        sort_ascending: bool = True,
        page: int = 1,
        page_size: int = 10
    ) -> ServiceResult[PaginatedResult[Dict[str, Any]]]:
        """
        List projects with filtering, sorting, and pagination.
        
        Args:
            filters: Filter criteria dictionary
            sort_by: Field to sort by
            sort_ascending: Sort direction
            page: Page number (1-based)
            page_size: Items per page
            
        Returns:
            ServiceResult with paginated project list
        """
        self.log_operation("list_projects", filters=filters, sort_by=sort_by, page=page)
        
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
            
            self.log_operation("list_projects_success", 
                             total_projects=result.total, 
                             page=page, 
                             returned_count=len(result.items))
            
            return ServiceResult.ok(result)
            
        except Exception as e:
            return self.handle_database_error("list_projects", e)
    
    def get_all_projects(self) -> ServiceResult[List[Dict[str, Any]]]:
        """
        Get all projects.
        
        Returns:
            ServiceResult with list of projects
        """
        self.log_operation("get_all_projects")
        
        try:
            projects = self.repository.find_all_projects()
            return ServiceResult.ok(projects)
            
        except Exception as e:
            return self.handle_database_error("get_all_projects", e)
    
    def get_project_summary(self, project_id: int) -> ServiceResult[Dict[str, Any]]:
        """
        Get project summary with metrics.

        Args:
            project_id: Project ID

        Returns:
            ServiceResult with project summary data
        """
        self.log_operation("get_project_summary", project_id=project_id)
        
        try:
            # Get project data
            project_result = self.get_project(project_id)
            if not project_result.success:
                return project_result
            
            project = project_result.data
            
            # Get project metrics
            metrics = self.repository.get_project_metrics(project_id)
            
            # Build summary
            summary = {
                **project,
                **metrics,
                'status_display': ProjectStatus.get_display_name(project.get('status', 'planning')),
                'has_epics': metrics['total_epics'] > 0,
                'duration_days': self._calculate_project_duration(project.get('start_date'), project.get('end_date'))
            }
            
            return ServiceResult.ok(summary)
            
        except Exception as e:
            return self.handle_database_error("get_project_summary", e)
    
    def validate_project_data(self, project_data: Dict[str, Any]) -> ServiceResult[bool]:
        """
        Validate project data without creating/updating.
        
        Args:
            project_data: Project data to validate
            
        Returns:
            ServiceResult indicating if data is valid
        """
        # Validate required fields
        required_fields = ['name']
        validation_errors = self.validate_required_fields(project_data, required_fields)
        
        # Validate business rules
        business_errors = self.validate_business_rules(project_data)
        validation_errors.extend(business_errors)
        
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        return ServiceResult.ok(True)
    
    def _calculate_project_duration(self, start_date: Any, end_date: Any) -> Optional[int]:
        """Calculate project duration in days."""
        if not start_date or not end_date:
            return None
        
        try:
            # Convert to date objects if they're strings
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            duration = (end_date - start_date).days
            return duration if duration >= 0 else None
            
        except (ValueError, TypeError):
            return None