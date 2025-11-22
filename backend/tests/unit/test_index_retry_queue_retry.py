import pytest


@pytest.mark.asyncio
async def test_retry_job():
    import backend.src.services.index_retry_queue as irq
    from backend.src.api import admin_vectorstore as admin_mod

    q = irq.get_index_job_queue()
    async with q._lock:
        q._jobs = []

    payload = {"texts": ["retryme"], "metadatas": [{"doc_id": "r1"}]}
    job = await q.enqueue(payload)

    res = await admin_mod.retry_index_job(job.id)
    assert "requeued_job_id" in res
    new_id = res["requeued_job_id"]
    assert new_id != job.id

    # ensure new job exists
    found = q.get_job(new_id)
    assert found is not None


@pytest.mark.asyncio
async def test_retry_nonexistent_job():
    from backend.src.api import admin_vectorstore as admin_mod
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        await admin_mod.retry_index_job("no-such-id")
