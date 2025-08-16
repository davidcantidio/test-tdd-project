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
```
# Run cleanup script
python scripts/cleanup_cache.py

# Quick Python cache cleanup
find . -name "__pycache__" -exec rm -rf {} +

# Quick Streamlit cache cleanup
find . -name ".streamlit_cache" -exec rm -rf {} +
```

### Automated Cleanup
Add to your development workflow:

```
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
