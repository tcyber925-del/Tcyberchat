import os
import sys
import pytest

# Make backend package importable when running from repo root
backend_root = os.path.join(os.getcwd(), "backend")
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Safe defaults across all backend tests (including those outside backend/tests)
os.environ.setdefault("RUN_INTEGRATION_TESTS", "0")
# Ensure provider API keys are not set during unit tests
os.environ.pop("TAVILY_API_KEY", None)
os.environ.pop("SERPAPI_API_KEY", None)
os.environ["TAVILY_API_KEY"] = ""
os.environ["SERPAPI_API_KEY"] = ""

# Ensure an event loop exists for tests that use get_event_loop()
import asyncio  # noqa: E402
try:
    asyncio.get_running_loop()
except RuntimeError:
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except Exception:
        pass


@pytest.fixture(autouse=True)
def ensure_event_loop():
    import asyncio
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    yield


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