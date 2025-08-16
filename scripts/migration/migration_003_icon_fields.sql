-- Migration 003: Add icon and display fields for better UI
-- Date: 2025-08-16
-- Description: Add icon, color, and display customization fields

-- Add icon field to framework_epics
ALTER TABLE framework_epics ADD COLUMN icon TEXT DEFAULT '📋';

-- Add color field to framework_epics
ALTER TABLE framework_epics ADD COLUMN color TEXT DEFAULT '#3498db';

-- Add icon field to framework_tasks
ALTER TABLE framework_tasks ADD COLUMN icon TEXT DEFAULT '📝';

-- Add priority field to framework_tasks
ALTER TABLE framework_tasks ADD COLUMN priority INTEGER DEFAULT 3;

-- Add status_icon mapping to work_sessions
ALTER TABLE work_sessions ADD COLUMN status_icon TEXT DEFAULT '⏱️';

-- Create indexes for UI performance
CREATE INDEX IF NOT EXISTS idx_epics_icon_color ON framework_epics(icon, color);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON framework_tasks(priority);
