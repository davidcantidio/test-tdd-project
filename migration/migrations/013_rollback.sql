-- Rollback for Migration 013

BEGIN TRANSACTION;

DROP TABLE IF EXISTS framework_epic_ai_audit;

COMMIT;

