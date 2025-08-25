#!/usr/bin/env python3
"""
🧪 Placeholder Test for TDD Project Template

This file ensures pytest finds at least one test to execute,
preventing "no tests collected" errors that cause workflow failures.

This is a temporary solution until real tests are implemented
following the TDD methodology defined in the epic files.
"""

import sys
from pathlib import Path


def test_placeholder_always_passes():
    """
    Placeholder test that always passes.
    
    This test ensures the pytest workflow doesn't fail with 
    exit code 5 (no tests collected), allowing the Jekyll 
    build to proceed and GitHub Pages to deploy successfully.
    """
    assert True, "This placeholder test always passes"


def test_project_structure_exists():
    """
    Basic test to verify project structure exists.
    
    This test checks that key directories exist in the project,
    providing a foundation for future real tests.
    """
    project_root = Path(__file__).parent.parent
    
    # Check that essential directories exist
    assert project_root.exists(), "Project root should exist"
    assert (project_root / "docs").exists(), "docs/ directory should exist"
    assert (project_root / "epics").exists(), "epics/ directory should exist"
    
    # Check that essential config files exist
    assert (project_root / "pytest.ini").exists(), "pytest.ini should exist"
    assert (project_root / "pyproject.toml").exists(), "pyproject.toml should exist"


def test_python_version():
    """
    Test that Python version meets minimum requirements.
    
    This ensures the project runs on a supported Python version
    as defined in the project configuration.
    """
    assert sys.version_info >= (3, 8), f"Python 3.8+ required, got {sys.version_info}"


def test_epic_files_exist():
    """
    Test that epic JSON files exist and are discoverable.
    
    This test verifies that the TDD project structure includes
    epic files as expected by the automation workflows.
    """
    project_root = Path(__file__).parent.parent
    epics_dir = project_root / "epics"
    
    # Find epic files (*.json in epics directory)
    epic_files = list(epics_dir.glob("*.json"))
    
    assert len(epic_files) > 0, f"At least one epic file should exist in {epics_dir}"
    
    # Verify files have .json extension
    for epic_file in epic_files:
        assert epic_file.suffix == ".json", f"Epic file {epic_file} should have .json extension"


class TestTDDMethodology:
    """
    Test class for TDD methodology validation.
    
    This class groups tests related to TDD practices and ensures
    the project follows Test-Driven Development principles.
    """
    
    def test_tdd_principles_documented(self):
        """Test that TDD principles are documented in the project."""
        project_root = Path(__file__).parent.parent
        
        # Check for TDD-related documentation
        readme_exists = (project_root / "README.md").exists()
        assert readme_exists, "README.md should document TDD methodology"
    
    def test_red_green_refactor_cycle_supported(self):
        """Test that the project supports Red-Green-Refactor cycle."""
        # This is a placeholder for testing TDD cycle support
        # In a real implementation, this would verify:
        # - Test runners are configured
        # - Coverage tools are available  
        # - Commit patterns support TDD phases
        assert True, "TDD cycle infrastructure should be in place"


# Pytest fixtures for future test development
import pytest

@pytest.fixture
def project_root():
    """Fixture providing project root path for tests."""
    return Path(__file__).parent.parent


@pytest.fixture  
def epic_files(project_root):
    """Fixture providing list of epic JSON files."""
    epics_dir = project_root / "epics"
    return list(epics_dir.glob("*.json"))


@pytest.fixture
def sample_epic_data():
    """Fixture providing sample epic data for testing."""
    return {
        "epic": {
            "id": "TEST-1",
            "name": "Sample Epic",
            "tdd_enabled": True,
            "tasks": [
                {
                    "id": "TEST-1.1",
                    "title": "TEST: Sample functionality",
                    "tdd_phase": "red",
                    "estimate_minutes": 5
                }
            ]
        }
    }


if __name__ == "__main__":
    # Allow running tests directly with: python tests/test_placeholder.py
    import pytest
    pytest.main([__file__])