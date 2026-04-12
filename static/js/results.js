// static/js/results.js

document.addEventListener('DOMContentLoaded', function () {
  initTabs();
  initDonutChart();
});

// ── Tab Switching ────────────────────────────────────
function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  tabBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const targetId = btn.getAttribute('data-tab');

      // Update button states
      tabBtns.forEach(function (b) {
        b.classList.remove('active');
      });
      btn.classList.add('active');

      // Show / hide tab content
      tabContents.forEach(function (content) {
        if (content.id === targetId) {
          content.style.display = 'block';
        } else {
          content.style.display = 'none';
        }
      });
    });
  });
}

// ── Donut Chart ──────────────────────────────────────
function initDonutChart() {
  const canvas = document.getElementById('donutChart');
  if (!canvas) return;

  const score = parseInt(canvas.getAttribute('data-score'), 10);
  const label = canvas.getAttribute('data-label');
  const ctx = canvas.getContext('2d');

  const cx = canvas.width / 2;        // center x = 90
  const cy = canvas.height / 2;       // center y = 90
  const radius = 72;                   // ring radius
  const strokeWidth = 10;             // ring thickness
  const startAngle = -Math.PI / 2;    // start at 12 o'clock

  // Colors
  const activeColor = label === 'phishing' ? '#E53935' : '#43A047';
  const trackColor = '#E5E7EB';

  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // ── Draw background track (full grey ring) ──
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
  ctx.strokeStyle = trackColor;
  ctx.lineWidth = strokeWidth;
  ctx.stroke();

  // ── Draw score arc ──────────────────────────
  const endAngle = startAngle + (score / 100) * 2 * Math.PI;

  ctx.beginPath();
  ctx.arc(cx, cy, radius, startAngle, endAngle);
  ctx.strokeStyle = activeColor;
  ctx.lineWidth = strokeWidth;
  ctx.lineCap = 'round';
  ctx.stroke();
}