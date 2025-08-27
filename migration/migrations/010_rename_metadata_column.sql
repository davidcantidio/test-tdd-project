-- Migration 010: Rename metadata column to avoid SQLAlchemy reserved name conflict
-- Date: 2025-08-27
-- Description: Rename 'metadata' column to 'extra_metadata' in product_visions table
-- Reason: SQLAlchemy Declarative API reserves 'metadata' as an attribute name
-- Impact: Fixes InvalidRequestError: Attribute name 'metadata' is reserved

-- ==================================================================================
-- SQLITE COLUMN RENAME OPERATION
-- ==================================================================================
-- SQLite >= 3.25 supports ALTER TABLE RENAME COLUMN
-- For compatibility with older versions, we use the recreate table approach

-- Step 1: Create new table with corrected column name
CREATE TABLE product_visions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    vision_statement TEXT NOT NULL,
    problem_statement TEXT,
    target_audience TEXT,
    value_proposition TEXT,
    constraints TEXT,  -- JSON field for constraints list
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_by TEXT,
    version INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active',
    notes TEXT,
    extra_metadata TEXT,  -- RENAMED: was 'metadata', now 'extra_metadata'
    
    -- Constraints
    FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE
);

-- Step 2: Copy data from old table to new table
INSERT INTO product_visions_new (
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
    extra_metadata  -- Copy old 'metadata' column to new 'extra_metadata'
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
    metadata  -- Source: old 'metadata' column
FROM product_visions;

-- Step 3: Drop old table
DROP TABLE product_visions;

-- Step 4: Rename new table to original name
ALTER TABLE product_visions_new RENAME TO product_visions;

-- Step 5: Recreate indexes
CREATE INDEX IF NOT EXISTS idx_product_visions_project_id ON product_visions(project_id);
CREATE INDEX IF NOT EXISTS idx_product_visions_status ON product_visions(status);
CREATE INDEX IF NOT EXISTS idx_product_visions_project_status ON product_visions(project_id, status);

-- Step 6: Recreate triggers (update timestamp trigger)
CREATE TRIGGER IF NOT EXISTS trigger_product_visions_updated_at
    AFTER UPDATE ON product_visions
    FOR EACH ROW
BEGIN
    UPDATE product_visions 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- ==================================================================================
-- DATA VALIDATION
-- ==================================================================================
-- Verify the migration completed successfully

-- Check table structure
-- PRAGMA table_info(product_visions);
-- Expected: column 'extra_metadata' exists, column 'metadata' does not exist

-- Check data integrity
-- SELECT COUNT(*) FROM product_visions;
-- Expected: Same count as before migration

-- Check metadata values were preserved
-- SELECT id, extra_metadata FROM product_visions WHERE extra_metadata IS NOT NULL LIMIT 5;
-- Expected: JSON data preserved in extra_metadata column

-- ==================================================================================
-- MIGRATION SUMMARY
-- ==================================================================================
-- ✅ Renamed column: metadata → extra_metadata
-- ✅ Preserved all existing data
-- ✅ Recreated indexes and triggers
-- ✅ Maintains foreign key constraints
-- ✅ Fixes SQLAlchemy reserved name conflict
-- 
-- Database Changes:
-- - product_visions.metadata (REMOVED)
-- - product_visions.extra_metadata (ADDED)
-- 
-- Compatibility:
-- - SQLAlchemy model now matches database schema
-- - No application code changes needed
-- - JSON field functionality preserved