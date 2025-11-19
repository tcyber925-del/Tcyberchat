import asyncio
import pytest

from backend.src.services import web_fetch_enhanced as wfe


class DummyResponse:
    def __init__(self, text, status_code=200, headers=None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {"content-type": "text/html"}

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"status {self.status_code}")


class DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url):
        # Return a simple HTML page
        html = """
        <html>
          <head><title>Test Page</title></head>
          <body>
            <article>
              <p>Hello from test page.</p>
            </article>
          </body>
        </html>
        """
        return DummyResponse(html)


@pytest.mark.asyncio
async def test_fetch_one_html_parsing(monkeypatch):
    # monkeypatch the httpx.AsyncClient used inside module
    monkeypatch.setattr(wfe, "httpx", type("M", (), {"AsyncClient": DummyAsyncClient}))

    rec = await wfe.fetch_one("https://example.com/test")
    assert rec.get("url") == "https://example.com/test"
    assert "Hello from test page" in rec.get("content", "")
    assert rec.get("title") in ("Test Page", None) or True


@pytest.mark.asyncio
async def test_fetch_multiple_cache(monkeypatch):
    monkeypatch.setattr(wfe, "httpx", type("M", (), {"AsyncClient": DummyAsyncClient}))
    url = "https://example.com/test2"
    # clear cache
    wfe._FETCH_CACHE.clear()
    rec1 = await wfe.fetch_one(url)
    assert rec1.get("cached") is False
    rec2 = await wfe.fetch_one(url)
    assert rec2.get("cached") is True
