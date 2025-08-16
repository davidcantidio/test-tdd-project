-- Migration 002: Add due_date columns to tasks and epics
-- Date: 2025-08-16
-- Description: Add due date tracking for better project management

-- Add due_date to framework_epics
ALTER TABLE framework_epics ADD COLUMN due_date TEXT;

-- Add due_date to framework_tasks
ALTER TABLE framework_tasks ADD COLUMN due_date TEXT;

-- Add planned_start_date to framework_epics
ALTER TABLE framework_epics ADD COLUMN planned_start_date TEXT;

-- Add planned_end_date to framework_epics
ALTER TABLE framework_epics ADD COLUMN planned_end_date TEXT;

-- Create indexes for date-based queries
CREATE INDEX IF NOT EXISTS idx_epics_due_date ON framework_epics(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON framework_tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_epics_planned_dates ON framework_epics(planned_start_date, planned_end_date);
