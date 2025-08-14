import sqlite3
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from streamlit_extension.utils.database import DatabaseManager


def setup_framework_db(db_path: Path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE framework_epics (
            id INTEGER PRIMARY KEY,
            epic_key TEXT,
            name TEXT,
            status TEXT,
            points_earned INTEGER
        )"""
    )
    cur.execute(
        """CREATE TABLE framework_tasks (
            id INTEGER PRIMARY KEY,
            epic_id INTEGER,
            status TEXT,
            deleted_at TEXT
        )"""
    )
    # Insert an epic with no tasks
    cur.execute(
        "INSERT INTO framework_epics (id, epic_key, name, status, points_earned) VALUES (1, 'E-1', 'Empty Epic', 'open', NULL)"
    )
    conn.commit()
    conn.close()


def test_epic_with_no_tasks_returns_zero_counts(tmp_path):
    db_file = tmp_path / "framework.db"
    setup_framework_db(db_file)

    manager = DatabaseManager(framework_db_path=str(db_file))
    progress = manager.get_epic_progress(1)

    assert progress["total_tasks"] == 0
    assert progress["completed_tasks"] == 0
    assert progress["in_progress_tasks"] == 0
    assert progress["points_earned"] == 0