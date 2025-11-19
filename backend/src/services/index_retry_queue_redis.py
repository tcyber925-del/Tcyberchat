"""Redis-backed retry queue adapter for indexing jobs.

This adapter is optional and used when `INDEX_RETRY_QUEUE_BACKEND=redis`.
It keeps job entries as JSON strings in a Redis list key and provides a
minimal API compatible with `IndexJobQueue` used elsewhere in the codebase.

The implementation below is intentionally pragmatic for tests: it provides
the same observable semantics the test-suite expects (enqueue, schedule,
process_all, failed list, claiming/ack/release) while avoiding overly
complex Lua scripts. For production, consider more robust atomic scripts
and error handling.
"""
from __future__ import annotations

import json
import uuid
import time
import random
from typing import Any, Dict, List

try:
    import redis
except Exception:
    # In test environments, a shim or fakeredis may be provided.
    import redis  # re-raise

from .vectorstore_manager import add_texts
from . import metrics


class RedisIndexJobQueue:
    KEY = "index_retry_queue"
    SCHEDULED_KEY = KEY + ":scheduled"
    PROCESSING_KEY = KEY + ":processing"
    PROCESSING_META = KEY + ":processing_meta"

    def __init__(self, url: str | None = None):
        import os

        redis_url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

        # Provide an asyncio.Lock-like placeholder for tests that do `async with q._lock`
        try:
            import asyncio

            self._lock = asyncio.Lock()
        except Exception:
            self._lock = None

    def _make_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        p = dict(payload) if isinstance(payload, dict) else {"data": payload}
        p.setdefault("attempts", 0)
        p.setdefault("max_attempts", 3)
        return {"id": uuid.uuid4().hex, "status": "queued", "payload": p, "error": None}

    def _now_seconds(self) -> float:
        return time.time()

    def schedule_job(self, job: Dict[str, Any], delay_seconds: int | float = 0) -> bool:
        score = self._now_seconds() + float(delay_seconds or 0)
        self._client.zadd(self.SCHEDULED_KEY, {json.dumps(job): score})
        try:
            metrics.INDEX_RETRY_SCHEDULED_SIZE.set(self._client.zcard(self.SCHEDULED_KEY))
        except Exception:
            pass
        return True

    def claim_next(self, visibility_seconds: int = 60) -> Dict[str, Any] | None:
        # Best-effort claim: RPOPLPUSH into processing list and set meta
        try:
            raw = self._client.rpoplpush(self.KEY, self.PROCESSING_KEY)
        except Exception:
            raw = None
        if not raw:
            return None
        try:
            job = json.loads(raw)
        except Exception:
            # malformed entry; remove and skip
            try:
                self._client.lrem(self.PROCESSING_KEY, 1, raw)
            except Exception:
                pass
            return None
        jid = job.get("id")
        now = float(self._now_seconds())
        meta = {"claimed_at": now, "visibility": int(visibility_seconds), "expires_at": now + float(visibility_seconds)}
        try:
            self._client.hset(self.PROCESSING_META, jid, json.dumps(meta))
        except Exception:
            pass
        return job

    def ack(self, job_id: str) -> bool:
        try:
            self._client.hdel(self.PROCESSING_META, job_id)
        except Exception:
            pass
        items = self._client.lrange(self.PROCESSING_KEY, 0, -1)
        for v in items:
            try:
                j = json.loads(v)
            except Exception:
                continue
            if j.get("id") == job_id:
                try:
                    self._client.lrem(self.PROCESSING_KEY, 1, v)
                except Exception:
                    pass
                return True
        return False

    def release(self, job_id: str, delay_seconds: float | None = None) -> bool:
        items = self._client.lrange(self.PROCESSING_KEY, 0, -1)
        for v in items:
            try:
                j = json.loads(v)
            except Exception:
                continue
            if j.get("id") == job_id:
                try:
                    self._client.hdel(self.PROCESSING_META, job_id)
                except Exception:
                    pass
                try:
                    self._client.lrem(self.PROCESSING_KEY, 1, v)
                except Exception:
                    pass
                if delay_seconds and delay_seconds > 0:
                    self.schedule_job(j, delay_seconds=delay_seconds)
                else:
                    try:
                        self._client.rpush(self.KEY, v)
                    except Exception:
                        pass
                return True
        return False

    def reclaim_expired(self) -> int:
        now = float(self._now_seconds())
        reclaimed = 0
        # Iterate the processing list directly and check meta for each job.
        try:
            processing_items = self._client.lrange(self.PROCESSING_KEY, 0, -1)
        except Exception:
            processing_items = []

        for raw in processing_items:
            try:
                j = json.loads(raw)
            except Exception:
                # malformed entry - remove and push back to queue
                try:
                    self._client.lrem(self.PROCESSING_KEY, 1, raw)
                    self._client.lpush(self.KEY, raw)
                except Exception:
                    pass
                reclaimed += 1
                continue

            jid = j.get("id")
            try:
                meta_raw = self._client.hget(self.PROCESSING_META, jid)
            except Exception:
                meta_raw = None

            if not meta_raw:
                # No metadata — treat as expired: move back to queue and remove any meta
                try:
                    self._client.lrem(self.PROCESSING_KEY, 1, raw)
                    # schedule immediately for re-delivery via the scheduled zset
                    self._client.zadd(self.SCHEDULED_KEY, {raw: now})
                    self._client.hdel(self.PROCESSING_META, jid)
                except Exception:
                    pass
                reclaimed += 1
                continue

            try:
                meta = json.loads(meta_raw)
            except Exception:
                meta = {}

            try:
                expires = float(meta.get("expires_at", 0))
            except Exception:
                expires = 0.0

            if expires and expires < now:
                try:
                    self._client.lrem(self.PROCESSING_KEY, 1, raw)
                    # schedule for immediate re-delivery
                    self._client.zadd(self.SCHEDULED_KEY, {raw: now})
                    self._client.hdel(self.PROCESSING_META, jid)
                except Exception:
                    pass
                reclaimed += 1

        return reclaimed

    def list(self) -> List[Dict[str, Any]]:
        items = self._client.lrange(self.KEY, 0, -1)
        out: List[Dict[str, Any]] = []
        for v in items:
            try:
                j = json.loads(v)
                out.append({"id": j.get("id"), "status": j.get("status"), "error": j.get("error")})
            except Exception:
                continue
        return out

    def list_failed(self) -> List[Dict[str, Any]]:
        items = self._client.lrange(self.KEY + ":failed", 0, -1)
        out: List[Dict[str, Any]] = []
        for v in items:
            try:
                j = json.loads(v)
                out.append({"id": j.get("id"), "status": j.get("status"), "error": j.get("error")})
            except Exception:
                continue
        return out

    def get_job(self, job_id: str) -> Dict[str, Any] | None:
        items = self._client.lrange(self.KEY, 0, -1)
        for v in items:
            try:
                j = json.loads(v)
            except Exception:
                continue
            if j.get("id") == job_id:
                return {"id": j.get("id"), "status": j.get("status"), "error": j.get("error")}
        return None

    async def enqueue(self, payload: Dict[str, Any]):
        delay = 0
        if isinstance(payload, dict) and "delay_seconds" in payload:
            try:
                delay = float(payload.get("delay_seconds", 0))
            except Exception:
                delay = 0
        job = self._make_job(payload)
        if delay and float(delay) > 0:
            self.schedule_job(job, delay_seconds=delay)
        else:
            try:
                self._client.rpush(self.KEY, json.dumps(job))
            except Exception:
                pass
        return job

    async def cancel(self, job_id: str) -> bool:
        items = self._client.lrange(self.KEY, 0, -1)
        for v in items:
            try:
                j = json.loads(v)
            except Exception:
                continue
            if j.get("id") == job_id:
                try:
                    self._client.lrem(self.KEY, 1, v)
                except Exception:
                    pass
                return True
        return False

    def requeue_failed(self, job_id: str) -> bool:
        # Move a job from failed list back to active queue, incrementing attempts and applying backoff
        items = self._client.lrange(self.KEY + ":failed", 0, -1)
        for v in items:
            try:
                j = json.loads(v)
            except Exception:
                continue
            if j.get("id") == job_id:
                payload = j.get("payload") or {}
                attempts = int(payload.get("attempts", 0)) + 1
                payload["attempts"] = attempts
                # compute backoff: 2^attempts capped
                backoff = min(2 ** attempts, 3600)
                jitter = random.uniform(0.5, 1.5)
                delay = int(backoff * jitter)
                j["payload"] = payload
                # remove from failed and schedule
                try:
                    self._client.lrem(self.KEY + ":failed", 1, v)
                except Exception:
                    pass
                self.schedule_job(j, delay_seconds=delay)
                try:
                    metrics.INDEX_RETRY_BACKOFF_SECONDS.observe(delay)
                except Exception:
                    pass
                return True
        return False

    def requeue_all_failed(self) -> int:
        items = self._client.lrange(self.KEY + ":failed", 0, -1)
        count = 0
        for v in items:
            try:
                j = json.loads(v)
            except Exception:
                continue
            jid = j.get("id")
            if self.requeue_failed(jid):
                count += 1
        return count

    def list_scheduled(self) -> List[Dict[str, Any]]:
        items = self._client.zrange(self.SCHEDULED_KEY, 0, -1, withscores=True)
        out = []
        for member, score in items:
            try:
                j = json.loads(member)
                out.append({"job": j, "score": score})
            except Exception:
                continue
        return out

    def _move_due_scheduled_to_queue(self) -> int:
        now = self._now_seconds()
        # get due items
        try:
            due = self._client.zrangebyscore(self.SCHEDULED_KEY, 0, now)
        except Exception:
            due = []
        moved = 0
        for member in due:
            try:
                # remove from scheduled and push to queue
                self._client.zrem(self.SCHEDULED_KEY, member)
                self._client.rpush(self.KEY, member)
                moved += 1
            except Exception:
                pass
        try:
            metrics.INDEX_RETRY_SCHEDULED_MOVED.inc(moved)
            metrics.INDEX_RETRY_SCHEDULED_SIZE.set(self._client.zcard(self.SCHEDULED_KEY))
        except Exception:
            pass
        return moved

    def process_all(self) -> int:
        # Move due scheduled jobs first
        self._move_due_scheduled_to_queue()
        processed = 0
        while True:
            try:
                raw = self._client.lpop(self.KEY)
            except Exception:
                raw = None
            if not raw:
                break
            processed += 1
            try:
                j = json.loads(raw)
            except Exception:
                # push to failed list for inspection
                try:
                    self._client.rpush(self.KEY + ":failed", raw)
                except Exception:
                    pass
                continue
            # call add_texts (vectorstore ingestion); tests monkeypatch this
            try:
                ok = add_texts([j.get("payload")])
            except Exception:
                ok = False
            if not ok:
                # push to failed list
                try:
                    self._client.rpush(self.KEY + ":failed", json.dumps(j))
                except Exception:
                    pass
            else:
                try:
                    metrics.INDEX_RETRY_PROCESSED.inc()
                    metrics.INDEX_RETRY_SUCCEEDED.inc()
                except Exception:
                    pass
        try:
            metrics.INDEX_RETRY_QUEUE_SIZE.set(self._client.llen(self.KEY))
        except Exception:
            pass
        return processed

    def list(self) -> List[Dict[str, Any]]:
        items = self._client.lrange(self.KEY, 0, -1)
        out: List[Dict[str, Any]] = []
        for v in items:
            try:
                j = json.loads(v)
                # normalize shape
                out.append({"id": j.get("id"), "status": j.get("status"), "error": j.get("error")})
            except Exception:
                continue
        return out

    def list_failed(self) -> List[Dict[str, Any]]:
        items = self._client.lrange(self.KEY + ":failed", 0, -1)
        out: List[Dict[str, Any]] = []
        for v in items:
            try:
                j = json.loads(v)
                out.append({"id": j.get("id"), "status": j.get("status"), "error": j.get("error")})
            except Exception:
                continue
        return out

    def get_job(self, job_id: str) -> Dict[str, Any] | None:
        items = self._client.lrange(self.KEY, 0, -1)
        for v in items:
            try:
                j = json.loads(v)
            except Exception:
                continue
            if j.get("id") == job_id:
                return {"id": j.get("id"), "status": j.get("status"), "error": j.get("error")}
        return None

    async def enqueue(self, payload: Dict[str, Any]):
        # Accept optional `delay_seconds` inside payload for compatibility with callers.
        delay = 0
        if isinstance(payload, dict) and "delay_seconds" in payload:
            try:
                delay = float(payload.get("delay_seconds", 0))
            except Exception:
                delay = 0
        job = self._make_job(payload)
        if delay and float(delay) > 0:
            self.schedule_job(job, delay_seconds=delay)
        else:
            self._client.rpush(self.KEY, json.dumps(job))
        return job

    async def cancel(self, job_id: str) -> bool:
        # Find matching element and remove it via LREM
        items = self._client.lrange(self.KEY, 0, -1)
        for v in items:
            try:
                j = json.loads(v)
            except Exception:
                continue
            if j.get("id") == job_id:
                # remove one occurrence
                self._client.lrem(self.KEY, 1, v)
                return True
        return False

    async def requeue_failed(self, job_id: str) -> bool:
        """Move a job from the failed list back to the main queue if attempts < max_attempts.

        Returns True if requeued, False if not found or max attempts exceeded.
        """
        # Try an atomic Lua path: find the matching raw JSON in the failed list,
        # increment its payload.attempts, remove it from failed list and ZADD
        # into the scheduled sorted-set with computed backoff (with jitter).
        lua = r"""
        local failed_key = KEYS[1]
        local sched_key = KEYS[2]
        local jid = ARGV[1]
        local now = tonumber(ARGV[2])
        local jitter_min = tonumber(ARGV[3])
        local jitter_max = tonumber(ARGV[4])
        -- iterate failed list to locate item
        local items = redis.call('LRANGE', failed_key, 0, -1)
        for i=1,#items do
            local raw = items[i]
            local ok, obj = pcall(cjson.decode, raw)
            if ok then
                local id = obj['id'] or obj.id
                if id == jid then
                    local payload = obj['payload'] or {}
                    local attempts = tonumber(payload['attempts'] or 0)
                    local max_attempts = tonumber(payload['max_attempts'] or 3)
                    if attempts >= max_attempts then
                        return -1
                    end
                    payload['attempts'] = attempts + 1
                    obj['payload'] = payload
                    local base = math.min(3600, 2 ^ attempts)
                    -- math.random returns [0,1) when called as math.random()
                    local jitter = (math.random() * (jitter_max - jitter_min)) + jitter_min
                    local backoff = base * jitter
                    local new_raw = cjson.encode(obj)
                    redis.call('LREM', failed_key, 1, raw)
                    redis.call('ZADD', sched_key, now + backoff, new_raw)
                    return backoff
                end
            end
        end
        return 0
        """

        try:
            try:
                # Provide now and jitter bounds as ARGV
                res = self._client.eval(
                    lua,
                    2,
                    self.KEY + ":failed",
                    self.SCHEDULED_KEY,
                    job_id,
                    float(self._now_seconds()),
                    0.5,
                    1.5,
                )
            except Exception:
                res = None
            # If Lua returned a positive backoff value, consider it requeued
            if res and float(res) > 0:
                try:
                    metrics.INDEX_RETRY_BACKOFF_SECONDS.observe(float(res))
                except Exception:
                    pass
                return True
            if res == -1:
                # exceeded max attempts
                return False
        except Exception:
            # fall through to Python fallback
            pass

        # Fallback: Scan the failed list in Python and do the same actions (non-atomic)
        items = self._client.lrange(self.KEY + ":failed", 0, -1)
        for v in items:
            try:
                j = json.loads(v)
            except Exception:
                continue
            if j.get("id") == job_id:
                payload = j.get("payload", {})
                attempts = payload.get("attempts", 0)
                max_attempts = payload.get("max_attempts", 3)
                if attempts >= max_attempts:
                    return False
                # increment attempts and schedule with exponential backoff
                payload["attempts"] = attempts + 1
                # reuse same job id and update payload in the scheduled member
                j["payload"] = payload
                new_raw = json.dumps(j)
                # remove the failed entry
                self._client.lrem(self.KEY + ":failed", 1, v)
                # exponential backoff: min cap to avoid enormous delays
                base = min(60 * 60, (2 ** attempts))
                # add jitter (0.5x - 1.5x) to spread retries
                backoff = base * random.uniform(0.5, 1.5)
                try:
                    metrics.INDEX_RETRY_BACKOFF_SECONDS.observe(backoff)
                except Exception:
                    pass
                # schedule the requeue instead of immediate push
                self._client.zadd(self.SCHEDULED_KEY, {new_raw: self._now_seconds() + backoff})
                return True
        return False

    async def requeue_all_failed(self) -> int:
        """Attempt to requeue all failed jobs. Returns number requeued."""
        requeued = 0
        items = self._client.lrange(self.KEY + ":failed", 0, -1)
        for v in list(items):
            try:
                j = json.loads(v)
            except Exception:
                continue
            jid = j.get("id")
            if not jid:
                continue
            ok = await self.requeue_failed(jid)
            if ok:
                requeued += 1
        return requeued

    def list_scheduled(self) -> List[Dict[str, Any]]:
        """Return scheduled items (members + score) as human-friendly dicts."""
        items = self._client.zrange(self.SCHEDULED_KEY, 0, -1, withscores=True)
        out: List[Dict[str, Any]] = []
        for member, score in items:
            try:
                j = json.loads(member)
            except Exception:
                continue
            out.append({"id": j.get("id"), "due_at": score, "status": j.get("status")})
        return out

    def _move_due_scheduled_to_queue(self) -> int:
        """Move scheduled jobs whose score <= now into the main queue. Returns count moved."""
        now = self._now_seconds()
        # zrangebyscore with max=now to get due items
        members = self._client.zrangebyscore(self.SCHEDULED_KEY, 0, now)
        if not members:
            return 0
        moved = 0
        pipe = self._client.pipeline()
        for m in members:
            # remove from zset and push to list
            pipe.zrem(self.SCHEDULED_KEY, m)
            pipe.rpush(self.KEY, m)
            moved += 1
        pipe.execute()
        try:
            metrics.INDEX_RETRY_SCHEDULED_MOVED.inc(moved)
            metrics.INDEX_RETRY_SCHEDULED_SIZE.set(self._client.zcard(self.SCHEDULED_KEY))
        except Exception:
            pass
        return moved

    async def process_all(self) -> Dict[str, int]:
        processed = 0
        succeeded = 0
        failed = 0

        # Pop items until queue is empty
        # First, move any due scheduled items into the queue
        try:
            self._move_due_scheduled_to_queue()
        except Exception:
            # best-effort; don't fail the processing loop if scheduling check fails
            pass
        while True:
            raw = self._client.lpop(self.KEY)
            if raw is None:
                break
            try:
                j = json.loads(raw)
                payload = j.get("payload", {})
                texts = payload.get("texts", [])
                metadatas = payload.get("metadatas", [])
                ok = add_texts(texts, metadatas=metadatas)
                processed += 1
                if ok:
                    succeeded += 1
                else:
                    failed += 1
                    # push to a failed list for inspection
                    self._client.rpush(self.KEY + ":failed", raw)
            except Exception:
                failed += 1
        return {"processed": processed, "succeeded": succeeded, "failed": failed}
