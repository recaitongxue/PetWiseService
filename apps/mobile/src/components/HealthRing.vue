<template>
  <div class="health-ring" :class="{ light }" :style="{ width: size + 'px', height: size + 'px' }">
    <svg :width="size" :height="size" viewBox="0 0 120 120">
      <circle cx="60" cy="60" r="52" fill="none" class="ring-track" stroke-width="10" />
      <circle
        cx="60"
        cy="60"
        r="52"
        fill="none"
        :stroke="color"
        stroke-width="10"
        stroke-linecap="round"
        :stroke-dasharray="circ"
        :stroke-dashoffset="offset"
        transform="rotate(-90 60 60)"
        class="ring-progress"
      />
    </svg>
    <div class="ring-center">
      <span class="ring-value num">{{ value }}</span>
      <span class="ring-label">{{ label }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 }, // 0-100
  label: { type: String, default: '健康分' },
  size: { type: Number, default: 120 },
  light: { type: Boolean, default: false } // 深色底模式
})

const circ = 2 * Math.PI * 52
const offset = ref(circ) // 初始为空，挂载后动画到目标
const color = computed(() => {
  if (props.value >= 85) return 'var(--color-good)'
  if (props.value >= 70) return 'var(--color-watch)'
  return 'var(--color-alert)'
})

onMounted(() => {
  requestAnimationFrame(() => {
    offset.value = circ * (1 - props.value / 100)
  })
})
</script>

<style scoped>
.health-ring {
  position: relative;
  display: grid;
  place-items: center;
}
.ring-track { stroke: var(--color-border); }
.ring-progress {
  transition: stroke-dashoffset 1s var(--ease-out);
}
.ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.ring-value {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 34px;
  line-height: 1;
  color: var(--color-ink);
}
.ring-label {
  font-size: 12px;
  color: var(--color-muted);
  margin-top: 2px;
  letter-spacing: 0.04em;
}
/* 深色底适配 */
.health-ring.light .ring-track { stroke: rgba(251, 246, 236, 0.22); }
.health-ring.light .ring-value { color: var(--color-surface); }
.health-ring.light .ring-label { color: rgba(251, 246, 236, 0.72); }
</style>
