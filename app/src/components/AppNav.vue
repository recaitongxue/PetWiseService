<template>
  <nav class="dock" aria-label="主导航">
    <router-link
      v-for="item in items"
      :key="item.name"
      :to="item.to"
      class="dock-item"
      :class="{ on: isActive(item) }"
    >
      <span class="dock-ic">
        <AppIcon :name="item.icon" :size="21" />
        <span v-if="item.name === 'chat' && unread > 0" class="dock-badge num">{{ unread }}</span>
      </span>
      <span class="dock-label">{{ item.label }}</span>
    </router-link>

    <router-link to="/recognize" class="dock-fab" aria-label="拍照识别">
      <AppIcon name="camera" :size="24" />
    </router-link>

    <router-link
      v-for="item in rightItems"
      :key="item.name"
      :to="item.to"
      class="dock-item"
      :class="{ on: isActive(item) }"
    >
      <span class="dock-ic"><AppIcon :name="item.icon" :size="21" /></span>
      <span class="dock-label">{{ item.label }}</span>
    </router-link>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import { conversations } from '@/data/mock'

const route = useRoute()

const items = [
  { name: 'home', label: '今日', icon: 'home', to: '/home' },
  { name: 'community', label: '社区', icon: 'paw', to: '/community' }
]
const rightItems = [
  { name: 'chat', label: '消息', icon: 'chat', to: '/chat' },
  { name: 'profile', label: '我的', icon: 'user', to: '/profile' }
]

const unread = computed(() => conversations.reduce((s, c) => s + (c.unread || 0), 0))

function isActive(item) {
  if (route.name === item.name) return true
  if (item.name === 'chat' && route.name === 'chatroom') return true
  return false
}
</script>

<style scoped>
/* 悬浮毛玻璃 Dock */
.dock {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(14px + env(safe-area-inset-bottom, 0px));
  width: calc(100% - 32px);
  max-width: calc(var(--shell-max) - 40px);
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 8px 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-surface) 84%, transparent);
  backdrop-filter: blur(18px) saturate(1.2);
  -webkit-backdrop-filter: blur(18px) saturate(1.2);
  box-shadow:
    0 0 0 1px var(--color-border),
    0 18px 44px rgba(27, 42, 34, 0.22);
  z-index: 30;
}

.dock-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 7px 0 6px;
  border-radius: 999px;
  color: var(--color-muted);
  transition: color var(--dur-fast) var(--ease-out), background var(--dur-fast);
  min-height: 44px;
  justify-content: center;
}
.dock-item.on {
  color: var(--color-ink);
  background: rgba(27, 42, 34, 0.07);
}
.dock-item:active { transform: scale(0.94); }

.dock-ic {
  position: relative;
  display: grid;
  place-items: center;
}
.dock-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.dock-badge {
  position: absolute;
  top: -5px;
  right: -9px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  background: var(--color-accent);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  display: grid;
  place-items: center;
  box-shadow: 0 0 0 2px var(--color-surface);
}

/* 中央识别 FAB */
.dock-fab {
  flex: 0 0 auto;
  width: 54px;
  height: 54px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #fff;
  margin: 0 8px;
  transform: translateY(-10px);
  background: linear-gradient(150deg, var(--color-accent), var(--color-accent-ink));
  box-shadow:
    0 12px 26px rgba(232, 85, 43, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  transition: transform var(--dur-base) var(--ease-out);
}
.dock-fab:active {
  transform: translateY(-8px) scale(0.94);
}
</style>
