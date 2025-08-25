import subprocess
import sys
from pathlib import Path
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from scripts.generate_api_docs import APIDocGenerator
from scripts.validate_docstrings import DocstringValidator


def test_api_doc_generation(tmp_path):
    generator = APIDocGenerator()
    docs = generator.extract_docstrings("streamlit_extension/utils/database.py")
    assert "DatabaseManager" in docs


def test_docstring_validation():
    validator = DocstringValidator()
    missing = validator.check_missing_docstrings("streamlit_extension/utils/database.py")
    assert missing == []


def test_documentation_completeness():
    assert Path("docs/README.md").exists()


def test_example_code_execution():
    result = subprocess.run([
        "python",
        "-m",
        "doctest",
        "docs/api/database_manager.md",
    ], capture_output=True, text=True)
    assert result.returncode == 0


def test_all_public_methods_documented():
    validator = DocstringValidator()
    missing = validator.check_missing_docstrings("streamlit_extension/utils/database.py")
    assert missing == []


def test_docstring_format_compliance():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_db", "streamlit_extension/utils/database.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[assignment]
    DatabaseManager = module.DatabaseManager

    validator = DocstringValidator()
    assert validator.validate_docstring_format(DatabaseManager.get_connection.__doc__)


def test_api_examples_work(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_db", "streamlit_extension/utils/database.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[assignment]
    DatabaseManager = module.DatabaseManager

    db_path = tmp_path / "example.db"
    db_path.touch()
    db = DatabaseManager(str(db_path))
    with db.get_connection():
        pass


def test_auth_manager_docstrings():
    validator = DocstringValidator()
    missing = validator.check_missing_docstrings("streamlit_extension.auth.auth_manager")
    assert missing == []


def test_security_manager_docstrings():
    validator = DocstringValidator()
    missing = validator.check_missing_docstrings("streamlit_extension/utils/security.py")
    assert missing == []


def test_duration_calculator_docstrings():
    validator = DocstringValidator()
    missing = validator.check_missing_docstrings("duration_system.duration_calculator")
    assert missing == []