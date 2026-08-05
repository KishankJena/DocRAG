// frontend/js/api.js
const API_BASE = '/api/v1';

export function getAuthHeaders(contentType = 'application/json') {
  const token = localStorage.getItem('token');
  const headers = {};
  if (contentType) headers['Content-Type'] = contentType;
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return await res.json();
}

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/documents`, { headers: getAuthHeaders() });
  if (res.status === 401) throw new Error('UNAUTHORIZED');
  return await res.json();
}

export async function deleteDocumentApi(docId) {
  const res = await fetch(`${API_BASE}/documents/${docId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  return { ok: res.ok, status: res.status, data: await res.json() };
}

export async function uploadPdfApi(formData) {
  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    headers: getAuthHeaders(null), // Browser auto-sets multipart boundary
    body: formData
  });
  return { ok: res.ok, data: await res.json() };
}

export async function sendQuestionApi(payload) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: getAuthHeaders('application/json'),
    body: JSON.stringify(payload)
  });
  return { ok: res.ok, data: await res.json() };
}

export async function registerApi(username, password) {
  const res = await fetch(
    `${API_BASE}/auth/register?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
    { method: 'POST' }
  );
  return { ok: res.ok, data: await res.json() };
}

export async function loginApi(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData
  });
  return { ok: res.ok, data: await res.json() };
}

export function toast(type, msg) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${msg}</span>`;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}