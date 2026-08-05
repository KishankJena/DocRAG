// frontend/js/docManager.js
import { fetchDocuments, deleteDocumentApi, uploadPdfApi, toast } from './api.js';
import { getAuthToken, openAuthModal, logout } from './auth.js';

let documents = [];
let selectedDocId = null;
let searchScope = 'all';

export function getSelectedDocId() {
  return searchScope === 'selected' ? selectedDocId : null;
}

export async function loadDocuments() {
  if (!getAuthToken()) return;
  try {
    const data = await fetchDocuments();
    documents = data.documents || [];
    renderDocumentList();
  } catch (e) {
    if (e.message === 'UNAUTHORIZED') logout();
  }
}

function renderDocumentList() {
  const list = document.getElementById('doc-list');
  if (documents.length === 0) {
    list.innerHTML = '<div class="empty-docs">No documents yet.<br>Upload a PDF to get started.</div>';
    return;
  }

  list.innerHTML = documents.map(doc => `
    <div class="doc-item ${doc.document_id === selectedDocId ? 'active' : ''}" data-id="${doc.document_id}">
      <div class="doc-icon">📄</div>
      <div class="doc-info">
        <div class="doc-name" title="${doc.filename}">${doc.filename}</div>
        <div class="doc-meta">${doc.total_chunks} chunks · ${formatDate(doc.uploaded_at)}</div>
      </div>
      <button class="doc-delete" data-delete-id="${doc.document_id}" title="Delete">✕</button>
    </div>
  `).join('');

  // Attach event handlers
  list.querySelectorAll('.doc-item').forEach(el => {
    el.addEventListener('click', () => selectDoc(el.dataset.id));
  });

  list.querySelectorAll('.doc-delete').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      deleteDoc(btn.dataset.deleteId);
    });
  });
}

function selectDoc(docId) {
  selectedDocId = selectedDocId === docId ? null : docId;
  setScope(selectedDocId ? 'selected' : 'all');
  renderDocumentList();
}

async function deleteDoc(docId) {
  if (!confirm('Delete this document and all its embeddings?')) return;
  const { ok, data } = await deleteDocumentApi(docId);
  if (ok) {
    toast('success', `Deleted: ${data.chunks_deleted} chunks removed`);
    if (selectedDocId === docId) { selectedDocId = null; setScope('all'); }
    await loadDocuments();
  } else {
    toast('error', data.detail || 'Delete failed');
  }
}

export function setScope(scope) {
  searchScope = scope;
  document.getElementById('scope-all').className = 'scope-btn' + (scope === 'all' ? ' active' : '');
  document.getElementById('scope-selected').className = 'scope-btn' + (scope === 'selected' ? ' active' : '');
  const hint = document.getElementById('scope-hint');
  if (scope === 'all') {
    hint.textContent = 'Searching across all uploaded documents';
  } else {
    const doc = documents.find(d => d.document_id === selectedDocId);
    hint.textContent = doc ? `Searching: ${doc.filename}` : 'Select a document from the list';
  }
}

export function setupUpload() {
  const zone = document.getElementById('upload-zone');
  const input = document.getElementById('file-input');

  zone.addEventListener('click', () => {
    if (!getAuthToken()) { openAuthModal(); return; }
    input.click();
  });
  
  input.addEventListener('change', (e) => {
    if (e.target.files[0]) uploadFile(e.target.files[0]);
  });

  zone.addEventListener('dragover', (e) => {
    e.preventDefault();
    zone.classList.add('drag-over');
  });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    if (!getAuthToken()) { openAuthModal(); return; }
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.pdf')) uploadFile(file);
    else toast('error', 'Only PDF files are supported');
  });
}

async function uploadFile(file) {
  const progress = document.getElementById('upload-progress');
  const fill = document.getElementById('progress-fill');
  const status = document.getElementById('upload-status');

  progress.style.display = 'block';
  fill.style.width = '30%';
  status.textContent = `Uploading ${file.name}...`;

  const formData = new FormData();
  formData.append('file', file);

  fill.style.width = '60%';
  status.textContent = 'Extracting text & generating embeddings...';

  const { ok, data } = await uploadPdfApi(formData);
  fill.style.width = '100%';

  if (ok) {
    status.textContent = `Done! ${data.total_chunks} chunks created`;
    toast('success', `✓ Uploaded "${data.filename}" · ${data.total_chunks} chunks`);
    await loadDocuments();
    const welcome = document.getElementById('welcome');
    if (welcome) welcome.style.display = 'none';
  } else {
    status.textContent = 'Upload failed.';
    toast('error', data.detail || 'Upload failed');
  }

  setTimeout(() => {
    progress.style.display = 'none';
    fill.style.width = '0%';
    document.getElementById('file-input').value = '';
  }, 2500);
}

function formatDate(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch { return ''; }
}