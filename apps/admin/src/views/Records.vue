<template>
  <section>
    <div class="toolbar" v-reveal>
      <label class="search">
        <AppIcon name="search" :size="16" />
        <input v-model.trim="kw" type="search" placeholder="搜索用户 / 品种…" />
      </label>
      <span class="tip-chip">
        <AppIcon name="eye" :size="13" /> 置信度低于 0.60 自动标记复核
      </span>
    </div>

    <!-- 筛选与数据集导出 -->
    <div class="filter-bar" v-reveal="{ delay: 40 }">
      <div class="tabs">
        <button
          v-for="t in tabs"
          :key="t.key"
          class="tab"
          type="button"
          :class="{ on: tab === t.key }"
          @click="tab = t.key"
        >
          {{ t.label }}
          <i v-if="t.key !== 'all'" class="num">{{ countOf(t.key) }}</i>
        </button>
      </div>
      <button class="export-btn" type="button" :disabled="!approvedCount" @click="exportDataset">
        <AppIcon name="doc" :size="14" /> 导出训练数据集（{{ approvedCount }}）
      </button>
    </div>

    <article class="card" v-reveal="{ delay: 80 }">
      <table class="table">
        <thead>
          <tr>
            <th>编号</th><th>用户</th><th>识别结果</th><th>纠正来源</th><th>置信度</th><th>时间</th><th>状态</th><th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in list" :key="r.id">
            <td class="num muted">{{ r.id }}</td>
            <td>{{ r.user }}</td>
            <td><b>{{ r.breed }}</b></td>
            <td>
              <span v-if="r.corrected" class="predicted">模型预测「{{ r.predicted }}」</span>
              <span v-else class="muted">—</span>
            </td>
            <td>
              <span class="conf-track">
                <span class="conf-bar" :style="{ width: r.conf * 100 + '%' }" :class="confState(r.conf)"></span>
              </span>
              <b class="num conf-num">{{ Math.round(r.conf * 100) }}%</b>
            </td>
            <td class="num muted">{{ r.time }}</td>
            <td>
              <span class="badge" :class="badgeOf(r.state)">{{
                r.state === 'review' ? ((r.predicted && r.predicted !== r.breed) ? '纠正待审核' : '低置信待审') : stateLabel(r.state)
              }}</span>
            </td>
            <td>
              <template v-if="r.state === 'review'">
                <button class="op pass" type="button" @click="review(r.id, true)">通过</button>
                <button class="op reject" type="button" @click="review(r.id, false)">驳回</button>
              </template>
              <span v-else class="muted op-none">—</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!list.length" class="empty">没有匹配的记录</p>
    </article>

    <p class="foot-note" v-reveal>
      审核通过的纠正样本将汇入训练数据集（含图片引用、模型预测与人工标签），
      按周导出后在 <code>cv/</code> 增量训练，实现「用户纠正 → 审核 → 数据回流」闭环。
    </p>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { recognitions as seedRecognitions } from '@/data/admin'
import { showToast } from '@/composables/toast'

const RECOG_KEY = 'petwise_recognitions' // 与 App 端共用：用户在识别页的手动纠正写入此键
const kw = ref('')
const tab = ref('all')

// 读取 App 端写入的识别记录，转成管理端行格式
function readAppRecords() {
  try {
    const rows = JSON.parse(localStorage.getItem(RECOG_KEY) || '[]')
    if (!Array.isArray(rows)) return []
    return rows.map((r) => ({
      id: r.id,
      user: '当前用户',
      pet: r.species === 'dog' ? '犬' : '猫',
      breed: r.corrected || r.predicted,
      predicted: r.predicted,
      corrected: Boolean(r.corrected),
      conf: r.confidence,
      time: new Date(r.time).toLocaleString('zh-CN', { hour12: false }).slice(5, 16),
      state: r.status
    }))
  } catch (e) {
    return []
  }
}

const rows = ref([...readAppRecords(), ...seedRecognitions])

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'review', label: '纠正待审核' },
  { key: 'approved', label: '已采纳' }
]

function countOf(state) {
  return rows.value.filter((r) => r.state === state).length
}

const approvedCount = computed(() => countOf('approved'))

const list = computed(() => {
  let out = rows.value
  if (tab.value !== 'all') out = out.filter((r) => r.state === tab.value)
  if (kw.value) {
    const k = kw.value
    out = out.filter((r) => r.user.includes(k) || r.breed.includes(k) || (r.predicted || '').includes(k))
  }
  return out
})

function confState(c) {
  if (c >= 0.85) return 'good'
  if (c >= 0.6) return 'mid'
  return 'low'
}
function badgeOf(s) {
  return { done: 'good', review: 'watch', failed: 'alert', approved: 'ok', rejected: 'neutral' }[s] || 'neutral'
}
function stateLabel(s) {
  return (
    { done: '已完成', review: '纠正待审核', failed: '识别失败', approved: '已采纳', rejected: '已驳回' }[s] || s
  )
}

// 审核：通过 → approved（进数据集）；驳回 → rejected（维持模型原预测）
function review(id, pass) {
  const row = rows.value.find((r) => r.id === id)
  if (!row) return
  row.state = pass ? 'approved' : 'rejected'
  if (!pass) {
    // 驳回后展示回模型原预测
    row.breed = row.predicted || row.breed
    row.corrected = false
  }
  // 同步写回共享键，App 端状态徽标随之更新
  try {
    const app = JSON.parse(localStorage.getItem(RECOG_KEY) || '[]')
    const hit = app.find((r) => r.id === id)
    if (hit) {
      hit.status = row.state
      if (!pass) hit.corrected = null
      localStorage.setItem(RECOG_KEY, JSON.stringify(app))
    }
  } catch (e) { /* 静态演示行不落盘 */ }
  showToast(pass ? `已通过「${row.breed}」，计入训练数据集` : '已驳回，维持模型原预测', { type: pass ? 'success' : 'warn' })
}

// 导出审核通过的样本为训练数据集（JSON：图片引用 + 人工标签）
function exportDataset() {
  const samples = rows.value
    .filter((r) => r.state === 'approved')
    .map((r) => ({
      image_ref: r.id,
      species: r.pet === '犬' ? 'dog' : 'cat',
      label: r.breed,
      model_predicted: r.predicted || r.breed,
      model_confidence: r.conf,
      source: 'user_correction',
      reviewed: true
    }))
  const blob = new Blob([JSON.stringify({ dataset: 'petwise-corrections', count: samples.length, samples }, null, 2)], {
    type: 'application/json'
  })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `petwise-corrections-${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(a.href)
  showToast(`已导出 ${samples.length} 条样本`, { type: 'success' })
}
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 12px;
  flex-wrap: wrap;
}
.search {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  padding: 8px 16px;
  color: var(--color-muted);
  flex: 1;
  min-width: 220px;
}
.search input {
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: var(--color-ink);
  width: 100%;
}
.tip-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-muted);
  background: var(--color-surface-2);
  padding: 7px 13px;
  border-radius: var(--radius-pill);
  white-space: nowrap;
}
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.tabs { display: flex; gap: 8px; }
.tab {
  padding: 7px 14px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-muted);
}
.tab.on {
  background: var(--color-ink);
  border-color: var(--color-ink);
  color: var(--color-surface);
}
.tab i {
  font-style: normal;
  font-size: 11px;
  margin-left: 4px;
  opacity: 0.75;
}
.export-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 15px;
  border-radius: var(--radius-pill);
  border: 1px solid transparent;
  background: var(--color-pine, #2d4a3e);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}
.export-btn:disabled { opacity: 0.45; }
.muted { color: var(--color-faint); }
.predicted {
  font-size: 12px;
  color: var(--color-muted);
}
.conf-track {
  display: inline-block;
  width: 90px;
  height: 8px;
  border-radius: 999px;
  background: var(--color-surface-2);
  overflow: hidden;
  vertical-align: middle;
  margin-right: 8px;
}
.conf-bar { display: block; height: 100%; border-radius: 999px; }
.conf-bar.good { background: var(--color-good); }
.conf-bar.mid { background: var(--color-sage); }
.conf-bar.low { background: var(--color-alert); }
.conf-num { font-size: 13px; }
.op {
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 600;
  margin-right: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-ink);
}
.op.pass {
  background: var(--color-sage-soft, #e8f0e9);
  border-color: transparent;
  color: var(--color-pine, #2d4a3e);
}
.op.reject {
  background: var(--color-surface-2);
  color: var(--color-muted);
}
.op-none { font-size: 12px; }
.empty { text-align: center; color: var(--color-muted); padding: 26px 0; font-size: 14px; }
.foot-note {
  margin-top: 14px;
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--color-muted);
}
.foot-note code {
  background: var(--color-surface-2);
  padding: 1px 7px;
  border-radius: 6px;
  font-size: 11.5px;
}
</style>
