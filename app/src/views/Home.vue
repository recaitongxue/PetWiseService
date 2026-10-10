<template>
  <section class="screen home">
    <!-- 顶部问候 -->
    <header class="head" v-reveal>
      <div>
        <p class="eyebrow num">{{ today }}</p>
        <h1 class="greet">
          {{ greeting }}，<span class="greet-name">{{ user.name.replace(/.$/, '·') }}</span>
        </h1>
      </div>
      <button class="bell" type="button" aria-label="通知" @click="showToast('暂无新通知')">
        <AppIcon name="bell" :size="20" />
        <span class="dot"></span>
      </button>
    </header>

    <!-- 平台公告（管理端发布，点击展开） -->
    <div v-if="announcements.length" class="ann" v-reveal="{ delay: 20 }">
      <button class="ann-row" type="button" @click="annOpen = !annOpen">
        <span class="ann-ic"><AppIcon name="bell" :size="15" /></span>
        <span class="ann-title">{{ announcements[0].title }}</span>
        <span class="ann-more num" v-if="announcements.length > 1">+{{ announcements.length - 1 }}</span>
        <AppIcon :name="annOpen ? 'x' : 'back'" :size="14" class="ann-arrow" :class="{ up: annOpen }" />
      </button>
      <transition name="ann-fold">
        <div v-if="annOpen" class="ann-body">
          <article v-for="a in announcements" :key="a.id" class="ann-item">
            <div class="ann-item-head">
              <b>{{ a.title }}</b>
              <span class="ann-tag" :class="a.level">{{ levelLabel(a.level) }}</span>
            </div>
            <p class="ann-text">{{ a.body }}</p>
          </article>
          <button class="ann-close" type="button" @click="dismissAll">知道了，不再显示</button>
        </div>
      </transition>
    </div>

    <!-- 多宠物切换 -->
    <div class="pet-switch" v-reveal="{ delay: 40 }">
      <button
        v-for="(p, i) in pets"
        :key="p.id"
        class="ps-tab"
        :class="{ on: current === i }"
        type="button"
        @click="current = i"
      >
        <PetAvatar :species="p.species" :name="p.name" :size="28" :ring="false" />
        <span>{{ p.name }}</span>
      </button>
    </div>

    <!-- 今日主角：深色锚点卡 -->
    <article class="hero" v-reveal="{ delay: 80 }">
      <div class="hero-deco" aria-hidden="true"></div>
      <div class="hero-left">
        <span class="hero-pill">{{ pet.tagline }}</span>
        <h2 class="hero-name">{{ pet.name }}</h2>
        <p class="hero-sub">{{ pet.breed }} · {{ pet.age }}岁 · {{ pet.gender }}</p>
        <div class="hero-chips">
          <span class="chip">
            <AppIcon name="calendar" :size="13" /> 疫苗 {{ pet.nextVaccine.slice(5) }}
          </span>
          <router-link :to="`/pet/${pet.id}`" class="chip link">
            健康档案 <AppIcon name="back" :size="12" />
          </router-link>
        </div>
      </div>
      <div class="hero-right">
        <span class="hero-ava">
          <PetAvatar :species="pet.species" :name="pet.name" :size="126" :ring="false" />
        </span>
        <span class="hero-ring">
          <HealthRing :value="pet.healthScore" label="健康分" :size="84" light />
        </span>
      </div>
    </article>

    <!-- 今日提醒 -->
    <section class="sec" v-reveal="{ delay: 120 }">
      <div class="sec-head">
        <span class="sec-idx num">01</span>
        <h3 class="sec-t">今日提醒</h3>
        <span class="sec-hint">{{ pet.name }}</span>
      </div>
      <div class="reminders">
        <div v-for="r in reminders" :key="r.label" class="reminder" :class="r.state">
          <span class="rem-ic"><AppIcon :name="r.icon" :size="17" /></span>
          <div class="rem-body">
            <span class="rem-label">{{ r.label }}</span>
            <span class="rem-date num">{{ r.date }}</span>
          </div>
          <button class="rem-done" type="button" @click="markDone(r)">知道了</button>
        </div>
      </div>
    </section>

    <!-- 快捷服务：2×2 Bento -->
    <section class="sec" v-reveal="{ delay: 160 }">
      <div class="sec-head">
        <span class="sec-idx num">02</span>
        <h3 class="sec-t">快捷服务</h3>
        <span class="sec-hint">智能驱动</span>
      </div>
      <div class="q-grid">
        <router-link
          v-for="a in quickActions"
          :key="a.id"
          :to="a.to"
          class="q-tile"
          :class="{ accent: a.accent }"
        >
          <span class="q-ic"><AppIcon :name="a.icon" :size="22" /></span>
          <span class="q-label">{{ a.label }}</span>
          <span class="q-sub">{{ a.sub }}</span>
        </router-link>
      </div>
    </section>

    <!-- 本周趋势：大数字 + 柱图 -->
    <section class="sec" v-reveal="{ delay: 200 }">
      <div class="sec-head">
        <span class="sec-idx num">03</span>
        <h3 class="sec-t">本周健康趋势</h3>
        <span class="sec-hint">近 7 日</span>
      </div>
      <div class="trend">
        <div class="trend-score">
          <b class="num">{{ avgScore }}</b>
          <span>平均分</span>
        </div>
        <div class="trend-bars">
          <div v-for="d in trend" :key="d.day" class="t-col">
            <div class="t-bar-wrap">
              <span class="t-bar" :class="barState(d.label)" :style="{ height: d.value + '%' }"></span>
            </div>
            <span class="t-day num">{{ d.day }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 每日贴士 -->
    <section class="sec" v-reveal="{ delay: 240 }">
      <div class="sec-head">
        <span class="sec-idx num">04</span>
        <h3 class="sec-t">每日贴士</h3>
      </div>
      <article class="tip">
        <span class="tip-tag">{{ tip.tag }}</span>
        <h4 class="tip-title">{{ tip.title }}</h4>
        <p class="tip-body">{{ tip.body }}</p>
      </article>
    </section>

    <!-- 社区引流 -->
    <router-link to="/community" class="discover" v-reveal="{ delay: 280 }">
      <div>
        <p class="discover-eyebrow">PET COMMUNITY</p>
        <h3 class="discover-title">看看大家今天在聊什么</h3>
      </div>
      <span class="discover-go"><AppIcon name="back" :size="18" /></span>
    </router-link>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import HealthRing from '@/components/HealthRing.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import { user, pets, petTrends, petReminders, quickActions, tips } from '@/data/mock'
import { activeAnnouncements, dismissAnnouncement } from '@/data/ops'
import { showToast } from '@/composables/toast'

const current = ref(0)
const annOpen = ref(false)
const announcements = ref(activeAnnouncements())
const pet = computed(() => pets[current.value])
const trend = computed(() => petTrends[pet.value.id] || petTrends.mochi)
const reminders = computed(() => petReminders[pet.value.id] || [])
const avgScore = computed(() =>
  Math.round(trend.value.reduce((s, d) => s + d.value, 0) / trend.value.length)
)

function markDone(r) {
  showToast(`已记下「${r.label}」`, { type: 'success' })
}

function levelLabel(l) {
  return { event: '活动', info: '通知', warn: '提醒' }[l] || '公告'
}

function dismissAll() {
  announcements.value.forEach((a) => dismissAnnouncement(a.id))
  announcements.value = []
  annOpen.value = false
  showToast('已收起平台公告')
}

const tip = tips[0]

const today = computed(() => {
  const d = new Date()
  const wk = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]
  return `${wk} · ${d.getMonth() + 1}.${String(d.getDate()).padStart(2, '0')}`
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 11) return '早安'
  if (h < 14) return '午安'
  if (h < 18) return '下午好'
  return '晚安'
})

function barState(label) {
  if (label === '优') return 'good'
  if (label === '需关注') return 'watch'
  return 'mid'
}
</script>

<style scoped>
/* ---------- 头部 ---------- */
.head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin: 14px 0 18px;
}
.greet {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-2xl);
  letter-spacing: -0.02em;
  line-height: 1.08;
  margin-top: 6px;
}
.greet-name { color: var(--color-accent-ink); }
.bell {
  position: relative;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-surface);
  color: var(--color-ink);
  box-shadow: var(--shadow-soft);
}
.bell .dot {
  position: absolute;
  top: 10px;
  right: 11px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-accent);
  border: 2px solid var(--color-surface);
}

/* ---------- 平台公告 ---------- */
.ann {
  margin-bottom: 18px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
  overflow: hidden;
}
.ann-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 13px 16px;
  text-align: left;
}
.ann-ic {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: var(--color-accent-soft);
  color: var(--color-accent-ink);
  flex-shrink: 0;
}
.ann-title {
  flex: 1;
  min-width: 0;
  font-weight: 700;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ann-more {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}
.ann-arrow { color: var(--color-faint); transform: rotate(180deg); }
.ann-arrow.up { transform: rotate(90deg); }
.ann-body {
  padding: 4px 16px 14px;
  border-top: 1px dashed var(--color-border);
}
.ann-item { padding: 12px 0 4px; }
.ann-item-head { display: flex; align-items: center; gap: 8px; }
.ann-item-head b { font-size: 14px; }
.ann-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: var(--color-sage-soft);
  color: var(--color-good);
}
.ann-tag.warn { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.ann-tag.event { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.ann-text {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.65;
  color: var(--color-ink-2);
}
.ann-close {
  margin-top: 8px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-faint);
}
.ann-fold-enter-active,
.ann-fold-leave-active { transition: all var(--dur-base) var(--ease-out); }
.ann-fold-enter-from,
.ann-fold-leave-to { opacity: 0; transform: translateY(-6px); }

/* ---------- 宠物切换 ---------- */
.pet-switch {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
}
.ps-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px 6px 7px;
  border-radius: var(--radius-pill);
  background: transparent;
  box-shadow: inset 0 0 0 1px var(--color-border);
  font-weight: 700;
  font-size: 14px;
  color: var(--color-muted);
  transition: all var(--dur-fast) var(--ease-out);
}
.ps-tab.on {
  color: var(--color-ink);
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
}
.ps-tab:active { transform: scale(0.96); }

/* ---------- 深色主角卡 ---------- */
.hero {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--grad-ink);
  border-radius: 32px;
  padding: 26px 22px;
  overflow: hidden;
  box-shadow: var(--shadow-2);
  color: var(--color-surface);
}
.hero-deco {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(16rem 12rem at 88% -10%, rgba(232, 85, 43, 0.35), transparent 62%),
    radial-gradient(14rem 12rem at -6% 110%, rgba(126, 155, 120, 0.4), transparent 60%);
}
.hero-left {
  position: relative;
  flex: 1;
  min-width: 0;
}
.hero-pill {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--color-peach);
  background: rgba(255, 255, 255, 0.1);
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  margin-bottom: 12px;
}
.hero-name {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: clamp(36px, 10vw, 46px);
  letter-spacing: -0.02em;
  line-height: 1;
}
.hero-sub {
  font-size: 13px;
  color: rgba(251, 246, 236, 0.72);
  margin-top: 8px;
}
.hero-chips {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(251, 246, 236, 0.85);
  background: rgba(255, 255, 255, 0.1);
  padding: 7px 12px;
  border-radius: var(--radius-pill);
}
.chip.link { background: rgba(255, 255, 255, 0.16); color: var(--color-surface); }
.chip.link svg { transform: rotate(180deg); }

.hero-right {
  position: relative;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}
.hero-ava {
  display: block;
  border-radius: 50%;
  box-shadow: 0 14px 32px rgba(0, 0, 0, 0.35);
}
.hero-ring {
  position: absolute;
  left: -14px;
  bottom: -6px;
  background: rgba(27, 42, 34, 0.55);
  backdrop-filter: blur(6px);
  border-radius: 50%;
  padding: 2px;
}

/* ---------- 区块（编辑式序号） ---------- */
.sec { margin-top: 32px; }
.sec-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 14px;
}
.sec-idx {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 13px;
  color: var(--color-accent-ink);
  letter-spacing: 0.06em;
}
.sec-t {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-lg);
  letter-spacing: -0.01em;
}
.sec-hint {
  margin-left: auto;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--color-faint);
  text-transform: uppercase;
}

/* ---------- 今日提醒 ---------- */
.reminders { display: flex; flex-direction: column; gap: 10px; }
.reminder {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
}
.rem-ic {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: var(--color-sage-soft);
  color: var(--color-good);
  flex-shrink: 0;
}
.reminder.watch .rem-ic { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.rem-body { flex: 1; display: flex; flex-direction: column; }
.rem-label { font-weight: 700; font-size: 15px; }
.rem-date { font-size: 12px; color: var(--color-muted); }
.rem-done {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-accent-ink);
  padding: 8px 4px 8px 12px;
}

/* ---------- 快捷服务 Bento ---------- */
.q-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.q-tile {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 16px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
  transition: transform var(--dur-fast) var(--ease-out);
  min-height: 96px;
}
.q-tile:active { transform: scale(0.97); }
.q-ic {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: var(--color-sage-soft);
  color: var(--color-ink);
  margin-bottom: 8px;
}
.q-label { font-weight: 700; font-size: 15px; }
.q-sub { font-size: 11px; color: var(--color-faint); }
.q-tile.accent {
  background: var(--grad-coral);
  color: #fff;
  box-shadow: 0 14px 30px rgba(214, 80, 42, 0.35);
}
.q-tile.accent .q-ic { background: rgba(255, 255, 255, 0.2); color: #fff; }
.q-tile.accent .q-sub { color: rgba(255, 255, 255, 0.8); }

/* ---------- 本周趋势 ---------- */
.trend {
  display: flex;
  align-items: stretch;
  gap: 18px;
  padding: 20px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
}
.trend-score {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex-shrink: 0;
  padding-right: 18px;
  border-right: 1px solid var(--color-border);
}
.trend-score b {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 52px;
  line-height: 1;
  letter-spacing: -0.03em;
  color: var(--color-ink);
}
.trend-score span {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--color-faint);
  margin-top: 6px;
  text-transform: uppercase;
}
.trend-bars {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: 6px;
  min-height: 110px;
}
.t-col {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}
.t-bar-wrap {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.t-bar {
  width: 62%;
  max-width: 16px;
  border-radius: 6px;
  background: var(--grad-sage);
  transition: height 0.9s var(--ease-out);
}
.t-bar.good { background: var(--grad-coral); }
.t-bar.watch { background: linear-gradient(180deg, #f2c26b, #d9952b); }
.t-day { font-size: 11px; color: var(--color-muted); font-weight: 600; }

/* ---------- 贴士 ---------- */
.tip {
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  background: var(--color-sage-soft);
}
.tip-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--color-accent-ink);
  text-transform: uppercase;
}
.tip-title {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: var(--fs-md);
  margin: 6px 0;
}
.tip-body {
  font-size: 14px;
  color: var(--color-ink-2);
  line-height: 1.6;
}

/* ---------- 社区引流 ---------- */
.discover {
  margin-top: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 22px;
  border-radius: var(--radius-lg);
  background: var(--grad-peach);
  color: var(--color-ink);
  box-shadow: var(--shadow-soft);
}
.discover-eyebrow {
  font-size: 10px;
  letter-spacing: 0.2em;
  font-weight: 700;
  color: var(--color-accent-ink);
}
.discover-title {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: var(--fs-md);
  margin-top: 6px;
}
.discover-go {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(27, 42, 34, 0.08);
}
.discover-go svg { transform: rotate(180deg); }
</style>
