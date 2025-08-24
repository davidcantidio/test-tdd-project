"""
🎯 Epic Service Layer

Business logic for epic management operations with gamification.
Implements complete CRUD operations with project relationships and progress tracking.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
import json
import re

from .base import (
    BaseService, ServiceResult, ServiceError, ServiceErrorType,
    BaseRepository, PaginatedResult, FilterCriteria, SortCriteria
)
from ..utils.database import DatabaseManager
from ..config.constants import ValidationRules, EpicStatus, TaskStatus


class EpicRepository(BaseRepository):
    # Delegation to EpicRepositoryDataaccess
    def __init__(self):
        self._epicrepositorydataaccess = EpicRepositoryDataaccess()
    # Delegation to EpicRepositoryLogging
    def __init__(self):
        self._epicrepositorylogging = EpicRepositoryLogging()
    # Delegation to EpicRepositoryErrorhandling
    def __init__(self):
        self._epicrepositoryerrorhandling = EpicRepositoryErrorhandling()
    # Delegation to EpicRepositoryFormatting
    def __init__(self):
        self._epicrepositoryformatting = EpicRepositoryFormatting()
    # Delegation to EpicRepositoryNetworking
    def __init__(self):
        self._epicrepositorynetworking = EpicRepositoryNetworking()
    # Delegation to EpicRepositoryCalculation
    def __init__(self):
        self._epicrepositorycalculation = EpicRepositoryCalculation()
    # Delegation to EpicRepositorySerialization
    def __init__(self):
        self._epicrepositoryserialization = EpicRepositorySerialization()
    """Repository for epic data access operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
    
    def find_by_id(self, epic_id: int) -> Optional[Dict[str, Any]]:
        """Find epic by ID with project information."""
        try:
            query = """
                SELECT e.*, p.name as project_name
                FROM framework_epics e
                LEFT JOIN framework_projects p ON e.project_id = p.id
                WHERE e.id = ?
            """
            result = self.db_manager.execute_query(query, (epic_id,))
            return result[0] if result else None
        except Exception as e:
            self.db_manager.logger.error(f"Error finding epic by ID {epic_id}: {e}")
            return None
    
    def find_by_key(self, epic_key: str) -> Optional[Dict[str, Any]]:
        """Find epic by unique key."""
        try:
            query = "SELECT * FROM framework_epics WHERE epic_key = ?"
            result = self.db_manager.execute_query(query, (epic_key,))
            return result[0] if result else None
        except Exception as e:
            self.db_manager.logger.error(f"Error finding epic by key {epic_key}: {e}")
            return None
    
    def find_all(
        self, 
        filters: Optional[FilterCriteria] = None,
        sort: Optional[SortCriteria] = None,
        page: int = 1,
        page_size: int = 10
    ) -> PaginatedResult[Dict[str, Any]]:
        """Find all epics with filtering, sorting, and pagination."""
        try:
            # Build base query with project information
            base_query = """
                SELECT e.*, p.name as project_name,
                       COUNT(t.id) as task_count,
                       SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
                FROM framework_epics e
                LEFT JOIN framework_projects p ON e.project_id = p.id
                LEFT JOIN framework_tasks t ON e.id = t.epic_id
            """
            
            where_conditions = []
            params = []
            
            if filters:
                if filters.has('status'):
                    where_conditions.append("e.status = ?")
                    params.append(filters.get('status'))
                
                if filters.has('title'):
                    where_conditions.append("e.title LIKE ?")
                    params.append(f"%{filters.get('title')}%")
                
                if filters.has('epic_key'):
                    where_conditions.append("e.epic_key LIKE ?")
                    params.append(f"%{filters.get('epic_key')}%")
                
                if filters.has('project_id'):
                    where_conditions.append("e.project_id = ?")
                    params.append(filters.get('project_id'))
                
                if filters.has('priority'):
                    where_conditions.append("e.priority = ?")
                    params.append(filters.get('priority'))
                
                if filters.has('difficulty'):
                    where_conditions.append("e.difficulty = ?")
                    params.append(filters.get('difficulty'))
                
                if filters.has('focus_time_min'):
                    where_conditions.append("e.focus_time_minutes >= ?")
                    params.append(filters.get('focus_time_min'))
                
                if filters.has('points_min'):
                    where_conditions.append("e.points >= ?")
                    params.append(filters.get('points_min'))
            
            # Build WHERE clause
            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            group_clause = " GROUP BY e.id"
            
            # Build ORDER BY clause
            order_clause = ""
            if sort:
                # Map sort fields to qualified column names
                sort_field = sort.field
                if sort_field in ['title', 'status', 'priority', 'difficulty', 'points', 'epic_key']:
                    sort_field = f"e.{sort_field}"
                elif sort_field in ['project_name']:
                    sort_field = f"p.name"
                elif sort_field == 'progress':
                    sort_field = "(completed_tasks * 100.0 / NULLIF(task_count, 0))"
                
                order_clause = f" ORDER BY {sort_field} {'ASC' if sort.ascending else 'DESC'}"
            
            # Count total records (need subquery for GROUP BY)
            count_query = f"""
                SELECT COUNT(*) FROM (
                    SELECT e.id
                    FROM framework_epics e
                    LEFT JOIN framework_projects p ON e.project_id = p.id
                    {where_clause}
                    GROUP BY e.id
                )
            """
            total_count = self.db_manager.execute_query(count_query, params)[0]['COUNT(*)']
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = (total_count + page_size - 1) // page_size
            
            # Get paginated results
            data_query = f"{base_query}{where_clause}{group_clause}{order_clause} LIMIT ? OFFSET ?"
            data_params = params + [page_size, offset]
            epics = self.db_manager.execute_query(data_query, data_params)
            
            # Calculate progress percentage for each epic
            for epic in epics:
                task_count = epic.get('task_count', 0)
                completed_tasks = epic.get('completed_tasks', 0)
                epic['progress_percentage'] = (
                    (completed_tasks / task_count * 100) if task_count > 0 else 0
                )
            
            return PaginatedResult(
                items=epics,
                total=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            self.db_manager.logger.error(f"Error finding epics: {e}")
            return PaginatedResult([], 0, page, page_size, 0)
    
    def find_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Find all epics for a specific project."""
        try:
            query = """
                SELECT e.*, COUNT(t.id) as task_count,
                       SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
                FROM framework_epics e
                LEFT JOIN framework_tasks t ON e.id = t.epic_id
                WHERE e.project_id = ?
                GROUP BY e.id
                ORDER BY e.priority DESC, e.created_at DESC
            """
            epics = self.db_manager.execute_query(query, (project_id,))
            
            # Calculate progress for each epic
            for epic in epics:
                task_count = epic.get('task_count', 0)
                completed_tasks = epic.get('completed_tasks', 0)
                epic['progress_percentage'] = (
                    (completed_tasks / task_count * 100) if task_count > 0 else 0
                )
            
            return epics
        except Exception as e:
            self.db_manager.logger.error(f"Error finding epics for project {project_id}: {e}")
            return []
    
    def create(self, epic_data: Dict[str, Any]) -> Optional[int]:
        """Create new epic and return the ID."""
        try:
            query = """
                INSERT INTO framework_epics (
                    epic_key, title, description, project_id, status, priority,
                    difficulty, estimated_hours, focus_time_minutes, points,
                    goals, definition_of_done, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                epic_data['epic_key'],
                epic_data['title'],
                epic_data.get('description'),
                epic_data['project_id'],
                epic_data.get('status', EpicStatus.PLANNING.value),
                epic_data.get('priority', 3),  # Default medium priority
                epic_data.get('difficulty', 3),  # Default medium difficulty
                epic_data.get('estimated_hours'),
                epic_data.get('focus_time_minutes'),
                epic_data.get('points', 0),
                json.dumps(epic_data.get('goals', [])),
                json.dumps(epic_data.get('definition_of_done', [])),
                datetime.now()
            )
            
            return self.db_manager.execute_insert(query, params)
            
        except Exception as e:
            self.db_manager.logger.error(f"Error creating epic: {e}")
            return None
    
    def update(self, epic_id: int, epic_data: Dict[str, Any]) -> bool:
        """Update existing epic."""
        try:
            query = """
                UPDATE framework_epics SET
                    epic_key = ?, title = ?, description = ?, project_id = ?,
                    status = ?, priority = ?, difficulty = ?, estimated_hours = ?,
                    focus_time_minutes = ?, points = ?, goals = ?,
                    definition_of_done = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                epic_data['epic_key'],
                epic_data['title'],
                epic_data.get('description'),
                epic_data['project_id'],
                epic_data.get('status', EpicStatus.PLANNING.value),
                epic_data.get('priority', 3),
                epic_data.get('difficulty', 3),
                epic_data.get('estimated_hours'),
                epic_data.get('focus_time_minutes'),
                epic_data.get('points', 0),
                json.dumps(epic_data.get('goals', [])),
                json.dumps(epic_data.get('definition_of_done', [])),
                datetime.now(),
                epic_id
            )
            
            affected_rows = self.db_manager.execute_update(query, params)
            return affected_rows > 0
            
        except Exception as e:
            self.db_manager.logger.error(f"Error updating epic {epic_id}: {e}")
            return False
    
    def delete(self, epic_id: int) -> bool:
        """Delete epic (soft delete by changing status)."""
        try:
            query = """
                UPDATE framework_epics SET
                    status = ?, updated_at = ?
                WHERE id = ?
            """
            params = (EpicStatus.CANCELLED.value, datetime.now(), epic_id)
            
            affected_rows = self.db_manager.execute_update(query, params)
            return affected_rows > 0
            
        except Exception as e:
            self.db_manager.logger.error(f"Error deleting epic {epic_id}: {e}")
            return False
    
    def count_tasks(self, epic_id: int) -> int:
        """Count tasks for an epic."""
        try:
            query = "SELECT COUNT(*) AS total FROM framework_tasks WHERE epic_id = ?"
            result = self.db_manager.execute_query(query, (epic_id,))
            return int(result[0]['total']) if result else 0
        except Exception as e:
            self.db_manager.logger.error(f"Error counting tasks for epic {epic_id}: {e}")
            return 0
    
    def get_epic_metrics(self, epic_id: int) -> Dict[str, Any]:
        """Get epic metrics (tasks, progress, time tracking)."""
        try:
            # Task counts by status
            task_query = """
                SELECT status, COUNT(*) as count
                FROM framework_tasks
                WHERE epic_id = ?
                GROUP BY status
            """
            task_counts = self.db_manager.execute_query(task_query, (epic_id,))
            
            # Total focus time from work sessions
            time_query = """
                SELECT SUM(duration_minutes) as total_time
                FROM work_sessions
                WHERE epic_id = ?
            """
            time_result = self.db_manager.execute_query(time_query, (epic_id,))
            total_time = time_result[0]['total_time'] if time_result and time_result[0]['total_time'] else 0
            
            # Calculate progress
            total_tasks = sum(row['count'] for row in task_counts)
            completed_tasks = sum(row['count'] for row in task_counts if row['status'] == 'completed')
            progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                'task_counts': {row['status']: row['count'] for row in task_counts},
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'progress_percentage': round(progress, 2),
                'total_focus_minutes': total_time,
                'total_focus_hours': round(total_time / 60, 2) if total_time else 0
            }
            
        except Exception as e:
            self.db_manager.logger.error(f"Error getting epic metrics for {epic_id}: {e}")
            return {
                'task_counts': {},
                'total_tasks': 0,
                'completed_tasks': 0,
                'progress_percentage': 0,
                'total_focus_minutes': 0,
                'total_focus_hours': 0
            }
    
    def project_exists(self, project_id: int) -> bool:
        """Check if project exists and is active."""
        try:
            query = "SELECT id FROM framework_projects WHERE id = ? AND status != 'cancelled'"
            result = self.db_manager.execute_query(query, (project_id,))
            return len(result) > 0
        except Exception as e:
            self.db_manager.logger.error(f"Error checking project existence {project_id}: {e}")
            return False


class EpicService(BaseService):
    """Service for epic business logic operations with gamification."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.repository = EpicRepository(db_manager)
        super().__init__(self.repository)
    
    def validate_business_rules(self, data: Dict[str, Any]) -> List[ServiceError]:
        """Validate epic-specific business rules."""
        errors = []
        
        # Epic key format validation (EPIC-X.X or similar)
        if 'epic_key' in data and data['epic_key']:
            epic_key_pattern = r'^[A-Z0-9]+-\d+(\.\d+)*$'
            if not re.match(epic_key_pattern, data['epic_key']):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Epic key must follow format 'EPIC-1.1' or similar",
                    field="epic_key"
                ))
        
        # Title length validation
        if 'title' in data and data['title']:
            if len(data['title']) > ValidationRules.MAX_NAME_LENGTH.value:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message=f"Title cannot exceed {ValidationRules.MAX_NAME_LENGTH.value} characters",
                    field="title"
                ))
        
        # Priority validation (1-5 scale)
        if 'priority' in data and data['priority'] is not None:
            try:
                priority = int(data['priority'])
                if priority < 1 or priority > 5:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Priority must be between 1 (low) and 5 (critical)",
                        field="priority"
                    ))
            except (ValueError, TypeError):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Priority must be a number between 1 and 5",
                    field="priority"
                ))
        
        # Difficulty validation (1-5 scale)
        if 'difficulty' in data and data['difficulty'] is not None:
            try:
                difficulty = int(data['difficulty'])
                if difficulty < 1 or difficulty > 5:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Difficulty must be between 1 (easy) and 5 (expert)",
                        field="difficulty"
                    ))
            except (ValueError, TypeError):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Difficulty must be a number between 1 and 5",
                    field="difficulty"
                ))
        
        # Estimated hours validation
        if 'estimated_hours' in data and data['estimated_hours'] is not None:
            try:
                hours = float(data['estimated_hours'])
                if hours < 0:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Estimated hours cannot be negative",
                        field="estimated_hours"
                    ))
                elif hours > 1000:  # 1000 hour limit
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Estimated hours cannot exceed 1000",
                        field="estimated_hours"
                    ))
            except (ValueError, TypeError):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Estimated hours must be a valid number",
                    field="estimated_hours"
                ))
        
        # Focus time validation
        if 'focus_time_minutes' in data and data['focus_time_minutes'] is not None:
            try:
                minutes = int(data['focus_time_minutes'])
                if minutes < 0:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Focus time cannot be negative",
                        field="focus_time_minutes"
                    ))
                elif minutes > 480:  # 8 hours limit
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Focus time cannot exceed 480 minutes (8 hours)",
                        field="focus_time_minutes"
                    ))
            except (ValueError, TypeError):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Focus time must be a valid number of minutes",
                    field="focus_time_minutes"
                ))
        
        # Points validation
        if 'points' in data and data['points'] is not None:
            try:
                points = int(data['points'])
                if points < 0:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Points cannot be negative",
                        field="points"
                    ))
            except (ValueError, TypeError):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Points must be a valid number",
                    field="points"
                ))
        
        # Status validation
        if 'status' in data and data['status']:
            valid_statuses = EpicStatus.get_all_values()
            if data['status'] not in valid_statuses:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message=f"Status must be one of: {', '.join(valid_statuses)}",
                    field="status"
                ))
        
        # Goals validation (must be JSON list)
        if 'goals' in data and data['goals'] is not None:
            if isinstance(data['goals'], str):
                try:
                    goals = json.loads(data['goals'])
                    if not isinstance(goals, list):
                        errors.append(ServiceError(
                            error_type=ServiceErrorType.VALIDATION_ERROR,
                            message="Goals must be a JSON array",
                            field="goals"
                        ))
                except json.JSONDecodeError:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Goals must be valid JSON",
                        field="goals"
                    ))
            elif not isinstance(data['goals'], list):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Goals must be a list",
                    field="goals"
                ))
        
        # Definition of done validation (must be JSON list)
        if 'definition_of_done' in data and data['definition_of_done'] is not None:
            if isinstance(data['definition_of_done'], str):
                try:
                    dod = json.loads(data['definition_of_done'])
                    if not isinstance(dod, list):
                        errors.append(ServiceError(
                            error_type=ServiceErrorType.VALIDATION_ERROR,
                            message="Definition of done must be a JSON array",
                            field="definition_of_done"
                        ))
                except json.JSONDecodeError:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Definition of done must be valid JSON",
                        field="definition_of_done"
                    ))
            elif not isinstance(data['definition_of_done'], list):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Definition of done must be a list",
                    field="definition_of_done"
                ))
        
        return errors
    
    def create_epic(self, epic_data: Dict[str, Any]) -> ServiceResult[int]:
        """
        Create a new epic with validation and gamification.
        
        Args:
            epic_data: Epic information dictionary
            
        Returns:
            ServiceResult with epic ID if successful
        """
        self.log_operation("create_epic", epic_data=epic_data)
        
        # Validate required fields
        required_fields = ['epic_key', 'title', 'project_id']
        validation_errors = self.validate_required_fields(epic_data, required_fields)
        
        # Validate business rules
        business_errors = self.validate_business_rules(epic_data)
        validation_errors.extend(business_errors)
        
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        # Check if project exists
        if not self.repository.project_exists(epic_data['project_id']):
            return ServiceResult.business_rule_violation(
                f"Project with ID {epic_data['project_id']} does not exist or is cancelled"
            )
        
        # Check epic key uniqueness
        existing_epic = self.repository.find_by_key(epic_data['epic_key'])
        if existing_epic:
            return ServiceResult.business_rule_violation(
                f"Epic with key '{epic_data['epic_key']}' already exists"
            )
        
        try:
            # Auto-calculate points based on difficulty and estimated hours if not provided
            if 'points' not in epic_data or epic_data['points'] is None:
                epic_data['points'] = self._calculate_epic_points(
                    epic_data.get('difficulty', 3),
                    epic_data.get('estimated_hours', 0)
                )
            
            # Create epic
            epic_id = self.repository.create(epic_data)
            
            if epic_id:
                self.log_operation("create_epic_success", epic_id=epic_id)
                return ServiceResult.ok(epic_id)
            else:
                return self.handle_database_error("create_epic", Exception("Failed to create epic"))
                
        except Exception as e:
            return self.handle_database_error("create_epic", e)
    
    def get_epic(self, epic_id: int) -> ServiceResult[Dict[str, Any]]:
        """
        Get epic by ID with project information.

        Args:
            epic_id: Epic ID

        Returns:
            ServiceResult with epic data if found
        """
        self.log_operation("get_epic", epic_id=epic_id)
        
        try:
            epic = self.repository.find_by_id(epic_id)
            
            if epic:
                # Parse JSON fields
                if 'goals' in epic and epic['goals']:
                    try:
                        epic['goals'] = json.loads(epic['goals'])
                    except json.JSONDecodeError:
                        epic['goals'] = []
                
                if 'definition_of_done' in epic and epic['definition_of_done']:
                    try:
                        epic['definition_of_done'] = json.loads(epic['definition_of_done'])
                    except json.JSONDecodeError:
                        epic['definition_of_done'] = []
                
                return ServiceResult.ok(epic)
            else:
                return ServiceResult.not_found("Epic", epic_id)
                
        except Exception as e:
            return self.handle_database_error("get_epic", e)
    
    def update_epic(self, epic_id: int, epic_data: Dict[str, Any]) -> ServiceResult[bool]:
        """
        Update existing epic.
        
        Args:
            epic_id: Epic ID
            epic_data: Updated epic information
            
        Returns:
            ServiceResult with success status
        """
        self.log_operation("update_epic", epic_id=epic_id, epic_data=epic_data)
        
        # Check if epic exists
        existing_epic = self.repository.find_by_id(epic_id)
        if not existing_epic:
            return ServiceResult.not_found("Epic", epic_id)
        
        # Validate required fields
        required_fields = ['epic_key', 'title', 'project_id']
        validation_errors = self.validate_required_fields(epic_data, required_fields)
        
        # Validate business rules
        business_errors = self.validate_business_rules(epic_data)
        validation_errors.extend(business_errors)
        
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        # Check if project exists
        if not self.repository.project_exists(epic_data['project_id']):
            return ServiceResult.business_rule_violation(
                f"Project with ID {epic_data['project_id']} does not exist or is cancelled"
            )
        
        # Check epic key uniqueness (excluding current epic)
        existing_key_epic = self.repository.find_by_key(epic_data['epic_key'])
        if existing_key_epic and existing_key_epic['id'] != epic_id:
            return ServiceResult.business_rule_violation(
                f"Another epic with key '{epic_data['epic_key']}' already exists"
            )
        
        try:
            # Update epic
            success = self.repository.update(epic_id, epic_data)
            
            if success:
                self.log_operation("update_epic_success", epic_id=epic_id)
                return ServiceResult.ok(True)
            else:
                return ServiceResult.business_rule_violation("Failed to update epic")
                
        except Exception as e:
            return self.handle_database_error("update_epic", e)
    
    def delete_epic(self, epic_id: int) -> ServiceResult[bool]:
        """
        Delete epic (soft delete).
        
        Args:
            epic_id: Epic ID
            
        Returns:
            ServiceResult with success status
        """
        self.log_operation("delete_epic", epic_id=epic_id)
        
        # Check if epic exists
        existing_epic = self.repository.find_by_id(epic_id)
        if not existing_epic:
            return ServiceResult.not_found("Epic", epic_id)
        
        # Check if epic has tasks
        task_count = self.repository.count_tasks(epic_id)
        if task_count > 0:
            return ServiceResult.business_rule_violation(
                f"Cannot delete epic with {task_count} tasks. "
                "Please delete or reassign tasks first."
            )
        
        try:
            # Soft delete epic
            success = self.repository.delete(epic_id)
            
            if success:
                self.log_operation("delete_epic_success", epic_id=epic_id)
                return ServiceResult.ok(True)
            else:
                return ServiceResult.business_rule_violation("Failed to delete epic")
                
        except Exception as e:
            return self.handle_database_error("delete_epic", e)
    
    def list_epics(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "priority",
        sort_ascending: bool = False,  # Default to highest priority first
        page: int = 1,
        page_size: int = 10
    ) -> ServiceResult[PaginatedResult[Dict[str, Any]]]:
        """
        List epics with filtering, sorting, and pagination.
        
        Args:
            filters: Filter criteria dictionary
            sort_by: Field to sort by
            sort_ascending: Sort direction
            page: Page number (1-based)
            page_size: Items per page
            
        Returns:
            ServiceResult with paginated epic list
        """
        self.log_operation("list_epics", filters=filters, sort_by=sort_by, page=page)
        
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
            
            # Process JSON fields for each epic
            for epic in result.items:
                if 'goals' in epic and epic['goals']:
                    try:
                        epic['goals'] = json.loads(epic['goals'])
                    except json.JSONDecodeError:
                        epic['goals'] = []
                
                if 'definition_of_done' in epic and epic['definition_of_done']:
                    try:
                        epic['definition_of_done'] = json.loads(epic['definition_of_done'])
                    except json.JSONDecodeError:
                        epic['definition_of_done'] = []
            
            self.log_operation("list_epics_success", 
                             total_epics=result.total, 
                             page=page, 
                             returned_count=len(result.items))
            
            return ServiceResult.ok(result)
            
        except Exception as e:
            return self.handle_database_error("list_epics", e)
    
    def get_epics_by_project(self, project_id: int) -> ServiceResult[List[Dict[str, Any]]]:
        """
        Get all epics for a specific project.
        
        Args:
            project_id: Project ID
            
        Returns:
            ServiceResult with list of epics
        """
        self.log_operation("get_epics_by_project", project_id=project_id)
        
        try:
            # Check if project exists
            if not self.repository.project_exists(project_id):
                return ServiceResult.business_rule_violation(
                    f"Project with ID {project_id} does not exist or is cancelled"
                )
            
            epics = self.repository.find_by_project(project_id)
            
            # Process JSON fields for each epic
            for epic in epics:
                if 'goals' in epic and epic['goals']:
                    try:
                        epic['goals'] = json.loads(epic['goals'])
                    except json.JSONDecodeError:
                        epic['goals'] = []
                
                if 'definition_of_done' in epic and epic['definition_of_done']:
                    try:
                        epic['definition_of_done'] = json.loads(epic['definition_of_done'])
                    except json.JSONDecodeError:
                        epic['definition_of_done'] = []
            
            return ServiceResult.ok(epics)
            
        except Exception as e:
            return self.handle_database_error("get_epics_by_project", e)
    
    def get_epic_summary(self, epic_id: int) -> ServiceResult[Dict[str, Any]]:
        """
        Get epic summary with metrics and gamification data.
        
        Args:
            epic_id: Epic ID
            
        Returns:
            ServiceResult with epic summary data
        """
        self.log_operation("get_epic_summary", epic_id=epic_id)
        
        try:
            # Get epic data
            epic_result = self.get_epic(epic_id)
            if not epic_result.success:
                return epic_result
            
            epic = epic_result.data
            
            # Get epic metrics
            metrics = self.repository.get_epic_metrics(epic_id)
            
            # Build summary with gamification elements
            summary = {
                **epic,
                **metrics,
                'status_display': EpicStatus.get_display_name(epic.get('status', 'planning')),
                'priority_display': self._get_priority_display(epic.get('priority', 3)),
                'difficulty_display': self._get_difficulty_display(epic.get('difficulty', 3)),
                'has_tasks': metrics['total_tasks'] > 0,
                'completion_reward': self._calculate_completion_reward(epic, metrics),
                'next_milestone': self._get_next_milestone(epic, metrics)
            }
            
            return ServiceResult.ok(summary)
            
        except Exception as e:
            return self.handle_database_error("get_epic_summary", e)
    
    def validate_epic_data(self, epic_data: Dict[str, Any]) -> ServiceResult[bool]:
        """
        Validate epic data without creating/updating.
        
        Args:
            epic_data: Epic data to validate
            
        Returns:
            ServiceResult indicating if data is valid
        """
        # Validate required fields
        required_fields = ['epic_key', 'title', 'project_id']
        validation_errors = self.validate_required_fields(epic_data, required_fields)
        
        # Validate business rules
        business_errors = self.validate_business_rules(epic_data)
        validation_errors.extend(business_errors)
        
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        return ServiceResult.ok(True)
    
    def _calculate_epic_points(self, difficulty: int, estimated_hours: float) -> int:
        """Calculate epic points based on difficulty and estimated hours."""
        # Base points from difficulty (1-5 scale)
        difficulty_points = difficulty * 10
        
        # Additional points from estimated hours
        hour_points = int(estimated_hours * 5) if estimated_hours else 0
        
        return difficulty_points + hour_points
    
    def _get_priority_display(self, priority: int) -> str:
        """Get human-readable priority display."""
        priority_map = {
            1: "🟢 Low",
            2: "🟡 Medium-Low", 
            3: "🟠 Medium",
            4: "🔴 High",
            5: "🚨 Critical"
        }
        return priority_map.get(priority, "🟠 Medium")
    
    def _get_difficulty_display(self, difficulty: int) -> str:
        """Get human-readable difficulty display."""
        difficulty_map = {
            1: "⭐ Easy",
            2: "⭐⭐ Medium-Easy",
            3: "⭐⭐⭐ Medium", 
            4: "⭐⭐⭐⭐ Hard",
            5: "⭐⭐⭐⭐⭐ Expert"
        }
        return difficulty_map.get(difficulty, "⭐⭐⭐ Medium")
    
    def _calculate_completion_reward(self, epic: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate rewards for completing this epic."""
        base_points = epic.get('points', 0)
        difficulty_multiplier = epic.get('difficulty', 3) * 0.2
        
        # Bonus for high completion rate
        completion_bonus = 0
        if metrics['progress_percentage'] >= 100:
            completion_bonus = base_points * 0.5
        elif metrics['progress_percentage'] >= 80:
            completion_bonus = base_points * 0.2
        
        total_reward = int(base_points * (1 + difficulty_multiplier) + completion_bonus)
        
        return {
            'points': total_reward,
            'achievements': self._get_potential_achievements(epic, metrics),
            'badges': self._get_potential_badges(epic, metrics)
        }
    
    def _get_next_milestone(self, epic: Dict[str, Any], metrics: Dict[str, Any]) -> Optional[str]:
        """Get the next milestone for this epic."""
        progress = metrics['progress_percentage']
        
        if progress < 25:
            return "🎯 Complete 25% of tasks"
        elif progress < 50:
            return "🎯 Reach halfway point (50%)"
        elif progress < 75:
            return "🎯 Complete 75% of tasks"
        elif progress < 100:
            return "🏁 Complete final tasks"
        else:
            return "🎉 Epic completed!"
    
    def _get_potential_achievements(self, epic: Dict[str, Any], metrics: Dict[str, Any]) -> List[str]:
        """Get potential achievements for completing this epic."""
        achievements = []
        
        if epic.get('difficulty', 3) >= 4:
            achievements.append("🏆 Expert Level Challenge")
        
        if metrics['total_tasks'] >= 10:
            achievements.append("📋 Task Master")
        
        if epic.get('priority', 3) >= 4:
            achievements.append("🚨 Crisis Manager")
        
        return achievements
    
    def _get_potential_badges(self, epic: Dict[str, Any], metrics: Dict[str, Any]) -> List[str]:
        """Get potential badges for this epic."""
        badges = []
        
        if metrics['progress_percentage'] >= 100:
            badges.append("✅ Completion Badge")
        
        if epic.get('focus_time_minutes', 0) >= 240:  # 4+ hours
            badges.append("⏱️ Focus Champion")
        
        return badges