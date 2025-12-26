"""Lightweight fakeredis shim for unit tests.

This module prefers the real `fakeredis` package when available and
falls back to a minimal in-repo shim implementing the subset of Redis
commands used by unit tests (lists, hashes, sorted-sets and a simple
pipeline).
"""Top-level compatibility wrapper for test shims.

This module re-exports the test-only shim that now lives under
`backend/tests/_shims/`. Keeping a tiny top-level wrapper preserves
`import fakeredis` semantics for tests and code that expect that
module name.
"""

from typing import Any, Dict, List, Tuple, Optional


try:
    import importlib, sys
    _real_faker = importlib.import_module("fakeredis")
    # If importing 'fakeredis' gave us this same module (self-import), treat as not available
    if _real_faker is sys.modules.get(__name__):
        raise ImportError("embedded shim: use fallback")

    FakeRedis = getattr(_real_faker, "FakeRedis", getattr(_real_faker, "FakeStrictRedis", None))

    class Redis:
        @staticmethod
        def from_url(url: str, decode_responses: bool = True):
            return FakeRedis()

except Exception:
    class FakePipeline:
        def __init__(self, store: "FakeRedisShim"):
            self.store = store
            self.ops: List[Tuple[str, Tuple[Any, ...], Dict[str, Any]]] = []

        def zrem(self, *args, **kwargs):
            self.ops.append(("zrem", args, kwargs))

        def rpush(self, *args, **kwargs):
            self.ops.append(("rpush", args, kwargs))

        def execute(self):
            for name, args, kwargs in self.ops:
                getattr(self.store, name)(*args, **kwargs)
            self.ops.clear()


    class FakeRedisShim:
        def __init__(self):
            self._lists: Dict[str, List[str]] = {}
            self._hashes: Dict[str, Dict[str, str]] = {}
            self._zsets: Dict[str, Dict[str, float]] = {}

        # Lists
        def rpush(self, key: str, value: Any):
            self._lists.setdefault(key, []).append(self._ensure_str(value))

        def lpush(self, key: str, value: Any):
            self._lists.setdefault(key, []).insert(0, self._ensure_str(value))

        def lrange(self, key: str, start: int, end: int) -> List[str]:
            lst = self._lists.get(key, [])
            if end == -1:
                end = len(lst) - 1
            return lst[start : end + 1]

        def lpop(self, key: str):
            lst = self._lists.get(key, [])
            if not lst:
                return None
            return lst.pop(0)

        def rpop(self, key: str):
            lst = self._lists.get(key, [])
            if not lst:
                return None
            return lst.pop()

        def rpoplpush(self, src: str, dst: str):
            val = self.rpop(src)
            if val is None:
                return None
            self.lpush(dst, val)
            return val

        def lrem(self, key: str, count: int, value: Any) -> int:
            lst = self._lists.get(key, [])
            vs = self._ensure_str(value)
            removed = 0
            if count == 0:
                newlst = [v for v in lst if v != vs]
                removed = len(lst) - len(newlst)
                self._lists[key] = newlst
                return removed
            if count > 0:
                newlst = []
                for v in lst:
                    if v == vs and removed < count:
                        removed += 1
                        continue
                    newlst.append(v)
                self._lists[key] = newlst
                return removed
            # negative count
            if count < 0:
                rev = list(reversed(lst))
                newrev = []
                for v in rev:
                    if v == vs and removed < abs(count):
                        removed += 1
                        continue
                    newrev.append(v)
                newlst = list(reversed(newrev))
                self._lists[key] = newlst
                return removed

        # Hashes
        def hset(self, key: str, field: str, value: Any):
            self._hashes.setdefault(key, {})[self._ensure_str(field)] = self._ensure_str(value)

        def hget(self, key: str, field: str):
            return self._hashes.get(key, {}).get(self._ensure_str(field))

        def hgetall(self, key: str) -> Dict[str, str]:
            return dict(self._hashes.get(key, {}))

        def hdel(self, key: str, field: str):
            h = self._hashes.get(key, {})
            if self._ensure_str(field) in h:
                del h[self._ensure_str(field)]

        # Sorted sets
        def zadd(self, key: str, mapping: Dict[str, float]):
            z = self._zsets.setdefault(key, {})
            for member, score in mapping.items():
                z[self._ensure_str(member)] = float(score)

        def zrange(self, key: str, start: int, end: int, withscores: bool = False):
            z = self._zsets.get(key, {})
            items = sorted(z.items(), key=lambda kv: (kv[1], kv[0]))
            members = [m for m, s in items]
            if end == -1:
                end = len(members) - 1
            slice_members = members[start : end + 1]
            if withscores:
                return [(m, z[m]) for m in slice_members]
            return slice_members

        def zrangebyscore(self, key: str, min_score: float, max_score: float):
            z = self._zsets.get(key, {})
            return [m for m, s in sorted(z.items(), key=lambda kv: (kv[1], kv[0])) if s >= min_score and s <= max_score]

        def zcard(self, key: str) -> int:
            return len(self._zsets.get(key, {}))

        def zrem(self, key: str, member: str):
            z = self._zsets.get(key, {})
            if member in z:
                del z[member]

        def pipeline(self):
            return FakePipeline(self)

        @staticmethod
        def _ensure_str(v: Any) -> str:
            if isinstance(v, (bytes, bytearray)):
                try:
                    return v.decode()
                except Exception:
                    return str(v)
            return v if isinstance(v, str) else str(v)


    FakeRedis = FakeRedisShim


    class Redis:
        @staticmethod
        def from_url(url: str, decode_responses: bool = True):
            return FakeRedis()
from backend.tests._shims import fakeredis as _shim

# Re-export the main symbols used by tests
FakeRedis = getattr(_shim, "FakeRedis")
Redis = getattr(_shim, "Redis")
