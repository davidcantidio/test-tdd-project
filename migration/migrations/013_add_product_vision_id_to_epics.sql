-- Migration 013: Add product_vision_id to framework_epics with FK
-- Rebuild table to include FK and preserve data

BEGIN TRANSACTION;

CREATE TABLE framework_epics_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    product_vision_id INTEGER,
    epic_key TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 3,
    ai_generated INTEGER DEFAULT 0,
    ai_confidence REAL DEFAULT 0.0,
    complexity_score REAL DEFAULT 3.0,
    effort_estimate INTEGER DEFAULT 5,
    sort_order INTEGER DEFAULT 0,
    unblock_potential INTEGER DEFAULT 0,
    critical_path_weight REAL DEFAULT 0.0,
    tdd_phase TEXT DEFAULT 'analysis',
    tdd_order INTEGER DEFAULT 1,
    business_value INTEGER DEFAULT 5,
    risk_mitigation INTEGER DEFAULT 5,
    strategic_alignment INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (product_vision_id) REFERENCES product_visions(id) ON DELETE SET NULL
);

INSERT INTO framework_epics_new (
    id, project_id, product_vision_id, epic_key, name, description, status, priority,
    ai_generated, ai_confidence, complexity_score, effort_estimate, sort_order,
    unblock_potential, critical_path_weight, tdd_phase, tdd_order,
    business_value, risk_mitigation, strategic_alignment,
    created_at, updated_at, started_at, completed_at
)
SELECT 
    id, project_id, NULL as product_vision_id, epic_key, name, description, status, priority,
    ai_generated, ai_confidence, complexity_score, effort_estimate, sort_order,
    unblock_potential, critical_path_weight, tdd_phase, tdd_order,
    business_value, risk_mitigation, strategic_alignment,
    created_at, updated_at, started_at, completed_at
FROM framework_epics;

DROP TABLE framework_epics;
ALTER TABLE framework_epics_new RENAME TO framework_epics;

CREATE INDEX IF NOT EXISTS idx_epics_project_pv ON framework_epics(project_id, product_vision_id);
CREATE INDEX IF NOT EXISTS idx_epics_key ON framework_epics(epic_key);

COMMIT;

