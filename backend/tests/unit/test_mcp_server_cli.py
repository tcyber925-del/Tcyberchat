import os
import sys
import builtins
import types
import pytest

# Ensure backend package is importable when running from repo root
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from scripts import mcp_server as cli  # noqa: E402


def test_parse_args_defaults():
    # Simulate no args
    argv = ["prog"]
    parser = cli.argparse.ArgumentParser()


@pytest.mark.parametrize("mode", ["stdio", "ws"])
def test_main_invokes_runner(monkeypatch, mode):
    calls = {"stdio": 0, "ws": 0}

    async def fake_stdio():
        calls["stdio"] += 1

    async def fake_ws(**kwargs):
        calls["ws"] += 1

    monkeypatch.setattr(cli, "run_stdio", fake_stdio)
    monkeypatch.setattr(cli, "run_ws", fake_ws)

    # Patch parse_args to return our desired mode without reading real argv
    class FakeNS:
        def __init__(self, mode):
            self.mode = mode
            self.host = "0.0.0.0"
            self.port = 8765
            self.token = None

    monkeypatch.setattr(cli, "parse_args", lambda: FakeNS(mode))

    # Run main (should call the appropriate async function)
    cli.main()

    if mode == "stdio":
        assert calls["stdio"] == 1
        assert calls["ws"] == 0
    else:
        assert calls["ws"] == 1
        assert calls["stdio"] == 0
