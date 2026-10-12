<template>
  <section class="screen">
    <header class="screen-head" v-reveal>
      <div>
        <p class="eyebrow">MESSAGES</p>
        <h1 class="title">消息</h1>
      </div>
      <button class="icon-btn" type="button" aria-label="搜索">
        <AppIcon name="search" :size="22" />
      </button>
    </header>

    <ul class="conv-list">
      <li v-for="c in conversations" :key="c.id" v-reveal>
        <router-link :to="`/chat/${c.id}`" class="conv">
          <span class="conv-avatar">
            {{ initial(c.name) }}
            <span v-if="c.online" class="online"></span>
          </span>
          <div class="conv-main">
            <div class="conv-row">
              <span class="conv-name">{{ c.name }}</span>
              <span class="conv-time num">{{ c.time }}</span>
            </div>
            <div class="conv-row">
              <span class="conv-last">{{ c.last }}</span>
              <span v-if="c.unread" class="conv-unread num">{{ c.unread }}</span>
            </div>
          </div>
          <span class="conv-kind" :class="c.kind">{{ kindLabel(c.kind) }}</span>
        </router-link>
      </li>
    </ul>
  </section>
</template>

<script setup>
import AppIcon from '@/components/icons/AppIcon.vue'
import { conversations } from '@/data/mock'

function kindLabel(k) {
  return { vet: '兽医', group: '群聊', friend: '好友' }[k] || ''
}

function initial(name) {
  return (name || '?').slice(0, 1)
}
</script>

<style scoped>
.title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-2xl);
  letter-spacing: -0.02em;
  line-height: 1;
}
.icon-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-ink);
}
.conv-list {
  margin-top: 14px;
}
.conv {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 4px;
  border-bottom: 1px solid var(--color-border);
  transition: background var(--dur-fast);
}
.conv:active { background: var(--color-surface-2); }
.conv-avatar {
  position: relative;
  width: 52px;
  height: 52px;
  border-radius: 30%;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 22px;
  color: var(--color-ink);
  background: var(--grad-sand);
  flex-shrink: 0;
}
.online {
  position: absolute;
  right: 0;
  bottom: 2px;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: var(--color-good);
  border: 2.5px solid var(--color-bg);
}
.conv-main { flex: 1; min-width: 0; }
.conv-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.conv-name { font-weight: 700; font-size: 16px; }
.conv-time { font-size: 12px; color: var(--color-muted); }
.conv-last {
  font-size: 13px;
  color: var(--color-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-unread {
  flex-shrink: 0;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--color-accent);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: grid;
  place-items: center;
}
.conv-kind {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: var(--radius-pill);
  color: var(--color-muted);
  background: var(--color-surface-2);
}
.conv-kind.vet { color: var(--color-accent-ink); background: var(--color-accent-soft); }
</style>
