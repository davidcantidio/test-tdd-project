-- SCHEMA APRIMORADO COM GAMIFICAÇÃO E MULTI-USER
-- Baseado na auditoria da Fase 1.1.1

-- Tabela de usuários (preparação multi-user)
CREATE TABLE IF NOT EXISTS framework_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    github_username VARCHAR(100),
    preferences JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tabela de épicos (aprimorada)
CREATE TABLE IF NOT EXISTS framework_epics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    epic_key VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    duration_days INTEGER,
    
    -- Campos de gamificação
    points_earned INTEGER DEFAULT 0,
    difficulty_level VARCHAR(20) DEFAULT 'medium',
    completion_bonus INTEGER DEFAULT 0,
    
    -- Integração GitHub
    github_issue_id INTEGER,
    github_milestone_id INTEGER,
    github_project_id VARCHAR(50),
    
    -- Time tracking integration
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2) DEFAULT 0,
    
    -- Multi-user support
    created_by INTEGER,
    assigned_to INTEGER,
    
    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    deleted_at TIMESTAMP NULL,
    
    FOREIGN KEY (created_by) REFERENCES framework_users(id),
    FOREIGN KEY (assigned_to) REFERENCES framework_users(id)
);

-- Tabela de tasks (aprimorada)
CREATE TABLE IF NOT EXISTS framework_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_key VARCHAR(50) NOT NULL,
    epic_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- TDD e status
    tdd_phase VARCHAR(20) CHECK(tdd_phase IN ('analysis', 'red', 'green', 'refactor', 'review')),
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Estimativas e tracking
    estimate_minutes INTEGER NOT NULL DEFAULT 60,
    actual_minutes INTEGER DEFAULT 0,
    story_points INTEGER DEFAULT 1,
    position INTEGER,
    
    -- Gamificação
    points_earned INTEGER DEFAULT 0,
    difficulty_modifier DECIMAL(3,2) DEFAULT 1.0,
    streak_bonus INTEGER DEFAULT 0,
    perfectionist_bonus INTEGER DEFAULT 0,
    
    -- GitHub integration
    github_issue_number INTEGER,
    github_branch VARCHAR(255),
    github_pr_number INTEGER,
    
    -- Multi-user
    assigned_to INTEGER,
    reviewer_id INTEGER,
    
    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    
    FOREIGN KEY (epic_id) REFERENCES framework_epics(id),
    FOREIGN KEY (assigned_to) REFERENCES framework_users(id),
    FOREIGN KEY (reviewer_id) REFERENCES framework_users(id),
    UNIQUE(epic_id, task_key)
);

-- Tabela de sessões de trabalho (integração com task_timer.db)
CREATE TABLE IF NOT EXISTS work_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER,
    
    -- Session data
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    session_type VARCHAR(20) DEFAULT 'work',
    
    -- Produtividade e TDAH metrics
    focus_score INTEGER,
    interruptions_count INTEGER DEFAULT 0,
    energy_level INTEGER,
    mood_rating INTEGER,
    
    -- Context
    environment VARCHAR(50),
    music_type VARCHAR(50),
    
    -- Integration
    timer_source VARCHAR(20) DEFAULT 'manual',
    
    FOREIGN KEY (task_id) REFERENCES framework_tasks(id),
    FOREIGN KEY (user_id) REFERENCES framework_users(id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON framework_tasks(assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON work_sessions(user_id, DATE(start_time));
CREATE INDEX IF NOT EXISTS idx_epics_github ON framework_epics(github_project_id, github_issue_id);
CREATE INDEX IF NOT EXISTS idx_tasks_github ON framework_tasks(github_issue_number);
