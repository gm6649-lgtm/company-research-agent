"""Step 5 — Pre-Call Report Generator: Strategic sales prep report using Gemini."""

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


_PRECALL_PROMPT = """
You are an elite B2B sales strategist. Based on the company research data below, write a
comprehensive **Pre-Call Preparation Report** for a sales representative.

Company: {company}
Your Product/Service: {product_context}

--- RESEARCH SUMMARY ---
{summary}

--- LINKEDIN DATA ---
{linkedin}

---

Write a detailed pre-call report in **Markdown format** with tables wherever appropriate.
Do NOT output JSON. Use a professional, action-oriented tone.

# {company} — Pre-Call Preparation Report

## 1. Company At a Glance
A concise table: Industry | Size | Revenue | Stage | HQ | Website | Key Product.

## 2. Prospect Profiles & Approach Strategies
For each key executive you identified:
- A table: Name | Title | LinkedIn | Tenure | Background Summary
- A paragraph: Personalised approach strategy — how to engage THIS person specifically,
  what they care about, what resonates with their background.

## 3. Pain Points & Opportunities
A table with columns:
Pain Point | Evidence | Severity (🔴 Critical / 🟠 High / 🟡 Medium) | How Your Product Helps

## 4. Recommended Talk Tracks

### Opening Lines
A table: Scenario | Opening Line

### Key Discovery Questions
A table: Question | Why Ask It | Expected Insight

## 5. Objection Handling
A table: Likely Objection | Root Cause | Recommended Response | Follow-up Question

## 6. Competitive Intel for the Call
A table: If They Mention | Their Strength | Your Counter | Proof Point

## 7. Pre-Call Checklist
A table: Task | Done? | Notes
(Include 10–12 tasks such as researching the prospect on LinkedIn, reviewing their latest
news, preparing a demo, setting a goal for the call, etc.)

## 8. Call Strategy Summary
A table: Element | Recommendation
(Include: Tone, Primary Goal, Secondary Goal, Ideal Call Length, Best Time to Call,
 Follow-up Action, Success Metric.)
""".strip()


def generate_precall_report(
    company: str,
    product_context: str,
    summary: str,
    linkedin_data: dict,
) -> str:
    """Generate a strategic pre-call report using Gemini.

    Args:
        company: Company name.
        product_context: Description of the caller's product/service.
        summary: Markdown research summary from Step 4.
        linkedin_data: LinkedIn research results.

    Returns:
        Markdown-formatted pre-call report as a string.
    """
    if not product_context:
        product_context = "a B2B SaaS solution (provide more context for a tailored report)"

    model = _get_model()

    linkedin_text = f"Company LinkedIn: {linkedin_data.get('company_page', 'N/A')}\n"
    for p in linkedin_data.get("prospects", []):
        linkedin_text += (
            f"\n**{p['role']}** — LinkedIn: {p.get('linkedin_url', 'N/A')}\n"
        )
        for snippet in p.get("snippets", []):
            linkedin_text += f"  - {snippet}\n"

    prompt = _PRECALL_PROMPT.format(
        company=company,
        product_context=product_context,
        summary=summary,
        linkedin=linkedin_text,
    )
    logger.info("Generating pre-call report with Gemini for: %s", company)
    response = model.generate_content(prompt)
    return response.text
