-- Migration 001: Add points_value column to framework_epics
-- Date: 2025-08-16
-- Description: Add points_value column for epic scoring system

-- Add points_value column if it doesn't exist
ALTER TABLE framework_epics ADD COLUMN points_value INTEGER DEFAULT 0;

-- Update existing epics with default points based on existing data
UPDATE framework_epics 
SET points_value = 10 
WHERE points_value IS NULL OR points_value = 0;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_epics_points_value ON framework_epics(points_value);
