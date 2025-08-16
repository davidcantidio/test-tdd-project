-- Migration 003: Add performance indexes
-- This migration adds indexes to improve query performance

-- Indexes for framework_epics
CREATE INDEX IF NOT EXISTS idx_framework_epics_status ON framework_epics(status);
CREATE INDEX IF NOT EXISTS idx_framework_epics_priority ON framework_epics(priority);
CREATE INDEX IF NOT EXISTS idx_framework_epics_project_id ON framework_epics(project_id);
CREATE INDEX IF NOT EXISTS idx_framework_epics_created_at ON framework_epics(created_at);

-- Indexes for framework_tasks
CREATE INDEX IF NOT EXISTS idx_framework_tasks_epic_id ON framework_tasks(epic_id);
CREATE INDEX IF NOT EXISTS idx_framework_tasks_status ON framework_tasks(status);
CREATE INDEX IF NOT EXISTS idx_framework_tasks_created_at ON framework_tasks(created_at);

-- Indexes for work_sessions
CREATE INDEX IF NOT EXISTS idx_work_sessions_user_id ON work_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_work_sessions_session_id ON work_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_work_sessions_created_at ON work_sessions(created_at);