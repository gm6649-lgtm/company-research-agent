"""Step 3 — Search Enricher: DuckDuckGo research across multiple dimensions."""

import logging

from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

_DIMENSIONS = {
    "overview": "{company} company overview what does it do",
    "leadership": "{company} CEO founder leadership team executives",
    "products": "{company} products services offerings",
    "financials": "{company} funding revenue valuation investors",
    "news": "{company} latest news 2024 2025",
    "competitors": "{company} competitors alternatives market",
    "linkedin": "{company} LinkedIn company page",
    "prospect_profiles": "{company} CEO CTO COO founder LinkedIn profile",
}

_MAX_RESULTS = 5


def enrich(company: str) -> dict[str, list[dict]]:
    """Search DuckDuckGo across multiple research dimensions for *company*.

    Args:
        company: The company name, e.g. "BYJUS".

    Returns:
        A dict mapping dimension name → list of result dicts, each with
        keys ``title``, ``href``, and ``body``.
    """
    data: dict[str, list[dict]] = {}

    with DDGS() as ddgs:
        for dimension, query_template in _DIMENSIONS.items():
            query = query_template.format(company=company)
            logger.info("Searching [%s]: %s", dimension, query)
            try:
                results = list(ddgs.text(query, max_results=_MAX_RESULTS))
                data[dimension] = [
                    {
                        "title": r.get("title", ""),
                        "href": r.get("href", ""),
                        "body": r.get("body", ""),
                    }
                    for r in results
                ]
            except Exception as exc:
                logger.warning("Search failed for dimension '%s': %s", dimension, exc)
                data[dimension] = []

    return data
