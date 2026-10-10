<template>
  <section>
    <div class="toolbar" v-reveal>
      <div class="filters">
        <button class="btn sm" :class="{ ghost: f !== 'all', primary: f === 'all' }" @click="f = 'all'">全部</button>
        <button class="btn sm" :class="{ ghost: f !== 'open', accent: f === 'open' }" @click="f = 'open'">
          待处理 {{ openCount }}
        </button>
        <button class="btn sm" :class="{ ghost: f !== 'resolved', primary: f === 'resolved' }" @click="f = 'resolved'">已处理</button>
      </div>
      <span class="tip-chip">
        <AppIcon name="bell" :size="13" /> 来自 App「意见反馈」，处理后用户端可见状态
      </span>
    </div>

    <div class="fb-list">
      <article v-for="fb in list" :key="fb.id" class="card fb" v-reveal>
        <div class="fb-main">
          <div class="fb-head">
            <span class="a-ava">{{ fb.user.slice(0, 1) }}</span>
            <b>{{ fb.user }}</b>
            <span class="type-chip" :class="fb.type">{{ typeLabel(fb.type) }}</span>
            <span class="time num">{{ fb.time }}</span>
            <span class="badge" :class="fb.state === 'open' ? 'watch' : 'good'" style="margin-left: auto">
              {{ fb.state === 'open' ? '待处理' : '已处理' }}
            </span>
          </div>
          <p class="fb-text">{{ fb.text }}</p>
        </div>
        <div v-if="fb.state === 'open'" class="fb-actions">
          <button class="btn sm primary" @click="resolve(fb)"><AppIcon name="check" :size="14" /> 标记已处理</button>
        </div>
      </article>
      <p v-if="!list.length" class="empty">该分类下暂无反馈</p>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { loadFeedbacks, saveFeedbacks } from '@/data/ops'
import { showToast } from '@/composables/toast'

const f = ref('all')
const rows = ref(loadFeedbacks())

const openCount = computed(() => rows.value.filter((x) => x.state === 'open').length)
const list = computed(() => rows.value.filter((x) => f.value === 'all' || x.state === f.value))

function persist() {
  saveFeedbacks(rows.value.map((x) => ({ ...x })))
}

function resolve(fb) {
  fb.state = 'resolved'
  persist()
  showToast('反馈已标记为处理完成', { type: 'success' })
}

function typeLabel(t) {
  return { bug: '问题', suggestion: '建议', other: '其他' }[t] || t
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
.fb-list { display: flex; flex-direction: column; gap: 12px; }
.fb { display: flex; align-items: flex-start; gap: 18px; }
.fb-main { flex: 1; min-width: 0; }
.fb-head { display: flex; align-items: center; gap: 9px; flex-wrap: wrap; }
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
.fb-head b { font-size: 14px; }
.time { font-size: 12px; color: var(--color-faint); }
.type-chip {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: var(--radius-pill);
}
.type-chip.bug { color: var(--color-alert); background: var(--color-alert-soft, rgba(200, 60, 40, 0.1)); }
.type-chip.suggestion { color: var(--color-good); background: var(--color-sage-soft); }
.type-chip.other { color: var(--color-muted); background: var(--color-sage-soft); }
.fb-text {
  margin: 9px 0 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-ink-2);
}
.fb-actions { display: flex; flex-shrink: 0; }
.empty { text-align: center; color: var(--color-muted); padding: 26px 0; font-size: 14px; }
</style>
