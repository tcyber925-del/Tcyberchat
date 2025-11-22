"""Top-level compatibility wrapper for test shims.

This wrapper re-exports the shim implementation that now lives under
`backend/tests/_shims/` so `import prometheus_client` continues to
work in test runs.
"""

from backend.tests._shims import prometheus_client as _shim

CollectorRegistry = getattr(_shim, "CollectorRegistry")
generate_latest = getattr(_shim, "generate_latest")
Counter = getattr(_shim, "Counter")
Gauge = getattr(_shim, "Gauge")
Histogram = getattr(_shim, "Histogram")
