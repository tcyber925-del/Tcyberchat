import anyio
import pytest
import sse_starlette.sse as sse_module

# Ensure sse-starlette global AppStatus event is bound to the current AnyIO backend
# to avoid event-loop mismatch when tests run under pytest/anyio.
try:
    sse_module.AppStatus.should_exit_event = anyio.Event()
except Exception:
    # Best-effort: if the internal symbol changes or package not installed, tests will fall back
    pass


@pytest.mark.integration
def test_sse_stream_with_mocked_ai(dev_mock_ai):
    """In-process test: ensure the mocked AI returns the expected stream via TestClient.

    This replaces the previous subprocess-based test which was flaky.
    """
    from starlette.testclient import TestClient

    from main import app

    with TestClient(app) as client:
        with client.stream("POST", "/chat/stream", json={"message": "test"}) as resp:
            assert resp.status_code == 200
            pieces = []
            for line in resp.iter_lines():
                if not line:
                    continue
                if isinstance(line, bytes):
                    s = line.decode("utf-8").strip()
                else:
                    s = str(line).strip()
                if s.startswith("data:"):
                    val = s[len("data:") :].strip()
                    pieces.append(val)

            joined = "".join([p for p in pieces if p and not p.startswith("{")])
            assert "Hello world" in joined or any("Hello world" in p for p in pieces)
