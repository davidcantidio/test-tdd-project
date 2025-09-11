-- Rollback for Migration 012
-- Note: Data in removed columns cannot be recovered.

BEGIN TRANSACTION;

-- Recreate removed columns (as NULL/defaults) to restore compatibility
ALTER TABLE framework_epics ADD COLUMN epic_key TEXT;
ALTER TABLE framework_epics ADD COLUMN epic_template_version TEXT;
ALTER TABLE framework_epics ADD COLUMN summary TEXT;
ALTER TABLE framework_epics ADD COLUMN goals JSON;
ALTER TABLE framework_epics ADD COLUMN definition_of_done JSON;
ALTER TABLE framework_epics ADD COLUMN quality_gates JSON;
ALTER TABLE framework_epics ADD COLUMN automation_hooks JSON;
ALTER TABLE framework_epics ADD COLUMN checklist_epic_level JSON;

-- Optional: recreate legacy table (empty) if dependent code expects it
CREATE TABLE IF NOT EXISTS framework_clients (
    id INTEGER PRIMARY KEY,
    name TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

COMMIT;
