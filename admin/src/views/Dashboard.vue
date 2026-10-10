<template>
  <section>
    <!-- 指标卡 -->
    <div class="stats">
      <article v-for="(s, i) in stats" :key="s.key" class="card stat" v-reveal="{ delay: i * 60 }">
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

    <!-- 快捷入口 -->
    <article class="card quick" v-reveal>
      <h2 class="card-title">运营速览</h2>
      <div class="quick-grid">
        <router-link v-for="q in quick" :key="q.to" :to="q.to" class="q-item">
          <span class="q-ic"><AppIcon :name="q.icon" :size="18" /></span>
          <div>
            <b>{{ q.label }}</b>
            <span>{{ q.hint }}</span>
          </div>
          <AppIcon name="back" :size="15" class="q-go" />
        </router-link>
      </div>
    </article>
  </section>
</template>

<script setup>
import AppIcon from '@/components/icons/AppIcon.vue'
import { stats, usageSeries, breedDist } from '@/data/admin'

const quick = [
  { to: '/moderation', label: '待审核内容', hint: '2 条待处理', icon: 'shield' },
  { to: '/records', label: '低置信度识别', hint: '1 条需复核', icon: 'eye' },
  { to: '/consults', label: '已转人工问诊', hint: '1 条跟进', icon: 'stethoscope' }
]

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

.quick { margin-top: 16px; }
.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 12px;
}
.q-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  transition: transform var(--dur-fast) var(--ease-out), background var(--dur-fast);
}
.q-item:hover { background: var(--color-sage-soft); }
.q-item:active { transform: scale(0.98); }
.q-ic {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: var(--color-surface);
  color: var(--color-accent-ink);
  flex-shrink: 0;
}
.q-item b { display: block; font-size: 14px; line-height: 1.2; }
.q-item span { font-size: 12px; color: var(--color-muted); }
.q-go { margin-left: auto; transform: rotate(180deg); color: var(--color-faint); }

@media (max-width: 1100px) {
  .stats { grid-template-columns: repeat(2, 1fr); }
  .grid { grid-template-columns: 1fr; }
  .quick-grid { grid-template-columns: 1fr; }
}
</style>
