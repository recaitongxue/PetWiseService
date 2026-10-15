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
        <AppIcon :name="item.icon" :size="21" :stroke-width="isActive(item) ? 2 : 1.6" />
        <span v-if="item.name === 'chat' && unread > 0" class="dock-badge num">{{ unread }}</span>
      </span>
      <span class="dock-label">{{ item.label }}</span>
    </router-link>

    <!-- 中央核心入口：问诊（最重要功能居中，拇指热区） -->
    <router-link to="/consult" class="dock-fab" :class="{ on: consultActive }" aria-label="问诊">
      <AppIcon name="stethoscope" :size="20" :stroke-width="2" />
      <span class="dock-fab-label">问诊</span>
    </router-link>

    <router-link
      v-for="item in rightItems"
      :key="item.name"
      :to="item.to"
      class="dock-item"
      :class="{ on: isActive(item) }"
    >
      <span class="dock-ic">
        <AppIcon :name="item.icon" :size="21" :stroke-width="isActive(item) ? 2 : 1.6" />
      </span>
      <span class="dock-label">{{ item.label }}</span>
    </router-link>
  </nav>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import { fetchConversations } from '@/api/data'

const route = useRoute()

const conversations = ref([])
onMounted(async () => {
  conversations.value = await fetchConversations()
})

// 3~5 个一级目的地（平台规范）；每个 tab 用 match 声明所属路由域，
// 保证进入子页面（医生列表 / 问诊室 / 报告）时高亮不丢失
const items = [
  { name: 'home', label: '今日', icon: 'home', to: '/home', match: ['/home'] },
  {
    name: 'community',
    label: '社区',
    icon: 'paw',
    to: '/community',
    match: ['/community', '/breed']
  }
]
const rightItems = [
  { name: 'chat', label: '消息', icon: 'chat', to: '/chat', match: ['/chat'] },
  {
    name: 'profile',
    label: '我的',
    icon: 'user',
    to: '/profile',
    match: ['/profile', '/pet', '/schedule', '/favorites', '/account']
  }
]

// 问诊域：AI 问诊 / 结构化预问诊 / 找医生 / 问诊室 / 报告 / 问诊记录
const CONSULT_DOMAIN = [
  '/consult',
  '/preconsult',
  '/doctors',
  '/doctor',
  '/consultation',
  '/report',
  '/records'
]

const unread = computed(() => conversations.reduce((s, c) => s + (c.unread || 0), 0))
const consultActive = computed(() => hit(CONSULT_DOMAIN))

function hit(prefixes) {
  const p = route.path
  return prefixes.some((x) => p === x || p.startsWith(x + '/'))
}

function isActive(item) {
  if (hit(item.match || [])) return true
  if (item.name === 'chat' && route.name === 'chatroom') return true
  return false
}
</script>

<style scoped>
/* 底部导航：嵌入外壳布局的静态 flex 项（不再是悬浮层）。
   内容区在它上方自然收住，任何页面都不会被遮挡；导航本身不随内容滚动。 */
.dock {
  position: relative;
  flex: 0 0 auto;
  width: 100%;
  display: flex;
  align-items: flex-end;
  gap: 2px;
  padding: 7px 8px calc(7px + env(safe-area-inset-bottom, 0px));
  background: color-mix(in srgb, var(--color-surface) 88%, transparent);
  backdrop-filter: blur(18px) saturate(1.2);
  -webkit-backdrop-filter: blur(18px) saturate(1.2);
  border-top: 1px solid var(--hairline);
  z-index: 30;
}

.dock-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 5px 0 6px;
  border-radius: 999px;
  color: var(--color-muted);
  min-height: 44px;
  transition: color var(--dur-fast) var(--ease-out);
}
.dock-item:active { transform: scale(0.94); }

/* 选中态：图标上色底托 + 文字加重（不只靠颜色区分） */
.dock-item.on { color: var(--color-ink); }

.dock-ic {
  position: relative;
  display: grid;
  place-items: center;
  width: 32px;
  height: 26px;
  border-radius: 999px;
  transition: background var(--dur-fast) var(--ease-out);
}
.dock-item.on .dock-ic {
  background: color-mix(in srgb, var(--color-accent) 14%, transparent);
  color: var(--color-accent-ink);
}

.dock-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.dock-item.on .dock-label { font-weight: 800; }

.dock-badge {
  position: absolute;
  top: -4px;
  right: -6px;
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

/* 中央核心入口：胶囊按钮（视觉焦点 + 文字标签，不做无标签纯图标）。
   注意：不做向上凸起——凸起会超出 dock 布局盒，导致上方操作栏与导航之间出现遮挡/缝隙 */
.dock-fab {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  width: 60px;
  height: 44px;
  border-radius: 999px;
  color: #fff;
  margin: 0 4px;
  background: linear-gradient(150deg, var(--color-accent), var(--color-accent-ink));
  box-shadow:
    0 6px 16px rgba(214, 80, 42, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transition:
    transform var(--dur-base) var(--ease-out),
    box-shadow var(--dur-base) var(--ease-out);
}
.dock-fab-label {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
}
/* 选中：外圈光环（保持焦点但不刺眼） */
.dock-fab.on {
  box-shadow:
    0 6px 16px rgba(214, 80, 42, 0.28),
    0 0 0 3px color-mix(in srgb, var(--color-accent) 22%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.dock-fab:active { transform: scale(0.94); }
</style>
