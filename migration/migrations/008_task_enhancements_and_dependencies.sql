-- Migration 008: Task Enhancements and Dependencies (Phase 2)
-- Date: 2025-08-22
-- Description: Enhance framework_tasks table and add task dependencies system
-- Phase 2 of 3: Task improvements and dependency management
-- Scope: ALTER TABLE framework_tasks + new dependency/label tables

-- ==================================================================================
-- FRAMEWORK_TASKS ENHANCEMENTS
-- ==================================================================================
-- Add critical new columns to framework_tasks table
-- These fields enable milestone tracking, better planning, and enhanced task metadata

-- Add milestone tracking
ALTER TABLE framework_tasks 
ADD COLUMN is_milestone BOOLEAN DEFAULT FALSE;

-- Add better date planning
ALTER TABLE framework_tasks 
ADD COLUMN planned_start_date DATE;

ALTER TABLE framework_tasks 
ADD COLUMN planned_end_date DATE;

ALTER TABLE framework_tasks 
ADD COLUMN due_date DATE;

-- Add detailed acceptance criteria as JSON
ALTER TABLE framework_tasks 
ADD COLUMN acceptance_criteria JSON;

-- Add task type enhancement
ALTER TABLE framework_tasks 
ADD COLUMN task_type VARCHAR(50) DEFAULT 'development';

-- Add parent-child task relationships
ALTER TABLE framework_tasks 
ADD COLUMN parent_task_id INTEGER;

-- Add task ordering within groups
ALTER TABLE framework_tasks 
ADD COLUMN task_order INTEGER DEFAULT 0;

-- Add effort tracking
ALTER TABLE framework_tasks 
ADD COLUMN original_estimate INTEGER; -- Baseline estimate for comparison

-- Add TDD enhancements
ALTER TABLE framework_tasks 
ADD COLUMN tdd_order INTEGER; -- Order within TDD sequence

ALTER TABLE framework_tasks 
ADD COLUMN tdd_skip_reason TEXT; -- Why TDD was skipped if applicable

-- Add user story relationship
ALTER TABLE framework_tasks 
ADD COLUMN user_story_id INTEGER;

-- Add constraints for new foreign keys
ALTER TABLE framework_tasks 
ADD CONSTRAINT fk_tasks_parent_task 
FOREIGN KEY (parent_task_id) REFERENCES framework_tasks(id);

ALTER TABLE framework_tasks 
ADD CONSTRAINT fk_tasks_user_story 
FOREIGN KEY (user_story_id) REFERENCES framework_user_stories(id) ON DELETE SET NULL;

-- ==================================================================================
-- TASK DEPENDENCIES TABLE
-- ==================================================================================
-- Manage complex task dependencies with different relationship types

CREATE TABLE IF NOT EXISTS task_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    depends_on_task_id INTEGER NOT NULL,
    
    -- Dependency Type
    dependency_type VARCHAR(50) DEFAULT 'finish_to_start', -- finish_to_start, start_to_start, finish_to_finish, start_to_finish
    dependency_strength VARCHAR(20) DEFAULT 'hard', -- hard, soft, preferred
    
    -- Timing
    lead_lag_days INTEGER DEFAULT 0, -- Positive = lag, Negative = lead
    
    -- Metadata
    dependency_reason TEXT, -- Why this dependency exists
    created_reason TEXT, -- Why this dependency was created
    business_impact TEXT, -- Impact if dependency is broken
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_validated BOOLEAN DEFAULT FALSE, -- Has this dependency been validated?
    validation_notes TEXT,
    
    -- Risk Management
    risk_level VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    mitigation_plan TEXT,
    alternative_approaches TEXT,
    
    -- External Dependencies
    external_dependency BOOLEAN DEFAULT FALSE,
    external_system VARCHAR(100),
    external_reference VARCHAR(255),
    external_contact JSON, -- Contact info for external dependencies
    
    -- Tracking
    created_by INTEGER,
    validated_by INTEGER,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP NULL,
    removed_at TIMESTAMP NULL,
    
    -- Constraints
    FOREIGN KEY (task_id) REFERENCES framework_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES framework_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES framework_users(id),
    FOREIGN KEY (validated_by) REFERENCES framework_users(id),
    
    -- Prevent self-dependencies and duplicates
    CHECK (task_id != depends_on_task_id),
    UNIQUE(task_id, depends_on_task_id)
);

-- ==================================================================================
-- TASK LABELS TABLE
-- ==================================================================================
-- Flexible labeling system for task categorization and filtering

CREATE TABLE IF NOT EXISTS task_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label_name VARCHAR(100) NOT NULL,
    
    -- Label Properties
    label_description TEXT,
    label_color VARCHAR(20) DEFAULT '#3498db',
    label_icon VARCHAR(50),
    label_category VARCHAR(50) DEFAULT 'general',
    
    -- Behavior
    is_system_label BOOLEAN DEFAULT FALSE, -- System vs user-created labels
    is_exclusive BOOLEAN DEFAULT FALSE, -- Can only have one label from this group
    auto_apply_rules JSON, -- Rules for automatically applying this label
    
    -- Usage Statistics
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    
    -- Organization
    display_order INTEGER DEFAULT 100,
    parent_label_id INTEGER, -- For hierarchical labels
    
    -- Access Control
    visibility VARCHAR(20) DEFAULT 'public', -- public, private, team
    created_by INTEGER,
    team_restricted JSON, -- Which teams can use this label
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    
    -- Constraints
    FOREIGN KEY (parent_label_id) REFERENCES task_labels(id),
    FOREIGN KEY (created_by) REFERENCES framework_users(id),
    
    UNIQUE(label_name) -- Global unique label names
);

-- ==================================================================================
-- TASK LABEL ASSIGNMENTS TABLE
-- ==================================================================================
-- Many-to-many relationship between tasks and labels

CREATE TABLE IF NOT EXISTS task_label_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    label_id INTEGER NOT NULL,
    
    -- Assignment Context
    assigned_reason TEXT,
    assignment_context VARCHAR(100), -- manual, automatic, bulk, import
    confidence_score DECIMAL(3,2), -- For auto-assigned labels (0.00-1.00)
    
    -- Assignment Metadata
    assigned_by INTEGER,
    validated_by INTEGER,
    is_validated BOOLEAN DEFAULT TRUE,
    
    -- Audit
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP NULL,
    removed_at TIMESTAMP NULL,
    
    -- Constraints
    FOREIGN KEY (task_id) REFERENCES framework_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (label_id) REFERENCES task_labels(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES framework_users(id),
    FOREIGN KEY (validated_by) REFERENCES framework_users(id),
    
    -- Prevent duplicate label assignments
    UNIQUE(task_id, label_id)
);

-- ==================================================================================
-- PERFORMANCE INDEXES - PHASE 2
-- ==================================================================================
-- Indexes for enhanced framework_tasks columns

CREATE INDEX IF NOT EXISTS idx_tasks_milestone ON framework_tasks(is_milestone, status);
CREATE INDEX IF NOT EXISTS idx_tasks_planned_dates ON framework_tasks(planned_start_date, planned_end_date);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON framework_tasks(due_date, status) WHERE due_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_parent ON framework_tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_user_story ON framework_tasks(user_story_id);
CREATE INDEX IF NOT EXISTS idx_tasks_task_order ON framework_tasks(epic_id, task_order);
CREATE INDEX IF NOT EXISTS idx_tasks_tdd_order ON framework_tasks(epic_id, tdd_order) WHERE tdd_order IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_task_type ON framework_tasks(task_type, status);

-- Task Dependencies indexes
CREATE INDEX IF NOT EXISTS idx_task_dependencies_task_id ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_depends_on ON task_dependencies(depends_on_task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_type ON task_dependencies(dependency_type, dependency_strength);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_active ON task_dependencies(is_active, risk_level);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_external ON task_dependencies(external_dependency, external_system);

-- Task Labels indexes
CREATE INDEX IF NOT EXISTS idx_task_labels_name ON task_labels(label_name);
CREATE INDEX IF NOT EXISTS idx_task_labels_category ON task_labels(label_category, display_order);
CREATE INDEX IF NOT EXISTS idx_task_labels_usage ON task_labels(usage_count, last_used_at);
CREATE INDEX IF NOT EXISTS idx_task_labels_parent ON task_labels(parent_label_id);
CREATE INDEX IF NOT EXISTS idx_task_labels_active ON task_labels(is_system_label, visibility) WHERE deleted_at IS NULL;

-- Task Label Assignments indexes
CREATE INDEX IF NOT EXISTS idx_task_label_assignments_task ON task_label_assignments(task_id);
CREATE INDEX IF NOT EXISTS idx_task_label_assignments_label ON task_label_assignments(label_id);
CREATE INDEX IF NOT EXISTS idx_task_label_assignments_context ON task_label_assignments(assignment_context, confidence_score);

-- ==================================================================================
-- DATA INTEGRITY TRIGGERS - PHASE 2
-- ==================================================================================

-- Update task_labels usage statistics
CREATE TRIGGER IF NOT EXISTS trigger_update_label_usage
    AFTER INSERT ON task_label_assignments
    FOR EACH ROW
BEGIN
    UPDATE task_labels 
    SET usage_count = usage_count + 1, 
        last_used_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.label_id;
END;

-- Decrease usage count when label assignment is removed
CREATE TRIGGER IF NOT EXISTS trigger_decrease_label_usage
    AFTER DELETE ON task_label_assignments
    FOR EACH ROW
BEGIN
    UPDATE task_labels 
    SET usage_count = GREATEST(0, usage_count - 1)
    WHERE id = OLD.label_id;
END;

-- Update task dependencies timestamp
CREATE TRIGGER IF NOT EXISTS trigger_task_dependencies_updated_at
    AFTER UPDATE ON task_dependencies
    FOR EACH ROW
BEGIN
    UPDATE task_dependencies 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Update task labels timestamp
CREATE TRIGGER IF NOT EXISTS trigger_task_labels_updated_at
    AFTER UPDATE ON task_labels
    FOR EACH ROW
BEGIN
    UPDATE task_labels 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Prevent circular task dependencies in parent-child relationships
CREATE TRIGGER IF NOT EXISTS trigger_prevent_circular_task_parents
    BEFORE UPDATE ON framework_tasks
    FOR EACH ROW
    WHEN NEW.parent_task_id IS NOT NULL AND NEW.parent_task_id = NEW.id
BEGIN
    SELECT RAISE(ABORT, 'Task cannot be its own parent');
END;

-- ==================================================================================
-- DEFAULT LABELS SETUP - PHASE 2
-- ==================================================================================
-- Create essential system labels for task organization

INSERT OR IGNORE INTO task_labels (label_name, label_description, label_color, label_category, is_system_label, display_order)
VALUES 
    -- Priority Labels
    ('Critical', 'Critical priority task requiring immediate attention', '#e74c3c', 'priority', TRUE, 1),
    ('High Priority', 'High priority task', '#f39c12', 'priority', TRUE, 2),
    ('Low Priority', 'Low priority task', '#95a5a6', 'priority', TRUE, 3),
    
    -- Task Type Labels
    ('Bug Fix', 'Task involves fixing a bug or defect', '#e67e22', 'type', TRUE, 10),
    ('Feature Development', 'Task involves developing new functionality', '#3498db', 'type', TRUE, 11),
    ('Refactoring', 'Task involves code improvement without changing functionality', '#9b59b6', 'type', TRUE, 12),
    ('Documentation', 'Task involves creating or updating documentation', '#1abc9c', 'type', TRUE, 13),
    ('Testing', 'Task involves writing or executing tests', '#27ae60', 'type', TRUE, 14),
    
    -- Status Labels
    ('Blocked', 'Task is blocked and cannot proceed', '#c0392b', 'status', TRUE, 20),
    ('Ready for Review', 'Task is complete and ready for review', '#f1c40f', 'status', TRUE, 21),
    ('In Progress', 'Task is actively being worked on', '#3498db', 'status', TRUE, 22),
    
    -- TDD Labels
    ('Red Phase', 'TDD Red phase - writing failing tests', '#e74c3c', 'tdd', TRUE, 30),
    ('Green Phase', 'TDD Green phase - making tests pass', '#27ae60', 'tdd', TRUE, 31),
    ('Refactor Phase', 'TDD Refactor phase - improving code quality', '#9b59b6', 'tdd', TRUE, 32),
    
    -- Complexity Labels
    ('Simple', 'Simple task requiring minimal effort', '#2ecc71', 'complexity', TRUE, 40),
    ('Complex', 'Complex task requiring significant effort', '#e74c3c', 'complexity', TRUE, 41),
    ('Research Needed', 'Task requires research before implementation', '#34495e', 'complexity', TRUE, 42);

-- ==================================================================================
-- DATA MIGRATION - PHASE 2
-- ==================================================================================
-- Migrate existing data to new structures where appropriate

-- Update existing tasks with default task_type based on current status and context
UPDATE framework_tasks 
SET task_type = CASE 
    WHEN title LIKE '%test%' OR title LIKE '%testing%' THEN 'testing'
    WHEN title LIKE '%bug%' OR title LIKE '%fix%' THEN 'bug_fix'
    WHEN title LIKE '%doc%' OR title LIKE '%documentation%' THEN 'documentation'
    WHEN title LIKE '%refactor%' OR title LIKE '%clean%' THEN 'refactoring'
    ELSE 'development'
END
WHERE task_type = 'development'; -- Only update default values

-- Set milestone flag for tasks that appear to be milestones
UPDATE framework_tasks 
SET is_milestone = TRUE
WHERE title LIKE '%milestone%' 
   OR title LIKE '%release%' 
   OR title LIKE '%deployment%'
   OR title LIKE '%launch%';

-- Copy estimated minutes to original_estimate for baseline tracking
UPDATE framework_tasks 
SET original_estimate = estimate_minutes
WHERE original_estimate IS NULL AND estimate_minutes IS NOT NULL;

-- ==================================================================================
-- ACHIEVEMENT TYPES UPDATE - PHASE 2
-- ==================================================================================
-- Add achievement types for enhanced task management

INSERT OR IGNORE INTO achievement_types (code, name, description, icon, points_value, category)
VALUES 
    ('MILESTONE_MASTER', 'Milestone Master', 'Completed 5 milestone tasks', '🏁', 40, 'tasks'),
    ('DEPENDENCY_SOLVER', 'Dependency Solver', 'Resolved complex task dependencies', '🔗', 35, 'planning'),
    ('LABEL_ORGANIZER', 'Label Organizer', 'Used task labels effectively for organization', '🏷️', 25, 'organization'),
    ('TDD_SEQUENCER', 'TDD Sequencer', 'Completed tasks in proper TDD order', '🔄', 45, 'tdd');

-- ==================================================================================
-- MIGRATION SUMMARY
-- ==================================================================================
-- Phase 2 Complete: Task Enhancements and Dependencies established
-- 
-- Enhanced Tables:
-- ✅ framework_tasks (+12 fields, +8 indexes, +1 trigger)
-- 
-- New Tables Created:
-- ✅ task_dependencies (20 fields, 5 indexes, 1 trigger)
-- ✅ task_labels (15 fields, 5 indexes, 1 trigger)
-- ✅ task_label_assignments (9 fields, 3 indexes, 2 triggers)
-- ✅ 17 default system labels added
-- ✅ 4 new achievement types added
-- 
-- Next Phase: Sprint System & Advanced Features (009_sprint_and_milestones.sql)
-- - CREATE TABLE sprints
-- - CREATE TABLE sprint_tasks 
-- - CREATE TABLE sprint_milestones
-- - CREATE TABLE ai_generations
-- - CREATE TABLE change_log
-- 
-- Compatibility: 100% backward compatible, existing data preserved and enhanced