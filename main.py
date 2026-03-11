"""CLI entry point for the AI Company Research Agent."""

import argparse
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Company Research Agent — generate a research report from the CLI."
    )
    parser.add_argument(
        "company",
        help="Company name or URL to research (e.g. 'BYJUS' or 'https://byjus.com')",
    )
    parser.add_argument(
        "--product",
        default="",
        metavar="PRODUCT_CONTEXT",
        help="Your product/service description (used to tailor the pre-call report)",
    )
    parser.add_argument(
        "--no-precall",
        action="store_true",
        help="Skip the pre-call report generation",
    )
    args = parser.parse_args()

    from agent.url_extractor import extract_url
    from agent.scraper import scrape_website
    from agent.search_enricher import enrich
    from agent.linkedin_researcher import research_linkedin
    from agent.summarizer import generate_summary
    from agent.precall_report import generate_precall_report
    from agent.report_generator import save_report

    print(f"\n🔍 Researching: {args.company}\n")

    # Step 1
    print("Step 1/5 — Extracting URL...")
    try:
        url = extract_url(args.company)
        print(f"  ✅ URL: {url}")
    except Exception as exc:
        print(f"  ⚠️  URL extraction failed: {exc}")
        url = ""

    # Step 2
    print("Step 2/5 — Scraping website...")
    scraped: dict[str, str] = {}
    if url:
        try:
            scraped = scrape_website(url)
            print(f"  ✅ Scraped {len(scraped)} page(s)")
        except Exception as exc:
            print(f"  ⚠️  Scraping failed: {exc}")

    # Step 3
    print("Step 3/5 — Web research...")
    try:
        search_data = enrich(args.company)
        print(f"  ✅ Collected data across {len(search_data)} dimensions")
    except Exception as exc:
        print(f"  ⚠️  Search failed: {exc}")
        search_data = {}

    print("Step 3b/5 — LinkedIn research...")
    try:
        linkedin_data = research_linkedin(args.company)
        prospects = len(linkedin_data.get("prospects", []))
        print(f"  ✅ Found {prospects} prospect profile(s)")
    except Exception as exc:
        print(f"  ⚠️  LinkedIn research failed: {exc}")
        linkedin_data = {"company_page": "", "prospects": []}

    # Step 4
    print("Step 4/5 — Generating AI research report...")
    try:
        summary = generate_summary(args.company, scraped, search_data, linkedin_data)
        print("  ✅ Research report generated")
    except Exception as exc:
        print(f"  ❌ Failed: {exc}")
        sys.exit(1)

    # Step 5
    precall = ""
    if not args.no_precall:
        print("Step 5/5 — Generating pre-call report...")
        try:
            precall = generate_precall_report(
                args.company, args.product, summary, linkedin_data
            )
            print("  ✅ Pre-call report generated")
        except Exception as exc:
            print(f"  ⚠️  Pre-call report failed: {exc}")

    # Save reports
    paths = save_report(args.company, summary, precall)
    print(f"\n📄 Reports saved:")
    print(f"   Research: {paths['summary_path']}")
    if precall:
        print(f"   Pre-call: {paths['precall_path']}")

    print("\n--- RESEARCH REPORT PREVIEW ---\n")
    print(summary[:2000])
    print("\n[... full report saved to file ...]")


if __name__ == "__main__":
    main()
