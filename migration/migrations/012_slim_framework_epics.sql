-- Migration 012: Slim down framework_epics and remove unused tables/columns
-- Date: 2025-09-09
-- Purpose:
--   - Remove rarely used/heavy columns from framework_epics
--   - Drop legacy table framework_clients (confirmed unused)
--   - Keep data for essential fields; columns removed will be lost
-- Notes:
--   - SQLite não suporta DROP COLUMN; recriamos a tabela com as colunas desejadas
--   - Recrie índices e gatilhos essenciais após a troca

BEGIN TRANSACTION;

-- 1) Criar nova tabela enxuta (mantendo campos essenciais)
CREATE TABLE IF NOT EXISTS framework_epics_new (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50),
    priority INTEGER,
    duration_days INTEGER,
    points_earned INTEGER,
    completion_bonus INTEGER,
    github_issue_id INTEGER,
    github_milestone_id INTEGER,
    github_project_id VARCHAR(50),
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2),
    created_by INTEGER,
    assigned_to INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP,
    deleted_at TIMESTAMP,
    sync_status VARCHAR(20),
    last_json_sync TIMESTAMP,
    json_checksum VARCHAR(64),
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    calculated_duration_days DECIMAL(5,2),
    duration_description VARCHAR(50),
    duration_unit VARCHAR(20),
    labels JSON,
    tdd_enabled BOOLEAN,
    methodology VARCHAR(100),
    project_id INTEGER,
    points_value INTEGER,
    due_date DATE,
    icon VARCHAR(50),
    product_vision_id INTEGER,
    sort_order INTEGER,
    ai_score REAL,
    ai_sort_version TEXT,
    ai_sort_explainer TEXT,
    order_locked INTEGER NOT NULL DEFAULT 0,
    effort_estimate INTEGER,
    tdd_phase TEXT,
    tdd_order INTEGER,
    complexity_score DECIMAL(5,2)
);

-- 2) Copiar dados preservando colunas
INSERT INTO framework_epics_new (
    id, name, description, status, priority, duration_days, points_earned,
    completion_bonus, github_issue_id, github_milestone_id, github_project_id,
    estimated_hours, actual_hours, created_by, assigned_to, created_at, updated_at,
    completed_at, deleted_at, sync_status, last_json_sync, json_checksum,
    planned_start_date, planned_end_date, actual_start_date, actual_end_date,
    calculated_duration_days, duration_description, duration_unit, labels,
    tdd_enabled, methodology, project_id, points_value, due_date, icon,
    product_vision_id, sort_order, ai_score, ai_sort_version, ai_sort_explainer,
    order_locked, effort_estimate, tdd_phase, tdd_order, complexity_score
)
SELECT
    id, name, description, status, priority, duration_days, points_earned,
    completion_bonus, github_issue_id, github_milestone_id, github_project_id,
    estimated_hours, actual_hours, created_by, assigned_to, created_at, updated_at,
    completed_at, deleted_at, sync_status, last_json_sync, json_checksum,
    planned_start_date, planned_end_date, actual_start_date, actual_end_date,
    calculated_duration_days, duration_description, duration_unit, labels,
    tdd_enabled, methodology, project_id, points_value, due_date, icon,
    product_vision_id, sort_order, ai_score, ai_sort_version, ai_sort_explainer,
    order_locked, effort_estimate, tdd_phase, tdd_order, complexity_score
FROM framework_epics;

-- 3) Trocar tabelas
ALTER TABLE framework_epics RENAME TO framework_epics_old;
ALTER TABLE framework_epics_new RENAME TO framework_epics;

-- 4) Índices essenciais
CREATE INDEX IF NOT EXISTS idx_epics_project_sort ON framework_epics(project_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_epics_due_date ON framework_epics(due_date);
CREATE INDEX IF NOT EXISTS idx_epics_points_value ON framework_epics(points_value);

-- 5) Remover tabela legada não utilizada
DROP TABLE IF EXISTS framework_clients;

COMMIT;

-- Observações:
-- - Colunas removidas: epic_key, epic_template_version, summary,
--   goals, definition_of_done, quality_gates, automation_hooks, checklist_epic_level
-- - Se existir algum trigger ligado à tabela antiga, recrie-o apontando para a nova estrutura
