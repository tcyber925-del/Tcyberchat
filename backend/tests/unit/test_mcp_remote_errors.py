import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
try:
    from src.services.mcp.clients.sse_client import SseMcpConnection
    from src.services.mcp.clients.ws_client import WsMcpConnection
except ImportError:
    from backend.src.services.mcp.clients.sse_client import SseMcpConnection
    from backend.src.services.mcp.clients.ws_client import WsMcpConnection

@pytest.mark.asyncio
async def test_sse_timeout():
    """Test that SseMcpConnection raises RuntimeError on timeout."""
    with patch("mcp.client.streamable_http.streamablehttp_client") as mock_client:
        # Mock context manager that hangs
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError("mock timeout"))
        mock_client.return_value = mock_ctx

        conn = SseMcpConnection("http://localhost:8000/sse", timeout=0.1)
        with pytest.raises(RuntimeError) as exc:
            await conn.start()
        assert "Timeout connecting" in str(exc.value)

@pytest.mark.asyncio
async def test_ws_timeout():
    """Test that WsMcpConnection raises RuntimeError on timeout."""
    with patch("mcp.client.websocket.websocket_client") as mock_ws:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError("mock timeout"))
        mock_ws.return_value = mock_ctx

        conn = WsMcpConnection("ws://localhost:8000/ws", connect_timeout=0.1)
        with pytest.raises(RuntimeError) as exc:
            await conn.start()
        assert "Timeout connecting" in str(exc.value)

@pytest.mark.asyncio
async def test_sse_connection_error():
    """Test that SseMcpConnection raises RuntimeError on generic error."""
    with patch("mcp.client.streamable_http.streamablehttp_client") as mock_client:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client.return_value = mock_ctx

        conn = SseMcpConnection("http://localhost:8000/sse")
        with pytest.raises(RuntimeError) as exc:
            await conn.start()
        assert "Failed to start SSE MCP connection" in str(exc.value)
        assert "Connection refused" in str(exc.value)
