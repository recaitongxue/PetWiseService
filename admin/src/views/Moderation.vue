<template>
  <section>
    <div class="toolbar" v-reveal>
      <div class="filters">
        <button class="btn sm" :class="{ ghost: f !== 'all', primary: f === 'all' }" @click="f = 'all'">全部</button>
        <button class="btn sm" :class="{ ghost: f !== 'pending', accent: f === 'pending' }" @click="f = 'pending'">
          待审核 {{ pendingCount }}
        </button>
        <button class="btn sm" :class="{ ghost: f !== 'pass', primary: f === 'pass' }" @click="f = 'pass'">已通过</button>
      </div>
      <span class="tip-chip">
        <AppIcon name="sparkle" :size="13" /> 敏感词初筛已自动命中 1 条
      </span>
    </div>

    <div class="mod-list">
      <article v-for="p in list" :key="p.id" class="card mod" v-reveal>
        <div class="mod-main">
          <div class="mod-head">
            <span class="a-ava">{{ p.author.slice(0, 1) }}</span>
            <b>{{ p.author }}</b>
            <span class="time num">{{ p.time }}</span>
            <span class="badge" :class="badgeOf(p.state)" style="margin-left: auto">
              {{ stateLabel(p.state) }}
            </span>
          </div>
          <p class="mod-text" :class="{ flagged: p.state === 'pending' }">{{ p.text }}</p>
          <p class="mod-meta">
            <AppIcon name="location" :size="13" /> 附图 {{ p.images }} 张 · 帖子 {{ p.id }}
          </p>
        </div>
        <div v-if="p.state === 'pending'" class="mod-actions">
          <button class="btn sm primary" @click="act(p, 'pass')"><AppIcon name="check" :size="14" /> 通过</button>
          <button class="btn sm danger" @click="act(p, 'reject')"><AppIcon name="ban" :size="14" /> 驳回</button>
        </div>
      </article>
      <p v-if="!list.length" class="empty">该分类下暂无内容</p>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { posts } from '@/data/admin'
import { showToast } from '@/composables/toast'

const f = ref('all')
const rows = ref(posts.map((p) => ({ ...p })))

const pendingCount = computed(() => rows.value.filter((p) => p.state === 'pending').length)
const list = computed(() => rows.value.filter((p) => f.value === 'all' || p.state === f.value))

function badgeOf(s) {
  return { pass: 'good', pending: 'watch', reject: 'alert' }[s] || 'neutral'
}
function stateLabel(s) {
  return { pass: '已通过', pending: '待审核', reject: '已驳回' }[s] || s
}
function act(p, kind) {
  p.state = kind === 'pass' ? 'pass' : 'reject'
  showToast(kind === 'pass' ? '已通过该内容' : '已驳回并通知作者', {
    type: kind === 'pass' ? 'success' : 'default'
  })
}
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.filters { display: flex; gap: 8px; }
.tip-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  padding: 7px 13px;
  border-radius: var(--radius-pill);
}
.mod-list { display: flex; flex-direction: column; gap: 12px; }
.mod { display: flex; align-items: flex-start; gap: 18px; }
.mod-main { flex: 1; min-width: 0; }
.mod-head { display: flex; align-items: center; gap: 9px; }
.a-ava {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 14px;
  background: var(--grad-sand, linear-gradient(150deg, #efe6d2, #d8c6a3));
  flex-shrink: 0;
}
.mod-head b { font-size: 14px; }
.time { font-size: 12px; color: var(--color-faint); }
.mod-text {
  margin: 9px 0 6px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-ink-2);
}
.mod-text.flagged { color: var(--color-alert); }
.mod-meta {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--color-faint);
}
.mod-actions { display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; }
.empty { text-align: center; color: var(--color-muted); padding: 26px 0; font-size: 14px; }
</style>
