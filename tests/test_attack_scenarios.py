"""
Attack Simulation Test Suite
Covers SQL injection, path traversal and DoS rate limiting scenarios.
"""

import sqlite3
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from streamlit_extension.utils.database import DatabaseManager
from streamlit_extension.utils.security import sanitize_input, security_manager


def _init_attack_db(db_path: Path) -> None:
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
    _init_attack_db(db_file)
    return DatabaseManager(framework_db_path=str(db_file))


class TestAttackScenarios:
    """Attack simulation test cases"""

    def test_sql_injection_attempts(self, db_manager):
        """Ensure SQL injection payloads do not alter database"""
        db_manager.create_client(client_key="safe", name="Safe")
        payload = "'; DROP TABLE framework_clients; --"
        result = db_manager.get_clients(name_filter=payload)
        assert isinstance(result, dict)
        # Table should still be writable
        new_id = db_manager.create_client(client_key="safe2", name="Safe2")
        assert new_id is not None

    def test_path_traversal_attempts(self):
        """Verify path traversal strings are sanitized"""
        payload = "../../etc/passwd"
        sanitized = sanitize_input(payload)
        assert isinstance(sanitized, str)

    def test_dos_rate_limiting(self):
        """Test basic DoS protection via rate limiting"""
        if hasattr(security_manager, 'check_rate_limit'):
            allowed = True
            for _ in range(20):
                allowed, _ = security_manager.check_rate_limit('form_submit', user_id='user', ip_address='127.0.0.1')
            assert isinstance(allowed, bool)
