# 🤖 AI Company Research Agent

An AI-powered company research agent that generates comprehensive, human-readable
research reports and pre-call sales briefs — in seconds. Built as an embeddable web
app so it can be integrated into any website.

---

## ✨ What It Does

Enter any company name or URL and the agent runs a 5-step pipeline:

1. **URL Extraction** — Resolves the company name to its official website via DuckDuckGo
2. **Website Scraping** — Scrapes key pages (homepage, /about, /products, /team, etc.)
3. **Web Research** — Searches DuckDuckGo across 8 dimensions: overview, leadership, products, financials, news, competitors, LinkedIn, prospect profiles
4. **AI Report Generation** — Uses Google Gemini to produce a structured Markdown report with tables
5. **Pre-Call Report** — Generates a strategic sales preparation brief with pain points, talk tracks, objection handling, and call strategy

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/gm6649-lgtm/company-research-agent.git
cd company-research-agent
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your FREE Gemini API key
# Get one at: https://aistudio.google.com/app/apikey
```

### 3. Run the server

```bash
uvicorn app:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

### 4. CLI usage

```bash
python main.py "BYJUS"
python main.py "Stripe" --product "B2B SaaS payments plugin"
python main.py "https://openai.com" --no-precall
```

---

## 🐳 Docker

```bash
docker build -t company-research-agent .
docker run -p 8000:8000 -e GOOGLE_API_KEY=your-key company-research-agent
```

---

## 🔌 Embedding

Add the widget to any web page:

```html
<!-- 1. Create a container div -->
<div id="company-research-widget"></div>

<!-- 2. Load the widget script (replace with your domain) -->
<script src="https://your-domain.com/static/embed.js"></script>
```

Optional configuration:

```html
<script>
  window.CRAConfig = {
    apiBase: 'https://your-domain.com',
    containerId: 'company-research-widget'
  };
</script>
<script src="https://your-domain.com/static/embed.js"></script>
```

The widget renders a compact search form and opens results in a modal overlay.

---

## 📡 API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/research` | Start a research job |
| `GET` | `/api/status/{job_id}` | Poll job status / results |
| `GET` | `/` | Main web UI |
| `GET` | `/static/embed.js` | Embeddable widget script |

### POST /api/research

```json
{
  "company": "BYJUS",
  "product_context": "B2B SaaS learning platform"
}
```

Returns:

```json
{
  "job_id": "uuid-...",
  "status": "running",
  "message": "Research started for 'BYJUS'. Poll /api/status/<job_id>."
}
```

### GET /api/status/{job_id}

```json
{
  "job_id": "uuid-...",
  "company": "BYJUS",
  "status": "completed",
  "step": 5,
  "step_name": "Complete",
  "progress": 100,
  "summary": "# BYJUS — Company Research Report\n...",
  "precall": "# BYJUS — Pre-Call Preparation Report\n...",
  "error": null
}
```

Status values: `running` | `completed` | `failed`

---

## 🗂️ Project Structure

```
company-research-agent/
├── agent/
│   ├── __init__.py
│   ├── url_extractor.py        # Step 1 — Resolve company → URL
│   ├── scraper.py              # Step 2 — Scrape website pages
│   ├── search_enricher.py      # Step 3 — DuckDuckGo research
│   ├── linkedin_researcher.py  # Step 3b — LinkedIn profiles
│   ├── summarizer.py           # Step 4 — Gemini AI report
│   ├── precall_report.py       # Step 5 — Pre-call brief
│   └── report_generator.py    # Save reports to /reports
├── static/
│   ├── index.html              # Main web app
│   ├── style.css               # Dark-theme styling
│   ├── app.js                  # Frontend polling + rendering
│   └── embed.js                # Self-contained embeddable widget
├── reports/                    # Generated .md reports (gitignored)
├── app.py                      # FastAPI server
├── main.py                     # CLI entry point
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

---

## 💰 Cost

**$0** — Uses the Google Gemini free tier and DuckDuckGo (no API key needed for search).

---

## 🔧 Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Google Gemini API key (required). Get free at https://aistudio.google.com/app/apikey |
