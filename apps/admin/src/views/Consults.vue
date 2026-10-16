<template>
  <section>
    <div class="toolbar" v-reveal>
      <label class="search">
        <AppIcon name="search" :size="16" />
        <input v-model.trim="kw" type="search" placeholder="搜索用户 / 主题…" />
      </label>
      <div class="filters">
        <button
          v-for="s in STATES"
          :key="s.key"
          class="btn sm"
          :class="state === s.key ? (s.key === 'all' ? 'primary' : 'accent') : 'ghost'"
          @click="state = s.key"
        >
          {{ s.label }}
        </button>
      </div>
      <span class="tip-chip">
        <AppIcon name="stethoscope" :size="13" /> 待回复 {{ pendingCount }} 条
      </span>
    </div>

    <article class="card" v-reveal="{ delay: 60 }">
      <table class="table">
        <thead>
          <tr>
            <th>编号</th><th>用户</th><th>宠物</th><th>问诊主题</th><th>接诊医生</th><th>方式</th><th>时间</th><th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in list" :key="c.id">
            <td class="num muted">{{ c.id }}</td>
            <td>{{ c.user }}</td>
            <td>{{ c.pet }}</td>
            <td><b>{{ c.topic }}</b></td>
            <td>{{ c.doctor }}</td>
            <td><span class="model">{{ c.mode }}</span></td>
            <td class="num muted">{{ c.time }}</td>
            <td>
              <span class="badge" :class="stateBadge(c.state)">{{ stateLabel(c.state) }}</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!list.length" class="empty">没有匹配的问诊记录</p>
    </article>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { adminApi } from '@/api'
import { showToast } from '@shared/toast'

// 状态筛选：后端 ConsultOrder.state = pending | replied | closed
const STATES = [
  { key: 'all', label: '全部' },
  { key: 'pending', label: '待回复' },
  { key: 'replied', label: '已回复' },
  { key: 'closed', label: '已结束' }
]
const MODE_LABEL = { text: '图文', voice: '语音', video: '视频' }

const kw = ref('')
const state = ref('all')
const rows = ref([])

function toRow(c) {
  return {
    id: c.id,
    user: c.userName || '—',
    pet: c.petName || '—',
    topic: c.summary || '—',
    doctor: c.doctorName || '—',
    mode: MODE_LABEL[c.mode] || c.mode || '—',
    time: c.createdAt || '',
    state: c.state
  }
}

async function loadConsults() {
  try {
    const res = await adminApi.consults(state.value)
    rows.value = (res?.list || []).map(toRow)
  } catch (e) {
    showToast(e?.message || '问诊单加载失败', { type: 'warn' })
    rows.value = []
  }
}

watch(state, loadConsults)
onMounted(loadConsults)

const pendingCount = computed(() => rows.value.filter((c) => c.state === 'pending').length)

// 搜索在本地结果内过滤（后端 consults 接口不提供关键字参数）
const list = computed(() =>
  rows.value.filter((c) => !kw.value || c.user.includes(kw.value) || c.topic.includes(kw.value))
)

function stateBadge(s) {
  return { pending: 'watch', replied: 'good', closed: 'neutral' }[s] || 'neutral'
}
function stateLabel(s) {
  return { pending: '待回复', replied: '已回复', closed: '已结束' }[s] || s || '—'
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
.filters { display: flex; gap: 8px; flex-wrap: wrap; }
.tip-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #a66e14;
  background: #f7e8cb;
  padding: 7px 13px;
  border-radius: var(--radius-pill);
}
.muted { color: var(--color-faint); }
.model {
  font-size: 12px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-2);
  color: var(--color-ink-2);
}
.empty { text-align: center; color: var(--color-muted); padding: 26px 0; font-size: 14px; }
</style>
