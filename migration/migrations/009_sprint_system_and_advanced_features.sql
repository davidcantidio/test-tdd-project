-- Migration 009: Sprint System and Advanced Features (Phase 3)
-- Date: 2025-08-22
-- Description: Complete advanced features including sprints, milestones, AI tracking, and audit log
-- Phase 3 of 3: Final advanced features for comprehensive project management
-- Scope: Sprint management, milestone tracking, AI integration, and comprehensive audit trail

-- ==================================================================================
-- SPRINTS TABLE
-- ==================================================================================
-- Agile sprint management with comprehensive planning and tracking capabilities

CREATE TABLE IF NOT EXISTS sprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    sprint_key VARCHAR(50) NOT NULL,
    sprint_name VARCHAR(255) NOT NULL,
    
    -- Sprint Planning
    sprint_goal TEXT,
    sprint_description TEXT,
    capacity_points INTEGER,
    planned_velocity INTEGER,
    actual_velocity INTEGER,
    
    -- Sprint Timeline
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    planned_hours INTEGER,
    actual_hours INTEGER DEFAULT 0,
    
    -- Sprint Status
    status VARCHAR(50) DEFAULT 'planning', -- planning, active, review, retrospective, completed, cancelled
    sprint_number INTEGER,
    is_current BOOLEAN DEFAULT FALSE,
    
    -- Team Configuration
    team_members JSON, -- Array of user IDs participating in sprint
    scrum_master_id INTEGER,
    product_owner_id INTEGER,
    development_team JSON, -- Array of developer user IDs
    
    -- Sprint Metrics
    story_points_committed INTEGER DEFAULT 0,
    story_points_completed INTEGER DEFAULT 0,
    tasks_committed INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    bugs_introduced INTEGER DEFAULT 0,
    bugs_resolved INTEGER DEFAULT 0,
    
    -- Sprint Health
    burndown_data JSON, -- Daily burndown chart data
    health_status VARCHAR(20) DEFAULT 'green', -- green, yellow, red
    risk_factors JSON, -- Array of identified risks
    impediments JSON, -- Array of current impediments
    
    -- Sprint Events
    planning_date DATE,
    review_date DATE,
    retrospective_date DATE,
    demo_scheduled BOOLEAN DEFAULT FALSE,
    
    -- Quality Metrics
    code_review_coverage DECIMAL(5,2),
    test_coverage DECIMAL(5,2),
    deployment_success_rate DECIMAL(5,2),
    customer_satisfaction INTEGER, -- 1-10 scale
    
    -- Sprint Outcomes
    demo_feedback JSON,
    retrospective_notes TEXT,
    lessons_learned TEXT,
    improvement_actions JSON,
    
    -- Integration
    external_sprint_id VARCHAR(100),
    external_system VARCHAR(50),
    sync_status VARCHAR(50) DEFAULT 'synced',
    
    -- Audit
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    cancelled_at TIMESTAMP NULL,
    
    -- Constraints
    FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (scrum_master_id) REFERENCES framework_users(id),
    FOREIGN KEY (product_owner_id) REFERENCES framework_users(id),
    FOREIGN KEY (created_by) REFERENCES framework_users(id),
    
    -- Ensure unique sprint keys per project
    UNIQUE(project_id, sprint_key),
    
    -- Ensure logical date ordering
    CHECK (start_date <= end_date),
    
    -- Ensure only one current sprint per project
    -- This will be enforced by a trigger instead of a unique constraint
    -- because SQLite doesn't support partial unique indexes well
);

-- ==================================================================================
-- SPRINT TASKS TABLE
-- ==================================================================================
-- Many-to-many relationship between sprints and tasks with sprint-specific metadata

CREATE TABLE IF NOT EXISTS sprint_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    
    -- Sprint Assignment Details
    commitment_type VARCHAR(50) DEFAULT 'committed', -- committed, stretch, carry_over
    assignment_reason TEXT,
    priority_in_sprint INTEGER,
    
    -- Sprint-Specific Planning
    sprint_estimate INTEGER, -- Estimate specifically for this sprint (may differ from task estimate)
    sprint_capacity DECIMAL(5,2), -- Percentage of sprint capacity this task consumes
    planned_start_day INTEGER, -- Day of sprint when task should start (1-based)
    planned_duration_days INTEGER, -- How many days the task should take in sprint
    
    -- Sprint Progress Tracking
    daily_updates JSON, -- Daily standup updates and progress
    actual_start_day INTEGER,
    actual_duration_days INTEGER,
    completion_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- Sprint Workflow
    workflow_status VARCHAR(50) DEFAULT 'backlog', -- backlog, ready, in_progress, review, done, removed
    sprint_stage VARCHAR(50), -- which part of sprint (beginning, middle, end)
    blocked_in_sprint BOOLEAN DEFAULT FALSE,
    blocking_reason TEXT,
    
    -- Team Assignment
    assigned_developers JSON, -- Array of user IDs working on this task in sprint
    reviewer_assigned INTEGER,
    pair_programming BOOLEAN DEFAULT FALSE,
    pair_partner_id INTEGER,
    
    -- Sprint Quality
    code_review_status VARCHAR(50),
    testing_status VARCHAR(50),
    definition_of_done_met BOOLEAN DEFAULT FALSE,
    acceptance_by_po BOOLEAN DEFAULT FALSE,
    
    -- Sprint Metrics
    effort_spent INTEGER DEFAULT 0, -- Minutes spent on this task during sprint
    interruptions_count INTEGER DEFAULT 0,
    context_switches INTEGER DEFAULT 0,
    collaboration_score INTEGER, -- 1-10 how well team collaborated on this task
    
    -- Sprint Changes
    scope_changes JSON, -- Changes made to task during sprint
    estimate_adjustments JSON, -- History of estimate changes during sprint
    assignment_changes JSON, -- History of assignment changes during sprint
    
    -- Audit
    added_to_sprint_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    removed_from_sprint_at TIMESTAMP NULL,
    completed_in_sprint_at TIMESTAMP NULL,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by INTEGER,
    
    -- Constraints
    FOREIGN KEY (sprint_id) REFERENCES sprints(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES framework_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_assigned) REFERENCES framework_users(id),
    FOREIGN KEY (pair_partner_id) REFERENCES framework_users(id),
    FOREIGN KEY (added_by) REFERENCES framework_users(id),
    
    -- Prevent duplicate task assignments to same sprint
    UNIQUE(sprint_id, task_id)
);

-- ==================================================================================
-- SPRINT MILESTONES TABLE
-- ==================================================================================
-- Track important milestones and deliverables within sprints

CREATE TABLE IF NOT EXISTS sprint_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id INTEGER NOT NULL,
    milestone_name VARCHAR(255) NOT NULL,
    
    -- Milestone Details
    milestone_description TEXT,
    milestone_type VARCHAR(50) DEFAULT 'deliverable', -- deliverable, checkpoint, review, demo, release
    success_criteria JSON,
    
    -- Milestone Planning
    target_date DATE,
    planned_effort INTEGER, -- Minutes
    dependencies JSON, -- Array of task IDs or other milestone IDs this depends on
    deliverables JSON, -- Array of expected deliverables
    
    -- Milestone Status
    status VARCHAR(50) DEFAULT 'planned', -- planned, in_progress, at_risk, completed, missed
    completion_percentage DECIMAL(5,2) DEFAULT 0,
    actual_completion_date DATE,
    
    -- Quality Gates
    quality_criteria JSON,
    quality_status VARCHAR(50),
    quality_notes TEXT,
    sign_off_required BOOLEAN DEFAULT FALSE,
    signed_off_by INTEGER,
    signed_off_at TIMESTAMP,
    
    -- Stakeholder Management
    stakeholders JSON, -- Array of user IDs who are interested in this milestone
    communication_plan JSON,
    status_update_frequency VARCHAR(50) DEFAULT 'weekly',
    
    -- Risk Management
    risk_factors JSON,
    mitigation_plans JSON,
    contingency_plans JSON,
    escalation_path JSON,
    
    -- Integration & External
    external_dependencies JSON,
    external_milestone_id VARCHAR(100),
    external_system VARCHAR(50),
    
    -- Audit
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    achieved_at TIMESTAMP NULL,
    
    -- Constraints
    FOREIGN KEY (sprint_id) REFERENCES sprints(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES framework_users(id),
    FOREIGN KEY (signed_off_by) REFERENCES framework_users(id)
);

-- ==================================================================================
-- AI GENERATIONS TABLE
-- ==================================================================================
-- Track AI-generated content, recommendations, and automation within the system

CREATE TABLE IF NOT EXISTS ai_generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Generation Context
    generation_type VARCHAR(50) NOT NULL, -- code_generation, task_creation, planning_assistance, estimation, review
    context_type VARCHAR(50), -- task, epic, user_story, sprint, project, general
    context_id INTEGER, -- ID of the related entity
    
    -- AI Model Information
    ai_model VARCHAR(100), -- gpt-4, claude-3, gemini-pro, etc.
    model_version VARCHAR(50),
    provider VARCHAR(50), -- openai, anthropic, google, etc.
    
    -- Generation Request
    user_prompt TEXT NOT NULL,
    system_prompt TEXT,
    input_context JSON, -- Additional context data provided to AI
    user_id INTEGER, -- User who requested the generation
    
    -- Generation Response
    ai_response TEXT NOT NULL,
    generation_metadata JSON, -- Token usage, costs, timing, etc.
    confidence_score DECIMAL(5,2), -- AI's confidence in the response (if available)
    
    -- Content Analysis
    content_type VARCHAR(50), -- text, code, json, markdown, etc.
    content_language VARCHAR(20), -- programming language if code
    content_quality_score INTEGER, -- 1-10 quality assessment
    
    -- Usage and Feedback
    used_by_user BOOLEAN DEFAULT FALSE,
    user_rating INTEGER, -- 1-5 star rating by user
    user_feedback TEXT,
    modifications_made TEXT, -- How user modified the AI output
    
    -- Generation Statistics
    input_tokens INTEGER,
    output_tokens INTEGER,
    processing_time_ms INTEGER,
    generation_cost DECIMAL(10,6), -- Cost in USD
    
    -- Quality Assurance
    reviewed_by INTEGER, -- User who reviewed the AI output
    review_status VARCHAR(50), -- approved, rejected, needs_modification
    review_notes TEXT,
    reviewed_at TIMESTAMP,
    
    -- Integration
    applied_to_system BOOLEAN DEFAULT FALSE, -- Whether the AI output was integrated
    integration_results JSON, -- Results of applying the AI output
    rollback_data JSON, -- Data needed to rollback AI changes
    
    -- Learning and Improvement
    feedback_loop_data JSON, -- Data for improving future generations
    success_metrics JSON,
    improvement_suggestions TEXT,
    
    -- Audit
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP, -- When to clean up old generations
    deleted_at TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (user_id) REFERENCES framework_users(id),
    FOREIGN KEY (reviewed_by) REFERENCES framework_users(id)
);

-- ==================================================================================
-- CHANGE LOG TABLE
-- ==================================================================================
-- Comprehensive audit trail for all system changes

CREATE TABLE IF NOT EXISTS change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Change Identification
    change_type VARCHAR(50) NOT NULL, -- create, update, delete, status_change, assignment_change
    entity_type VARCHAR(50) NOT NULL, -- task, epic, user_story, sprint, project, user, etc.
    entity_id INTEGER NOT NULL,
    
    -- Change Details
    field_name VARCHAR(100), -- Specific field that changed
    old_value TEXT, -- Previous value (JSON encoded if complex)
    new_value TEXT, -- New value (JSON encoded if complex)
    change_summary TEXT, -- Human-readable description of change
    
    -- Change Context
    change_reason VARCHAR(100), -- user_action, system_trigger, api_call, migration, etc.
    change_context JSON, -- Additional context about why change was made
    business_impact TEXT, -- Impact of this change on business/project
    
    -- User and Session
    user_id INTEGER, -- User who made the change
    session_id VARCHAR(100), -- Session identifier
    user_agent TEXT, -- Browser/client information
    ip_address VARCHAR(50), -- IP address of user
    
    -- System Context
    system_version VARCHAR(50), -- Version of the system when change was made
    component VARCHAR(50), -- System component that made the change
    api_endpoint VARCHAR(255), -- API endpoint used (if applicable)
    request_id VARCHAR(100), -- Unique request identifier
    
    -- Change Metadata
    change_batch_id VARCHAR(100), -- Group related changes together
    is_automated BOOLEAN DEFAULT FALSE, -- Whether change was automated
    confidence_level INTEGER, -- 1-10 confidence in change accuracy
    validation_status VARCHAR(50), -- validated, pending, failed
    
    -- Reversal and Rollback
    is_reversible BOOLEAN DEFAULT TRUE,
    reversal_data JSON, -- Data needed to reverse this change
    reversed_at TIMESTAMP,
    reversed_by INTEGER,
    reversal_reason TEXT,
    
    -- Approval Workflow
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_by INTEGER,
    approved_at TIMESTAMP,
    approval_notes TEXT,
    
    -- Notification and Communication
    notifications_sent JSON, -- Who was notified about this change
    change_visibility VARCHAR(50) DEFAULT 'internal', -- internal, team, public
    announcement_made BOOLEAN DEFAULT FALSE,
    
    -- Performance Impact
    performance_impact VARCHAR(50), -- none, low, medium, high
    resource_usage JSON, -- CPU, memory usage for this change
    affected_queries JSON, -- Database queries affected by this change
    
    -- Data Quality
    data_validation_passed BOOLEAN DEFAULT TRUE,
    validation_errors JSON,
    data_quality_score INTEGER, -- 1-10 score
    
    -- Compliance and Security
    compliance_relevant BOOLEAN DEFAULT FALSE,
    security_classification VARCHAR(50), -- public, internal, confidential, restricted
    retention_period INTEGER, -- Days to retain this log entry
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (user_id) REFERENCES framework_users(id),
    FOREIGN KEY (reversed_by) REFERENCES framework_users(id),
    FOREIGN KEY (approved_by) REFERENCES framework_users(id)
);

-- ==================================================================================
-- PERFORMANCE INDEXES - PHASE 3
-- ==================================================================================

-- Sprints indexes
CREATE INDEX IF NOT EXISTS idx_sprints_project_id ON sprints(project_id);
CREATE INDEX IF NOT EXISTS idx_sprints_status ON sprints(status);
CREATE INDEX IF NOT EXISTS idx_sprints_current ON sprints(is_current, status);
CREATE INDEX IF NOT EXISTS idx_sprints_dates ON sprints(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_sprints_team ON sprints(scrum_master_id, product_owner_id);
CREATE INDEX IF NOT EXISTS idx_sprints_number ON sprints(project_id, sprint_number);

-- Sprint Tasks indexes
CREATE INDEX IF NOT EXISTS idx_sprint_tasks_sprint_id ON sprint_tasks(sprint_id);
CREATE INDEX IF NOT EXISTS idx_sprint_tasks_task_id ON sprint_tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_sprint_tasks_status ON sprint_tasks(workflow_status);
CREATE INDEX IF NOT EXISTS idx_sprint_tasks_assignment ON sprint_tasks(reviewer_assigned, pair_partner_id);
CREATE INDEX IF NOT EXISTS idx_sprint_tasks_progress ON sprint_tasks(completion_percentage, workflow_status);
CREATE INDEX IF NOT EXISTS idx_sprint_tasks_commitment ON sprint_tasks(commitment_type, priority_in_sprint);

-- Sprint Milestones indexes
CREATE INDEX IF NOT EXISTS idx_sprint_milestones_sprint_id ON sprint_milestones(sprint_id);
CREATE INDEX IF NOT EXISTS idx_sprint_milestones_status ON sprint_milestones(status);
CREATE INDEX IF NOT EXISTS idx_sprint_milestones_dates ON sprint_milestones(target_date, actual_completion_date);
CREATE INDEX IF NOT EXISTS idx_sprint_milestones_type ON sprint_milestones(milestone_type, status);

-- AI Generations indexes
CREATE INDEX IF NOT EXISTS idx_ai_generations_user_id ON ai_generations(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_generations_type ON ai_generations(generation_type, context_type);
CREATE INDEX IF NOT EXISTS idx_ai_generations_context ON ai_generations(context_type, context_id);
CREATE INDEX IF NOT EXISTS idx_ai_generations_model ON ai_generations(ai_model, provider);
CREATE INDEX IF NOT EXISTS idx_ai_generations_usage ON ai_generations(used_by_user, user_rating);
CREATE INDEX IF NOT EXISTS idx_ai_generations_dates ON ai_generations(generated_at, expires_at);
CREATE INDEX IF NOT EXISTS idx_ai_generations_review ON ai_generations(review_status, reviewed_by);

-- Change Log indexes
CREATE INDEX IF NOT EXISTS idx_change_log_entity ON change_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_change_log_user_id ON change_log(user_id);
CREATE INDEX IF NOT EXISTS idx_change_log_type ON change_log(change_type, entity_type);
CREATE INDEX IF NOT EXISTS idx_change_log_dates ON change_log(created_at, indexed_at);
CREATE INDEX IF NOT EXISTS idx_change_log_batch ON change_log(change_batch_id);
CREATE INDEX IF NOT EXISTS idx_change_log_approval ON change_log(requires_approval, approved_by);
CREATE INDEX IF NOT EXISTS idx_change_log_reversal ON change_log(is_reversible, reversed_at);
CREATE INDEX IF NOT EXISTS idx_change_log_automated ON change_log(is_automated, change_reason);

-- ==================================================================================
-- DATA INTEGRITY TRIGGERS - PHASE 3
-- ==================================================================================

-- Ensure only one current sprint per project
CREATE TRIGGER IF NOT EXISTS trigger_single_current_sprint
    BEFORE UPDATE ON sprints
    FOR EACH ROW
    WHEN NEW.is_current = TRUE
BEGIN
    UPDATE sprints 
    SET is_current = FALSE 
    WHERE project_id = NEW.project_id 
      AND id != NEW.id 
      AND is_current = TRUE;
END;

-- Update sprints timestamp
CREATE TRIGGER IF NOT EXISTS trigger_sprints_updated_at
    AFTER UPDATE ON sprints
    FOR EACH ROW
BEGIN
    UPDATE sprints 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Update sprint_tasks timestamp
CREATE TRIGGER IF NOT EXISTS trigger_sprint_tasks_updated_at
    AFTER UPDATE ON sprint_tasks
    FOR EACH ROW
BEGIN
    UPDATE sprint_tasks 
    SET last_updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Update sprint_milestones timestamp  
CREATE TRIGGER IF NOT EXISTS trigger_sprint_milestones_updated_at
    AFTER UPDATE ON sprint_milestones
    FOR EACH ROW
BEGIN
    UPDATE sprint_milestones 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Auto-update AI generations timestamp
CREATE TRIGGER IF NOT EXISTS trigger_ai_generations_updated_at
    AFTER UPDATE ON ai_generations
    FOR EACH ROW
BEGIN
    UPDATE ai_generations 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Auto-create change log entries for critical tables
CREATE TRIGGER IF NOT EXISTS trigger_auto_change_log_tasks
    AFTER UPDATE ON framework_tasks
    FOR EACH ROW
    WHEN OLD.status != NEW.status 
      OR OLD.assigned_to != NEW.assigned_to 
      OR OLD.tdd_phase != NEW.tdd_phase
BEGIN
    INSERT INTO change_log (
        change_type, entity_type, entity_id,
        field_name, old_value, new_value,
        change_summary, user_id
    ) VALUES (
        'update', 'task', NEW.id,
        CASE 
            WHEN OLD.status != NEW.status THEN 'status'
            WHEN OLD.assigned_to != NEW.assigned_to THEN 'assigned_to'
            WHEN OLD.tdd_phase != NEW.tdd_phase THEN 'tdd_phase'
        END,
        CASE 
            WHEN OLD.status != NEW.status THEN OLD.status
            WHEN OLD.assigned_to != NEW.assigned_to THEN CAST(OLD.assigned_to AS TEXT)
            WHEN OLD.tdd_phase != NEW.tdd_phase THEN OLD.tdd_phase
        END,
        CASE 
            WHEN OLD.status != NEW.status THEN NEW.status
            WHEN OLD.assigned_to != NEW.assigned_to THEN CAST(NEW.assigned_to AS TEXT)
            WHEN OLD.tdd_phase != NEW.tdd_phase THEN NEW.tdd_phase
        END,
        'Task ' || 
        CASE 
            WHEN OLD.status != NEW.status THEN 'status changed from ' || OLD.status || ' to ' || NEW.status
            WHEN OLD.assigned_to != NEW.assigned_to THEN 'assignment changed'
            WHEN OLD.tdd_phase != NEW.tdd_phase THEN 'TDD phase changed from ' || OLD.tdd_phase || ' to ' || NEW.tdd_phase
        END,
        NEW.assigned_to -- Assumes the assigned user made the change; could be improved
    );
END;

-- ==================================================================================
-- ACHIEVEMENT TYPES - PHASE 3
-- ==================================================================================
-- Add achievement types for advanced sprint and AI features

INSERT OR IGNORE INTO achievement_types (code, name, description, icon, points_value, category)
VALUES 
    -- Sprint Achievements
    ('SPRINT_MASTER', 'Sprint Master', 'Successfully completed 5 sprints as Scrum Master', '🏃‍♂️', 60, 'sprint'),
    ('VELOCITY_CHAMPION', 'Velocity Champion', 'Achieved planned velocity for 3 consecutive sprints', '⚡', 50, 'sprint'),
    ('MILESTONE_ACHIEVER', 'Milestone Achiever', 'Completed all sprint milestones on time', '🎯', 45, 'sprint'),
    ('BURNDOWN_MASTER', 'Burndown Master', 'Maintained ideal burndown curve throughout sprint', '📉', 40, 'sprint'),
    
    -- AI Integration Achievements
    ('AI_COLLABORATOR', 'AI Collaborator', 'Successfully used AI assistance for 10 tasks', '🤖', 35, 'ai'),
    ('AI_REVIEWER', 'AI Reviewer', 'Provided feedback on AI-generated content', '🔍', 25, 'ai'),
    ('PROMPT_ENGINEER', 'Prompt Engineer', 'Created effective AI prompts', '🎨', 30, 'ai'),
    
    -- Quality Achievements
    ('CHANGE_TRACKER', 'Change Tracker', 'Maintained comprehensive change documentation', '📋', 20, 'quality'),
    ('AUDIT_CHAMPION', 'Audit Champion', 'Contributed to system audit trail', '🔐', 15, 'quality');

-- ==================================================================================
-- DEFAULT SPRINT DATA
-- ==================================================================================
-- Create sample sprint templates and configurations

-- Insert default sprint milestone types (these can be reused across projects)
INSERT OR IGNORE INTO sprint_milestones (
    sprint_id, milestone_name, milestone_description, milestone_type,
    success_criteria, status, created_by
) VALUES 
    -- Note: These would typically be created when actual sprints are created
    -- This is just to show the structure
    (-1, 'Sprint Planning Complete', 'All tasks estimated and committed to sprint', 'checkpoint', 
     '["All user stories estimated", "Team capacity confirmed", "Sprint goal defined"]', 'completed', 1);

-- Delete the sample data (we don't want actual milestones for non-existent sprints)
DELETE FROM sprint_milestones WHERE sprint_id = -1;

-- ==================================================================================
-- MIGRATION SUMMARY
-- ==================================================================================
-- Phase 3 Complete: Sprint System and Advanced Features established
-- 
-- New Tables Created:
-- ✅ sprints (35+ fields, 6 indexes, 2 triggers)
-- ✅ sprint_tasks (30+ fields, 6 indexes, 1 trigger)  
-- ✅ sprint_milestones (25+ fields, 4 indexes, 1 trigger)
-- ✅ ai_generations (30+ fields, 7 indexes, 1 trigger)
-- ✅ change_log (40+ fields, 8 indexes, 1 auto-trigger for tasks)
-- ✅ 9 new achievement types added
-- 
-- Full Migration Series Complete:
-- Phase 1: Product Visions & User Stories ✅
-- Phase 2: Task Enhancements & Dependencies ✅  
-- Phase 3: Sprint System & Advanced Features ✅
-- 
-- Total Enhancement:
-- - 7 new tables created
-- - 1 table enhanced (framework_tasks)
-- - 50+ new indexes for optimal performance
-- - 15+ triggers for data integrity
-- - 30+ achievement types for gamification
-- - Complete audit trail and AI integration
-- 
-- New Hierarchy Complete:
-- Client → Project → ProductVision → Epic → UserStory → Task
--                                         ↘ Sprint → Milestone
-- 
-- Compatibility: 100% backward compatible, all existing functionality preserved