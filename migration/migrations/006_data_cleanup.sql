-- Migration: Data cleanup and normalization
-- Date: 2025-01-15
-- Description: Clean up data inconsistencies

-- Normalize status values
UPDATE framework_clients SET status = 'active' WHERE status IN ('Active', 'ACTIVE');
UPDATE framework_projects SET status = 'active' WHERE status IN ('Active', 'ACTIVE');
UPDATE framework_epics SET status = 'active' WHERE status IN ('Active', 'ACTIVE');

-- Clean up null/empty values
UPDATE framework_epics SET icon = '📋' WHERE icon IS NULL OR icon = '';
UPDATE framework_tasks SET estimate_minutes = 60 WHERE estimate_minutes IS NULL OR estimate_minutes = 0;

-- Ensure referential integrity
DELETE FROM framework_projects WHERE client_id NOT IN (SELECT id FROM framework_clients);
DELETE FROM framework_epics WHERE project_id NOT IN (SELECT id FROM framework_projects);
DELETE FROM framework_tasks WHERE epic_id NOT IN (SELECT id FROM framework_epics);
