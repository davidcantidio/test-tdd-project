-- Rollback 004: Remove missing columns added to framework_epics
-- Date: 2025-08-18

-- Remove points_value column
ALTER TABLE framework_epics DROP COLUMN points_value;

-- Remove due_date column
ALTER TABLE framework_epics DROP COLUMN due_date;

-- Remove icon column
ALTER TABLE framework_epics DROP COLUMN icon;

-- Drop related indexes
DROP INDEX IF EXISTS idx_epics_due_date;
DROP INDEX IF EXISTS idx_epics_points_value;