-- Rollback 008: Remove Task Enhancements and Dependencies (Phase 2)
-- Date: 2025-08-22
-- Description: Rollback migration 008 - Remove task enhancements and dependency system
-- WARNING: This rollback will remove data added by the migration

-- ==================================================================================
-- REMOVE TRIGGERS
-- ==================================================================================
-- Drop triggers in reverse order

DROP TRIGGER IF EXISTS trigger_prevent_circular_task_parents;
DROP TRIGGER IF EXISTS trigger_task_labels_updated_at;
DROP TRIGGER IF EXISTS trigger_task_dependencies_updated_at;
DROP TRIGGER IF EXISTS trigger_decrease_label_usage;
DROP TRIGGER IF EXISTS trigger_update_label_usage;

-- ==================================================================================
-- REMOVE INDEXES
-- ==================================================================================
-- Drop all indexes created by migration 008

-- Task Label Assignments indexes
DROP INDEX IF EXISTS idx_task_label_assignments_context;
DROP INDEX IF EXISTS idx_task_label_assignments_label;
DROP INDEX IF EXISTS idx_task_label_assignments_task;

-- Task Labels indexes
DROP INDEX IF EXISTS idx_task_labels_active;
DROP INDEX IF EXISTS idx_task_labels_parent;
DROP INDEX IF EXISTS idx_task_labels_usage;
DROP INDEX IF EXISTS idx_task_labels_category;
DROP INDEX IF EXISTS idx_task_labels_name;

-- Task Dependencies indexes
DROP INDEX IF EXISTS idx_task_dependencies_external;
DROP INDEX IF EXISTS idx_task_dependencies_active;
DROP INDEX IF EXISTS idx_task_dependencies_type;
DROP INDEX IF EXISTS idx_task_dependencies_depends_on;
DROP INDEX IF EXISTS idx_task_dependencies_task_id;

-- Enhanced framework_tasks indexes
DROP INDEX IF EXISTS idx_tasks_task_type;
DROP INDEX IF EXISTS idx_tasks_tdd_order;
DROP INDEX IF EXISTS idx_tasks_task_order;
DROP INDEX IF EXISTS idx_tasks_user_story;
DROP INDEX IF EXISTS idx_tasks_parent;
DROP INDEX IF EXISTS idx_tasks_due_date;
DROP INDEX IF EXISTS idx_tasks_planned_dates;
DROP INDEX IF EXISTS idx_tasks_milestone;

-- ==================================================================================
-- REMOVE TABLES
-- ==================================================================================
-- Drop tables in dependency order (child tables first)

-- Drop Task Label Assignments table
DROP TABLE IF EXISTS task_label_assignments;

-- Drop Task Labels table
DROP TABLE IF EXISTS task_labels;

-- Drop Task Dependencies table
DROP TABLE IF EXISTS task_dependencies;

-- ==================================================================================
-- REMOVE ENHANCED FRAMEWORK_TASKS COLUMNS
-- ==================================================================================
-- WARNING: SQLite doesn't support DROP COLUMN directly
-- We need to recreate the table without the new columns

-- Step 1: Create backup of existing data (excluding new columns)
CREATE TEMPORARY TABLE framework_tasks_backup AS 
SELECT 
    id, task_key, epic_id, title, description,
    tdd_phase, status, 
    estimate_minutes, actual_minutes, story_points, position,
    points_earned, difficulty_modifier, streak_bonus, perfectionist_bonus,
    github_issue_number, github_branch, github_pr_number,
    assigned_to, reviewer_id,
    created_at, updated_at, completed_at, reviewed_at, deleted_at
FROM framework_tasks;

-- Step 2: Drop the current framework_tasks table
DROP TABLE framework_tasks;

-- Step 3: Recreate framework_tasks table with original schema
CREATE TABLE framework_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_key VARCHAR(50) NOT NULL,
    epic_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- TDD
    tdd_phase VARCHAR(20) CHECK(tdd_phase IN ('analysis', 'red', 'green', 'refactor', 'review')),
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Estimates
    estimate_minutes INTEGER NOT NULL DEFAULT 60,
    actual_minutes INTEGER DEFAULT 0,
    story_points INTEGER DEFAULT 1,
    position INTEGER,
    
    -- Gamification
    points_earned INTEGER DEFAULT 0,
    difficulty_modifier DECIMAL(3,2) DEFAULT 1.0,
    streak_bonus INTEGER DEFAULT 0,
    perfectionist_bonus INTEGER DEFAULT 0,
    
    -- GitHub
    github_issue_number INTEGER,
    github_branch VARCHAR(255),
    github_pr_number INTEGER,
    
    -- Multi-user
    assigned_to INTEGER,
    reviewer_id INTEGER,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    reviewed_at TIMESTAMP NULL,
    deleted_at TIMESTAMP NULL,
    
    FOREIGN KEY (epic_id) REFERENCES framework_epics(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES framework_users(id),
    FOREIGN KEY (reviewer_id) REFERENCES framework_users(id)
);

-- Step 4: Restore data from backup
INSERT INTO framework_tasks (
    id, task_key, epic_id, title, description,
    tdd_phase, status,
    estimate_minutes, actual_minutes, story_points, position,
    points_earned, difficulty_modifier, streak_bonus, perfectionist_bonus,
    github_issue_number, github_branch, github_pr_number,
    assigned_to, reviewer_id,
    created_at, updated_at, completed_at, reviewed_at, deleted_at
)
SELECT 
    id, task_key, epic_id, title, description,
    tdd_phase, status,
    estimate_minutes, actual_minutes, story_points, position,
    points_earned, difficulty_modifier, streak_bonus, perfectionist_bonus,
    github_issue_number, github_branch, github_pr_number,
    assigned_to, reviewer_id,
    created_at, updated_at, completed_at, reviewed_at, deleted_at
FROM framework_tasks_backup;

-- Step 5: Drop the backup table
DROP TABLE framework_tasks_backup;

-- Step 6: Recreate original framework_tasks indexes (if they existed)
-- These would have been dropped when we dropped the table
CREATE INDEX IF NOT EXISTS idx_framework_tasks_epic_id ON framework_tasks(epic_id);
CREATE INDEX IF NOT EXISTS idx_framework_tasks_status ON framework_tasks(status);
CREATE INDEX IF NOT EXISTS idx_framework_tasks_tdd_phase ON framework_tasks(tdd_phase);
CREATE INDEX IF NOT EXISTS idx_framework_tasks_assigned ON framework_tasks(assigned_to);

-- ==================================================================================
-- REMOVE ACHIEVEMENT TYPES
-- ==================================================================================
-- Remove achievement types added by migration 008

DELETE FROM achievement_types 
WHERE code IN ('MILESTONE_MASTER', 'DEPENDENCY_SOLVER', 'LABEL_ORGANIZER', 'TDD_SEQUENCER');

-- ==================================================================================
-- SCHEMA VERSION CLEANUP
-- ==================================================================================
-- Remove this migration from schema_migrations table (if it exists)

-- Note: This will be handled by the migration runner
-- DELETE FROM schema_migrations WHERE version = '008';

-- ==================================================================================
-- ROLLBACK VERIFICATION QUERIES
-- ==================================================================================
-- These queries can be run to verify successful rollback

-- Verify tables don't exist:
-- SELECT name FROM sqlite_master WHERE type='table' AND name IN ('task_dependencies', 'task_labels', 'task_label_assignments');
-- Should return no rows

-- Verify framework_tasks columns are back to original:
-- PRAGMA table_info(framework_tasks);
-- Should not show: is_milestone, planned_start_date, planned_end_date, due_date, acceptance_criteria, 
-- task_type, parent_task_id, task_order, original_estimate, tdd_order, tdd_skip_reason, user_story_id

-- Verify indexes don't exist:
-- SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_task_%';
-- Should return no rows

-- Verify triggers don't exist:
-- SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE '%task_%' OR name LIKE '%label%';
-- Should return no rows

-- ==================================================================================
-- DATA LOSS WARNING
-- ==================================================================================
-- WARNING: This rollback will permanently delete the following data:
--
-- 1. All task dependencies and their relationships
-- 2. All custom task labels and their assignments 
-- 3. Task milestone flags and planning dates
-- 4. Task acceptance criteria (JSON data)
-- 5. Parent-child task relationships
-- 6. Task ordering information
-- 7. Enhanced TDD tracking data
-- 8. Task type classifications
-- 9. User story relationships
-- 10. Original estimate baselines
--
-- Make sure you have a backup before running this rollback!

-- ==================================================================================
-- ROLLBACK COMPLETE
-- ==================================================================================
-- Migration 008 has been successfully rolled back
-- System restored to state before Task Enhancements and Dependencies were added
-- All enhanced columns, tables, indexes, triggers, and related data have been removed
--
-- IMPORTANT: Some data loss has occurred as documented above
-- Ensure you have backups if you need to recover this data