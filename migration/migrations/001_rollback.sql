-- Rollback for Migration 001: Remove migration tracking table
-- This rollback removes the schema_migrations table and its indexes

DROP INDEX IF EXISTS idx_schema_migrations_applied_at;
DROP INDEX IF EXISTS idx_schema_migrations_version;
DROP TABLE IF EXISTS schema_migrations;