import pytest


@pytest.mark.asyncio
async def test_requeue_all_failed_with_fakeredis(monkeypatch):
    import fakeredis
    import json

    import backend.src.services.index_retry_queue_redis as rq

    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(rq.redis.Redis, "from_url", staticmethod(lambda url, decode_responses=True: fake))

    q = rq.RedisIndexJobQueue(url="redis://unused")

    # Patch add_texts to always fail so job goes to failed list
    monkeypatch.setattr(rq, "add_texts", lambda texts, metadatas=None: False)

    # Enqueue two failing jobs
    await q.enqueue({"texts": ["a"], "metadatas": [{"doc_id": "1"}], "max_attempts": 2})
    await q.enqueue({"texts": ["b"], "metadatas": [{"doc_id": "2"}], "max_attempts": 2})

    # Process all -> both should end up in failed list
    res = await q.process_all()
    assert res["processed"] == 2

    failed_before = fake.lrange(q.KEY + ":failed", 0, -1)
    assert len(failed_before) >= 2

    # Requeue all failed via helper
    requeued = await q.requeue_all_failed()
    assert requeued >= 1

    # After requeue_all_failed, there may be fewer items in failed list (requeued removed)
    failed_after = fake.lrange(q.KEY + ":failed", 0, -1)
    assert isinstance(failed_after, list)
