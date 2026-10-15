<template>
  <section>
    <!-- 双 Tab：内容审核 / 举报处理 -->
    <div class="tabs" v-reveal>
      <button class="tab" :class="{ on: tab === 'posts' }" @click="tab = 'posts'">
        <AppIcon name="shield" :size="15" /> 内容审核
        <span class="tab-num num">{{ pendingPosts }}</span>
      </button>
      <button class="tab" :class="{ on: tab === 'reports' }" @click="tab = 'reports'">
        <AppIcon name="alert" :size="15" /> 举报处理
        <span class="tab-num num" :class="{ hot: pendingReports }">{{ pendingReports }}</span>
      </button>
    </div>

    <!-- ============ 内容审核 ============ -->
    <template v-if="tab === 'posts'">
      <div class="toolbar" v-reveal>
        <div class="filters">
          <button class="btn sm" :class="{ ghost: f !== 'all', primary: f === 'all' }" @click="f = 'all'">全部</button>
          <button class="btn sm" :class="{ ghost: f !== 'pending', accent: f === 'pending' }" @click="f = 'pending'">
            待审核 {{ pendingPosts }}
          </button>
          <button class="btn sm" :class="{ ghost: f !== 'pass', primary: f === 'pass' }" @click="f = 'pass'">已通过</button>
          <button class="btn sm" :class="{ ghost: f !== 'reject', primary: f === 'reject' }" @click="f = 'reject'">已驳回</button>
        </div>
        <span class="tip-chip">
          <AppIcon name="sparkle" :size="13" /> AI 预审已标记 {{ flaggedCount }} 条高风险内容
        </span>
      </div>

      <div class="mod-list">
        <article v-for="p in postList" :key="p.id" class="card mod" v-reveal>
          <div class="mod-main">
            <div class="mod-head">
              <span class="a-ava">{{ p.author.slice(0, 1) }}</span>
              <b>{{ p.author }}</b>
              <span class="time num">{{ p.time }}</span>
              <span class="badge" :class="badgeOf(p.state)" style="margin-left: auto">
                {{ stateLabel(p.state) }}
              </span>
            </div>
            <p class="mod-text" :class="{ flagged: p.state === 'pending' && p.ai.hit }">{{ p.text }}</p>
            <p class="mod-meta">
              <AppIcon name="location" :size="13" /> 附图 {{ p.images }} 张 · 帖子 {{ p.id }}
            </p>
            <!-- AI 预审结论：命中敏感词 → 建议驳回；未命中 → 建议通过 -->
            <div class="ai-row" :class="p.ai.hit ? 'risk' : 'safe'">
              <AppIcon name="sparkle" :size="13" />
              <span v-if="p.ai.hit">
                AI 预审：命中敏感词
                <b v-for="w in p.ai.words" :key="w" class="hit-word">{{ w }}</b>
                ，疑似{{ p.ai.kind }}，建议驳回
              </span>
              <span v-else>AI 预审：未命中风险词库，内容未见异常，建议通过</span>
            </div>
          </div>
          <div v-if="p.state === 'pending'" class="mod-actions">
            <button class="btn sm primary" @click="act(p, 'pass')"><AppIcon name="check" :size="14" /> 通过</button>
            <button class="btn sm danger" @click="act(p, 'reject')"><AppIcon name="ban" :size="14" /> 驳回</button>
          </div>
          <div v-else class="mod-actions">
            <span class="done-note">{{ p.state === 'pass' ? '已放行至社区' : '已下架并通知作者' }}</span>
          </div>
        </article>
        <p v-if="!postList.length" class="empty">该分类下暂无内容</p>
      </div>
    </template>

    <!-- ============ 举报处理 ============ -->
    <template v-else>
      <div class="toolbar" v-reveal>
        <div class="filters">
          <button class="btn sm" :class="{ ghost: rf !== 'pending', accent: rf === 'pending' }" @click="rf = 'pending'">
            待处理 {{ pendingReports }}
          </button>
          <button class="btn sm" :class="{ ghost: rf !== 'all', primary: rf === 'all' }" @click="rf = 'all'">全部记录</button>
        </div>
        <span class="tip-chip muted">
          <AppIcon name="location" :size="13" /> 数据来自 App 端用户举报，与管理台实时同键
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
            <p v-if="r.detail" class="mod-detail">补充说明：{{ r.detail }}</p>
          </div>
          <div v-if="r.state === 'pending'" class="mod-actions">
            <button class="btn sm danger" @click="handle(r, 'removed')"><AppIcon name="ban" :size="14" /> 下架内容</button>
            <button class="btn sm ghost" @click="handle(r, 'ignored')">驳回举报</button>
          </div>
          <div v-else class="mod-actions">
            <span class="done-note">{{ r.state === 'removed' ? '内容已下架，举报人已反馈' : '经核实举报不成立，已驳回' }}</span>
          </div>
        </article>
        <div v-if="!reportList.length" class="empty-box">
          <AppIcon name="shield" :size="30" />
          <p>暂无待处理举报</p>
          <span>App 端用户提交的举报会实时出现在这里</span>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { posts, sensitiveWords } from '@/data/admin'
import { showToast } from '@/composables/toast'

// 与 App 端共用的举报存储键（App：Community.vue 举报 → 本页处理 → Dashboard 计数）
const REPORT_KEY = 'petwise_post_reports'

const tab = ref('posts')
const f = ref('all')
const rf = ref('pending')

// ---- AI 预审：敏感词扫描 + 违规类型归类 ----
function aiScan(text) {
  const hit = sensitiveWords.filter((w) => text.includes(w))
  if (!hit.length) return { hit: false, words: [], kind: '' }
  const adWords = ['微信', 'VX', 'vx', '加我', '私聊', '低价', '促销', '优惠', '代购']
  const abuseWords = ['辱骂', '垃圾', '该死', '打死']
  const kind = hit.some((w) => adWords.includes(w))
    ? '广告导流'
    : hit.some((w) => abuseWords.includes(w))
      ? '辱骂攻击'
      : '违法违规'
  return { hit: true, words: hit.slice(0, 4), kind }
}

const rows = ref(posts.map((p) => ({ ...p, ai: aiScan(p.text) })))
const flaggedCount = computed(() => rows.value.filter((p) => p.ai.hit).length)
const pendingPosts = computed(() => rows.value.filter((p) => p.state === 'pending').length)
const postList = computed(() => rows.value.filter((p) => f.value === 'all' || p.state === f.value))

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

// ---- 举报处理：读取 / 写回共享键 ----
function loadReports() {
  try {
    return JSON.parse(localStorage.getItem(REPORT_KEY) || '[]')
  } catch (e) {
    return []
  }
}
const reports = ref(loadReports())
const pendingReports = computed(() => reports.value.filter((r) => r.state === 'pending').length)
const reportList = computed(() =>
  reports.value.filter((r) => rf.value === 'all' || r.state === 'pending')
)

function reportBadge(s) {
  return { pending: 'watch', removed: 'alert', ignored: 'neutral' }[s] || 'neutral'
}
function reportLabel(s) {
  return { pending: '待处理', removed: '已下架', ignored: '举报驳回' }[s] || s
}
function handle(r, kind) {
  r.state = kind
  localStorage.setItem(REPORT_KEY, JSON.stringify(reports.value))
  showToast(kind === 'removed' ? '已下架被举报内容并反馈举报人' : '已驳回该举报', {
    type: kind === 'removed' ? 'success' : 'default'
  })
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
.mod-text.flagged { color: var(--color-alert); }
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

/* AI 预审结论行 */
.ai-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 9px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  line-height: 1.5;
}
.ai-row.risk {
  background: rgba(200, 67, 31, 0.08);
  color: var(--color-alert);
}
.ai-row.safe {
  background: var(--color-sage-soft);
  color: var(--color-sage);
}
.hit-word {
  display: inline-block;
  margin: 0 2px;
  padding: 0 7px;
  border-radius: var(--radius-pill);
  background: rgba(200, 67, 31, 0.14);
  font-weight: 700;
}

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
