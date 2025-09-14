-- Rollback 012: Restore product_visions schema prior to 012_enhance_product_visions_add_fields
-- Reverts explicit columns (name, product_description, success_metrics, tech_requirements,
-- non_functional_requirements, compliance_requirements, risks, assumptions, deliverables,
-- market_opportunity, must_have, cannot_have) back to the simplified shape with extra_metadata

BEGIN TRANSACTION;

-- Original baseline from migration 010_rename_metadata_column.sql
CREATE TABLE product_visions_rollback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    vision_statement TEXT NOT NULL,
    problem_statement TEXT,
    target_audience TEXT,
    value_proposition TEXT,
    constraints TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_by TEXT,
    version INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active',
    notes TEXT,
    extra_metadata TEXT,
    FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE
);

-- Best-effort data migration from current explicit schema back to baseline
INSERT INTO product_visions_rollback (
    id,
    project_id,
    vision_statement,
    problem_statement,
    target_audience,
    value_proposition,
    constraints,
    created_at,
    updated_at,
    created_by,
    updated_by,
    version,
    status,
    notes,
    extra_metadata
)
SELECT
    id,
    project_id,
    vision_statement,
    problem_statement,
    target_audience,
    value_proposition,
    -- Represent constraints as a single string using must_have (fallback)
    must_have AS constraints,
    created_at,
    updated_at,
    created_by,
    updated_by,
    version,
    status,
    notes,
    NULL AS extra_metadata
FROM product_visions;

DROP TABLE product_visions;
ALTER TABLE product_visions_rollback RENAME TO product_visions;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_product_visions_project_id ON product_visions(project_id);
CREATE INDEX IF NOT EXISTS idx_product_visions_status ON product_visions(status);
CREATE INDEX IF NOT EXISTS idx_product_visions_project_status ON product_visions(project_id, status);

-- Recreate updated_at trigger
CREATE TRIGGER IF NOT EXISTS trigger_product_visions_updated_at
AFTER UPDATE ON product_visions
FOR EACH ROW
BEGIN
    UPDATE product_visions 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

COMMIT;

