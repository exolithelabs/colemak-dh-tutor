<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue';

const props = defineProps<{
  targetText: string;
}>();

const emit = defineEmits(['complete', 'targetChange']);

const userInput = ref('');
const inputRef = ref<HTMLInputElement | null>(null);
const isFocused = ref(true);
const startTime = ref<number | null>(null);
const wpm = ref(0);
const accuracy = ref(100);
const currentKey = ref('');

const handleInput = (e: KeyboardEvent) => {
  if (userInput.value.length === props.targetText.length) return;
  
  if (!startTime.value) {
    startTime.value = Date.now();
  }

  currentKey.value = e.key;
};

const checkInput = () => {
  const target = props.targetText;
  const current = userInput.value;
  
  const nextChar = target[current.length] || '';
  emit('targetChange', nextChar);

  // Auto-scroll logic
  nextTick(() => {
    const currentElem = document.querySelector('.char.current');
    if (currentElem) {
      currentElem.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  });

  let errors = 0;
  for (let i = 0; i < current.length; i++) {
    if (current[i] !== target[i]) {
      errors++;
    }
  }
  
  accuracy.value = Math.max(0, Math.round(((current.length - errors) / current.length) * 100)) || 100;
  
  if (startTime.value) {
    const elapsedMinutes = (Date.now() - startTime.value) / 60000;
    if (elapsedMinutes > 0) {
      wpm.value = Math.round((current.length / 5) / elapsedMinutes);
    }
  }

  if (current.length === target.length) {
    emit('complete', { wpm: wpm.value, accuracy: accuracy.value });
  }
};

watch(userInput, checkInput);

watch(() => props.targetText, () => {
  userInput.value = '';
  startTime.value = null;
  wpm.value = 0;
  accuracy.value = 100;
  emit('targetChange', props.targetText[0] || '');
  nextTick(() => {
    inputRef.value?.focus();
  });
});

const onKeyDown = (e: KeyboardEvent) => {
  // Use currentKey for visualization
  currentKey.value = e.key;

  // TAB: Refocus the input
  if (e.key === 'Tab') {
    e.preventDefault();
    inputRef.value?.focus();
    isFocused.value = true;
  }

  // ESC: Reset the current lesson
  if (e.key === 'Escape') {
    e.preventDefault();
    userInput.value = '';
    startTime.value = null;
    wpm.value = 0;
    accuracy.value = 100;
    emit('targetChange', props.targetText[0] || '');
    nextTick(() => {
      inputRef.value?.focus();
    });
  }
};

const onBlur = () => {
  isFocused.value = false;
};

const onFocus = () => {
  isFocused.value = true;
};

const forceFocus = () => {
  inputRef.value?.focus();
};

onMounted(() => {
  emit('targetChange', props.targetText[0] || '');
  window.addEventListener('keydown', onKeyDown);
  nextTick(() => forceFocus());
});

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown);
});
</script>

<template>
  <div class="typing-container">
    <div class="stats-bar">
      <div class="stat-bubble">
        <span class="label">Speed</span>
        <span class="value">{{ wpm }} <small>WPM</small></span>
      </div>
      <div class="stat-bubble">
        <span class="label">Accuracy</span>
        <span class="value">{{ accuracy }}%</span>
      </div>
    </div>

    <div 
      class="text-display-card" 
      :class="{ unfocused: !isFocused }"
      @click="forceFocus"
    >
      <div v-if="!isFocused" class="focus-overlay">
        <span>Click to Resume</span>
      </div>
      <div class="scroll-container">
        <div class="text-scroller">
          <span 
            v-for="(char, index) in targetText" 
            :key="index"
            class="char"
            :class="{
              correct: userInput[index] === char,
              incorrect: userInput[index] !== undefined && userInput[index] !== char,
              current: userInput.length === index
            }"
          >
            {{ char }}
          </span>
        </div>
      </div>
    </div>

    <input 
      ref="inputRef"
      v-model="userInput" 
      class="hidden-input" 
      autofocus
      @keydown="handleInput"
      @blur="onBlur"
      @focus="onFocus"
    />
    
    <div class="typing-hint">
      <kbd>ESC</kbd> to restart lesson • <kbd>TAB</kbd> to focus input
    </div>
  </div>
</template>

<style scoped>
.typing-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 0;
  justify-content: center;
}

.stats-bar {
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-shrink: 0;
}

.stat-bubble {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-bubble .label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

.stat-bubble .value {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text-main);
}

.stat-bubble .value small {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--text-muted);
}

.text-display-card {
  background: var(--card-bg);
  padding: 0;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.1);
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  font-size: 1.8rem; /* Slightly smaller for better fit */
  line-height: 1.5;
  position: relative;
  overflow: hidden;
  height: 160px; /* Fixed height to prevent shifting */
  flex-shrink: 0;
}

.scroll-container {
  height: 100%;
  overflow-y: auto;
  padding: 40px;
  scrollbar-width: thin;
  scrollbar-color: var(--primary-color) transparent;
}

.scroll-container::-webkit-scrollbar {
  width: 6px;
}

.scroll-container::-webkit-scrollbar-thumb {
  background-color: var(--primary-color);
  border-radius: 10px;
}

.text-display-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0; width: 10px;
  background: var(--primary-color);
}

.text-display-card.unfocused {
  filter: grayscale(0.5);
  cursor: pointer;
}

.focus-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  backdrop-filter: blur(2px);
}

.focus-overlay span {
  background: var(--primary-color);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 1rem;
  font-weight: 700;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}

.char {
  color: #94a3b8;
  position: relative;
  transition: all 0.1s;
}

.char.correct {
  color: var(--text-main);
}

.char.incorrect {
  color: var(--error-color);
  background: #fee2e2;
  border-radius: 4px;
}

.char.current {
  color: var(--primary-color);
  background: #f0fdf4;
  border-radius: 4px;
}

.char.current::after {
  content: '';
  position: absolute;
  bottom: -2px; left: 0; right: 0;
  height: 3px;
  background: var(--primary-color);
  border-radius: 2px;
  animation: blink 1s infinite;
}

@keyframes blink {
  50% { opacity: 0; }
}

.hidden-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.typing-hint {
  text-align: center;
  font-size: 0.85rem;
  color: var(--text-muted);
}

kbd {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 0.75rem;
  font-weight: 700;
  font-family: sans-serif;
}

@media (max-height: 760px) {
  .typing-container {
    gap: 10px;
  }

  .text-display-card {
    height: 125px;
    font-size: 1.5rem;
  }

  .scroll-container {
    padding: 24px 30px;
  }
}
</style>
