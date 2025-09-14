-- Migration 012: Enhance product_visions with first-class columns and remove extra_metadata
-- Date: 2025-09-14
-- Description:
--   - Add explicit columns for ProductVision fields to avoid generic metadata JSON
--   - Keep constraints as TEXT (JSON array of strings) for list semantics
--   - Preserve existing data where possible; set new fields to NULL if no prior data
--   - Drop extra_metadata column by rebuilding the table

BEGIN TRANSACTION;

-- Rebuild product_visions table with explicit columns
CREATE TABLE IF NOT EXISTS product_visions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    
    -- Core identification and naming
    name VARCHAR(255) NOT NULL,

    -- Vision Content (explicit fields)
    vision_statement TEXT NOT NULL,
    problem_statement TEXT,
    target_audience TEXT,
    value_proposition TEXT,
    product_description TEXT,
    success_metrics TEXT,
    tech_requirements TEXT,
    non_functional_requirements TEXT,
    compliance_requirements TEXT,
    risks TEXT,
    assumptions TEXT,
    deliverables TEXT,
    market_opportunity TEXT,

    -- Requirement strings
    must_have TEXT,
    cannot_have TEXT,

    -- Audit & status
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_by TEXT,
    version INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active',
    notes TEXT,

    FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE
);

-- Migrate data from existing product_visions (best-effort mapping)
INSERT INTO product_visions_new (
    id, project_id, name,
    vision_statement, problem_statement, target_audience, value_proposition,
    product_description, success_metrics, tech_requirements, non_functional_requirements,
    compliance_requirements, risks, assumptions, deliverables, market_opportunity,
    must_have, cannot_have, created_at, updated_at, created_by, updated_by, version, status, notes
)
SELECT 
    id,
    project_id,
    -- use vision_statement as fallback for name if old schema didn't have name column
    CASE WHEN vision_statement IS NOT NULL THEN substr(vision_statement, 1, 255) ELSE '' END AS name,
    vision_statement,
    problem_statement,
    target_audience,
    value_proposition,
    NULL AS product_description,
    NULL AS success_metrics,
    NULL AS tech_requirements,
    NULL AS non_functional_requirements,
    NULL AS compliance_requirements,
    NULL AS risks,
    NULL AS assumptions,
    NULL AS deliverables,
    NULL AS market_opportunity,
    constraints AS must_have,
    NULL AS cannot_have,
    created_at,
    updated_at,
    created_by,
    updated_by,
    COALESCE(version, 1) AS version,
    COALESCE(status, 'active') AS status,
    notes
FROM product_visions;

-- Replace old table
DROP TABLE product_visions;
ALTER TABLE product_visions_new RENAME TO product_visions;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_product_visions_project_id ON product_visions(project_id);
CREATE INDEX IF NOT EXISTS idx_product_visions_status ON product_visions(status);
CREATE INDEX IF NOT EXISTS idx_product_visions_project_status ON product_visions(project_id, status);

-- Trigger to keep updated_at in sync
CREATE TRIGGER IF NOT EXISTS trigger_product_visions_updated_at
AFTER UPDATE ON product_visions
FOR EACH ROW
BEGIN
    UPDATE product_visions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

COMMIT;
