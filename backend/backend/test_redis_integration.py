import asyncio
import os
import sys

os.environ.setdefault("INDEX_RETRY_QUEUE_BACKEND", os.getenv("INDEX_RETRY_QUEUE_BACKEND", "redis"))

from src.services.index_retry_queue import get_index_job_queue


async def main():
    print("Using REDIS_URL:", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"))
    q = get_index_job_queue()

    print("Enqueuing test job...")
    job = await q.enqueue({"texts": ["integration test"], "metadatas": [{"doc_id": "int-test"}]})
    jid = job.get("id") if isinstance(job, dict) else getattr(job, "id", None)
    print("Enqueued job id:", jid)

    print("Processing queue (this will pop jobs)...")
    res = await q.process_all()
    print("Process result:", res)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("Error during integration test:", e)
        sys.exit(2)