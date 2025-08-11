# 📝 Placeholder Reference Guide

## 🎯 Quick Reference

This document lists all placeholders used in the TDD Project Template and their expected values.

## 📋 Essential Placeholders

### **Project Identity**
| Placeholder | Description | Example | Used In |
|-------------|-------------|---------|---------|
| `[PROJECT_NAME]` | Project name (lowercase with hyphens) | `my-awesome-app` | pyproject.toml, package.json, README.md |
| `[AUTHOR_NAME]` | Your full name | `John Doe` | All config files, README.md |
| `[AUTHOR_EMAIL]` | Your email address | `john.doe@example.com` | All config files |
| `[USERNAME]` | GitHub username | `johndoe` | URLs, config files |
| `[REPOSITORY_NAME]` | GitHub repository name | `my-awesome-app` | URLs, workflows |
| `[DESCRIPTION]` | Project description | `A TDD project for awesome features` | README.md, config files |

### **Epic & Task Placeholders**
| Placeholder | Description | Example | Used In |
|-------------|-------------|---------|---------|
| `[EPIC-ID]` | Epic identifier | `EPIC-1` | epic_template.json |
| `[Epic Name]` | Human-readable epic name | `User Authentication` | epic_template.json |
| `[specific behavior]` | Behavior being tested | `user login validation` | Epic tasks |
| `[module]` | Code module name | `auth` | File paths, test names |
| `[epic-name]` | Branch-safe epic name | `user-authentication` | Branch names |

### **File & Path Placeholders**
| Placeholder | Description | Example | Used In |
|-------------|-------------|---------|---------|
| `[module_path]` | Path to module | `src/auth` | Epic tasks |
| `test_[module].py` | Test file name | `test_auth.py` | Epic tasks |
| `[test_name]` | Specific test function | `test_login_validation` | Epic tasks |

## 🔍 Placeholder Locations

### **Configuration Files**

#### `config/python/pyproject_poetry.toml`
```toml
name = "[PROJECT_NAME]"
authors = ["[AUTHOR_NAME] <[AUTHOR_EMAIL]>"]
homepage = "https://github.com/[USERNAME]/[REPOSITORY_NAME]"
repository = "https://github.com/[USERNAME]/[REPOSITORY_NAME]"
documentation = "https://[USERNAME].github.io/[REPOSITORY_NAME]/"
```

#### `config/node/package.json`
```json
{
  "name": "[PROJECT_NAME]",
  "author": "[AUTHOR_NAME] <[AUTHOR_EMAIL]>",
  "homepage": "https://github.com/[USERNAME]/[REPOSITORY_NAME]#readme",
  "repository": {
    "url": "https://github.com/[USERNAME]/[REPOSITORY_NAME].git"
  }
}
```

#### `README_TEMPLATE.md` → `README.md`
```markdown
# [PROJECT_NAME]
> [DESCRIPTION]

**Author:** [AUTHOR_NAME]
**Repository:** https://github.com/[USERNAME]/[REPOSITORY_NAME]
```

### **Epic Templates**

#### `epics/epic_template.json`
```json
{
  "epic": {
    "id": "[EPIC-ID]",
    "name": "[Epic Name]",
    "summary": "[Summary focused on testable behaviors]",
    "tasks": [
      {
        "id": "[EPIC-ID].1",
        "title": "TEST: [specific behavior]",
        "branch": "feature/[epic-name]",
        "files_touched": ["tests/test_[module].py"]
      }
    ]
  }
}
```

### **GitHub Configuration**

#### `.github/workflows/*.yml`
```yaml
name: [PROJECT_NAME] CI/CD
env:
  PROJECT_NAME: [PROJECT_NAME]
  REPOSITORY_URL: https://github.com/[USERNAME]/[REPOSITORY_NAME]
```

#### `docs/_config.yml`
```yaml
title: [PROJECT_NAME]
description: [DESCRIPTION]
baseurl: "/[REPOSITORY_NAME]"
url: "https://[USERNAME].github.io"
```

## 🚀 Automated Replacement

The setup wizard (`setup/init_tdd_project.py`) automatically replaces these placeholders:

```python
replacements = {
    "[PROJECT_NAME]": self.config["project_name"],
    "[AUTHOR_NAME]": self.config["author_name"], 
    "[AUTHOR_EMAIL]": self.config["author_email"],
    "[USERNAME]": self.config["github_username"],
    "[REPOSITORY_NAME]": self.config["repository_name"],
    "[DESCRIPTION]": self.config["description"],
}
```

## 🔧 Manual Replacement

If you need to replace placeholders manually:

### **Find All Placeholders**
```bash
# Search for all placeholder patterns
grep -r "\[.*\]" . --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=venv

# Search for specific placeholder
grep -r "\[PROJECT_NAME\]" . --exclude-dir=.git
```

### **Replace All Instances**
```bash
# Replace PROJECT_NAME in all files
find . -type f -name "*.json" -o -name "*.toml" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" | \
  xargs sed -i 's/\[PROJECT_NAME\]/my-awesome-app/g'

# Replace AUTHOR_NAME
find . -type f -name "*.json" -o -name "*.toml" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" | \
  xargs sed -i 's/\[AUTHOR_NAME\]/John Doe/g'
```

### **Validation After Replacement**
```bash
# Check that no placeholders remain
grep -r "\[.*\]" . --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=venv

# Should return no results if all placeholders are replaced
```

## ⚠️ Common Mistakes

### **1. Case Sensitivity**
- ❌ `[project_name]` (wrong case)
- ✅ `[PROJECT_NAME]` (correct case)

### **2. Missing Brackets**
- ❌ `PROJECT_NAME` (missing brackets)
- ✅ `[PROJECT_NAME]` (correct format)

### **3. URL Format**
- ❌ `https://github.com/[USERNAME]/[PROJECT_NAME]` (wrong placeholder)
- ✅ `https://github.com/[USERNAME]/[REPOSITORY_NAME]` (correct placeholder)

### **4. Epic Task IDs**
- ❌ `[EPIC-ID]-1` (wrong separator)
- ✅ `[EPIC-ID].1` (correct format)

## 📝 Custom Placeholders

You can add your own placeholders for project-specific values:

### **Add Custom Placeholders**
```python
# In setup/init_tdd_project.py
custom_replacements = {
    "[API_VERSION]": "v1.0",
    "[DATABASE_NAME]": "myapp_db",
    "[DOCKER_IMAGE]": "myapp:latest",
}
```

### **Use in Templates**
```yaml
# In docker-compose.yml
version: '3.8'
services:
  api:
    image: [DOCKER_IMAGE]
    environment:
      DATABASE_URL: postgresql://user:pass@db/[DATABASE_NAME]
```

## 🎯 Epic-Specific Placeholders

### **TDD Phase Templates**
```json
{
  "tasks": [
    {
      "title": "TEST: [specific behavior]",     // What you're testing
      "tdd_phase": "red",
      "test_specs": [
        "should_[action]_when_[condition]",   // Test specification
        "should_raise_[exception]_when_[invalid_input]"
      ]
    },
    {
      "title": "IMPL: [minimal functionality]", // What you're implementing
      "tdd_phase": "green"
    },
    {
      "title": "REFACTOR: [design improvement]", // What you're improving
      "tdd_phase": "refactor"
    }
  ]
}
```

### **Branch Naming**
```json
{
  "branch": "feature/[epic-name]",           // kebab-case epic name
  "files_touched": ["tests/test_[module].py"] // module name in tests
}
```

## ✅ Validation Checklist

After replacing placeholders:

- [ ] No `[.*]` patterns remain in source files
- [ ] All URLs point to correct GitHub repository
- [ ] Author information is consistent across files
- [ ] Project name matches in all configurations
- [ ] Epic IDs follow correct format (`EPIC-X.Y`)
- [ ] Branch names use kebab-case
- [ ] Test file paths are valid

---

**Last Updated:** 2025-01-09  
**For Template Version:** 1.0