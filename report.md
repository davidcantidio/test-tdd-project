Summary
Instrumented the database layer with an early epic_id guard and verbose SQL/result tracing to surface missing or malformed progress data during retrieval

Added detailed debug logging around each epic card, capturing epic metadata, progress payloads, and full exception context for faster root-cause diagnosis

Introduced a regression test confirming that get_epic_progress gracefully falls back when given a None epic ID, preventing downstream crashes in the UI

Testing
✅ pytest


Arquivos (4)

streamlit_extension/streamlit_app.py
+24
-7

streamlit_extension/utils/database.py
+56
-34

tests/test_epic_progress_defaults.py
+11
-0

tests/test_epic_summary_formatting.py
Novo