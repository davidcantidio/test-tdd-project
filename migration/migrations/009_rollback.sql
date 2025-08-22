-- Rollback 009: Remove Sprint System and Advanced Features (Phase 3)
-- Date: 2025-08-22
-- Description: Rollback migration 009 - Remove sprint system, milestones, AI tracking, and change log
-- WARNING: This rollback will remove extensive data and functionality

-- ==================================================================================
-- REMOVE TRIGGERS
-- ==================================================================================
-- Drop triggers in reverse order

DROP TRIGGER IF EXISTS trigger_auto_change_log_tasks;
DROP TRIGGER IF EXISTS trigger_ai_generations_updated_at;
DROP TRIGGER IF EXISTS trigger_sprint_milestones_updated_at;
DROP TRIGGER IF EXISTS trigger_sprint_tasks_updated_at;
DROP TRIGGER IF EXISTS trigger_sprints_updated_at;
DROP TRIGGER IF EXISTS trigger_single_current_sprint;

-- ==================================================================================
-- REMOVE INDEXES  
-- ==================================================================================
-- Drop all indexes created by migration 009

-- Change Log indexes
DROP INDEX IF EXISTS idx_change_log_automated;
DROP INDEX IF EXISTS idx_change_log_reversal;
DROP INDEX IF EXISTS idx_change_log_approval;
DROP INDEX IF EXISTS idx_change_log_batch;
DROP INDEX IF EXISTS idx_change_log_dates;
DROP INDEX IF EXISTS idx_change_log_type;
DROP INDEX IF EXISTS idx_change_log_user_id;
DROP INDEX IF EXISTS idx_change_log_entity;

-- AI Generations indexes
DROP INDEX IF EXISTS idx_ai_generations_review;
DROP INDEX IF EXISTS idx_ai_generations_dates;
DROP INDEX IF EXISTS idx_ai_generations_usage;
DROP INDEX IF EXISTS idx_ai_generations_model;
DROP INDEX IF EXISTS idx_ai_generations_context;
DROP INDEX IF EXISTS idx_ai_generations_type;
DROP INDEX IF EXISTS idx_ai_generations_user_id;

-- Sprint Milestones indexes
DROP INDEX IF EXISTS idx_sprint_milestones_type;
DROP INDEX IF EXISTS idx_sprint_milestones_dates;
DROP INDEX IF EXISTS idx_sprint_milestones_status;
DROP INDEX IF EXISTS idx_sprint_milestones_sprint_id;

-- Sprint Tasks indexes
DROP INDEX IF EXISTS idx_sprint_tasks_commitment;
DROP INDEX IF EXISTS idx_sprint_tasks_progress;
DROP INDEX IF EXISTS idx_sprint_tasks_assignment;
DROP INDEX IF EXISTS idx_sprint_tasks_status;
DROP INDEX IF EXISTS idx_sprint_tasks_task_id;
DROP INDEX IF EXISTS idx_sprint_tasks_sprint_id;

-- Sprints indexes
DROP INDEX IF EXISTS idx_sprints_number;
DROP INDEX IF EXISTS idx_sprints_team;
DROP INDEX IF EXISTS idx_sprints_dates;
DROP INDEX IF EXISTS idx_sprints_current;
DROP INDEX IF EXISTS idx_sprints_status;
DROP INDEX IF EXISTS idx_sprints_project_id;

-- ==================================================================================
-- REMOVE TABLES
-- ==================================================================================
-- Drop tables in dependency order (child tables first)

-- Drop Change Log table
DROP TABLE IF EXISTS change_log;

-- Drop AI Generations table  
DROP TABLE IF EXISTS ai_generations;

-- Drop Sprint Milestones table
DROP TABLE IF EXISTS sprint_milestones;

-- Drop Sprint Tasks table (depends on sprints and tasks)
DROP TABLE IF EXISTS sprint_tasks;

-- Drop Sprints table
DROP TABLE IF EXISTS sprints;

-- ==================================================================================
-- REMOVE ACHIEVEMENT TYPES
-- ==================================================================================
-- Remove achievement types added by migration 009

DELETE FROM achievement_types 
WHERE code IN (
    'SPRINT_MASTER', 'VELOCITY_CHAMPION', 'MILESTONE_ACHIEVER', 'BURNDOWN_MASTER',
    'AI_COLLABORATOR', 'AI_REVIEWER', 'PROMPT_ENGINEER',
    'CHANGE_TRACKER', 'AUDIT_CHAMPION'
);

-- ==================================================================================
-- SCHEMA VERSION CLEANUP
-- ==================================================================================
-- Remove this migration from schema_migrations table (if it exists)

-- Note: This will be handled by the migration runner
-- DELETE FROM schema_migrations WHERE version = '009';

-- ==================================================================================
-- ROLLBACK VERIFICATION QUERIES
-- ==================================================================================
-- These queries can be run to verify successful rollback

-- Verify tables don't exist:
-- SELECT name FROM sqlite_master WHERE type='table' 
-- AND name IN ('sprints', 'sprint_tasks', 'sprint_milestones', 'ai_generations', 'change_log');
-- Should return no rows

-- Verify indexes don't exist:
-- SELECT name FROM sqlite_master WHERE type='index' 
-- AND (name LIKE 'idx_sprint_%' OR name LIKE 'idx_ai_%' OR name LIKE 'idx_change_%');
-- Should return no rows

-- Verify triggers don't exist:
-- SELECT name FROM sqlite_master WHERE type='trigger' 
-- AND (name LIKE '%sprint%' OR name LIKE '%ai_generation%' OR name LIKE '%change_log%');
-- Should return no rows

-- Verify achievement types removed:
-- SELECT code FROM achievement_types WHERE category IN ('sprint', 'ai', 'quality');
-- Should not show the deleted achievement types

-- ==================================================================================
-- DATA LOSS WARNING
-- ==================================================================================
-- WARNING: This rollback will permanently delete the following data and functionality:
--
-- SPRINT MANAGEMENT SYSTEM:
-- 1. All sprint definitions, timelines, and goals
-- 2. Sprint team assignments and capacity planning
-- 3. Sprint metrics (velocity, burndown, health status)
-- 4. Sprint retrospective notes and lessons learned
-- 5. Task assignments to sprints and sprint-specific tracking
-- 6. Sprint milestone definitions and progress tracking
-- 7. Sprint quality metrics and deployment data
--
-- AI INTEGRATION SYSTEM:
-- 8. All AI-generated content and recommendations  
-- 9. AI model usage tracking and cost data
-- 10. User feedback on AI generations
-- 11. AI prompt engineering data
-- 12. AI content quality assessments
--
-- AUDIT & CHANGE TRACKING:
-- 13. Complete system change log and audit trail
-- 14. User action tracking and accountability
-- 15. System performance and resource usage data
-- 16. Compliance and security classification data
-- 17. Change approval workflows and notifications
-- 18. Rollback and reversal capabilities
--
-- ADVANCED PROJECT MANAGEMENT:
-- 19. Advanced milestone management capabilities
-- 20. Complex dependency tracking between sprints
-- 21. Team collaboration and assignment history
-- 22. Quality gate and sign-off procedures
-- 23. Risk management and mitigation tracking
-- 24. External system integration data
--
-- GAMIFICATION ENHANCEMENTS:
-- 25. 9 achievement types for advanced features
-- 26. Sprint-based point earning mechanisms
-- 27. AI collaboration rewards
-- 28. Quality contribution tracking
--
-- Make sure you have comprehensive backups before running this rollback!
-- This rollback removes the most advanced features of the system.

-- ==================================================================================
-- SYSTEM IMPACT ASSESSMENT
-- ==================================================================================
-- After this rollback, the system will revert to Phase 2 capabilities:
--
-- REMAINING FUNCTIONALITY:
-- ✅ Product Visions and User Stories (Phase 1)
-- ✅ Enhanced Tasks with Dependencies and Labels (Phase 2)
-- ✅ Basic project and epic management
-- ✅ TDD workflow support
-- ✅ Basic gamification
-- ✅ User management and authentication
--
-- REMOVED FUNCTIONALITY:
-- ❌ Sprint planning and execution
-- ❌ Agile project management features
-- ❌ AI integration and automation
-- ❌ Comprehensive audit trails
-- ❌ Advanced milestone tracking
-- ❌ Team collaboration features
-- ❌ Performance monitoring
-- ❌ Change management workflows
--
-- The system will still be fully functional but without advanced project management,
-- AI features, and comprehensive tracking capabilities.

-- ==================================================================================
-- ROLLBACK COMPLETE
-- ==================================================================================
-- Migration 009 has been successfully rolled back
-- System restored to Phase 2 state (Task Enhancements and Dependencies)
-- All sprint management, AI integration, and advanced audit features have been removed
--
-- IMPORTANT: Significant functionality and data loss has occurred
-- Ensure you have backups if you need to recover advanced features and data
--
-- To restore full functionality, re-run migration 009 after backing up current state