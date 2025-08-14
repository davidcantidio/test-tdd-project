-- ==================================================================================
-- FRAMEWORK DATABASE SCHEMA V6 - HIERARCHICAL CLIENT-PROJECT-EPIC-TASK STRUCTURE
-- Focus: Implement complete Client → Project → Epic → Task hierarchy
-- Date: 2025-08-14
-- Base: framework_v3.sql + schema_extensions_v4.sql + schema_extensions_v5.sql
-- ==================================================================================

-- ==================================================================================
-- PHASE 1: CLIENT-PROJECT HIERARCHY TABLES
-- ==================================================================================

-- ==================================================================================
-- PHASE 1.1: FRAMEWORK_CLIENTS TABLE
-- ==================================================================================

-- Create clients table for top-level organizational hierarchy
CREATE TABLE IF NOT EXISTS framework_clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_key VARCHAR(50) UNIQUE NOT NULL, -- "internal", "acme_corp", "startup_xyz"
    name VARCHAR(255) NOT NULL, -- "Internal Development", "Acme Corporation", "Startup XYZ"
    
    -- Client Information
    description TEXT,
    industry VARCHAR(100), -- "Software", "Healthcare", "Finance", etc.
    company_size VARCHAR(50), -- "startup", "sme", "enterprise"
    
    -- Contact Information
    primary_contact_name VARCHAR(255),
    primary_contact_email VARCHAR(255),
    primary_contact_phone VARCHAR(50),
    
    -- Business Information
    billing_email VARCHAR(255),
    billing_address TEXT,
    tax_id VARCHAR(100), -- CNPJ, VAT, etc.
    
    -- Client Configuration
    timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo',
    currency VARCHAR(10) DEFAULT 'BRL',
    preferred_language VARCHAR(10) DEFAULT 'pt-BR',
    
    -- Client Preferences and Settings
    preferences JSON, -- Client-specific preferences
    custom_fields JSON, -- Extensible custom fields
    
    -- Billing and Commercial
    hourly_rate DECIMAL(10,2), -- Default hourly rate for this client
    contract_type VARCHAR(50) DEFAULT 'time_and_materials', -- "fixed_price", "time_and_materials", "retainer"
    payment_terms VARCHAR(100), -- "NET 30", "NET 15", etc.
    
    -- Status and Lifecycle
    status VARCHAR(50) DEFAULT 'active', -- "active", "inactive", "suspended", "archived"
    client_tier VARCHAR(20) DEFAULT 'standard', -- "basic", "standard", "premium", "enterprise"
    priority_level INTEGER DEFAULT 5, -- 1-10 priority scale
    
    -- Relationship Management
    account_manager_id INTEGER, -- Who manages this client
    technical_lead_id INTEGER, -- Technical point of contact
    
    -- Integration and External Systems
    external_client_id VARCHAR(100), -- ID in external CRM/billing system
    external_system_name VARCHAR(100), -- "Salesforce", "HubSpot", etc.
    
    -- Security and Access Control
    access_level VARCHAR(50) DEFAULT 'standard', -- "basic", "standard", "full", "admin"
    allowed_ips JSON, -- Array of allowed IP addresses/ranges
    requires_2fa BOOLEAN DEFAULT FALSE,
    
    -- Audit and Compliance
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    last_contact_date DATE,
    
    -- Soft delete
    deleted_at TIMESTAMP NULL,
    deleted_by INTEGER,
    
    -- Foreign Keys
    FOREIGN KEY (account_manager_id) REFERENCES framework_users(id),
    FOREIGN KEY (technical_lead_id) REFERENCES framework_users(id),
    FOREIGN KEY (created_by) REFERENCES framework_users(id),
    FOREIGN KEY (deleted_by) REFERENCES framework_users(id)
);

-- ==================================================================================
-- PHASE 1.2: FRAMEWORK_PROJECTS TABLE  
-- ==================================================================================

-- Create projects table for organizing epics within clients
CREATE TABLE IF NOT EXISTS framework_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    project_key VARCHAR(50) NOT NULL, -- "tdd_framework", "mobile_app", "api_redesign"
    name VARCHAR(255) NOT NULL, -- "TDD Framework", "Mobile App Development", etc.
    
    -- Project Information
    description TEXT,
    summary TEXT, -- Executive summary
    project_type VARCHAR(50) DEFAULT 'development', -- "development", "maintenance", "consulting", "research"
    methodology VARCHAR(100) DEFAULT 'agile', -- "agile", "waterfall", "kanban", "scrum"
    
    -- Project Scope and Objectives
    objectives JSON, -- Array of project objectives
    deliverables JSON, -- Array of expected deliverables
    success_criteria JSON, -- Array of success criteria
    assumptions JSON, -- Array of project assumptions
    constraints JSON, -- Array of constraints
    risks JSON, -- Array of identified risks
    
    -- Timeline and Planning
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2) DEFAULT 0,
    
    -- Budget and Commercial
    budget_amount DECIMAL(15,2),
    budget_currency VARCHAR(10) DEFAULT 'BRL',
    hourly_rate DECIMAL(10,2), -- Override client default if needed
    fixed_price DECIMAL(15,2), -- For fixed-price projects
    
    -- Status and Progress
    status VARCHAR(50) DEFAULT 'planning', -- "planning", "active", "on_hold", "completed", "cancelled", "archived"
    priority INTEGER DEFAULT 5, -- 1-10 priority scale
    health_status VARCHAR(20) DEFAULT 'green', -- "green", "yellow", "red"
    completion_percentage DECIMAL(5,2) DEFAULT 0, -- Calculated or manual override
    
    -- Team and Responsibilities
    project_manager_id INTEGER,
    technical_lead_id INTEGER,
    client_contact_id INTEGER, -- Client's primary contact for this project
    
    -- Integration and Tools
    repository_url VARCHAR(500), -- Git repository
    deployment_url VARCHAR(500), -- Production/staging URL
    documentation_url VARCHAR(500), -- Project documentation
    
    -- External System Integration
    external_project_id VARCHAR(100), -- ID in external project management system
    github_project_id VARCHAR(100), -- GitHub Projects V2 ID
    jira_project_key VARCHAR(50), -- JIRA project key
    
    -- Notifications and Communication
    slack_channel VARCHAR(100), -- Dedicated Slack channel
    teams_channel VARCHAR(100), -- Microsoft Teams channel
    notification_settings JSON, -- Custom notification preferences
    
    -- Security and Access
    visibility VARCHAR(20) DEFAULT 'client', -- "public", "client", "team", "private"
    access_level VARCHAR(50) DEFAULT 'standard',
    
    -- Gamification and Metrics
    total_points_earned INTEGER DEFAULT 0,
    complexity_score DECIMAL(5,2), -- Project complexity (1-10)
    quality_score DECIMAL(5,2), -- Project quality metrics
    
    -- Custom Fields and Metadata
    custom_fields JSON, -- Extensible custom fields
    tags JSON, -- Array of project tags
    labels JSON, -- Array of labels for filtering
    
    -- Audit and Compliance
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    
    -- Soft delete
    deleted_at TIMESTAMP NULL,
    deleted_by INTEGER,
    
    -- Foreign Keys
    FOREIGN KEY (client_id) REFERENCES framework_clients(id) ON DELETE CASCADE,
    FOREIGN KEY (project_manager_id) REFERENCES framework_users(id),
    FOREIGN KEY (technical_lead_id) REFERENCES framework_users(id),
    FOREIGN KEY (created_by) REFERENCES framework_users(id),
    FOREIGN KEY (deleted_by) REFERENCES framework_users(id),
    
    -- Unique constraint for project key within client
    UNIQUE(client_id, project_key)
);

-- ==================================================================================
-- PHASE 1.3: MODIFY FRAMEWORK_EPICS FOR PROJECT RELATIONSHIP
-- ==================================================================================

-- Add project_id foreign key to framework_epics
ALTER TABLE framework_epics ADD COLUMN project_id INTEGER;

-- Add foreign key constraint (will be enforced after data migration)
-- This will be added as a separate step after migrating existing data

-- ==================================================================================
-- PHASE 1.4: PERFORMANCE INDEXES FOR HIERARCHICAL QUERIES
-- ==================================================================================

-- Indexes for framework_clients table
CREATE INDEX IF NOT EXISTS idx_clients_key ON framework_clients(client_key);
CREATE INDEX IF NOT EXISTS idx_clients_status ON framework_clients(status, deleted_at);
CREATE INDEX IF NOT EXISTS idx_clients_tier_priority ON framework_clients(client_tier, priority_level);
CREATE INDEX IF NOT EXISTS idx_clients_account_manager ON framework_clients(account_manager_id);
CREATE INDEX IF NOT EXISTS idx_clients_contact_date ON framework_clients(last_contact_date);

-- Indexes for framework_projects table
CREATE INDEX IF NOT EXISTS idx_projects_client ON framework_projects(client_id, deleted_at);
CREATE INDEX IF NOT EXISTS idx_projects_key ON framework_projects(project_key);
CREATE INDEX IF NOT EXISTS idx_projects_status ON framework_projects(status, deleted_at);
CREATE INDEX IF NOT EXISTS idx_projects_dates ON framework_projects(planned_start_date, planned_end_date);
CREATE INDEX IF NOT EXISTS idx_projects_manager ON framework_projects(project_manager_id);
CREATE INDEX IF NOT EXISTS idx_projects_health ON framework_projects(health_status, status);
CREATE INDEX IF NOT EXISTS idx_projects_completion ON framework_projects(completion_percentage);

-- Indexes for hierarchical queries
CREATE INDEX IF NOT EXISTS idx_epics_project ON framework_epics(project_id, deleted_at);
CREATE INDEX IF NOT EXISTS idx_epics_project_status ON framework_epics(project_id, status);

-- Composite indexes for common hierarchy queries
CREATE INDEX IF NOT EXISTS idx_hierarchy_client_project_epic ON framework_epics(project_id, id) 
WHERE project_id IS NOT NULL;

-- ==================================================================================
-- PHASE 1.5: VIEWS FOR HIERARCHICAL QUERIES AND AGGREGATIONS
-- ==================================================================================

-- View for complete hierarchy with client, project, epic information
CREATE VIEW IF NOT EXISTS hierarchy_overview AS
SELECT 
    -- Client information
    c.id as client_id,
    c.client_key,
    c.name as client_name,
    c.status as client_status,
    c.client_tier,
    
    -- Project information
    p.id as project_id,
    p.project_key,
    p.name as project_name,
    p.status as project_status,
    p.health_status as project_health,
    p.completion_percentage as project_completion,
    
    -- Epic information
    e.id as epic_id,
    e.epic_key,
    e.name as epic_name,
    e.status as epic_status,
    e.calculated_duration_days,
    
    -- Calculated aggregations
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    ROUND(
        COUNT(CASE WHEN t.status = 'completed' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(t.id), 0), 2
    ) as epic_completion_percentage,
    
    -- Timeline information
    p.planned_start_date,
    p.planned_end_date,
    e.planned_start_date as epic_planned_start,
    e.planned_end_date as epic_planned_end
    
FROM framework_clients c
LEFT JOIN framework_projects p ON c.id = p.client_id AND p.deleted_at IS NULL
LEFT JOIN framework_epics e ON p.id = e.project_id AND e.deleted_at IS NULL
LEFT JOIN framework_tasks t ON e.id = t.epic_id
WHERE c.deleted_at IS NULL
GROUP BY c.id, p.id, e.id
ORDER BY c.name, p.name, e.epic_key;

-- View for client summary dashboard
CREATE VIEW IF NOT EXISTS client_dashboard AS
SELECT 
    c.id as client_id,
    c.client_key,
    c.name as client_name,
    c.status as client_status,
    c.client_tier,
    c.hourly_rate,
    
    -- Project aggregations
    COUNT(DISTINCT p.id) as total_projects,
    COUNT(DISTINCT CASE WHEN p.status = 'active' THEN p.id END) as active_projects,
    COUNT(DISTINCT CASE WHEN p.status = 'completed' THEN p.id END) as completed_projects,
    
    -- Epic aggregations
    COUNT(DISTINCT e.id) as total_epics,
    COUNT(DISTINCT CASE WHEN e.status IN ('in_progress', 'pending') THEN e.id END) as active_epics,
    COUNT(DISTINCT CASE WHEN e.status = 'completed' THEN e.id END) as completed_epics,
    
    -- Task aggregations
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as in_progress_tasks,
    
    -- Time and budget aggregations
    COALESCE(SUM(p.actual_hours), 0) as total_hours_logged,
    COALESCE(SUM(p.budget_amount), 0) as total_budget,
    
    -- Points and gamification
    COALESCE(SUM(e.points_earned), 0) as total_points_earned,
    
    -- Timeline information
    MIN(p.planned_start_date) as earliest_project_start,
    MAX(p.planned_end_date) as latest_project_end,
    
    -- Health and status indicators
    COUNT(CASE WHEN p.health_status = 'red' THEN 1 END) as projects_at_risk,
    AVG(p.completion_percentage) as avg_project_completion
    
FROM framework_clients c
LEFT JOIN framework_projects p ON c.id = p.client_id AND p.deleted_at IS NULL
LEFT JOIN framework_epics e ON p.id = e.project_id AND e.deleted_at IS NULL
LEFT JOIN framework_tasks t ON e.id = t.epic_id
WHERE c.deleted_at IS NULL
GROUP BY c.id, c.client_key, c.name, c.status, c.client_tier, c.hourly_rate
ORDER BY c.name;

-- View for project dashboard
CREATE VIEW IF NOT EXISTS project_dashboard AS
SELECT 
    p.id as project_id,
    p.project_key,
    p.name as project_name,
    p.status as project_status,
    p.health_status,
    p.completion_percentage,
    
    -- Client information
    c.id as client_id,
    c.name as client_name,
    c.client_tier,
    
    -- Epic aggregations
    COUNT(DISTINCT e.id) as total_epics,
    COUNT(DISTINCT CASE WHEN e.status = 'completed' THEN e.id END) as completed_epics,
    COUNT(DISTINCT CASE WHEN e.status IN ('in_progress', 'pending') THEN e.id END) as active_epics,
    
    -- Task aggregations
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as in_progress_tasks,
    
    -- Time tracking
    p.estimated_hours,
    p.actual_hours,
    COALESCE(SUM(t.estimate_minutes), 0) / 60.0 as estimated_task_hours,
    COALESCE(SUM(t.actual_minutes), 0) / 60.0 as actual_task_hours,
    
    -- Budget and commercial
    p.budget_amount,
    p.hourly_rate,
    
    -- Timeline
    p.planned_start_date,
    p.planned_end_date,
    p.actual_start_date,
    p.actual_end_date,
    
    -- Progress calculations
    ROUND(
        COUNT(CASE WHEN t.status = 'completed' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(t.id), 0), 2
    ) as calculated_completion_percentage,
    
    -- Points and quality
    COALESCE(SUM(e.points_earned), 0) as total_points_earned,
    p.complexity_score,
    p.quality_score
    
FROM framework_projects p
INNER JOIN framework_clients c ON p.client_id = c.id AND c.deleted_at IS NULL
LEFT JOIN framework_epics e ON p.id = e.project_id AND e.deleted_at IS NULL
LEFT JOIN framework_tasks t ON e.id = t.epic_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, c.id
ORDER BY c.name, p.name;

-- ==================================================================================
-- PHASE 1: COMPLETION NOTES
-- ==================================================================================

-- Schema extensions v6 Phase 1 completed:
-- ✅ Created framework_clients table with comprehensive client management
-- ✅ Created framework_projects table with full project lifecycle support
-- ✅ Added project_id column to framework_epics (FK constraint pending migration)
-- ✅ Created performance indexes for hierarchical queries
-- ✅ Created comprehensive views for dashboard and reporting

-- Features included:
-- ✅ Complete client information and contact management
-- ✅ Billing and commercial data structure
-- ✅ Project lifecycle management with status tracking
-- ✅ Budget and time tracking integration
-- ✅ Team assignment and responsibility management
-- ✅ External system integration support
-- ✅ Security and access control framework
-- ✅ Comprehensive audit trail
-- ✅ Soft delete for data preservation
-- ✅ Extensible custom fields and metadata

-- Next Phase: Data migration and constraint creation
-- Performance Targets: All queries < 10ms with proper indexing
-- Data Integrity: Full referential integrity with cascading rules