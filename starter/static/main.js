// Client-side rendering and interaction for the Flask-backed Sudoku
const SIZE = 9;
const LEADERBOARD_KEY = 'sudokuLeaderboard';
const MAX_NAME_LENGTH = 30;
// Lower is better: elapsed seconds plus hint penalties minus the difficulty bonus.
const DIFFICULTY_BONUSES = {easy: 0, medium: 60, hard: 120};
const HINT_PENALTY_SECONDS = 30;
let puzzle = [];
let activeDifficulty = null;
let timerInterval = null;
let gameStartedAt = null;
let elapsedSeconds = 0;
let gameCompleted = false;
const THEME_KEY = 'sudokuTheme';

function setMessage(text, type = 'neutral') {
  const message = document.getElementById('message');
  message.className = text ? `message-${type}` : '';
  message.innerText = text;
}

function applyTheme(theme) {
  const selectedTheme = theme === 'dark' ? 'dark' : 'light';
  document.documentElement.dataset.theme = selectedTheme;
  document.getElementById('theme-toggle').checked = selectedTheme === 'dark';
}

function initializeTheme() {
  let savedTheme = 'light';
  try {
    savedTheme = localStorage.getItem(THEME_KEY) || 'light';
  } catch (error) {
    // Use the light theme when browser storage is unavailable.
  }
  applyTheme(savedTheme);
  document.getElementById('theme-toggle').addEventListener('change', (event) => {
    const theme = event.target.checked ? 'dark' : 'light';
    applyTheme(theme);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch (error) {
      // The theme remains active for the current page.
    }
  });
}

function createBoardElement() {
  const boardDiv = document.getElementById('sudoku-board');
  boardDiv.innerHTML = '';
  for (let i = 0; i < SIZE; i++) {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'sudoku-row';
    for (let j = 0; j < SIZE; j++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.maxLength = 1;
      input.className = 'sudoku-cell';
      input.dataset.row = i;
      input.dataset.col = j;
      input.dataset.box = Math.floor(i / 3) * 3 + Math.floor(j / 3);
      input.classList.add(Number(input.dataset.box) % 2 === 0 ? 'box-tone-a' : 'box-tone-b');
      input.setAttribute('aria-label', `Row ${i + 1}, Column ${j + 1}`);
      input.addEventListener('input', (e) => {
        const val = e.target.value.replace(/[^1-9]/g, '');
        e.target.value = val;
        e.target.classList.toggle('incorrect', val !== '' && hasConflict(i, j, val));
      });
      rowDiv.appendChild(input);
    }
    boardDiv.appendChild(rowDiv);
  }
}

function hasConflict(row, col, value) {
  const inputs = document.getElementById('sudoku-board').getElementsByTagName('input');
  for (let index = 0; index < inputs.length; index++) {
    const input = inputs[index];
    if (input === inputs[row * SIZE + col] || input.value !== value) continue;
    const otherRow = Number(input.dataset.row);
    const otherCol = Number(input.dataset.col);
    if (otherRow === row || otherCol === col ||
        (Math.floor(otherRow / 3) === Math.floor(row / 3) &&
         Math.floor(otherCol / 3) === Math.floor(col / 3))) {
      return true;
    }
  }
  return false;
}

function renderPuzzle(puz) {
  puzzle = puz;
  createBoardElement();
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  for (let i = 0; i < SIZE; i++) {
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = puzzle[i][j];
      const inp = inputs[idx];
      if (val !== 0) {
        inp.value = val;
        inp.disabled = true;
        inp.className += ' prefilled';
      } else {
        inp.value = '';
        inp.disabled = false;
      }
    }
  }
}

function formatElapsedTime(seconds) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, '0');
  const remainingSeconds = (seconds % 60).toString().padStart(2, '0');
  return `${minutes}:${remainingSeconds}`;
}

function updateTimer() {
  if (gameStartedAt === null || gameCompleted) return;
  elapsedSeconds = Math.floor((Date.now() - gameStartedAt) / 1000);
  document.getElementById('timer').innerText = formatElapsedTime(elapsedSeconds);
}

function startTimer() {
  clearInterval(timerInterval);
  gameStartedAt = Date.now();
  elapsedSeconds = 0;
  gameCompleted = false;
  document.getElementById('timer').innerText = '00:00';
  updateTimer();
  timerInterval = setInterval(updateTimer, 1000);
}

function stopTimer() {
  updateTimer();
  clearInterval(timerInterval);
  timerInterval = null;
}

function getCurrentBoard() {
  const inputs = document.getElementById('sudoku-board').getElementsByTagName('input');
  const board = [];
  for (let i = 0; i < SIZE; i++) {
    board[i] = [];
    for (let j = 0; j < SIZE; j++) {
      const val = inputs[i * SIZE + j].value;
      board[i][j] = val ? parseInt(val, 10) : 0;
    }
  }
  return board;
}

function readLeaderboard() {
  try {
    const stored = localStorage.getItem(LEADERBOARD_KEY);
    if (!stored) return [];
    const entries = JSON.parse(stored);
    if (!Array.isArray(entries)) return [];
    return entries.filter((entry) => entry &&
      typeof entry.id === 'string' &&
      typeof entry.name === 'string' &&
      Number.isInteger(entry.timeSeconds) && entry.timeSeconds >= 0 &&
      Object.prototype.hasOwnProperty.call(DIFFICULTY_BONUSES, entry.difficulty) &&
      Number.isInteger(entry.hintsUsed) && entry.hintsUsed >= 0 &&
      typeof entry.score === 'number' && Number.isFinite(entry.score) &&
      typeof entry.completedAt === 'string');
  } catch (error) {
    return [];
  }
}

function saveLeaderboard(entries) {
  try {
    localStorage.setItem(LEADERBOARD_KEY, JSON.stringify(entries));
  } catch (error) {
    // Gameplay remains available when browser storage is unavailable.
  }
}

function sortLeaderboard(entries) {
  return entries.sort((left, right) =>
    left.score - right.score ||
    left.timeSeconds - right.timeSeconds ||
    left.hintsUsed - right.hintsUsed ||
    left.completedAt.localeCompare(right.completedAt)
  ).slice(0, 10);
}

function renderLeaderboard() {
  const list = document.getElementById('leaderboard-list');
  list.innerHTML = '';
  sortLeaderboard(readLeaderboard()).forEach((entry) => {
    const item = document.createElement('li');
    item.innerText = `${entry.name} - ${formatElapsedTime(entry.timeSeconds)} (${entry.difficulty}, ${entry.hintsUsed} hints)`;
    list.appendChild(item);
  });
}

function createLeaderboardEntry() {
  const enteredName = window.prompt('Enter your name for the leaderboard:') || '';
  const name = enteredName.trim().slice(0, MAX_NAME_LENGTH) || 'Anonymous';
  const entry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    name,
    timeSeconds: elapsedSeconds,
    difficulty: activeDifficulty,
    hintsUsed: Number(document.getElementById('hint-count').dataset.count || 0),
    score: elapsedSeconds +
      Number(document.getElementById('hint-count').dataset.count || 0) * HINT_PENALTY_SECONDS -
      DIFFICULTY_BONUSES[activeDifficulty],
    completedAt: new Date().toISOString(),
  };
  const entries = sortLeaderboard([...readLeaderboard(), entry]);
  saveLeaderboard(entries);
  renderLeaderboard();
}

function completeGame() {
  if (gameCompleted) return;
  stopTimer();
  gameCompleted = true;
  document.getElementById('check-solution').disabled = true;
  document.getElementById('hint').disabled = true;
  document.querySelectorAll('#sudoku-board input').forEach((input) => {
    input.disabled = true;
  });
  setMessage(`Congratulations! You solved it in ${formatElapsedTime(elapsedSeconds)}.`, 'success');
  createLeaderboardEntry();
}

async function newGame() {
  const difficulty = document.getElementById('difficulty').value;
  const res = await fetch(`/new?difficulty=${encodeURIComponent(difficulty)}`);
  const data = await res.json();
  if (data.error) {
    setMessage(data.error, 'error');
    return;
  }
  activeDifficulty = data.difficulty;
  renderPuzzle(data.puzzle);
  document.getElementById('check-solution').disabled = false;
  document.getElementById('hint').disabled = false;
  document.getElementById('hint-count').innerText = 'Hints used: 0';
  document.getElementById('hint-count').dataset.count = '0';
  setMessage('');
  startTimer();
}

async function requestHint() {
  const res = await fetch('/hint', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board: getCurrentBoard()})
  });
  const data = await res.json();
  const msg = document.getElementById('message');
  if (data.error) {
    setMessage(data.error, 'error');
    return;
  }

  document.getElementById('hint-count').innerText = `Hints used: ${data.hints_used}`;
  document.getElementById('hint-count').dataset.count = data.hints_used;
  if (data.hint === null) {
    setMessage('No empty cells remain.', 'neutral');
    return;
  }

  const input = document.querySelector(
    `input[data-row="${data.row}"][data-col="${data.column}"]`
  );
  input.value = data.value;
  input.disabled = true;
  input.classList.add('hinted');
  input.classList.remove('incorrect');
  setMessage('Hint added.', 'success');
}

async function checkSolution() {
  if (gameCompleted) return;
  const inputs = document.getElementById('sudoku-board').getElementsByTagName('input');
  const board = getCurrentBoard();
  const res = await fetch('/check', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board})
  });
  const data = await res.json();
  const msg = document.getElementById('message');
  if (data.error) {
    setMessage(data.error, 'error');
    return;
  }
  const incorrect = new Set(data.incorrect.map(x => x[0]*SIZE + x[1]));
  for (let idx = 0; idx < inputs.length; idx++) {
    const inp = inputs[idx];
    if (inp.disabled) continue;
    inp.classList.remove('incorrect');
    if (incorrect.has(idx)) {
      inp.classList.add('incorrect');
    }
  }
  if (incorrect.size === 0 && !gameCompleted) {
    completeGame();
  } else {
    setMessage('Some cells are incorrect.', 'error');
  }
}

// Wire buttons
window.addEventListener('load', () => {
  initializeTheme();
  document.getElementById('new-game').addEventListener('click', newGame);
  document.getElementById('check-solution').addEventListener('click', checkSolution);
  document.getElementById('hint').addEventListener('click', requestHint);
  renderLeaderboard();
  // initialize
  newGame();
});