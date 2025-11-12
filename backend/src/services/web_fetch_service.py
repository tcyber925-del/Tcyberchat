"""
Web Fetch Service for extracting readable content from URLs
Supports HTML and PDF extraction with fallback strategies
"""

import asyncio
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Result of fetching and extracting content from a URL"""

    url: str
    canonical_url: str | None
    content: str | None
    content_type: str | None
    title: str | None
    published_at: datetime | None
    extracted_at: datetime
    tokens_estimate: int
    error: str | None = None


class WebFetchService:
    """Service for fetching and extracting content from web URLs"""

    def __init__(
        self,
        enabled: bool = False,
        concurrency: int = 5,
        timeout_ms: int = 8000,
        cache_ttl: int = 3600,
        max_bytes: int = 2_000_000,
        pdf_enabled: bool = True,
        user_agent: str = "LocalChatbot/1.0",
        blocklist_domains: list[str] | None = None,
        allowlist_domains: list[str] | None = None,
        max_fetch: int = 3,
    ):
        """
        Initialize web fetch service

        Args:
            enabled: Enable web fetch (default False for backward compatibility)
            concurrency: Max concurrent fetches
            timeout_ms: Request timeout in milliseconds
            cache_ttl: Cache time-to-live in seconds
            max_bytes: Maximum response size in bytes
            pdf_enabled: Enable PDF extraction
            user_agent: User agent string
            blocklist_domains: Domains to skip (optional)
            allowlist_domains: Only fetch from these domains if set (optional)
            max_fetch: Maximum number of URLs to fetch per enrichment call
        """
        self.enabled = enabled
        self.concurrency = concurrency
        self.timeout = timeout_ms / 1000.0  # Convert to seconds
        self.cache_ttl = cache_ttl
        self.max_bytes = max_bytes
        self.pdf_enabled = pdf_enabled
        self.user_agent = user_agent
        self.blocklist_domains = set(blocklist_domains or [])
        self.allowlist_domains = (
            set(allowlist_domains or []) if allowlist_domains else None
        )
        self.max_fetch = max_fetch

        # Cache: canonical_url -> (FetchResult, timestamp)
        self._cache: dict[str, tuple[FetchResult, datetime]] = {}

        # Rate limiting: domain -> list of request timestamps
        self._rate_limit_tracker: dict[str, list[float]] = defaultdict(list)
        self._domain_rate_limit = 5  # Max requests per minute per domain

        # Semaphore for concurrency control
        self._semaphore = asyncio.Semaphore(concurrency)

        # Stats
        self._stats = {
            "fetched_count": 0,
            "cache_hits": 0,
            "failures": 0,
            "total_fetch_time": 0.0,
            "failures_by_reason": defaultdict(int),
        }

        # Check for optional dependencies
        self._httpx_available = self._check_httpx()
        self._extraction_libs = self._check_extraction_libs()

        if enabled and not self._httpx_available:
            logger.warning(
                "WEB_FETCH_ENABLED=true but httpx not installed. Install with: pip install httpx"
            )
            self.enabled = False

        logger.info(
            f"WebFetchService initialized: enabled={self.enabled}, "
            f"concurrency={concurrency}, timeout={self.timeout}s, "
            f"httpx_available={self._httpx_available}, "
            f"extraction_libs={list(self._extraction_libs.keys())}"
        )

    def _check_httpx(self) -> bool:
        """Check if httpx is available"""
        try:
            import httpx

            return True
        except ImportError:
            return False

    def _check_extraction_libs(self) -> dict[str, bool]:
        """Check which extraction libraries are available"""
        libs = {}

        # HTML extraction
        try:
            import trafilatura

            libs["trafilatura"] = True
        except ImportError:
            libs["trafilatura"] = False

        try:
            from readability import Document

            libs["readability"] = True
        except ImportError:
            libs["readability"] = False

        try:
            from bs4 import BeautifulSoup

            libs["beautifulsoup"] = True
        except ImportError:
            libs["beautifulsoup"] = False

        # PDF extraction
        try:
            import pymupdf

            libs["pymupdf"] = True
        except ImportError:
            libs["pymupdf"] = False

        try:
            import pypdf

            libs["pypdf"] = True
        except ImportError:
            libs["pypdf"] = False

        return libs

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and tracking params"""
        parsed = urlparse(url)
        # Remove fragment
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            # Remove common tracking params
            query_parts = []
            for part in parsed.query.split("&"):
                # Check if part starts with any tracking param prefix
                is_tracking = False
                for prefix in ["utm_", "fbclid", "gclid", "ref"]:
                    if part.startswith(prefix):
                        is_tracking = True
                        break
                if not is_tracking:
                    query_parts.append(part)
            if query_parts:
                normalized += "?" + "&".join(query_parts)
        return normalized

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        return urlparse(url).netloc

    def _is_allowed_domain(self, url: str) -> bool:
        """Check if domain is allowed based on allow/block lists"""
        domain = self._get_domain(url)

        # Check allowlist first (if set, only these domains are allowed)
        if self.allowlist_domains:
            return domain in self.allowlist_domains

        # Check blocklist
        if domain in self.blocklist_domains:
            return False

        return True

    def _check_domain_rate_limit(self, url: str) -> bool:
        """Check if request to domain is within rate limit"""
        domain = self._get_domain(url)
        now = time.time()
        minute_ago = now - 60

        # Clean old entries
        self._rate_limit_tracker[domain] = [
            t for t in self._rate_limit_tracker[domain] if t > minute_ago
        ]

        # Check limit
        if len(self._rate_limit_tracker[domain]) >= self._domain_rate_limit:
            return False

        # Record this request
        self._rate_limit_tracker[domain].append(now)
        return True

    def _get_cached_result(self, canonical_url: str) -> FetchResult | None:
        """Get cached result if available and not expired"""
        if canonical_url not in self._cache:
            return None

        result, timestamp = self._cache[canonical_url]
        age = (datetime.now() - timestamp).total_seconds()

        if age > self.cache_ttl:
            # Cache expired
            del self._cache[canonical_url]
            return None

        self._stats["cache_hits"] += 1
        logger.debug(f"Returning cached result for: {canonical_url[:60]}")
        return result

    def _cache_result(self, canonical_url: str, result: FetchResult):
        """Cache fetch result"""
        self._cache[canonical_url] = (result, datetime.now())

        # Simple cache size management (keep last 200 entries)
        if len(self._cache) > 200:
            # Remove oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate (words * 1.3)"""
        if not text:
            return 0
        words = len(text.split())
        return int(words * 1.3)

    async def _extract_html_content(
        self, html: str, url: str
    ) -> tuple[str | None, str | None, datetime | None]:
        """
        Extract readable content from HTML using available libraries
        Returns: (content, title, published_at)
        """
        content = None
        title = None
        published_at = None

        # Try trafilatura first (best for article extraction)
        if self._extraction_libs.get("trafilatura"):
            try:
                import trafilatura
                from trafilatura.metadata import extract_metadata

                content = trafilatura.extract(
                    html, include_comments=False, include_tables=False
                )
                if content:
                    # Try to extract metadata
                    metadata = extract_metadata(html)
                    if metadata:
                        title = metadata.title
                        if metadata.date:
                            try:
                                published_at = datetime.fromisoformat(metadata.date)
                            except Exception:
                                pass

                    logger.debug(f"Extracted content with trafilatura from {url[:60]}")
                    return content, title, published_at
            except Exception as e:
                logger.debug(f"Trafilatura extraction failed: {e}")

        # Fallback to readability-lxml
        if self._extraction_libs.get("readability") and self._extraction_libs.get(
            "beautifulsoup"
        ):
            try:
                from bs4 import BeautifulSoup
                from readability import Document

                doc = Document(html)
                title = doc.title()
                content_html = doc.summary()

                # Extract text from HTML
                soup = BeautifulSoup(content_html, "html.parser")
                content = soup.get_text(separator="\n", strip=True)

                # Try to extract published date from meta tags
                soup_full = BeautifulSoup(html, "html.parser")
                for meta_name in [
                    "article:published_time",
                    "datePublished",
                    "publishdate",
                ]:
                    meta = soup_full.find("meta", property=meta_name) or soup_full.find(
                        "meta", attrs={"name": meta_name}
                    )
                    if meta and meta.get("content"):
                        try:
                            published_at = datetime.fromisoformat(
                                meta["content"].replace("Z", "+00:00")
                            )
                            break
                        except Exception:
                            pass

                logger.debug(f"Extracted content with readability from {url[:60]}")
                return content, title, published_at
            except Exception as e:
                logger.debug(f"Readability extraction failed: {e}")

        # Final fallback to BeautifulSoup text extraction
        if self._extraction_libs.get("beautifulsoup"):
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(html, "html.parser")

                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()

                # Get title
                title_tag = soup.find("title")
                title = title_tag.get_text() if title_tag else None

                # Get text
                content = soup.get_text(separator="\n", strip=True)

                logger.debug(f"Extracted content with BeautifulSoup from {url[:60]}")
                return content, title, published_at
            except Exception as e:
                logger.debug(f"BeautifulSoup extraction failed: {e}")

        return None, None, None

    async def _extract_pdf_content(
        self, pdf_bytes: bytes, url: str
    ) -> tuple[str | None, str | None]:
        """
        Extract text from PDF using available libraries
        Returns: (content, title)
        """
        if not self.pdf_enabled:
            return None, None

        # Try PyMuPDF first (best quality)
        if self._extraction_libs.get("pymupdf"):
            try:
                import io

                import pymupdf

                doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
                content_parts = []
                title = doc.metadata.get("title")

                for page in doc:
                    content_parts.append(page.get_text())

                content = "\n".join(content_parts)
                doc.close()

                logger.debug(f"Extracted PDF content with PyMuPDF from {url[:60]}")
                return content, title
            except Exception as e:
                logger.debug(f"PyMuPDF extraction failed: {e}")

        # Fallback to pypdf
        if self._extraction_libs.get("pypdf"):
            try:
                import io

                import pypdf

                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                content_parts = []
                title = reader.metadata.title if reader.metadata else None

                for page in reader.pages:
                    content_parts.append(page.extract_text())

                content = "\n".join(content_parts)

                logger.debug(f"Extracted PDF content with pypdf from {url[:60]}")
                return content, title
            except Exception as e:
                logger.debug(f"pypdf extraction failed: {e}")

        return None, None

    async def fetch_url(self, url: str) -> FetchResult:
        """
        Fetch and extract content from a single URL

        Args:
            url: URL to fetch

        Returns:
            FetchResult with extracted content or error
        """
        if not self.enabled:
            return FetchResult(
                url=url,
                canonical_url=url,
                content=None,
                content_type=None,
                title=None,
                published_at=None,
                extracted_at=datetime.now(),
                tokens_estimate=0,
                error="Web fetch disabled",
            )

        # Normalize URL
        canonical_url = self._normalize_url(url)

        # Check cache
        cached = self._get_cached_result(canonical_url)
        if cached:
            return cached

        # Check domain allowlist/blocklist
        if not self._is_allowed_domain(url):
            error = f"Domain blocked or not in allowlist: {self._get_domain(url)}"
            logger.debug(error)
            self._stats["failures"] += 1
            self._stats["failures_by_reason"]["blocked_domain"] += 1
            return FetchResult(
                url=url,
                canonical_url=canonical_url,
                content=None,
                content_type=None,
                title=None,
                published_at=None,
                extracted_at=datetime.now(),
                tokens_estimate=0,
                error=error,
            )

        # Check rate limit
        if not self._check_domain_rate_limit(url):
            error = f"Rate limit exceeded for domain: {self._get_domain(url)}"
            logger.debug(error)
            self._stats["failures"] += 1
            self._stats["failures_by_reason"]["rate_limited"] += 1
            return FetchResult(
                url=url,
                canonical_url=canonical_url,
                content=None,
                content_type=None,
                title=None,
                published_at=None,
                extracted_at=datetime.now(),
                tokens_estimate=0,
                error=error,
            )

        # Fetch with concurrency control
        async with self._semaphore:
            start_time = time.time()

            # Optional LangChain backend (feature-flagged)
            try:
                if os.getenv("WEB_FETCH_IMPL", "custom").lower() == "langchain":
                    from .web_fetch_lc_loader import LangChainWebLoader

                    lc = LangChainWebLoader()
                    if lc.is_available():
                        content, title, published_at, content_type = await lc.fetch(url)
                        canonical = self._normalize_url(url)
                        tokens_estimate = (
                            self._estimate_tokens(content) if content else 0
                        )
                        result = FetchResult(
                            url=url,
                            canonical_url=canonical,
                            content=(content[:10000] if content else None),
                            content_type=content_type or "text/html",
                            title=title,
                            published_at=published_at,
                            extracted_at=datetime.now(),
                            tokens_estimate=min(tokens_estimate, 3000),
                            error=None if content else "No content extracted",
                        )
                        if content:
                            self._cache_result(canonical, result)
                        return result
            except Exception:
                # If LC path fails, fall through to custom HTTPX fetch
                pass

            try:
                import httpx

                headers = {
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/pdf,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                }

                async with httpx.AsyncClient(
                    timeout=self.timeout, follow_redirects=True
                ) as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()

                    # Check content length
                    content_length = int(response.headers.get("content-length", 0))
                    if content_length > self.max_bytes:
                        error = f"Content too large: {content_length} bytes"
                        logger.debug(error)
                        self._stats["failures"] += 1
                        self._stats["failures_by_reason"]["too_large"] += 1
                        return FetchResult(
                            url=url,
                            canonical_url=str(response.url),
                            content=None,
                            content_type=response.headers.get("content-type"),
                            title=None,
                            published_at=None,
                            extracted_at=datetime.now(),
                            tokens_estimate=0,
                            error=error,
                        )

                    # Update canonical URL from final redirect
                    canonical_url = str(response.url)
                    content_type = response.headers.get("content-type", "").lower()

                    # Extract content based on content type
                    content = None
                    title = None
                    published_at = None

                    if "html" in content_type:
                        html = response.text
                        content, title, published_at = await self._extract_html_content(
                            html, url
                        )
                    elif "pdf" in content_type and self.pdf_enabled:
                        pdf_bytes = response.content
                        content, title = await self._extract_pdf_content(pdf_bytes, url)
                    else:
                        error = f"Unsupported content type: {content_type}"
                        logger.debug(error)
                        self._stats["failures"] += 1
                        self._stats["failures_by_reason"]["unsupported_type"] += 1
                        return FetchResult(
                            url=url,
                            canonical_url=canonical_url,
                            content=None,
                            content_type=content_type,
                            title=None,
                            published_at=None,
                            extracted_at=datetime.now(),
                            tokens_estimate=0,
                            error=error,
                        )

                    # Create result
                    tokens_estimate = self._estimate_tokens(content) if content else 0

                    result = FetchResult(
                        url=url,
                        canonical_url=canonical_url,
                        content=content[:10000]
                        if content
                        else None,  # Cap at 10k chars for safety
                        content_type=content_type,
                        title=title,
                        published_at=published_at,
                        extracted_at=datetime.now(),
                        tokens_estimate=min(
                            tokens_estimate, 3000
                        ),  # Cap token estimate
                        error=None if content else "No content extracted",
                    )

                    # Update stats
                    fetch_time = time.time() - start_time
                    self._stats["fetched_count"] += 1
                    self._stats["total_fetch_time"] += fetch_time

                    if content:
                        # Cache successful result
                        self._cache_result(canonical_url, result)
                        logger.info(
                            f"Successfully fetched and extracted content from {url[:60]} ({fetch_time:.2f}s, {tokens_estimate} tokens)"
                        )
                    else:
                        self._stats["failures"] += 1
                        self._stats["failures_by_reason"]["extraction_failed"] += 1

                    return result

            except httpx.TimeoutException:
                error = f"Timeout fetching URL: {url}"
                logger.debug(error)
                self._stats["failures"] += 1
                self._stats["failures_by_reason"]["timeout"] += 1
            except httpx.HTTPStatusError as e:
                error = f"HTTP error {e.response.status_code}: {url}"
                logger.debug(error)
                self._stats["failures"] += 1
                self._stats["failures_by_reason"][f"http_{e.response.status_code}"] += 1
            except Exception as e:
                error = f"Error fetching URL: {str(e)}"
                logger.debug(error)
                self._stats["failures"] += 1
                self._stats["failures_by_reason"]["other"] += 1

            return FetchResult(
                url=url,
                canonical_url=canonical_url,
                content=None,
                content_type=None,
                title=None,
                published_at=None,
                extracted_at=datetime.now(),
                tokens_estimate=0,
                error=error,
            )

    async def fetch_multiple(self, urls: list[str]) -> list[FetchResult]:
        """
        Fetch and extract content from multiple URLs concurrently

        Args:
            urls: List of URLs to fetch

        Returns:
            List of FetchResult objects
        """
        if not self.enabled:
            return [
                FetchResult(
                    url=url,
                    canonical_url=url,
                    content=None,
                    content_type=None,
                    title=None,
                    published_at=None,
                    extracted_at=datetime.now(),
                    tokens_estimate=0,
                    error="Web fetch disabled",
                )
                for url in urls
            ]

        # Limit number of URLs to fetch
        urls_to_fetch = urls[: self.max_fetch]

        logger.info(f"Fetching {len(urls_to_fetch)} URLs (max: {self.max_fetch})")

        # Fetch concurrently with semaphore control
        tasks = [self.fetch_url(url) for url in urls_to_fetch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions from gather
        fetch_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Exception fetching {urls_to_fetch[i]}: {result}")
                fetch_results.append(
                    FetchResult(
                        url=urls_to_fetch[i],
                        canonical_url=urls_to_fetch[i],
                        content=None,
                        content_type=None,
                        title=None,
                        published_at=None,
                        extracted_at=datetime.now(),
                        tokens_estimate=0,
                        error=str(result),
                    )
                )
            else:
                fetch_results.append(result)

        return fetch_results

    def get_stats(self) -> dict[str, any]:
        """Get fetch statistics"""
        cache_hit_rate = 0.0
        if self._stats["fetched_count"] + self._stats["cache_hits"] > 0:
            cache_hit_rate = self._stats["cache_hits"] / (
                self._stats["fetched_count"] + self._stats["cache_hits"]
            )

        avg_fetch_ms = 0.0
        if self._stats["fetched_count"] > 0:
            avg_fetch_ms = (
                self._stats["total_fetch_time"] / self._stats["fetched_count"]
            ) * 1000

        return {
            "enabled": self.enabled,
            "fetched_count": self._stats["fetched_count"],
            "cache_hits": self._stats["cache_hits"],
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self._cache),
            "failures": self._stats["failures"],
            "failures_by_reason": dict(self._stats["failures_by_reason"]),
            "avg_fetch_ms": avg_fetch_ms,
            "extraction_libs_available": {
                k: v for k, v in self._extraction_libs.items() if v
            },
        }

    def clear_cache(self):
        """Clear the fetch result cache"""
        self._cache.clear()
        logger.info("Web fetch cache cleared")


# Global singleton instance
_web_fetch_service_instance: WebFetchService | None = None


def get_web_fetch_service() -> WebFetchService:
    """Get singleton WebFetchService instance"""
    global _web_fetch_service_instance

    if _web_fetch_service_instance is None:
        # Load configuration from environment
        enabled = os.getenv("WEB_FETCH_ENABLED", "false").lower() == "true"
        concurrency = int(os.getenv("WEB_FETCH_CONCURRENCY", "5"))
        timeout_ms = int(os.getenv("WEB_FETCH_TIMEOUT_MS", "8000"))
        cache_ttl = int(os.getenv("WEB_FETCH_CACHE_TTL", "3600"))
        max_bytes = int(os.getenv("WEB_FETCH_MAX_BYTES", "2000000"))
        pdf_enabled = os.getenv("WEB_FETCH_PDF_ENABLED", "true").lower() == "true"
        user_agent = os.getenv("WEB_FETCH_USER_AGENT", "LocalChatbot/1.0")
        max_fetch = int(os.getenv("WEB_FETCH_MAX_FETCH", "3"))

        # Parse domain lists
        blocklist_str = os.getenv("WEB_FETCH_BLOCKLIST_DOMAINS", "")
        blocklist = (
            [d.strip() for d in blocklist_str.split(",") if d.strip()]
            if blocklist_str
            else None
        )

        allowlist_str = os.getenv("WEB_FETCH_ALLOWLIST_DOMAINS", "")
        allowlist = (
            [d.strip() for d in allowlist_str.split(",") if d.strip()]
            if allowlist_str
            else None
        )

        _web_fetch_service_instance = WebFetchService(
            enabled=enabled,
            concurrency=concurrency,
            timeout_ms=timeout_ms,
            cache_ttl=cache_ttl,
            max_bytes=max_bytes,
            pdf_enabled=pdf_enabled,
            user_agent=user_agent,
            blocklist_domains=blocklist,
            allowlist_domains=allowlist,
            max_fetch=max_fetch,
        )

    return _web_fetch_service_instance
