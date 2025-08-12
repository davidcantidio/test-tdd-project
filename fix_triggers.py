#!/usr/bin/env python3
"""
🔧 Fix Database Triggers

Fixes and recreates database triggers for proper functionality.
"""

import sqlite3

def fix_triggers():
    """Fix database triggers."""
    print("🔧 Fixing database triggers...")
    
    conn = sqlite3.connect('framework.db')
    cursor = conn.cursor()
    
    # Drop existing triggers
    print("🗑️ Dropping existing triggers...")
    cursor.execute("DROP TRIGGER IF EXISTS update_user_points_on_task_complete")
    cursor.execute("DROP TRIGGER IF EXISTS calculate_task_points_on_complete")
    cursor.execute("DROP TRIGGER IF EXISTS update_daily_streak")
    
    # Recreate triggers with proper logic
    print("⚡ Creating fixed triggers...")
    
    # Fixed trigger for calculating task points
    cursor.execute("""
        CREATE TRIGGER calculate_task_points_on_complete
        AFTER UPDATE OF status ON framework_tasks
        WHEN NEW.status = 'completed' AND OLD.status != 'completed'
        BEGIN
            UPDATE framework_tasks
            SET points_earned = CASE 
                WHEN NEW.difficulty_modifier IS NULL THEN NEW.story_points * 10
                ELSE CAST(NEW.story_points * 10 * NEW.difficulty_modifier AS INTEGER)
            END,
            updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END
    """)
    
    # Fixed trigger for updating user points (with NULL check)
    cursor.execute("""
        CREATE TRIGGER update_user_points_on_task_complete
        AFTER UPDATE OF points_earned ON framework_tasks
        WHEN NEW.points_earned > OLD.points_earned AND NEW.assigned_to IS NOT NULL
        BEGIN
            UPDATE framework_users 
            SET total_points = total_points + (NEW.points_earned - OLD.points_earned),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.assigned_to;
        END
    """)
    
    # Fixed trigger for daily streak
    cursor.execute("""
        CREATE TRIGGER update_daily_streak
        AFTER UPDATE OF status ON framework_tasks
        WHEN NEW.status = 'completed' AND OLD.status != 'completed' AND NEW.assigned_to IS NOT NULL
        BEGIN
            INSERT OR REPLACE INTO user_streaks (
                user_id, streak_type, current_count, best_count, last_activity_date, updated_at
            )
            SELECT 
                NEW.assigned_to,
                'daily_tasks',
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM user_streaks 
                        WHERE user_id = NEW.assigned_to 
                        AND streak_type = 'daily_tasks'
                        AND DATE(last_activity_date) = DATE('now', '-1 day')
                    ) THEN (
                        SELECT current_count + 1 FROM user_streaks 
                        WHERE user_id = NEW.assigned_to AND streak_type = 'daily_tasks'
                    )
                    WHEN EXISTS (
                        SELECT 1 FROM user_streaks 
                        WHERE user_id = NEW.assigned_to 
                        AND streak_type = 'daily_tasks'
                        AND DATE(last_activity_date) = DATE('now')
                    ) THEN (
                        SELECT current_count FROM user_streaks 
                        WHERE user_id = NEW.assigned_to AND streak_type = 'daily_tasks'
                    )
                    ELSE 1
                END,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM user_streaks 
                        WHERE user_id = NEW.assigned_to 
                        AND streak_type = 'daily_tasks'
                        AND DATE(last_activity_date) = DATE('now', '-1 day')
                    ) THEN (
                        SELECT MAX(best_count, current_count + 1) FROM user_streaks 
                        WHERE user_id = NEW.assigned_to AND streak_type = 'daily_tasks'
                    )
                    ELSE (
                        SELECT COALESCE(MAX(best_count, 1), 1) FROM user_streaks 
                        WHERE user_id = NEW.assigned_to AND streak_type = 'daily_tasks'
                    )
                END,
                DATE('now'),
                CURRENT_TIMESTAMP;
        END
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Triggers fixed successfully!")

if __name__ == "__main__":
    fix_triggers()