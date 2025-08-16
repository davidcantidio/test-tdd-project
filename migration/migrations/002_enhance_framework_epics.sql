-- Migration 002: Enhance framework_epics table
-- This migration adds missing columns and constraints to framework_epics

-- Add created_by and updated_by columns if they don't exist
ALTER TABLE framework_epics ADD COLUMN created_by TEXT DEFAULT 'system';
ALTER TABLE framework_epics ADD COLUMN updated_by TEXT DEFAULT 'system';
ALTER TABLE framework_epics ADD COLUMN version INTEGER DEFAULT 1;
ALTER TABLE framework_epics ADD COLUMN deleted_at TIMESTAMP NULL;

-- Update existing records to have default values
UPDATE framework_epics 
SET created_by = 'system', updated_by = 'system', version = 1 
WHERE created_by IS NULL OR updated_by IS NULL OR version IS NULL;