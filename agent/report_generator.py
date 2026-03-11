"""Report Generator: Save research reports as Markdown files."""

import logging
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)

_REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")


def _safe_filename(name: str) -> str:
    """Convert a company name to a filesystem-safe string."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def save_report(company: str, summary: str, precall: str) -> dict[str, str]:
    """Save research reports to the /reports directory.

    Args:
        company: Company name (used in file names).
        summary: Markdown content of the company research report.
        precall: Markdown content of the pre-call report.

    Returns:
        A dict with keys ``summary_path`` and ``precall_path`` pointing to
        the saved files.
    """
    os.makedirs(_REPORTS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = _safe_filename(company)

    summary_filename = f"{slug}_research_{timestamp}.md"
    precall_filename = f"{slug}_precall_{timestamp}.md"

    summary_path = os.path.join(_REPORTS_DIR, summary_filename)
    precall_path = os.path.join(_REPORTS_DIR, precall_filename)

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)

    with open(precall_path, "w", encoding="utf-8") as f:
        f.write(precall)

    logger.info("Reports saved: %s, %s", summary_path, precall_path)
    return {"summary_path": summary_path, "precall_path": precall_path}
