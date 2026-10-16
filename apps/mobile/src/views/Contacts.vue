<template>
  <section class="screen">
    <header class="screen-head" v-reveal>
      <div>
        <p class="eyebrow">CONTACTS</p>
        <h1 class="title">通讯录</h1>
      </div>
      <button class="icon-btn" type="button" aria-label="添加联系人" @click="addContact">
        <AppIcon name="plus" :size="22" />
      </button>
    </header>

    <!-- 搜索：按姓名 / 简介过滤全部联系人 -->
    <div class="search" v-reveal="{ delay: 40 }">
      <AppIcon name="search" :size="16" />
      <input v-model="q" class="search-input" type="search" placeholder="搜索联系人、兽医或社群" />
      <button v-if="q" class="search-clear" type="button" aria-label="清空" @click="q = ''">
        <AppIcon name="x" :size="14" />
      </button>
    </div>

    <!-- 快捷入口 -->
    <div class="quick-rows" v-reveal="{ delay: 70 }">
      <button class="quick-row" type="button" @click="showToast('暂无新的好友申请')">
        <span class="qr-ic coral"><AppIcon name="user" :size="18" /></span>
        <span class="qr-label">新的朋友</span>
        <span v-if="friendRequests" class="qr-badge num">{{ friendRequests }}</span>
        <AppIcon name="back" :size="14" class="qr-arrow" />
      </button>
      <router-link to="/consult/ai" class="quick-row">
        <span class="qr-ic sage"><AppIcon name="sparkle" :size="18" /></span>
        <span class="qr-label">AI 养宠助手</span>
        <span class="qr-hint">7×24 在线</span>
        <AppIcon name="back" :size="14" class="qr-arrow" />
      </router-link>
    </div>

    <!-- 联系人分组 -->
    <template v-for="g in filteredGroups" :key="g.id">
      <section v-if="g.members.length" class="c-group" v-reveal>
        <h2 class="c-group-t">
          <AppIcon :name="g.icon" :size="14" />
          {{ g.label }}
          <span class="c-count num">{{ g.members.length }}</span>
        </h2>
        <ul class="c-list">
          <li v-for="m in g.members" :key="m.id">
            <button class="c-row" type="button" @click="open(m)">
              <span class="c-ava" :class="m.kind">
                {{ initial(m.name) }}
                <i v-if="m.online" class="c-online"></i>
              </span>
              <span class="c-main">
                <span class="c-line">
                  <b class="c-name">{{ m.name }}</b>
                  <span v-if="m.kind === 'vet'" class="c-cert">
                    <AppIcon name="verified" :size="12" /> 认证兽医
                  </span>
                  <span v-else-if="m.kind === 'group'" class="c-tag">群聊</span>
                </span>
                <span class="c-bio">{{ m.bio }}</span>
              </span>
              <span class="c-go" :class="m.kind">
                <AppIcon :name="m.chatId ? 'chat' : m.doctorId ? 'stethoscope' : 'send'" :size="16" />
              </span>
            </button>
          </li>
        </ul>
      </section>
    </template>

    <p v-if="!filteredGroups.some((g) => g.members.length)" class="empty">
      没有找到相关联系人
    </p>

    <p class="c-foot num">{{ totalContacts }} 位联系人 · 点击即可开始对话</p>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import { fetchContactGroups, createConversation } from '@/api/data'
import { showToast } from '@shared/toast'

const router = useRouter()
const q = ref('')
const friendRequests = 2

// 后端分组返回 {id, title, count, members}；模板用 label/icon，这里做一次归一化
const GROUP_META = {
  friend: { label: '我的好友', icon: 'user' },
  vet: { label: '我的兽医', icon: 'stethoscope' },
  group: { label: '宠物社群', icon: 'chat' }
}
const contactGroups = ref([])

onMounted(async () => {
  try {
    const r = await fetchContactGroups()
    contactGroups.value = (r?.groups || []).map((g) => ({
      id: g.id,
      label: GROUP_META[g.id]?.label || g.title || g.id,
      icon: GROUP_META[g.id]?.icon || 'user',
      members: g.members || []
    }))
  } catch (e) {
    showToast(e?.message || '通讯录加载失败', { type: 'error' })
  }
})

const totalContacts = computed(() =>
  contactGroups.value.reduce((s, g) => s + g.members.length, 0)
)

const filteredGroups = computed(() => {
  const kw = q.value.trim().toLowerCase()
  if (!kw) return contactGroups.value
  return contactGroups.value
    .map((g) => ({
      ...g,
      members: g.members.filter(
        (m) => (m.name || '').toLowerCase().includes(kw) || (m.bio || '').toLowerCase().includes(kw)
      )
    }))
    .filter((g) => g.members.length)
})

function initial(name) {
  return (name || '?').slice(0, 1)
}

// 有会话直达聊天室；兽医看资料页；其余从通讯录发起新会话
function open(m) {
  if (m.doctorId) return router.push(`/doctor/${m.doctorId}`)
  // 有直达会话 id 的（seed 绑定的老会话）直接进；
  // 否则先调后端按联系人建/复用会话，拿到真实会话 id 再跳转
  // （联系人 id 与会话 id 是不同命名空间，不能互相顶替）
  if (m.chatId) return router.push(`/chat/${m.chatId}`)
  createConversation(m.id)
    .then((conv) => {
      if (conv?.id) router.push(`/chat/${conv.id}`)
      else showToast('无法发起会话，请稍后重试', { type: 'warn' })
    })
    .catch((e) => showToast(e?.message || '发起会话失败', { type: 'error' }))
}

function addContact() {
  showToast('演示环境：手机号添加联系人待开放')
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
.icon-btn:active { transform: scale(0.94); }

/* ---------- 搜索 ---------- */
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

/* ---------- 快捷入口 ---------- */
.quick-rows {
  margin-top: 14px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
  overflow: hidden;
}
.quick-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 13px 14px;
  text-align: left;
  transition: background var(--dur-fast);
}
.quick-row + .quick-row { border-top: 1px solid var(--hairline); }
.quick-row:active { background: var(--color-surface-2); }
.qr-ic {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}
.qr-ic.coral { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.qr-ic.sage { background: var(--color-sage-soft); color: var(--color-good); }
.qr-label { flex: 1; min-width: 0; font-weight: 700; font-size: 15px; }
.qr-hint { font-size: 11px; font-weight: 700; color: var(--color-faint); }
.qr-badge {
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
.qr-arrow { color: var(--color-faint); transform: rotate(180deg); flex-shrink: 0; }

/* ---------- 分组 ---------- */
.c-group { margin-top: 22px; }
.c-group-t {
  display: flex;
  align-items: center;
  gap: 7px;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.04em;
  color: var(--color-muted);
  margin-bottom: 8px;
  padding-left: 2px;
}
.c-count {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-faint);
  background: var(--color-surface-2);
  border-radius: var(--radius-pill);
  padding: 1px 8px;
}
.c-list {
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
  overflow: hidden;
}
.c-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 11px 14px;
  text-align: left;
  transition: background var(--dur-fast);
}
.c-row + .c-row { border-top: 1px solid var(--hairline); }
.c-row:active { background: var(--color-surface-2); }

/* 头像：按联系人类型区分色调 */
.c-ava {
  position: relative;
  width: 46px;
  height: 46px;
  border-radius: 30%;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 19px;
  color: var(--color-ink);
  background: var(--grad-sand);
  flex-shrink: 0;
}
.c-ava.vet { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.c-ava.group { background: var(--color-sage-soft); color: var(--color-good); }
.c-online {
  position: absolute;
  right: -1px;
  bottom: -1px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-good);
  border: 2.5px solid var(--color-surface);
}

.c-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.c-line { display: flex; align-items: center; gap: 6px; min-width: 0; }
.c-name {
  font-weight: 700;
  font-size: 15.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.c-cert {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  font-weight: 700;
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  padding: 2px 7px;
  border-radius: var(--radius-pill);
  flex-shrink: 0;
}
.c-tag {
  font-size: 10px;
  font-weight: 700;
  color: var(--color-good);
  background: var(--color-sage-soft);
  padding: 2px 7px;
  border-radius: var(--radius-pill);
  flex-shrink: 0;
}
.c-bio {
  font-size: 12.5px;
  color: var(--color-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.c-go { color: var(--color-faint); flex-shrink: 0; display: grid; place-items: center; }
.c-go.vet { color: var(--color-accent-ink); }

.empty {
  text-align: center;
  color: var(--color-muted);
  font-size: 14px;
  padding: 30px 0;
}
.c-foot {
  text-align: center;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--color-faint);
  margin-top: 26px;
}
</style>
