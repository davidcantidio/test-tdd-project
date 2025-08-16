# 🤖 PROMPT FF: CACHE ARTIFACTS CLEANUP

## 🎯 OBJECTIVE
Remove cache artifacts and optimize .gitignore to address report.md requirement: "Untracked cache artifacts indicate inadequate .gitignore and potential repository bloat" in the Critical Issues List.

## 📋 TASKS TO COMPLETE

### 1. Clean Existing Cache Artifacts

Remove any existing cache files and directories:

```bash
# Remove Streamlit cache directories
find . -name ".streamlit_cache" -type d -exec rm -rf {} +
find . -name "__streamlit_cache__" -type d -exec rm -rf {} +
find . -name ".streamlit" -type d -exec rm -rf {} +

# Remove Python cache
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# Remove pytest cache
find . -name ".pytest_cache" -type d -exec rm -rf {} +

# Remove coverage cache
find . -name ".coverage" -delete
find . -name "htmlcov" -type d -exec rm -rf {} +

# Remove other cache artifacts
find . -name "*_cache.json" -delete
find . -name "*.cache" -delete
find . -name ".cache" -type d -exec rm -rf {} +

# Remove log files that shouldn't be tracked
find . -name "*.log" -delete
find . -name "logs" -type d -exec rm -rf {} +
```

### 2. Optimize .gitignore File

Replace the current .gitignore with this comprehensive version:

```gitignore
# Python
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
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
ENV/
env/
.venv/
.env

# Poetry
poetry.lock

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/
.hypothesis/
.cache/
coverage.xml
*.cover
.coverage.*

# Documentation
docs/_build/
docs/_site/
site/

# Logs
*.log
logs/
*.log.*

# Database
*.db
*.sqlite
*.sqlite3

# Environment variables
.env
.env.local
.env.development
.env.staging
.env.production

# Node.js (if mixed project)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Streamlit specific
.streamlit/
.streamlit_cache/
*.streamlit_cache
**/.streamlit_cache/
**/streamlit_cache/
.streamlit/secrets.toml
.streamlit/config.toml

# Performance and cache files
performance_cache.db
task_timer.db
.cache/
*_cache.json
*.cache

# Temporary files
*.tmp
*.temp
.tmp/
.temp/

# Backup files
*.bak
*.backup
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Security
.secrets/
secrets.toml
private_key
*.pem
*.key

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# pipenv
Pipfile.lock

# Poetry
poetry.lock

# Celery
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# PyCharm
.idea/

# Archives
*.tar.gz
*.zip
*.rar

# Custom project files
patches_backup/
old_versions/
deprecated/

# Docker
docker-compose.override.yml
.dockerignore

# Monitoring
prometheus_data/
grafana_data/

# Local development
local_config.yaml
development.db
test_output/
```

### 3. Create Cache Management Script

Create `scripts/cleanup_cache.py`:

```python
#!/usr/bin/env python3
"""
Cache Cleanup Script
Removes cache artifacts and cleans up the repository.
"""

import os
import shutil
import glob
from pathlib import Path
from typing import List, Dict


def find_cache_files() -> Dict[str, List[str]]:
    """Find all cache files and directories in the project."""
    cache_patterns = {
        'python_cache': ['**/__pycache__', '**/*.pyc', '**/*.pyo'],
        'streamlit_cache': ['**/.streamlit_cache', '**/streamlit_cache', '**/.streamlit'],
        'pytest_cache': ['**/.pytest_cache', '**/.cache'],
        'coverage_cache': ['**/.coverage', '**/htmlcov', '**/.coverage.*'],
        'other_cache': ['**/*_cache.json', '**/*.cache', '**/logs'],
        'temp_files': ['**/*.tmp', '**/*.temp', '**/*.log']
    }
    
    found_files = {}
    for category, patterns in cache_patterns.items():
        found_files[category] = []
        for pattern in patterns:
            found_files[category].extend(glob.glob(pattern, recursive=True))
    
    return found_files


def remove_cache_files(dry_run: bool = False) -> Dict[str, int]:
    """Remove cache files and return counts."""
    cache_files = find_cache_files()
    removed_counts = {}
    
    for category, files in cache_files.items():
        removed_counts[category] = 0
        
        for file_path in files:
            try:
                if os.path.isfile(file_path):
                    if not dry_run:
                        os.remove(file_path)
                    removed_counts[category] += 1
                    print(f"{'[DRY RUN] ' if dry_run else ''}Removed file: {file_path}")
                    
                elif os.path.isdir(file_path):
                    if not dry_run:
                        shutil.rmtree(file_path)
                    removed_counts[category] += 1
                    print(f"{'[DRY RUN] ' if dry_run else ''}Removed directory: {file_path}")
                    
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
    
    return removed_counts


def check_gitignore_coverage() -> List[str]:
    """Check if .gitignore covers all cache patterns."""
    gitignore_path = Path('.gitignore')
    
    if not gitignore_path.exists():
        return ["No .gitignore file found"]
    
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()
    
    missing_patterns = []
    required_patterns = [
        '__pycache__/',
        '.streamlit_cache/',
        '.pytest_cache/',
        '.coverage',
        '*.log',
        '*.cache',
        '.cache/',
        '*.tmp'
    ]
    
    for pattern in required_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)
    
    return missing_patterns


def get_repository_size() -> Dict[str, float]:
    """Calculate repository size breakdown."""
    sizes = {}
    
    # Calculate cache size
    cache_files = find_cache_files()
    cache_size = 0
    for files in cache_files.values():
        for file_path in files:
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    cache_size += os.path.getsize(file_path)
                elif os.path.isdir(file_path):
                    for dirpath, dirnames, filenames in os.walk(file_path):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                cache_size += os.path.getsize(filepath)
                            except OSError:
                                pass
    
    # Calculate total repository size
    total_size = 0
    for dirpath, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except OSError:
                pass
    
    sizes['cache_size_mb'] = cache_size / (1024 * 1024)
    sizes['total_size_mb'] = total_size / (1024 * 1024)
    sizes['cache_percentage'] = (cache_size / total_size * 100) if total_size > 0 else 0
    
    return sizes


def main():
    """Main cleanup function."""
    print("🧹 Cache Cleanup Tool")
    print("=" * 50)
    
    # Check current state
    print("\n📊 Repository Analysis:")
    sizes = get_repository_size()
    print(f"Total repository size: {sizes['total_size_mb']:.2f} MB")
    print(f"Cache files size: {sizes['cache_size_mb']:.2f} MB")
    print(f"Cache percentage: {sizes['cache_percentage']:.1f}%")
    
    # Check .gitignore coverage
    print("\n🔍 GitIgnore Analysis:")
    missing_patterns = check_gitignore_coverage()
    if missing_patterns:
        print("⚠️ Missing patterns in .gitignore:")
        for pattern in missing_patterns:
            print(f"  - {pattern}")
    else:
        print("✅ All cache patterns covered in .gitignore")
    
    # Show what would be removed (dry run)
    print("\n🔍 Cache Files Found:")
    cache_files = find_cache_files()
    total_files = sum(len(files) for files in cache_files.values())
    
    if total_files == 0:
        print("✅ No cache files found - repository is clean!")
        return
    
    for category, files in cache_files.items():
        if files:
            print(f"  {category}: {len(files)} items")
    
    print(f"\nTotal cache items: {total_files}")
    
    # Ask for confirmation
    response = input("\n🗑️ Remove all cache files? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        print("\n🧹 Cleaning cache files...")
        removed_counts = remove_cache_files(dry_run=False)
        
        total_removed = sum(removed_counts.values())
        print(f"\n✅ Cleanup complete! Removed {total_removed} items")
        
        # Show final sizes
        print("\n📊 Final Repository Analysis:")
        final_sizes = get_repository_size()
        print(f"Total repository size: {final_sizes['total_size_mb']:.2f} MB")
        print(f"Cache files size: {final_sizes['cache_size_mb']:.2f} MB")
        print(f"Space saved: {sizes['cache_size_mb'] - final_sizes['cache_size_mb']:.2f} MB")
        
    else:
        print("❌ Cleanup cancelled")


if __name__ == "__main__":
    main()
```

### 4. Update Project Documentation

Create `docs/CACHE_MANAGEMENT.md`:

```markdown
# Cache Management

## Overview
This project implements comprehensive cache management to prevent repository bloat and ensure clean development environments.

## Cache Types

### 1. Python Cache
- `__pycache__/` directories
- `*.pyc`, `*.pyo` files
- Automatically ignored by .gitignore

### 2. Streamlit Cache
- `.streamlit_cache/` directories
- Session state cache files
- Configuration cache

### 3. Testing Cache
- `.pytest_cache/` directories
- `.coverage` files
- `htmlcov/` coverage reports

### 4. Development Cache
- Editor temporary files
- Log files
- Performance cache files

## Cleanup Commands

### Manual Cleanup
```bash
# Run cleanup script
python scripts/cleanup_cache.py

# Quick Python cache cleanup
find . -name "__pycache__" -exec rm -rf {} +

# Quick Streamlit cache cleanup
find . -name ".streamlit_cache" -exec rm -rf {} +
```

### Automated Cleanup
Add to your development workflow:

```bash
# Add to .pre-commit-hook (if using)
- repo: local
  hooks:
    - id: cache-cleanup
      name: Cache Cleanup
      entry: python scripts/cleanup_cache.py
      language: python
```

## Best Practices

1. **Regular Cleanup**: Run cleanup script weekly
2. **Pre-commit**: Clean cache before commits
3. **CI/CD**: Include cache cleanup in deployment scripts
4. **Monitoring**: Check repository size regularly

## .gitignore Patterns

Key patterns to prevent cache tracking:
```
__pycache__/
.streamlit_cache/
.pytest_cache/
.coverage
*.log
*.cache
.cache/
*.tmp
```

## Size Monitoring

Monitor repository health:
- Cache files should be <5% of total repository size
- Run `python scripts/cleanup_cache.py` for analysis
- Check .gitignore coverage regularly
```

### 5. Add Cache Cleanup to Development Workflow

Create `.github/workflows/cache-cleanup.yml` (if using GitHub):

```yaml
name: Cache Cleanup Check

on:
  pull_request:
    branches: [ main ]

jobs:
  cache-check:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Check for cache artifacts
      run: |
        python scripts/cleanup_cache.py
        
        # Fail if cache files found
        cache_files=$(find . -name "__pycache__" -o -name ".streamlit_cache" -o -name "*.pyc")
        if [ ! -z "$cache_files" ]; then
          echo "❌ Cache artifacts found in repository:"
          echo "$cache_files"
          exit 1
        fi
        
        echo "✅ No cache artifacts found"
```

## ✅ REQUIREMENTS

1. **Remove all existing cache artifacts** from repository
2. **Optimize .gitignore** with comprehensive patterns
3. **Create cache cleanup script** for ongoing maintenance
4. **Add documentation** for cache management
5. **Include workflow integration** for automated checks
6. **Provide size analysis** tools
7. **Ensure no functional code changes**

## 🚫 WHAT NOT TO CHANGE
- Source code functionality
- Database files that contain data
- Configuration files with user settings
- Valid log files with important data
- Import statements or dependencies

## ✅ VERIFICATION CHECKLIST
- [ ] All cache artifacts removed from repository
- [ ] .gitignore updated with comprehensive patterns
- [ ] Cache cleanup script created and tested
- [ ] Documentation added for cache management
- [ ] Repository size reduced significantly
- [ ] No functional code affected
- [ ] Workflow integration provided
- [ ] Size analysis tools working

## 🎯 CONTEXT
This addresses report.md issue: "Untracked cache artifacts indicate inadequate .gitignore and potential repository bloat" with MEDIUM severity and CERTAIN confidence in the Critical Issues List.

The goal is to maintain a clean repository and prevent future cache bloat.