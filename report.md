Executive Summary
Strengthened database access by validating fetchone() results and supplying safe defaults, preventing NoneType errors across key query paths

Improved backup restore robustness with structured logging for JSON decode issues and centralized logger initialization

Priority 1 Fixes
Database fetch validation – added explicit fetchone() checks and default values to eliminate unsafe direct indexing in statistics and timeline queries.

Priority 2 Enhancements
Structured logging during config restore – introduced module-level logger and warnings on JSON decode failures for easier diagnostics.

Priority 3 Optimizations
None identified in this iteration.

Implementation Patches
diff --git a/streamlit_extension/utils/database.py b/streamlit_extension/utils/database.py
@@
-                    stats["completed_tasks"] = result.scalar()
+                    stats["completed_tasks"] = result.scalar() or 0
@@
-                    stats["total_points"] = result.scalar()
+                    stats["total_points"] = result.scalar() or 0
@@
-                    stats["active_streaks"] = result.scalar()
+                    stats["active_streaks"] = result.scalar() or 0
@@
-                    stats["completed_tasks"] = cursor.fetchone()[0]
+                    row = cursor.fetchone()
+                    stats["completed_tasks"] = row[0] if row and row[0] is not None else 0
@@
-                    stats["total_points"] = cursor.fetchone()[0]
+                    row = cursor.fetchone()
+                    stats["total_points"] = row[0] if row and row[0] is not None else 0
@@
-                    stats["active_streaks"] = cursor.fetchone()[0]
+                    row = cursor.fetchone()
+                    stats["active_streaks"] = row[0] if row and row[0] is not None else 0
@@
-                    summary["tasks_completed"] = cursor.fetchone()[0] or 0
+                    row = cursor.fetchone()
+                    summary["tasks_completed"] = row[0] if row and row[0] is not None else 0
@@
-                    summary["tasks_in_progress"] = cursor.fetchone()[0] or 0
+                    row = cursor.fetchone()
+                    summary["tasks_in_progress"] = row[0] if row and row[0] is not None else 0
@@
-                    summary["tasks_created"] = cursor.fetchone()[0] or 0
+                    row = cursor.fetchone()
+                    summary["tasks_created"] = row[0] if row and row[0] is not None else 0
@@
-                    epic_data = dict(result.fetchone()._mapping) if result.rowcount > 0 else None
+                    row = result.fetchone()
+                    epic_data = dict(row._mapping) if row else None
@@
-                    total_minutes = cursor.fetchone()[0] or 0
+                    row = cursor.fetchone()
+                    total_minutes = row[0] if row and row[0] is not None else 0
diff --git a/streamlit_extension/config/backup_restore.py b/streamlit_extension/config/backup_restore.py
@@
-import json
+import json
+import logging
@@
-    THEMES_AVAILABLE = False
-
-
+    THEMES_AVAILABLE = False
+
+
+logger = logging.getLogger(__name__)
@@
-                    except (KeyError, json.JSONDecodeError):
-                        pass
+                    except (KeyError, json.JSONDecodeError) as e:
+                        logger.warning("Failed to restore streamlit config: %s", e)
@@
-                    except (KeyError, json.JSONDecodeError):
-                        pass
+                    except (KeyError, json.JSONDecodeError) as e:
+                        logger.warning("Failed to restore themes: %s", e)
Testing
✅ pytest

Notes
Further enterprise hardening opportunities remain (e.g., comprehensive input validation, advanced SQL security policies) and should be scheduled for future iterations.


Arquivos (2)

streamlit_extension/config/backup_restore.py
+8
-4

streamlit_extension/utils/database.py
+26
-18


