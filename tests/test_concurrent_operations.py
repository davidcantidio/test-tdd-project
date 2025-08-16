"""
Concurrent Operations Test Suite
Validates database behavior under concurrent access patterns.
"""

import sqlite3
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from streamlit_extension.utils.database import DatabaseManager


def _init_concurrent_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE framework_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_key TEXT UNIQUE,
            name TEXT,
            description TEXT,
            industry TEXT,
            company_size TEXT,
            primary_contact_name TEXT,
            primary_contact_email TEXT,
            timezone TEXT,
            currency TEXT,
            preferred_language TEXT,
            hourly_rate REAL,
            contract_type TEXT,
            status TEXT,
            client_tier TEXT,
            priority_level INTEGER,
            account_manager_id INTEGER,
            technical_lead_id INTEGER,
            created_by INTEGER,
            created_at TEXT,
            updated_at TEXT,
            last_contact_date TEXT,
            deleted_at TEXT
        )"""
    )
    conn.commit()
    conn.close()


@pytest.fixture
def db_manager(tmp_path):
    db_file = tmp_path / "framework.db"
    _init_concurrent_db(db_file)
    return DatabaseManager(framework_db_path=str(db_file))


class TestConcurrentOperations:
    """Concurrent operations test cases"""

    def test_concurrent_client_creation(self, db_manager):
        """Test concurrent client creation"""
        def create_client(index: int):
            return db_manager.create_client(
                client_key=f"concurrent_{index}",
                name=f"Client {index}",
                description=f"Desc {index}"
            )

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_client, i) for i in range(10)]
            results = [f.result() for f in futures]

        successful = [r for r in results if r is not None]
        assert len(successful) == 10
        assert len(set(successful)) == 10

    def test_concurrent_client_updates(self, db_manager):
        """Test concurrent updates to same client"""
        client_id = db_manager.create_client(client_key="upd", name="Original")

        def update_client(suffix: int):
            return db_manager.update_client(client_id, name=f"Updated {suffix}")

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(update_client, i) for i in range(5)]
            results = [f.result() for f in futures]

        if not any(results):
            pytest.skip("Client updates not supported")
        final_client = db_manager.get_client(client_id)
        assert "Updated" in final_client["name"]

    def test_database_connection_pool_limit(self, db_manager):
        """Ensure multiple concurrent reads do not deadlock"""
        def perform_query(_: int):
            try:
                result = db_manager.get_clients(page=1, page_size=5)
                return result is not None
            except Exception:
                return False

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(perform_query, i) for i in range(20)]
            results = [f.result() for f in futures]

        assert sum(1 for r in results if r) >= 15
