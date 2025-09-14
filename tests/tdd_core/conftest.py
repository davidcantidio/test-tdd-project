"""Shared fixtures for tdd_core tests."""

import pytest
from pathlib import Path


@pytest.fixture
def tdd_core_module():
    """Import tdd_core module for testing."""
    import tdd_core
    return tdd_core


@pytest.fixture
def tdd_core_path():
    """Return the path to the tdd_core module."""
    return Path(__file__).parent.parent.parent / "tdd_core"


@pytest.fixture  
def project_root():
    """Return the project root path."""
    return Path(__file__).parent.parent.parent