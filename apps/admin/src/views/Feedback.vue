<template>
  <section>
    <div class="toolbar" v-reveal>
      <div class="filters">
        <button class="btn sm" :class="{ ghost: f !== 'all', primary: f === 'all' }" @click="f = 'all'">全部</button>
        <button class="btn sm" :class="{ ghost: f !== 'pending', accent: f === 'pending' }" @click="f = 'pending'">
          待处理 {{ pendingCount }}
        </button>
        <button class="btn sm" :class="{ ghost: f !== 'processing', accent: f === 'processing' }" @click="f = 'processing'">处理中</button>
        <button class="btn sm" :class="{ ghost: f !== 'resolved', primary: f === 'resolved' }" @click="f = 'resolved'">已处理</button>
        <button class="btn sm" :class="{ ghost: f !== 'rejected', primary: f === 'rejected' }" @click="f = 'rejected'">已驳回</button>
      </div>
      <span class="tip-chip">
        <AppIcon name="bell" :size="13" /> 来自 App「意见反馈」，处理后用户端可见状态
      </span>
    </div>

    <div class="fb-list">
      <article v-for="fb in list" :key="fb.id" class="card fb" v-reveal>
        <div class="fb-main">
          <div class="fb-head">
            <span class="a-ava">{{ (fb.userName || '匿').slice(0, 1) }}</span>
            <b>{{ fb.userName }}</b>
            <span class="type-chip" :class="fb.type">{{ typeLabel(fb.type) }}</span>
            <span class="time num">{{ fb.createdAt }}</span>
            <span v-if="fb.contact" class="time num">联系方式 {{ fb.contact }}</span>
            <span class="badge" :class="badgeClass(fb.status)" style="margin-left: auto">
              {{ statusLabel(fb.status) }}
            </span>
          </div>
          <p class="fb-text">{{ fb.content }}</p>
        </div>
        <div v-if="fb.status === 'pending' || fb.status === 'processing'" class="fb-actions">
          <button class="btn sm primary" @click="handle(fb, 'resolved')"><AppIcon name="check" :size="14" /> 标记已处理</button>
          <button class="btn sm danger" @click="handle(fb, 'rejected')"><AppIcon name="x" :size="13" /> 驳回</button>
        </div>
      </article>
      <p v-if="!list.length" class="empty">{{ loading ? '加载中…' : '该分类下暂无反馈' }}</p>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { adminApi } from '@/api'
import { showToast } from '@shared/toast'

const f = ref('all')
const list = ref([])
const pendingCount = ref(0)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    // 分页信封：数组在 res.list；state 传 'all' 时后端不做状态过滤
    const [res, pend] = await Promise.all([adminApi.feedbacks(f.value), adminApi.feedbacks('pending')])
    list.value = res?.list ?? []
    pendingCount.value = Number(pend?.total) || 0
  } catch (e) {
    showToast(e?.message || '反馈加载失败', { type: 'warn' })
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(f, load)

async function handle(fb, status) {
  try {
    await adminApi.handleFeedback(fb.id, { status })
    showToast(status === 'resolved' ? '反馈已标记为处理完成' : '反馈已驳回', { type: 'success' })
    await load()
  } catch (e) {
    showToast(e?.message || '操作失败', { type: 'warn' })
  }
}

const TYPE_LABEL = { bug: '问题', suggestion: '建议', complaint: '投诉', other: '其他' }
const STATUS_MAP = {
  pending: { label: '待处理', cls: 'watch' },
  processing: { label: '处理中', cls: 'watch' },
  resolved: { label: '已处理', cls: 'good' },
  rejected: { label: '已驳回', cls: 'neutral' }
}
function typeLabel(t) {
  return TYPE_LABEL[t] || t
}
function statusLabel(s) {
  return STATUS_MAP[s]?.label || '待处理'
}
function badgeClass(s) {
  return STATUS_MAP[s]?.cls || 'watch'
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
.type-chip.complaint { color: var(--color-alert); background: var(--color-alert-soft, rgba(200, 60, 40, 0.1)); }
.fb-text {
  margin: 9px 0 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-ink-2);
}
.fb-actions { display: flex; gap: 8px; flex-shrink: 0; }
.empty { text-align: center; color: var(--color-muted); padding: 26px 0; font-size: 14px; }
</style>
