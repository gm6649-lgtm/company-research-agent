/* global app state */
let currentJobId = null;
let pollTimer = null;
let currentSummary = '';
let currentPrecall = '';
let activeTab = 'summary';

const POLL_INTERVAL = 3000; // ms

// Step name → pipeline-step data-step mapping
const STEP_MAP = {
  'Initialising':            null,
  'URL Extraction':          '1',
  'Website Scraping':        '2',
  'Web Research':            '3',
  'LinkedIn Research':       '3b',
  'AI Report Generation':    '4',
  'Pre-Call Report':         '5',
  'Complete':                '5',
};

/* ── Start Research ── */
async function startResearch() {
  const company = document.getElementById('company-input').value.trim();
  if (!company) {
    showError('Please enter a company name or URL.');
    return;
  }
  const product = document.getElementById('product-input').value.trim();

  // Reset UI
  clearError();
  hideResults();
  resetSteps();
  showProgress();

  document.getElementById('research-btn').disabled = true;
  updateProgress(0, 'Initialising…');

  try {
    const resp = await fetch('/api/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company, product_context: product }),
    });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || 'Failed to start research.');
    }
    const data = await resp.json();
    currentJobId = data.job_id;
    pollTimer = setInterval(pollStatus, POLL_INTERVAL);
  } catch (err) {
    showError(err.message);
    document.getElementById('research-btn').disabled = false;
    hideProgress();
  }
}

/* ── Poll Job Status ── */
async function pollStatus() {
  if (!currentJobId) return;
  try {
    const resp = await fetch(`/api/status/${currentJobId}`);
    if (!resp.ok) return;
    const job = await resp.json();

    updateProgress(job.progress, job.step_name || 'Running…');
    highlightStep(job.step_name);

    if (job.status === 'completed') {
      clearInterval(pollTimer);
      currentSummary = job.summary || '';
      currentPrecall = job.precall || '';
      renderResults(currentSummary, currentPrecall);
      document.getElementById('research-btn').disabled = false;
    } else if (job.status === 'failed') {
      clearInterval(pollTimer);
      showError(job.error || 'Research pipeline failed.');
      document.getElementById('research-btn').disabled = false;
      hideProgress();
    }
  } catch (_) {
    /* network hiccup — keep polling */
  }
}

/* ── Render Reports ── */
function renderResults(summary, precall) {
  document.getElementById('tab-summary').innerHTML =
    summary ? marked.parse(summary) : '<p>No report generated.</p>';
  document.getElementById('tab-precall').innerHTML =
    precall ? marked.parse(precall) : '<p>No pre-call report generated.</p>';

  // Mark all steps done
  document.querySelectorAll('.pipeline-step').forEach(el => {
    el.classList.remove('active');
    el.classList.add('done');
    el.querySelector('.step-icon').textContent = '✅';
  });

  updateProgress(100, 'Complete ✅');
  document.getElementById('results-section').classList.remove('hidden');
  document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}

/* ── Tab Switching ── */
function switchTab(tab) {
  activeTab = tab;
  document.querySelectorAll('.tab').forEach(el =>
    el.classList.toggle('active', el.dataset.tab === tab)
  );
  document.querySelectorAll('.tab-content').forEach(el =>
    el.classList.toggle('active', el.id === `tab-${tab}`)
  );
}

/* ── Copy Report ── */
async function copyReport() {
  const text = activeTab === 'summary' ? currentSummary : currentPrecall;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    showTempMessage('📋 Copied!');
  } catch (_) {
    showTempMessage('Could not copy — try selecting and copying manually.');
  }
}

/* ── Download as Markdown ── */
function downloadReport() {
  const text = activeTab === 'summary' ? currentSummary : currentPrecall;
  if (!text) return;
  const suffix = activeTab === 'summary' ? 'research' : 'precall';
  const blob = new Blob([text], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `company_${suffix}_report.md`;
  a.click();
  URL.revokeObjectURL(url);
}

/* ── UI Helpers ── */
function updateProgress(pct, label) {
  document.getElementById('progress-bar').style.width = `${pct}%`;
  document.getElementById('progress-pct').textContent = `${pct}%`;
  document.getElementById('progress-label').textContent = label;
}

function highlightStep(stepName) {
  const stepKey = STEP_MAP[stepName];
  document.querySelectorAll('.pipeline-step').forEach(el => {
    const s = el.dataset.step;
    if (stepKey && s === stepKey) {
      el.classList.add('active');
      el.classList.remove('done');
      el.querySelector('.step-icon').textContent = '🔄';
    } else if (stepPassed(s, stepKey)) {
      el.classList.remove('active');
      el.classList.add('done');
      el.querySelector('.step-icon').textContent = '✅';
    }
  });
}

function stepPassed(step, currentStep) {
  const order = ['1', '2', '3', '3b', '4', '5'];
  const ci = order.indexOf(currentStep);
  const si = order.indexOf(step);
  return ci > -1 && si > -1 && si < ci;
}

function resetSteps() {
  document.querySelectorAll('.pipeline-step').forEach(el => {
    el.classList.remove('active', 'done');
    el.querySelector('.step-icon').textContent = '⏳';
  });
}

function showProgress() {
  document.getElementById('progress-section').classList.remove('hidden');
}

function hideProgress() {
  document.getElementById('progress-section').classList.add('hidden');
}

function hideResults() {
  document.getElementById('results-section').classList.add('hidden');
}

function showError(msg) {
  const banner = document.getElementById('error-banner');
  banner.textContent = `⚠️ ${msg}`;
  banner.classList.remove('hidden');
}

function clearError() {
  document.getElementById('error-banner').classList.add('hidden');
}

function showTempMessage(msg) {
  const el = document.createElement('div');
  el.style.cssText =
    'position:fixed;bottom:1.5rem;right:1.5rem;background:#1f6feb;color:#fff;' +
    'padding:.6rem 1.1rem;border-radius:6px;font-size:.9rem;z-index:9999;';
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2500);
}

/* ── Allow Enter key in inputs ── */
document.addEventListener('DOMContentLoaded', () => {
  ['company-input', 'product-input'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('keydown', e => { if (e.key === 'Enter') startResearch(); });
  });
});
