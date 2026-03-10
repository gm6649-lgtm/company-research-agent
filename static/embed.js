/**
 * AI Company Research Agent — Embeddable Widget
 *
 * Usage:
 *   <div id="company-research-widget"></div>
 *   <script src="https://your-domain.com/static/embed.js"></script>
 *
 * Optional configuration:
 *   <script>
 *     window.CRAConfig = {
 *       apiBase: 'https://your-domain.com',  // default: auto-detected
 *       containerId: 'company-research-widget'
 *     };
 *   </script>
 */
(function () {
  'use strict';

  /* ── Config ── */
  const cfg = window.CRAConfig || {};
  const CONTAINER_ID = cfg.containerId || 'company-research-widget';
  const API_BASE =
    cfg.apiBase ||
    (document.currentScript
      ? new URL(document.currentScript.src).origin
      : window.location.origin);
  const POLL_INTERVAL = 3000;

  /* ── Inject CSS ── */
  const STYLE = `
  #cra-widget * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  #cra-widget { display: inline-block; width: 100%; }
  .cra-form { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.25rem; }
  .cra-title { font-size: 1rem; font-weight: 700; color: #58a6ff; margin-bottom: .9rem; display: flex; align-items: center; gap: .4rem; }
  .cra-input { width: 100%; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #e6edf3; font-size: .9rem; padding: .5rem .75rem; outline: none; margin-bottom: .6rem; transition: border-color .15s; }
  .cra-input:focus { border-color: #58a6ff; }
  .cra-input::placeholder { color: #8b949e; }
  .cra-btn { width: 100%; background: #1f6feb; color: #fff; border: none; border-radius: 6px; font-size: .95rem; font-weight: 600; padding: .55rem; cursor: pointer; transition: opacity .15s; }
  .cra-btn:hover { opacity: .85; }
  .cra-btn:disabled { opacity: .4; cursor: not-allowed; }
  /* Modal */
  .cra-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.75); z-index: 99998; display: flex; align-items: center; justify-content: center; padding: 1rem; }
  .cra-modal { background: #161b22; border: 1px solid #30363d; border-radius: 10px; width: 100%; max-width: 860px; max-height: 92vh; display: flex; flex-direction: column; overflow: hidden; }
  .cra-modal-header { display: flex; align-items: center; justify-content: space-between; padding: .9rem 1.25rem; border-bottom: 1px solid #30363d; }
  .cra-modal-title { font-size: 1rem; font-weight: 700; color: #e6edf3; }
  .cra-modal-close { background: none; border: none; color: #8b949e; font-size: 1.4rem; cursor: pointer; line-height: 1; }
  .cra-modal-close:hover { color: #e6edf3; }
  .cra-modal-body { flex: 1; overflow-y: auto; padding: 1.25rem; }
  /* Progress */
  .cra-progress-wrap { margin-bottom: 1rem; }
  .cra-progress-label { font-size: .8rem; color: #8b949e; margin-bottom: .3rem; display: flex; justify-content: space-between; }
  .cra-progress-track { height: 5px; background: #30363d; border-radius: 3px; overflow: hidden; }
  .cra-progress-fill { height: 100%; background: linear-gradient(90deg, #1f6feb, #58a6ff); border-radius: 3px; transition: width .4s ease; }
  /* Tabs */
  .cra-tabs { display: flex; gap: .4rem; border-bottom: 1px solid #30363d; margin-bottom: .9rem; padding-bottom: .4rem; }
  .cra-tab { background: none; border: 1px solid transparent; border-radius: 6px 6px 0 0; color: #8b949e; font-size: .85rem; padding: .35rem .8rem; cursor: pointer; transition: all .15s; }
  .cra-tab.active { background: #0d1117; border-color: #30363d; color: #58a6ff; font-weight: 600; }
  .cra-tab-content { display: none; color: #c9d1d9; font-size: .88rem; line-height: 1.7; }
  .cra-tab-content.active { display: block; }
  /* Report markdown */
  .cra-report h1 { font-size: 1.4rem; color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: .4rem; margin: 0 0 1rem; }
  .cra-report h2 { font-size: 1.1rem; color: #c9d1d9; border-left: 3px solid #58a6ff; padding-left: .5rem; margin: 1.5rem 0 .5rem; }
  .cra-report h3 { font-size: .95rem; color: #c9d1d9; margin: 1rem 0 .4rem; }
  .cra-report p { margin-bottom: .7rem; }
  .cra-report table { width: 100%; border-collapse: collapse; margin: .75rem 0 1.1rem; font-size: .82rem; }
  .cra-report th { background: #1c2128; color: #58a6ff; text-align: left; padding: .45rem .65rem; border-bottom: 2px solid #30363d; }
  .cra-report td { padding: .4rem .65rem; border-bottom: 1px solid #30363d; vertical-align: top; }
  .cra-report tr:nth-child(even) td { background: rgba(255,255,255,.02); }
  .cra-report ul, .cra-report ol { padding-left: 1.2rem; margin-bottom: .7rem; }
  .cra-report a { color: #58a6ff; }
  .cra-report strong { color: #e6edf3; }
  .cra-actions { display: flex; gap: .5rem; margin-bottom: .75rem; }
  .cra-action-btn { background: #21262d; border: 1px solid #30363d; border-radius: 5px; color: #c9d1d9; font-size: .78rem; padding: .3rem .7rem; cursor: pointer; transition: opacity .15s; }
  .cra-action-btn:hover { opacity: .8; }
  .cra-error { color: #f85149; font-size: .85rem; margin-top: .5rem; }
  `;

  function injectStyle() {
    if (document.getElementById('cra-style')) return;
    const el = document.createElement('style');
    el.id = 'cra-style';
    el.textContent = STYLE;
    document.head.appendChild(el);
  }

  /* ── Load marked.js dynamically ── */
  function loadMarked(cb) {
    if (window.marked) { cb(); return; }
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
    s.onload = cb;
    document.head.appendChild(s);
  }

  /* ── Widget State ── */
  let jobId = null;
  let pollTimer = null;
  let summaryMd = '';
  let precallMd = '';
  let activeTab = 'summary';

  /* ── Build Widget Form ── */
  function buildForm(container) {
    container.innerHTML = `
      <div class="cra-form">
        <div class="cra-title">🤖 Company Research Agent</div>
        <input class="cra-input" id="cra-company" type="text" placeholder="Company name or URL…" />
        <input class="cra-input" id="cra-product" type="text" placeholder="Your product/service (optional)" />
        <button class="cra-btn" id="cra-search-btn" onclick="window.__craSearch()">🔍 Research</button>
        <div class="cra-error" id="cra-form-error" style="display:none;"></div>
      </div>
    `;

    document.getElementById('cra-company').addEventListener('keydown', e => {
      if (e.key === 'Enter') window.__craSearch();
    });
  }

  /* ── Build Modal ── */
  function openModal(company) {
    const overlay = document.createElement('div');
    overlay.className = 'cra-overlay';
    overlay.id = 'cra-overlay';
    overlay.innerHTML = `
      <div class="cra-modal" id="cra-modal">
        <div class="cra-modal-header">
          <span class="cra-modal-title">🔍 Researching: ${escHtml(company)}</span>
          <button class="cra-modal-close" onclick="window.__craCloseModal()">✕</button>
        </div>
        <div class="cra-modal-body" id="cra-modal-body">
          <div class="cra-progress-wrap" id="cra-modal-progress">
            <div class="cra-progress-label">
              <span id="cra-prog-label">Initialising…</span>
              <span id="cra-prog-pct">0%</span>
            </div>
            <div class="cra-progress-track">
              <div class="cra-progress-fill" id="cra-prog-fill" style="width:0%"></div>
            </div>
          </div>
          <div id="cra-modal-results" style="display:none;">
            <div class="cra-actions">
              <button class="cra-action-btn" onclick="window.__craCopy()">📋 Copy</button>
              <button class="cra-action-btn" onclick="window.__craDownload()">⬇️ Download .md</button>
            </div>
            <div class="cra-tabs">
              <button class="cra-tab active" id="cra-tab-summary" onclick="window.__craTab('summary')">📊 Company Report</button>
              <button class="cra-tab" id="cra-tab-precall" onclick="window.__craTab('precall')">📞 Pre-Call Report</button>
            </div>
            <div class="cra-tab-content cra-report active" id="cra-content-summary"></div>
            <div class="cra-tab-content cra-report" id="cra-content-precall"></div>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    // Close on overlay click
    overlay.addEventListener('click', e => {
      if (e.target === overlay) window.__craCloseModal();
    });
  }

  /* ── Global Handlers ── */
  window.__craSearch = function () {
    const company = (document.getElementById('cra-company') || {}).value || '';
    const product = (document.getElementById('cra-product') || {}).value || '';
    const errEl = document.getElementById('cra-form-error');

    if (!company.trim()) {
      errEl.textContent = 'Please enter a company name or URL.';
      errEl.style.display = 'block';
      return;
    }
    errEl.style.display = 'none';
    document.getElementById('cra-search-btn').disabled = true;

    openModal(company.trim());

    fetch(`${API_BASE}/api/research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company: company.trim(), product_context: product.trim() }),
    })
      .then(r => r.json())
      .then(data => {
        jobId = data.job_id;
        pollTimer = setInterval(poll, POLL_INTERVAL);
      })
      .catch(err => {
        setProgress(0, 'Error: ' + err.message);
      });
  };

  window.__craCloseModal = function () {
    clearInterval(pollTimer);
    const ov = document.getElementById('cra-overlay');
    if (ov) ov.remove();
    const btn = document.getElementById('cra-search-btn');
    if (btn) btn.disabled = false;
    jobId = null;
  };

  window.__craTab = function (tab) {
    activeTab = tab;
    ['summary', 'precall'].forEach(t => {
      document.getElementById(`cra-tab-${t}`).classList.toggle('active', t === tab);
      document.getElementById(`cra-content-${t}`).classList.toggle('active', t === tab);
    });
  };

  window.__craCopy = function () {
    const text = activeTab === 'summary' ? summaryMd : precallMd;
    if (!text) return;
    navigator.clipboard.writeText(text).catch(() => {});
  };

  window.__craDownload = function () {
    const text = activeTab === 'summary' ? summaryMd : precallMd;
    if (!text) return;
    const blob = new Blob([text], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `company_${activeTab}_report.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  function setProgress(pct, label) {
    const fill = document.getElementById('cra-prog-fill');
    const lbl = document.getElementById('cra-prog-label');
    const pctEl = document.getElementById('cra-prog-pct');
    if (fill) fill.style.width = `${pct}%`;
    if (lbl) lbl.textContent = label;
    if (pctEl) pctEl.textContent = `${pct}%`;
  }

  function poll() {
    if (!jobId) return;
    fetch(`${API_BASE}/api/status/${jobId}`)
      .then(r => r.json())
      .then(job => {
        setProgress(job.progress || 0, job.step_name || 'Running…');
        if (job.status === 'completed') {
          clearInterval(pollTimer);
          summaryMd = job.summary || '';
          precallMd = job.precall || '';
          loadMarked(() => showResults());
          const btn = document.getElementById('cra-search-btn');
          if (btn) btn.disabled = false;
        } else if (job.status === 'failed') {
          clearInterval(pollTimer);
          setProgress(0, '⚠️ Failed: ' + (job.error || 'Unknown error'));
          const btn = document.getElementById('cra-search-btn');
          if (btn) btn.disabled = false;
        }
      })
      .catch(() => {});
  }

  function showResults() {
    const progEl = document.getElementById('cra-modal-progress');
    const resEl = document.getElementById('cra-modal-results');
    if (progEl) progEl.style.display = 'none';
    if (resEl) resEl.style.display = 'block';

    const sumEl = document.getElementById('cra-content-summary');
    const preEl = document.getElementById('cra-content-precall');
    if (sumEl) sumEl.innerHTML = summaryMd ? marked.parse(summaryMd) : '<p>No report.</p>';
    if (preEl) preEl.innerHTML = precallMd ? marked.parse(precallMd) : '<p>No report.</p>';
  }

  function escHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  /* ── Init ── */
  function init() {
    injectStyle();
    const container = document.getElementById(CONTAINER_ID);
    if (!container) {
      console.warn('[CRA Widget] Container #' + CONTAINER_ID + ' not found.');
      return;
    }
    const wrapper = document.createElement('div');
    wrapper.id = 'cra-widget';
    container.appendChild(wrapper);
    buildForm(wrapper);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
