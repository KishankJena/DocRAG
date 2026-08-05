// frontend/js/auth.js
import { registerApi, loginApi, toast } from './api.js';

let isRegisterMode = false;

export function getAuthToken() {
  return localStorage.getItem('token');
}

export function getCurrentUser() {
  return localStorage.getItem('username');
}

export function updateAuthUI() {
  const btn = document.getElementById('user-display-btn');
  const token = getAuthToken();
  const user = getCurrentUser();

  if (token && user) {
    btn.textContent = `👤 ${user} (Logout)`;
    btn.onclick = logout;
  } else {
    btn.textContent = 'Login';
    btn.onclick = openAuthModal;
  }
}

export function openAuthModal() {
  document.getElementById('auth-modal').style.display = 'flex';
}

export function closeAuthModal() {
  document.getElementById('auth-modal').style.display = 'none';
}

export function toggleAuthMode() {
  isRegisterMode = !isRegisterMode;
  document.getElementById('modal-title').textContent = isRegisterMode ? 'Create Account' : 'Sign In';
  document.getElementById('modal-submit-btn').textContent = isRegisterMode ? 'Register' : 'Log In';
  document.getElementById('modal-toggle').innerHTML = isRegisterMode 
    ? 'Already have an account? <span>Log In</span>' 
    : 'Need an account? <span>Register</span>';
}

export async function handleAuthSubmit(onSuccess) {
  const username = document.getElementById('auth-username').value.trim();
  const password = document.getElementById('auth-password').value.trim();

  if (!username || !password) {
    toast('error', 'Please enter username and password');
    return;
  }

  if (isRegisterMode) {
    const { ok, data } = await registerApi(username, password);
    if (ok) {
      toast('success', 'Account created! Logging in...');
      isRegisterMode = false;
      toggleAuthMode();
    } else {
      toast('error', data.detail || 'Registration failed');
    }
  } else {
    const { ok, data } = await loginApi(username, password);
    if (ok) {
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('username', username);
      updateAuthUI();
      closeAuthModal();
      toast('success', `Welcome back, ${username}!`);
      if (onSuccess) onSuccess();
    } else {
      toast('error', data.detail || 'Login failed');
    }
  }
}

export function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  updateAuthUI();
  toast('info', 'Logged out');
  location.reload();
}