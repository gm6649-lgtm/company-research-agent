"""Step 1 — URL Extractor: Resolve a company name or URL to its official website URL."""

import logging
from urllib.parse import urlparse, urlunparse

from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

# Domains that should be rejected as official company websites
_REJECT_DOMAINS = {
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "youtube.com",
    "wikipedia.org",
    "crunchbase.com",
    "bloomberg.com",
    "forbes.com",
    "techcrunch.com",
    "reuters.com",
    "businesswire.com",
    "prnewswire.com",
    "glassdoor.com",
    "indeed.com",
    "pitchbook.com",
    "owler.com",
    "zoominfo.com",
}


def _looks_like_url(text: str) -> bool:
    """Return True if the text appears to already be a URL."""
    text = text.strip()
    if text.startswith(("http://", "https://")):
        return True
    # bare domain like 'example.com'
    if "." in text and " " not in text and "/" not in text[:text.find(".")]:
        return True
    return False


def _normalise_url(url: str) -> str:
    """Ensure the URL has a scheme and normalise it."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    # Drop query/fragment from the root URL
    normalised = urlunparse((parsed.scheme, parsed.netloc, "/", "", "", ""))
    return normalised.rstrip("/")


def _domain_is_accepted(url: str) -> bool:
    """Return True if the URL belongs to an acceptable domain."""
    try:
        netloc = urlparse(url).netloc.lower()
        host = netloc[4:] if netloc.startswith("www.") else netloc
        for rejected in _REJECT_DOMAINS:
            if host == rejected or host.endswith("." + rejected):
                return False
        return True
    except Exception:
        return False


def extract_url(company_input: str) -> str:
    """Resolve *company_input* to the company's official website URL.

    Args:
        company_input: A company name (e.g. "BYJUS") or a URL
                       (e.g. "https://byjus.com").

    Returns:
        The canonical root URL of the company website, e.g.
        "https://byjus.com".

    Raises:
        ValueError: If no suitable URL can be found.
    """
    if _looks_like_url(company_input):
        return _normalise_url(company_input)

    logger.info("Searching DuckDuckGo for official website of: %s", company_input)
    query = f"{company_input} official website"
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=10))
    except Exception as exc:
        raise ValueError(f"DuckDuckGo search failed: {exc}") from exc

    for result in results:
        href = result.get("href", "")
        if href and _domain_is_accepted(href):
            url = _normalise_url(href)
            logger.info("Resolved '%s' → %s", company_input, url)
            return url

    raise ValueError(
        f"Could not find an official website URL for '{company_input}'."
    )
