<template>
  <div class="toast-host" aria-live="polite">
    <transition-group name="toast">
      <div v-for="t in toasts" :key="t.id" class="toast" :class="t.type">
        <span class="toast-ic" v-if="t.type === 'success'"><AppIcon name="check" :size="16" /></span>
        <span class="toast-ic" v-else-if="t.type === 'warn'"><AppIcon name="bell" :size="16" /></span>
        <span class="toast-text">{{ t.message }}</span>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import AppIcon from '@/components/icons/AppIcon.vue'
import { toasts } from '@/composables/toast'
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
