# 🌿 TDD Branch Strategy

## 📋 Overview
Branch strategy optimized for Test-Driven Development with epic-based project management.

## 🎯 Branch Structure

### **Main Branches**
- **`main`** - Stable production branch
- **`develop`** - Main development branch (optional)

### **Feature Branches**
Each epic has its own feature branch following TDD phases:

```
feature/epic-[ID]-[name]
├── RED phase commits (failing tests)
├── GREEN phase commits (implementation)
└── REFACTOR phase commits (optimization)
```

**Examples:**
- `feature/epic-1-user-authentication`
- `feature/epic-2-data-processing`
- `feature/epic-3-api-endpoints`

## 🔄 TDD Workflow per Branch

### **RED Phase**
```bash
git checkout -b feature/epic-1-user-auth
# Write failing tests
git add tests/
git commit -m "🔴 RED: Add failing tests for user authentication"
```

### **GREEN Phase**
```bash
# Implement minimal code to pass tests
git add src/
git commit -m "🟢 GREEN: Implement basic user authentication"
```

### **REFACTOR Phase**
```bash
# Improve code while keeping tests green
git add src/ tests/
git commit -m "🔄 REFACTOR: Optimize authentication flow"
```

## 📋 Branch Naming Convention

### **Feature Branches**
- `feature/epic-[ID]-[short-name]`
- `feature/epic-1-user-auth`
- `feature/epic-2-data-validation`

### **Bug Fix Branches**
- `bugfix/[issue-number]-[short-description]`
- `bugfix/123-login-validation`

### **Hotfix Branches**
- `hotfix/[version]-[short-description]`
- `hotfix/1.0.1-security-patch`

## 🔀 Merge Strategy

### **Merge Requirements**
1. ✅ All tests pass (RED-GREEN-REFACTOR cycle complete)
2. ✅ Code coverage >= 90%
3. ✅ Code review approved
4. ✅ Epic tasks completed as defined
5. ✅ Documentation updated

### **Merge Process**
```bash
# Before merging
git checkout feature/epic-1-user-auth
git rebase main
git push --force-with-lease

# Create pull request with epic template
gh pr create --template=epic-implementation
```

## 🚀 Release Strategy

### **Version Tags**
- Follow semantic versioning: `v1.0.0`
- Tag when epic milestones are complete
- Include epic completion in release notes

### **Release Branches**
```bash
# Create release branch
git checkout -b release/v1.0.0 develop
git tag v1.0.0
git push --tags
```

## 🔒 Protected Branch Rules

### **Main Branch**
- ✅ Require pull request reviews
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Require conversation resolution
- ❌ Allow force pushes
- ❌ Allow deletions

### **Develop Branch** (if used)
- ✅ Require pull request reviews
- ✅ Require status checks to pass
- ✅ Allow force pushes (for rebasing)

## 📝 Commit Message Convention

### **TDD Phase Prefixes**
- `🔴 RED:` - Failing tests
- `🟢 GREEN:` - Implementation
- `🔄 REFACTOR:` - Code improvement
- `📚 DOCS:` - Documentation
- `🧪 TEST:` - Test additions/improvements
- `🐛 FIX:` - Bug fixes

### **Examples**
```
🔴 RED: Add failing test for user login validation
🟢 GREEN: Implement JWT token generation
🔄 REFACTOR: Extract authentication service
📚 DOCS: Update API documentation for auth endpoints
```

## 🎯 Integration with Epic Management

### **Branch-Epic Mapping**
- Each feature branch maps to one epic
- Branch name includes epic ID for traceability
- Commits reference specific epic tasks

### **Automated Updates**
- GitHub Actions update epic progress based on branch status
- Pull requests automatically link to epic issues
- Merge completion triggers epic task closure

This strategy ensures clean TDD development with full traceability from epic to production deployment.