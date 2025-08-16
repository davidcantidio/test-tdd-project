-- Rollback for Migration 002: Remove enhanced columns from framework_epics
-- This rollback removes the added columns from framework_epics table

ALTER TABLE framework_epics DROP COLUMN deleted_at;
ALTER TABLE framework_epics DROP COLUMN version;
ALTER TABLE framework_epics DROP COLUMN updated_by;
ALTER TABLE framework_epics DROP COLUMN created_by;