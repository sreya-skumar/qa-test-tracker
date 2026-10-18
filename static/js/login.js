/**
 * QATracker - Authentication Client Logic
 * Handles Sign In, Account Registration, and Quick Demo Logins.
 */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // Elements
  const tabLogin = document.getElementById('tab-login');
  const tabRegister = document.getElementById('tab-register');
  const formLogin = document.getElementById('form-login');
  const formRegister = document.getElementById('form-register');
  const authAlert = document.getElementById('auth-alert');
  const themeToggleBtn = document.getElementById('theme-toggle');

  // Input Elements
  const loginIdentifier = document.getElementById('login-identifier');
  const loginPassword = document.getElementById('login-password');
  const btnSubmitLogin = document.getElementById('btn-submit-login');
  const btnSubmitRegister = document.getElementById('btn-submit-register');

  // Demo buttons
  const demoBtnSreya = document.getElementById('demo-btn-sreya');
  const demoBtnAlex = document.getElementById('demo-btn-alex');

  // -------------------------------------------------------------------------
  // 1. Theme Persistence
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

  // Check if redirected after sign-out
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('logged_out') === '1') {
    showAlert('You have been signed out successfully.', 'success');
  }

  // -------------------------------------------------------------------------
  // 2. Tab Switching (Sign In / Create Account)
  // -------------------------------------------------------------------------
  tabLogin.addEventListener('click', () => {
    tabLogin.classList.add('active');
    tabRegister.classList.remove('active');
    formLogin.classList.add('active');
    formRegister.classList.remove('active');
    clearAlert();
  });

  tabRegister.addEventListener('click', () => {
    tabRegister.classList.add('active');
    tabLogin.classList.remove('active');
    formRegister.classList.add('active');
    formLogin.classList.remove('active');
    clearAlert();
  });

  // -------------------------------------------------------------------------
  // 3. Password Visibility Toggle
  // -------------------------------------------------------------------------
  document.querySelectorAll('.toggle-password-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const input = btn.previousElementSibling;
      if (!input) return;

      if (input.type === 'password') {
        input.type = 'text';
        btn.innerHTML = `
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
            <line x1="1" y1="1" x2="23" y2="23"></line>
          </svg>
        `;
      } else {
        input.type = 'password';
        btn.innerHTML = `
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
          </svg>
        `;
      }
    });
  });

  // -------------------------------------------------------------------------
  // 4. Login Submission
  // -------------------------------------------------------------------------
  formLogin.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAlert();

    const loginVal = loginIdentifier.value.trim();
    const passwordVal = loginPassword.value;

    if (!loginVal || !passwordVal) {
      showAlert('Please enter both your username/email and password.', 'error');
      return;
    }

    setLoading(btnSubmitLogin, true, 'Signing in...');

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login: loginVal, password: passwordVal })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Login failed. Please check credentials.');
      }

      showAlert(`Welcome back, ${data.user.username}! Redirecting...`, 'success');

      setTimeout(() => {
        window.location.href = '/';
      }, 700);
    } catch (err) {
      showAlert(err.message, 'error');
      setLoading(btnSubmitLogin, false, 'Sign In to Dashboard');
    }
  });

  // -------------------------------------------------------------------------
  // 5. Register Submission
  // -------------------------------------------------------------------------
  formRegister.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAlert();

    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const role = document.getElementById('reg-role').value;
    const password = document.getElementById('reg-password').value;

    if (!username || !email || !password) {
      showAlert('All fields marked * are required.', 'error');
      return;
    }

    setLoading(btnSubmitRegister, true, 'Creating account...');

    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, role, password })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Failed to create account.');
      }

      showAlert('Account created successfully! Redirecting...', 'success');

      setTimeout(() => {
        window.location.href = '/';
      }, 700);
    } catch (err) {
      showAlert(err.message, 'error');
      setLoading(btnSubmitRegister, false, 'Create Account');
    }
  });

  // -------------------------------------------------------------------------
  // 6. Autofill Demo Credentials (User clicks 'Log In' button to enter)
  // -------------------------------------------------------------------------
  if (demoBtnSreya) {
    demoBtnSreya.addEventListener('click', () => {
      loginIdentifier.value = 'sreya';
      loginPassword.value = 'Password123!';
      btnSubmitLogin.focus();
      showAlert('Demo credentials filled for Sreya! Click the "Log In" button below to enter the dashboard.', 'success');
    });
  }

  if (demoBtnAlex) {
    demoBtnAlex.addEventListener('click', () => {
      loginIdentifier.value = 'alex';
      loginPassword.value = 'Password123!';
      btnSubmitLogin.focus();
      showAlert('Demo credentials filled for Alex! Click the "Log In" button below to enter the dashboard.', 'success');
    });
  }

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------
  function showAlert(msg, type) {
    authAlert.textContent = msg;
    authAlert.className = `auth-alert ${type}`;
    authAlert.style.display = 'block';
  }

  function clearAlert() {
    authAlert.textContent = '';
    authAlert.className = 'auth-alert';
    authAlert.style.display = 'none';
  }

  function setLoading(btn, isLoading, text) {
    if (!btn) return;
    btn.disabled = isLoading;
    btn.querySelector('span').textContent = text;
  }
});
