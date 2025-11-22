import os


def test_metrics_http_endpoint():
    # Force in-memory queue before importing app to avoid Redis adapter
    os.environ["INDEX_RETRY_QUEUE_BACKEND"] = "inmemory"

    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    text = resp.text
    # basic assertions that our metrics are present
    assert "index_retry_processed_total" in text
    assert "index_retry_queue_size" in text
