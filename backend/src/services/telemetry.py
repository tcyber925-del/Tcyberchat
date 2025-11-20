"""
Lightweight telemetry/tracing helpers.
Writes JSON lines to logs/telemetry.log and returns a trace_id per request.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

# Ensure logs dir exists
os.makedirs("logs", exist_ok=True)
_TELEMETRY_PATH = os.path.join("logs", "telemetry.log")


def new_trace_id() -> str:
    return uuid.uuid4().hex


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def log_event(kind: str, trace_id: str, data: Optional[Dict[str, Any]] = None) -> None:
    rec = {
        "ts": now_iso(),
        "trace_id": trace_id,
        "kind": kind,
        **(data or {}),
    }
    try:
        with open(_TELEMETRY_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        # Best-effort logging
        pass


def time_block() -> Any:
    start = time.time()
    def done() -> float:
        return time.time() - start
    return done
