<template>
  <section>
    <!-- 举报处理：数据来自后端 GET /admin/reports + PATCH /admin/reports/{id} -->
    <div class="toolbar" v-reveal>
      <div class="filters">
        <button class="btn sm" :class="{ ghost: rf !== 'pending', accent: rf === 'pending' }" @click="rf = 'pending'">
          待处理 {{ pendingReports }}
        </button>
        <button class="btn sm" :class="{ ghost: rf !== 'all', primary: rf === 'all' }" @click="rf = 'all'">全部记录</button>
      </div>
      <span class="tip-chip muted">
        <AppIcon name="location" :size="13" /> 数据来自 App 端用户举报，处理后用户端可见状态
      </span>
    </div>

    <div class="mod-list">
      <article v-for="r in reportList" :key="r.id" class="card mod" v-reveal>
        <div class="mod-main">
          <div class="mod-head">
            <span class="a-ava alert">{{ r.author.slice(0, 1) || '匿' }}</span>
            <b>{{ r.author || '匿名用户' }}</b>
            <span class="time num">{{ r.time }}</span>
            <span class="badge" :class="reportBadge(r.state)" style="margin-left: auto">
              {{ reportLabel(r.state) }}
            </span>
          </div>
          <p class="mod-text">
            被举报动态 <b class="num">{{ r.postId }}</b>
          </p>
          <p class="mod-meta">
            <span class="reason-chip">{{ r.reason }}</span>
            举报人 <b class="num">{{ r.reporter }}</b>
          </p>
          <p v-if="r.text" class="mod-detail">被举报内容：{{ r.text }}</p>
          <p v-if="r.detail" class="mod-detail">补充说明：{{ r.detail }}</p>
        </div>
        <div v-if="r.state === 'pending'" class="mod-actions">
          <button class="btn sm danger" @click="handle(r, 'resolved')"><AppIcon name="ban" :size="14" /> 下架内容</button>
          <button class="btn sm ghost" @click="handle(r, 'rejected')">驳回举报</button>
        </div>
        <div v-else class="mod-actions">
          <span class="done-note">{{ r.state === 'resolved' ? '内容已下架，举报人已反馈' : '经核实举报不成立，已驳回' }}</span>
          <button class="btn sm ghost" @click="handle(r, 'pending')">恢复待处理</button>
        </div>
      </article>
      <div v-if="!reportList.length" class="empty-box">
        <AppIcon name="shield" :size="30" />
        <p>暂无待处理举报</p>
        <span>App 端用户提交的举报会实时出现在这里</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { adminApi } from '@/api'
import { showToast } from '@shared/toast'

// ---- 举报处理：后端 GET /admin/reports + PATCH /admin/reports/{id} ----
// 后端字段：{id, postId, postAuthor, postText, userId, reason, note, status, createdAt}
const REASON_LABEL = {
  spam: '广告垃圾',
  abuse: '辱骂攻击',
  inappropriate: '不宜内容',
  other: '其他'
}

const rf = ref('pending')
const reports = ref([])

function toReport(r) {
  return {
    id: r.id,
    postId: r.postId || '—',
    author: r.postAuthor || '',
    text: r.postText || '',
    reporter: r.userId ? String(r.userId) : '匿名',
    reason: REASON_LABEL[r.reason] || r.reason || '其他',
    detail: r.note || '',
    time: r.createdAt || '',
    state: r.status
  }
}

async function loadReports() {
  try {
    const res = await adminApi.reports(rf.value === 'all' ? undefined : 'pending')
    reports.value = (res?.list || []).map(toReport)
  } catch (e) {
    showToast(e?.message || '举报列表加载失败', { type: 'warn' })
    reports.value = []
  }
}

watch(rf, loadReports)
onMounted(loadReports)

const pendingReports = computed(() => reports.value.filter((r) => r.state === 'pending').length)
const reportList = computed(() => reports.value)

function reportBadge(s) {
  return { pending: 'watch', resolved: 'alert', rejected: 'neutral' }[s] || 'neutral'
}
function reportLabel(s) {
  return { pending: '待处理', resolved: '已下架', rejected: '举报驳回' }[s] || s || '—'
}

// 通过（下架内容）/ 驳回（举报不成立）/ 恢复待处理
async function handle(r, status) {
  try {
    await adminApi.handleReport(r.id, { status })
    showToast(
      { resolved: '已下架被举报内容并反馈举报人', rejected: '已驳回该举报', pending: '已恢复为待处理' }[
        status
      ] || '举报已处理',
      { type: status === 'rejected' || status === 'pending' ? 'default' : 'success' }
    )
    await loadReports()
  } catch (e) {
    showToast(e?.message || '举报处理失败', { type: 'warn' })
  }
}
</script>

<style scoped>
/* ---------- Tab 栏 ---------- */
.tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.tab {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink-2);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease-out);
}
.tab:hover { border-color: var(--color-border-strong); }
.tab.on {
  background: var(--color-ink);
  border-color: var(--color-ink);
  color: #fff;
}
.tab.on .app-icon { color: var(--color-accent); }
.tab-num {
  font-size: 12px;
  padding: 1px 8px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-2);
  color: var(--color-muted);
}
.tab.on .tab-num { background: rgba(255, 255, 255, 0.16); color: #fff; }
.tab-num.hot { background: rgba(200, 67, 31, 0.14); color: var(--color-alert); }

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
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  padding: 7px 13px;
  border-radius: var(--radius-pill);
}
.tip-chip.muted {
  color: var(--color-muted);
  background: var(--color-surface-2);
}
.mod-list { display: flex; flex-direction: column; gap: 12px; }
.mod { display: flex; align-items: flex-start; gap: 18px; }
.mod-main { flex: 1; min-width: 0; }
.mod-head { display: flex; align-items: center; gap: 9px; flex-wrap: wrap; }
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
.a-ava.alert { background: rgba(200, 67, 31, 0.12); color: var(--color-alert); }
.mod-head b { font-size: 14px; }
.time { font-size: 12px; color: var(--color-faint); }
.mod-text {
  margin: 9px 0 6px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-ink-2);
}
.mod-meta {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--color-faint);
  flex-wrap: wrap;
}
.mod-detail {
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-ink-2);
  background: var(--color-surface-2);
  border-radius: var(--radius-sm);
  padding: 8px 11px;
  line-height: 1.6;
}
.mod-actions { display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; }
.done-note { font-size: 12px; color: var(--color-faint); max-width: 130px; text-align: right; }

.reason-chip {
  padding: 2px 9px;
  border-radius: var(--radius-pill);
  background: var(--color-accent-soft);
  color: var(--color-accent-ink);
  font-weight: 700;
}

.empty { text-align: center; color: var(--color-muted); padding: 26px 0; font-size: 14px; }
.empty-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  padding: 46px 0 40px;
  color: var(--color-faint);
}
.empty-box .app-icon { color: var(--color-sage); }
.empty-box p { font-size: 15px; font-weight: 600; color: var(--color-muted); }
.empty-box span { font-size: 12px; }
</style>
