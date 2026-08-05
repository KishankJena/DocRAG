// frontend/js/chat.js
import { sendQuestionApi } from './api.js';
import { getAuthToken, openAuthModal } from './auth.js';
import { getSelectedDocId } from './docManager.js';

export function setupInput() {
  const input = document.getElementById('question-input');
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendQuestion();
    }
  });
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  });

  document.getElementById('send-btn').addEventListener('click', sendQuestion);
}

async function sendQuestion() {
  if (!getAuthToken()) { openAuthModal(); return; }

  const input = document.getElementById('question-input');
  const question = input.value.trim();
  if (!question) return;

  const topK = parseInt(document.getElementById('top-k-select').value);
  const docId = getSelectedDocId();

  const welcome = document.getElementById('welcome');
  if (welcome) welcome.style.display = 'none';

  appendMessage('user', question);
  input.value = '';
  input.style.height = 'auto';

  const thinkingId = appendThinking();
  document.getElementById('send-btn').disabled = true;

  const { ok, data } = await sendQuestionApi({
    question,
    document_id: docId,
    top_k: topK
  });

  removeThinking(thinkingId);

  if (ok) {
    appendAssistantMessage(data);
  } else {
    appendMessage('assistant', `Error: ${data.detail || 'Something went wrong'}`);
  }

  document.getElementById('send-btn').disabled = false;
}

function appendMessage(role, content) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.innerHTML = `<div class="bubble">${escapeHtml(content)}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function appendAssistantMessage(data) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'message assistant';

  const sourceCards = data.source_chunks.map((chunk, i) => {
    const scorePercent = Math.round(chunk.similarity_score * 100);
    const cardId = `src-${Date.now()}-${i}`;
    return `
      <div class="source-card">
        <div class="source-meta">
          <span class="source-tag">📄 ${chunk.filename}</span>
          <span class="source-tag">Page ${chunk.page_number || '?'}</span>
          <span class="source-tag" style="color:var(--green)">▲ ${scorePercent}% match</span>
        </div>
        <div class="score-bar"><div class="score-fill" style="width:${scorePercent}%"></div></div>
        <div class="source-text" id="${cardId}">${escapeHtml(chunk.content)}</div>
        <button class="expand-btn" data-card="${cardId}">Show more</button>
      </div>
    `;
  }).join('');

  div.innerHTML = `
    <div class="bubble">${escapeHtml(data.answer)}</div>
    ${data.source_chunks.length > 0 ? `
      <div class="sources">
        <div class="sources-header">
          📎 ${data.source_chunks.length} source${data.source_chunks.length > 1 ? 's' : ''} retrieved
        </div>
        ${sourceCards}
      </div>
    ` : ''}
    <div class="msg-stats">
      <span>⏱ ${data.response_time_seconds}s</span>
      <span>🤖 ${data.model_used}</span>
      <span>🔍 ${data.total_chunks_searched} chunks searched</span>
    </div>
  `;

  // Attach expansion handlers
  div.querySelectorAll('.expand-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const card = document.getElementById(btn.dataset.card);
      card.classList.toggle('expanded');
      btn.textContent = card.classList.contains('expanded') ? 'Show less' : 'Show more';
    });
  });

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function appendThinking() {
  const container = document.getElementById('chat-messages');
  const id = `thinking-${Date.now()}`;
  const div = document.createElement('div');
  div.className = 'message assistant';
  div.id = id;
  div.innerHTML = `<div class="thinking"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeThinking(id) {
  document.getElementById(id)?.remove();
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}