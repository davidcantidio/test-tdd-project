-- Rollback 010: Revert metadata column rename
-- Date: 2025-08-27
-- Description: Revert 'extra_metadata' column back to 'metadata' in product_visions table
-- Reason: Rollback SQLAlchemy reserved name fix if needed

-- ==================================================================================
-- SQLITE ROLLBACK COLUMN RENAME OPERATION
-- ==================================================================================
-- Recreate table with original column name 'metadata'

-- Step 1: Create table with original column name
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
    metadata TEXT,  -- RESTORED: back to 'metadata' from 'extra_metadata'
    
    -- Constraints
    FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE
);

-- Step 2: Copy data from current table to rollback table
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
    metadata  -- Restore to old 'metadata' column name
)
SELECT 
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
    extra_metadata  -- Source: current 'extra_metadata' column
FROM product_visions;

-- Step 3: Drop current table
DROP TABLE product_visions;

-- Step 4: Rename rollback table to original name
ALTER TABLE product_visions_rollback RENAME TO product_visions;

-- Step 5: Recreate indexes
CREATE INDEX IF NOT EXISTS idx_product_visions_project_id ON product_visions(project_id);
CREATE INDEX IF NOT EXISTS idx_product_visions_status ON product_visions(status);
CREATE INDEX IF NOT EXISTS idx_product_visions_project_status ON product_visions(project_id, status);

-- Step 6: Recreate triggers
CREATE TRIGGER IF NOT EXISTS trigger_product_visions_updated_at
    AFTER UPDATE ON product_visions
    FOR EACH ROW
BEGIN
    UPDATE product_visions 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- ==================================================================================
-- ROLLBACK SUMMARY
-- ==================================================================================
-- ✅ Restored column: extra_metadata → metadata
-- ✅ Preserved all existing data
-- ✅ Recreated indexes and triggers
-- ✅ Maintains foreign key constraints
-- ⚠️ WARNING: SQLAlchemy reserved name issue will return
-- 
-- Database Changes:
-- - product_visions.extra_metadata (REMOVED)
-- - product_visions.metadata (RESTORED)
-- 
-- Post-Rollback Actions Required:
-- - Revert SQLAlchemy model change
-- - Update mapped_column("extra_metadata") back to mapped_column("metadata")