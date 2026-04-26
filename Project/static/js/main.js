// ── STATE ──
let numQuestions = 5;
let quizData = null;
let answeredCount = 0;
let correctCount = 0;
let sumMode = 'text';        // 'text' or 'file'
let uploadedFile = null;     // actual File object

// ── INIT ──
window.onload = function () {

  // Show first panel
  document.querySelectorAll('.panel').forEach(p => p.classList.add('hidden'));
  const first = document.getElementById('panel-qa');
  if (first) { first.classList.remove('hidden'); first.classList.add('active'); }

  // Nav tab clicks
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.getAttribute('data-tab')));
  });

  // Style options
  document.querySelectorAll('.style-opt').forEach(opt => {
    opt.addEventListener('click', () => {
      document.querySelectorAll('.style-opt').forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
    });
  });

  // Difficulty buttons
  document.querySelectorAll('.diff-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.diff-btn').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
    });
  });

  // Level buttons
  document.querySelectorAll('.level-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.level-btn').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
    });
  });

  // Keyboard shortcuts
  document.getElementById('qa-question')?.addEventListener('keydown', e => { if (e.ctrlKey && e.key === 'Enter') askQuestion(); });
  document.getElementById('qa-context')?.addEventListener('keydown', e => { if (e.key === 'Enter') askQuestion(); });
  document.getElementById('quiz-topic')?.addEventListener('keydown', e => { if (e.key === 'Enter') generateQuiz(); });
  document.getElementById('exp-concept')?.addEventListener('keydown', e => { if (e.key === 'Enter') explainConcept(); });
};

// ── TAB SWITCH ──
function switchTab(tabName) {
  document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => { p.classList.add('hidden'); p.classList.remove('active'); });

  const btn = document.querySelector(`[data-tab="${tabName}"]`);
  if (btn) btn.classList.add('active');

  const panel = document.getElementById(`panel-${tabName}`);
  if (panel) { panel.classList.remove('hidden'); panel.classList.add('active'); }

  // Scroll hero out of view smoothly on mobile
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── NUM STEPPER ──
function changeNum(d) {
  numQuestions = Math.max(3, Math.min(10, numQuestions + d));
  document.getElementById('num-display').textContent = numQuestions;
}

// ── LOADING ──
function showLoading(msg) {
  const el = document.getElementById('loading-msg');
  if (el) el.textContent = msg || 'AI is thinking...';
  document.getElementById('loading').classList.remove('hidden');
}
function hideLoading() {
  document.getElementById('loading').classList.add('hidden');
}

// ── TOAST ──
function showToast(msg, isErr) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (isErr ? ' err' : '');
  clearTimeout(t._tid);
  t._tid = setTimeout(() => { t.classList.remove('show'); }, 3000);
}

// ── COPY ──
function copyResult(id) {
  const el = document.getElementById(id);
  if (!el) return;
  navigator.clipboard.writeText(el.textContent)
    .then(() => showToast('Copied to clipboard! 📋'))
    .catch(() => showToast('Copy failed', true));
}

// ── API CALL ──
function apiCall(endpoint, body) {
  return fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  }).then(res => {
    if (!res.ok) throw new Error('Server error ' + res.status);
    return res.json();
  });
}

// ── SHOW RESULT ──
function showResult(boxId, textId, content) {
  const box = document.getElementById(boxId);
  const txt = document.getElementById(textId);
  if (!box || !txt) return;
  txt.textContent = content;
  box.classList.remove('hidden');
  box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ── ASK QUESTION ──
function askQuestion() {
  const question = document.getElementById('qa-question').value.trim();
  const context  = document.getElementById('qa-context').value.trim();
  if (!question) { showToast('Please enter a question!', true); return; }
  showLoading('Finding the best answer...');
  apiCall('/ask', { question, context })
    .then(data => showResult('qa-result', 'qa-result-text', data.answer))
    .catch(() => showToast('Server error! Make sure Flask is running.', true))
    .finally(hideLoading);
}

// ── SUMMARIZE MODE SWITCH ──
function switchSumMode(mode) {
  sumMode = mode;
  uploadedFile = null;
  document.getElementById('file-tag').classList.add('hidden');

  const textMode = document.getElementById('sum-text-mode');
  const fileMode = document.getElementById('sum-file-mode');
  const textBtn  = document.getElementById('mode-text-btn');
  const fileBtn  = document.getElementById('mode-file-btn');

  if (mode === 'text') {
    textMode.style.display = 'block';
    fileMode.style.display = 'none';
    textBtn.classList.add('active');
    fileBtn.classList.remove('active');
  } else {
    textMode.style.display = 'none';
    fileMode.style.display = 'block';
    fileBtn.classList.add('active');
    textBtn.classList.remove('active');
  }
}

// ── FILE UPLOAD ──
function dragOver(e) {
  e.preventDefault();
  document.getElementById('upload-zone').classList.add('drag-over');
}
function dragLeave() {
  document.getElementById('upload-zone').classList.remove('drag-over');
}
function dropFile(e) {
  e.preventDefault();
  document.getElementById('upload-zone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
}
function handleFile(e) {
  const file = e.target.files[0];
  if (file) setFile(file);
}
function setFile(file) {
  const allowed = ['pdf', 'docx', 'txt'];
  const ext = file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showToast('Only PDF, DOCX, or TXT files!', true); return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showToast('File too large! Max 10MB.', true); return;
  }
  uploadedFile = file;
  const tag = document.getElementById('file-tag');
  tag.innerHTML = '✅ ' + file.name + ' <button onclick="clearFile()" class="clear-file-btn">✕ Clear</button>';
  tag.classList.remove('hidden');
  showToast('File ready! 📄');
}

function clearFile() {
  uploadedFile = null;
  document.getElementById('file-input').value = '';
  const tag = document.getElementById('file-tag');
  tag.classList.add('hidden');
  tag.innerHTML = '';
  showToast('File cleared ✓');
}
// ── SUMMARIZE (text or file) ──
function summarize() {
  const styleEl = document.querySelector('input[name="sum-style"]:checked');
  const style   = styleEl ? styleEl.value : 'concise';

  if (sumMode === 'file') {
    // File upload path
    if (!uploadedFile) { showToast('Please upload a file first!', true); return; }
    showLoading('Reading your file...');
    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('style', style);
    fetch('/summarize-file', { method: 'POST', body: formData })
      .then(res => res.json())
      .then(data => {
        if (data.error) { showToast(data.error, true); return; }
        showResult('sum-result', 'sum-result-text', data.summary);
      })
      .catch(() => showToast('Server error! Make sure Flask is running.', true))
      .finally(hideLoading);
  } else {
    // Text paste path
    const text = document.getElementById('sum-text').value.trim();
    if (!text) { showToast('Please paste some text first!', true); return; }
    showLoading('Summarizing your text...');
    apiCall('/summarize', { text, style })
      .then(data => showResult('sum-result', 'sum-result-text', data.summary))
      .catch(() => showToast('Server error! Make sure Flask is running.', true))
      .finally(hideLoading);
  }
}

function clearResultBox(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.style.transition = 'all 0.3s cubic-bezier(0.16,1,0.3,1)';
  el.style.transform = 'scale(0.95)';
  el.style.opacity = '0';
  setTimeout(() => {
    el.classList.add('hidden');
    el.style.transform = '';
    el.style.opacity = '';
    el.innerHTML = id === 'quiz-container' ? '' : el.innerHTML;
  }, 300);
  showToast('Cleared ✓');
}

// ── GENERATE QUIZ ──
function generateQuiz() {
  const topic = document.getElementById('quiz-topic').value.trim();
  if (!topic) { showToast('Please enter a topic!', true); return; }
  const diffEl   = document.querySelector('.diff-btn.selected');
  const difficulty = diffEl ? diffEl.getAttribute('data-diff') : 'medium';
  showLoading('Generating your quiz...');
  answeredCount = 0; correctCount = 0;
  apiCall('/quiz', { topic, num_questions: numQuestions, difficulty })
    .then(data => { quizData = data; renderQuiz(data); })
    .catch(() => showToast('Error generating quiz!', true))
    .finally(hideLoading);
}

function renderQuiz(data) {
  const c = document.getElementById('quiz-container');
  c.innerHTML = '';
  c.classList.remove('hidden');

  // Title
  const title = document.createElement('div');
  title.className = 'quiz-title-bar';
  title.textContent = data.quiz_title || 'Quiz';
  c.appendChild(title);

  // Questions
  data.questions.forEach((q, i) => {
    const card = document.createElement('div');
    card.className = 'q-card';
    card.id = 'q-' + i;
    card.innerHTML = `
      <div class="q-num">Question ${i + 1} of ${data.questions.length}</div>
      <div class="q-text">${q.question}</div>
      <div class="q-opts" id="opts-${i}"></div>
      <div class="q-exp" id="qexp-${i}">💡 ${q.explanation}</div>
    `;
    c.appendChild(card);

    const optsDiv = document.getElementById('opts-' + i);
    Object.entries(q.options).forEach(([letter, text]) => {
      const opt = document.createElement('div');
      opt.className = 'q-opt';
      opt.setAttribute('data-letter', letter);
      opt.innerHTML = `<span class="opt-letter">${letter}</span><span>${text}</span>`;
      opt.addEventListener('click', () => handleAnswer(i, letter, q.correct_answer, card));
      optsDiv.appendChild(opt);
    });
  });

  // Score strip
  const strip = document.createElement('div');
  strip.className = 'score-strip';
  strip.innerHTML = `
    <span class="score-label" id="score-label">0 / ${data.questions.length}</span>
    <div class="score-track"><div class="score-fill" id="score-fill" style="width:0%"></div></div>
  `;
  c.appendChild(strip);
  c.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function handleAnswer(idx, selected, correct, card) {
  if (card.getAttribute('data-answered')) return;
  card.setAttribute('data-answered', 'true');
  answeredCount++;

  card.querySelectorAll('.q-opt').forEach(opt => {
    opt.style.pointerEvents = 'none';
    const letter = opt.getAttribute('data-letter');
    if (letter === correct) opt.classList.add('correct');
    else if (letter === selected) opt.classList.add('wrong');
  });

  document.getElementById('qexp-' + idx).style.display = 'block';
  if (selected === correct) correctCount++;

  const total = quizData.questions.length;
  document.getElementById('score-label').textContent = `${correctCount} / ${total}`;
  document.getElementById('score-fill').style.width = Math.round(correctCount / total * 100) + '%';

  if (answeredCount === total) {
    setTimeout(() => showToast(`Quiz done! ${correctCount}/${total} correct 🎉`), 400);
  }
}

// ── EXPLAIN ──
function explainConcept() {
  const concept = document.getElementById('exp-concept').value.trim();
  if (!concept) { showToast('Please enter a concept!', true); return; }
  const lvlEl = document.querySelector('.level-btn.selected');
  const level = lvlEl ? lvlEl.getAttribute('data-level') : 'intermediate';
  showLoading('Crafting your explanation...');
  apiCall('/explain', { concept, level })
    .then(data => showResult('exp-result', 'exp-result-text', data.explanation))
    .catch(() => showToast('Server error! Make sure Flask is running.', true))
    .finally(hideLoading);
}
