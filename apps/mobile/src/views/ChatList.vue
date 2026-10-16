<template>
  <section class="screen">
    <header class="screen-head" v-reveal>
      <div>
        <p class="eyebrow">MESSAGES</p>
        <h1 class="title">消息</h1>
      </div>
      <router-link to="/contacts" class="icon-btn" type="button" aria-label="通讯录">
        <AppIcon name="user" :size="22" />
      </router-link>
    </header>

    <!-- 搜索：按昵称或最近消息过滤 -->
    <div class="search" v-reveal="{ delay: 40 }">
      <AppIcon name="search" :size="16" />
      <input v-model="q" class="search-input" type="search" placeholder="搜索联系人或消息" />
      <button v-if="q" class="search-clear" type="button" aria-label="清空" @click="q = ''">
        <AppIcon name="x" :size="14" />
      </button>
    </div>

    <!-- 通讯录入口：三组联系人直达 -->
    <router-link to="/contacts" class="gate-row" v-reveal="{ delay: 60 }">
      <span class="gate-ic"><AppIcon name="user" :size="19" /></span>
      <span class="gate-label">通讯录</span>
      <span class="gate-count num">{{ contactCount }} 位联系人</span>
      <AppIcon name="back" :size="14" class="gate-arrow" />
    </router-link>

    <ul class="conv-list">
      <li v-for="c in visibleConvs" :key="c.id" v-reveal>
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

    <p v-if="!visibleConvs.length" class="empty">没有匹配的会话</p>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { fetchConversations, fetchContactGroups } from '@/api/data'
import { showToast } from '@shared/toast'

const q = ref('')

// 后端分组返回 {id, title, count, members}；模板沿用 label/icon，这里做一次归一化
const GROUP_META = {
  friend: { label: '我的好友', icon: 'user' },
  vet: { label: '我的兽医', icon: 'stethoscope' },
  group: { label: '宠物社群', icon: 'chat' }
}

const conversations = ref([])
const contactGroups = ref([])

const contactCount = computed(() =>
  contactGroups.value.reduce((s, g) => s + (g.members?.length || 0), 0)
)

const visibleConvs = computed(() => {
  const kw = q.value.trim().toLowerCase()
  if (!kw) return conversations.value
  return conversations.value.filter(
    (c) =>
      (c.name || '').toLowerCase().includes(kw) || (c.last || '').toLowerCase().includes(kw)
  )
})

function kindLabel(k) {
  return { vet: '兽医', group: '群聊', friend: '好友' }[k] || ''
}

function initial(name) {
  return (name || '?').slice(0, 1)
}

onMounted(async () => {
  try {
    const [convs, contactRes] = await Promise.all([fetchConversations(), fetchContactGroups()])
    conversations.value = convs || []
    contactGroups.value = (contactRes?.groups || []).map((g) => ({
      id: g.id,
      label: GROUP_META[g.id]?.label || g.title || g.id,
      icon: GROUP_META[g.id]?.icon || 'user',
      members: g.members || []
    }))
  } catch (e) {
    showToast(e?.message || '消息列表加载失败', { type: 'error' })
  }
})
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

/* 搜索 */
.search {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding: 11px 14px;
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  color: var(--color-faint);
}
.search-input {
  flex: 1;
  min-width: 0;
  border: none;
  background: transparent;
  font: inherit;
  font-size: 14.5px;
  color: var(--color-ink);
  outline: none;
}
.search-input::-webkit-search-cancel-button { display: none; }
.search-clear {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-surface-2);
  color: var(--color-muted);
  flex-shrink: 0;
}
.empty {
  text-align: center;
  color: var(--color-muted);
  font-size: 14px;
  padding: 30px 0;
}

/* ---------- 通讯录入口行 ---------- */
.gate-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 14px;
  padding: 13px 14px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
  transition: transform var(--dur-fast) var(--ease-out);
}
.gate-row:active { transform: scale(0.978); }
.gate-ic {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: var(--color-sage-soft);
  color: var(--color-good);
  flex-shrink: 0;
}
.gate-label { flex: 1; font-weight: 700; font-size: 15px; }
.gate-count { font-size: 11px; font-weight: 700; color: var(--color-faint); }
.gate-arrow { color: var(--color-faint); transform: rotate(180deg); flex-shrink: 0; }

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
