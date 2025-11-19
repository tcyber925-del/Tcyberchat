"""In-memory retry queue for indexing jobs (fallback from document processing).

Jobs are simple dicts containing `texts` and `metadatas` and optional document_id.
This is an in-process queue intended for dev/staging; for production use Redis/RQ.
"""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from typing import Any, Dict, List

from .vectorstore_manager import add_texts
from . import metrics


class IndexJob:
    def __init__(self, payload: Dict[str, Any]):
        self.id = uuid.uuid4().hex
        self.payload = payload
        self.status = "queued"  # queued|running|done|error
        self.error: str | None = None

    def to_dict(self):
        return {"id": self.id, "status": self.status, "error": self.error}


class IndexJobQueue:
    def __init__(self) -> None:
        self._jobs: List[IndexJob] = []
        self._lock = asyncio.Lock()

    def list(self) -> List[Dict[str, Any]]:
        out = [j.to_dict() for j in self._jobs]
        # update gauge
        try:
            metrics.INDEX_RETRY_QUEUE_SIZE.set(len(out))
        except Exception:
            pass
        return out

    def get_job(self, job_id: str) -> Dict[str, Any] | None:
        for j in self._jobs:
            if j.id == job_id:
                return j.to_dict()
        return None

    async def enqueue(self, payload: Dict[str, Any]) -> IndexJob:
        job = IndexJob(payload)
        async with self._lock:
            self._jobs.append(job)
        try:
            metrics.INDEX_RETRY_QUEUE_SIZE.inc()
        except Exception:
            pass
        return job

    async def process_all(self) -> Dict[str, int]:
        """Process all queued jobs synchronously.

        Returns counts: {processed, succeeded, failed}
        """
        processed = 0
        succeeded = 0
        failed = 0
        async with self._lock:
            jobs = list(self._jobs)
            self._jobs = []

        for job in jobs:
            job.status = "running"
            processed += 1
            try:
                payload = job.payload
                texts = payload.get("texts", [])
                metadatas = payload.get("metadatas", [])
                ok = add_texts(texts, metadatas=metadatas)
                if ok:
                    job.status = "done"
                    succeeded += 1
                else:
                    job.status = "error"
                    job.error = "add_texts returned False"
                    failed += 1
            except Exception as e:
                job.status = "error"
                job.error = str(e)
                failed += 1

        # update metrics
        try:
            metrics.INDEX_RETRY_PROCESSED.inc(processed)
            metrics.INDEX_RETRY_SUCCEEDED.inc(succeeded)
            metrics.INDEX_RETRY_FAILED.inc(failed)
            # queue was cleared for these jobs
            metrics.INDEX_RETRY_QUEUE_SIZE.set(len(self._jobs))
        except Exception:
            pass

        return {"processed": processed, "succeeded": succeeded, "failed": failed}

    async def cancel(self, job_id: str) -> bool:
        """Cancel (remove) a queued job by id. Returns True if removed."""
        async with self._lock:
            for i, j in enumerate(self._jobs):
                if j.id == job_id:
                    j.status = "cancelled"
                    # remove from queue so it won't be processed
                    self._jobs.pop(i)
                    try:
                        metrics.INDEX_RETRY_QUEUE_SIZE.dec()
                    except Exception:
                        pass
                    return True
        return False


_index_queue: IndexJobQueue | None = None


def get_index_job_queue() -> IndexJobQueue:
    """Return a singleton queue instance.

    If env var `INDEX_RETRY_QUEUE_BACKEND=redis` the code will attempt to
    instantiate the Redis-backed adapter. If that fails, it falls back to
    the in-memory `IndexJobQueue`.
    """
    global _index_queue
    backend = os.getenv("INDEX_RETRY_QUEUE_BACKEND", "inmemory").lower()

    # When running under pytest, return a fresh in-memory instance so tests
    # can mutate/reset the queue without cross-test pollution. Tests that need
    # the Redis adapter should instantiate `RedisIndexJobQueue` directly.
    if os.getenv("PYTEST_CURRENT_TEST"):
        # Return a cached in-memory instance per-process so tests within the
        # same process (and admin handlers) see the same queue object.
        if not isinstance(_index_queue, IndexJobQueue):
            _index_queue = IndexJobQueue()
        return _index_queue

    # Normal runtime path: keep a cached singleton matching configured backend.
    if backend == "redis":
        try:
            from .index_retry_queue_redis import RedisIndexJobQueue

            if not isinstance(_index_queue, RedisIndexJobQueue):
                _index_queue = RedisIndexJobQueue()
            return _index_queue
        except Exception:
            _index_queue = IndexJobQueue()
            return _index_queue

    if not isinstance(_index_queue, IndexJobQueue):
        _index_queue = IndexJobQueue()
    return _index_queue
