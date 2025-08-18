-- Rollback 005: Remove additional indexes
-- Date: 2025-08-18

-- Drop framework_tasks indexes
DROP INDEX IF EXISTS idx_framework_tasks_epic_id;
DROP INDEX IF EXISTS idx_framework_tasks_status;
DROP INDEX IF EXISTS idx_framework_tasks_tdd_phase;

-- Drop framework_epics indexes
DROP INDEX IF EXISTS idx_framework_epics_status;
DROP INDEX IF EXISTS idx_framework_epics_client_id;
DROP INDEX IF EXISTS idx_framework_epics_project_id;

-- Drop work_sessions indexes
DROP INDEX IF EXISTS idx_work_sessions_user_id;
DROP INDEX IF EXISTS idx_work_sessions_task_id;
DROP INDEX IF EXISTS idx_work_sessions_start_time;