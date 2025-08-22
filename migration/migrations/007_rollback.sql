-- Rollback 007: Remove Product Visions and User Stories (Phase 1)
-- Date: 2025-08-22
-- Description: Rollback migration 007 - Remove product_visions and framework_user_stories tables

-- ==================================================================================
-- REMOVE TRIGGERS
-- ==================================================================================
-- Drop triggers in reverse order

DROP TRIGGER IF EXISTS trigger_prevent_circular_user_stories;
DROP TRIGGER IF EXISTS trigger_user_stories_updated_at;
DROP TRIGGER IF EXISTS trigger_product_visions_updated_at;

-- ==================================================================================
-- REMOVE INDEXES
-- ==================================================================================
-- Drop all indexes created by migration 007

-- User Stories indexes
DROP INDEX IF EXISTS idx_user_stories_active;
DROP INDEX IF EXISTS idx_user_stories_dates;
DROP INDEX IF EXISTS idx_user_stories_dependencies;
DROP INDEX IF EXISTS idx_user_stories_story_points;
DROP INDEX IF EXISTS idx_user_stories_assigned;
DROP INDEX IF EXISTS idx_user_stories_priority;
DROP INDEX IF EXISTS idx_user_stories_workflow_stage;
DROP INDEX IF EXISTS idx_user_stories_status;
DROP INDEX IF EXISTS idx_user_stories_epic_id;

-- Product Visions indexes  
DROP INDEX IF EXISTS idx_product_visions_active;
DROP INDEX IF EXISTS idx_product_visions_owner;
DROP INDEX IF EXISTS idx_product_visions_dates;
DROP INDEX IF EXISTS idx_product_visions_priority;
DROP INDEX IF EXISTS idx_product_visions_status;
DROP INDEX IF EXISTS idx_product_visions_project_id;

-- ==================================================================================
-- REMOVE TABLES
-- ==================================================================================
-- Drop tables in dependency order (child tables first)

-- Drop User Stories table (depends on framework_epics)
DROP TABLE IF EXISTS framework_user_stories;

-- Drop Product Visions table (depends on framework_projects)
DROP TABLE IF EXISTS product_visions;

-- ==================================================================================
-- REMOVE ACHIEVEMENT TYPES
-- ==================================================================================
-- Remove achievement types added by migration 007

DELETE FROM achievement_types 
WHERE code IN ('VISION_CREATOR', 'STORY_MASTER', 'ACCEPTANCE_GURU');

-- ==================================================================================
-- SCHEMA VERSION CLEANUP
-- ==================================================================================
-- Remove this migration from schema_migrations table (if it exists)

-- Note: This will be handled by the migration runner
-- DELETE FROM schema_migrations WHERE version = '007';

-- ==================================================================================
-- ROLLBACK VERIFICATION
-- ==================================================================================
-- Verify that all objects have been removed

-- Tables should not exist after rollback:
-- - product_visions
-- - framework_user_stories

-- Indexes should not exist after rollback:
-- - All idx_product_visions_* indexes
-- - All idx_user_stories_* indexes

-- Triggers should not exist after rollback:
-- - trigger_product_visions_updated_at
-- - trigger_user_stories_updated_at  
-- - trigger_prevent_circular_user_stories

-- Achievement types should be removed:
-- - VISION_CREATOR, STORY_MASTER, ACCEPTANCE_GURU

-- ==================================================================================
-- ROLLBACK COMPLETE
-- ==================================================================================
-- Migration 007 has been successfully rolled back
-- System restored to state before Product Visions and User Stories were added
-- All related indexes, triggers, and data have been removed