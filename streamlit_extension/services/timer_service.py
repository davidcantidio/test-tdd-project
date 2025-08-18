"""
⏱️ Timer Service Layer

Business logic for time tracking, focus sessions, and TDAH-optimized productivity.
Implements pomodoro technique, session management, and productivity analytics.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from enum import Enum

from .base import (
    BaseService, ServiceResult, ServiceError, ServiceErrorType,
    BaseRepository
)
from ..utils.database import DatabaseManager


class SessionStatus(Enum):
    """Work session status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionType(Enum):
    """Work session type enumeration."""
    FOCUS = "focus"
    BREAK = "break"
    LONG_BREAK = "long_break"
    DEEP_WORK = "deep_work"
    PLANNING = "planning"
    REVIEW = "review"


class TimerRepository(BaseRepository):
    """Repository for timer and work session data access operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
    
    def find_session_by_id(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Find work session by ID."""
        try:
            query = """
                SELECT ws.*, t.title as task_title, t.task_key, 
                       e.title as epic_title, e.epic_key
                FROM work_sessions ws
                LEFT JOIN framework_tasks t ON ws.task_id = t.id
                LEFT JOIN framework_epics e ON t.epic_id = e.id
                WHERE ws.id = ?
            """
            result = self.db_manager.execute_query(query, (session_id,))
            return result[0] if result else None
        except Exception as e:
            self.db_manager.logger.error(f"Error finding session by ID {session_id}: {e}")
            return None
    
    def find_active_session(self) -> Optional[Dict[str, Any]]:
        """Find currently active work session."""
        try:
            query = """
                SELECT ws.*, t.title as task_title, t.task_key,
                       e.title as epic_title, e.epic_key
                FROM work_sessions ws
                LEFT JOIN framework_tasks t ON ws.task_id = t.id
                LEFT JOIN framework_epics e ON t.epic_id = e.id
                WHERE ws.status = 'active'
                ORDER BY ws.start_time DESC
                LIMIT 1
            """
            result = self.db_manager.execute_query(query)
            return result[0] if result else None
        except Exception as e:
            self.db_manager.logger.error(f"Error finding active session: {e}")
            return None
    
    def find_sessions_by_task(self, task_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find all work sessions for a specific task."""
        try:
            query = """
                SELECT * FROM work_sessions
                WHERE task_id = ?
                ORDER BY start_time DESC
            """
            params = [task_id]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            self.db_manager.logger.error(f"Error finding sessions for task {task_id}: {e}")
            return []
    
    def find_sessions_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        task_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Find work sessions within a date range."""
        try:
            base_query = """
                SELECT ws.*, t.title as task_title, t.task_key,
                       e.title as epic_title, e.epic_key
                FROM work_sessions ws
                LEFT JOIN framework_tasks t ON ws.task_id = t.id
                LEFT JOIN framework_epics e ON t.epic_id = e.id
                WHERE ws.start_time >= ? AND ws.start_time <= ?
            """
            params = [start_date, end_date]
            
            if task_id:
                base_query += " AND ws.task_id = ?"
                params.append(task_id)
            
            base_query += " ORDER BY ws.start_time DESC"
            
            return self.db_manager.execute_query(base_query, params)
        except Exception as e:
            self.db_manager.logger.error(f"Error finding sessions by date range: {e}")
            return []
    
    def find_recent_sessions(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """Find recent work sessions."""
        try:
            date_filter = datetime.now() - timedelta(days=days)
            
            query = """
                SELECT ws.*, t.title as task_title, t.task_key,
                       e.title as epic_title, e.epic_key
                FROM work_sessions ws
                LEFT JOIN framework_tasks t ON ws.task_id = t.id
                LEFT JOIN framework_epics e ON t.epic_id = e.id
                WHERE ws.start_time >= ?
                ORDER BY ws.start_time DESC
                LIMIT ?
            """
            
            return self.db_manager.execute_query(query, [date_filter, limit])
        except Exception as e:
            self.db_manager.logger.error(f"Error finding recent sessions: {e}")
            return []
    
    def create_session(self, session_data: Dict[str, Any]) -> Optional[int]:
        """Create new work session and return the ID."""
        try:
            query = """
                INSERT INTO work_sessions (
                    task_id, epic_id, session_type, status, start_time,
                    planned_duration_minutes, focus_rating, energy_level,
                    mood_rating, environment_notes, interruption_count,
                    notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                session_data.get('task_id'),
                session_data.get('epic_id'),
                session_data.get('session_type', SessionType.FOCUS.value),
                session_data.get('status', SessionStatus.ACTIVE.value),
                session_data.get('start_time', datetime.now()),
                session_data.get('planned_duration_minutes', 25),  # Default Pomodoro
                session_data.get('focus_rating'),
                session_data.get('energy_level'),
                session_data.get('mood_rating'),
                session_data.get('environment_notes'),
                session_data.get('interruption_count', 0),
                session_data.get('notes'),
                datetime.now()
            )
            
            return self.db_manager.execute_insert(query, params)
            
        except Exception as e:
            self.db_manager.logger.error(f"Error creating session: {e}")
            return None
    
    def update_session(self, session_id: int, session_data: Dict[str, Any]) -> bool:
        """Update existing work session."""
        try:
            query = """
                UPDATE work_sessions SET
                    status = ?, end_time = ?, duration_minutes = ?,
                    focus_rating = ?, energy_level = ?, mood_rating = ?,
                    environment_notes = ?, interruption_count = ?,
                    notes = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                session_data.get('status'),
                session_data.get('end_time'),
                session_data.get('duration_minutes'),
                session_data.get('focus_rating'),
                session_data.get('energy_level'),
                session_data.get('mood_rating'),
                session_data.get('environment_notes'),
                session_data.get('interruption_count', 0),
                session_data.get('notes'),
                datetime.now(),
                session_id
            )
            
            affected_rows = self.db_manager.execute_update(query, params)
            return affected_rows > 0
            
        except Exception as e:
            self.db_manager.logger.error(f"Error updating session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: int) -> bool:
        """Delete work session."""
        try:
            query = "DELETE FROM work_sessions WHERE id = ?"
            affected_rows = self.db_manager.execute_update(query, (session_id,))
            return affected_rows > 0
        except Exception as e:
            self.db_manager.logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def get_session_statistics(self, task_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """Get session statistics for analytics."""
        try:
            date_filter = datetime.now() - timedelta(days=days)
            
            if task_id:
                where_clause = "WHERE task_id = ? AND start_time >= ?"
                params = [task_id, date_filter]
            else:
                where_clause = "WHERE start_time >= ?"
                params = [date_filter]
            
            query = f"""
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(duration_minutes) as total_minutes,
                    AVG(duration_minutes) as avg_duration,
                    MAX(duration_minutes) as max_duration,
                    MIN(duration_minutes) as min_duration,
                    AVG(focus_rating) as avg_focus_rating,
                    AVG(energy_level) as avg_energy_level,
                    AVG(mood_rating) as avg_mood_rating,
                    SUM(interruption_count) as total_interruptions,
                    AVG(interruption_count) as avg_interruptions_per_session
                FROM work_sessions
                {where_clause}
                AND status = 'completed'
            """
            
            result = self.db_manager.execute_query(query, params)
            return result[0] if result else {}
            
        except Exception as e:
            self.db_manager.logger.error(f"Error getting session statistics: {e}")
            return {}
    
    def get_productivity_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Get productivity patterns for analysis."""
        try:
            date_filter = datetime.now() - timedelta(days=days)
            
            # Sessions by hour of day
            hourly_query = """
                SELECT 
                    CAST(strftime('%H', start_time) AS INTEGER) as hour_of_day,
                    COUNT(*) as session_count,
                    SUM(duration_minutes) as total_minutes,
                    AVG(focus_rating) as avg_focus
                FROM work_sessions
                WHERE start_time >= ? AND status = 'completed'
                GROUP BY hour_of_day
                ORDER BY hour_of_day
            """
            
            hourly_results = self.db_manager.execute_query(hourly_query, [date_filter])
            
            # Sessions by day of week
            daily_query = """
                SELECT 
                    CAST(strftime('%w', start_time) AS INTEGER) as day_of_week,
                    COUNT(*) as session_count,
                    SUM(duration_minutes) as total_minutes,
                    AVG(focus_rating) as avg_focus
                FROM work_sessions
                WHERE start_time >= ? AND status = 'completed'
                GROUP BY day_of_week
                ORDER BY day_of_week
            """
            
            daily_results = self.db_manager.execute_query(daily_query, [date_filter])
            
            # Session type distribution
            type_query = """
                SELECT 
                    session_type,
                    COUNT(*) as session_count,
                    SUM(duration_minutes) as total_minutes,
                    AVG(focus_rating) as avg_focus
                FROM work_sessions
                WHERE start_time >= ? AND status = 'completed'
                GROUP BY session_type
            """
            
            type_results = self.db_manager.execute_query(type_query, [date_filter])
            
            return {
                'hourly_patterns': hourly_results,
                'daily_patterns': daily_results,
                'type_distribution': type_results
            }
            
        except Exception as e:
            self.db_manager.logger.error(f"Error getting productivity patterns: {e}")
            return {}
    
    def task_exists(self, task_id: int) -> bool:
        """Check if task exists."""
        try:
            query = "SELECT id FROM framework_tasks WHERE id = ?"
            result = self.db_manager.execute_query(query, (task_id,))
            return len(result) > 0
        except Exception as e:
            self.db_manager.logger.error(f"Error checking task existence {task_id}: {e}")
            return False
    
    def epic_exists(self, epic_id: int) -> bool:
        """Check if epic exists."""
        try:
            query = "SELECT id FROM framework_epics WHERE id = ?"
            result = self.db_manager.execute_query(query, (epic_id,))
            return len(result) > 0
        except Exception as e:
            self.db_manager.logger.error(f"Error checking epic existence {epic_id}: {e}")
            return False


class TimerService(BaseService):
    """Service for timer and work session management with TDAH optimization."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.repository = TimerRepository(db_manager)
        super().__init__(self.repository)
    
    def validate_business_rules(self, data: Dict[str, Any]) -> List[ServiceError]:
        """Validate timer-specific business rules."""
        errors = []
        
        # Planned duration validation
        if 'planned_duration_minutes' in data and data['planned_duration_minutes'] is not None:
            try:
                duration = int(data['planned_duration_minutes'])
                if duration < 1:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Planned duration must be at least 1 minute",
                        field="planned_duration_minutes"
                    ))
                elif duration > 480:  # 8 hours max
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Planned duration cannot exceed 480 minutes (8 hours)",
                        field="planned_duration_minutes"
                    ))
            except (ValueError, TypeError):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Planned duration must be a valid number of minutes",
                    field="planned_duration_minutes"
                ))
        
        # Rating validations (1-10 scale)
        rating_fields = ['focus_rating', 'energy_level', 'mood_rating']
        for field in rating_fields:
            if field in data and data[field] is not None:
                try:
                    rating = int(data[field])
                    if rating < 1 or rating > 10:
                        errors.append(ServiceError(
                            error_type=ServiceErrorType.VALIDATION_ERROR,
                            message=f"{field.replace('_', ' ').title()} must be between 1 and 10",
                            field=field
                        ))
                except (ValueError, TypeError):
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message=f"{field.replace('_', ' ').title()} must be a valid number",
                        field=field
                    ))
        
        # Interruption count validation
        if 'interruption_count' in data and data['interruption_count'] is not None:
            try:
                count = int(data['interruption_count'])
                if count < 0:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Interruption count cannot be negative",
                        field="interruption_count"
                    ))
                elif count > 100:  # Reasonable upper limit
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="Interruption count seems unrealistic (max 100)",
                        field="interruption_count"
                    ))
            except (ValueError, TypeError):
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message="Interruption count must be a valid number",
                    field="interruption_count"
                ))
        
        # Session type validation
        if 'session_type' in data and data['session_type']:
            valid_types = [t.value for t in SessionType]
            if data['session_type'] not in valid_types:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message=f"Session type must be one of: {', '.join(valid_types)}",
                    field="session_type"
                ))
        
        # Status validation
        if 'status' in data and data['status']:
            valid_statuses = [s.value for s in SessionStatus]
            if data['status'] not in valid_statuses:
                errors.append(ServiceError(
                    error_type=ServiceErrorType.VALIDATION_ERROR,
                    message=f"Status must be one of: {', '.join(valid_statuses)}",
                    field="status"
                ))
        
        # Time consistency validation
        if 'start_time' in data and 'end_time' in data:
            start_time = data['start_time']
            end_time = data['end_time']
            
            if start_time and end_time:
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                
                if end_time <= start_time:
                    errors.append(ServiceError(
                        error_type=ServiceErrorType.VALIDATION_ERROR,
                        message="End time must be after start time",
                        field="end_time"
                    ))
        
        return errors
    
    def start_session(self, session_data: Dict[str, Any]) -> ServiceResult[int]:
        """
        Start a new work session.
        
        Args:
            session_data: Session information dictionary
            
        Returns:
            ServiceResult with session ID if successful
        """
        self.log_operation("start_session", session_data=session_data)
        
        # Check for active session
        active_session = self.repository.find_active_session()
        if active_session:
            return ServiceResult.business_rule_violation(
                f"Cannot start new session. Active session {active_session['id']} is running. "
                "Please stop or pause the current session first."
            )
        
        # Validate business rules
        validation_errors = self.validate_business_rules(session_data)
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        # Validate task/epic existence
        if 'task_id' in session_data and session_data['task_id']:
            if not self.repository.task_exists(session_data['task_id']):
                return ServiceResult.business_rule_violation(
                    f"Task with ID {session_data['task_id']} does not exist"
                )
        
        if 'epic_id' in session_data and session_data['epic_id']:
            if not self.repository.epic_exists(session_data['epic_id']):
                return ServiceResult.business_rule_violation(
                    f"Epic with ID {session_data['epic_id']} does not exist"
                )
        
        try:
            # Set default values
            session_data.setdefault('start_time', datetime.now())
            session_data.setdefault('status', SessionStatus.ACTIVE.value)
            session_data.setdefault('session_type', SessionType.FOCUS.value)
            session_data.setdefault('planned_duration_minutes', 25)  # Default Pomodoro
            
            # Create session
            session_id = self.repository.create_session(session_data)
            
            if session_id:
                self.log_operation("start_session_success", session_id=session_id)
                return ServiceResult.ok(session_id)
            else:
                return self.handle_database_error("start_session", Exception("Failed to create session"))
                
        except Exception as e:
            return self.handle_database_error("start_session", e)
    
    def stop_session(self, session_id: int, completion_data: Optional[Dict[str, Any]] = None) -> ServiceResult[Dict[str, Any]]:
        """
        Stop/complete a work session.
        
        Args:
            session_id: Session ID to stop
            completion_data: Optional completion data (ratings, notes, etc.)
            
        Returns:
            ServiceResult with session summary
        """
        self.log_operation("stop_session", session_id=session_id, completion_data=completion_data)
        
        # Get current session
        session = self.repository.find_session_by_id(session_id)
        if not session:
            return ServiceResult.not_found("Work session", session_id)
        
        if session['status'] not in [SessionStatus.ACTIVE.value, SessionStatus.PAUSED.value]:
            return ServiceResult.business_rule_violation(
                f"Cannot stop session with status '{session['status']}'"
            )
        
        try:
            # Calculate session duration
            end_time = datetime.now()
            start_time = datetime.fromisoformat(session['start_time']) if isinstance(session['start_time'], str) else session['start_time']
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
            
            # Prepare update data
            update_data = {
                'status': SessionStatus.COMPLETED.value,
                'end_time': end_time,
                'duration_minutes': duration_minutes,
            }
            
            # Add completion data if provided
            if completion_data:
                update_data.update(completion_data)
            
            # Validate completion data
            validation_errors = self.validate_business_rules(update_data)
            if validation_errors:
                return ServiceResult.fail_multiple(validation_errors)
            
            # Update session
            success = self.repository.update_session(session_id, update_data)
            
            if success:
                # Get updated session for summary
                updated_session = self.repository.find_session_by_id(session_id)
                
                session_summary = {
                    'session_id': session_id,
                    'duration_minutes': duration_minutes,
                    'duration_display': self._format_duration(duration_minutes),
                    'planned_vs_actual': self._compare_planned_vs_actual(
                        session.get('planned_duration_minutes', 0), 
                        duration_minutes
                    ),
                    'task_info': {
                        'task_id': session.get('task_id'),
                        'task_title': session.get('task_title'),
                        'epic_title': session.get('epic_title')
                    },
                    'performance_metrics': self._calculate_performance_metrics(updated_session),
                    'recommendations': self._generate_session_recommendations(updated_session)
                }
                
                self.log_operation("stop_session_success", session_id=session_id, duration=duration_minutes)
                return ServiceResult.ok(session_summary)
            else:
                return ServiceResult.business_rule_violation("Failed to stop session")
                
        except Exception as e:
            return self.handle_database_error("stop_session", e)
    
    def pause_session(self, session_id: int) -> ServiceResult[bool]:
        """
        Pause an active work session.
        
        Args:
            session_id: Session ID to pause
            
        Returns:
            ServiceResult with success status
        """
        self.log_operation("pause_session", session_id=session_id)
        
        # Get current session
        session = self.repository.find_session_by_id(session_id)
        if not session:
            return ServiceResult.not_found("Work session", session_id)
        
        if session['status'] != SessionStatus.ACTIVE.value:
            return ServiceResult.business_rule_violation(
                f"Cannot pause session with status '{session['status']}'"
            )
        
        try:
            # Update session to paused
            update_data = {'status': SessionStatus.PAUSED.value}
            success = self.repository.update_session(session_id, update_data)
            
            if success:
                self.log_operation("pause_session_success", session_id=session_id)
                return ServiceResult.ok(True)
            else:
                return ServiceResult.business_rule_violation("Failed to pause session")
                
        except Exception as e:
            return self.handle_database_error("pause_session", e)
    
    def resume_session(self, session_id: int) -> ServiceResult[bool]:
        """
        Resume a paused work session.
        
        Args:
            session_id: Session ID to resume
            
        Returns:
            ServiceResult with success status
        """
        self.log_operation("resume_session", session_id=session_id)
        
        # Check for other active sessions
        active_session = self.repository.find_active_session()
        if active_session and active_session['id'] != session_id:
            return ServiceResult.business_rule_violation(
                f"Cannot resume session. Another session {active_session['id']} is active"
            )
        
        # Get current session
        session = self.repository.find_session_by_id(session_id)
        if not session:
            return ServiceResult.not_found("Work session", session_id)
        
        if session['status'] != SessionStatus.PAUSED.value:
            return ServiceResult.business_rule_violation(
                f"Cannot resume session with status '{session['status']}'"
            )
        
        try:
            # Update session to active
            update_data = {'status': SessionStatus.ACTIVE.value}
            success = self.repository.update_session(session_id, update_data)
            
            if success:
                self.log_operation("resume_session_success", session_id=session_id)
                return ServiceResult.ok(True)
            else:
                return ServiceResult.business_rule_violation("Failed to resume session")
                
        except Exception as e:
            return self.handle_database_error("resume_session", e)
    
    def cancel_session(self, session_id: int, reason: Optional[str] = None) -> ServiceResult[bool]:
        """
        Cancel a work session.
        
        Args:
            session_id: Session ID to cancel
            reason: Optional cancellation reason
            
        Returns:
            ServiceResult with success status
        """
        self.log_operation("cancel_session", session_id=session_id, reason=reason)
        
        # Get current session
        session = self.repository.find_session_by_id(session_id)
        if not session:
            return ServiceResult.not_found("Work session", session_id)
        
        if session['status'] in [SessionStatus.COMPLETED.value, SessionStatus.CANCELLED.value]:
            return ServiceResult.business_rule_violation(
                f"Cannot cancel session with status '{session['status']}'"
            )
        
        try:
            # Update session to cancelled
            update_data = {
                'status': SessionStatus.CANCELLED.value,
                'end_time': datetime.now(),
                'notes': f"Cancelled: {reason}" if reason else "Cancelled"
            }
            success = self.repository.update_session(session_id, update_data)
            
            if success:
                self.log_operation("cancel_session_success", session_id=session_id)
                return ServiceResult.ok(True)
            else:
                return ServiceResult.business_rule_violation("Failed to cancel session")
                
        except Exception as e:
            return self.handle_database_error("cancel_session", e)
    
    def get_active_session(self) -> ServiceResult[Optional[Dict[str, Any]]]:
        """
        Get currently active work session.
        
        Returns:
            ServiceResult with active session or None
        """
        self.log_operation("get_active_session")
        
        try:
            active_session = self.repository.find_active_session()
            
            if active_session:
                # Add calculated fields
                active_session['elapsed_minutes'] = self._calculate_elapsed_time(active_session)
                active_session['remaining_minutes'] = self._calculate_remaining_time(active_session)
                active_session['progress_percentage'] = self._calculate_progress_percentage(active_session)
            
            return ServiceResult.ok(active_session)
            
        except Exception as e:
            return self.handle_database_error("get_active_session", e)
    
    def get_session(self, session_id: int) -> ServiceResult[Dict[str, Any]]:
        """
        Get work session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            ServiceResult with session data
        """
        self.log_operation("get_session", session_id=session_id)
        
        try:
            session = self.repository.find_session_by_id(session_id)
            
            if session:
                # Add calculated fields
                if session['status'] == SessionStatus.ACTIVE.value:
                    session['elapsed_minutes'] = self._calculate_elapsed_time(session)
                    session['remaining_minutes'] = self._calculate_remaining_time(session)
                    session['progress_percentage'] = self._calculate_progress_percentage(session)
                
                return ServiceResult.ok(session)
            else:
                return ServiceResult.not_found("Work session", session_id)
                
        except Exception as e:
            return self.handle_database_error("get_session", e)
    
    def get_sessions_for_task(self, task_id: int, limit: Optional[int] = None) -> ServiceResult[List[Dict[str, Any]]]:
        """
        Get all work sessions for a specific task.
        
        Args:
            task_id: Task ID
            limit: Optional limit on number of sessions
            
        Returns:
            ServiceResult with list of sessions
        """
        self.log_operation("get_sessions_for_task", task_id=task_id, limit=limit)
        
        try:
            sessions = self.repository.find_sessions_by_task(task_id, limit)
            return ServiceResult.ok(sessions)
            
        except Exception as e:
            return self.handle_database_error("get_sessions_for_task", e)
    
    def get_recent_sessions(self, days: int = 7, limit: int = 50) -> ServiceResult[List[Dict[str, Any]]]:
        """
        Get recent work sessions.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of sessions to return
            
        Returns:
            ServiceResult with list of recent sessions
        """
        self.log_operation("get_recent_sessions", days=days, limit=limit)
        
        try:
            if days < 1 or days > 365:
                return ServiceResult.validation_error("Days must be between 1 and 365", "days")
            
            sessions = self.repository.find_recent_sessions(days, limit)
            return ServiceResult.ok(sessions)
            
        except Exception as e:
            return self.handle_database_error("get_recent_sessions", e)
    
    def get_session_statistics(self, task_id: Optional[int] = None, days: int = 30) -> ServiceResult[Dict[str, Any]]:
        """
        Get session statistics for analytics.
        
        Args:
            task_id: Optional task ID to filter by
            days: Number of days to analyze
            
        Returns:
            ServiceResult with session statistics
        """
        self.log_operation("get_session_statistics", task_id=task_id, days=days)
        
        try:
            if days < 1 or days > 365:
                return ServiceResult.validation_error("Days must be between 1 and 365", "days")
            
            stats = self.repository.get_session_statistics(task_id, days)
            
            # Add derived metrics
            if stats:
                stats['total_hours'] = round((stats.get('total_minutes', 0) or 0) / 60, 2)
                stats['avg_duration_display'] = self._format_duration(stats.get('avg_duration', 0) or 0)
                stats['productivity_score'] = self._calculate_productivity_score(stats)
                stats['focus_consistency'] = self._calculate_focus_consistency(stats)
            
            return ServiceResult.ok(stats)
            
        except Exception as e:
            return self.handle_database_error("get_session_statistics", e)
    
    def get_productivity_patterns(self, days: int = 30) -> ServiceResult[Dict[str, Any]]:
        """
        Get productivity patterns for analysis.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            ServiceResult with productivity patterns
        """
        self.log_operation("get_productivity_patterns", days=days)
        
        try:
            if days < 1 or days > 365:
                return ServiceResult.validation_error("Days must be between 1 and 365", "days")
            
            patterns = self.repository.get_productivity_patterns(days)
            
            # Analyze patterns
            analysis = {
                'peak_productivity_hour': self._find_peak_hour(patterns.get('hourly_patterns', [])),
                'best_day_of_week': self._find_best_day(patterns.get('daily_patterns', [])),
                'preferred_session_type': self._find_preferred_type(patterns.get('type_distribution', [])),
                'focus_trends': self._analyze_focus_trends(patterns),
                'recommendations': self._generate_pattern_recommendations(patterns)
            }
            
            return ServiceResult.ok({**patterns, 'analysis': analysis})
            
        except Exception as e:
            return self.handle_database_error("get_productivity_patterns", e)
    
    def suggest_optimal_session(self, task_id: Optional[int] = None) -> ServiceResult[Dict[str, Any]]:
        """
        Suggest optimal session configuration based on patterns.
        
        Args:
            task_id: Optional task ID for task-specific suggestions
            
        Returns:
            ServiceResult with session suggestions
        """
        self.log_operation("suggest_optimal_session", task_id=task_id)
        
        try:
            # Get user's patterns
            patterns_result = self.get_productivity_patterns(days=30)
            if not patterns_result.success:
                # Provide default suggestion
                suggestion = self._get_default_session_suggestion()
            else:
                patterns = patterns_result.data
                suggestion = self._generate_session_suggestion(patterns, task_id)
            
            return ServiceResult.ok(suggestion)
            
        except Exception as e:
            return self.handle_database_error("suggest_optimal_session", e)
    
    def update_session_ratings(self, session_id: int, ratings: Dict[str, int]) -> ServiceResult[bool]:
        """
        Update session ratings (focus, energy, mood).
        
        Args:
            session_id: Session ID
            ratings: Dictionary with rating values
            
        Returns:
            ServiceResult with success status
        """
        self.log_operation("update_session_ratings", session_id=session_id, ratings=ratings)
        
        # Validate ratings
        validation_errors = self.validate_business_rules(ratings)
        if validation_errors:
            return ServiceResult.fail_multiple(validation_errors)
        
        try:
            success = self.repository.update_session(session_id, ratings)
            
            if success:
                self.log_operation("update_session_ratings_success", session_id=session_id)
                return ServiceResult.ok(True)
            else:
                return ServiceResult.business_rule_violation("Failed to update session ratings")
                
        except Exception as e:
            return self.handle_database_error("update_session_ratings", e)
    
    # Private helper methods
    
    def _calculate_elapsed_time(self, session: Dict[str, Any]) -> int:
        """Calculate elapsed time for active session."""
        start_time = session['start_time']
        was_utc_format = False
        
        if isinstance(start_time, str):
            # Normaliza ISO 8601 com sufixo 'Z' (UTC) para compatibilidade com fromisoformat
            was_utc_format = start_time.endswith('Z')
            iso_str = start_time.replace('Z', '+00:00') if was_utc_format else start_time
            start_time = datetime.fromisoformat(iso_str)
            # Convert to naive datetime to avoid timezone mixing issues
            if start_time.tzinfo is not None:
                start_time = start_time.replace(tzinfo=None)
        
        # Always use local naive datetime for compatibility
        elapsed = datetime.now() - start_time
        return int(elapsed.total_seconds() / 60)
    
    def _calculate_remaining_time(self, session: Dict[str, Any]) -> int:
        """Calculate remaining time for session."""
        planned_duration = session.get('planned_duration_minutes', 0)
        elapsed = self._calculate_elapsed_time(session)
        
        return max(0, planned_duration - elapsed)
    
    def _calculate_progress_percentage(self, session: Dict[str, Any]) -> float:
        """Calculate progress percentage for session."""
        planned_duration = session.get('planned_duration_minutes', 0)
        if planned_duration <= 0:
            return 0.0
        
        elapsed = self._calculate_elapsed_time(session)
        return min(100.0, (elapsed / planned_duration) * 100)
    
    def _format_duration(self, minutes: float) -> str:
        """Format duration in minutes to human-readable string."""
        if minutes is None:
            return "0 minutes"
        
        hours = int(minutes // 60)
        remaining_minutes = int(minutes % 60)
        
        if hours > 0:
            return f"{hours}h {remaining_minutes}m"
        else:
            return f"{remaining_minutes}m"
    
    def _compare_planned_vs_actual(self, planned: int, actual: int) -> Dict[str, Any]:
        """Compare planned vs actual duration."""
        if planned <= 0:
            return {'variance': None, 'accuracy': 'No plan'}
        
        variance = actual - planned
        variance_percentage = (variance / planned) * 100
        
        if abs(variance_percentage) <= 10:
            accuracy = "Excellent"
        elif abs(variance_percentage) <= 25:
            accuracy = "Good"
        elif abs(variance_percentage) <= 50:
            accuracy = "Fair"
        else:
            accuracy = "Needs improvement"
        
        return {
            'planned_minutes': planned,
            'actual_minutes': actual,
            'variance_minutes': variance,
            'variance_percentage': round(variance_percentage, 1),
            'accuracy': accuracy
        }
    
    def _calculate_performance_metrics(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics for session."""
        metrics = {}
        
        # Focus score
        focus_rating = session.get('focus_rating')
        if focus_rating:
            metrics['focus_score'] = f"{focus_rating}/10"
        
        # Energy level
        energy_level = session.get('energy_level')
        if energy_level:
            metrics['energy_level'] = f"{energy_level}/10"
        
        # Mood rating
        mood_rating = session.get('mood_rating')
        if mood_rating:
            metrics['mood_rating'] = f"{mood_rating}/10"
        
        # Interruption rate
        interruptions = session.get('interruption_count', 0)
        duration = session.get('duration_minutes', 0)
        if duration > 0:
            interruption_rate = interruptions / (duration / 60)  # per hour
            metrics['interruption_rate'] = f"{interruption_rate:.1f}/hour"
        
        return metrics
    
    def _generate_session_recommendations(self, session: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on session performance."""
        recommendations = []
        
        focus_rating = session.get('focus_rating', 0)
        energy_level = session.get('energy_level', 0)
        interruptions = session.get('interruption_count', 0)
        
        if focus_rating and focus_rating < 6:
            recommendations.append("Consider reducing distractions for better focus")
        
        if energy_level and energy_level < 5:
            recommendations.append("Take a break or adjust your schedule for higher energy periods")
        
        if interruptions > 3:
            recommendations.append("Try to minimize interruptions by setting boundaries")
        
        if not recommendations:
            recommendations.append("Great session! Keep up the good work")
        
        return recommendations
    
    def _calculate_productivity_score(self, stats: Dict[str, Any]) -> float:
        """Calculate overall productivity score."""
        if not stats:
            return 0.0
        
        # Factors: session count, average duration, focus rating, low interruptions
        session_count = stats.get('total_sessions', 0)
        avg_duration = stats.get('avg_duration', 0) or 0
        avg_focus = stats.get('avg_focus_rating', 0) or 0
        avg_interruptions = stats.get('avg_interruptions_per_session', 0) or 0
        
        # Normalize and weight factors
        session_score = min(10, session_count / 3)  # 3+ sessions per month = 10
        duration_score = min(10, avg_duration / 30)  # 30+ min avg = 10
        focus_score = avg_focus
        interruption_score = max(0, 10 - avg_interruptions)  # fewer interruptions = higher score
        
        # Weighted average
        productivity_score = (
            session_score * 0.2 + 
            duration_score * 0.3 + 
            focus_score * 0.3 + 
            interruption_score * 0.2
        )
        
        return round(productivity_score, 2)
    
    def _calculate_focus_consistency(self, stats: Dict[str, Any]) -> str:
        """Calculate focus consistency rating."""
        avg_focus = stats.get('avg_focus_rating', 0) or 0
        
        if avg_focus >= 8:
            return "Excellent"
        elif avg_focus >= 6:
            return "Good"
        elif avg_focus >= 4:
            return "Fair"
        else:
            return "Needs improvement"
    
    def _find_peak_hour(self, hourly_patterns: List[Dict[str, Any]]) -> Optional[int]:
        """Find peak productivity hour."""
        if not hourly_patterns:
            return None
        
        peak_hour_data = max(hourly_patterns, key=lambda x: x.get('total_minutes', 0))
        return peak_hour_data.get('hour_of_day')
    
    def _find_best_day(self, daily_patterns: List[Dict[str, Any]]) -> Optional[str]:
        """Find most productive day of week."""
        if not daily_patterns:
            return None
        
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        best_day_data = max(daily_patterns, key=lambda x: x.get('total_minutes', 0))
        day_index = best_day_data.get('day_of_week', 0)
        
        return day_names[day_index] if 0 <= day_index < 7 else None
    
    def _find_preferred_type(self, type_distribution: List[Dict[str, Any]]) -> Optional[str]:
        """Find preferred session type."""
        if not type_distribution:
            return None
        
        preferred_type_data = max(type_distribution, key=lambda x: x.get('session_count', 0))
        return preferred_type_data.get('session_type')
    
    def _analyze_focus_trends(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze focus trends from patterns."""
        hourly_patterns = patterns.get('hourly_patterns', [])
        
        if not hourly_patterns:
            return {'trend': 'insufficient_data'}
        
        # Find hours with highest focus
        focus_hours = sorted(hourly_patterns, key=lambda x: x.get('avg_focus', 0), reverse=True)
        top_focus_hours = focus_hours[:3]
        
        return {
            'trend': 'analyzed',
            'best_focus_hours': [h.get('hour_of_day') for h in top_focus_hours],
            'avg_peak_focus': sum(h.get('avg_focus', 0) for h in top_focus_hours) / len(top_focus_hours)
        }
    
    def _generate_pattern_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on patterns."""
        recommendations = []
        
        # Analyze patterns and provide suggestions
        analysis = patterns.get('analysis', {})
        
        peak_hour = analysis.get('peak_productivity_hour')
        if peak_hour is not None:
            recommendations.append(f"Schedule important work around {peak_hour}:00 for peak productivity")
        
        best_day = analysis.get('best_day_of_week')
        if best_day:
            recommendations.append(f"Plan challenging tasks for {best_day}s")
        
        preferred_type = analysis.get('preferred_session_type')
        if preferred_type and preferred_type != 'focus':
            recommendations.append(f"Consider more {preferred_type} sessions based on your preferences")
        
        return recommendations
    
    def _get_default_session_suggestion(self) -> Dict[str, Any]:
        """Get default session suggestion when no patterns available."""
        return {
            'suggested_duration': 25,
            'suggested_type': SessionType.FOCUS.value,
            'rationale': 'Standard Pomodoro technique (25 minutes)',
            'tips': [
                'Start with shorter sessions and gradually increase',
                'Take 5-minute breaks between sessions',
                'Eliminate distractions before starting'
            ]
        }
    
    def _generate_session_suggestion(self, patterns: Dict[str, Any], task_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate session suggestion based on patterns."""
        analysis = patterns.get('analysis', {})
        
        # Base suggestion on patterns
        preferred_type = analysis.get('preferred_session_type', SessionType.FOCUS.value)
        
        # Calculate suggested duration based on historical data
        hourly_patterns = patterns.get('hourly_patterns', [])
        if hourly_patterns:
            avg_duration = sum(h.get('total_minutes', 0) for h in hourly_patterns) / len(hourly_patterns)
            suggested_duration = min(60, max(15, int(avg_duration)))
        else:
            suggested_duration = 25
        
        # Current hour recommendations
        current_hour = datetime.now().hour
        peak_hour = analysis.get('peak_productivity_hour')
        
        tips = []
        if peak_hour is not None:
            if abs(current_hour - peak_hour) <= 1:
                tips.append("Perfect timing! This is your peak productivity hour")
            else:
                tips.append(f"Consider scheduling sessions around {peak_hour}:00 for better focus")
        
        return {
            'suggested_duration': suggested_duration,
            'suggested_type': preferred_type,
            'rationale': f'Based on your productivity patterns over the last 30 days',
            'tips': tips or ['Stay consistent with your session routine']
        }