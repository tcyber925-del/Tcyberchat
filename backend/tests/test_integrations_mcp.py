import time
from fastapi.testclient import TestClient

import importlib


def setup_dummy(monkeypatch, models=None):
    # Simple dummy AI service to avoid external calls
    class DummyService:
        def __init__(self, model_name=None):
            self.model_name = model_name

        def get_available_models(self):
            return models if models is not None else [{"name": "dummy-model", "provider": "none", "size": 0, "modified_at": "now"}]

    # Patch the module path used by the running app (src.api.integrations_mcp)
    try:
        m = importlib.import_module("src.api.integrations_mcp")
    except Exception:
        m = importlib.import_module("backend.src.api.integrations_mcp")
    monkeypatch.setattr(m, "get_ai_service", lambda model=None: DummyService(model))
    return m


def test_health_and_metrics(monkeypatch):
    m = setup_dummy(monkeypatch, models=[{"name": "m1", "provider": "none", "size": 0, "modified_at": "now"}])
    # Import main app after monkeypatching integrations module so the patched symbol is used
    main_app = importlib.import_module("backend.main")
    client = TestClient(main_app.app)

    r = client.get("/api/integrations/mcp/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("ai") and body["ai"].get("available_models") == 1

    # metrics endpoint should reflect the health check
    r2 = client.get("/api/integrations/mcp/metrics")
    assert r2.status_code == 200
    metrics = r2.json().get("metrics", {})
    assert metrics.get("health_check_count", 0) >= 1


def test_init_model_and_cooldown(monkeypatch):
    m = setup_dummy(monkeypatch)
    main_app = importlib.import_module("backend.main")
    client = TestClient(main_app.app)

    # First init should start
    r = client.post("/api/integrations/mcp/init-model", json={"model": "dummy-model"})
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("started") is True

    # Immediately call again; should be blocked by cooldown
    r2 = client.post("/api/integrations/mcp/init-model", json={"model": "dummy-model"})
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2.get("ok") is False
    assert "cooldown" in (body2.get("error") or "").lower()

    # Metrics should show two requests, and at least one started (background task)
    time.sleep(0.1)
    r3 = client.get("/api/integrations/mcp/metrics")
    metrics = r3.json().get("metrics", {})
    assert metrics.get("init_request_count", 0) >= 2
    # init_started_count may be incremented by background task; ensure key exists
    assert "init_started_count" in metrics
