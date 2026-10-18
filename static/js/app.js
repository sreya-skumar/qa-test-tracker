/**
 * QATracker Full-Stack Client Application
 * Communicates with Python Flask REST API and SQLite Database
 */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // State cache
  let allTestCases = [];
  let allDefects = [];

  // DOM Elements
  const apiStatusEl = document.getElementById('api-status');
  const apiStatusText = document.getElementById('api-status-text');
  const themeToggleBtn = document.getElementById('theme-toggle');

  // KPI elements
  const kpiTotal = document.getElementById('kpi-total');
  const kpiPassRate = document.getElementById('kpi-pass-rate');
  const kpiPassed = document.getElementById('kpi-passed');
  const kpiDefects = document.getElementById('kpi-defects');
  const kpiCritical = document.getElementById('kpi-critical');
  const kpiAutoRate = document.getElementById('kpi-auto-rate');
  const tabCountTests = document.getElementById('tab-count-tests');
  const tabCountDefects = document.getElementById('tab-count-defects');

  // View containers
  const testCardsContainer = document.getElementById('test-cards-container');
  const defectsContainer = document.getElementById('defects-container');
  const viewTabs = document.querySelectorAll('.view-tab');
  const viewSections = document.querySelectorAll('.view-section');

  // Search & Filters
  const testSearchInput = document.getElementById('test-search-input');
  const filterStatusSelect = document.getElementById('filter-status-select');
  const filterModuleSelect = document.getElementById('filter-module-select');

  // Modals & Forms
  const modalNewTest = document.getElementById('modal-new-test');
  const modalNewDefect = document.getElementById('modal-new-defect');
  const formNewTest = document.getElementById('form-new-test');
  const formNewDefect = document.getElementById('form-new-defect');
  const openNewTestBtn = document.getElementById('open-new-test-btn');
  const openNewDefectBtn = document.getElementById('open-new-defect-btn');
  const linkedTestSelect = document.getElementById('new-defect-test-id');

  // API Explorer elements
  const apiMethodSelect = document.getElementById('api-method-select');
  const apiEndpointInput = document.getElementById('api-endpoint-input');
  const apiSendBtn = document.getElementById('api-send-btn');
  const apiResponseCode = document.getElementById('api-response-code');
  const responseStatusBadge = document.getElementById('response-status-badge');
  const presetBtns = document.querySelectorAll('.preset-btn');

  // Auth elements
  const btnLoginNav = document.getElementById('btn-login-nav');
  const userProfileBadge = document.getElementById('user-profile-badge');
  const userAvatarInitials = document.getElementById('user-avatar-initials');
  const userDisplayName = document.getElementById('user-display-name');
  const userDisplayRole = document.getElementById('user-display-role');
  const btnLogout = document.getElementById('btn-logout');

  // -------------------------------------------------------------------------
  // 1. Theme Management (Dark/Light with localStorage)
  // -------------------------------------------------------------------------
  const savedTheme = localStorage.getItem('qa_tracker_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('qa_tracker_theme', next);
    });
  }

  // -------------------------------------------------------------------------
  // 2. Navigation Tabs
  // -------------------------------------------------------------------------
  viewTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const targetView = tab.getAttribute('data-view');
      viewTabs.forEach((t) => t.classList.remove('active'));
      viewSections.forEach((s) => s.classList.remove('active'));

      tab.classList.add('active');
      const section = document.getElementById(`view-${targetView}`);
      if (section) section.classList.add('active');
    });
  });

  // -------------------------------------------------------------------------
  // 3. API Communication & Data Fetching
  // -------------------------------------------------------------------------
  async function checkHealth() {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        apiStatusEl.className = 'api-status-badge online';
        apiStatusText.textContent = `Backend Online • ${data.framework}`;
      } else {
        throw new Error('Health check failed');
      }
    } catch (err) {
      apiStatusEl.className = 'api-status-badge';
      apiStatusText.textContent = 'Backend Offline';
    }
  }

  async function fetchStats() {
    try {
      const res = await fetch('/api/stats');
      if (!res.ok) throw new Error('Failed to load stats');
      const data = await res.json();

      kpiTotal.textContent = data.total_test_cases;
      kpiPassRate.textContent = `${data.pass_rate_percent}%`;
      kpiPassed.textContent = data.passed;
      kpiDefects.textContent = data.open_defects;
      kpiCritical.textContent = data.critical_defects;
      kpiAutoRate.textContent = `${data.automation_rate_percent}%`;

      tabCountTests.textContent = data.total_test_cases;
      tabCountDefects.textContent = data.total_defects;
    } catch (err) {
      console.error('Stats error:', err);
    }
  }

  async function fetchTestCases() {
    try {
      const res = await fetch('/api/testcases');
      if (!res.ok) throw new Error('Failed to load test cases');
      const data = await res.json();
      allTestCases = data.test_cases || [];

      renderTestCases();
      populateLinkedTestDropdown();
    } catch (err) {
      testCardsContainer.innerHTML = `<div class="error-msg">Failed to load test cases from backend: ${err.message}</div>`;
    }
  }

  async function fetchDefects() {
    try {
      const res = await fetch('/api/defects');
      if (!res.ok) throw new Error('Failed to load defects');
      const data = await res.json();
      allDefects = data.defects || [];

      renderDefects();
    } catch (err) {
      defectsContainer.innerHTML = `<div class="error-msg">Failed to load defects: ${err.message}</div>`;
    }
  }

  // -------------------------------------------------------------------------
  // 4. Rendering Functions
  // -------------------------------------------------------------------------
  function renderTestCases() {
    const searchTerm = (testSearchInput.value || '').toLowerCase().trim();
    const statusFilter = filterStatusSelect.value;
    const moduleFilter = filterModuleSelect.value;

    const filtered = allTestCases.filter((t) => {
      const matchSearch =
        t.title.toLowerCase().includes(searchTerm) ||
        (t.description || '').toLowerCase().includes(searchTerm);
      const matchStatus = !statusFilter || t.status === statusFilter;
      const matchModule = !moduleFilter || t.module === moduleFilter;
      return matchSearch && matchStatus && matchModule;
    });

    if (filtered.length === 0) {
      testCardsContainer.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-dim);">
          No test cases match your criteria. Click "+ New Test Case" to add one!
        </div>
      `;
      return;
    }

    testCardsContainer.innerHTML = filtered.map((test) => `
      <article class="test-card" data-id="${test.id}">
        <div class="test-card-top">
          <span class="module-badge">${escapeHtml(test.module)}</span>
          <span class="priority-badge priority-${test.priority}">${test.priority}</span>
        </div>
        <h4 class="test-card-title">${escapeHtml(test.title)}</h4>
        <p class="test-card-desc">${escapeHtml(test.description || 'No description provided.')}</p>
        <div class="test-card-meta">
          <span>🛠️ ${escapeHtml(test.automated_by)}</span>
          <span class="status-chip status-${test.status}">${test.status}</span>
        </div>
        <div class="test-card-actions">
          <button class="action-btn pass" title="Mark Passed" data-action="status" data-status="Passed">✔ Pass</button>
          <button class="action-btn fail" title="Mark Failed" data-action="status" data-status="Failed">✖ Fail</button>
          <button class="action-btn block" title="Mark Blocked" data-action="status" data-status="Blocked">🚫 Block</button>
          <button class="action-btn del" title="Delete Test Case" data-action="delete">🗑</button>
        </div>
      </article>
    `).join('');

    // Attach card action listeners
    testCardsContainer.querySelectorAll('.test-card').forEach((card) => {
      const id = card.getAttribute('data-id');

      card.querySelectorAll('[data-action="status"]').forEach((btn) => {
        btn.addEventListener('click', () => {
          const newStatus = btn.getAttribute('data-status');
          updateTestStatus(id, newStatus);
        });
      });

      card.querySelector('[data-action="delete"]').addEventListener('click', () => {
        if (confirm(`Are you sure you want to delete test case #${id}?`)) {
          deleteTestCase(id);
        }
      });
    });
  }

  function renderDefects() {
    if (allDefects.length === 0) {
      defectsContainer.innerHTML = `
        <div style="text-align: center; padding: 3rem; color: var(--text-dim);">
          No defects logged. Click "+ Log Defect" to record an issue!
        </div>
      `;
      return;
    }

    defectsContainer.innerHTML = allDefects.map((d) => `
      <div class="defect-card" data-id="${d.id}">
        <div class="defect-main">
          <div class="defect-header">
            <span class="priority-badge priority-${d.severity}">${d.severity}</span>
            <span style="font-size: 0.8rem; color: var(--text-dim);">Defect #${d.id} • ${escapeHtml(d.test_case_module || 'General')}</span>
          </div>
          <h4 class="defect-title">${escapeHtml(d.title)}</h4>
          ${d.test_case_title ? `<div style="font-size: 0.85rem; color: var(--color-primary); margin-bottom: 0.5rem;">Linked: ${escapeHtml(d.test_case_title)}</div>` : ''}
          ${d.steps_to_reproduce ? `<div class="defect-steps"><strong>Steps to Reproduce:</strong>\n${escapeHtml(d.steps_to_reproduce)}</div>` : ''}
        </div>
        <div class="defect-actions">
          <select class="defect-status-select" data-id="${d.id}">
            <option value="Open" ${d.status === 'Open' ? 'selected' : ''}>Open</option>
            <option value="In Progress" ${d.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
            <option value="Resolved" ${d.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
            <option value="Closed" ${d.status === 'Closed' ? 'selected' : ''}>Closed</option>
          </select>
          <button class="action-btn del" data-delete-defect="${d.id}" title="Delete Defect">Delete</button>
        </div>
      </div>
    `).join('');

    // Status change listeners
    defectsContainer.querySelectorAll('.defect-status-select').forEach((sel) => {
      sel.addEventListener('change', () => {
        updateDefectStatus(sel.getAttribute('data-id'), sel.value);
      });
    });

    // Delete listeners
    defectsContainer.querySelectorAll('[data-delete-defect]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = btn.getAttribute('data-delete-defect');
        if (confirm(`Delete defect #${id}?`)) {
          deleteDefect(id);
        }
      });
    });
  }

  function populateLinkedTestDropdown() {
    if (!linkedTestSelect) return;
    const options = [
      '<option value="">-- Standalone (No Test Case) --</option>',
      ...allTestCases.map((t) => `<option value="${t.id}">#${t.id}: ${escapeHtml(t.title)}</option>`)
    ];
    linkedTestSelect.innerHTML = options.join('');
  }

  // -------------------------------------------------------------------------
  // 5. API Mutation Operations
  // -------------------------------------------------------------------------
  async function updateTestStatus(id, status) {
    try {
      const simulatedLatency = Math.floor(40 + Math.random() * 280);
      const res = await fetch(`/api/testcases/${id}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, execution_time_ms: simulatedLatency })
      });

      if (!res.ok) throw new Error('Failed to update status');

      showToast(`Test #${id} marked as ${status} (${simulatedLatency}ms)`, 'success');
      await Promise.all([fetchTestCases(), fetchStats()]);
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  async function deleteTestCase(id) {
    try {
      const res = await fetch(`/api/testcases/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete test case');

      showToast(`Test case #${id} deleted`, 'success');
      await Promise.all([fetchTestCases(), fetchStats()]);
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  async function updateDefectStatus(id, status) {
    try {
      const res = await fetch(`/api/defects/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      if (!res.ok) throw new Error('Failed to update defect');

      showToast(`Defect #${id} updated to ${status}`, 'success');
      await Promise.all([fetchDefects(), fetchStats()]);
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  async function deleteDefect(id) {
    try {
      const res = await fetch(`/api/defects/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete defect');

      showToast(`Defect #${id} deleted`, 'success');
      await Promise.all([fetchDefects(), fetchStats()]);
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // -------------------------------------------------------------------------
  // 6. Form Submissions
  // -------------------------------------------------------------------------
  if (formNewTest) {
    formNewTest.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        title: document.getElementById('new-test-title').value.trim(),
        module: document.getElementById('new-test-module').value.trim(),
        priority: document.getElementById('new-test-priority').value,
        status: document.getElementById('new-test-status').value,
        automated_by: document.getElementById('new-test-tool').value,
        description: document.getElementById('new-test-desc').value.trim()
      };

      try {
        const res = await fetch('/api/testcases', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.error || 'Failed to create test case');
        }

        showToast('New test case saved to SQLite database!', 'success');
        formNewTest.reset();
        closeModal(modalNewTest);
        await Promise.all([fetchTestCases(), fetchStats()]);
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  if (formNewDefect) {
    formNewDefect.addEventListener('submit', async (e) => {
      e.preventDefault();
      const testIdVal = document.getElementById('new-defect-test-id').value;
      const payload = {
        title: document.getElementById('new-defect-title').value.trim(),
        severity: document.getElementById('new-defect-severity').value,
        test_case_id: testIdVal ? parseInt(testIdVal, 10) : null,
        steps_to_reproduce: document.getElementById('new-defect-steps').value.trim()
      };

      try {
        const res = await fetch('/api/defects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.error || 'Failed to log defect');
        }

        showToast('Defect successfully logged!', 'success');
        formNewDefect.reset();
        closeModal(modalNewDefect);
        await Promise.all([fetchDefects(), fetchStats()]);
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // -------------------------------------------------------------------------
  // 7. Modals Open/Close
  // -------------------------------------------------------------------------
  if (openNewTestBtn) openNewTestBtn.addEventListener('click', () => openModal(modalNewTest));
  if (openNewDefectBtn) openNewDefectBtn.addEventListener('click', () => openModal(modalNewDefect));

  document.querySelectorAll('[data-close]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const modalId = btn.getAttribute('data-close');
      const target = document.getElementById(modalId);
      if (target) closeModal(target);
    });
  });

  function openModal(modal) {
    if (!modal) return;
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
  }

  function closeModal(modal) {
    if (!modal) return;
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
  }

  // -------------------------------------------------------------------------
  // 8. Interactive API Explorer Console
  // -------------------------------------------------------------------------
  async function executeApiRequest() {
    const method = apiMethodSelect.value;
    const endpoint = (apiEndpointInput.value || '').trim();

    if (!endpoint.startsWith('/api')) {
      showToast('Endpoint must start with /api', 'error');
      return;
    }

    responseStatusBadge.textContent = 'Sending...';
    responseStatusBadge.style.color = 'var(--color-warning)';
    apiResponseCode.textContent = '// Waiting for response...';

    const startTime = performance.now();

    try {
      const res = await fetch(endpoint, { method });
      const elapsed = Math.round(performance.now() - startTime);
      const json = await res.json();

      responseStatusBadge.textContent = `HTTP ${res.status} ${res.statusText} (${elapsed}ms)`;
      responseStatusBadge.style.color = res.ok ? 'var(--color-success)' : 'var(--color-danger)';
      apiResponseCode.textContent = JSON.stringify(json, null, 2);
    } catch (err) {
      responseStatusBadge.textContent = 'Network Error';
      responseStatusBadge.style.color = 'var(--color-danger)';
      apiResponseCode.textContent = `// Error: ${err.message}`;
    }
  }

  if (apiSendBtn) apiSendBtn.addEventListener('click', executeApiRequest);

  presetBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      apiMethodSelect.value = btn.getAttribute('data-method') || 'GET';
      apiEndpointInput.value = btn.getAttribute('data-endpoint') || '/api/stats';
      executeApiRequest();
    });
  });

  // Filter input listeners
  if (testSearchInput) testSearchInput.addEventListener('input', renderTestCases);
  if (filterStatusSelect) filterStatusSelect.addEventListener('change', renderTestCases);
  if (filterModuleSelect) filterModuleSelect.addEventListener('change', renderTestCases);

  // -------------------------------------------------------------------------
  // 9. Toast Notification Helper
  // -------------------------------------------------------------------------
  function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 3200);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // -------------------------------------------------------------------------
  // 10. User Authentication State
  // -------------------------------------------------------------------------
  async function checkAuth() {
    try {
      const res = await fetch('/api/auth/me');
      const data = await res.json();
      if (data.authenticated && data.user) {
        if (btnLoginNav) btnLoginNav.style.display = 'none';
        if (userProfileBadge) {
          userProfileBadge.style.display = 'flex';
          const name = data.user.username || 'User';
          if (userDisplayName) userDisplayName.textContent = name;
          if (userDisplayRole) userDisplayRole.textContent = data.user.role || 'QA Member';
          if (userAvatarInitials) userAvatarInitials.textContent = name.charAt(0).toUpperCase();
        }
      } else {
        if (btnLoginNav) btnLoginNav.style.display = 'inline-flex';
        if (userProfileBadge) userProfileBadge.style.display = 'none';
      }
    } catch (err) {
      console.warn('Auth check failed:', err);
    }
  }

  if (btnLogout) {
    btnLogout.addEventListener('click', async () => {
      try {
        await fetch('/api/auth/logout', { method: 'POST' });
        showToast('Signed out successfully. Redirecting...', 'success');
        setTimeout(() => {
          window.location.href = '/login?logged_out=1';
        }, 300);
      } catch (err) {
        showToast('Error signing out', 'error');
      }
    });
  }

  // -------------------------------------------------------------------------
  // 11. Initial Application Boot
  // -------------------------------------------------------------------------
  checkHealth();
  checkAuth();
  fetchStats();
  fetchTestCases();
  fetchDefects();
});
