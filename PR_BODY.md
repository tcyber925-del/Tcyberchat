Move test shims into backend/tests/_shims

This PR moves test-only shims into `backend/tests/_shims` and keeps tiny top-level
wrappers so `import fakeredis` and `import prometheus_client` still work in tests.

Local test run: 198 passed, 9 skipped.
