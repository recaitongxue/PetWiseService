<template>
  <router-link :to="action.to" class="quick" :class="{ accent: action.accent }">
    <span class="quick-icon">
      <AppIcon :name="action.icon" :size="24" />
    </span>
    <span class="quick-label">{{ action.label }}</span>
    <span class="quick-arrow"><AppIcon name="back" :size="14" /></span>
  </router-link>
</template>

<script setup>
import AppIcon from '@/components/icons/AppIcon.vue'

defineProps({
  action: { type: Object, required: true }
})
</script>

<style scoped>
.quick {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-1);
  transition: transform var(--dur-fast) var(--ease-out), box-shadow var(--dur-base) var(--ease-out);
}
.quick:active {
  transform: scale(0.97);
}
.quick.accent {
  background: linear-gradient(140deg, var(--color-ink), #243a30);
  border-color: transparent;
}
.quick.accent .quick-label,
.quick.accent .quick-icon {
  color: var(--color-surface);
}
.quick-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: var(--color-sage-soft);
  color: var(--color-ink);
  flex-shrink: 0;
}
.quick.accent .quick-icon {
  background: rgba(255, 255, 255, 0.14);
}
.quick-label {
  font-weight: 700;
  font-size: 15px;
  flex: 1;
}
.quick-arrow {
  color: var(--color-muted);
  transform: rotate(180deg);
  opacity: 0.5;
}
.quick.accent .quick-arrow {
  color: var(--color-surface);
  opacity: 0.7;
}
</style>
