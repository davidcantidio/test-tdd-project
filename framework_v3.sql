-- FRAMEWORK DATABASE SCHEMA V3 - COMPLETO COM GAMIFICAÇÃO
-- Baseado na auditoria da Fase 1.1.1 e expandido para Fase 1.1.2
-- Data: 2025-08-12

-- =============================================================================
-- CORE TABLES - Multi-user Framework
-- =============================================================================

-- Tabela de usuários (preparação multi-user)
CREATE TABLE IF NOT EXISTS framework_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    github_username VARCHAR(100),
    preferences JSON,
    
    -- Gamificação user-level
    total_points INTEGER DEFAULT 0,
    current_level INTEGER DEFAULT 1,
    experience_points INTEGER DEFAULT 0,
    
    -- Status e auditoria
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

-- =============================================================================
-- GAMIFICATION SYSTEM - Achievement Engine
-- =============================================================================

-- Tipos de achievements disponíveis
CREATE TABLE IF NOT EXISTS achievement_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- 'productivity', 'consistency', 'quality', 'social'
    
    -- Configuração do achievement
    points_reward INTEGER DEFAULT 0,
    icon_name VARCHAR(50),
    rarity VARCHAR(20) DEFAULT 'common', -- 'common', 'rare', 'epic', 'legendary'
    
    -- Condições de unlock
    unlock_criteria JSON, -- Condições complexas em JSON
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Achievements desbloqueados pelos usuários
CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_id INTEGER NOT NULL,
    
    -- Contexto do unlock
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unlocked_by_task_id INTEGER, -- Task que triggou o achievement
    unlocked_by_epic_id INTEGER, -- Epic que triggou o achievement
    
    -- Dados contextuais
    context_data JSON, -- Dados adicionais do momento do unlock
    points_earned INTEGER DEFAULT 0,
    
    FOREIGN KEY (user_id) REFERENCES framework_users(id),
    FOREIGN KEY (achievement_id) REFERENCES achievement_types(id),
    FOREIGN KEY (unlocked_by_task_id) REFERENCES framework_tasks(id),
    FOREIGN KEY (unlocked_by_epic_id) REFERENCES framework_epics(id),
    UNIQUE(user_id, achievement_id) -- Um achievement por usuário
);

-- Sistema de streaks de produtividade
CREATE TABLE IF NOT EXISTS user_streaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    streak_type VARCHAR(50) NOT NULL, -- 'daily_tasks', 'tdd_cycles', 'focus_sessions'
    
    -- Dados do streak
    current_count INTEGER DEFAULT 0,
    best_count INTEGER DEFAULT 0,
    last_activity_date DATE,
    
    -- Bonus e rewards
    current_bonus_multiplier DECIMAL(3,2) DEFAULT 1.0,
    total_bonus_points INTEGER DEFAULT 0,
    
    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES framework_users(id),
    UNIQUE(user_id, streak_type)
);

-- =============================================================================
-- INTEGRATION SYSTEM - External Systems
-- =============================================================================

-- Log de sincronizações com GitHub
CREATE TABLE IF NOT EXISTS github_sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Contexto da sync
    sync_type VARCHAR(50) NOT NULL, -- 'issues', 'projects', 'milestones', 'prs'
    direction VARCHAR(20) NOT NULL, -- 'import', 'export', 'bidirectional'
    
    -- Status da operação
    status VARCHAR(20) NOT NULL, -- 'success', 'error', 'partial'
    records_processed INTEGER DEFAULT 0,
    records_successful INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    
    -- Dados técnicos
    github_api_calls INTEGER DEFAULT 0,
    execution_time_ms INTEGER,
    error_message TEXT,
    
    -- Auditoria
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    triggered_by_user_id INTEGER,
    
    FOREIGN KEY (triggered_by_user_id) REFERENCES framework_users(id)
);

-- Configurações do sistema
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50) NOT NULL,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20) DEFAULT 'string', -- 'string', 'integer', 'boolean', 'json'
    
    -- Metadata
    description TEXT,
    is_user_configurable BOOLEAN DEFAULT FALSE,
    
    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by_user_id INTEGER,
    
    FOREIGN KEY (updated_by_user_id) REFERENCES framework_users(id),
    UNIQUE(category, setting_key)
);

-- =============================================================================
-- PERFORMANCE INDEXES
-- =============================================================================

-- Índices para performance otimizada
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON framework_tasks(assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_tasks_epic_phase ON framework_tasks(epic_id, tdd_phase);
CREATE INDEX IF NOT EXISTS idx_tasks_github ON framework_tasks(github_issue_number);

CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON work_sessions(user_id, DATE(start_time));
CREATE INDEX IF NOT EXISTS idx_sessions_task_duration ON work_sessions(task_id, duration_minutes);

CREATE INDEX IF NOT EXISTS idx_epics_github ON framework_epics(github_project_id, github_issue_id);
CREATE INDEX IF NOT EXISTS idx_epics_status_priority ON framework_epics(status, priority);

CREATE INDEX IF NOT EXISTS idx_achievements_user ON user_achievements(user_id, unlocked_at);
CREATE INDEX IF NOT EXISTS idx_achievements_type ON user_achievements(achievement_id);

CREATE INDEX IF NOT EXISTS idx_streaks_user_type ON user_streaks(user_id, streak_type);
CREATE INDEX IF NOT EXISTS idx_streaks_activity ON user_streaks(last_activity_date);

CREATE INDEX IF NOT EXISTS idx_sync_log_type_status ON github_sync_log(sync_type, status);
CREATE INDEX IF NOT EXISTS idx_sync_log_date ON github_sync_log(DATE(started_at));

-- =============================================================================
-- TRIGGERS - Automated Gamification
-- =============================================================================

-- Trigger para atualizar pontos do usuário quando task é completada
CREATE TRIGGER IF NOT EXISTS update_user_points_on_task_complete
    AFTER UPDATE OF status ON framework_tasks
    WHEN NEW.status = 'completed' AND OLD.status != 'completed'
BEGIN
    UPDATE framework_users 
    SET total_points = total_points + NEW.points_earned,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.assigned_to;
END;

-- Trigger para calcular pontos da task baseado na dificuldade
CREATE TRIGGER IF NOT EXISTS calculate_task_points_on_complete
    AFTER UPDATE OF status ON framework_tasks
    WHEN NEW.status = 'completed' AND OLD.status != 'completed'
BEGIN
    UPDATE framework_tasks
    SET points_earned = CASE 
        WHEN NEW.difficulty_modifier IS NULL THEN NEW.story_points * 10
        ELSE CAST(NEW.story_points * 10 * NEW.difficulty_modifier AS INTEGER)
    END,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Trigger para atualizar streak diário
CREATE TRIGGER IF NOT EXISTS update_daily_streak
    AFTER UPDATE OF status ON framework_tasks
    WHEN NEW.status = 'completed' AND OLD.status != 'completed'
BEGIN
    INSERT OR REPLACE INTO user_streaks (
        user_id, streak_type, current_count, last_activity_date, updated_at
    )
    SELECT 
        NEW.assigned_to,
        'daily_tasks',
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM user_streaks 
                WHERE user_id = NEW.assigned_to 
                AND streak_type = 'daily_tasks'
                AND DATE(last_activity_date) = DATE('now', '-1 day')
            ) THEN (
                SELECT current_count + 1 FROM user_streaks 
                WHERE user_id = NEW.assigned_to AND streak_type = 'daily_tasks'
            )
            WHEN EXISTS (
                SELECT 1 FROM user_streaks 
                WHERE user_id = NEW.assigned_to 
                AND streak_type = 'daily_tasks'
                AND DATE(last_activity_date) = DATE('now')
            ) THEN (
                SELECT current_count FROM user_streaks 
                WHERE user_id = NEW.assigned_to AND streak_type = 'daily_tasks'
            )
            ELSE 1
        END,
        DATE('now'),
        CURRENT_TIMESTAMP;
END;

-- =============================================================================
-- INITIAL DATA - Default Settings and Achievements
-- =============================================================================

-- Inserir configurações padrão do sistema
INSERT OR REPLACE INTO system_settings (category, setting_key, setting_value, setting_type, description) VALUES
('gamification', 'points_per_story_point', '10', 'integer', 'Points awarded per story point'),
('gamification', 'streak_bonus_multiplier', '1.5', 'decimal', 'Multiplier for streak bonuses'),
('gamification', 'perfectionist_bonus', '25', 'integer', 'Extra points for completing without bugs'),
('github', 'sync_enabled', 'true', 'boolean', 'Enable GitHub synchronization'),
('github', 'auto_sync_interval_hours', '24', 'integer', 'Hours between automatic syncs'),
('performance', 'max_work_session_minutes', '480', 'integer', 'Maximum work session duration'),
('performance', 'focus_score_threshold', '7', 'integer', 'Minimum focus score for quality bonus');

-- Inserir tipos de achievements padrão
INSERT OR REPLACE INTO achievement_types (code, name, description, category, points_reward, rarity) VALUES
('first_task', 'First Steps', 'Complete your first task', 'productivity', 50, 'common'),
('tdd_master', 'TDD Master', 'Complete 10 tasks following TDD cycle', 'quality', 200, 'rare'),
('streak_warrior', 'Streak Warrior', 'Maintain a 7-day completion streak', 'consistency', 300, 'epic'),
('focus_expert', 'Focus Expert', 'Complete 5 high-focus work sessions', 'productivity', 150, 'rare'),
('github_ninja', 'GitHub Ninja', 'Complete 20 tasks with GitHub integration', 'social', 250, 'epic'),
('early_bird', 'Early Bird', 'Complete tasks before 9 AM for 5 days', 'consistency', 100, 'rare'),
('night_owl', 'Night Owl', 'Complete tasks after 10 PM for 5 days', 'consistency', 100, 'rare'),
('perfectionist', 'Perfectionist', 'Complete 10 tasks without any bugs', 'quality', 400, 'legendary'),
('marathon_runner', 'Marathon Runner', 'Work for 6+ hours in a single day', 'productivity', 200, 'epic'),
('team_player', 'Team Player', 'Review 10 other people''s tasks', 'social', 150, 'rare');

-- Inserir usuário padrão para desenvolvimento
INSERT OR REPLACE INTO framework_users (id, username, email, github_username, is_active) 
VALUES (1, 'dev_user', 'dev@example.com', 'devuser', TRUE);

-- =============================================================================
-- VIEWS - Convenience Queries
-- =============================================================================

-- View para dashboard principal
CREATE VIEW IF NOT EXISTS user_dashboard AS
SELECT 
    u.id as user_id,
    u.username,
    u.total_points,
    u.current_level,
    COUNT(DISTINCT t.id) as total_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks,
    COUNT(DISTINCT e.id) as total_epics,
    COALESCE(MAX(s.current_count), 0) as current_streak,
    COUNT(DISTINCT a.id) as achievements_unlocked
FROM framework_users u
LEFT JOIN framework_tasks t ON u.id = t.assigned_to
LEFT JOIN framework_epics e ON u.id = e.assigned_to
LEFT JOIN user_streaks s ON u.id = s.user_id AND s.streak_type = 'daily_tasks'
LEFT JOIN user_achievements a ON u.id = a.user_id
WHERE u.is_active = TRUE
GROUP BY u.id, u.username, u.total_points, u.current_level;

-- View para progress tracking
CREATE VIEW IF NOT EXISTS epic_progress AS
SELECT 
    e.id as epic_id,
    e.epic_key,
    e.name as epic_name,
    e.status as epic_status,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    ROUND(
        COUNT(CASE WHEN t.status = 'completed' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(t.id), 0), 2
    ) as completion_percentage,
    SUM(t.estimate_minutes) as total_estimated_minutes,
    SUM(t.actual_minutes) as total_actual_minutes
FROM framework_epics e
LEFT JOIN framework_tasks t ON e.id = t.epic_id
GROUP BY e.id, e.epic_key, e.name, e.status;