import sqlite3
import threading

import pytest

from duration_system.database_transactions import DatabaseConnectionPool


def test_emergency_connections_are_closed(tmp_path):
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE t(id INTEGER)")
    conn.close()

    pool = DatabaseConnectionPool(str(db_file), max_connections=1, connection_timeout=0.1)

    # Acquire the only pooled connection
    with pool.get_connection() as primary:
        results = {}

        def worker():
            with pool.get_connection() as emergency:
                results["conn"] = emergency
                emergency.execute("SELECT 1")

        t = threading.Thread(target=worker)
        t.start()
        t.join()

    # After both context managers exit, the emergency connection should be closed
    emergency_conn = results["conn"]
    with pytest.raises(sqlite3.ProgrammingError):
        emergency_conn.execute("SELECT 1")

    pool.close_all()
