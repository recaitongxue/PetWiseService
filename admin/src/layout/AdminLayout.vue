<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <aside class="side">
      <div class="brand">
        <span class="brand-mark">
          <AppIcon name="paw" :size="22" />
        </span>
        <div class="brand-text">
          <b>Petwise</b>
          <span>管理控制台</span>
        </div>
      </div>

      <nav class="menu">
        <router-link
          v-for="m in menus"
          :key="m.to"
          :to="m.to"
          class="menu-item"
          :class="{ on: isActive(m) }"
        >
          <AppIcon :name="m.icon" :size="19" />
          <span>{{ m.label }}</span>
          <span v-if="m.badge" class="menu-badge num">{{ m.badge }}</span>
        </router-link>
      </nav>

      <div class="side-foot">
        <div class="me">
          <span class="me-ava">运</span>
          <div class="me-info">
            <b>{{ admin.name }}</b>
            <span>{{ admin.role }}</span>
          </div>
        </div>
        <button class="logout" type="button" @click="logout">
          <AppIcon name="logout" :size="17" /> 退出登录
        </button>
      </div>
    </aside>

    <!-- 主区 -->
    <div class="main">
      <header class="topbar">
        <div>
          <p class="crumb">Petwise 平台</p>
          <h1 class="top-title">{{ route.meta.title }}</h1>
        </div>
        <div class="top-right">
          <label class="search">
            <AppIcon name="search" :size="16" />
            <input type="search" placeholder="搜索用户 / 宠物 / 记录…" />
          </label>
          <span class="env-chip">
            <AppIcon name="sparkle" :size="13" /> CV + LLM 服务正常
          </span>
        </div>
      </header>

      <main class="content">
        <router-view v-slot="{ Component }">
          <transition name="view" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import { admin } from '@/data/admin'
import { loadFeedbacks } from '@/data/ops'

const route = useRoute()
const router = useRouter()

const fbOpen = loadFeedbacks().filter((x) => x.state === 'open').length

const menus = [
  { to: '/dashboard', label: '数据看板', icon: 'chart' },
  { to: '/users', label: '用户管理', icon: 'users' },
  { to: '/records', label: '识别记录', icon: 'camera' },
  { to: '/moderation', label: '内容审核', icon: 'shield', badge: 2 },
  { to: '/consults', label: '问诊记录', icon: 'stethoscope' },
  { to: '/announce', label: '公告管理', icon: 'bell' },
  { to: '/feedback', label: '用户反馈', icon: 'comment', badge: fbOpen || null },
  { to: '/settings', label: '系统设置', icon: 'settings' }
]

function isActive(m) {
  return route.path.startsWith(m.to)
}

function logout() {
  localStorage.removeItem('petwise_admin_auth')
  router.replace('/login')
}
</script>

<style scoped>
.layout {
  display: flex;
  height: 100%;
  position: relative;
  z-index: 1;
}

/* ---------- 侧边栏 ---------- */
.side {
  width: 236px;
  flex-shrink: 0;
  background: var(--color-panel);
  color: var(--color-surface);
  display: flex;
  flex-direction: column;
  padding: 22px 14px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 0 8px 20px;
  border-bottom: 1px solid var(--color-line);
}
.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 13px;
  display: grid;
  place-items: center;
  background: var(--grad-coral, linear-gradient(150deg, #f4a987, #d6502a));
  color: #fff;
  flex-shrink: 0;
}
.brand-text { display: flex; flex-direction: column; line-height: 1.2; }
.brand-text b {
  font-family: var(--font-display);
  font-size: 17px;
  letter-spacing: -0.01em;
}
.brand-text span {
  font-size: 11px;
  color: rgba(251, 247, 238, 0.55);
  letter-spacing: 0.06em;
}

.menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding-top: 16px;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 11px 12px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 600;
  color: rgba(251, 247, 238, 0.66);
  transition: background var(--dur-fast), color var(--dur-fast);
  min-height: 44px;
}
.menu-item:hover { color: var(--color-surface); background: rgba(251, 247, 238, 0.06); }
.menu-item.on {
  color: var(--color-surface);
  background: rgba(251, 247, 238, 0.1);
  box-shadow: inset 2px 0 0 var(--color-accent);
}
.menu-badge {
  margin-left: auto;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--color-accent);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  display: grid;
  place-items: center;
}

.side-foot {
  border-top: 1px solid var(--color-line);
  padding-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.me { display: flex; align-items: center; gap: 10px; padding: 0 8px; }
.me-ava {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  background: rgba(251, 247, 238, 0.12);
  flex-shrink: 0;
}
.me-info { display: flex; flex-direction: column; line-height: 1.25; }
.me-info b { font-size: 13px; }
.me-info span { font-size: 11px; color: rgba(251, 247, 238, 0.5); }
.logout {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  color: rgba(251, 247, 238, 0.6);
  transition: color var(--dur-fast), background var(--dur-fast);
}
.logout:hover { color: var(--color-surface); background: rgba(251, 247, 238, 0.06); }

/* ---------- 主区 ---------- */
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 28px;
  border-bottom: 1px solid var(--color-border);
  background: color-mix(in srgb, var(--color-bg) 88%, transparent);
  backdrop-filter: blur(8px);
  position: sticky;
  top: 0;
  z-index: 10;
}
.crumb {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-faint);
}
.top-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 22px;
  letter-spacing: -0.01em;
  line-height: 1.15;
}
.top-right { display: flex; align-items: center; gap: 14px; }
.env-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-good);
  background: var(--color-sage-soft);
  padding: 7px 13px;
  border-radius: var(--radius-pill);
  white-space: nowrap;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 26px 28px 40px;
}

.view-enter-active,
.view-leave-active {
  transition: opacity var(--dur-base) var(--ease-out), transform var(--dur-base) var(--ease-out);
}
.view-enter-from { opacity: 0; transform: translateY(10px); }
.view-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
