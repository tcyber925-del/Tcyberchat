"""Local test shim for `serpapi` used by unit tests.

This small shim provides a `Client` class with a `search` method so tests
that patch `serpapi.Client` can operate even if the real `serpapi` package
is not installed or lacks the expected symbol in the test environment.
"""
from typing import Any, Dict


class Client:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Return a minimal, empty-shaped response compatible with callers
        return {"organic_results": []}
