import json
import pytest

import fakeredis


@pytest.mark.asyncio
async def test_processing_admin_endpoints(monkeypatch):
    import backend.src.services.index_retry_queue_redis as rq
    import backend.src.api.admin_vectorstore as admin_mod

    fake = fakeredis.FakeRedis()

    class _Shim:
        class Redis:
            @staticmethod
            def from_url(url, decode_responses=True):
                return fake

    monkeypatch.setattr(rq, "redis", _Shim)

    q = rq.RedisIndexJobQueue(url="redis://unused")

    # ensure factory returns our queue
    import backend.src.services.index_retry_queue as irq

    monkeypatch.setattr(irq, "get_index_job_queue", lambda: q)

    # enqueue and claim a job
    job = await q.enqueue({"texts": ["x"], "metadatas": [{}]})
    jid = job["id"] if isinstance(job, dict) else getattr(job, "id")

    claimed = q.claim_next(visibility_seconds=10)
    assert claimed is not None

    # list processing jobs via admin endpoint
    res = await admin_mod.list_processing_jobs()
    assert res["size"] >= 1

    # ack via admin endpoint
    ack_res = await admin_mod.ack_processing_job(jid)
    assert ack_res == {"acked": True}

    # enqueue and claim again for release test
    job2 = await q.enqueue({"texts": ["y"], "metadatas": [{}]})
    jid2 = job2.get("id")
    claimed2 = q.claim_next(visibility_seconds=10)
    assert claimed2 is not None

    # release via admin endpoint
    rel = await admin_mod.release_processing_job(jid2, delay_seconds=0)
    assert rel == {"released": True}

    # force reclaim (no-op here but should return int)
    rec = await admin_mod.reclaim_processing_jobs()
    assert isinstance(rec["reclaimed"], int)
