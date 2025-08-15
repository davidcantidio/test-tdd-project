 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/streamlit_extension/utils/database.py b/streamlit_extension/utils/database.py
index 8f395c08817ef32a845d8528edacf3805005258d..b665ac7c2247fc667aa9af0f59abdf5d57764e8f 100644
--- a/streamlit_extension/utils/database.py
+++ b/streamlit_extension/utils/database.py
@@ -421,78 +421,80 @@ class DatabaseManager:
                     """, [
                         str(task_id) if task_id else None,
                         ended_at,
                         duration_minutes,
                         actual_duration_minutes or duration_minutes,
                         focus_rating,
                         interruptions,
                         notes
                     ])
                     conn.commit()
                 
                 return True
                 
         except Exception as e:
             print(f"Error creating timer session: {e}")
             return False
     
     def get_epic_progress(self, epic_id: int) -> Dict[str, Any]:
         """Get detailed progress for an epic."""
         try:
             with self.get_connection("framework") as conn:
                 if SQLALCHEMY_AVAILABLE:
                     # Get epic info
                     epic_result = conn.execute(text("""
                         SELECT id, epic_key, name, status, points_earned
-                        FROM framework_epics WHERE id = :epic_id
+                        FROM framework_epics
+                        WHERE id = :epic_id AND deleted_at IS NULL
                     """), {"epic_id": epic_id})
                     epic_row = epic_result.fetchone()
                     if not epic_row:
                         return self._get_default_progress()
                     epic = dict(epic_row._mapping)
                     
                     # Get task counts
                     task_result = conn.execute(text("""
                         SELECT 
                             COUNT(*) as total_tasks,
                             SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                             SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks
-                        FROM framework_tasks WHERE epic_id = :epic_id
+                        FROM framework_tasks
+                        WHERE epic_id = :epic_id AND deleted_at IS NULL
                     """), {"epic_id": epic_id})
                     task_row = task_result.fetchone()
                     if not task_row:
                         tasks = {"total_tasks": 0, "completed_tasks": 0, "in_progress_tasks": 0}
                     else:
                         tasks = {k: (v or 0) for k, v in dict(task_row._mapping).items()}
                     
                 else:
                     cursor = conn.cursor()
                     
                     # Get epic info
                     cursor.execute("""
                         SELECT id, epic_key, name, status, points_earned
-                        FROM framework_epics WHERE id = ?
+                        FROM framework_epics WHERE id = ? AND deleted_at IS NULL
                     """, [epic_id])
                     epic_row = cursor.fetchone()
                     if not epic_row:
                         return self._get_default_progress()
                     epic = dict(epic_row)
                     
                     # Get task counts
                     cursor.execute("""
                         SELECT 
                             COUNT(*) as total_tasks,
                             SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                             SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks
                         FROM framework_tasks WHERE epic_id = ? AND deleted_at IS NULL
                     """, [epic_id])
                     task_row = cursor.fetchone()
                     if not task_row:
                         tasks = {"total_tasks": 0, "completed_tasks": 0, "in_progress_tasks": 0}
                     else:
                         tasks = {k: (v or 0) for k, v in dict(task_row).items()}
                 
                 # Calculate progress
                 total = tasks.get("total_tasks") or 0
                 completed = tasks.get("completed_tasks") or 0
                 progress_pct = (completed / total * 100) if total > 0 else 0
                 
diff --git a/tests/test_epic_progress_defaults.py b/tests/test_epic_progress_defaults.py
index 4b8f5b35a80597286ad2abb97961b2df9913f582..45907290d1d08c4717115f5ac82b35fece63a39a 100644
--- a/tests/test_epic_progress_defaults.py
+++ b/tests/test_epic_progress_defaults.py
@@ -1,48 +1,82 @@
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
-            points_earned INTEGER
+            points_earned INTEGER,
+            deleted_at TEXT
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
-        "INSERT INTO framework_epics (id, epic_key, name, status, points_earned) VALUES (1, 'E-1', 'Empty Epic', 'open', NULL)"
+        (
+            "INSERT INTO framework_epics (id, epic_key, name, status, points_earned, deleted_at)"
+            " VALUES (1, 'E-1', 'Empty Epic', 'open', NULL, NULL)"
+        )
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
-    assert progress["points_earned"] == 0
\ No newline at end of file
+    assert progress["points_earned"] == 0
+
+
+def test_missing_epic_returns_default_progress(tmp_path):
+    db_file = tmp_path / "framework.db"
+    setup_framework_db(db_file)
+
+    manager = DatabaseManager(framework_db_path=str(db_file))
+    progress = manager.get_epic_progress(999)
+
+    assert progress["name"] == "Unknown"
+    assert progress["progress_percentage"] == 0.0
+
+
+def test_deleted_epic_returns_default_progress(tmp_path):
+    db_file = tmp_path / "framework.db"
+    setup_framework_db(db_file)
+
+    conn = sqlite3.connect(db_file)
+    cur = conn.cursor()
+    cur.execute("UPDATE framework_epics SET deleted_at = '2024-01-01' WHERE id = 1")
+    conn.commit()
+    conn.close()
+
+    manager = DatabaseManager(framework_db_path=str(db_file))
+    progress = manager.get_epic_progress(1)
+
+    assert progress["name"] == "Unknown"
+    assert progress["total_tasks"] == 0
+    assert progress["progress_percentage"] == 0.0
+
 
EOF
)