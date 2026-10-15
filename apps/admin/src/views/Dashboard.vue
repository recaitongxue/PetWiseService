<template>
  <section>
    <!-- 指标卡：基础量为演示累计值，增量读共享键真实数据 -->
    <div class="stats">
      <article v-for="(s, i) in statCards" :key="s.key" class="card stat" v-reveal="{ delay: i * 60 }">
        <p class="stat-label">{{ s.label }}</p>
        <p class="stat-value num">{{ s.value.toLocaleString() }}</p>
        <p class="stat-foot">
          <span class="delta" :class="s.dir">{{ s.delta }}</span>
          <span class="hint">{{ s.hint }}</span>
        </p>
      </article>
    </div>

    <div class="grid">
      <!-- 调用量折线 -->
      <article class="card chart-card" v-reveal>
        <div class="card-head">
          <div>
            <h2 class="card-title">近 7 日调用量</h2>
            <p class="card-sub">CV 识别 vs 大模型问诊</p>
          </div>
          <div class="legend">
            <span class="lg"><i class="dot coral"></i>识别</span>
            <span class="lg"><i class="dot sage"></i>问诊</span>
          </div>
        </div>
        <svg class="line-chart" viewBox="0 0 560 220" role="img" aria-label="近7日调用量折线图">
          <!-- 横向网格 -->
          <g v-for="g in 4" :key="g" class="grid-line">
            <line x1="36" :y1="30 + (g - 1) * 45" x2="548" :y2="30 + (g - 1) * 45" />
          </g>
          <!-- 两条折线 -->
          <g>
            <polyline class="line coral" :points="linePoints(usageSeries.recognize)" />
            <circle
              v-for="(p, i) in points(usageSeries.recognize)"
              :key="'a' + i"
              class="pt coral"
              :cx="p.x"
              :cy="p.y"
              r="4"
            >
              <title>{{ usageSeries.days[i] }} 识别 {{ usageSeries.recognize[i] }}</title>
            </circle>
          </g>
          <g>
            <polyline class="line sage" :points="linePoints(usageSeries.consult)" />
            <circle
              v-for="(p, i) in points(usageSeries.consult)"
              :key="'b' + i"
              class="pt sage"
              :cx="p.x"
              :cy="p.y"
              r="4"
            >
              <title>{{ usageSeries.days[i] }} 问诊 {{ usageSeries.consult[i] }}</title>
            </circle>
          </g>
          <!-- X 轴标签 -->
          <text v-for="(d, i) in usageSeries.days" :key="d" class="axis" :x="xAt(i)" y="212" text-anchor="middle">
            {{ d }}
          </text>
        </svg>
      </article>

      <!-- 品种分布 -->
      <article class="card breed-card" v-reveal="{ delay: 80 }">
        <div class="card-head">
          <div>
            <h2 class="card-title">品种识别分布</h2>
            <p class="card-sub">近 30 日 TOP 6</p>
          </div>
        </div>
        <ul class="breeds">
          <li v-for="(b, i) in breedDist" :key="b.name" class="breed" v-reveal="{ delay: 120 + i * 50 }">
            <span class="b-name">{{ b.name }}</span>
            <span class="b-track">
              <span class="b-bar" :style="{ width: (b.pct / 30) * 100 + '%' }"></span>
            </span>
            <span class="b-pct num">{{ b.pct }}%</span>
          </li>
        </ul>
      </article>
    </div>

    <div class="grid-2">
      <!-- 运营待办：全部来自共享键的真实待处理数据 -->
      <article class="card" v-reveal>
        <div class="card-head">
          <div>
            <h2 class="card-title">运营待办</h2>
            <p class="card-sub">来自 App 端实时写入的共享数据</p>
          </div>
        </div>
        <div class="todo-list">
          <router-link v-for="t in todos" :key="t.to" :to="t.to" class="todo">
            <span class="todo-ic" :class="t.tone"><AppIcon :name="t.icon" :size="16" /></span>
            <div class="todo-body">
              <b>{{ t.label }}</b>
              <span>{{ t.hint }}</span>
            </div>
            <span class="todo-num num" :class="{ zero: t.count === 0 }">{{ t.count }}</span>
            <AppIcon name="back" :size="14" class="q-go" />
          </router-link>
        </div>
      </article>

      <!-- 系统状态：CV 模型配置真实读取 -->
      <article class="card" v-reveal="{ delay: 60 }">
        <div class="card-head">
          <div>
            <h2 class="card-title">系统状态</h2>
            <p class="card-sub">服务与模型运行情况</p>
          </div>
          <span class="live"><i></i>运行正常</span>
        </div>
        <div class="sys-list">
          <div v-for="m in modelStatus" :key="m.kind" class="sys-row">
            <span class="sys-ic"><AppIcon name="sparkle" :size="15" /></span>
            <div class="sys-body">
              <b>{{ m.name }}</b>
              <span>{{ m.backbone }} · {{ m.classes }} 类 · {{ m.note }}</span>
            </div>
            <span class="badge watch">流水线就绪</span>
          </div>
          <div class="sys-row">
            <span class="sys-ic sage"><AppIcon name="check" :size="15" /></span>
            <div class="sys-body">
              <b>API 网关</b>
              <span>识别 / 问诊 / 社区接口正常</span>
            </div>
            <span class="badge good">正常</span>
          </div>
          <div class="sys-row">
            <span class="sys-ic sage"><AppIcon name="check" :size="15" /></span>
            <div class="sys-body">
              <b>数据回流</b>
              <span>识别纠正 → 审核 → 训练集导出链路可用</span>
            </div>
            <span class="badge good">正常</span>
          </div>
        </div>
      </article>
    </div>

    <!-- 今日动态：真实识别与举报 -->
    <article class="card" v-reveal style="margin-top: 16px">
      <div class="card-head">
        <div>
          <h2 class="card-title">今日动态</h2>
          <p class="card-sub">App 端最新写入的识别与举报</p>
        </div>
      </div>
      <div class="feed-list">
        <div v-for="r in latestRecognitions" :key="r.id" class="feed-row">
          <span class="feed-ic coral"><AppIcon name="camera" :size="14" /></span>
          <span class="feed-text">
            <b>{{ r.predicted }}</b>
            <template v-if="r.corrected"> · 用户手动纠正为 <b>{{ r.corrected }}</b></template>
            <span class="feed-meta num">置信度 {{ Math.round((r.confidence || 0) * 100) }}% · {{ r.date }}</span>
          </span>
          <span class="badge" :class="r.corrected ? 'watch' : 'good'">{{ r.corrected ? '待审核' : '已通过' }}</span>
        </div>
        <div v-for="rp in latestReports" :key="rp.id" class="feed-row">
          <span class="feed-ic alert"><AppIcon name="alert" :size="14" /></span>
          <span class="feed-text">
            举报：<b>{{ rp.author }}</b> 的动态 · {{ rp.reason }}
            <span class="feed-meta num">{{ rp.time }}</span>
          </span>
          <span class="badge watch">待处理</span>
        </div>
        <p v-if="!latestRecognitions.length && !latestReports.length" class="empty">
          暂无今日动态。App 端的识别、纠正与举报会实时出现在这里。
        </p>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { users, pets, recognitions, posts, consults, usageSeries, breedDist, modelStatus } from '@/data/admin'

const RECOG_KEY = 'petwise_recognitions'
const REPORT_KEY = 'petwise_post_reports'
const USER_KEY = 'petwise_admin_users'

function readJSON(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || '[]')
  } catch (e) {
    return []
  }
}

// 真实数据：App 端识别记录 / 举报 + 管理端自定义用户
const appRecognitions = readJSON(RECOG_KEY)
const postReports = readJSON(REPORT_KEY)
const customUsers = readJSON(USER_KEY)

const reviewCount = recognitions.filter((r) => r.state === 'review').length + appRecognitions.filter((r) => r.status === 'review').length
const pendingReports = postReports.filter((r) => r.state === 'pending').length
const pendingPosts = posts.filter((p) => p.state === 'pending').length
const todayRecognitions = recognitions.length + appRecognitions.length

const statCards = computed(() => [
  { key: 'users', label: '注册用户', value: 12840 + users.length + customUsers.length, delta: `+${customUsers.length}`, dir: 'up', hint: '管理端新增' },
  { key: 'pets', label: '在档宠物', value: 17230 + pets.length, delta: `+${pets.length}`, dir: 'up', hint: '含演示档案' },
  { key: 'recog', label: '累计识别', value: 42130 + todayRecognitions, delta: `+${todayRecognitions}`, dir: 'up', hint: 'CV 调用量' },
  { key: 'consult', label: '累计问诊', value: 9860 + consults.length, delta: `+${consults.length}`, dir: 'up', hint: '大模型会话' }
])

const todos = computed(() => [
  { to: '/moderation', label: '待处理举报', hint: '来自 App 端用户举报', icon: 'alert', tone: 'alert', count: pendingReports },
  { to: '/moderation', label: '待审核内容', hint: 'AI 预审标记的可疑动态', icon: 'shield', tone: 'coral', count: pendingPosts },
  { to: '/records', label: '识别纠正待审', hint: '用户手动更改的识别结果', icon: 'eye', tone: 'sage', count: reviewCount },
  { to: '/consults', label: '转人工问诊', hint: 'AI 分诊建议线下面诊', icon: 'stethoscope', tone: 'sage', count: consults.filter((c) => c.state === 'transferred').length }
])

const latestRecognitions = computed(() =>
  [...appRecognitions]
    .sort((a, b) => (a.date < b.date ? 1 : -1))
    .slice(0, 4)
)
const latestReports = computed(() =>
  postReports.filter((r) => r.state === 'pending').slice(0, 3)
)

// SVG 折线几何：560x220 视窗，左边距 36，右 12
const X0 = 52
const X1 = 548
const Y0 = 155
const Y1 = 30
const MAX = 1600

function xAt(i) {
  const n = usageSeries.days.length
  return X0 + (i * (X1 - X0)) / (n - 1)
}
function points(arr) {
  return arr.map((v, i) => ({ x: xAt(i), y: Y0 - (v / MAX) * (Y0 - Y1) }))
}
function linePoints(arr) {
  return points(arr).map((p) => `${p.x},${p.y}`).join(' ')
}
</script>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.stat-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-faint);
}
.stat-value {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 40px;
  line-height: 1.05;
  letter-spacing: -0.02em;
  margin: 8px 0 6px;
}
.stat-foot { display: flex; align-items: center; gap: 8px; }
.delta { font-size: 12px; font-weight: 700; padding: 3px 9px; border-radius: var(--radius-pill); }
.delta.up { color: var(--color-good); background: var(--color-sage-soft); }
.delta.down { color: var(--color-alert); background: var(--color-accent-soft); }
.hint { font-size: 12px; color: var(--color-faint); }

.grid {
  display: grid;
  grid-template-columns: 1.7fr 1fr;
  gap: 16px;
  margin-top: 16px;
}
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 16px;
}
.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;
}
.card-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 17px;
  letter-spacing: -0.01em;
}
.card-sub { font-size: 12px; color: var(--color-faint); margin-top: 2px; }
.legend { display: flex; gap: 14px; }
.lg { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--color-muted); font-weight: 600; }
.dot { width: 9px; height: 9px; border-radius: 3px; display: inline-block; }
.dot.coral { background: var(--color-accent); }
.dot.sage { background: var(--color-sage); }

.live {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-good);
  background: var(--color-sage-soft);
  padding: 4px 11px;
  border-radius: var(--radius-pill);
}
.live i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-good);
  animation: pulse 1.8s var(--ease-in-out) infinite;
}
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }

.line-chart { width: 100%; height: auto; }
.grid-line line { stroke: var(--color-border); stroke-dasharray: 3 5; }
.line { fill: none; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
.line.coral { stroke: var(--color-accent); }
.line.sage { stroke: var(--color-sage); }
.pt { stroke: var(--color-surface); stroke-width: 2; }
.pt.coral { fill: var(--color-accent); }
.pt.sage { fill: var(--color-sage); }
.axis { font-size: 11px; fill: var(--color-faint); font-family: var(--font-body); }

.breeds { display: flex; flex-direction: column; gap: 14px; }
.breed { display: flex; align-items: center; gap: 12px; }
.b-name { width: 88px; flex-shrink: 0; font-size: 13px; font-weight: 600; color: var(--color-ink-2); }
.b-track {
  flex: 1;
  height: 10px;
  border-radius: 999px;
  background: var(--color-surface-2);
  overflow: hidden;
}
.b-bar {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: var(--grad-sage, linear-gradient(90deg, #dfead8, #7e9b78));
}
.breed:nth-child(2) .b-bar { background: linear-gradient(90deg, #f6dcc4, #f2a65a); }
.breed:nth-child(3) .b-bar { background: linear-gradient(90deg, #f6cdbb, #e8552b); }
.b-pct { width: 40px; text-align: right; font-weight: 700; font-size: 13px; }

/* ---------- 运营待办 ---------- */
.todo-list { display: flex; flex-direction: column; gap: 9px; }
.todo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  transition: transform var(--dur-fast) var(--ease-out), background var(--dur-fast);
}
.todo:hover { background: var(--color-sage-soft); }
.todo:active { transform: scale(0.985); }
.todo-ic {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: var(--color-surface);
  color: var(--color-accent-ink);
  flex-shrink: 0;
}
.todo-ic.alert { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.todo-ic.coral { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.todo-ic.sage { background: var(--color-sage-soft); color: var(--color-good); }
.todo-body { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.todo-body b { font-size: 14px; }
.todo-body span { font-size: 11.5px; color: var(--color-muted); }
.todo-num {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 20px;
  color: var(--color-accent-ink);
  flex-shrink: 0;
}
.todo-num.zero { color: var(--color-faint); }
.q-go { transform: rotate(180deg); color: var(--color-faint); flex-shrink: 0; }

/* ---------- 系统状态 ---------- */
.sys-list { display: flex; flex-direction: column; gap: 10px; }
.sys-row {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 11px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}
.sys-ic {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: var(--color-accent-soft);
  color: var(--color-accent-ink);
  flex-shrink: 0;
}
.sys-ic.sage { background: var(--color-sage-soft); color: var(--color-good); }
.sys-body { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.sys-body b { font-size: 13.5px; }
.sys-body span { font-size: 11px; color: var(--color-muted); }

/* ---------- 今日动态 ---------- */
.feed-list { display: flex; flex-direction: column; gap: 2px; }
.feed-row {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 10px 2px;
  border-bottom: 1px solid var(--color-border);
}
.feed-row:last-child { border-bottom: none; }
.feed-ic {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: var(--color-accent-soft);
  color: var(--color-accent-ink);
  flex-shrink: 0;
}
.feed-ic.sage { background: var(--color-sage-soft); color: var(--color-good); }
.feed-ic.alert { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.feed-text { flex: 1; font-size: 13px; color: var(--color-ink-2); min-width: 0; }
.feed-meta { display: block; font-size: 11px; color: var(--color-faint); margin-top: 2px; }

.empty { text-align: center; color: var(--color-muted); padding: 22px 0; font-size: 13px; }

@media (max-width: 1100px) {
  .stats { grid-template-columns: repeat(2, 1fr); }
  .grid, .grid-2 { grid-template-columns: 1fr; }
}
</style>
