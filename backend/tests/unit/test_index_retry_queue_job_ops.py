import pytest


@pytest.mark.asyncio
async def test_get_and_cancel_job():
    import backend.src.services.index_retry_queue as irq
    from backend.src.api import admin_vectorstore as admin_mod

    q = irq.get_index_job_queue()
    async with q._lock:
        q._jobs = []

    payload = {"texts": ["x"], "metadatas": [{"doc_id": "1"}]}
    job = await q.enqueue(payload)

    # get via queue API
    got = q.get_job(job.id)
    assert got is not None
    assert got["id"] == job.id

    # call admin handler directly
    res = await admin_mod.get_index_job(job.id)
    assert res["id"] == job.id

    # cancel via admin handler
    res2 = await admin_mod.cancel_index_job(job.id)
    assert res2 == {"cancelled": True}

    # after cancel, job should not be listed
    listed = q.list()
    assert not any(j["id"] == job.id for j in listed)


@pytest.mark.asyncio
async def test_cancel_nonexistent_job():
    import backend.src.services.index_retry_queue as irq
    from backend.src.api import admin_vectorstore as admin_mod
    from fastapi import HTTPException

    q = irq.get_index_job_queue()
    async with q._lock:
        q._jobs = []

    with pytest.raises(HTTPException):
        await admin_mod.cancel_index_job("nonexistent")
