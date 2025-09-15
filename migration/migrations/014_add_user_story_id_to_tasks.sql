-- Migration 014: Add user_story_id to framework_tasks with FK
-- Rebuild table to include FK and preserve data

BEGIN TRANSACTION;

CREATE TABLE framework_tasks_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_key TEXT NOT NULL,
    epic_id INTEGER NOT NULL,
    user_story_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    tdd_phase TEXT,
    status TEXT DEFAULT 'todo',
    estimate_minutes INTEGER,
    actual_minutes INTEGER,
    story_points INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (epic_id) REFERENCES framework_epics(id) ON DELETE CASCADE,
    FOREIGN KEY (user_story_id) REFERENCES framework_user_stories(id) ON DELETE SET NULL
);

INSERT INTO framework_tasks_new (
    id, task_key, epic_id, user_story_id, title, description, tdd_phase, status,
    estimate_minutes, actual_minutes, story_points, created_at, updated_at
)
SELECT
    id, task_key, epic_id, NULL as user_story_id, title, description, tdd_phase, status,
    estimate_minutes, actual_minutes, story_points, created_at, updated_at
FROM framework_tasks;

DROP TABLE framework_tasks;
ALTER TABLE framework_tasks_new RENAME TO framework_tasks;

CREATE INDEX IF NOT EXISTS idx_tasks_epic_user_story ON framework_tasks(epic_id, user_story_id);

COMMIT;

