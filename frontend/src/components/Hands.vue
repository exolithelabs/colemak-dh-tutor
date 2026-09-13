<script setup lang="ts">
const props = defineProps<{
  targetFinger: number;
}>();

const fingerColors = [
  '#cbd5e1', // Thumb
  '#fda4af', '#fbbf24', '#fde047', '#a7f3d0', // Left
  '#99f6e4', '#bae6fd', '#c7d2fe', '#ddd6fe'  // Right
];
</script>

<template>
  <div class="hands-container">
    <!-- Left Hand -->
    <svg viewBox="0 0 200 200" class="hand-svg left">
      <path d="M40,150 Q60,180 100,170 Q130,160 140,120 L130,80 Q100,70 60,80 Z" fill="#fde047" opacity="0.2" stroke="#64748b" />
      <rect x="30" y="70" width="15" height="40" rx="7" :fill="targetFinger === 1 ? fingerColors[1] : '#f1f5f9'" stroke="#64748b" :class="{ active: targetFinger === 1 }" />
      <rect x="55" y="40" width="18" height="60" rx="9" :fill="targetFinger === 2 ? fingerColors[2] : '#f1f5f9'" stroke="#64748b" :class="{ active: targetFinger === 2 }" />
      <rect x="85" y="30" width="18" height="70" rx="9" :fill="targetFinger === 3 ? fingerColors[3] : '#f1f5f9'" stroke="#64748b" :class="{ active: targetFinger === 3 }" />
      <rect x="115" y="40" width="18" height="60" rx="9" :fill="targetFinger === 4 ? fingerColors[4] : '#f1f5f9'" stroke="#64748b" :class="{ active: targetFinger === 4 }" />
      <rect x="145" y="110" width="40" height="15" rx="7" transform="rotate(-30 145 110)" :fill="targetFinger === 0 ? fingerColors[0] : '#f1f5f9'" stroke="#64748b" :class="{ active: targetFinger === 0 }" />
    </svg>

    <!-- Right Hand -->
    <svg viewBox="0 0 200 200" class="hand-svg right">
      <path d="M160,150 Q140,180 100,170 Q70,160 60,120 L70,80 Q100,70 140,80 Z" fill="#fde047" opacity="0.2" stroke="#64748b" />
      <rect x="155" y="70" width="15" height="40" rx="7" :fill="targetFinger === 8 ? fingerColors[8] : '#f1f5f9'" stroke="#64748b" :class="{ active: targetFinger === 8 }" />
      <rect x="127" y="40" width="18" height="60" rx="9" :fill="targetFinger === 7 ? fingerColors[7] : '#f1f5f9'" stroke="#64748b" :class="{ active: targetFinger === 7 }" />
      <rect x="97" y="30" width="18" height="70" rx="9" :fill="targetFinger === 6 ? fingerColors[6] : '#f1f5f9'" stroke="#64748b" :class="{ active: targetFinger === 6 }" />
      <rect x="67" y="40" width="18" height="60" rx="9" :fill="targetFinger === 5 ? fingerColors[5] : '#f1f5f9'" stroke="#64748b" :class="{ active: targetFinger === 5 }" />
      <rect x="15" y="110" width="40" height="15" rx="7" transform="rotate(30 55 110)" :fill="targetFinger === 0 ? fingerColors[0] : '#f1f5f9'" stroke="#64748b" :class="{ active: targetFinger === 0 }" />
    </svg>
  </div>
</template>

<style scoped>
.hands-container {
  display: flex;
  justify-content: space-between;
  width: 100%;
  max-width: 600px;
}

.hand-svg {
  width: 180px;
  height: 180px;
}

.active {
  stroke: var(--primary-color);
  stroke-width: 3px;
  animation: tap 0.3s ease-in-out infinite alternate;
}

@keyframes tap {
  from { transform: scale(1); }
  to { transform: scale(1.05) translateY(-5px); }
}

/* Specific transform for thumb to keep origin correct */
rect.active[transform*="rotate"] {
  animation: tap-rotate 0.3s ease-in-out infinite alternate;
}

@keyframes tap-rotate {
  from { transform: rotate(-30deg) scale(1); }
  to { transform: rotate(-30deg) scale(1.1) translateY(-5px); }
}

.right rect.active[transform*="rotate"] {
  animation: tap-rotate-right 0.3s ease-in-out infinite alternate;
}

@keyframes tap-rotate-right {
  from { transform: rotate(30deg) scale(1); }
  to { transform: rotate(30deg) scale(1.1) translateY(-5px); }
}
</style>
