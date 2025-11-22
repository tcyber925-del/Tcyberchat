import json
import time

import fakeredis
import pytest

from backend.src.services import index_retry_queue_redis as rq_mod
from backend.src.services.index_retry_queue_redis import RedisIndexJobQueue


@pytest.fixture()
def fake_redis(monkeypatch):
    fake = fakeredis.FakeRedis()

    class _Shim:
        class Redis:
            @staticmethod
            def from_url(url, decode_responses=True):
                return fake

    monkeypatch.setattr(rq_mod, "redis", _Shim)
    return fake


def test_claim_ack_and_reclaim(fake_redis):
    q = RedisIndexJobQueue(url="redis://unused")
    # enqueue a job
    import asyncio

    job = asyncio.get_event_loop().run_until_complete(q.enqueue({"texts": ["a"], "metadatas": [{}]}))
    jid = job["id"] if isinstance(job, dict) else getattr(job, "id")

    # claim the job with short visibility
    claimed = q.claim_next(visibility_seconds=1)
    assert claimed is not None
    assert claimed.get("id") == jid

    # ack the job
    ok = q.ack(jid)
    assert ok is True

    # enqueue another job and claim but do not ack; ensure reclaim works
    job2 = asyncio.get_event_loop().run_until_complete(q.enqueue({"texts": ["b"], "metadatas": [{}]}))
    jid2 = job2.get("id")
    claimed2 = q.claim_next(visibility_seconds=1)
    assert claimed2 is not None
    assert claimed2.get("id") == jid2

    # wait for visibility to expire and then reclaim
    time.sleep(1.2)
    reclaimed = q.reclaim_expired()
    assert reclaimed >= 1

    # move due scheduled to queue and process
    moved = q._move_due_scheduled_to_queue()
    assert moved >= 1

    # now claim again should get the job
    claimed3 = q.claim_next(visibility_seconds=1)
    assert claimed3 is not None
    assert claimed3.get("id") == jid2
