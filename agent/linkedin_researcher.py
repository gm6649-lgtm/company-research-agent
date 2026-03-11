"""Step 3b — LinkedIn Researcher: Find LinkedIn profiles for key prospects."""

import logging

from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

_ROLES = ["CEO", "Co-Founder", "CTO", "COO"]
_MAX_RESULTS = 3


def _search(query: str) -> list[dict]:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=_MAX_RESULTS))
            return [
                {
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", ""),
                }
                for r in results
            ]
    except Exception as exc:
        logger.warning("LinkedIn search failed: %s", exc)
        return []


def _find_linkedin_url(results: list[dict]) -> str:
    """Extract the first LinkedIn URL from search results."""
    from urllib.parse import urlparse

    for r in results:
        href = r.get("href", "")
        try:
            parsed = urlparse(href)
            netloc = parsed.netloc.lower()
            # Strip leading 'www.' before comparing to avoid substring false positives
            host = netloc[4:] if netloc.startswith("www.") else netloc
            if host == "linkedin.com" or host.endswith(".linkedin.com"):
                return href
        except Exception:
            pass
    return ""


def research_linkedin(company: str) -> dict:
    """Research LinkedIn presence for *company* and key decision-makers.

    Args:
        company: Company name, e.g. "BYJUS".

    Returns:
        A dict with:
          - ``company_page``: LinkedIn URL for the company page
          - ``prospects``: list of dicts per role with keys
            ``role``, ``linkedin_url``, ``snippets``
    """
    # Company LinkedIn page
    company_results = _search(f"{company} LinkedIn company page site:linkedin.com")
    company_page = _find_linkedin_url(company_results)
    if not company_page:
        # fallback without site: restriction
        company_results = _search(f"{company} official LinkedIn page")
        company_page = _find_linkedin_url(company_results)

    prospects = []
    for role in _ROLES:
        query = f"{company} {role} LinkedIn profile career background education"
        results = _search(query)
        linkedin_url = _find_linkedin_url(results)
        snippets = [r["body"] for r in results if r.get("body")]
        prospects.append(
            {
                "role": role,
                "linkedin_url": linkedin_url,
                "snippets": snippets,
            }
        )

    return {
        "company_page": company_page,
        "prospects": prospects,
    }
