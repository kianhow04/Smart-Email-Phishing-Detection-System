// static/js/admin_chart.js

document.addEventListener('DOMContentLoaded', function () {
  const canvas = document.getElementById('adminDonut');
  if (!canvas) return;

  const phishingPct = parseInt(canvas.getAttribute('data-phishing'), 10) || 0;
  const total = parseInt(canvas.getAttribute('data-total'), 10) || 0;
  const ctx = canvas.getContext('2d');

  const cx = canvas.width / 2;
  const cy = canvas.height / 2;
  const radius = 72;
  const strokeWidth = 10;
  const startAngle = -Math.PI / 2;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Background grey ring
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
  ctx.strokeStyle = '#E5E7EB';
  ctx.lineWidth = strokeWidth;
  ctx.stroke();

  // Only draw phishing arc if there is data
  if (total > 0 && phishingPct > 0) {
    const endAngle = startAngle + (phishingPct / 100) * 2 * Math.PI;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, endAngle);
    ctx.strokeStyle = '#E53935';
    ctx.lineWidth = strokeWidth;
    ctx.lineCap = 'round';
    ctx.stroke();
  }
});