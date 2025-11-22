import pytest


@pytest.mark.asyncio
async def test_process_queue_function(monkeypatch):
    # Import the admin module and the index queue service to patch
    import backend.src.api.admin_vectorstore as admin_mod
    import backend.src.services.index_retry_queue as irq

    class FakeQueue:
        async def process_all(self):
            return {"processed": 2, "succeeded": 1, "failed": 1}

    # Patch the factory to return our fake queue
    monkeypatch.setattr(irq, "get_index_job_queue", lambda: FakeQueue())

    # Call the function directly to avoid app startup side-effects
    res = await admin_mod.process_index_queue()
    assert res == {"processed": 2, "succeeded": 1, "failed": 1}
