"""Minimal middleware utilities for agent tool error handling.

Provides a `wrap_tool_call` decorator (LangChain-like) that converts exceptions
into structured error dicts so agents can receive ToolMessage-like responses.
"""
from __future__ import annotations

from typing import Any, Callable


def wrap_tool_call(func: Callable) -> Callable:
    """Decorator that wraps tool execution and returns an error dict on exceptions."""

    def _wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return {"tool_error": True, "tool_name": getattr(func, "__name__", "tool"), "error": str(e)}

    _wrapped.__name__ = getattr(func, "__name__", "wrapped_tool")
    _wrapped.__doc__ = getattr(func, "__doc__", "")
    return _wrapped
