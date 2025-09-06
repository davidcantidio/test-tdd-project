-- ==================================================================================
-- Rollback Migration 011: Remove Priority Settings Table
-- Reverts changes from 011_add_priority_settings.sql
-- Date: 2025-09-06
-- ==================================================================================

-- Drop the trigger first
DROP TRIGGER IF EXISTS trg_priority_settings_updated;

-- Drop the index
DROP INDEX IF EXISTS idx_priority_settings_project;

-- Drop the table
DROP TABLE IF EXISTS framework_priority_settings;

-- NOTE: Migration tracking rollback is managed by MigrationManager (schema_migrations)
