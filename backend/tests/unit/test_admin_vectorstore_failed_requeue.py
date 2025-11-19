import json
import pytest


@pytest.mark.asyncio
async def test_list_and_requeue_failed(monkeypatch):
    import fakeredis

    import backend.src.services.index_retry_queue_redis as rq
    import backend.src.api.admin_vectorstore as admin_mod

    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(rq.redis.Redis, "from_url", staticmethod(lambda url, decode_responses=True: fake))

    q = rq.RedisIndexJobQueue(url="redis://unused")

    # make add_texts fail so job goes to failed list
    monkeypatch.setattr(rq, "add_texts", lambda texts, metadatas=None: False)

    job = await q.enqueue({"texts": ["x"], "metadatas": [{"doc_id": "f1"}], "max_attempts": 2})
    # process -> moves to failed
    await q.process_all()

    # list failed via admin function
    res = await admin_mod.list_failed_jobs()
    assert res["size"] >= 1

    # pick a failed job id
    items = fake.lrange(q.KEY + ":failed", 0, -1)
    fj = json.loads(items[0])
    fid = fj.get("id")

    # requeue using admin handler
    resp = await admin_mod.requeue_failed_job(fid)
    assert resp == {"requeued": True}
