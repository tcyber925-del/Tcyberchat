import json
import asyncio

import fakeredis

from backend.src.services import index_retry_queue_redis as rq_mod
from backend.src.services.index_retry_queue_redis import RedisIndexJobQueue


def test_atomic_ack_and_release(monkeypatch):
    fake = fakeredis.FakeRedis()

    class _Shim:
        class Redis:
            @staticmethod
            def from_url(url, decode_responses=True):
                return fake

    monkeypatch.setattr(rq_mod, "redis", _Shim)

    q = RedisIndexJobQueue(url="redis://unused")

    # enqueue and claim
    job = asyncio.get_event_loop().run_until_complete(q.enqueue({"texts": ["x"], "metadatas": [{}]}))
    jid = job.get("id")

    claimed = q.claim_next(visibility_seconds=10)
    assert claimed is not None and claimed.get("id") == jid

    # processing list should contain the raw JSON and meta should exist
    proc_items = fake.lrange(q.PROCESSING_KEY, 0, -1)
    assert any(jid in (item if isinstance(item, str) else item.decode()) for item in proc_items)
    meta = fake.hget(q.PROCESSING_META, jid)
    assert meta is not None

    # ack should remove processing entry and meta atomically
    ok = q.ack(jid)
    assert ok is True
    proc_items_after = fake.lrange(q.PROCESSING_KEY, 0, -1)
    assert not any(jid in (item if isinstance(item, str) else item.decode()) for item in proc_items_after)
    assert fake.hget(q.PROCESSING_META, jid) is None

    # enqueue another, claim then release back to queue
    job2 = asyncio.get_event_loop().run_until_complete(q.enqueue({"texts": ["y"], "metadatas": [{}]}))
    jid2 = job2.get("id")
    claimed2 = q.claim_next(visibility_seconds=10)
    assert claimed2 is not None and claimed2.get("id") == jid2

    # release with no delay should push back to main queue
    ok2 = q.release(jid2, delay_seconds=0)
    assert ok2 is True

    # processing should no longer have jid2 and main queue should contain it
    assert fake.hget(q.PROCESSING_META, jid2) is None
    main_items = fake.lrange(q.KEY, 0, -1)
    assert any(jid2 in (m if isinstance(m, str) else m.decode()) for m in main_items)
