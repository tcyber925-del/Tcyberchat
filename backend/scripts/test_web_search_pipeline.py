"""
Test web search pipeline end-to-end.
- Service-level search + enrichment (no server required)
- Optional API tests if backend is running (health + test)
- Optional chat stream smoke test (requires server)
"""

import asyncio
import json
import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from dotenv import load_dotenv

load_dotenv()

# Ensure a user-agent to reduce warnings
os.environ.setdefault("USER_AGENT", os.getenv("USER_AGENT", "LocalChatbot/1.0"))


async def service_level_tests():
    from src.services.web_search_service import get_web_search_service

    svc = get_web_search_service()
    print(
        f"Impl={getattr(svc, 'impl', 'custom')} Primary={svc.provider_name} PrimaryAvail={svc.primary_provider is not None}"
    )

    # Search
    results = await svc.search(
        "latest AI news", max_results=3, use_cache=False, force_fresh=True
    )
    print(f"Results={len(results)}")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {(r.title or '')[:80]} - {r.url}")

    # Enrich
    os.environ.setdefault("WEB_FETCH_ENABLED", os.getenv("WEB_FETCH_ENABLED", "true"))
    enriched = await svc.enrich_results(results)
    enriched_count = sum(1 for r in enriched if r.content)
    print(f"Enriched={enriched_count}")
    for i, r in enumerate(enriched, 1):
        preview = (r.content or "")[:80].replace("\n", " ")
        print(
            f"  [{i}] content={bool(r.content)} tokens={r.tokens_estimate} url={r.url} preview='{preview}'"
        )


def api_health_tests(base="http://localhost:8000"):
    import requests

    try:
        r = requests.get(f"{base}/api/tools/web-search/health", timeout=5)
        print("/health:", r.status_code)
        print(json.dumps(r.json(), indent=2)[:800])
    except Exception as e:
        print("/health unreachable:", e)

    try:
        r = requests.post(
            f"{base}/api/tools/web-search/test",
            json={"q": "latest AI news", "maxResults": 3},
            timeout=10,
        )
        print("/test:", r.status_code)
        print(json.dumps(r.json(), indent=2)[:800])
    except Exception as e:
        print("/test unreachable:", e)


def chat_stream_smoke(base="http://localhost:8000"):
    """Optional: smoke test for /chat/stream (requires server running)."""
    import requests

    url = f"{base}/chat/stream"
    payload = {
        "message": "What is the latest AI news today?",
        "enableWebSearch": True,
        "model": os.getenv("GEMINI_MODEL") or None,
    }

    try:
        with requests.post(url, json=payload, stream=True, timeout=30) as resp:
            print("/chat/stream:", resp.status_code)
            last_json = None
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data:"):
                    data = line[5:].strip()
                    try:
                        last_json = json.loads(data)
                    except Exception:
                        pass
            if last_json:
                print("Final SSE keys:", list(last_json.keys()))
                print(
                    "webSearchUsed:",
                    last_json.get("webSearchUsed"),
                    "count:",
                    last_json.get("webSearchResultsCount"),
                )
                print(
                    "webProvider:",
                    last_json.get("webProvider"),
                    "webImpl:",
                    last_json.get("webImpl"),
                )
                print("content preview:", (last_json.get("content") or "")[:200])
            else:
                print("No final SSE message parsed.")
    except Exception as e:
        print("/chat/stream unreachable:", e)


if __name__ == "__main__":
    print("== Service-level tests ==")
    asyncio.get_event_loop().run_until_complete(service_level_tests())

    print("\n== API health/tests (if backend is running) ==")
    api_health_tests()

    print("\n== Chat stream smoke (if backend is running) ==")
    chat_stream_smoke()
