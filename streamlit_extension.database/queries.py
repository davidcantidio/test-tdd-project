# Auto-gerado por tools/refactor_split_db.py — NÃO EDITAR À MÃO
from __future__ import annotations

def get_epics(manager, page: int=1, page_size: int=50, status_filter: Optional[Union[EpicStatus, str]]=None, project_id: Optional[int]=None) -> Dict[str, Any]:
    """Get epics with intelligent caching and pagination.
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            status_filter: Filter by specific status
            project_id: Filter by specific project ID
            
        Returns:
            Dictionary with 'data' (list of epics), 'total', 'page', 'total_pages'
        """
    try:
        with manager.get_connection('framework') as conn:
            where_conditions = ['deleted_at IS NULL']
            params: Dict[str, Any] = {}
            if status_filter:
                where_conditions.append(f'{FieldNames.STATUS} = :status_filter')
                params['status_filter'] = status_filter.value if isinstance(status_filter, EpicStatus) else status_filter
            if project_id:
                where_conditions.append('project_id = :project_id')
                params['project_id'] = project_id
            where_clause = ' AND '.join(where_conditions)
            count_query = f'SELECT COUNT(*) FROM {TableNames.EPICS} WHERE {where_clause}'
            if SQLALCHEMY_AVAILABLE:
                count_result = conn.execute(text(count_query), params)
                total = count_result.scalar()
            else:
                cursor = conn.cursor()
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
            total_pages = (total + page_size - 1) // page_size
            offset = (page - 1) * page_size
            data_query = f'\n                    SELECT id, epic_key, name, description, status, \n                           created_at, updated_at, completed_at,\n                           points_earned, difficulty_level, project_id\n                    FROM {TableNames.EPICS}\n                    WHERE {where_clause}\n                    ORDER BY created_at DESC\n                    LIMIT :limit OFFSET :offset\n                '
            params['limit'] = page_size
            params['offset'] = offset
            if SQLALCHEMY_AVAILABLE:
                result = conn.execute(text(data_query), params)
                data = [dict(row._mapping) for row in result]
            else:
                cursor = conn.cursor()
                cursor.execute(data_query, params)
                data = [dict(row) for row in cursor.fetchall()]
            return {'data': data, 'total': total, 'page': page, 'page_size': page_size, 'total_pages': total_pages}
    except Exception as e:
        print(f'Error loading epics: {e}')
        return {'data': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}

def get_all_epics(manager) -> List[Dict[str, Any]]:
    """Backward compatibility method - get all epics without pagination."""
    result = manager.get_epics(page=1, page_size=1000)
    return result['data'] if isinstance(result, dict) else result

def get_tasks(manager, epic_id: Optional[int]=None, page: int=1, page_size: int=100, status_filter: Optional[Union[TaskStatus, str]]=None, tdd_phase_filter: Optional[Union[TDDPhase, str]]=None) -> Dict[str, Any]:
    """Get tasks with intelligent caching, pagination, and filtering.
        
        Args:
            epic_id: Filter by specific epic ID
            page: Page number (1-based)
            page_size: Number of items per page
            status_filter: Filter by specific status
            tdd_phase_filter: Filter by TDD phase
            
        Returns:
            Dictionary with 'data' (list of tasks), 'total', 'page', 'total_pages'
        """
    try:
        with manager.get_connection('framework') as conn:
            where_conditions = ['1=1']
            params: Dict[str, Any] = {}
            if epic_id:
                where_conditions.append('t.epic_id = :epic_id')
                params['epic_id'] = epic_id
            if status_filter:
                where_conditions.append('t.status = :status_filter')
                params['status_filter'] = status_filter.value if isinstance(status_filter, TaskStatus) else status_filter
            if tdd_phase_filter:
                where_conditions.append('t.tdd_phase = :tdd_phase_filter')
                params['tdd_phase_filter'] = tdd_phase_filter.value if isinstance(tdd_phase_filter, TDDPhase) else tdd_phase_filter
            where_clause = ' AND '.join(where_conditions)
            count_query = f'\n                    SELECT COUNT(*)\n                    FROM {TableNames.TASKS} t\n                    JOIN {TableNames.EPICS} e ON t.epic_id = e.id\n                    WHERE {where_clause}\n                '
            if SQLALCHEMY_AVAILABLE:
                count_result = conn.execute(text(count_query), params)
                total = count_result.scalar()
            else:
                cursor = conn.cursor()
                cursor.execute(count_query, list(params.values()))
                total = cursor.fetchone()[0]
            total_pages = (total + page_size - 1) // page_size
            offset = (page - 1) * page_size
            data_query = f'\n                    SELECT t.id, t.epic_id, t.title, t.description, t.status,\n                           t.estimate_minutes, t.tdd_phase, t.position,\n                           t.created_at, t.updated_at, t.completed_at,\n                           e.name as epic_name, e.epic_key, t.task_key\n                    FROM {TableNames.TASKS} t\n                    JOIN {TableNames.EPICS} e ON t.epic_id = e.id\n                    WHERE {where_clause}\n                    ORDER BY t.position ASC, t.created_at DESC\n                    LIMIT :limit OFFSET :offset\n                '
            params['limit'] = page_size
            params['offset'] = offset
            if SQLALCHEMY_AVAILABLE:
                result = conn.execute(text(data_query), params)
                data = [dict(row._mapping) for row in result]
            else:
                cursor = conn.cursor()
                cursor.execute(data_query, list(params.values()))
                data = [dict(row) for row in cursor.fetchall()]
            return {'data': data, 'total': total, 'page': page, 'page_size': page_size, 'total_pages': total_pages}
    except Exception as e:
        logger.error(f'Error loading tasks: {e}')
        if STREAMLIT_AVAILABLE and st:
            st.error(f'❌ Error loading tasks: {e}')
        print(f'Error loading tasks: {e}')
        return {'data': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}

def get_all_tasks(manager, epic_id: Optional[int]=None) -> List[Dict[str, Any]]:
    """Backward compatibility method - get all tasks without pagination."""
    result = manager.get_tasks(epic_id=epic_id, page=1, page_size=1000)
    return result['data'] if isinstance(result, dict) else result

def get_timer_sessions(manager, days: int=30) -> List[Dict[str, Any]]:
    """Get recent timer sessions with short-term caching."""
    if not manager.timer_db_path.exists():
        return []
    try:
        with manager.get_connection('timer') as conn:
            query = "\n                    SELECT task_reference, user_identifier, started_at, ended_at,\n                           planned_duration_minutes, actual_duration_minutes,\n                           focus_rating, energy_level, mood_rating,\n                           interruptions_count,\n                           created_at\n                    FROM timer_sessions\n                    WHERE created_at >= DATE('now', ? || ' days')\n                    ORDER BY created_at DESC\n                    LIMIT 1000\n                "
            if SQLALCHEMY_AVAILABLE:
                result = conn.execute(text(query), [f'-{days}'])
                return [dict(row._mapping) for row in result]
            else:
                cursor = conn.cursor()
                cursor.execute(query, [f'-{days}'])
                return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f'Error loading timer sessions: {e}')
        return []

def get_user_stats(manager, user_id: int=1) -> Dict[str, Any]:
    """Get user statistics and gamification data."""
    try:
        with manager.get_connection('framework') as conn:
            stats = {}
            if SQLALCHEMY_AVAILABLE:
                result = conn.execute(text("\n                        SELECT COUNT(*) as completed_tasks\n                        FROM framework_tasks\n                        WHERE status = 'completed' AND deleted_at IS NULL\n                    "))
                stats['completed_tasks'] = result.scalar() or 0
                result = conn.execute(text('\n                        SELECT COALESCE(SUM(points_earned), 0) as total_points\n                        FROM framework_epics WHERE deleted_at IS NULL\n                    '))
                stats['total_points'] = result.scalar() or 0
                result = conn.execute(text('\n                        SELECT COUNT(*) as active_streaks\n                        FROM user_streaks\n                        WHERE user_id = ? AND current_count > 0\n                    '), [user_id])
                stats['active_streaks'] = result.scalar() or 0
            else:
                cursor = conn.cursor()
                cursor.execute("\n                        SELECT COUNT(*) FROM framework_tasks\n                        WHERE status = 'completed' AND deleted_at IS NULL\n                    ")
                row = cursor.fetchone()
                stats['completed_tasks'] = row[0] if row and row[0] is not None else 0
                cursor.execute('\n                        SELECT COALESCE(SUM(points_earned), 0)\n                        FROM framework_epics WHERE deleted_at IS NULL\n                    ')
                row = cursor.fetchone()
                stats['total_points'] = row[0] if row and row[0] is not None else 0
                cursor.execute('\n                        SELECT COUNT(*) FROM user_streaks\n                        WHERE user_id = ? AND current_count > 0\n                    ', [user_id])
                row = cursor.fetchone()
                stats['active_streaks'] = row[0] if row and row[0] is not None else 0
            return stats
    except Exception as e:
        print(f'Error loading user stats: {e}')
        return {'completed_tasks': 0, 'total_points': 0, 'active_streaks': 0}

def get_achievements(manager, user_id: int=1) -> List[Dict[str, Any]]:
    """Get user achievements."""
    try:
        with manager.get_connection('framework') as conn:
            query = '\n                    SELECT at.code, at.name, at.description, at.category,\n                           at.points_reward, at.rarity, ua.unlocked_at\n                    FROM user_achievements ua\n                    JOIN achievement_types at ON ua.achievement_code = at.code\n                    WHERE ua.user_id = ?\n                    ORDER BY ua.unlocked_at DESC\n                '
            if SQLALCHEMY_AVAILABLE:
                result = conn.execute(text(query), [user_id])
                return [dict(row._mapping) for row in result]
            else:
                cursor = conn.cursor()
                cursor.execute(query, [user_id])
                return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f'Error loading achievements: {e}')
        return []

def get_epics_with_hierarchy(manager, project_id: Optional[int]=None, client_id: Optional[int]=None, page: int=1, page_size: int=25, status_filter: str='') -> Dict[str, Any]:
    """Get epics with complete hierarchy information (client → project → epic) with pagination.
        
        Args:
            project_id: Filter by specific project ID (optional)
            client_id: Filter by specific client ID (optional)
            page: Page number (1-based)
            page_size: Number of items per page
            status_filter: Filter by epic status
            
        Returns:
            Dictionary with 'data' (list of epics), 'total', 'page', 'total_pages'
        """
    try:
        with manager.get_connection('framework') as conn:
            where_conditions = ['e.deleted_at IS NULL']
            params: Dict[str, Any] = {}
            if project_id:
                where_conditions.append('e.project_id = :project_id')
                params['project_id'] = project_id
            elif client_id:
                where_conditions.append('p.client_id = :client_id')
                params['client_id'] = client_id
            if status_filter:
                where_conditions.append('e.status = :status_filter')
                params['status_filter'] = status_filter
            where_clause = ' AND '.join(where_conditions)
            count_query = f'\n                    SELECT COUNT(*) \n                    FROM framework_epics e\n                    LEFT JOIN framework_projects p ON e.project_id = p.id AND p.deleted_at IS NULL\n                    LEFT JOIN framework_clients c ON p.client_id = c.id AND c.deleted_at IS NULL\n                    WHERE {where_clause}\n                '
            if SQLALCHEMY_AVAILABLE:
                count_result = conn.execute(text(count_query), params)
                total = count_result.scalar()
            else:
                cursor = conn.cursor()
                cursor.execute(count_query, list(params.values()))
                total = cursor.fetchone()[0]
            total_pages = (total + page_size - 1) // page_size
            offset = (page - 1) * page_size
            data_query = f'\n                    SELECT e.id, e.epic_key, e.name, e.description, e.summary,\n                           e.status, e.priority, e.duration_days,\n                           e.points_earned, e.difficulty_level,\n                           e.planned_start_date, e.planned_end_date,\n                           e.actual_start_date, e.actual_end_date,\n                           e.calculated_duration_days, e.duration_description,\n                           e.created_at, e.updated_at, e.completed_at,\n                           e.project_id,\n                           p.name as project_name, p.project_key, p.status as project_status,\n                           p.health_status as project_health, p.client_id,\n                           c.name as client_name, c.client_key, c.status as client_status,\n                           c.client_tier, c.hourly_rate as client_hourly_rate\n                    FROM framework_epics e\n                    LEFT JOIN framework_projects p ON e.project_id = p.id AND p.deleted_at IS NULL\n                    LEFT JOIN framework_clients c ON p.client_id = c.id AND c.deleted_at IS NULL\n                    WHERE {where_clause}\n                    ORDER BY c.priority_level DESC, p.priority DESC, e.created_at DESC\n                    LIMIT :limit OFFSET :offset\n                '
            params['limit'] = page_size
            params['offset'] = offset
            if SQLALCHEMY_AVAILABLE:
                result = conn.execute(text(data_query), params)
                data = [dict(row._mapping) for row in result]
            else:
                cursor = conn.cursor()
                cursor.execute(data_query, list(params.values()))
                data = [dict(row) for row in cursor.fetchall()]
            return {'data': data, 'total': total, 'page': page, 'page_size': page_size, 'total_pages': total_pages}
    except Exception as e:
        logger.error(f'Error loading epics with hierarchy: {e}')
        if STREAMLIT_AVAILABLE and st:
            st.error(f'❌ Error loading epics with hierarchy: {e}')
        return {'data': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}

def get_all_epics_with_hierarchy(manager, project_id: Optional[int]=None, client_id: Optional[int]=None) -> List[Dict[str, Any]]:
    """Backward compatibility method - get all epics with hierarchy without pagination."""
    result = manager.get_epics_with_hierarchy(project_id=project_id, client_id=client_id, page=1, page_size=1000)
    return result['data'] if isinstance(result, dict) else result

def get_hierarchy_overview(manager, client_id: Optional[int]=None) -> List[Dict[str, Any]]:
    """Get complete hierarchy overview using the database view.
        
        Args:
            client_id: Filter by specific client ID (optional)
            
        Returns:
            List of hierarchy records with aggregated task counts
        """
    try:
        with manager.get_connection('framework') as conn:
            query = '\n                    SELECT client_id, client_key, client_name, client_status, client_tier,\n                           project_id, project_key, project_name, project_status, project_health,\n                           project_completion, epic_id, epic_key, epic_name, epic_status,\n                           calculated_duration_days, total_tasks, completed_tasks,\n                           epic_completion_percentage, planned_start_date, planned_end_date,\n                           epic_planned_start, epic_planned_end\n                    FROM hierarchy_overview\n                    WHERE 1=1\n                '
            params = []
            if client_id:
                query += ' AND client_id = ?'
                params.append(client_id)
            query += ' ORDER BY client_name, project_name, epic_key'
            if SQLALCHEMY_AVAILABLE:
                result = conn.execute(text(query), params)
                return [dict(row._mapping) for row in result]
            else:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f'Error loading hierarchy overview: {e}')
        return []

def get_client_dashboard(manager, client_id: Optional[int]=None) -> List[Dict[str, Any]]:
    """Get client dashboard data using the database view.
        
        Args:
            client_id: Get data for specific client (optional)
            
        Returns:
            List of client dashboard records with aggregated metrics
        """
    try:
        with manager.get_connection('framework') as conn:
            query = '\n                    SELECT client_id, client_key, client_name, client_status, client_tier,\n                           hourly_rate, total_projects, active_projects, completed_projects,\n                           total_epics, active_epics, completed_epics,\n                           total_tasks, completed_tasks, in_progress_tasks,\n                           total_hours_logged, total_budget, total_points_earned,\n                           earliest_project_start, latest_project_end,\n                           projects_at_risk, avg_project_completion\n                    FROM client_dashboard\n                    WHERE 1=1\n                '
            params = []
            if client_id:
                query += ' AND client_id = ?'
                params.append(client_id)
            query += ' ORDER BY client_name'
            if SQLALCHEMY_AVAILABLE:
                result = conn.execute(text(query), params)
                return [dict(row._mapping) for row in result]
            else:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f'Error loading client dashboard: {e}')
        return []

def get_project_dashboard(manager, project_id: Optional[int]=None, client_id: Optional[int]=None) -> List[Dict[str, Any]]:
    """Get project dashboard data using the database view.
        
        Args:
            project_id: Get data for specific project (optional)
            client_id: Get data for projects of specific client (optional)
            
        Returns:
            List of project dashboard records with aggregated metrics
        """
    try:
        with manager.get_connection('framework') as conn:
            query = '\n                    SELECT project_id, project_key, project_name, project_status, health_status,\n                           completion_percentage, client_id, client_name, client_tier,\n                           total_epics, completed_epics, active_epics,\n                           total_tasks, completed_tasks, in_progress_tasks,\n                           estimated_hours, actual_hours, estimated_task_hours, actual_task_hours,\n                           budget_amount, hourly_rate, planned_start_date, planned_end_date,\n                           actual_start_date, actual_end_date, calculated_completion_percentage,\n                           total_points_earned, complexity_score, quality_score\n                    FROM project_dashboard\n                    WHERE 1=1\n                '
            params = []
            if project_id:
                query += ' AND project_id = ?'
                params.append(project_id)
            elif client_id:
                query += ' AND client_id = ?'
                params.append(client_id)
            query += ' ORDER BY client_name, project_name'
            if SQLALCHEMY_AVAILABLE:
                result = conn.execute(text(query), params)
                return [dict(row._mapping) for row in result]
            else:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f'Error loading project dashboard: {e}')
        return []

def create_client(manager, client_key: str, name: str, description: str='', industry: str='', company_size: str='startup', primary_contact_name: str='', primary_contact_email: str='', hourly_rate: float=0.0, **kwargs: Any) -> Optional[int]:
    """Create new client record.

        Creates client with full validation and automatic timestamp assignment.
        Invalidates related caches and triggers audit logging.

        Args:
            client_key: Unique client identifier string (3-20 chars).
            name: Client display name (1-100 characters).
            description: Client description (max 500 chars).
            industry: Industry classification.
            company_size: Company size category.
            primary_contact_name: Primary contact name.
            primary_contact_email: Primary contact email.
            hourly_rate: Billing rate per hour.
            **kwargs: Additional optional fields like ``status`` or
                ``client_tier``.

        Returns:
            Optional[int]: New client ID if successful, ``None`` if failed.

        Raises:
            ValueError: If required fields are missing or invalid.
            IntegrityError: If ``client_key`` already exists.
            DatabaseError: If insert operation fails.

        Side Effects:
            - Invalidates client list caches.
            - Creates audit log entry.

        Performance:
            - Insert operation: ~5ms.

        Example:
            >>> client_id = db_manager.create_client(
            ...     client_key="acme_corp", name="ACME Corporation"
            ... )
        """
    try:
        client_data = {'client_key': client_key, 'name': name, 'description': description, 'industry': industry, 'company_size': company_size, 'primary_contact_name': primary_contact_name, 'primary_contact_email': primary_contact_email, 'hourly_rate': hourly_rate, 'status': kwargs.get('status', ClientStatus.ACTIVE.value), 'client_tier': kwargs.get('client_tier', 'standard'), 'priority_level': kwargs.get('priority_level', 5), 'timezone': kwargs.get('timezone', 'America/Sao_Paulo'), 'currency': kwargs.get('currency', 'BRL'), 'preferred_language': kwargs.get('preferred_language', 'pt-BR'), 'contract_type': kwargs.get('contract_type', 'time_and_materials'), 'created_by': kwargs.get('created_by', 1)}
        with manager.get_connection('framework') as conn:
            placeholders = ', '.join(['?' for _ in client_data])
            columns = ', '.join(client_data.keys())
            if SQLALCHEMY_AVAILABLE:
                named_placeholders = ', '.join([f':{key}' for key in client_data.keys()])
                result = conn.execute(text(f'INSERT INTO {TableNames.CLIENTS} ({columns}) VALUES ({named_placeholders})'), client_data)
                conn.commit()
                return result.lastrowid
            else:
                cursor = conn.cursor()
                cursor.execute(f'INSERT INTO {TableNames.CLIENTS} ({columns}) VALUES ({placeholders})', list(client_data.values()))
                conn.commit()
                return cursor.lastrowid
    except Exception as e:
        logger.error(f'Error creating client: {e}')
        if STREAMLIT_AVAILABLE and st:
            st.error(f'❌ Error creating client: {e}')
        return None

def create_project(manager, client_id: int, project_key: str, name: str, description: str='', project_type: str='development', methodology: str='agile', **kwargs: Any) -> Optional[int]:
    """Create a new project.
        
        Args:
            client_id: ID of the client who owns this project
            project_key: Unique project identifier within client
            name: Project name
            description: Project description
            project_type: Type of project (development, maintenance, etc.)
            methodology: Development methodology (agile, waterfall, etc.)
            **kwargs: Additional project fields
            
        Returns:
            Project ID if successful, None otherwise
        """
    try:
        project_data = {'client_id': client_id, 'project_key': project_key, 'name': name, 'description': description, 'project_type': project_type, 'methodology': methodology, 'status': kwargs.get('status', ProjectStatus.PLANNING.value), 'priority': kwargs.get('priority', 5), 'health_status': kwargs.get('health_status', 'green'), 'completion_percentage': kwargs.get('completion_percentage', 0), 'planned_start_date': kwargs.get('planned_start_date'), 'planned_end_date': kwargs.get('planned_end_date'), 'estimated_hours': kwargs.get('estimated_hours', 0), 'budget_amount': kwargs.get('budget_amount', 0), 'budget_currency': kwargs.get('budget_currency', 'BRL'), 'hourly_rate': kwargs.get('hourly_rate'), 'project_manager_id': kwargs.get('project_manager_id', 1), 'technical_lead_id': kwargs.get('technical_lead_id', 1), 'repository_url': kwargs.get('repository_url', ''), 'visibility': kwargs.get('visibility', 'client'), 'access_level': kwargs.get('access_level', 'standard'), 'complexity_score': kwargs.get('complexity_score', 5.0), 'quality_score': kwargs.get('quality_score', 8.0), 'created_by': kwargs.get('created_by', 1)}
        with manager.get_connection('framework') as conn:
            project_data = {k: v for k, v in project_data.items() if v is not None}
            placeholders = ', '.join(['?' for _ in project_data])
            columns = ', '.join(project_data.keys())
            if SQLALCHEMY_AVAILABLE:
                named_placeholders = ', '.join([f':{key}' for key in project_data.keys()])
                result = conn.execute(text(f'INSERT INTO {TableNames.PROJECTS} ({columns}) VALUES ({named_placeholders})'), project_data)
                conn.commit()
                return result.lastrowid
            else:
                cursor = conn.cursor()
                cursor.execute(f'INSERT INTO {TableNames.PROJECTS} ({columns}) VALUES ({placeholders})', list(project_data.values()))
                conn.commit()
                return cursor.lastrowid
    except Exception as e:
        logger.error(f'Error creating project: {e}')
        if STREAMLIT_AVAILABLE and st:
            st.error(f'❌ Error creating project: {e}')
        return None

def update_epic_project(manager, epic_id: int, project_id: int) -> bool:
    """Update the project assignment for an epic.
        
        Args:
            epic_id: ID of the epic to update
            project_id: ID of the new project
            
        Returns:
            True if successful, False otherwise
        """
    try:
        with manager.get_connection('framework') as conn:
            if SQLALCHEMY_AVAILABLE:
                conn.execute(text('\n                        UPDATE framework_epics \n                        SET project_id = :project_id, updated_at = CURRENT_TIMESTAMP\n                        WHERE id = :epic_id\n                    '), {'project_id': project_id, 'epic_id': epic_id})
                conn.commit()
            else:
                cursor = conn.cursor()
                cursor.execute('\n                        UPDATE framework_epics \n                        SET project_id = ?, updated_at = CURRENT_TIMESTAMP\n                        WHERE id = ?\n                    ', (project_id, epic_id))
                conn.commit()
            return True
    except Exception as e:
        logger.error(f'Error updating epic project: {e}')
        return False

def get_client_by_key(manager, client_key: str) -> Optional[Dict[str, Any]]:
    """Get client by client_key.
        
        Args:
            client_key: Client key to search for
            
        Returns:
            Client dictionary if found, None otherwise
        """
    try:
        with manager.get_connection('framework') as conn:
            if SQLALCHEMY_AVAILABLE:
                result = conn.execute(text('\n                        SELECT * FROM framework_clients \n                        WHERE client_key = :client_key AND deleted_at IS NULL\n                    '), {'client_key': client_key})
                row = result.fetchone()
                return dict(row._mapping) if row else None
            else:
                cursor = conn.cursor()
                cursor.execute('\n                        SELECT * FROM framework_clients \n                        WHERE client_key = ? AND deleted_at IS NULL\n                    ', (client_key,))
                row = cursor.fetchone()
                return dict(row) if row else None
    except Exception as e:
        logger.error(f'Error getting client by key: {e}')
        return None

def get_project_by_key(manager, client_id: int, project_key: str) -> Optional[Dict[str, Any]]:
    """Get project by client_id and project_key.
        
        Args:
            client_id: Client ID
            project_key: Project key to search for
            
        Returns:
            Project dictionary if found, None otherwise
        """
    try:
        with manager.get_connection('framework') as conn:
            if SQLALCHEMY_AVAILABLE:
                result = conn.execute(text('\n                        SELECT * FROM framework_projects \n                        WHERE client_id = :client_id AND project_key = :project_key \n                        AND deleted_at IS NULL\n                    '), {'client_id': client_id, 'project_key': project_key})
                row = result.fetchone()
                return dict(row._mapping) if row else None
            else:
                cursor = conn.cursor()
                cursor.execute('\n                        SELECT * FROM framework_projects \n                        WHERE client_id = ? AND project_key = ? AND deleted_at IS NULL\n                    ', (client_id, project_key))
                row = cursor.fetchone()
                return dict(row) if row else None
    except Exception as e:
        logger.error(f'Error getting project by key: {e}')
        return None

def update_client(manager, client_id: int, **fields: Any) -> bool:
    """Update existing client record.

        Updates specified fields while preserving others. Validates all input
        and maintains data integrity. Supports partial updates.

        Args:
            client_id: Client ID to update. Must exist.
            **fields: Fields to update. Same validation as ``create_client``.

        Returns:
            bool: ``True`` if update successful, ``False`` if failed or no
                changes.

        Raises:
            ValueError: If ``client_id`` invalid or field validation fails.
            DatabaseError: If update operation fails.

        Side Effects:
            - Invalidates client caches for this client.
            - Updates ``updated_at`` timestamp.

        Performance:
            - Update operation: ~3ms.

        Example:
            >>> db_manager.update_client(123, name="New Name")
        """
    try:
        if not fields:
            return True
        fields['updated_at'] = 'CURRENT_TIMESTAMP'
        set_clauses = []
        values = {}
        for key, value in fields.items():
            if key == 'updated_at':
                set_clauses.append(f'{key} = CURRENT_TIMESTAMP')
            else:
                set_clauses.append(f'{key} = :{key}')
                values[key] = value
        values['client_id'] = client_id
        with manager.get_connection('framework') as conn:
            if SQLALCHEMY_AVAILABLE:
                conn.execute(text(f'\n                        UPDATE {TableNames.CLIENTS}\n                        SET {', '.join(set_clauses)}\n                        WHERE id = :client_id AND deleted_at IS NULL\n                    '), values)
                conn.commit()
            else:
                cursor = conn.cursor()
                positional_values = [values[key] for key in values.keys() if key != 'client_id']
                positional_values.append(client_id)
                sqlite_clauses = [clause.replace(f':{key}', '?') for clause in set_clauses if f':{key}' in clause]
                sqlite_clauses.extend([clause for clause in set_clauses if '?' not in clause and ':' not in clause])
                cursor.execute(f'\n                        UPDATE {TableNames.CLIENTS}\n                        SET {', '.join(sqlite_clauses)}\n                        WHERE id = ? AND deleted_at IS NULL\n                    ', positional_values)
                conn.commit()
            return True
    except Exception as e:
        logger.error(f'Error updating client: {e}')
        if STREAMLIT_AVAILABLE and st:
            st.error(f'❌ Error updating client: {e}')
        return False

def delete_client(manager, client_id: int, soft_delete: bool=True) -> bool:
    """Delete client record (soft or hard delete).

        Removes client from active use. Soft delete preserves data for audit
        purposes. Hard delete permanently removes all data.

        Args:
            client_id: Client ID to delete. Must exist.
            soft_delete: Use soft delete. Defaults to ``True``.

        Returns:
            bool: ``True`` if deletion successful, ``False`` if failed.

        Raises:
            ValueError: If ``client_id`` invalid.
            DatabaseError: If delete operation fails.

        Side Effects:
            - Invalidates all client-related caches.

        Performance:
            - Soft delete: ~2ms.
            - Hard delete: ~10-100ms (depends on related data).

        Example:
            >>> db_manager.delete_client(123, soft_delete=True)
        """
    try:
        with manager.get_connection('framework') as conn:
            if soft_delete:
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text('\n                            UPDATE {TableNames.CLIENTS}\n                            SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP\n                            WHERE id = :client_id\n                        '), {'client_id': client_id})
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    cursor.execute('\n                            UPDATE {TableNames.CLIENTS}\n                            SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP\n                            WHERE id = ?\n                        ', (client_id,))
                    conn.commit()
            else:
                return manager.delete_cascade_safe(table_name='clients', record_id=client_id, cascade_tables=['projects', 'epics', 'tasks'])
            return True
    except Exception as e:
        logger.error(f'Error deleting client: {e}')
        if STREAMLIT_AVAILABLE and st:
            st.error(f'❌ Error deleting client: {e}')
        return False

def update_project(manager, project_id: int, **fields: Any) -> bool:
    """Update an existing project.
        
        Args:
            project_id: ID of the project to update
            **fields: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
    try:
        if not fields:
            return True
        fields['updated_at'] = 'CURRENT_TIMESTAMP'
        set_clauses = []
        values = {}
        for key, value in fields.items():
            if key == 'updated_at':
                set_clauses.append(f'{key} = CURRENT_TIMESTAMP')
            else:
                set_clauses.append(f'{key} = :{key}')
                values[key] = value
        values['project_id'] = project_id
        with manager.get_connection('framework') as conn:
            if SQLALCHEMY_AVAILABLE:
                conn.execute(text(f'\n                        UPDATE {TableNames.PROJECTS}\n                        SET {', '.join(set_clauses)}\n                        WHERE id = :project_id AND deleted_at IS NULL\n                    '), values)
                conn.commit()
            else:
                cursor = conn.cursor()
                positional_values = [values[key] for key in values.keys() if key != 'project_id']
                positional_values.append(project_id)
                sqlite_clauses = [clause.replace(f':{key}', '?') for clause in set_clauses if f':{key}' in clause]
                sqlite_clauses.extend([clause for clause in set_clauses if '?' not in clause and ':' not in clause])
                cursor.execute(f'\n                        UPDATE {TableNames.PROJECTS}\n                        SET {', '.join(sqlite_clauses)}\n                        WHERE id = ? AND deleted_at IS NULL\n                    ', positional_values)
                conn.commit()
            return True
    except Exception as e:
        logger.error(f'Error updating project: {e}')
        if STREAMLIT_AVAILABLE and st:
            st.error(f'❌ Error updating project: {e}')
        return False

def delete_project(manager, project_id: int, soft_delete: bool=True) -> bool:
    """Delete a project (soft delete by default).
        
        Args:
            project_id: ID of the project to delete
            soft_delete: If True, mark as deleted instead of removing
            
        Returns:
            True if successful, False otherwise
        """
    try:
        with manager.get_connection('framework') as conn:
            if soft_delete:
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text('\n                            UPDATE {TableNames.PROJECTS}\n                            SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP\n                            WHERE id = :project_id\n                        '), {'project_id': project_id})
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    cursor.execute('\n                            UPDATE {TableNames.PROJECTS}\n                            SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP\n                            WHERE id = ?\n                        ', (project_id,))
                    conn.commit()
            else:
                return manager.delete_cascade_safe(table_name='projects', record_id=project_id, cascade_tables=['epics', 'tasks'])
            return True
    except Exception as e:
        logger.error(f'Error deleting project: {e}')
        if STREAMLIT_AVAILABLE and st:
            st.error(f'❌ Error deleting project: {e}')
        return False

