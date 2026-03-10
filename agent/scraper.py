"""Step 2 — Website Scraper: Scrape key pages from a company website."""

import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_TARGET_PATHS = [
    "/",
    "/about",
    "/about-us",
    "/team",
    "/leadership",
    "/products",
    "/services",
    "/careers",
    "/contact",
]

_MAX_CHARS_PER_PAGE = 5_000
_TIMEOUT = 10  # seconds


def _fetch_page(url: str, session: requests.Session) -> str | None:
    """Fetch *url* and return cleaned text content, or None on failure."""
    try:
        resp = session.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        logger.debug("Failed to fetch %s: %s", url, exc)
        return None

    try:
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as exc:
        logger.debug("Failed to parse %s: %s", url, exc)
        return None

    # Remove noisy tags
    for tag in soup(["script", "style", "nav", "footer", "noscript", "iframe"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = " ".join(text.split())
    return text[:_MAX_CHARS_PER_PAGE]


def scrape_website(base_url: str) -> dict[str, str]:
    """Scrape key pages of *base_url* and return a mapping of path → text.

    Args:
        base_url: Root URL of the company website, e.g. "https://byjus.com".

    Returns:
        A dict where keys are the page paths that were successfully scraped
        and values are the extracted text content (≤5 000 chars each).
    """
    base_url = base_url.rstrip("/")
    session = requests.Session()
    session.headers.update({"User-Agent": _USER_AGENT})

    results: dict[str, str] = {}
    seen_content: set[str] = set()

    for path in _TARGET_PATHS:
        url = urljoin(base_url + "/", path.lstrip("/"))
        if path == "/":
            url = base_url + "/"
        logger.info("Scraping %s", url)
        text = _fetch_page(url, session)
        if text and text not in seen_content:
            results[path] = text
            seen_content.add(text)

    return results
