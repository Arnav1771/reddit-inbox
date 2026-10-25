/**
 * Reddit Inbox - Interactive Google Stitch Dashboard Engine
 */

(function () {
  'use strict';

  let rawData = null;
  let currentView = 'worthy'; // 'worthy' | 'quarantine'
  let activeSubreddit = 'all';
  let currentThreshold = 80.0;
  let searchQuery = '';

  // DOM Elements
  const postsGrid = document.getElementById('posts-grid');
  const emptyState = document.getElementById('empty-state');
  const searchInput = document.getElementById('search-input');
  const thresholdSlider = document.getElementById('threshold-slider');
  const sliderValText = document.getElementById('slider-val-text');
  const subFiltersContainer = document.getElementById('subreddit-filters');
  const btnViewWorthy = document.getElementById('btn-view-worthy');
  const btnViewQuarantine = document.getElementById('btn-view-quarantine');
  const feedHeading = document.getElementById('feed-heading');
  const lastSyncTime = document.getElementById('last-sync-time');
  const toast = document.getElementById('toast');

  // Stats Elements
  const statSignalRatio = document.getElementById('stat-signal-ratio');
  const statWorthyCount = document.getElementById('stat-worthy-count');
  const statNoiseCount = document.getElementById('stat-noise-count');
  const worthyPillCount = document.getElementById('worthy-pill-count');
  const quarantinePillCount = document.getElementById('quarantine-pill-count');

  // Initialize
  async function init() {
    setupEventListeners();
    await loadData();
  }

  function setupEventListeners() {
    // Search input
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      render();
    });

    // Threshold slider
    thresholdSlider.addEventListener('input', (e) => {
      currentThreshold = parseFloat(e.target.value);
      sliderValText.textContent = `${currentThreshold.toFixed(1)}%`;
      render();
    });

    // View toggles
    btnViewWorthy.addEventListener('click', () => {
      currentView = 'worthy';
      btnViewWorthy.classList.add('active');
      btnViewQuarantine.classList.remove('active');
      feedHeading.textContent = 'Curated High-Signal Intelligence';
      render();
    });

    btnViewQuarantine.addEventListener('click', () => {
      currentView = 'quarantine';
      btnViewQuarantine.classList.add('active');
      btnViewWorthy.classList.remove('active');
      feedHeading.textContent = 'Quarantined Low-Signal Noise Audit';
      render();
    });
  }

  async function loadData() {
    try {
      const resp = await fetch('data.json');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      rawData = await resp.json();
      updateHeaderStats(rawData.metadata);
      buildSubredditPills(rawData.posts || []);
      render();
    } catch (err) {
      console.warn('Could not load data.json directly, falling back to embedded baseline:', err);
      // Fallback fallback if loaded via file:// protocol
      postsGrid.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">⚠️</div>
          <h3>Running via File URL</h3>
          <p>Please launch via <code>python -m src.cli serve</code> to load data.json over HTTP.</p>
        </div>
      `;
    }
  }

  function updateHeaderStats(meta) {
    if (!meta) return;
    if (statSignalRatio) statSignalRatio.textContent = `${meta.signal_ratio}%`;
    if (statWorthyCount) statWorthyCount.textContent = meta.total_worthy;
    if (statNoiseCount) statNoiseCount.textContent = meta.quarantined_noise;
    if (worthyPillCount) worthyPillCount.textContent = meta.total_worthy;
    if (quarantinePillCount) quarantinePillCount.textContent = meta.quarantined_noise;
    if (lastSyncTime) lastSyncTime.textContent = `Synchronized: ${meta.last_synced_at || 'Just now'}`;
  }

  function buildSubredditPills(posts) {
    const subCounts = {};
    posts.forEach(p => {
      const sub = p.subreddit || 'r/Other';
      subCounts[sub] = (subCounts[sub] || 0) + 1;
    });

    let html = `<button class="filter-pill active" data-sub="all">All Sources (${posts.length})</button>`;
    for (const [sub, count] of Object.entries(subCounts)) {
      html += `<button class="filter-pill" data-sub="${sub}">${sub} (${count})</button>`;
    }
    subFiltersContainer.innerHTML = html;

    subFiltersContainer.querySelectorAll('.filter-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        subFiltersContainer.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeSubreddit = btn.dataset.sub;
        render();
      });
    });
  }

  function render() {
    if (!rawData) return;

    let items = currentView === 'worthy' 
      ? (rawData.posts || []) 
      : (rawData.quarantine_sample || []);

    // Filter by Threshold (for worthy view)
    if (currentView === 'worthy') {
      items = items.filter(item => (item.confidence_score || 0) >= currentThreshold);
    }

    // Filter by Subreddit
    if (activeSubreddit !== 'all') {
      items = items.filter(item => item.subreddit === activeSubreddit);
    }

    // Filter by Search Query
    if (searchQuery) {
      items = items.filter(item => {
        const titleMatch = (item.title || '').toLowerCase().includes(searchQuery);
        const subMatch = (item.subreddit || '').toLowerCase().includes(searchQuery);
        const synthMatch = (item.synthesis || []).join(' ').toLowerCase().includes(searchQuery);
        const repoMatch = (item.github_repos || []).some(r => r.toLowerCase().includes(searchQuery));
        return titleMatch || subMatch || synthMatch || repoMatch;
      });
    }

    if (items.length === 0) {
      postsGrid.innerHTML = '';
      emptyState.classList.remove('hidden');
      return;
    }

    emptyState.classList.add('hidden');
    postsGrid.innerHTML = items.map(renderCard).join('');

    // Attach copy repo buttons
    postsGrid.querySelectorAll('.btn-copy-repo').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const repo = btn.dataset.repo;
        navigator.clipboard.writeText(`git clone ${repo}`);
        showToast(`Copied: git clone ${repo}`);
      });
    });
  }

  function renderCard(item) {
    const isWorthy = item.is_worthy !== false;
    const score = item.confidence_score || 0;
    const scoreClass = isWorthy ? 'score-worthy' : 'score-quarantine';
    const scoreBadgeText = isWorthy ? `🛡️ ${score}% Worthy` : `⚠️ ${score}% Filtered`;
    const repos = item.github_repos || [];
    const dateStr = (item.published_at || '').substring(0, 10) || 'Recent';

    // Synthesis bullets
    let synthesisHtml = '';
    if (item.synthesis && item.synthesis.length) {
      synthesisHtml = `
        <div class="synthesis-box">
          ${item.synthesis.map(line => `<div class="synthesis-line">${formatMarkdown(line)}</div>`).join('')}
        </div>
      `;
    }

    // Repositories
    let reposHtml = '';
    if (repos.length) {
      reposHtml = repos.map(r => `
        <div class="repo-box">
          <a href="${r}" target="_blank" class="repo-link">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
            ${r.replace('https://github.com/', '')}
          </a>
          <button class="btn-copy-repo" data-repo="${r}" title="Copy git clone command">Copy Clone</button>
        </div>
      `).join('');
    }

    // Factor items
    let factorsHtml = '';
    if (item.factors && item.factors.length) {
      factorsHtml = `
        <details class="factors-drawer">
          <summary class="factors-summary">Intelligence Scoring Factors (${item.factors.length})</summary>
          <div class="factors-list">
            ${item.factors.map(f => {
              const isPos = f.delta && f.delta.startsWith('+');
              const deltaClass = isPos ? 'factor-delta-pos' : 'factor-delta-neg';
              return `
                <div class="factor-item">
                  <span>${escapeHtml(f.name)}: <small>${escapeHtml(f.detail || '')}</small></span>
                  <span class="${deltaClass}">${escapeHtml(f.delta)}</span>
                </div>
              `;
            }).join('')}
          </div>
        </details>
      `;
    }

    return `
      <article class="post-card">
        <div class="card-top">
          <span class="card-sub-badge">${escapeHtml(item.subreddit || 'r/General')}</span>
          <span class="confidence-score-badge ${scoreClass}">${scoreBadgeText}</span>
        </div>

        <div>
          <a href="${escapeHtml(item.url || '#')}" target="_blank" class="card-title">
            ${escapeHtml(item.title || 'Untitled Post')}
          </a>
          <div class="card-meta">
            <span>By ${escapeHtml(item.author || 'unknown')}</span>
            <span>•</span>
            <span>${escapeHtml(dateStr)}</span>
            <span>•</span>
            <span>${escapeHtml(item.category || 'Engineering')}</span>
          </div>
        </div>

        ${synthesisHtml}
        ${reposHtml}
        ${factorsHtml}
      </article>
    `;
  }

  function formatMarkdown(str) {
    if (!str) return '';
    return str
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`(.*?)`/g, '<code>$1</code>');
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.remove('hidden');
    setTimeout(() => {
      toast.classList.add('hidden');
    }, 2500);
  }

  // Run on DOM loaded
  document.addEventListener('DOMContentLoaded', init);
})();
