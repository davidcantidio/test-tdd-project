"""
📁 Project Service Layer

Business logic for project management operations.
Implements complete CRUD operations with validation.
Clean modular architecture - no DatabaseManager dependencies.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
import re
import logging

from .base import (
    BaseService, ServiceResult, ServiceError, ServiceErrorType,
    BaseRepository, PaginatedResult, FilterCriteria, SortCriteria
)
from ..database import queries as db_queries
from ..database.connection import transaction, get_connection_context, execute
from ..config.constants import ValidationRules, ProjectStatus


class ProjectRepository(BaseRepository):
    """Repository for project data access operations."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def find_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Find project by ID."""
        try:
            query = """
                SELECT p.*
                FROM framework_projects p
                WHERE p.id = ?
            """
            result = execute(query, (project_id,))
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Error finding project by ID {project_id}: {e}")
            return None
    
    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find project by name."""
        try:
            query = "SELECT * FROM framework_projects WHERE name = ?"
            result = execute(query, (name,))
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Error finding project by name {name}: {e}")
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
            count_query = f"""
                SELECT COUNT(*) AS total
                FROM framework_projects p
                {where_clause}
            """
            total_count = execute(count_query, params)[0]['total']
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = (total_count + page_size - 1) // page_size
            
            # Get paginated results
            data_query = f"{base_query}{where_clause}{order_clause} LIMIT ? OFFSET ?"
            data_params = params + [page_size, offset]
            projects = execute(data_query, data_params)
            
            return PaginatedResult(
                items=projects,
                total=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            self.logger.error(f"Error finding projects: {e}")
            return PaginatedResult([], 0, page, page_size, 0)
    
    def find_all_projects(self) -> List[Dict[str, Any]]:
        """Find all projects."""
        try:
            query = "SELECT * FROM framework_projects ORDER BY created_at DESC"
            return execute(query)
        except Exception as e:
            self.logger.error(f"Error finding projects: {e}")
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
            
            with transaction() as conn:
                cursor = conn.execute(query, params)
                return cursor.lastrowid
            
        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
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
            
            with transaction() as conn:
                cursor = conn.execute(query, params)
                return cursor.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Error updating project {project_id}: {e}")
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
            
            with transaction() as conn:
                cursor = conn.execute(query, params)
                return cursor.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting project {project_id}: {e}")
            return False
    
    def count_epics(self, project_id: int) -> int:
        """Count epics for a project."""
        try:
            query = "SELECT COUNT(*) as count FROM framework_epics WHERE project_id = ?"
            result = execute(query, (project_id,))
            return result[0]['count'] if result else 0
        except Exception as e:
            self.logger.error(f"Error counting epics for project {project_id}: {e}")
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
            epic_counts = execute(epic_query, (project_id,))
            
            # Count tasks by status
            task_query = """
                SELECT t.status, COUNT(*) as count
                FROM framework_tasks t
                JOIN framework_epics e ON t.epic_id = e.id
                WHERE e.project_id = ?
                GROUP BY t.status
            """
            task_counts = execute(task_query, (project_id,))
            
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
            self.logger.error(f"Error getting project metrics for {project_id}: {e}")
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
    
    def __init__(self):
        super().__init__()
        self.repository = ProjectRepository()
        self.logger = logging.getLogger(__name__)
    
    def get_all_projects(self, include_inactive: bool = False) -> ServiceResult[List[Dict[str, Any]]]:
        """Get all projects, optionally including inactive ones."""
        try:
            projects = self.repository.find_all_projects()
            
            if not include_inactive:
                projects = [p for p in projects if p.get('status') != ProjectStatus.CANCELLED.value]
            
            return ServiceResult.success(projects)
        
        except Exception as e:
            self.logger.error(f"Error getting all projects: {e}")
            return ServiceResult.failure(
                ServiceError(ServiceErrorType.DATABASE_ERROR, str(e))
            )
    
    def get_project_by_id(self, project_id: int) -> ServiceResult[Optional[Dict[str, Any]]]:
        """Get project by ID."""
        try:
            project = self.repository.find_by_id(project_id)
            return ServiceResult.success(project)
        
        except Exception as e:
            self.logger.error(f"Error getting project {project_id}: {e}")
            return ServiceResult.failure(
                ServiceError(ServiceErrorType.DATABASE_ERROR, str(e))
            )
    
    def create_project(self, project_data: Dict[str, Any]) -> ServiceResult[int]:
        """Create new project with validation."""
        # Validate project data
        validation_result = self._validate_project_data(project_data)
        if not validation_result.is_success():
            return validation_result
        
        try:
            # Check for duplicate name
            existing = self.repository.find_by_name(project_data['name'])
            if existing:
                return ServiceResult.failure(
                    ServiceError(ServiceErrorType.DUPLICATE_ERROR, "Project name already exists")
                )
            
            # Create project
            project_id = self.repository.create(project_data)
            if project_id:
                return ServiceResult.success(project_id)
            else:
                return ServiceResult.failure(
                    ServiceError(ServiceErrorType.DATABASE_ERROR, "Failed to create project")
                )
        
        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
            return ServiceResult.failure(
                ServiceError(ServiceErrorType.DATABASE_ERROR, str(e))
            )
    
    def update_project(self, project_id: int, project_data: Dict[str, Any]) -> ServiceResult[bool]:
        """Update project with validation."""
        # Validate project data
        validation_result = self._validate_project_data(project_data, is_update=True)
        if not validation_result.is_success():
            return validation_result
        
        try:
            # Check if project exists
            existing = self.repository.find_by_id(project_id)
            if not existing:
                return ServiceResult.failure(
                    ServiceError(ServiceErrorType.NOT_FOUND_ERROR, "Project not found")
                )
            
            # Check for duplicate name (excluding current project)
            name_check = self.repository.find_by_name(project_data['name'])
            if name_check and name_check['id'] != project_id:
                return ServiceResult.failure(
                    ServiceError(ServiceErrorType.DUPLICATE_ERROR, "Project name already exists")
                )
            
            # Update project
            success = self.repository.update(project_id, project_data)
            if success:
                return ServiceResult.success(True)
            else:
                return ServiceResult.failure(
                    ServiceError(ServiceErrorType.DATABASE_ERROR, "Failed to update project")
                )
        
        except Exception as e:
            self.logger.error(f"Error updating project {project_id}: {e}")
            return ServiceResult.failure(
                ServiceError(ServiceErrorType.DATABASE_ERROR, str(e))
            )
    
    def delete_project(self, project_id: int) -> ServiceResult[bool]:
        """Delete project (soft delete)."""
        try:
            # Check if project exists
            existing = self.repository.find_by_id(project_id)
            if not existing:
                return ServiceResult.failure(
                    ServiceError(ServiceErrorType.NOT_FOUND_ERROR, "Project not found")
                )
            
            # Perform soft delete
            success = self.repository.delete(project_id)
            if success:
                return ServiceResult.success(True)
            else:
                return ServiceResult.failure(
                    ServiceError(ServiceErrorType.DATABASE_ERROR, "Failed to delete project")
                )
        
        except Exception as e:
            self.logger.error(f"Error deleting project {project_id}: {e}")
            return ServiceResult.failure(
                ServiceError(ServiceErrorType.DATABASE_ERROR, str(e))
            )
    
    def get_project_metrics(self, project_id: int) -> ServiceResult[Dict[str, Any]]:
        """Get project metrics."""
        try:
            metrics = self.repository.get_project_metrics(project_id)
            return ServiceResult.success(metrics)
        
        except Exception as e:
            self.logger.error(f"Error getting project metrics for {project_id}: {e}")
            return ServiceResult.failure(
                ServiceError(ServiceErrorType.DATABASE_ERROR, str(e))
            )
    
    def _validate_project_data(self, data: Dict[str, Any], is_update: bool = False) -> ServiceResult[bool]:
        """Validate project data."""
        errors = []
        
        # Required fields validation
        if not is_update or 'name' in data:
            if not data.get('name') or not data['name'].strip():
                errors.append("Project name is required")
            elif len(data['name'].strip()) < ValidationRules.MIN_NAME_LENGTH:
                errors.append(f"Project name must be at least {ValidationRules.MIN_NAME_LENGTH} characters")
            elif len(data['name'].strip()) > ValidationRules.MAX_NAME_LENGTH:
                errors.append(f"Project name cannot exceed {ValidationRules.MAX_NAME_LENGTH} characters")
        
        # Optional validations
        if 'description' in data and data['description']:
            if len(data['description']) > ValidationRules.MAX_DESCRIPTION_LENGTH:
                errors.append(f"Description cannot exceed {ValidationRules.MAX_DESCRIPTION_LENGTH} characters")
        
        if 'budget' in data and data['budget'] is not None:
            try:
                budget = float(data['budget'])
                if budget < 0:
                    errors.append("Budget cannot be negative")
            except (ValueError, TypeError):
                errors.append("Budget must be a valid number")
        
        # Date validations
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] and data['end_date']:
                try:
                    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
                    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
                    if end_date <= start_date:
                        errors.append("End date must be after start date")
                except ValueError:
                    errors.append("Invalid date format (use YYYY-MM-DD)")
        
        if errors:
            return ServiceResult.failure(
                ServiceError(ServiceErrorType.VALIDATION_ERROR, "; ".join(errors))
            )
        
        return ServiceResult.success(True)