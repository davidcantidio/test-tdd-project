-- ==================================================================================
-- FRAMEWORK DATABASE SCHEMA - FINAL CONSOLIDATED VERSION
-- Complete TDD Framework with Client-Project-Epic-Task Hierarchy
-- Date: 2025-08-15
-- Status: PRODUCTION READY
-- ==================================================================================

-- This schema consolidates all previous versions:
-- - framework_v3.sql (core tables)
-- - schema_extensions_v4.sql (duration system)
-- - schema_extensions_v5.sql (bidirectional sync)
-- - schema_extensions_v6.sql (client-project hierarchy)

-- ==================================================================================
-- CORE TABLES - Multi-user Framework
-- ==================================================================================

-- Users table (multi-user support)
CREATE TABLE IF NOT EXISTS framework_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    github_username VARCHAR(100),
    preferences JSON,
    
    -- Gamification
    total_points INTEGER DEFAULT 0,
    current_level INTEGER DEFAULT 1,
    experience_points INTEGER DEFAULT 0,
    
    -- Status
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- ==================================================================================
-- CLIENT-PROJECT HIERARCHY
-- ==================================================================================

-- Clients table (top-level organization)
CREATE TABLE IF NOT EXISTS framework_clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_key VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    
    -- Client Information
    description TEXT,
    industry VARCHAR(100),
    company_size VARCHAR(50),
    
    -- Contact
    primary_contact_name VARCHAR(255),
    primary_contact_email VARCHAR(255),
    primary_contact_phone VARCHAR(50),
    
    -- Business
    billing_email VARCHAR(255),
    billing_address TEXT,
    tax_id VARCHAR(100),
    
    -- Configuration
    timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo',
    currency VARCHAR(10) DEFAULT 'BRL',
    preferred_language VARCHAR(10) DEFAULT 'pt-BR',
    preferences JSON,
    custom_fields JSON,
    
    -- Commercial
    hourly_rate DECIMAL(10,2),
    contract_type VARCHAR(50) DEFAULT 'time_and_materials',
    payment_terms VARCHAR(100),
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    client_tier VARCHAR(20) DEFAULT 'standard',
    priority_level INTEGER DEFAULT 5,
    
    -- Relationships
    account_manager_id INTEGER,
    technical_lead_id INTEGER,
    
    -- Integration
    external_client_id VARCHAR(100),
    external_system_name VARCHAR(100),
    
    -- Security
    access_level VARCHAR(50) DEFAULT 'standard',
    allowed_ips JSON,
    requires_2fa BOOLEAN DEFAULT FALSE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    last_contact_date DATE,
    deleted_at TIMESTAMP NULL,
    deleted_by INTEGER,
    
    FOREIGN KEY (account_manager_id) REFERENCES framework_users(id),
    FOREIGN KEY (technical_lead_id) REFERENCES framework_users(id),
    FOREIGN KEY (created_by) REFERENCES framework_users(id),
    FOREIGN KEY (deleted_by) REFERENCES framework_users(id)
);

-- Projects table (client's projects)
CREATE TABLE IF NOT EXISTS framework_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    project_key VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    
    -- Project Info
    description TEXT,
    summary TEXT,
    project_type VARCHAR(50) DEFAULT 'development',
    methodology VARCHAR(100) DEFAULT 'agile',
    
    -- Scope
    objectives JSON,
    deliverables JSON,
    success_criteria JSON,
    assumptions JSON,
    constraints JSON,
    risks JSON,
    
    -- Timeline
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2) DEFAULT 0,
    
    -- Budget
    budget_amount DECIMAL(15,2),
    budget_currency VARCHAR(10) DEFAULT 'BRL',
    hourly_rate DECIMAL(10,2),
    fixed_price DECIMAL(15,2),
    
    -- Status
    status VARCHAR(50) DEFAULT 'planning',
    priority INTEGER DEFAULT 5,
    health_status VARCHAR(20) DEFAULT 'green',
    completion_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- Team
    project_manager_id INTEGER,
    technical_lead_id INTEGER,
    client_contact_id INTEGER,
    
    -- Integration
    repository_url VARCHAR(500),
    deployment_url VARCHAR(500),
    documentation_url VARCHAR(500),
    external_project_id VARCHAR(100),
    github_project_id VARCHAR(100),
    jira_project_key VARCHAR(50),
    
    -- Communication
    slack_channel VARCHAR(100),
    teams_channel VARCHAR(100),
    notification_settings JSON,
    
    -- Security
    visibility VARCHAR(20) DEFAULT 'client',
    access_level VARCHAR(50) DEFAULT 'standard',
    
    -- Gamification
    total_points_earned INTEGER DEFAULT 0,
    complexity_score DECIMAL(5,2),
    quality_score DECIMAL(5,2),
    
    -- Metadata
    custom_fields JSON,
    tags JSON,
    labels JSON,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    deleted_at TIMESTAMP NULL,
    deleted_by INTEGER,
    
    FOREIGN KEY (client_id) REFERENCES framework_clients(id) ON DELETE CASCADE,
    FOREIGN KEY (project_manager_id) REFERENCES framework_users(id),
    FOREIGN KEY (technical_lead_id) REFERENCES framework_users(id),
    FOREIGN KEY (created_by) REFERENCES framework_users(id),
    FOREIGN KEY (deleted_by) REFERENCES framework_users(id),
    
    UNIQUE(client_id, project_key)
);

-- ==================================================================================
-- EPICS AND TASKS
-- ==================================================================================

-- Epics table (project's epics)
CREATE TABLE IF NOT EXISTS framework_epics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    epic_key VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    duration_days INTEGER,
    
    -- Duration System Extensions (v4)
    summary TEXT,
    epic_number VARCHAR(50),
    duration_description VARCHAR(255),
    duration_text VARCHAR(100),
    business_days INTEGER,
    calendar_days INTEGER,
    
    -- Sync Extensions (v5)
    planned_start_date DATE,
    planned_end_date DATE,
    calculated_duration_days INTEGER,
    dependencies JSON,
    blockers JSON,
    
    -- Gamification
    points_earned INTEGER DEFAULT 0,
    difficulty_level VARCHAR(20) DEFAULT 'medium',
    completion_bonus INTEGER DEFAULT 0,
    
    -- GitHub Integration
    github_issue_id INTEGER,
    github_milestone_id INTEGER,
    github_project_id VARCHAR(50),
    
    -- Time Tracking
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2) DEFAULT 0,
    
    -- Multi-user
    created_by INTEGER,
    assigned_to INTEGER,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    deleted_at TIMESTAMP NULL,
    
    FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES framework_users(id),
    FOREIGN KEY (assigned_to) REFERENCES framework_users(id)
);

-- Tasks table (epic's tasks)
CREATE TABLE IF NOT EXISTS framework_tasks (
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

-- ==================================================================================
-- GAMIFICATION SYSTEM
-- ==================================================================================

-- Achievement types
CREATE TABLE IF NOT EXISTS achievement_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    category VARCHAR(50) DEFAULT 'general',
    points_value INTEGER DEFAULT 10,
    difficulty VARCHAR(20) DEFAULT 'medium',
    
    -- Requirements
    requirement_type VARCHAR(50),
    requirement_value INTEGER,
    requirement_json JSON,
    
    -- Display
    badge_color VARCHAR(20),
    display_order INTEGER DEFAULT 100,
    is_secret BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User achievements
CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_id INTEGER NOT NULL,
    
    -- Progress
    progress_value INTEGER DEFAULT 0,
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unlocked_at TIMESTAMP NULL,
    notified_at TIMESTAMP NULL,
    
    -- Metadata
    context_data JSON,
    epic_id INTEGER,
    task_id INTEGER,
    
    FOREIGN KEY (user_id) REFERENCES framework_users(id),
    FOREIGN KEY (achievement_id) REFERENCES achievement_types(id),
    FOREIGN KEY (epic_id) REFERENCES framework_epics(id),
    FOREIGN KEY (task_id) REFERENCES framework_tasks(id),
    
    UNIQUE(user_id, achievement_id)
);

-- User streaks
CREATE TABLE IF NOT EXISTS user_streaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    streak_type VARCHAR(50) NOT NULL,
    
    -- Streak data
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    total_days INTEGER DEFAULT 0,
    
    -- Dates
    start_date DATE NOT NULL,
    last_activity_date DATE,
    streak_broken_date DATE,
    
    -- Metadata
    metadata JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES framework_users(id),
    UNIQUE(user_id, streak_type)
);

-- ==================================================================================
-- TRACKING AND INTEGRATION
-- ==================================================================================

-- Work sessions
CREATE TABLE IF NOT EXISTS work_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    task_id INTEGER,
    epic_id INTEGER,
    
    -- Session data
    session_type VARCHAR(50) DEFAULT 'work',
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    
    -- Productivity metrics
    focus_score DECIMAL(3,2),
    interruptions_count INTEGER DEFAULT 0,
    lines_of_code INTEGER,
    commits_count INTEGER DEFAULT 0,
    
    -- TDAH support
    energy_level INTEGER CHECK(energy_level BETWEEN 1 AND 10),
    mood_rating INTEGER CHECK(mood_rating BETWEEN 1 AND 10),
    notes TEXT,
    
    -- Metadata
    tools_used JSON,
    files_modified JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES framework_users(id),
    FOREIGN KEY (task_id) REFERENCES framework_tasks(id),
    FOREIGN KEY (epic_id) REFERENCES framework_epics(id)
);

-- GitHub sync log
CREATE TABLE IF NOT EXISTS github_sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type VARCHAR(50) NOT NULL,
    sync_status VARCHAR(20) NOT NULL,
    
    -- Sync details
    items_synced INTEGER DEFAULT 0,
    items_created INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    
    -- Errors
    error_message TEXT,
    error_details JSON,
    
    -- Timing
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Metadata
    sync_metadata JSON,
    triggered_by INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (triggered_by) REFERENCES framework_users(id)
);

-- System settings
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) DEFAULT 'string',
    
    -- Metadata
    category VARCHAR(50) DEFAULT 'general',
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE,
    is_editable BOOLEAN DEFAULT TRUE,
    
    -- Validation
    validation_rules JSON,
    allowed_values JSON,
    default_value TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER,
    
    FOREIGN KEY (updated_by) REFERENCES framework_users(id)
);

-- ==================================================================================
-- PERFORMANCE INDEXES
-- ==================================================================================

-- Client indexes
CREATE INDEX IF NOT EXISTS idx_clients_key ON framework_clients(client_key);
CREATE INDEX IF NOT EXISTS idx_clients_status ON framework_clients(status, deleted_at);
CREATE INDEX IF NOT EXISTS idx_clients_tier_priority ON framework_clients(client_tier, priority_level);

-- Project indexes
CREATE INDEX IF NOT EXISTS idx_projects_client ON framework_projects(client_id, deleted_at);
CREATE INDEX IF NOT EXISTS idx_projects_key ON framework_projects(project_key);
CREATE INDEX IF NOT EXISTS idx_projects_status ON framework_projects(status, deleted_at);
CREATE INDEX IF NOT EXISTS idx_projects_health ON framework_projects(health_status, status);

-- Epic indexes
CREATE INDEX IF NOT EXISTS idx_epics_project ON framework_epics(project_id, deleted_at);
CREATE INDEX IF NOT EXISTS idx_epics_status ON framework_epics(status);
CREATE INDEX IF NOT EXISTS idx_epics_key ON framework_epics(epic_key);
CREATE INDEX IF NOT EXISTS idx_epics_project_status ON framework_epics(project_id, status);

-- Task indexes
CREATE INDEX IF NOT EXISTS idx_tasks_epic ON framework_tasks(epic_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON framework_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON framework_tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_tdd ON framework_tasks(tdd_phase);

-- Session indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user ON work_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_task ON work_sessions(task_id);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON work_sessions(start_time);

-- Achievement indexes
CREATE INDEX IF NOT EXISTS idx_achievements_user ON user_achievements(user_id, is_completed);
CREATE INDEX IF NOT EXISTS idx_achievements_type ON user_achievements(achievement_id);

-- ==================================================================================
-- VIEWS FOR REPORTING AND DASHBOARDS
-- ==================================================================================

-- Complete hierarchy view
CREATE VIEW IF NOT EXISTS hierarchy_overview AS
SELECT 
    c.id as client_id,
    c.client_key,
    c.name as client_name,
    c.status as client_status,
    
    p.id as project_id,
    p.project_key,
    p.name as project_name,
    p.status as project_status,
    p.health_status as project_health,
    
    e.id as epic_id,
    e.epic_key,
    e.name as epic_name,
    e.status as epic_status,
    
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    ROUND(
        COUNT(CASE WHEN t.status = 'completed' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(t.id), 0), 2
    ) as completion_percentage
    
FROM framework_clients c
LEFT JOIN framework_projects p ON c.id = p.client_id AND p.deleted_at IS NULL
LEFT JOIN framework_epics e ON p.id = e.project_id AND e.deleted_at IS NULL
LEFT JOIN framework_tasks t ON e.id = t.epic_id
WHERE c.deleted_at IS NULL
GROUP BY c.id, p.id, e.id
ORDER BY c.name, p.name, e.epic_key;

-- Client dashboard view
CREATE VIEW IF NOT EXISTS client_dashboard AS
SELECT 
    c.id as client_id,
    c.name as client_name,
    c.client_tier,
    
    COUNT(DISTINCT p.id) as total_projects,
    COUNT(DISTINCT CASE WHEN p.status = 'active' THEN p.id END) as active_projects,
    
    COUNT(DISTINCT e.id) as total_epics,
    COUNT(DISTINCT CASE WHEN e.status = 'completed' THEN e.id END) as completed_epics,
    
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    
    COALESCE(SUM(p.actual_hours), 0) as total_hours_logged,
    COALESCE(SUM(p.budget_amount), 0) as total_budget
    
FROM framework_clients c
LEFT JOIN framework_projects p ON c.id = p.client_id AND p.deleted_at IS NULL
LEFT JOIN framework_epics e ON p.id = e.project_id AND e.deleted_at IS NULL
LEFT JOIN framework_tasks t ON e.id = t.epic_id
WHERE c.deleted_at IS NULL
GROUP BY c.id
ORDER BY c.name;

-- Project dashboard view
CREATE VIEW IF NOT EXISTS project_dashboard AS
SELECT 
    p.id as project_id,
    p.name as project_name,
    p.status as project_status,
    p.health_status,
    
    c.name as client_name,
    
    COUNT(DISTINCT e.id) as total_epics,
    COUNT(DISTINCT CASE WHEN e.status = 'completed' THEN e.id END) as completed_epics,
    
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    
    p.estimated_hours,
    p.actual_hours,
    p.budget_amount,
    
    ROUND(
        COUNT(CASE WHEN t.status = 'completed' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(t.id), 0), 2
    ) as calculated_completion_percentage
    
FROM framework_projects p
INNER JOIN framework_clients c ON p.client_id = c.id AND c.deleted_at IS NULL
LEFT JOIN framework_epics e ON p.id = e.project_id AND e.deleted_at IS NULL
LEFT JOIN framework_tasks t ON e.id = t.epic_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, c.id
ORDER BY c.name, p.name;

-- ==================================================================================
-- TRIGGERS FOR DATA INTEGRITY
-- ==================================================================================

-- Update timestamp triggers
CREATE TRIGGER IF NOT EXISTS update_clients_timestamp 
AFTER UPDATE ON framework_clients
BEGIN
    UPDATE framework_clients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_projects_timestamp 
AFTER UPDATE ON framework_projects
BEGIN
    UPDATE framework_projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_epics_timestamp 
AFTER UPDATE ON framework_epics
BEGIN
    UPDATE framework_epics SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_tasks_timestamp 
AFTER UPDATE ON framework_tasks
BEGIN
    UPDATE framework_tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ==================================================================================
-- INITIAL DATA
-- ==================================================================================

-- Insert default achievement types if not exists
INSERT OR IGNORE INTO achievement_types (code, name, description, points_value, category) VALUES
('FIRST_EPIC_COMPLETE', 'First Epic', 'Complete your first epic', 50, 'milestone'),
('TDD_MASTER', 'TDD Master', 'Complete 100 TDD cycles', 100, 'methodology'),
('SPRINT_CHAMPION', 'Sprint Champion', 'Complete a sprint on time', 75, 'productivity'),
('FOCUS_WARRIOR', 'Focus Warrior', 'Maintain focus for 4 hours', 30, 'focus'),
('EARLY_BIRD', 'Early Bird', 'Start work before 7 AM', 20, 'schedule'),
('NIGHT_OWL', 'Night Owl', 'Work after midnight', 20, 'schedule'),
('BUG_SQUASHER', 'Bug Squasher', 'Fix 50 bugs', 80, 'quality'),
('REFACTOR_EXPERT', 'Refactor Expert', 'Complete 25 refactor tasks', 60, 'quality'),
('DOCUMENTATION_HERO', 'Documentation Hero', 'Document 20 features', 40, 'documentation'),
('COLLABORATION_STAR', 'Collaboration Star', 'Review 30 pull requests', 50, 'teamwork');

-- Insert default system settings
INSERT OR IGNORE INTO system_settings (setting_key, setting_value, category, description) VALUES
('app_version', '1.2.1', 'system', 'Application version'),
('default_theme', 'dark', 'ui', 'Default UI theme'),
('session_timeout', '3600', 'security', 'Session timeout in seconds'),
('max_upload_size', '10485760', 'limits', 'Maximum file upload size in bytes'),
('enable_notifications', 'true', 'features', 'Enable system notifications'),
('default_language', 'pt-BR', 'localization', 'Default system language');

-- ==================================================================================
-- SCHEMA METADATA
-- ==================================================================================

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Record this schema version
INSERT INTO schema_versions (version, description) VALUES
('FINAL_v1.0', 'Consolidated production-ready schema with complete Client-Project-Epic-Task hierarchy');

-- ==================================================================================
-- END OF SCHEMA
-- ==================================================================================