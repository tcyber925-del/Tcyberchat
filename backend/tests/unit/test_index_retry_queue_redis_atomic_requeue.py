import json
import asyncio

import fakeredis

from backend.src.services import index_retry_queue_redis as rq_mod
from backend.src.services.index_retry_queue_redis import RedisIndexJobQueue


def test_atomic_requeue_from_failed(monkeypatch):
    fake = fakeredis.FakeRedis()

    class _Shim:
        class Redis:
            @staticmethod
            def from_url(url, decode_responses=True):
                return fake

    monkeypatch.setattr(rq_mod, "redis", _Shim)

    q = RedisIndexJobQueue(url="redis://unused")

    # create a failed job entry manually
    job = asyncio.get_event_loop().run_until_complete(q.enqueue({"texts": ["z"], "metadatas": [{}]}))
    jid = job.get("id")
    # push raw job JSON to failed list to simulate a processing failure
    fake.rpush(q.KEY + ":failed", json.dumps(job))

    # call requeue_failed and assert it returns True
    ok = asyncio.get_event_loop().run_until_complete(q.requeue_failed(jid))
    assert ok is True

    # scheduled zset should now contain one member with updated attempts
    sched = fake.zrange(q.SCHEDULED_KEY, 0, -1)
    assert len(sched) >= 1
    found = False
    for m in sched:
        raw = m if isinstance(m, str) else m.decode()
        obj = json.loads(raw)
        if obj.get("id") == jid:
            found = True
            assert obj.get("payload", {}).get("attempts", 0) >= 1
    assert found
