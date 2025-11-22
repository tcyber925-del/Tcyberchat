"""Small agent utilities used by deep research and agents.

Includes run id generation and a resilient JSON extractor for LLM outputs.
"""
from __future__ import annotations

import json
import re
from uuid import uuid4
from typing import Any, Dict, Optional


def generate_run_id() -> str:
    return uuid4().hex


def safe_extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Try to extract the first JSON object from text.

    The function attempts direct json.loads first, then searches for the
    first brace-delimited object using a simple regex. Returns None if parsing
    fails.
    """
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        # Try to find a {...} block
        m = re.search(r"\{(?:[^{}]|(?R))*\}", text)
        if m:
            js = m.group(0)
            try:
                return json.loads(js)
            except Exception:
                return None
        # Fallback: find first balanced braces substring naively
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return None
    return None
