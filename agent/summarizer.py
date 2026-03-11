"""Step 4 — AI Summary Generator: Generate a comprehensive Markdown research report."""

import json
import logging
import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_MODEL = "gemini-1.5-flash"


def _get_model() -> genai.GenerativeModel:
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY is not set. "
            "Get a free key at https://aistudio.google.com/app/apikey"
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(_MODEL)


def _format_scraped(scraped: dict[str, str]) -> str:
    parts = []
    for path, text in scraped.items():
        parts.append(f"### Page: {path}\n{text}")
    return "\n\n".join(parts) if parts else "No scraped content available."


def _format_search(search_data: dict[str, list[dict]]) -> str:
    parts = []
    for dimension, results in search_data.items():
        parts.append(f"### {dimension.upper()}")
        for r in results:
            parts.append(f"- **{r.get('title', '')}** ({r.get('href', '')})")
            if r.get("body"):
                parts.append(f"  {r['body']}")
    return "\n".join(parts) if parts else "No search data available."


def _format_linkedin(linkedin_data: dict) -> str:
    lines = [f"Company LinkedIn: {linkedin_data.get('company_page', 'N/A')}"]
    for p in linkedin_data.get("prospects", []):
        lines.append(
            f"\n**{p['role']}** — LinkedIn: {p.get('linkedin_url', 'N/A')}"
        )
        for snippet in p.get("snippets", []):
            lines.append(f"  - {snippet}")
    return "\n".join(lines)


_REPORT_PROMPT = """
You are a professional business analyst. Based on the research data below, write a
comprehensive company research report in **Markdown format**.

Company: {company}

--- WEBSITE CONTENT ---
{scraped}

--- WEB SEARCH DATA ---
{search}

--- LINKEDIN DATA ---
{linkedin}

---

Write a well-structured Markdown report with the following sections. Use tables wherever
data fits naturally. Write in a professional, informative tone. Do NOT output JSON.

# {company} — Company Research Report

## 1. Company Snapshot
A concise table with: Industry, Founded, Headquarters, CEO, Employees, Website, LinkedIn.

## 2. About the Company
2–3 paragraphs describing what the company does, its mission, and its market position.

## 3. Company Timeline
A table with columns: Year | Milestone | Significance.

## 4. Leadership Team & Prospect Profiles
For each key executive (CEO, Co-Founder, CTO, COO — include all you can find):
- A brief header with their name, title, and LinkedIn URL
- A table with: Background | Education | Previous Companies | Years at Company
- A paragraph with career history and notable achievements
- An AI Insight paragraph: what makes them tick, communication style, what to know
  before a call

## 5. Products & Services
A table with columns: Product/Service | Description | Target Market | Key Differentiator.

## 6. Key Platform Features
A table with columns: Feature | Description | Benefit (use emojis in the Feature column).

## 7. Financials & Funding
Two tables:
- Financial Metrics: Metric | Value | Notes
- Investors & Funding Rounds: Round | Amount | Investors | Date

## 8. Recent News & Developments
A table with columns: Date | Event | Impact/Significance.

## 9. Competitive Landscape
A table with columns: Competitor | Strengths | Weaknesses | Differentiator vs {company}.

## 10. Key Takeaways
A numbered list of 5–7 key insights a sales rep should know before engaging this company.
""".strip()


def generate_summary(
    company: str,
    scraped: dict[str, str],
    search_data: dict[str, list[dict]],
    linkedin_data: dict,
) -> str:
    """Generate a comprehensive Markdown research report using Gemini.

    Args:
        company: Company name.
        scraped: Dict of path → scraped text from the website.
        search_data: Dict of dimension → search results.
        linkedin_data: LinkedIn research results.

    Returns:
        Markdown-formatted research report as a string.
    """
    model = _get_model()
    prompt = _REPORT_PROMPT.format(
        company=company,
        scraped=_format_scraped(scraped),
        search=_format_search(search_data),
        linkedin=_format_linkedin(linkedin_data),
    )
    logger.info("Generating summary report with Gemini for: %s", company)
    response = model.generate_content(prompt)
    return response.text
