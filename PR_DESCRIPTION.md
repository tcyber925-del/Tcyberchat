Title: Move test shims into `backend/tests/_shims`

Description:
- Move test-only shims into `backend/tests/_shims/` and keep tiny top-level wrappers
  (`fakeredis.py` and `prometheus_client.py`) so existing `import fakeredis` and
  `import prometheus_client` continue to work.

Files changed:
- `backend/tests/_shims/fakeredis.py` (new)
- `backend/tests/_shims/prometheus_client.py` (new)
- `fakeredis.py` (wrapper)
- `prometheus_client.py` (wrapper)
- `backend/README.md` (documentation note)

Testing:
- Ran full backend test suite locally: `198 passed, 9 skipped`.
- Focused admin/index-retry tests passed.

Notes:
- This groups test-only utilities under `backend/tests/_shims/` and keeps top-level
  compatibility wrappers to avoid changing test imports.
- Follow-up: we can remove the wrappers and update imports if we prefer explicit
  `tests._shims` imports, but leaving wrappers minimizes churn.
