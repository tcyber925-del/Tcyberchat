import json
import time

import fakeredis
import pytest

from backend.src.services import index_retry_queue_redis as redis_mod
from backend.src.services.index_retry_queue_redis import RedisIndexJobQueue


@pytest.fixture()
def fake_redis(monkeypatch):
    r = fakeredis.FakeRedis()
    # set a small shim module object with Redis.from_url returning our fake client
    class _Shim:
        class Redis:
            @staticmethod
            def from_url(url, decode_responses=True):
                return r

    monkeypatch.setattr(redis_mod, "redis", _Shim)
    return r


def test_schedule_and_move_due(fake_redis):
    q = RedisIndexJobQueue(url="redis://localhost:6379/0")
    # create a simple payload
    payload = {"texts": ["hello world"], "metadatas": [{"source": "test"}], "delay_seconds": 1}
    job = q._make_job(payload)
    # schedule with 1 second delay
    q.schedule_job(job, delay_seconds=1)
    scheduled = q.list_scheduled()
    assert len(scheduled) == 1
    # ensure it's not moved yet
    moved = q._move_due_scheduled_to_queue()
    assert moved in (0, 1)  # depending on timing; tolerate immediate move
    # if not moved yet, wait and move
    if moved == 0:
        time.sleep(1.1)
        moved = q._move_due_scheduled_to_queue()
        assert moved == 1
    # now queue should have one item
    lst = q.list()
    assert len(lst) == 1


def test_enqueue_with_delay_places_in_scheduled(fake_redis):
    q = RedisIndexJobQueue(url="redis://localhost:6379/0")
    payload = {"texts": ["t"], "metadatas": [{}], "delay_seconds": 2}
    # call enqueue (async) synchronously for test
    import asyncio

    asyncio.get_event_loop().run_until_complete(q.enqueue(payload))
    scheduled = q.list_scheduled()
    assert len(scheduled) == 1
