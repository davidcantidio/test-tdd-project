-- Rollback for Migration 003: Remove performance indexes
-- This rollback removes all the performance indexes added

-- Remove work_sessions indexes
DROP INDEX IF EXISTS idx_work_sessions_created_at;
DROP INDEX IF EXISTS idx_work_sessions_session_id;
DROP INDEX IF EXISTS idx_work_sessions_user_id;

-- Remove framework_tasks indexes
DROP INDEX IF EXISTS idx_framework_tasks_created_at;
DROP INDEX IF EXISTS idx_framework_tasks_status;
DROP INDEX IF EXISTS idx_framework_tasks_epic_id;

-- Remove framework_epics indexes
DROP INDEX IF EXISTS idx_framework_epics_created_at;
DROP INDEX IF EXISTS idx_framework_epics_project_id;
DROP INDEX IF EXISTS idx_framework_epics_priority;
DROP INDEX IF EXISTS idx_framework_epics_status;