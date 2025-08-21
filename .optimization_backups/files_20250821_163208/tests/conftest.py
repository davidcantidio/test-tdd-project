"""
🧪 Pytest Configuration and Fixtures

Shared fixtures and configuration for all tests:
- Database setup and teardown
- Mock configurations
- Test data factories
- Environment setup
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import sqlite3
from datetime import datetime, timedelta

# Test configuration
pytest_plugins = []


@pytest.fixture(scope="session")
def test_data_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        yield test_dir


@pytest.fixture(scope="function")
# TODO: Consider extracting this block into a separate method
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        db_path = Path(temp_file.name)
    
    # Create basic test schema
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE framework_epics (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE framework_tasks (
            id INTEGER PRIMARY KEY,
            epic_id INTEGER,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (epic_id) REFERENCES framework_epics (id)
        )
    """)
    conn.execute("""
        CREATE TABLE timer_sessions (
            id INTEGER PRIMARY KEY,
            task_reference TEXT,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            planned_duration_minutes INTEGER,
            focus_rating INTEGER,
            interruptions_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    try:
        db_path.unlink()
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_epic_data():
    """Sample epic data for testing."""
    return {
        "id": 1,
        "name": "Test Epic",
        "description": "Epic for testing purposes",
        "status": "active",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "id": 1,
        "epic_id": 1,
        "title": "Test Task",
        "description": "Task for testing purposes",
        "status": "pending",
        "estimate_minutes": 60,
        "created_at": "2023-01-01T00:00:00"
    }


# TODO: Consider extracting this block into a separate method
@pytest.fixture
def sample_timer_sessions():
    """Sample timer session data for testing."""
    now = datetime.now()
    return [
        {
            "id": 1,
            "task_reference": "1",
            "started_at": (now - timedelta(hours=2)).isoformat(),
            "planned_duration_minutes": 25,
            "focus_rating": 8,
            "interruptions_count": 1
        },
        {
            "id": 2,
            "task_reference": "1",
            "started_at": (now - timedelta(hours=1)).isoformat(),
            "planned_duration_minutes": 25,
            "focus_rating": 7,
            "interruptions_count": 0
        }
    ]


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock()
    config.github_token = "test_token"
    config.github_repo_owner = "test_owner"
    config.github_repo_name = "test_repo"
    config.cache_ttl_seconds = 300
    config.max_disk_cache_mb = 100
    return config


# TODO: Consider extracting this block into a separate method

@pytest.fixture
def mock_database_manager(temp_db, sample_epic_data, sample_task_data, sample_timer_sessions):
    """Mock database manager with test data."""
    
    # Populate test database
    conn = sqlite3.connect(str(temp_db))
    conn.execute("INSERT INTO framework_epics (id, name, status) VALUES (?, ?, ?)",
                 (sample_epic_data["id"], sample_epic_data["name"], sample_epic_data["status"]))
    conn.execute("INSERT INTO framework_tasks (id, epic_id, title, status) VALUES (?, ?, ?, ?)",
                 (sample_task_data["id"], sample_task_data["epic_id"], 
                  sample_task_data["title"], sample_task_data["status"]))
    
    for session in sample_timer_sessions:
        conn.execute("""
            INSERT INTO timer_sessions (id, task_reference, started_at, 
                                      planned_duration_minutes, focus_rating, interruptions_count) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session["id"], session["task_reference"], session["started_at"],
              session["planned_duration_minutes"], session["focus_rating"], 
              session["interruptions_count"]))
    
    conn.commit()
    conn.close()
    
    # Create mock database manager
    db_manager = Mock()
    db_manager.get_epics.return_value = [sample_epic_data]
    db_manager.get_tasks.return_value = [sample_task_data]
    db_manager.get_timer_sessions.return_value = sample_timer_sessions
    db_manager.get_user_stats.return_value = {
        "completed_tasks": 5,
        "total_points": 150,
        "active_streaks": 2
    }
    db_manager.check_database_health.return_value = {
        "framework_db_exists": True,
        "timer_db_exists": True,
        "framework_db_connected": True,
        "timer_db_connected": True
    }
    
    # TODO: Consider extracting this block into a separate method
    return db_manager


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit for testing UI components."""
    with patch('streamlit_extension.components.status_components.st') as mock_st:
        # Configure common Streamlit mock methods
        mock_st.markdown = Mock()
        mock_st.write = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock()])
        mock_st.container = Mock()
        mock_st.expander = Mock()
        mock_st.tabs = Mock(return_value=[Mock(), Mock()])
        mock_st.selectbox = Mock(return_value=0)
        mock_st.button = Mock(return_value=False)
        mock_st.text_input = Mock(return_value="")
        mock_st.number_input = Mock(return_value=0)
        mock_st.slider = Mock(return_value=5)
        mock_st.checkbox = Mock(return_value=False)
        mock_st.metric = Mock()
        mock_st.success = Mock()
        mock_st.error = Mock()
        mock_st.warning = Mock()
        mock_st.info = Mock()
        mock_st.caption = Mock()
        mock_st.divider = Mock()
        mock_st.rerun = Mock()
        
        # Sidebar mock
        mock_st.sidebar = Mock()
        mock_st.sidebar.markdown = Mock()
        mock_st.sidebar.expander = Mock()
        
        # Session state mock
        mock_st.session_state = {}
        
# TODO: Consider extracting this block into a separate method
        
        yield mock_st


@pytest.fixture 
def analytics_test_data():
    """Test data for analytics components."""
    return {
        "report": {
            "period_days": 30,
            "total_sessions": 45,
            "total_focus_time": 1125,  # 45 sessions * 25 minutes
            "completed_tasks": 12,
            "average_focus_rating": 7.5,
            "total_points": 360,
            "active_epics": 3,
            "productivity_score": 82.3,
            "trends": {
                "focus_trend": 0.5,
                "session_frequency": "increasing"
            },
            "recommendations": [
                "Great focus consistency! Consider longer deep work sessions.",
                "Your interruption rate is low - keep up the distraction management.",
                "Morning sessions show highest focus - schedule important work then."
            ],
            "daily_metrics": [
                {
                    "date": "2023-01-01",
                    "sessions": 3,
                    "focus_time": 75,
                    "avg_focus": 8.0,
                    "tasks_completed": 1,
                    "interruptions": 2
                },
                {
                    "date": "2023-01-02", 
                    "sessions": 2,
                    "focus_time": 50,
                    "avg_focus": 7.0,
                    "tasks_completed": 0,
                    "interruptions": 1
                # TODO: Consider extracting this block into a separate method
                }
            ]
        }
    }


# Pytest marks for test organization
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as a UI component test"
    )
    config.addinivalue_line(
        "markers", "cache: mark test as a cache system test"
    )
    config.addinivalue_line(
        "markers", "theme: mark test as a theme system test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_streamlit: mark test as requiring Streamlit"
    )


# Test utilities
class TestDataFactory:
    """Factory for creating test data objects."""
    
    @staticmethod
    def create_epic(id=1, name="Test Epic", status="active", **kwargs):
        """Create test epic data."""
        epic_data = {
            "id": id,
            "name": name,
            "status": status,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        epic_data.update(kwargs)
        return epic_data
    
    @staticmethod
    def create_task(id=1, epic_id=1, title="Test Task", status="pending", **kwargs):
        """Create test task data."""
        task_data = {
            "id": id,
            "epic_id": epic_id,
            "title": title,
            "status": status,
            "estimate_minutes": 60,
            "created_at": "2023-01-01T00:00:00"
        }
        task_data.update(kwargs)
        return task_data
    
    @staticmethod
    def create_timer_session(id=1, task_reference="1", focus_rating=8, **kwargs):
        """Create test timer session data."""
        session_data = {
            "id": id,
            "task_reference": task_reference,
            "started_at": datetime.now().isoformat(),
            "planned_duration_minutes": 25,
            "focus_rating": focus_rating,
            "interruptions_count": 0
        }
        session_data.update(kwargs)
        return session_data


@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory