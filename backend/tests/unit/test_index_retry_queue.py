import pytest

from backend.src.services import index_retry_queue as irq


@pytest.mark.asyncio
async def test_enqueue_and_list():
    q = irq.get_index_job_queue()
    # clear any existing jobs to isolate test
    async with q._lock:
        q._jobs = []

    payload = {"texts": ["sample text"], "metadatas": [{"doc_id": "1"}]}
    job = await q.enqueue(payload)

    listed = q.list()
    assert any(j["id"] == job.id and j["status"] == "queued" for j in listed)


@pytest.mark.asyncio
async def test_process_all_success(monkeypatch):
    q = irq.get_index_job_queue()
    async with q._lock:
        q._jobs = []

    payload = {"texts": ["t1"], "metadatas": [{"doc_id": "x"}]}
    await q.enqueue(payload)

    # stub add_texts to simulate successful indexing
    monkeypatch.setattr(irq, "add_texts", lambda texts, metadatas=None: True)

    res = await q.process_all()
    assert res["processed"] == 1
    assert res["succeeded"] == 1
    assert res["failed"] == 0


@pytest.mark.asyncio
async def test_process_all_failure(monkeypatch):
    q = irq.get_index_job_queue()
    async with q._lock:
        q._jobs = []

    payload = {"texts": ["t1"], "metadatas": [{"doc_id": "x"}]}
    await q.enqueue(payload)

    # stub add_texts to simulate failing indexing
    monkeypatch.setattr(irq, "add_texts", lambda texts, metadatas=None: False)

    res = await q.process_all()
    assert res["processed"] == 1
    assert res["succeeded"] == 0
    assert res["failed"] == 1
