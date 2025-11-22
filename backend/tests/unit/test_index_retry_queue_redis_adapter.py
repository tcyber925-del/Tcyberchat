import pytest


@pytest.mark.asyncio
async def test_redis_adapter_with_fakeredis(monkeypatch):
    # Use fakeredis to mock the redis client used by the adapter
    import fakeredis

    import backend.src.services.index_retry_queue_redis as rq

    fake = fakeredis.FakeRedis()

    # Patch the redis.Redis.from_url used by the module to return our fake
    # The module imported `redis` at top-level, so modify rq.redis.Redis.from_url
    monkeypatch.setattr(rq.redis.Redis, "from_url", staticmethod(lambda url, decode_responses=True: fake))

    # Instantiate the Redis adapter (will use patched from_url)
    q = rq.RedisIndexJobQueue(url="redis://unused")

    # Enqueue a job
    job = await q.enqueue({"texts": ["hello"], "metadatas": [{"doc_id": "r1"}]})
    assert isinstance(job.get("id"), str)

    # List should show the queued job
    listed = q.list()
    assert any(j["id"] == job["id"] for j in listed)

    # get_job should return the job metadata
    got = q.get_job(job["id"])
    assert got and got["id"] == job["id"]

    # Process all should pop and attempt add_texts; monkeypatch add_texts to True
    # Patch the add_texts used inside the redis adapter module
    monkeypatch.setattr(rq, "add_texts", lambda texts, metadatas=None: True)

    res = await q.process_all()
    assert res["processed"] >= 1
    assert res["succeeded"] >= 1
