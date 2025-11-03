import os
import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration (requires services)")


def pytest_collection_modifyitems(config, items):
    """Skip tests marked as integration unless RUN_INTEGRATION_TESTS=1."""
    run_integration = os.getenv("RUN_INTEGRATION_TESTS", "0") == "1"
    if run_integration:
        return

    skip_integration = pytest.mark.skip(reason="Integration tests skipped (set RUN_INTEGRATION_TESTS=1 to enable)")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture
def dev_mock_ai(monkeypatch):
    """Fixture to enable DEV_MOCK_AI for tests that need the lightweight mock AI.

    Usage:
        def test_foo(dev_mock_ai):
            # DEV_MOCK_AI is set for the duration of this test
            ...
    """
    monkeypatch.setenv("DEV_MOCK_AI", "1")
    yield
