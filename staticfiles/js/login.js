// static/js/login.js

document.addEventListener('DOMContentLoaded', function () {
  const passwordInput = document.getElementById('password');
  const toggleBtn = document.getElementById('toggle-eye');
  const eyeOpen = document.getElementById('eye-open');
  const eyeClosed = document.getElementById('eye-closed');

  if (!toggleBtn) return;

  toggleBtn.addEventListener('click', function () {
    const isPassword = passwordInput.type === 'password';

    // Toggle input type
    passwordInput.type = isPassword ? 'text' : 'password';

    // Toggle icons
    eyeOpen.style.display = isPassword ? 'none' : 'block';
    eyeClosed.style.display = isPassword ? 'block' : 'none';
  });
});