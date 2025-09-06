-- ==================================================================================
-- Migration 011: Add Priority Settings Table
-- História 3.2 - Pesos de Priorização Personalizados por Projeto
-- Date: 2025-09-06
-- ==================================================================================

-- Create framework_priority_settings table for project-specific weight configuration
CREATE TABLE IF NOT EXISTS framework_priority_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    
    -- Normalized weights [0,1] that sum to ~1.0
    -- Default values preserve 5:3:2:2 proportion from História 3.1
    valor_weight REAL DEFAULT 0.4167,      -- Business value weight (5/12)
    risco_weight REAL DEFAULT 0.25,        -- Risk mitigation weight (3/12)
    esforco_weight REAL DEFAULT 0.1667,    -- Effort efficiency weight (2/12)
    alinhamento_weight REAL DEFAULT 0.1667,-- Strategic alignment weight (2/12)
    confidence_weight REAL DEFAULT 0.0,    -- AI confidence weight (feature flag OFF)
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE,
    UNIQUE(project_id),  -- One configuration per project
    
    -- Validate weights sum to ~1.0 (with tolerance for floating point)
    CHECK (ABS((valor_weight + risco_weight + esforco_weight + alinhamento_weight + confidence_weight) - 1.0) <= 0.0001),
    
    -- Validate all weights are non-negative
    CHECK (valor_weight >= 0 AND risco_weight >= 0 AND esforco_weight >= 0 AND alinhamento_weight >= 0 AND confidence_weight >= 0)
);

-- Create index for fast lookups by project
CREATE INDEX IF NOT EXISTS idx_priority_settings_project 
ON framework_priority_settings(project_id);

-- Trigger to automatically update updated_at on changes
-- NOTE: Migration tracking is handled by schema_migrations via MigrationManager
-- No manual inserts into tracking tables here.
