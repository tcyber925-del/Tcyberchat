import json
import pytest

from backend.src.services.index_retry_queue_redis import RedisIndexJobQueue
import backend.src.api.admin_vectorstore as admin_mod


@pytest.mark.asyncio
async def test_list_and_process_scheduled(monkeypatch):
    import fakeredis

    fake = fakeredis.FakeRedis()
    # shim redis so Redis.from_url returns our fake client
    import backend.src.services.index_retry_queue_redis as rq

    class _Shim:
        class Redis:
            @staticmethod
            def from_url(url, decode_responses=True):
                return fake

    monkeypatch.setattr(rq, "redis", _Shim)

    q = RedisIndexJobQueue(url="redis://unused")

    # schedule a job with no delay
    payload = {"texts": ["x"], "metadatas": [{}]}
    job = q._make_job(payload)
    q.schedule_job(job, delay_seconds=0)

    # Ensure the admin function uses our queue instance
    import backend.src.services.index_retry_queue as irq
    monkeypatch.setattr(irq, "get_index_job_queue", lambda: q)

    # list via admin function
    res = await admin_mod.list_scheduled_jobs()
    assert res["size"] >= 1

    # process scheduled
    p = await admin_mod.process_scheduled_jobs()
    assert p["moved"] >= 1
    # now queue should have an item
    qlist = q.list()
    assert len(qlist) >= 1
