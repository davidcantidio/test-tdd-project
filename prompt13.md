# PROMPT 13: Repository Cleanup & Standards

## 🎯 OBJETIVO
Limpar repositório e padronizar para resolver itens do report.md: "Remove .streamlit_cache from repository and enforce gitignore" e "Mixed naming conventions (snake_case vs. camelCase) reduce readability."

## 📁 ARQUIVOS ALVO (CONFIGS - SEM INTERSEÇÃO)
- `.gitignore` (ATUALIZAÇÃO)
- `pyproject.toml` (NOVO/ATUALIZAÇÃO)
- `scripts/cleanup_repository.py` (NOVO)
- `scripts/enforce_standards.py` (NOVO)
- `docs/CODING_STANDARDS.md` (NOVO)

## 🚀 DELIVERABLES

### 1. Enhanced .gitignore

```gitignore
# TDD Framework - Comprehensive .gitignore

# ============================================================================
# PYTHON
# ============================================================================
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# ============================================================================
# STREAMLIT CACHE (CRITICAL CLEANUP)
# ============================================================================
.streamlit_cache/
.streamlit/
*.streamlit_cache
**/streamlit_cache/
**/.streamlit_cache/

# ============================================================================
# DATABASES & DATA
# ============================================================================
*.db
*.sqlite
*.sqlite3
*.db-journal
*.db-wal
*.db-shm
/data/
/backups/
test_*.db
dev_*.db
staging_*.db

# ============================================================================
# REDIS & CACHING
# ============================================================================
dump.rdb
redis-stable/
*.rdb

# ============================================================================
# LOGS & MONITORING
# ============================================================================
logs/
*.log
*.log.*
.logs/
/var/log/

# ============================================================================
# ENVIRONMENT & SECRETS
# ============================================================================
.env
.env.local
.env.development
.env.staging
.env.production
*.pem
*.key
secrets/
.secrets/

# ============================================================================
# DEVELOPMENT TOOLS
# ============================================================================
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
.pytest_cache/
.coverage
htmlcov/
.tox/
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/

# ============================================================================
# DOCUMENTATION BUILD
# ============================================================================
docs/_build/
docs/build/
site/

# ============================================================================
# TEMPORARY FILES
# ============================================================================
tmp/
temp/
*.tmp
*.temp
.temporary/

# ============================================================================
# MIGRATION ARTIFACTS
# ============================================================================
migrations/applied/
migration_backups/

# ============================================================================
# PERFORMANCE TESTING
# ============================================================================
performance_reports/
load_test_results/
benchmarks/results/

# ============================================================================
# DOCKER & CONTAINERS
# ============================================================================
.dockerignore
docker-compose.override.yml
```

### 2. Project Configuration (pyproject.toml)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "tdd-framework"
version = "2.4.0"
description = "TDD Framework with Streamlit Dashboard and Enterprise Features"
authors = [{name = "TDD Framework Team", email = "team@tddframework.dev"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.8"

dependencies = [
    "streamlit>=1.28.0",
    "pandas>=1.5.0",
    "plotly>=5.15.0",
    "sqlite3",
    "redis>=4.5.0",
    "requests>=2.28.0",
    "pydantic>=1.10.0",
    "python-dotenv>=0.19.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "black>=22.0.0",
    "isort>=5.10.0",
    "flake8>=5.0.0",
    "mypy>=1.0.0",
    "bandit>=1.7.0",
]

test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-timeout>=2.1.0",
    "factory-boy>=3.2.0",
]

security = [
    "bandit[toml]>=1.7.0",
    "safety>=2.3.0",
    "pip-audit>=2.6.0",
]

[project.urls]
Homepage = "https://github.com/tdd-framework/tdd-framework"
Documentation = "https://docs.tddframework.dev"
Repository = "https://github.com/tdd-framework/tdd-framework.git"
Issues = "https://github.com/tdd-framework/tdd-framework/issues"

# ============================================================================
# CODE QUALITY TOOLS
# ============================================================================

[tool.black]
line-length = 100
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
  | migrations
)/
'''

[tool.isort]
profile = "black"
line_length = 100
known_first_party = ["streamlit_extension", "duration_system"]
known_third_party = ["streamlit", "pandas", "plotly", "redis"]
sections = ["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = ["streamlit.*", "plotly.*", "redis.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "security: marks tests as security tests",
    "performance: marks tests as performance tests",
]

[tool.coverage.run]
source = ["streamlit_extension", "duration_system"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/scripts/*",
    "*/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]

[tool.bandit]
exclude_dirs = ["tests", "migrations", "scripts/cleanup_repository.py"]
skips = ["B101", "B601"]  # Skip assert_used and paramiko

[tool.bandit.assert_used]
skips = ["**/test_*.py", "**/tests.py"]
```

### 3. Repository Cleanup Script

```python
"""
🧹 Repository Cleanup Script

Automated cleanup of repository artifacts:
- Remove .streamlit_cache directories
- Clean temporary files
- Remove database artifacts
- Clean build artifacts
- Standardize file permissions
"""

import os
import shutil
import glob
from pathlib import Path
from typing import List, Dict

class RepositoryCleanup:
    """Automated repository cleanup system."""
    
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.cleaned_items = []
        self.errors = []
    
    def clean_streamlit_cache(self) -> Dict[str, int]:
        """Remove all .streamlit_cache directories."""
        
    def clean_python_artifacts(self) -> Dict[str, int]:
        """Remove Python build and cache artifacts."""
        
    def clean_database_artifacts(self) -> Dict[str, int]:
        """Remove database artifacts and temporary files."""
        
    def clean_log_files(self) -> Dict[str, int]:
        """Remove log files and temporary logs."""
        
    def standardize_permissions(self) -> Dict[str, int]:
        """Standardize file permissions."""
        
    def run_full_cleanup(self) -> Dict[str, any]:
        """Run complete repository cleanup."""
```

### 4. Standards Enforcement Script

```python
"""
📏 Coding Standards Enforcement

Automated enforcement of coding standards:
- snake_case naming validation
- Import organization
- Docstring compliance
- File structure validation
"""

class StandardsEnforcer:
    """Enforces coding standards across codebase."""
    
    NAMING_CONVENTIONS = {
        'files': r'^[a-z][a-z0-9_]*\.py$',
        'functions': r'^[a-z][a-z0-9_]*$',
        'variables': r'^[a-z][a-z0-9_]*$',
        'classes': r'^[A-Z][a-zA-Z0-9]*$',
        'constants': r'^[A-Z][A-Z0-9_]*$',
    }
    
    def validate_naming_conventions(self) -> List[Dict]:
        """Validate naming conventions across codebase."""
        
    def check_import_organization(self) -> List[Dict]:
        """Check import statement organization."""
        
    def validate_docstring_compliance(self) -> List[Dict]:
        """Validate docstring compliance."""
        
    def generate_standards_report(self) -> Dict[str, Any]:
        """Generate comprehensive standards report."""
```

### 5. Coding Standards Documentation

```markdown
# 📏 TDD Framework Coding Standards

## Naming Conventions

### Files and Directories
- **Files**: `snake_case.py` ✅
- **Directories**: `snake_case/` ✅
- **Modules**: `snake_case` ✅

### Python Code
- **Variables**: `snake_case` ✅
- **Functions**: `snake_case()` ✅
- **Classes**: `PascalCase` ✅
- **Constants**: `UPPER_SNAKE_CASE` ✅
- **Private methods**: `_private_method()` ✅

### Database
- **Tables**: `snake_case` ✅
- **Columns**: `snake_case` ✅
- **Indexes**: `idx_table_column` ✅

## Import Organization
```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import streamlit as st
import pandas as pd
import redis

# Local imports
from streamlit_extension.utils.database import DatabaseManager
from .security import security_manager
```

## Documentation Standards
- **All public methods**: Comprehensive docstrings
- **Type hints**: Required for all functions
- **Examples**: Real-world usage examples
- **Performance notes**: For database operations
```

## 🔧 CLEANUP TARGETS

### Critical Removals:
- ✅ `.streamlit_cache/` directories (>500MB saved)
- ✅ Temporary database files
- ✅ Build artifacts
- ✅ Log files and temporary data

### Standardization:
- ✅ snake_case naming throughout codebase
- ✅ Consistent import organization
- ✅ File permission standardization
- ✅ Directory structure cleanup

### Quality Improvements:
- ✅ Enhanced .gitignore coverage
- ✅ Project configuration standardization
- ✅ Automated standards enforcement
- ✅ Documentation standardization

## 📊 SUCCESS CRITERIA

- [ ] .streamlit_cache completely removed from repository
- [ ] Enhanced .gitignore prevents future cache commits
- [ ] Naming conventions standardized to snake_case
- [ ] Import organization standardized
- [ ] Automated cleanup scripts functional
- [ ] Standards enforcement automated
- [ ] Documentation standards established
- [ ] Repository size reduced by >500MB