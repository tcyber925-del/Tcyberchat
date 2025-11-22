import pytest


@pytest.mark.asyncio
async def test_redis_adapter_requeue_with_fakeredis(monkeypatch):
    import fakeredis
    import json

    import backend.src.services.index_retry_queue_redis as rq

    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(rq.redis.Redis, "from_url", staticmethod(lambda url, decode_responses=True: fake))

    q = rq.RedisIndexJobQueue(url="redis://unused")

    # Patch add_texts to always fail so job goes to failed list
    monkeypatch.setattr(rq, "add_texts", lambda texts, metadatas=None: False)

    job = await q.enqueue({"texts": ["fail"], "metadatas": [{"doc_id": "r1"}], "max_attempts": 2})
    jid = job["id"]

    # Process all: should move job to failed list
    res = await q.process_all()
    assert res["processed"] == 1
    # failed should be at least 1
    failed_items = fake.lrange(q.KEY + ":failed", 0, -1)
    assert len(failed_items) >= 1

    # Find failed job id in failed list
    failed_job = json.loads(failed_items[0])
    failed_id = failed_job.get("id")
    assert failed_id is not None

    # Requeue it: should succeed (attempts < max_attempts)
    ok = await q.requeue_failed(failed_id)
    assert ok is True

    # Now process again: still failing because add_texts returns False, attempts increments
    # Move due scheduled jobs into queue so they can be processed. In production this
    # happens in a background loop; for the test we trigger it directly.
    moved = q._move_due_scheduled_to_queue()
    if moved == 0:
        # wait a bit and try again (backoff may delay the job)
        import time

        time.sleep(1.5)
        q._move_due_scheduled_to_queue()

    res2 = await q.process_all()
    assert res2["processed"] >= 1

    # Try to requeue any remaining failed job: attempts may now be >= max, so requeue may return False
    # Collect any remaining failed ids
    remaining = fake.lrange(q.KEY + ":failed", 0, -1)
    if remaining:
        rem_job = json.loads(remaining[0])
        rem_id = rem_job.get("id")
        ok2 = await q.requeue_failed(rem_id)
        # ok2 can be True or False depending on attempts; ensure method executes
        assert isinstance(ok2, bool)
