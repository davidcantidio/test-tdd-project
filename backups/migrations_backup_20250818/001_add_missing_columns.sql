-- Migration: Add missing columns identified in report.md
-- Date: 2025-01-15
-- Description: Add points_value, due_date, icon columns to framework_epics table

-- Add points_value column for epic scoring
ALTER TABLE framework_epics 
ADD COLUMN points_value INTEGER DEFAULT 0;

-- Add due_date column for deadline tracking
ALTER TABLE framework_epics 
ADD COLUMN due_date TEXT;

-- Add icon column for visual identification
ALTER TABLE framework_epics 
ADD COLUMN icon TEXT DEFAULT '📋';

-- Update existing records with default values
UPDATE framework_epics 
SET points_value = COALESCE(points_earned, 0)
WHERE points_value IS NULL;

-- Add constraints
CREATE INDEX idx_epics_due_date ON framework_epics(due_date);
CREATE INDEX idx_epics_points_value ON framework_epics(points_value);
