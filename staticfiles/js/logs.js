// static/js/logs.js

document.addEventListener('DOMContentLoaded', function () {
  initSearch();
  initDelete();
  initFilter();
});

// ── Search filter ─────────────────────────────────────
function initSearch() {
  const searchInput = document.getElementById('search-input');
  if (!searchInput) return;

  searchInput.addEventListener('input', function () {
    applyFilters();
  });
}

// ── Filter pills ──────────────────────────────────────
function initFilter() {
  const filterBtn = document.getElementById('filter-btn');
  const filterPills = document.getElementById('filter-pills');
  if (!filterBtn || !filterPills) return;

  filterBtn.addEventListener('click', function () {
    const isVisible = filterPills.style.display !== 'none';
    filterPills.style.display = isVisible ? 'none' : 'flex';
  });

  const pills = document.querySelectorAll('.pill');
  pills.forEach(function (pill) {
    pill.addEventListener('click', function () {
      pills.forEach(function (p) { p.classList.remove('active'); });
      pill.classList.add('active');
      applyFilters();
    });
  });
}

// ── Apply both search + filter together ───────────────
function applyFilters() {
  const query = (document.getElementById('search-input').value || '')
                  .toLowerCase().trim();
  const activePill = document.querySelector('.pill.active');
  const labelFilter = activePill ? activePill.getAttribute('data-filter') : 'all';

  const rows = document.querySelectorAll('#logs-tbody .log-row');
  rows.forEach(function (row) {
    const text = row.textContent.toLowerCase();
    const label = row.getAttribute('data-label');

    const matchesSearch = query === '' || text.includes(query);
    const matchesFilter = labelFilter === 'all' || label === labelFilter;

    row.style.display = (matchesSearch && matchesFilter) ? '' : 'none';
  });
}

// ── Delete log entry ──────────────────────────────────
function initDelete() {
  document.getElementById('logs-tbody').addEventListener('click', function (e) {
    const btn = e.target.closest('.delete-btn');
    if (!btn) return;

    const logId = btn.getAttribute('data-id');
    const row = btn.closest('.log-row');

    if (!confirm('Delete this log entry? This cannot be undone.')) return;

    // Get CSRF token from cookie
    const csrfToken = getCookie('csrftoken');

    fetch(`/admin-portal/logs/delete/${logId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/json',
      },
    })
    .then(function (response) {
      if (response.ok) {
        // Fade out and remove row
        row.style.transition = 'opacity 0.3s';
        row.style.opacity = '0';
        setTimeout(function () { row.remove(); }, 300);
      } else {
        alert('Failed to delete log. Please try again.');
      }
    })
    .catch(function () {
      alert('Network error. Please try again.');
    });
  });
}

// ── CSRF cookie helper ────────────────────────────────
function getCookie(name) {
  const value = '; ' + document.cookie;
  const parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}