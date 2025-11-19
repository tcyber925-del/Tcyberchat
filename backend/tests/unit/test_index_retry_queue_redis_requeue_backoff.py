import json
import time

import fakeredis
import pytest

from backend.src.services import index_retry_queue_redis as redis_mod
from backend.src.services.index_retry_queue_redis import RedisIndexJobQueue


@pytest.fixture()
def fake_redis(monkeypatch):
    r = fakeredis.FakeRedis()
    class _Shim:
        class Redis:
            @staticmethod
            def from_url(url, decode_responses=True):
                return r

    monkeypatch.setattr(redis_mod, "redis", _Shim)
    return r


def test_requeue_failed_schedules_with_backoff(fake_redis):
    q = RedisIndexJobQueue(url="redis://localhost:6379/0")
    # build a failed job entry
    payload = {"texts": ["x"], "metadatas": [{}], "attempts": 0, "max_attempts": 3}
    job = {"id": "job1", "status": "failed", "payload": payload, "error": "boom"}
    # push to failed list
    q._client.rpush(q.KEY + ":failed", json.dumps(job))
    # call requeue_failed
    import asyncio

    ok = asyncio.get_event_loop().run_until_complete(q.requeue_failed("job1"))
    assert ok is True
    # scheduled set should have one member
    scheduled = q.list_scheduled()
    assert len(scheduled) == 1
    # the stored payload attempts should be incremented
    members = q._client.zrange(q.SCHEDULED_KEY, 0, -1, withscores=True)
    member, score = members[0]
    j = json.loads(member)
    assert j["payload"]["attempts"] == 1
    # score should be roughly now + base_backoff * jitter (attempts was 0 so base=1)
    now = time.time()
    # allow a bit of slack around the jitter window
    assert now + 0.4 <= score <= now + 1.6
