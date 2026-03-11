"""FastAPI server for the AI Company Research Agent."""

import logging
import os
import threading
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.linkedin_researcher import research_linkedin
from agent.precall_report import generate_precall_report
from agent.report_generator import save_report
from agent.scraper import scrape_website
from agent.search_enricher import enrich
from agent.summarizer import generate_summary
from agent.url_extractor import extract_url

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="AI Company Research Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# ---------------------------------------------------------------------------
# In-memory job store
# ---------------------------------------------------------------------------

_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _update_job(job_id: str, **kwargs: object) -> None:
    with _jobs_lock:
        _jobs[job_id].update(kwargs)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ResearchRequest(BaseModel):
    company: str
    product_context: Optional[str] = ""


class ResearchResponse(BaseModel):
    job_id: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# Background pipeline
# ---------------------------------------------------------------------------


def _run_pipeline(job_id: str, company: str, product_context: str) -> None:
    """Execute the full 5-step research pipeline in a background thread."""
    try:
        # Step 1 — URL Extraction
        _update_job(job_id, step=1, step_name="URL Extraction", progress=10)
        logger.info("[%s] Step 1: Extracting URL for '%s'", job_id, company)
        try:
            url = extract_url(company)
        except Exception as exc:
            url = ""
            logger.warning("[%s] URL extraction failed: %s", job_id, exc)
        _update_job(job_id, url=url, progress=20)

        # Step 2 — Website Scraping
        _update_job(job_id, step=2, step_name="Website Scraping", progress=20)
        logger.info("[%s] Step 2: Scraping website %s", job_id, url)
        scraped: dict[str, str] = {}
        if url:
            try:
                scraped = scrape_website(url)
            except Exception as exc:
                logger.warning("[%s] Scraping failed: %s", job_id, exc)
        _update_job(job_id, scraped_pages=list(scraped.keys()), progress=35)

        # Step 3 — Web Search Enrichment
        _update_job(job_id, step=3, step_name="Web Research", progress=35)
        logger.info("[%s] Step 3: Web research for '%s'", job_id, company)
        try:
            search_data = enrich(company)
        except Exception as exc:
            logger.warning("[%s] Search enrichment failed: %s", job_id, exc)
            search_data = {}
        _update_job(job_id, progress=50)

        # Step 3b — LinkedIn Research
        _update_job(job_id, step_name="LinkedIn Research", progress=50)
        logger.info("[%s] Step 3b: LinkedIn research for '%s'", job_id, company)
        try:
            linkedin_data = research_linkedin(company)
        except Exception as exc:
            logger.warning("[%s] LinkedIn research failed: %s", job_id, exc)
            linkedin_data = {"company_page": "", "prospects": []}
        _update_job(job_id, progress=60)

        # Step 4 — AI Summary
        _update_job(job_id, step=4, step_name="AI Report Generation", progress=60)
        logger.info("[%s] Step 4: Generating AI summary", job_id)
        try:
            summary = generate_summary(company, scraped, search_data, linkedin_data)
        except Exception as exc:
            logger.error("[%s] Summary generation failed: %s", job_id, exc)
            summary = f"# {company} — Research Report\n\n*Report generation failed: {exc}*"
        _update_job(job_id, progress=80)

        # Step 5 — Pre-Call Report
        _update_job(job_id, step=5, step_name="Pre-Call Report", progress=80)
        logger.info("[%s] Step 5: Generating pre-call report", job_id)
        try:
            precall = generate_precall_report(company, product_context, summary, linkedin_data)
        except Exception as exc:
            logger.error("[%s] Pre-call report failed: %s", job_id, exc)
            precall = f"# {company} — Pre-Call Report\n\n*Report generation failed: {exc}*"
        _update_job(job_id, progress=95)

        # Save reports
        try:
            paths = save_report(company, summary, precall)
        except Exception as exc:
            logger.warning("[%s] Failed to save reports: %s", job_id, exc)
            paths = {}

        _update_job(
            job_id,
            status="completed",
            step=5,
            step_name="Complete",
            progress=100,
            summary=summary,
            precall=precall,
            report_paths=paths,
        )
        logger.info("[%s] Pipeline complete for '%s'", job_id, company)

    except Exception as exc:
        logger.exception("[%s] Pipeline failed: %s", job_id, exc)
        _update_job(
            job_id,
            status="failed",
            error=str(exc),
            progress=0,
        )


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------


@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Company Research Agent"}


@app.post("/api/research", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest, background_tasks: BackgroundTasks
) -> ResearchResponse:
    """Start a research pipeline job.

    Returns a job_id for polling via GET /api/status/{job_id}.
    """
    company = request.company.strip()
    if not company:
        raise HTTPException(status_code=400, detail="'company' field is required.")

    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "company": company,
            "product_context": request.product_context or "",
            "status": "running",
            "step": 0,
            "step_name": "Initialising",
            "progress": 0,
            "summary": None,
            "precall": None,
            "error": None,
        }

    background_tasks.add_task(
        _run_pipeline, job_id, company, request.product_context or ""
    )
    return ResearchResponse(
        job_id=job_id,
        status="running",
        message=f"Research started for '{company}'. Poll /api/status/{job_id}.",
    )


@app.get("/api/status/{job_id}")
async def get_status(job_id: str) -> dict:
    """Poll the status of a research job."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    # Return a copy without exposing internal keys
    return {
        "job_id": job["job_id"],
        "company": job["company"],
        "status": job["status"],
        "step": job["step"],
        "step_name": job["step_name"],
        "progress": job["progress"],
        "summary": job.get("summary"),
        "precall": job.get("precall"),
        "error": job.get("error"),
    }


@app.get("/", response_class=HTMLResponse)
async def serve_index() -> FileResponse:
    """Serve the main web application."""
    index_path = _STATIC_DIR / "index.html"
    return FileResponse(str(index_path))
