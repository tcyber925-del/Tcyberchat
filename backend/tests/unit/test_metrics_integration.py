import pytest


@pytest.mark.asyncio
async def test_metrics_endpoint_and_counters(monkeypatch):
    # Ensure we use the in-memory queue for this test
    import os
    os.environ["INDEX_RETRY_QUEUE_BACKEND"] = "inmemory"

    from backend.src.services import index_retry_queue as irq
    from backend.src.services import metrics as metrics_mod
    from backend.src.api import metrics as metrics_api

    q = irq.get_index_job_queue()
    async with q._lock:
        q._jobs = []

    # Reset registry counters by creating a fresh registry in metrics module
    # (the module-level registry is used; for test isolation we rely on increments)

    # Enqueue a job and ensure gauge increments
    await q.enqueue({"texts": ["m1"], "metadatas": [{"doc_id": "m1"}]})
    # call list to update gauge
    _ = q.list()

    # Now patch add_texts used by queue processing to always succeed
    monkeypatch.setattr(irq, "add_texts", lambda texts, metadatas=None: True, raising=False)

    res = await q.process_all()
    assert res["processed"] >= 1

    # render metrics and check metric names present
    payload = metrics_mod.render_metrics().decode("utf-8")
    assert "index_retry_processed_total" in payload
    assert "index_retry_succeeded_total" in payload
    assert "index_retry_queue_size" in payload
