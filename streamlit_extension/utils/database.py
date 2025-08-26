"""
🗄️ Database Management - DEPRECATED

⚠️ IMPORTANT MIGRATION NOTICE ⚠️

DatabaseManager has been completely removed as part of Phase 4.2: Clean Architecture.
This monolithic approach has been replaced with a modern modular database API.

========================================================================
MIGRATION GUIDE - How to update your code:
========================================================================

OLD (DEPRECATED):
    from streamlit_extension.utils.database import DatabaseManager
    db = DatabaseManager()
    conn = db.get_connection()
    results = db.execute_query("SELECT * FROM table")

NEW (CLEAN MODULAR APPROACH):
    from streamlit_extension.database.connection import get_connection_context, execute
    from streamlit_extension.database import queries
    
    # Direct SQL execution
    results = execute("SELECT * FROM table")
    
    # Connection context
    with get_connection_context() as conn:
        cursor = conn.execute("SELECT * FROM table")
        results = cursor.fetchall()
    
    # Pre-built queries
    epics = queries.list_epics()
    tasks = queries.list_tasks(epic_id)

FOR SERVICES:
    OLD: def __init__(self, db_manager: DatabaseManager):
    NEW: def __init__(self):  # Use modular database API directly

========================================================================
"""

class DatabaseManager:
    """
    DEPRECATED: DatabaseManager has been removed.
    
    This class now raises DeprecationWarning to guide migration to modular API.
    """
    
    def __init__(self, *args, **kwargs):
        raise DeprecationWarning(
            "\n"
            "🚨 DatabaseManager has been DEPRECATED and REMOVED 🚨\n"
            "\n"
            "Phase 4.2: Clean Architecture Migration Complete\n"
            "\n"
            "REPLACE THIS:\n"
            "  from streamlit_extension.utils.database import DatabaseManager\n"
            "  db = DatabaseManager()\n"
            "\n"
            "WITH THIS:\n"
            "  from streamlit_extension.database.connection import execute\n"
            "  from streamlit_extension.database import queries\n"
            "  \n"
            "  # Direct execution: execute(sql, params)\n"
            "  # Pre-built queries: queries.list_epics(), queries.list_tasks()\n"
            "\n"
            "📚 See modular API documentation in streamlit_extension/database/\n"
            "✅ Clean architecture achieved - no more monolith!\n"
        )


# Prevent imports of the old monolithic API while allowing system attributes
def __getattr__(name):
    # Allow system attributes that Python and Streamlit need
    system_attributes = {
        '__path__', '__file__', '__name__', '__package__', '__spec__',
        '__loader__', '__cached__', '__builtins__', '__doc__'
    }
    
    if name in system_attributes:
        # Let Python handle these attributes normally
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    # Block deprecated DatabaseManager API attributes
    deprecated_attributes = {
        'DatabaseManager', 'get_connection', 'execute_query', 
        'create_tables', 'get_epics', 'get_tasks', 'create_task',
        'update_task', 'delete_task', 'get_projects', 'create_project',
        'dict_rows'  # This should now come from the modular API
    }
    
    if name in deprecated_attributes:
        raise DeprecationWarning(
            f"'{name}' from DatabaseManager is deprecated. "
            "Use streamlit_extension.database modular API instead."
        )
    
    # For any other attribute, raise AttributeError (standard Python behavior)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")