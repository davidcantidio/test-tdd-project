-- Migration: Create performance indexes
-- Date: 2025-01-15
-- Description: Add indexes for heavy queries identified in report.md

-- Client search optimization
CREATE INDEX idx_clients_name_search ON framework_clients(name);
CREATE INDEX idx_clients_status_active ON framework_clients(status) WHERE status = 'active';

-- Project filtering optimization
CREATE INDEX idx_projects_client_status ON framework_projects(client_id, status);
CREATE INDEX idx_projects_created_date ON framework_projects(created_at);

-- Epic progress calculation optimization
CREATE INDEX idx_epics_project_status ON framework_epics(project_id, status);
CREATE INDEX idx_epics_progress_calc ON framework_epics(project_id, status, points_earned);

-- Task query optimization
CREATE INDEX idx_tasks_epic_status ON framework_tasks(epic_id, status);
CREATE INDEX idx_tasks_tdd_phase ON framework_tasks(tdd_phase, status);
