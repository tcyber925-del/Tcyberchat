import pytest


@pytest.mark.integration
def test_sse_stream_inproc_mocked(dev_mock_ai):
    """Run the FastAPI app in-process with DEV_MOCK_AI=1 using TestClient and assert streamed chunks."""
    # Import the ASGI app after fixture `dev_mock_ai` sets DEV_MOCK_AI
    from starlette.testclient import TestClient

    from main import app

    with TestClient(app) as client:
        with client.stream("POST", "/chat/stream", json={"message": "test"}) as resp:
            assert resp.status_code == 200
            pieces = []
            for line in resp.iter_lines():
                if not line:
                    continue
                # resp.iter_lines() may yield bytes in TestClient
                if isinstance(line, bytes):
                    s = line.decode("utf-8").strip()
                else:
                    s = str(line).strip()
                if s.startswith("data:"):
                    val = s[len("data:") :].strip()
                    pieces.append(val)

            joined = "".join([p for p in pieces if p and not p.startswith("{")])
            assert "Hello world" in joined or any("Hello world" in p for p in pieces)
