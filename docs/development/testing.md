# Testing Guide

## Test Structure
```
tests/
├── unit/                 # Unit tests
├── integration/          # Integration tests
├── load_testing/         # Load tests
├── security/             # Security tests
└── e2e/                  # End-to-end tests
```

## Running Tests

### All Tests
```bash
python -m pytest tests/ -v
```

### Specific Test Categories
```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Load tests
python -m pytest tests/load_testing/ -v

# Security tests
python -m pytest tests/security/ -v
```

## Test Coverage
```bash
python -m pytest tests/ --cov=streamlit_extension --cov-report=html
```

## Writing Tests
[Testing best practices...]
