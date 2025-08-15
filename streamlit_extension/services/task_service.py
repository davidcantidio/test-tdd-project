"""
📋 Task Service Layer

Business logic for task management with TDD phase tracking.
Implements complete CRUD operations with epic relationships and time tracking.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
import json
import re

from .base import (
    BaseService, ServiceResult, ServiceError, ServiceErrorType,
    BaseRepository, PaginatedResult, FilterCriteria, SortCriteria
)
from ..utils.database import DatabaseManager
from ..config.constants import ValidationRules, TaskStatus, TDDPhase


class TaskRepository(BaseRepository):
    """Repository for task data access operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
    
    def find_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Find task by ID with epic and project information."""
        try:
            query = """
                SELECT t.*, e.title as epic_title, e.epic_key, 
                       p.name as project_name, c.name as client_name
                FROM framework_tasks t
                LEFT JOIN framework_epics e ON t.epic_id = e.id
                LEFT JOIN framework_projects p ON e.project_id = p.id
                LEFT JOIN framework_clients c ON p.client_id = c.id
                WHERE t.id = ?
            """
            result = self.db_manager.execute_query(query, (task_id,))
            return result[0] if result else None
        except Exception as e:
            self.db_manager.logger.error(f"Error finding task by ID {task_id}: {e}")
            return None
    
    def find_by_task_key(self, task_key: str) -> Optional[Dict[str, Any]]:
        """Find task by unique task key."""
        try:
            query = "SELECT * FROM framework_tasks WHERE task_key = ?"
            result = self.db_manager.execute_query(query, (task_key,))
            return result[0] if result else None
        except Exception as e:
            self.db_manager.logger.error(f"Error finding task by key {task_key}: {e}")
            return None
    
    def find_all(
        self, 
        filters: Optional[FilterCriteria] = None,
        sort: Optional[SortCriteria] = None,
        page: int = 1,
        page_size: int = 10
    ) -> PaginatedResult[Dict[str, Any]]:
        """Find all tasks with filtering, sorting, and pagination."""
        try:
            # Build base query with epic, project, and client information
            base_query = """
                SELECT t.*, e.title as epic_title, e.epic_key, 
                       p.name as project_name, c.name as client_name,
                       COALESCE(ws.total_time, 0) as total_time_minutes
                FROM framework_tasks t
                LEFT JOIN framework_epics e ON t.epic_id = e.id
                LEFT JOIN framework_projects p ON e.project_id = p.id
                LEFT JOIN framework_clients c ON p.client_id = c.id
                LEFT JOIN (
                    SELECT task_id, SUM(duration_minutes) as total_time
                    FROM work_sessions
                    GROUP BY task_id
                ) ws ON t.id = ws.task_id
            """
            
            where_conditions = []
            params = []
            
            if filters:
                if filters.has('status'):
                    where_conditions.append("t.status = ?")
                    params.append(filters.get('status'))
                
                if filters.has('tdd_phase'):
                    where_conditions.append("t.tdd_phase = ?")
                    params.append(filters.get('tdd_phase'))
                
                if filters.has('title'):
                    where_conditions.append("t.title LIKE ?")
                    params.append(f"%{filters.get('title')}%")
                
                if filters.has('task_key'):
                    where_conditions.append("t.task_key LIKE ?")
                    params.append(f"%{filters.get('task_key')}%")
                
                if filters.has('epic_id'):
                    where_conditions.append("t.epic_id = ?")
                    params.append(filters.get('epic_id'))
                
                if filters.has('project_id'):
                    where_conditions.append("e.project_id = ?")
                    params.append(filters.get('project_id'))
                
                if filters.has('client_id'):
                    where_conditions.append("p.client_id = ?")
                    params.append(filters.get('client_id'))
                
                if filters.has('priority'):
                    where_conditions.append("t.priority = ?")
                    params.append(filters.get('priority'))
                
                if filters.has('estimated_hours_min'):
                    where_conditions.append("t.estimated_hours >= ?")
                    params.append(filters.get('estimated_hours_min'))
                
                if filters.has('assigned_to'):
                    where_conditions.append("t.assigned_to LIKE ?")
                    params.append(f"%{filters.get('assigned_to')}%")
                
                if filters.has('due_date_from'):
                    where_conditions.append("t.due_date >= ?")
                    params.append(filters.get('due_date_from'))
                
                if filters.has('due_date_to'):
                    where_conditions.append("t.due_date <= ?")
                    params.append(filters.get('due_date_to'))
            
            # Build WHERE clause
            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Build ORDER BY clause
            order_clause = ""
            if sort:
                # Map sort fields to qualified column names
                sort_field = sort.field
                if sort_field in ['title', 'status', 'tdd_phase', 'priority', 'task_key', 'due_date']:
                    sort_field = f"t.{sort_field}"
                elif sort_field in ['epic_title']:
                    sort_field = f"e.title"
                elif sort_field in ['project_name']:
                    sort_field = f"p.name"
                elif sort_field in ['client_name']:
                    sort_field = f"c.name"
                elif sort_field == 'total_time':
                    sort_field = "total_time_minutes"
                
                order_clause = f" ORDER BY {sort_field} {'ASC' if sort.ascending else 'DESC'}"
            
            # Count total records
            count_query = f"""
                SELECT COUNT(*)
                FROM framework_tasks t
                LEFT JOIN framework_epics e ON t.epic_id = e.id
                LEFT JOIN framework_projects p ON e.project_id = p.id
                LEFT JOIN framework_clients c ON p.client_id = c.id
                {where_clause}
            """
            total_count = self.db_manager.execute_query(count_query, params)[0]['COUNT(*)']
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = (total_count + page_size - 1) // page_size
            
            # Get paginated results
            data_query = f"{base_query}{where_clause}{order_clause} LIMIT ? OFFSET ?"
            data_params = params + [page_size, offset]
            tasks = self.db_manager.execute_query(data_query, data_params)
            
            return PaginatedResult(
                items=tasks,
                total=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            self.db_manager.logger.error(f"Error finding tasks: {e}")
            return PaginatedResult([], 0, page, page_size, 0)
    
    def find_by_epic(self, epic_id: int) -> List[Dict[str, Any]]:
        """Find all tasks for a specific epic."""
        try:
            query = """
                SELECT t.*, COALESCE(ws.total_time, 0) as total_time_minutes
                FROM framework_tasks t
                LEFT JOIN (
                    SELECT task_id, SUM(duration_minutes) as total_time
                    FROM work_sessions
                    GROUP BY task_id
                ) ws ON t.id = ws.task_id
                WHERE t.epic_id = ?
                ORDER BY t.priority DESC, t.created_at ASC
            """
            return self.db_manager.execute_query(query, (epic_id,))
        except Exception as e:
            self.db_manager.logger.error(f"Error finding tasks for epic {epic_id}: {e}")
            return []
    
    def find_by_status(self, status: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find tasks by status."""
        try:
            query = """
                SELECT t.*, e.title as epic_title, e.epic_key
                FROM framework_tasks t
                LEFT JOIN framework_epics e ON t.epic_id = e.id
                WHERE t.status = ?
                ORDER BY t.priority DESC, t.created_at ASC
            """
            params = [status]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            self.db_manager.logger.error(f"Error finding tasks by status {status}: {e}")
            return []
    
    def find_by_tdd_phase(self, tdd_phase: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find tasks by TDD phase."""
        try:
            query = """
                SELECT t.*, e.title as epic_title, e.epic_key
                FROM framework_tasks t
                LEFT JOIN framework_epics e ON t.epic_id = e.id
                WHERE t.tdd_phase = ?
                ORDER BY t.priority DESC, t.created_at ASC
            """
            params = [tdd_phase]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            self.db_manager.logger.error(f"Error finding tasks by TDD phase {tdd_phase}: {e}")
            return []
    
    def create(self, task_data: Dict[str, Any]) -> Optional[int]:
        """Create new task and return the ID."""
        try:
            query = """
                INSERT INTO framework_tasks (
                    task_key, title, description, epic_id, status, tdd_phase,
                    priority, estimated_hours, assigned_to, due_date, 
                    test_criteria, acceptance_criteria, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                task_data['task_key'],
                task_data['title'],
                task_data.get('description'),
                task_data['epic_id'],
                task_data.get('status', TaskStatus.TODO.value),
                task_data.get('tdd_phase', TDDPhase.RED.value),
                task_data.get('priority', 3),  # Default medium priority
                task_data.get('estimated_hours'),
                task_data.get('assigned_to'),
                task_data.get('due_date'),
                json.dumps(task_data.get('test_criteria', [])),
                json.dumps(task_data.get('acceptance_criteria', [])),
                datetime.now()
            )
            
            return self.db_manager.execute_insert(query, params)
            
        except Exception as e:
            self.db_manager.logger.error(f"Error creating task: {e}")
            return None
    
    def update(self, task_id: int, task_data: Dict[str, Any]) -> bool:
        """Update existing task."""
        try:
            query = """
                UPDATE framework_tasks SET
                    task_key = ?, title = ?, description = ?, epic_id = ?,
                    status = ?, tdd_phase = ?, priority = ?, estimated_hours = ?,
                    assigned_to = ?, due_date = ?, test_criteria = ?,
                    acceptance_criteria = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                task_data['task_key'],
                task_data['title'],
                task_data.get('description'),
                task_data['epic_id'],
                task_data.get('status', TaskStatus.TODO.value),
                task_data.get('tdd_phase', TDDPhase.RED.value),
                task_data.get('priority', 3),
                task_data.get('estimated_hours'),
                task_data.get('assigned_to'),
                task_data.get('due_date'),
                json.dumps(task_data.get('test_criteria', [])),
                json.dumps(task_data.get('acceptance_criteria', [])),
                datetime.now(),
                task_id
            )
            
            affected_rows = self.db_manager.execute_update(query, params)
            return affected_rows > 0
            
        except Exception as e:
            self.db_manager.logger.error(f"Error updating task {task_id}: {e}")
            return False
    
    def delete(self, task_id: int) -> bool:
        """Delete task (hard delete since tasks are granular)."""
        try:
            # First delete related work sessions
            self.db_manager.execute_update(
                "DELETE FROM work_sessions WHERE task_id = ?", 
                (task_id,)
            )
            
            # Then delete the task
            query = "DELETE FROM framework_tasks WHERE id = ?"
            affected_rows = self.db_manager.execute_update(query, (task_id,))
            return affected_rows > 0
            
        except Exception as e:
            self.db_manager.logger.error(f"Error deleting task {task_id}: {e}")
            return False
    
    def epic_exists(self, epic_id: int) -> bool:
        """Check if epic exists and is not cancelled."""
        try:
            query = "SELECT id FROM framework_epics WHERE id = ? AND status != 'cancelled'"
            result = self.db_manager.execute_query(query, (epic_id,))
            return len(result) > 0
        except Exception as e:
            self.db_manager.logger.error(f"Error checking epic existence {epic_id}: {e}")
            return False
    
    def get_task_time_tracking(self, task_id: int) -> Dict[str, Any]:
        """Get time tracking data for a task."""
        try:
            query = """
                SELECT 
                    COUNT(*) as session_count,
                    SUM(duration_minutes) as total_minutes,
                    AVG(duration_minutes) as avg_session_minutes,
                    MAX(end_time) as last_session,
                    MIN(start_time) as first_session
                FROM work_sessions
                WHERE task_id = ?
            """
            result = self.db_manager.execute_query(query, (task_id,))
            
            if result and result[0]['session_count']:
                data = result[0]
                return {
                    'session_count': data['session_count'],
                    'total_minutes': data['total_minutes'] or 0,
                    'total_hours': round((data['total_minutes'] or 0) / 60, 2),
                    'avg_session_minutes': round(data['avg_session_minutes'] or 0, 1),
                    'last_session': data['last_session'],
                    'first_session': data['first_session']
                }
            else:
                return {
                    'session_count': 0,
                    'total_minutes': 0,
                    'total_hours': 0,
                    'avg_session_minutes': 0,
                    'last_session': None,
                    'first_session': None
                }
                
        except Exception as e:
            self.db_manager.logger.error(f"Error getting time tracking for task {task_id}: {e}")
            return {
                'session_count': 0,
                'total_minutes': 0,
                'total_hours': 0,
                'avg_session_minutes': 0,
                'last_session': None,
                'first_session': None
            }


class TaskService(BaseService):
    """Service for task business logic operations with TDD workflow."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.repository = TaskRepository(db_manager)
        super().__init__(self.repository)
    
    def validate_business_rules(self, data: Dict[str, Any]) -> List[ServiceError]:
        """Validate task-specific business rules."""
        errors = []
        
        # Task key format validation (TASK-X.X.X or similar)
        if 'task_key' in data and data['task_key']:
            task_key_pattern = r'^[A-Z0-9]+-\d+(\.\d+)*(\.\d+)*$'
            if not re.match(task_key_pattern, data['task_key']):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Task key must follow format 'TASK-1.1.1' or similar",
                    field="task_key"
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
                elif hours > 40:  # 40 hour limit per task
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Estimated hours cannot exceed 40 (consider breaking into smaller tasks)",
                        field="estimated_hours"
                    ))
            except (ValueError, TypeError):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Estimated hours must be a valid number",
                    field="estimated_hours"
                ))
        
        # Due date validation
        if 'due_date' in data and data['due_date']:
            if isinstance(data['due_date'], str):
                try:
                    due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
                    # Check if due date is not in the past (allow today)
                    if due_date < date.today():
                        errors.append(ServiceError(
                            error_type=ServiceErrorType.VALIDATION_ERROR,
                            message="Due date cannot be in the past",
                            field="due_date"
                        ))
                except ValueError:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Invalid due date format (use YYYY-MM-DD)",
                        field="due_date"
                    ))
        
        # Status validation
        if 'status' in data and data['status']:
            valid_statuses = TaskStatus.get_all_values()
            if data['status'] not in valid_statuses:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message=f"Status must be one of: {', '.join(valid_statuses)}",
                    field="status"
                ))
        
        # TDD Phase validation
        if 'tdd_phase' in data and data['tdd_phase']:
            valid_phases = TDDPhase.get_all_values()
            if data['tdd_phase'] not in valid_phases:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message=f"TDD phase must be one of: {', '.join(valid_phases)}",
                    field="tdd_phase"
                ))
        
        # TDD Phase + Status consistency validation
        if 'status' in data and 'tdd_phase' in data:
            status = data['status']
            tdd_phase = data['tdd_phase']
            
            # Business rules for TDD phase consistency
            if status == TaskStatus.COMPLETED.value and tdd_phase != TDDPhase.REFACTOR.value:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.BUSINESS_RULE_VIOLATION,
                    message="Completed tasks must be in REFACTOR phase (TDD cycle complete)",
                    field="tdd_phase"
                ))
            
            if status == TaskStatus.TODO.value and tdd_phase != TDDPhase.RED.value:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.BUSINESS_RULE_VIOLATION,
                    message="TODO tasks should typically start in RED phase",
                    field="tdd_phase"
                ))
        
        # Test criteria validation (must be JSON list)
        if 'test_criteria' in data and data['test_criteria'] is not None:
            if isinstance(data['test_criteria'], str):
                try:
                    criteria = json.loads(data['test_criteria'])
                    if not isinstance(criteria, list):
                        errors.append(ServiceError(
                            error_type=ServiceErrorType.VALIDATION_ERROR,
                            message="Test criteria must be a JSON array",
                            field="test_criteria"
                        ))
                except json.JSONDecodeError:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Test criteria must be valid JSON",
                        field="test_criteria"
                    ))
            elif not isinstance(data['test_criteria'], list):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Test criteria must be a list",
                    field="test_criteria"
                ))
        
        # Acceptance criteria validation (must be JSON list)
        if 'acceptance_criteria' in data and data['acceptance_criteria'] is not None:
            if isinstance(data['acceptance_criteria'], str):
                try:
                    criteria = json.loads(data['acceptance_criteria'])
                    if not isinstance(criteria, list):
                        errors.append(ServiceError(
                            error_type=ServiceErrorType.VALIDATION_ERROR,
                            message="Acceptance criteria must be a JSON array",
                            field="acceptance_criteria"
                        ))
                except json.JSONDecodeError:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Acceptance criteria must be valid JSON",
                        field="acceptance_criteria"
                    ))
            elif not isinstance(data['acceptance_criteria'], list):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Acceptance criteria must be a list",
                    field="acceptance_criteria"
                ))
        
        return errors
    
    def create_task(self, task_data: Dict[str, Any]) -> ServiceResult[int]:
        """
        Create a new task with TDD workflow validation.
        
        Args:
            task_data: Task information dictionary
            
        Returns:
            ServiceResult with task ID if successful
        """
        self.log_operation("create_task", task_data=task_data)
        
        # Validate required fields
        required_fields = ['task_key', 'title', 'epic_id']
        validation_errors = self.validate_required_fields(task_data, required_fields)
        
        # Validate business rules
        business_errors = self.validate_business_rules(task_data)
        validation_errors.extend(business_errors)
        
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        # Check if epic exists
        if not self.repository.epic_exists(task_data['epic_id']):
            return ServiceResult.business_rule_violation(
                f"Epic with ID {task_data['epic_id']} does not exist or is cancelled"
            )
        
        # Check task key uniqueness
        existing_task = self.repository.find_by_task_key(task_data['task_key'])
        if existing_task:
            return ServiceResult.business_rule_violation(
                f"Task with key '{task_data['task_key']}' already exists"
            )
        
        try:
            # Set default TDD phase and status if not provided
            if 'tdd_phase' not in task_data or not task_data['tdd_phase']:
                task_data['tdd_phase'] = TDDPhase.RED.value
            
            if 'status' not in task_data or not task_data['status']:
                task_data['status'] = TaskStatus.TODO.value
            
            # Create task
            task_id = self.repository.create(task_data)
            
            if task_id:
                self.log_operation("create_task_success", task_id=task_id)
                return ServiceResult.ok(task_id)
            else:
                return self.handle_database_error("create_task", Exception("Failed to create task"))
                
        except Exception as e:
            return self.handle_database_error("create_task", e)
    
    def get_task(self, task_id: int) -> ServiceResult[Dict[str, Any]]:
        """
        Get task by ID with epic and project information.
        
        Args:
            task_id: Task ID
            
        Returns:
            ServiceResult with task data if found
        """
        self.log_operation("get_task", task_id=task_id)
        
        try:
            task = self.repository.find_by_id(task_id)
            
            if task:
                # Parse JSON fields
                if 'test_criteria' in task and task['test_criteria']:
                    try:
                        task['test_criteria'] = json.loads(task['test_criteria'])
                    except json.JSONDecodeError:
                        task['test_criteria'] = []
                
                if 'acceptance_criteria' in task and task['acceptance_criteria']:
                    try:
                        task['acceptance_criteria'] = json.loads(task['acceptance_criteria'])
                    except json.JSONDecodeError:
                        task['acceptance_criteria'] = []
                
                return ServiceResult.ok(task)
            else:
                return ServiceResult.not_found("Task", task_id)
                
        except Exception as e:
            return self.handle_database_error("get_task", e)
    
    def update_task(self, task_id: int, task_data: Dict[str, Any]) -> ServiceResult[bool]:
        """
        Update existing task with TDD workflow validation.
        
        Args:
            task_id: Task ID
            task_data: Updated task information
            
        Returns:
            ServiceResult with success status
        """
        self.log_operation("update_task", task_id=task_id, task_data=task_data)
        
        # Check if task exists
        existing_task = self.repository.find_by_id(task_id)
        if not existing_task:
            return ServiceResult.not_found("Task", task_id)
        
        # Validate required fields
        required_fields = ['task_key', 'title', 'epic_id']
        validation_errors = self.validate_required_fields(task_data, required_fields)
        
        # Validate business rules
        business_errors = self.validate_business_rules(task_data)
        validation_errors.extend(business_errors)
        
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        # Check if epic exists
        if not self.repository.epic_exists(task_data['epic_id']):
            return ServiceResult.business_rule_violation(
                f"Epic with ID {task_data['epic_id']} does not exist or is cancelled"
            )
        
        # Check task key uniqueness (excluding current task)
        existing_key_task = self.repository.find_by_task_key(task_data['task_key'])
        if existing_key_task and existing_key_task['id'] != task_id:
            return ServiceResult.business_rule_violation(
                f"Another task with key '{task_data['task_key']}' already exists"
            )
        
        try:
            # Update task
            success = self.repository.update(task_id, task_data)
            
            if success:
                self.log_operation("update_task_success", task_id=task_id)
                return ServiceResult.ok(True)
            else:
                return ServiceResult.business_rule_violation("Failed to update task")
                
        except Exception as e:
            return self.handle_database_error("update_task", e)
    
    def delete_task(self, task_id: int) -> ServiceResult[bool]:
        """
        Delete task (hard delete).
        
        Args:
            task_id: Task ID
            
        Returns:
            ServiceResult with success status
        """
        self.log_operation("delete_task", task_id=task_id)
        
        # Check if task exists
        existing_task = self.repository.find_by_id(task_id)
        if not existing_task:
            return ServiceResult.not_found("Task", task_id)
        
        try:
            # Delete task (will also delete related work sessions)
            success = self.repository.delete(task_id)
            
            if success:
                self.log_operation("delete_task_success", task_id=task_id)
                return ServiceResult.ok(True)
            else:
                return ServiceResult.business_rule_violation("Failed to delete task")
                
        except Exception as e:
            return self.handle_database_error("delete_task", e)
    
    def list_tasks(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "priority",
        sort_ascending: bool = False,  # Default to highest priority first
        page: int = 1,
        page_size: int = 20
    ) -> ServiceResult[PaginatedResult[Dict[str, Any]]]:
        """
        List tasks with filtering, sorting, and pagination.
        
        Args:
            filters: Filter criteria dictionary
            sort_by: Field to sort by
            sort_ascending: Sort direction
            page: Page number (1-based)
            page_size: Items per page
            
        Returns:
            ServiceResult with paginated task list
        """
        self.log_operation("list_tasks", filters=filters, sort_by=sort_by, page=page)
        
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
            
            # Process JSON fields for each task
            for task in result.items:
                if 'test_criteria' in task and task['test_criteria']:
                    try:
                        task['test_criteria'] = json.loads(task['test_criteria'])
                    except json.JSONDecodeError:
                        task['test_criteria'] = []
                
                if 'acceptance_criteria' in task and task['acceptance_criteria']:
                    try:
                        task['acceptance_criteria'] = json.loads(task['acceptance_criteria'])
                    except json.JSONDecodeError:
                        task['acceptance_criteria'] = []
            
            self.log_operation("list_tasks_success", 
                             total_tasks=result.total, 
                             page=page, 
                             returned_count=len(result.items))
            
            return ServiceResult.ok(result)
            
        except Exception as e:
            return self.handle_database_error("list_tasks", e)
    
    def get_tasks_by_epic(self, epic_id: int) -> ServiceResult[List[Dict[str, Any]]]:
        """
        Get all tasks for a specific epic.
        
        Args:
            epic_id: Epic ID
            
        Returns:
            ServiceResult with list of tasks
        """
        self.log_operation("get_tasks_by_epic", epic_id=epic_id)
        
        try:
            # Check if epic exists
            if not self.repository.epic_exists(epic_id):
                return ServiceResult.business_rule_violation(
                    f"Epic with ID {epic_id} does not exist or is cancelled"
                )
            
            tasks = self.repository.find_by_epic(epic_id)
            
            # Process JSON fields for each task
            for task in tasks:
                if 'test_criteria' in task and task['test_criteria']:
                    try:
                        task['test_criteria'] = json.loads(task['test_criteria'])
                    except json.JSONDecodeError:
                        task['test_criteria'] = []
                
                if 'acceptance_criteria' in task and task['acceptance_criteria']:
                    try:
                        task['acceptance_criteria'] = json.loads(task['acceptance_criteria'])
                    except json.JSONDecodeError:
                        task['acceptance_criteria'] = []
            
            return ServiceResult.ok(tasks)
            
        except Exception as e:
            return self.handle_database_error("get_tasks_by_epic", e)
    
    def get_tasks_by_status(self, status: str, limit: Optional[int] = None) -> ServiceResult[List[Dict[str, Any]]]:
        """
        Get tasks by status for workflow management.
        
        Args:
            status: Task status
            limit: Optional limit on number of tasks
            
        Returns:
            ServiceResult with list of tasks
        """
        self.log_operation("get_tasks_by_status", status=status, limit=limit)
        
        try:
            # Validate status
            valid_statuses = TaskStatus.get_all_values()
            if status not in valid_statuses:
                return ServiceResult.validation_error(
                    f"Status must be one of: {', '.join(valid_statuses)}", "status"
                )
            
            tasks = self.repository.find_by_status(status, limit)
            return ServiceResult.ok(tasks)
            
        except Exception as e:
            return self.handle_database_error("get_tasks_by_status", e)
    
    def get_tasks_by_tdd_phase(self, tdd_phase: str, limit: Optional[int] = None) -> ServiceResult[List[Dict[str, Any]]]:
        """
        Get tasks by TDD phase for workflow management.
        
        Args:
            tdd_phase: TDD phase
            limit: Optional limit on number of tasks
            
        Returns:
            ServiceResult with list of tasks
        """
        self.log_operation("get_tasks_by_tdd_phase", tdd_phase=tdd_phase, limit=limit)
        
        try:
            # Validate TDD phase
            valid_phases = TDDPhase.get_all_values()
            if tdd_phase not in valid_phases:
                return ServiceResult.validation_error(
                    f"TDD phase must be one of: {', '.join(valid_phases)}", "tdd_phase"
                )
            
            tasks = self.repository.find_by_tdd_phase(tdd_phase, limit)
            return ServiceResult.ok(tasks)
            
        except Exception as e:
            return self.handle_database_error("get_tasks_by_tdd_phase", e)
    
    def advance_tdd_phase(self, task_id: int) -> ServiceResult[str]:
        """
        Advance task to next TDD phase (RED -> GREEN -> REFACTOR).
        
        Args:
            task_id: Task ID
            
        Returns:
            ServiceResult with new TDD phase
        """
        self.log_operation("advance_tdd_phase", task_id=task_id)
        
        try:
            # Get current task
            task_result = self.get_task(task_id)
            if not task_result.success:
                return task_result
            
            task = task_result.data
            current_phase = task.get('tdd_phase', TDDPhase.RED.value)
            
            # Determine next phase
            phase_progression = {
                TDDPhase.RED.value: TDDPhase.GREEN.value,
                TDDPhase.GREEN.value: TDDPhase.REFACTOR.value,
                TDDPhase.REFACTOR.value: TDDPhase.RED.value  # Cycle back for new features
            }
            
            new_phase = phase_progression.get(current_phase, TDDPhase.RED.value)
            
            # Update status based on new phase
            new_status = task.get('status', TaskStatus.TODO.value)
            if new_phase == TDDPhase.GREEN.value:
                new_status = TaskStatus.IN_PROGRESS.value
            elif new_phase == TDDPhase.REFACTOR.value:
                new_status = TaskStatus.IN_PROGRESS.value
            elif new_phase == TDDPhase.RED.value and current_phase == TDDPhase.REFACTOR.value:
                # Completing a full TDD cycle
                new_status = TaskStatus.COMPLETED.value
            
            # Update task
            update_data = {
                **task,
                'tdd_phase': new_phase,
                'status': new_status
            }
            
            update_result = self.update_task(task_id, update_data)
            if update_result.success:
                self.log_operation("advance_tdd_phase_success", 
                                 task_id=task_id, 
                                 old_phase=current_phase, 
                                 new_phase=new_phase)
                return ServiceResult.ok(new_phase)
            else:
                return update_result
                
        except Exception as e:
            return self.handle_database_error("advance_tdd_phase", e)
    
    def get_task_summary(self, task_id: int) -> ServiceResult[Dict[str, Any]]:
        """
        Get task summary with time tracking and TDD progress.
        
        Args:
            task_id: Task ID
            
        Returns:
            ServiceResult with task summary data
        """
        self.log_operation("get_task_summary", task_id=task_id)
        
        try:
            # Get task data
            task_result = self.get_task(task_id)
            if not task_result.success:
                return task_result
            
            task = task_result.data
            
            # Get time tracking data
            time_data = self.repository.get_task_time_tracking(task_id)
            
            # Build summary with TDD workflow information
            summary = {
                **task,
                **time_data,
                'status_display': TaskStatus.get_display_name(task.get('status', 'todo')),
                'tdd_phase_display': TDDPhase.get_display_name(task.get('tdd_phase', 'red')),
                'priority_display': self._get_priority_display(task.get('priority', 3)),
                'progress_percentage': self._calculate_task_progress(task),
                'next_tdd_phase': self._get_next_tdd_phase(task.get('tdd_phase', 'red')),
                'estimated_vs_actual': self._compare_estimated_vs_actual(task, time_data),
                'is_overdue': self._is_task_overdue(task.get('due_date')),
                'days_until_due': self._days_until_due(task.get('due_date'))
            }
            
            return ServiceResult.ok(summary)
            
        except Exception as e:
            return self.handle_database_error("get_task_summary", e)
    
    def validate_task_data(self, task_data: Dict[str, Any]) -> ServiceResult[bool]:
        """
        Validate task data without creating/updating.
        
        Args:
            task_data: Task data to validate
            
        Returns:
            ServiceResult indicating if data is valid
        """
        # Validate required fields
        required_fields = ['task_key', 'title', 'epic_id']
        validation_errors = self.validate_required_fields(task_data, required_fields)
        
        # Validate business rules
        business_errors = self.validate_business_rules(task_data)
        validation_errors.extend(business_errors)
        
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        return ServiceResult.ok(True)
    
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
    
    def _calculate_task_progress(self, task: Dict[str, Any]) -> float:
        """Calculate task progress based on TDD phase and status."""
        status = task.get('status', 'todo')
        tdd_phase = task.get('tdd_phase', 'red')
        
        if status == TaskStatus.COMPLETED.value:
            return 100.0
        elif status == TaskStatus.IN_PROGRESS.value:
            if tdd_phase == TDDPhase.GREEN.value:
                return 50.0
            elif tdd_phase == TDDPhase.REFACTOR.value:
                return 80.0
            else:
                return 30.0
        elif tdd_phase == TDDPhase.RED.value and status != TaskStatus.TODO.value:
            return 20.0
        else:
            return 0.0
    
    def _get_next_tdd_phase(self, current_phase: str) -> str:
        """Get next TDD phase in the cycle."""
        phase_progression = {
            TDDPhase.RED.value: TDDPhase.GREEN.value,
            TDDPhase.GREEN.value: TDDPhase.REFACTOR.value,
            TDDPhase.REFACTOR.value: "Complete"
        }
        return phase_progression.get(current_phase, TDDPhase.GREEN.value)
    
    def _compare_estimated_vs_actual(self, task: Dict[str, Any], time_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare estimated vs actual time spent."""
        estimated_hours = task.get('estimated_hours')
        actual_hours = time_data.get('total_hours', 0)
        
        if estimated_hours and estimated_hours > 0:
            variance_hours = actual_hours - estimated_hours
            variance_percentage = (variance_hours / estimated_hours) * 100
            
            return {
                'estimated_hours': estimated_hours,
                'actual_hours': actual_hours,
                'variance_hours': round(variance_hours, 2),
                'variance_percentage': round(variance_percentage, 1),
                'is_over_estimate': variance_hours > 0,
                'accuracy_rating': self._get_estimate_accuracy_rating(abs(variance_percentage))
            }
        else:
            return {
                'estimated_hours': estimated_hours,
                'actual_hours': actual_hours,
                'variance_hours': None,
                'variance_percentage': None,
                'is_over_estimate': None,
                'accuracy_rating': 'No estimate provided'
            }
    
    def _get_estimate_accuracy_rating(self, variance_percentage: float) -> str:
        """Get accuracy rating based on variance percentage."""
        if variance_percentage <= 10:
            return "🎯 Excellent"
        elif variance_percentage <= 25:
            return "👍 Good"
        elif variance_percentage <= 50:
            return "👌 Fair"
        else:
            return "🔄 Needs Improvement"
    
    def _is_task_overdue(self, due_date: Any) -> bool:
        """Check if task is overdue."""
        if not due_date:
            return False
        
        try:
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            
            return due_date < date.today()
        except (ValueError, TypeError):
            return False
    
    def _days_until_due(self, due_date: Any) -> Optional[int]:
        """Calculate days until due date."""
        if not due_date:
            return None
        
        try:
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            
            delta = due_date - date.today()
            return delta.days
        except (ValueError, TypeError):
            return None