import pytest


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "stress: mark test as stress test (may take long time)"
    )
    config.addinivalue_line(
        "markers", "endurance: mark test as endurance test (very long running)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )


def pytest_collection_modifyitems(config, items):
    """Skip stress tests by default."""
    if config.getoption("--stress") or config.getoption("--endurance"):
        return
        
    skip_stress = pytest.mark.skip(reason="need --stress option to run")
    skip_endurance = pytest.mark.skip(reason="need --endurance option to run")
    
    for item in items:
        if "stress" in item.keywords:
            item.add_marker(skip_stress)
        if "endurance" in item.keywords:
            item.add_marker(skip_endurance)


def pytest_addoption(parser):
    """Add command line options."""
    parser.addoption(
        "--stress", action="store_true", default=False, help="run stress tests"
    )
    parser.addoption(
        "--endurance", action="store_true", default=False, help="run endurance tests"
    )