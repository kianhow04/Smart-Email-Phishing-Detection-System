// static/js/upload.js
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('eml-file-input');
const filenameDisplay = document.getElementById('filename-display');
const uploadBtn = document.getElementById('upload-btn');
const uploadForm = document.getElementById('upload-form');

// ── Click drop zone to open file picker ─────────────
dropZone.addEventListener('click', () => fileInput.click());

// ── Drag and drop events ─────────────────────────────
dropZone.addEventListener('dragenter', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

// ── File input change ────────────────────────────────
fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) handleFile(fileInput.files[0]);
});

// ── Handle selected file ─────────────────────────────
function handleFile(file) {
  // Client-side extension check
  if (!file.name.toLowerCase().endsWith('.eml')) {
    filenameDisplay.textContent = '✗ Only .eml files are accepted.';
    filenameDisplay.style.color = '#E53935';
    uploadBtn.disabled = true;
    return;
  }

  // Show filename in drop zone
  filenameDisplay.textContent = '✓ ' + file.name;
  filenameDisplay.style.color = '#6C3FE8';
  dropZone.classList.add('has-file');

  // Transfer file to the real input if dropped (not selected via picker)
  if (file !== fileInput.files[0]) {
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;
  }

  uploadBtn.disabled = false;
}

// ── Form submit — show loading state ─────────────────
uploadForm.addEventListener('submit', (e) => {
  // Final safety check
  if (!fileInput.files[0]) {
    e.preventDefault();
    return;
  }

  // Show spinner and disable button
  uploadBtn.style.pointerEvents = 'none';
  uploadBtn.classList.add('loading');
  uploadBtn.innerHTML = '<span class="spinner"></span>Analyzing...';
});