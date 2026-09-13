<script setup lang="ts">
import { ref, onMounted } from 'vue';
import Keyboard from './components/Keyboard.vue';
import TypingArea from './components/TypingArea.vue';
import { apiFetch, restartApplication, stopApplication } from './api';

interface Lesson {
  id: number;
  title: string;
  content: string;
  level: number;
}

const lessons = ref<Lesson[]>([]);
const currentLesson = ref<Lesson | null>(null);
const activeKey = ref('');
const targetKey = ref('');
const username = ref('User1');
const showStats = ref(false);
const finalStats = ref({ wpm: 0, accuracy: 0 });
const history = ref<any[]>([]);

// Web App UI State
const isDrawerOpen = ref(false);
const currentView = ref('lesson'); // 'lesson', 'history', 'custom'
const customText = ref('');

const toggleDrawer = () => {
  isDrawerOpen.value = !isDrawerOpen.value;
};

const setView = (view: string) => {
  currentView.value = view;
  isDrawerOpen.value = false;
  showStats.value = false;
};

const fetchLessons = async () => {
  try {
    const res = await apiFetch('/api/lessons');
    lessons.value = await res.json();
    if (lessons.value.length > 0) {
      const savedLessonId = localStorage.getItem('currentLessonId');
      const savedLesson = lessons.value.find(l => l.id === Number(savedLessonId));
      currentLesson.value = savedLesson || lessons.value[0];
      targetKey.value = currentLesson.value.content[0];
    }
  } catch (err) {
    console.error('Failed to fetch lessons', err);
  }
};

const fetchHistory = async () => {
  try {
    const savedUser = localStorage.getItem('username') || 'User1';
    username.value = savedUser;
    const res = await apiFetch(`/api/user/progress/${encodeURIComponent(username.value)}`);
    history.value = await res.json();
  } catch (err) {
    console.error('Failed to fetch history', err);
  }
};

const handleComplete = async (stats: { wpm: number, accuracy: number }) => {
  finalStats.value = stats;
  showStats.value = true;
  
  if (currentLesson.value) {
    try {
      await apiFetch('/api/user/progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username.value,
          lesson_id: currentLesson.value.id,
          wpm: stats.wpm,
          accuracy: stats.accuracy
        })
      });
      fetchHistory();
    } catch (err) {
      console.error('Failed to save progress', err);
    }
  }
};

const nextLesson = () => {
  showStats.value = false;
  const currentIndex = lessons.value.findIndex(l => l.id === currentLesson.value?.id);
  if (currentIndex < lessons.value.length - 1) {
    const next = lessons.value[currentIndex + 1];
    switchLesson(next);
  } else {
    alert('All lessons completed!');
  }
};

const switchLesson = (lesson: Lesson) => {
  currentLesson.value = lesson;
  targetKey.value = lesson.content[0];
  setView('lesson');
  if (lesson.id !== 999) {
    localStorage.setItem('currentLessonId', lesson.id.toString());
  }
};

const handleCustomPractice = () => {
  if (!customText.value.trim()) return;
  const lesson: Lesson = {
    id: 999,
    title: 'Custom Practice',
    content: customText.value.trim().toLowerCase(),
    level: 99
  };
  switchLesson(lesson);
  setView('lesson'); // Force view change
};

const handleFileUpload = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    customText.value = e.target?.result as string;
  };
  reader.readAsText(file);
};

const stopApp = async () => {
  if (confirm('Are you sure you want to stop the application? Both backend and frontend will be shut down.')) {
    try {
      await stopApplication();
    } catch (e) {
      // Expecting network error as server shuts down
    }
    alert('Application is stopping. You can close this tab now.');
  }
};

const restartApp = async () => {
  if (confirm('Restart the application? This will reload all processes.')) {
    try {
      await restartApplication();
    } catch (e) {
      // Expecting network error
    }
    alert('Application is restarting. Please wait a few seconds and then refresh this page.');
  }
};

onMounted(() => {
  fetchLessons();
  fetchHistory();
  window.addEventListener('keydown', (e) => {
    activeKey.value = e.key;
  });
  window.addEventListener('keyup', () => {
    activeKey.value = '';
  });
});
</script>

<template>
  <div class="app-container">
    <!-- Overlay for Drawer -->
    <div v-if="isDrawerOpen" class="drawer-overlay" @click="toggleDrawer"></div>

    <!-- SIDE DRAWER (Hamburger Menu) -->
    <aside class="drawer" :class="{ open: isDrawerOpen }">
      <div class="drawer-header">
        <h2>Menu</h2>
        <button class="hamburger-btn" @click="toggleDrawer">✕</button>
      </div>

      <div class="drawer-content">
        <nav class="drawer-nav">
          <button class="nav-item" :class="{ active: currentView === 'lesson' }" @click="setView('lesson')">
            📖 Lessons
          </button>
          <button class="nav-item" :class="{ active: currentView === 'custom' }" @click="setView('custom')">
            ✍️ Custom Practice
          </button>
          <button class="nav-item" :class="{ active: currentView === 'history' }" @click="setView('history')">
            📊 Progress History
          </button>
        </nav>

        <div v-if="currentView === 'lesson'" class="drawer-section">
          <h3>Choose Lesson</h3>
          <ul class="lesson-list">
            <li 
              v-for="lesson in lessons" 
              :key="lesson.id"
              :class="{ active: currentLesson?.id === lesson.id }"
              @click="switchLesson(lesson)"
            >
              <span class="level">Lv. {{ lesson.level }}</span>
              <span class="title">{{ lesson.title }}</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="drawer-footer">
        <button class="system-btn restart" @click="restartApp">🔄 Restart App</button>
        <button class="system-btn stop" @click="stopApp">🛑 Stop App</button>
      </div>
    </aside>

    <!-- HEADER -->
    <header class="app-header">
      <div class="header-left">
        <button class="hamburger-btn" @click="toggleDrawer">☰</button>
        <div class="logo">
          <h1>Colemak-DH</h1>
        </div>
      </div>
      <div class="current-lesson-name">
        {{ currentLesson?.title || 'No Lesson Selected' }}
      </div>
    </header>

    <!-- MAIN VIEW -->
    <main class="main-view">
      
      <!-- Lesson Practice View -->
      <div v-if="currentView === 'lesson' && !showStats" class="typing-section">
        <TypingArea 
          v-if="currentLesson"
          :targetText="currentLesson.content" 
          @complete="handleComplete"
          @targetChange="(key) => targetKey = key"
        />
      </div>

      <!-- Custom Practice Setup -->
      <div v-if="currentView === 'custom'" class="custom-view-content">
        <div class="card full-height-card">
          <h2>Custom Practice</h2>
          <p>Paste text or upload a file to begin.</p>
          <textarea 
            v-model="customText" 
            placeholder="Paste your text here..." 
            class="custom-textarea flex-grow"
          ></textarea>
          <div class="upload-actions">
            <label class="file-label">
              📁 Upload .txt
              <input type="file" accept=".txt" @change="handleFileUpload" />
            </label>
            <button @click="handleCustomPractice" :disabled="!customText.trim()">Start Practice</button>
          </div>
        </div>
      </div>

      <!-- History View -->
      <div v-if="currentView === 'history'" class="history-view-content">
        <div class="card">
          <h2>Your History</h2>
          <div class="history-table-wrapper">
            <table class="history-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>WPM</th>
                  <th>Accuracy</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(entry, index) in history.slice().reverse()" :key="index">
                  <td>{{ new Date(entry.completed_at).toLocaleDateString() }}</td>
                  <td class="wpm-val">{{ entry.wpm }}</td>
                  <td class="acc-val">{{ entry.accuracy }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Stats Modal (Overlay on Top) -->
      <div v-if="showStats" class="stats-overlay">
        <div class="stats-modal card">
          <div class="success-icon">🎉</div>
          <h2>Well Done!</h2>
          <div class="final-stats-grid">
            <div class="stat-item">
              <label>Speed</label>
              <div class="value">{{ finalStats.wpm }} <small>WPM</small></div>
            </div>
            <div class="stat-item">
              <label>Accuracy</label>
              <div class="value">{{ finalStats.accuracy }}%</div>
            </div>
          </div>
          <div class="modal-actions">
            <button @click="nextLesson">Next Lesson</button>
            <button class="secondary" @click="showStats = false; setView('lesson')">Practice Again</button>
          </div>
        </div>
      </div>

      <!-- FIXED VISUALIZER SECTION -->
      <div v-if="currentView === 'lesson' && !showStats" class="visualizer-section">
        <Keyboard :activeKey="activeKey" :targetKey="targetKey" />
      </div>

    </main>
  </div>
</template>

<style scoped>
.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.app-header h1 {
  font-size: 1.2rem;
  margin: 0;
}

.current-lesson-name {
  font-weight: 600;
  color: var(--text-muted);
  font-size: 0.9rem;
}

/* Side Drawer Styles */
.drawer-nav {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 30px;
}

.nav-item {
  text-align: left;
  background: transparent;
  padding: 12px;
  width: 100%;
  color: var(--text-muted);
}

.nav-item.active {
  background: rgba(66, 184, 131, 0.1);
  color: var(--primary-color);
}

.drawer-section h3 {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 10px;
}

.lesson-list {
  list-style: none;
  padding: 0;
}

.lesson-list li {
  padding: 10px;
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  margin-bottom: 5px;
}

.lesson-list li:hover { background: rgba(255,255,255,0.05); }
.lesson-list li.active { border: 1px solid var(--primary-color); }
.lesson-list li .level { font-size: 0.6rem; color: var(--primary-color); font-weight: 800; }
.lesson-list li .title { font-size: 0.9rem; font-weight: 600; }

/* Views Content */
.custom-view-content, .history-view-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.custom-textarea {
  width: 100%;
  background: var(--bg-color);
  color: white;
  border: 1px solid rgba(255,255,255,0.1);
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 15px;
  min-height: 200px;
}

.full-height-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.flex-grow {
  flex: 1;
}

.upload-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-label {
  cursor: pointer;
  color: var(--primary-color);
  font-weight: 600;
}

.file-label input { display: none; }

/* Stats Overlay */
.stats-overlay {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.stats-modal {
  text-align: center;
  width: 100%;
  max-width: 400px;
}

.final-stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin: 20px 0;
}

.stat-item {
  background: var(--bg-color);
  padding: 15px;
  border-radius: 10px;
}

.stat-item label { font-size: 0.7rem; color: var(--text-muted); }
.stat-item .value { font-size: 1.5rem; font-weight: 800; }

.modal-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* History Table */
.history-table-wrapper {
  max-height: 300px;
  overflow-y: auto;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th { text-align: left; padding: 10px; color: var(--text-muted); font-size: 0.8rem; }
.history-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); }
.wpm-val { color: var(--primary-color); font-weight: 700; }
.acc-val { color: var(--accent-color); font-weight: 700; }

.drawer-footer {
  margin-top: auto;
  padding: 20px;
  border-top: 1px solid rgba(255,255,255,0.1);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.system-btn {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  color: var(--text-muted);
  font-size: 0.85rem;
  justify-content: center;
}

.system-btn.restart:hover {
  background: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
}

.system-btn.stop:hover {
  background: var(--error-color);
  color: white;
  border-color: var(--error-color);
}
</style>
