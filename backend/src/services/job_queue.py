"""
In-memory background job registry for deep research jobs.
Optionally can be extended to Redis/RQ later.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, Optional

from ..agents.deep_research_agent import run_deep_research


class Job:
    def __init__(self, query: str, model: Optional[str], max_iterations: int) -> None:
        self.id = uuid.uuid4().hex
        self.query = query
        self.model = model
        self.max_iterations = max_iterations
        self.status = "queued"  # queued|running|done|error|cancelled
        self.result: Dict[str, Any] | None = None
        self.error: str | None = None
        self._task: asyncio.Task | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "error": self.error,
            "has_result": self.result is not None,
        }


class JobQueue:
    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def list(self) -> Dict[str, Any]:
        return {jid: job.to_dict() for jid, job in self._jobs.items()}

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        if job._task and not job._task.done():
            job._task.cancel()
            job.status = "cancelled"
            return True
        return False

    def enqueue(self, query: str, model: Optional[str], max_iterations: int) -> Job:
        job = Job(query, model, max_iterations)
        self._jobs[job.id] = job

        async def runner():
            job.status = "running"
            try:
                job.result = await run_deep_research(query=query, model_name=model, max_iterations=max_iterations)
                job.status = "done"
            except asyncio.CancelledError:
                job.status = "cancelled"
            except Exception as e:  # pragma: no cover
                job.error = str(e)
                job.status = "error"

        job._task = asyncio.create_task(runner())
        return job


_job_queue: JobQueue | None = None


def get_job_queue() -> JobQueue:
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueue()
    return _job_queue
