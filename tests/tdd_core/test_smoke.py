"""
Smoke tests for tdd_core module structure and imports.

These tests ensure the basic module structure is working
and all imports are functional after História 1.1 implementation.
"""

import sys
from pathlib import Path
import pytest


def test_module_imports():
    """Test that tdd_core module can be imported."""
    try:
        import tdd_core
        assert tdd_core is not None
    except ImportError as e:
        pytest.fail(f"Failed to import tdd_core: {e}")


def test_version_available():
    """Test that version information is accessible."""
    import tdd_core
    
    # Test version attribute exists
    assert hasattr(tdd_core, '__version__')
    assert tdd_core.__version__ == "1.0.0"
    
    # Test version function works
    assert tdd_core.get_version() == "1.0.0"


def test_module_info():
    """Test that module info is available.""" 
    import tdd_core
    
    info = tdd_core.get_info()
    assert isinstance(info, dict)
    assert info["name"] == "tdd_core"
    assert info["version"] == "1.0.0"
    assert info["architecture"] == "Clean Architecture + DDD"
    assert info["status"] == "História 1.1 Complete - Structure Ready"


def test_architecture_info():
    """Test that detailed architecture info is available."""
    import tdd_core
    
    arch_info = tdd_core.get_architecture_info()
    assert isinstance(arch_info, dict)
    assert arch_info["name"] == "tdd_core"
    assert arch_info["version"] == "1.0.0"
    assert arch_info["architecture"] == "Clean Architecture + DDD"
    assert "layers" in arch_info
    assert "python_version" in arch_info
    assert "dependencies" in arch_info


def test_layer_imports():
    """Test that all main layers can be imported."""
    import tdd_core
    
    # Test domain layer
    assert hasattr(tdd_core, 'domain')
    from tdd_core import domain
    assert domain is not None
    
    # Test application layer
    assert hasattr(tdd_core, 'application')
    from tdd_core import application  
    assert application is not None
    
    # Test infrastructure layer
    assert hasattr(tdd_core, 'infrastructure')
    from tdd_core import infrastructure
    assert infrastructure is not None


def test_sublayer_imports():
    """Test that sublayers within each main layer can be imported."""
    # Domain sublayers
    from tdd_core.domain import entities, value_objects, exceptions, repositories
    assert all([entities, value_objects, exceptions, repositories])
    
    # Application sublayers  
    from tdd_core.application import services, dto, validators, use_cases
    assert all([services, dto, validators, use_cases])
    
    # Infrastructure sublayers
    from tdd_core.infrastructure import adapters, mappers, repositories as infra_repos, ai
    assert all([adapters, mappers, infra_repos, ai])


def test_no_premature_imports():
    """Test that we don't have premature concrete imports."""
    import tdd_core
    
    # Should be empty at História 1.1 stage
    assert len(tdd_core.__all__) == 0
    
    # Domain layer should also be empty
    from tdd_core import domain
    assert len(domain.__all__) == 0
    
    # Application layer should also be empty
    from tdd_core import application
    assert len(application.__all__) == 0
    
    # Infrastructure layer should also be empty  
    from tdd_core import infrastructure
    assert len(infrastructure.__all__) == 0


def test_directory_structure(tdd_core_path):
    """Test that the expected directory structure exists."""
    # Test main directory
    assert tdd_core_path.exists(), "tdd_core directory should exist"
    assert tdd_core_path.is_dir(), "tdd_core should be a directory"
    
    # Test main layers
    domain_path = tdd_core_path / "domain"
    application_path = tdd_core_path / "application"
    infrastructure_path = tdd_core_path / "infrastructure"
    
    assert domain_path.exists(), "domain directory should exist"
    assert application_path.exists(), "application directory should exist"
    assert infrastructure_path.exists(), "infrastructure directory should exist"
    
    # Test domain sublayers
    for sublayer in ["entities", "value_objects", "exceptions", "repositories"]:
        sublayer_path = domain_path / sublayer
        assert sublayer_path.exists(), f"domain/{sublayer} should exist"
    
    # Test application sublayers
    for sublayer in ["services", "dto", "validators", "use_cases"]:
        sublayer_path = application_path / sublayer
        assert sublayer_path.exists(), f"application/{sublayer} should exist"
    
    # Test infrastructure sublayers
    for sublayer in ["adapters", "mappers", "repositories", "ai"]:
        sublayer_path = infrastructure_path / sublayer
        assert sublayer_path.exists(), f"infrastructure/{sublayer} should exist"


def test_init_files_exist(tdd_core_path):
    """Test that all __init__.py files are present."""
    # Main __init__.py
    main_init = tdd_core_path / "__init__.py"
    assert main_init.exists(), "Main __init__.py should exist"
    
    # Layer __init__.py files
    for layer in ["domain", "application", "infrastructure"]:
        layer_init = tdd_core_path / layer / "__init__.py"
        assert layer_init.exists(), f"{layer}/__init__.py should exist"
    
    # Sublayer __init__.py files
    sublayers = [
        "domain/entities", "domain/value_objects", "domain/exceptions", "domain/repositories",
        "application/services", "application/dto", "application/validators", "application/use_cases",
        "infrastructure/adapters", "infrastructure/mappers", "infrastructure/repositories", "infrastructure/ai"
    ]
    
    for sublayer in sublayers:
        sublayer_init = tdd_core_path / sublayer / "__init__.py"
        assert sublayer_init.exists(), f"{sublayer}/__init__.py should exist"


def test_no_syntax_errors(tdd_core_path):
    """Test that all __init__.py files have valid Python syntax."""
    import ast
    
    # Find all __init__.py files
    init_files = list(tdd_core_path.glob("**/__init__.py"))
    assert len(init_files) == 16, f"Should find 16 __init__.py files, found {len(init_files)}"
    
    for init_file in init_files:
        try:
            with open(init_file, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content, filename=str(init_file))
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {init_file}: {e}")


def test_layer_metadata():
    """Test that layers have proper metadata."""
    from tdd_core import domain, application, infrastructure
    
    # Test domain layer metadata
    assert hasattr(domain, 'LAYER_INFO')
    domain_info = domain.LAYER_INFO
    assert domain_info["name"] == "domain"
    assert domain_info["dependencies"] == []  # No dependencies
    
    # Test application layer metadata
    assert hasattr(application, 'LAYER_INFO')
    app_info = application.LAYER_INFO
    assert app_info["name"] == "application"
    assert "domain" in app_info["dependencies"]  # Depends on domain
    
    # Test infrastructure layer metadata
    assert hasattr(infrastructure, 'LAYER_INFO')
    infra_info = infrastructure.LAYER_INFO
    assert infra_info["name"] == "infrastructure"
    assert "domain" in infra_info["dependencies"]  # Depends on domain
    assert "application" in infra_info["dependencies"]  # Depends on application


@pytest.mark.integration
def test_readme_exists(tdd_core_path):
    """Test that README.md exists and has content."""
    readme_path = tdd_core_path / "README.md"
    assert readme_path.exists(), "README.md should exist"
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for key sections
    assert "# 🏗️ TDD Core - Domain Layer" in content
    assert "Clean Architecture" in content
    assert "Domain-Driven Design" in content
    assert "História 1.1" in content


@pytest.mark.integration
def test_poetry_recognizes_package(project_root):
    """Test that Poetry configuration recognizes tdd_core."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml should exist"
    
    with open(pyproject_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that tdd_core is in packages
    assert '{include = "tdd_core"}' in content, "tdd_core should be in Poetry packages"
    
    # Check that tdd_core is in coverage and other configs
    assert '"tdd_core"' in content, "tdd_core should be in various configs"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])