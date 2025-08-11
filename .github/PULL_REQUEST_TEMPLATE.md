# 🎯 TDD Pull Request

## Epic Information
**Epic ID:** [EPIC-X.Y]  
**Epic Name:** [Epic Name]  
**TDD Phase:** [red/green/refactor/analysis]

## 📋 Summary
Brief description of what this PR accomplishes in the context of TDD methodology.

## 🧪 TDD Checklist
### Red Phase
- [ ] Tests written before implementation
- [ ] Tests fail for the right reasons
- [ ] Test names clearly describe expected behavior
- [ ] Edge cases identified and tested

### Green Phase  
- [ ] Minimal implementation to make tests pass
- [ ] All new tests are now green
- [ ] No existing tests were broken
- [ ] Implementation is focused only on making tests pass

### Refactor Phase
- [ ] All tests remain green during refactoring
- [ ] Code is cleaner and more maintainable
- [ ] No functionality was added during refactor
- [ ] Complexity reduced where possible

## 🔍 Changes Made
- [ ] Added new tests in: `tests/test_*.py`
- [ ] Modified implementation in: `src/*.py`
- [ ] Updated documentation
- [ ] Refactored existing code

## 🧪 Testing
- [ ] All tests pass locally (`pytest`)
- [ ] Test coverage maintained or improved
- [ ] Performance tests pass (if applicable)
- [ ] Integration tests pass

### Test Evidence
```bash
# Paste test output here
pytest -v
```

### Coverage Report
```bash
# Paste coverage report here
pytest --cov
```

## 📊 Quality Metrics
- **Test Coverage:** X%
- **New Tests Added:** X
- **Files Modified:** X
- **Cyclomatic Complexity:** [Maintained/Reduced/Increased]

## 🔗 Related Issues
Closes #[issue_number]  
Related to #[issue_number]

## 📝 Additional Notes
Any additional context, decisions made, or future work needed.

## 🎯 TDD Principles Followed
- [ ] **Red:** Write failing tests first
- [ ] **Green:** Minimum code to pass tests  
- [ ] **Refactor:** Improve design while keeping tests green
- [ ] **Small steps:** Changes are incremental and focused
- [ ] **Fast feedback:** Tests provide quick validation

---
/cc @team-lead @code-reviewer