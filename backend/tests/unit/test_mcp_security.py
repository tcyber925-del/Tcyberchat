import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
try:
    from src.api.integrations_mcp import router, _validate_stdio_command
except ImportError:
    from backend.src.api.integrations_mcp import router, _validate_stdio_command

def test_validate_stdio_command_no_allowlist():
    """If allowlist is not set, all commands should be allowed."""
    with patch.dict(os.environ, {}, clear=True):
        assert _validate_stdio_command("ls") is True
        assert _validate_stdio_command("cat") is True

def test_validate_stdio_command_allowlist():
    """If allowlist is set, only permitted commands are allowed."""
    with patch.dict(os.environ, {"MCP_STDIO_ALLOWLIST": "python,node,uv"}, clear=True):
        assert _validate_stdio_command("python") is True
        assert _validate_stdio_command("node") is True
        assert _validate_stdio_command("uv") is True
        assert _validate_stdio_command("bash") is False
        assert _validate_stdio_command("rm") is False

def test_validate_stdio_command_wildcard():
    """If allowlist is *, all commands allowed."""
    with patch.dict(os.environ, {"MCP_STDIO_ALLOWLIST": "*"}, clear=True):
        assert _validate_stdio_command("rm") is True

# Note: Testing the router directly requires a full app instance or careful patching of dependencies
# like get_multi_mcp_client. For unit testing, testing the validation logic is sufficient.
