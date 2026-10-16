<template>
  <div class="toast-host" aria-live="polite">
    <transition-group name="toast">
      <div v-for="t in toasts" :key="t.id" class="toast" :class="t.type">
        <svg v-if="t.type === 'success'" class="toast-ic" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"
             stroke-linejoin="round" aria-hidden="true">
          <path d="m5 12 4.5 4.5L19 7" />
        </svg>
        <svg v-else-if="t.type === 'warn'" class="toast-ic" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"
             stroke-linejoin="round" aria-hidden="true">
          <path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6Z" />
          <path d="M10 19a2 2 0 0 0 4 0" />
        </svg>
        <span class="toast-text">{{ t.message }}</span>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
// 共享组件（packages/shared）：图标内联，不依赖各端 AppIcon，保持自包含
import { toasts } from './toast'
</script>

<style scoped>
.toast-host {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(96px + env(safe-area-inset-bottom, 0px));
  z-index: 60;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  pointer-events: none;
  width: max-content;
  max-width: 84vw;
}
.toast {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 11px 18px;
  border-radius: var(--radius-pill);
  background: var(--color-ink);
  color: var(--color-surface);
  font-size: 14px;
  font-weight: 600;
  box-shadow: var(--shadow-2);
  white-space: nowrap;
}
.toast.success { background: var(--color-good); }
.toast.warn { background: var(--color-watch); }
.toast-ic { display: grid; place-items: center; }

.toast-enter-active,
.toast-leave-active {
  transition: opacity var(--dur-base) var(--ease-out), transform var(--dur-base) var(--ease-out);
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.96);
}
</style>
