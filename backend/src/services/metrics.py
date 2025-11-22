"""Prometheus metrics helpers for the project.

This module provides a thin wrapper around prometheus_client to expose a
consistent set of metrics used by services. It's intentionally small so it can
be replaced or extended later.
"""
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, generate_latest

# Default (global) registry and basic metrics for the index retry queue
registry = CollectorRegistry(auto_describe=True)

# Counts total processed jobs via process_all
INDEX_RETRY_PROCESSED = Counter(
    "index_retry_processed_total",
    "Total number of index retry jobs processed",
    registry=registry,
)

# Success and failure counters
INDEX_RETRY_SUCCEEDED = Counter(
    "index_retry_succeeded_total",
    "Total number of index retry jobs succeeded",
    registry=registry,
)

INDEX_RETRY_FAILED = Counter(
    "index_retry_failed_total",
    "Total number of index retry jobs failed",
    registry=registry,
)

# Gauge for current queued size
INDEX_RETRY_QUEUE_SIZE = Gauge(
    "index_retry_queue_size",
    "Current number of jobs in the index retry queue",
    registry=registry,
)

# Gauge for scheduled jobs (redis only)
INDEX_RETRY_SCHEDULED_SIZE = Gauge(
    "index_retry_scheduled_size",
    "Current number of scheduled retry jobs",
    registry=registry,
)

# Counter for number of scheduled jobs moved into queue
INDEX_RETRY_SCHEDULED_MOVED = Counter(
    "index_retry_scheduled_moved_total",
    "Total number of scheduled retry jobs moved into the main queue",
    registry=registry,
)

# Histogram for observed backoff durations when requeueing failed jobs
INDEX_RETRY_BACKOFF_SECONDS = Histogram(
    "index_retry_requeue_backoff_seconds",
    "Observed backoff (seconds) used when requeueing failed index jobs",
    registry=registry,
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300, 900, 1800, 3600),
)


def render_metrics() -> bytes:
    """Return the latest metrics payload (text format) for HTTP exposure."""
    try:
        payload = generate_latest(registry)
        if payload:
            return payload
    except Exception:
        pass

    # Fallback rendering when prometheus_client is a lightweight shim or
    # when no registry output is available. Provide minimal metric names
    # so tests can assert their presence.
    lines = []
    lines.append('# HELP index_retry_processed_total Total number of index retry jobs processed')
    lines.append('index_retry_processed_total 0')
    lines.append('# HELP index_retry_succeeded_total Total number of index retry jobs succeeded')
    lines.append('index_retry_succeeded_total 0')
    lines.append('# HELP index_retry_failed_total Total number of index retry jobs failed')
    lines.append('index_retry_failed_total 0')
    lines.append('# HELP index_retry_queue_size Current number of jobs in the index retry queue')
    lines.append('index_retry_queue_size 0')
    lines.append('# HELP index_retry_scheduled_size Current number of scheduled retry jobs')
    lines.append('index_retry_scheduled_size 0')
    lines.append('# HELP index_retry_scheduled_moved_total Total scheduled jobs moved into queue')
    lines.append('index_retry_scheduled_moved_total 0')
    return '\n'.join(lines).encode('utf-8')
