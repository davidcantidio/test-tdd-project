-- Migration 013: Create framework_epic_ai_audit table
-- Date: 2025-09-09
-- Purpose: Persist AI ordering metadata separately from framework_epics

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS framework_epic_ai_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    epic_id INTEGER NOT NULL,
    project_id INTEGER,
    model TEXT,
    version TEXT,
    explainer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (epic_id) REFERENCES framework_epics(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_epic_ai_audit_epic ON framework_epic_ai_audit(epic_id);
CREATE INDEX IF NOT EXISTS idx_epic_ai_audit_project_created ON framework_epic_ai_audit(project_id, created_at DESC);

COMMIT;

