"""Top-level compatibility wrapper for test shims.

This module re-exports the test-only shim that now lives under
`backend/tests/_shims/`. Keeping a tiny top-level wrapper preserves
`import fakeredis` semantics for tests and code that expect that
module name.
"""

from backend.tests._shims import fakeredis as _shim

# Re-export the main symbols used by tests
FakeRedis = getattr(_shim, "FakeRedis")
Redis = getattr(_shim, "Redis")
