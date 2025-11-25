import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Ensure backend package is importable when running from repo root
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from src.services.mcp.clients.sse_client import SseMcpConnection

@pytest.mark.asyncio
async def test_sse_client_start_lifecycle():
    """Test that SseMcpConnection uses streamablehttp_client and manages the session correctly."""
    
    # Mock the mcp dependencies
    # We patch the actual modules because the imports are inside the method
    with patch("mcp.client.streamable_http.streamablehttp_client") as mock_streamable_client, \
         patch("mcp.client.session.ClientSession") as mock_client_session:
        
        # Setup mock context manager for streamablehttp_client
        mock_context = AsyncMock()
        mock_read = MagicMock()
        mock_write = MagicMock()
        mock_worker = MagicMock()
        # streamablehttp_client yields (read, write, worker)
        mock_context.__aenter__.return_value = (mock_read, mock_write, mock_worker)
        mock_streamable_client.return_value = mock_context

        # Setup mock session
        mock_session = AsyncMock()
        mock_client_session.return_value = mock_session

        # Initialize connection
        url = "http://test.local/sse"
        headers = {"Authorization": "Bearer token"}
        conn = SseMcpConnection(url, headers)

        # Start connection
        await conn.start()

        # Verify streamablehttp_client was called with correct args
        mock_streamable_client.assert_called_once_with(url, headers=headers)
        
        # Verify context manager was entered
        mock_context.__aenter__.assert_called_once()

        # Verify ClientSession was created with read/write streams
        mock_client_session.assert_called_once_with(mock_read, mock_write)

        # Verify session was initialized
        mock_session.initialize.assert_called_once()

        # Verify internal state
        assert conn._session == mock_session
        assert conn._client == mock_session

        # Stop connection
        await conn.stop()

        # Verify context manager was exited
        mock_context.__aexit__.assert_called_once()
        assert conn._session is None
        assert conn._client is None
        assert conn._context is None

@pytest.mark.asyncio
async def test_sse_client_call_tool():
    """Test calling a tool via SseMcpConnection."""
    
    with patch("mcp.client.streamable_http.streamablehttp_client") as mock_streamable_client, \
         patch("mcp.client.session.ClientSession") as mock_client_session:
        
        # Setup mocks
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_streamable_client.return_value = mock_context
        
        mock_session = AsyncMock()
        mock_client_session.return_value = mock_session
        
        # Mock tool result
        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Tool output"
        mock_result.content = [mock_content]
        mock_result.isError = False
        mock_session.call_tool.return_value = mock_result

        conn = SseMcpConnection("http://test.local/sse")
        await conn.start()

        # Call tool
        res = await conn.call_tool("test_tool", {"param": "value"})

        # Verify result
        assert res["content"] == "Tool output"
        assert res["isError"] is False
        
        mock_session.call_tool.assert_called_once_with("test_tool", {"param": "value"})

@pytest.mark.asyncio
async def test_sse_client_list_tools():
    """Test listing tools via SseMcpConnection."""
    
    with patch("mcp.client.streamable_http.streamablehttp_client") as mock_streamable_client, \
         patch("mcp.client.session.ClientSession") as mock_client_session:
        
        # Setup mocks
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_streamable_client.return_value = mock_context
        
        mock_session = AsyncMock()
        mock_client_session.return_value = mock_session
        
        # Mock list tools result
        mock_tool = MagicMock()
        mock_tool.name = "my_tool"
        mock_tool.description = "My description"
        mock_tool.inputSchema = {"type": "object"}
        
        mock_result = MagicMock()
        mock_result.tools = [mock_tool]
        mock_session.list_tools.return_value = mock_result

        conn = SseMcpConnection("http://test.local/sse")
        await conn.start()

        # List tools
        tools = await conn.list_tools()

        # Verify result
        assert len(tools) == 1
        assert tools[0]["name"] == "my_tool"
        assert tools[0]["description"] == "My description"
        
        mock_session.list_tools.assert_called_once()
