<template>
  <section class="screen home">
    <!-- 顶部问候 -->
    <header class="head" v-reveal>
      <div>
        <p class="eyebrow num">{{ todayText }}</p>
        <h1 class="greet">
          {{ greeting.text }}，<span class="greet-name">{{ user.name }}</span>
        </h1>
        <p class="greet-sub">{{ greeting.sub }}</p>
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

    <!-- 每日贴士：一行轻量提示，不占独立区块 -->
    <button class="tip-line" type="button" v-reveal="{ delay: 100 }" @click="nextTip">
      <span class="tl-ic"><AppIcon name="sparkle" :size="14" /></span>
      <span class="tl-text"><b>{{ tip.tag }}</b> · {{ tip.title }}</span>
      <AppIcon name="back" :size="13" class="tl-arrow" />
    </button>

    <!-- 今日提醒：聚合全部宠物日程的大卡，可按宠物筛选 -->
    <section class="sec" v-reveal="{ delay: 120 }">
      <div class="sec-head">
        <span class="sec-idx num">01</span>
        <h3 class="sec-t">今日提醒</h3>
        <router-link to="/schedule" class="sec-link">
          全部日程 <AppIcon name="back" :size="12" />
        </router-link>
      </div>
      <div class="today-card">
        <!-- 统计条：随筛选范围联动 -->
        <div class="log-strip">
          <div class="log-cell">
            <b class="num" :class="{ warn: logStats.overdue }">{{ logStats.overdue }}</b>
            <span>已逾期</span>
          </div>
          <span class="log-sep"></span>
          <div class="log-cell">
            <b class="num">{{ logStats.today }}</b>
            <span>今天待办</span>
          </div>
          <span class="log-sep"></span>
          <div class="log-cell">
            <b class="num">{{ logStats.done }}</b>
            <span>已完成</span>
          </div>
        </div>

        <!-- 宠物筛选：默认全部宠物 -->
        <div class="pet-filter">
          <button class="pf-chip" :class="{ on: petFilter === 'all' }" type="button" @click="petFilter = 'all'">
            <span class="pf-ava all"><AppIcon name="paw" :size="14" /></span>
            全部
            <span v-if="pendingAll" class="pf-num num">{{ pendingAll }}</span>
          </button>
          <button
            v-for="p in pets"
            :key="p.id"
            class="pf-chip"
            :class="{ on: petFilter === p.id }"
            type="button"
            @click="petFilter = p.id"
          >
            <PetAvatar :species="p.species" :name="p.name" :size="22" :ring="false" />
            {{ p.name }}
            <span v-if="pendingOf(p.id)" class="pf-num num">{{ pendingOf(p.id) }}</span>
          </button>
        </div>

        <!-- 提醒列表：全部视图下带宠物名标签 -->
        <div class="reminders">
          <div v-for="r in todayLogs" :key="r.id" class="reminder" :class="r.overdue ? 'watch' : ''">
            <span class="rem-ic" :class="r.tone"><AppIcon :name="r.icon" :size="17" /></span>
            <div class="rem-body">
              <span class="rem-label">
                <span v-if="petFilter === 'all'" class="rem-pet">
                  <PetAvatar :species="r.species" :name="r.petName" :size="18" :ring="false" />{{ r.petName }}
                </span>
                {{ r.title }}
              </span>
              <span class="rem-date num">{{ r.dateText }}{{ r.time ? ' · ' + r.time : '' }}{{ r.cycle ? ' · ' + r.cycle : '' }}</span>
            </div>
            <button class="rem-done" type="button" @click="markDone(r)">完成了</button>
          </div>
          <p v-if="!todayLogs.length" class="log-empty">
            {{ filterName }}今天都没有待办日程。去<router-link to="/schedule" class="lnk">日程页</router-link>用 AI 一键生成养护计划吧。
          </p>
          <router-link v-else-if="remaining" to="/schedule" class="rem-more">
            还有 {{ remaining }} 条待办，查看全部日程
            <AppIcon name="back" :size="12" />
          </router-link>
        </div>
      </div>
    </section>

    <!-- 快捷入口：弱化为单行工具条（磁铁让位于日志提醒） -->
    <section class="sec" v-reveal="{ delay: 160 }">
      <div class="sec-head">
        <span class="sec-idx num">02</span>
        <h3 class="sec-t">常用工具</h3>
      </div>
      <div class="tool-strip">
        <router-link
          v-for="a in quickActions"
          :key="a.id"
          :to="a.to"
          class="tool"
          :class="{ accent: a.accent }"
        >
          <span class="tool-ic"><AppIcon :name="a.icon" :size="20" /></span>
          <span class="tool-label">{{ a.label }}</span>
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

    <!-- 社区引流：收敛为描边卡，不再用大块渐变 -->
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
import { ref, computed, onMounted, watch } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import HealthRing from '@/components/HealthRing.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import { quickActions, tips } from '@/data/static'
import {
  fetchUser, fetchPets, fetchPetTrend, fetchPetSchedule, fetchScheduleTypes,
  fetchAnnouncements, dismissAnnouncement, toggleScheduleDone
} from '@/api/data'
import { showToast } from '@shared/toast'

const user = ref({ name: '' })
const pets = ref([])
const current = ref(0)
const annOpen = ref(false)
const announcements = ref([])
const schedMap = ref({})
const typeMeta = ref({})

const pet = computed(() =>
  pets.value[current.value] || {
    id: null, name: '', species: '', breed: '', age: '', gender: '',
    tagline: '', healthScore: 0, nextVaccine: ''
  }
)
const trend = ref([])
const avgScore = computed(() =>
  trend.value.length ? Math.round(trend.value.reduce((s, d) => s + d.value, 0) / trend.value.length) : 0
)

/* ---------- 今日提醒：聚合全部宠物日程，可按宠物筛选 ---------- */

const petFilter = ref('all')
const today = new Date()

// 全部宠物的日程（来自后端），统一计算图标/色调/剩余天数
const allPetLogs = computed(() => {
  const list = []
  pets.value.forEach((p) => {
    ;(schedMap.value[p.id] || []).forEach((s) => {
      const meta = typeMeta.value[s.type] || typeMeta.value.other || {}
      const diff = Math.round((new Date(s.date) - today) / 86400000)
      list.push({
        ...s,
        petId: p.id,
        petName: p.name,
        species: p.species,
        icon: meta.icon,
        tone: meta.tone,
        diff
      })
    })
  })
  return list
})

const scopedLogs = computed(() =>
  petFilter.value === 'all'
    ? allPetLogs.value
    : allPetLogs.value.filter((s) => s.petId === petFilter.value)
)

// 未完成且已到期（含逾期）的待办，按日期升序
const pendingSorted = computed(() =>
  scopedLogs.value
    .filter((s) => !s.done && s.diff <= 0)
    .sort((a, b) => (a.date < b.date ? -1 : 1))
)

const todayLogs = computed(() =>
  pendingSorted.value.slice(0, 4).map((s) => ({
    ...s,
    overdue: s.diff < 0,
    dateText:
      s.diff === 0 ? '今天' :
      s.diff === -1 ? '昨天' :
      s.diff < -1 ? `${Math.abs(s.diff)} 天前` : '即将到期'
  }))
)

const remaining = computed(() => Math.max(0, pendingSorted.value.length - todayLogs.value.length))

const pendingAll = computed(
  () => allPetLogs.value.filter((s) => !s.done && s.diff <= 0).length
)
const pendingOf = (petId) =>
  allPetLogs.value.filter((s) => s.petId === petId && !s.done && s.diff <= 0).length

const filterName = computed(() =>
  petFilter.value === 'all' ? '所有宠物' : pets.value.find((p) => p.id === petFilter.value)?.name || '这只宠物'
)

const logStats = computed(() => {
  const all = scopedLogs.value
  return {
    overdue: all.filter((s) => !s.done && s.diff < 0).length,
    today: all.filter((s) => !s.done && s.diff === 0).length,
    done: all.filter((s) => s.done).length
  }
})

async function markDone(r) {
  try {
    await toggleScheduleDone(r.id, !r.done)
    for (const pid in schedMap.value) {
      const it = schedMap.value[pid].find((x) => x.id === r.id)
      if (it) {
        it.done = !r.done
        break
      }
    }
    schedMap.value = { ...schedMap.value }
    showToast(`已完成「${r.title}」`, { type: 'success' })
  } catch (e) {
    showToast(e?.message || '操作失败', { type: 'error' })
  }
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

// 贴士轮播：一行提示点击即切换，避免占用独立区块
const tipIndex = ref(0)
const tip = computed(() => tips[tipIndex.value % tips.length])
function nextTip() {
  tipIndex.value = (tipIndex.value + 1) % tips.length
}

/* ---------- 多样化问候：时段 × 星期 × 宠物状态 ---------- */

const GREETINGS = {
  dawn: ['夜深了', '早点休息'],
  morning: ['早安', '早上好'],
  noon: ['午安', '中午好'],
  afternoon: ['下午好', '午后好'],
  evening: ['晚上好', '晚安']
}
const WEEK_EXTRA = { 1: '新的一周，从照顾好它开始', 5: '周五了，周末带它出去走走' }
const HOUR_EXTRA = {
  dawn: '它都睡了，你也早点休息',
  morning: '别忘了给它准备早餐',
  noon: '午间陪它玩十分钟吧',
  afternoon: '下午好，看看它今天状态如何',
  evening: '今晚的散步安排上了吗'
}

const greeting = computed(() => {
  const h = new Date().getHours()
  const wk = new Date().getDay()
  const slot =
    h < 6 ? 'dawn' :
    h < 11 ? 'morning' :
    h < 14 ? 'noon' :
    h < 18 ? 'afternoon' : 'evening'
  const options = GREETINGS[slot]
  const text = options[Math.floor(Math.random() * options.length)]
  const sub = WEEK_EXTRA[wk] || HOUR_EXTRA[slot]
  return { text, sub }
})

const todayText = computed(() => {
  const d = new Date()
  const wk = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]
  return `${wk} · ${d.getMonth() + 1}.${String(d.getDate()).padStart(2, '0')}`
})

async function loadTrend(petId) {
  if (!petId) return
  try {
    trend.value = await fetchPetTrend(petId)
  } catch {
    trend.value = []
  }
}

watch(current, (i) => {
  if (pets.value[i]) loadTrend(pets.value[i].id)
})

onMounted(async () => {
  try {
    const [u, ps, sm, tm, anns] = await Promise.all([
      fetchUser(),
      fetchPets(),
      fetchPetSchedule(),
      fetchScheduleTypes(),
      fetchAnnouncements(true)
    ])
    user.value = u || { name: '' }
    pets.value = ps || []
    schedMap.value = sm || {}
    typeMeta.value = tm || {}
    announcements.value = anns || []
    if (pets.value.length) await loadTrend(pets.value[current.value].id)
  } catch (e) {
    showToast(e?.message || '首页加载失败', { type: 'error' })
  }
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
.greet-sub {
  margin-top: 6px;
  font-size: 12.5px;
  color: var(--color-muted);
}
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
  border: 1px solid var(--hairline);
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
  border-radius: var(--radius-xl);
  padding: 24px 20px;
  overflow: hidden;
  box-shadow: var(--shadow-2);
  color: var(--color-surface);
}
/* 单层极淡环境光，避免多团渐变叠加造成的"渐变过载" */
.hero-deco {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(
    18rem 14rem at 90% -14%,
    rgba(232, 85, 43, 0.22),
    transparent 62%
  );
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
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.22);
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
/* 区块右上「查看全部」：统一为可点击的弱强调文字 */
.sec-link {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-muted);
  transition: color var(--dur-fast) var(--ease-out);
}
.sec-link:active { color: var(--color-accent-ink); }
.sec-link svg { transform: rotate(180deg); }

/* ---------- 今日提醒大卡：统计 + 筛选 + 列表一体 ---------- */
.today-card {
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
  overflow: hidden;
}
.today-card .log-strip {
  padding: 16px 18px;
  border-bottom: 1px solid var(--hairline);
}
.today-card .log-cell b { font-size: 26px; }

/* 宠物筛选 chips：默认「全部」，横向可滑 */
.pet-filter {
  display: flex;
  gap: 8px;
  padding: 12px 14px;
  overflow-x: auto;
  scrollbar-width: none;
  border-bottom: 1px solid var(--hairline);
}
.pet-filter::-webkit-scrollbar { display: none; }
.pf-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 5px 13px 5px 6px;
  border-radius: var(--radius-pill);
  background: transparent;
  box-shadow: inset 0 0 0 1px var(--color-border);
  font-weight: 700;
  font-size: 13px;
  color: var(--color-muted);
  transition: all var(--dur-fast) var(--ease-out);
}
.pf-chip.on {
  color: var(--color-ink);
  background: var(--color-surface-2);
  box-shadow: inset 0 0 0 1px transparent;
}
.pf-chip:active { transform: scale(0.95); }
.pf-ava.all {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--grad-ink);
  color: var(--color-surface);
}
.pf-num {
  min-width: 17px;
  height: 17px;
  padding: 0 4px;
  border-radius: 999px;
  background: var(--color-accent);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  display: grid;
  place-items: center;
}

/* 卡内列表：扁平行 + 发丝分隔，取代独立浮卡 */
.today-card .reminders { padding: 4px 14px 12px; gap: 0; }
.today-card .reminder {
  background: transparent;
  box-shadow: none;
  border: none;
  border-radius: 0;
  padding: 12px 0;
}
.today-card .reminder + .reminder { border-top: 1px solid var(--hairline); }
.today-card .reminder.watch { background: var(--color-accent-soft); }
.today-card .reminder.watch .rem-label { color: var(--color-accent-ink); }
.today-card .log-empty { margin: 12px 0; }

/* 「全部」视图下的宠物名标签 */
.rem-pet {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  padding: 2px 8px 2px 3px;
  border-radius: var(--radius-pill);
  margin-right: 6px;
  vertical-align: -1px;
  flex-shrink: 0;
}
.rem-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 13px 0 2px;
  font-size: 12.5px;
  font-weight: 700;
  color: var(--color-muted);
}
.rem-more svg { transform: rotate(180deg); }

/* ---------- 今日日志与提醒 ---------- */
.log-strip {
  display: flex;
  align-items: center;
  padding: 13px 18px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
  margin-bottom: 10px;
}
.log-cell { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.log-cell b {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  line-height: 1;
}
.log-cell b.warn { color: var(--color-accent-ink); }
.log-cell span { font-size: 11px; font-weight: 700; letter-spacing: 0.06em; color: var(--color-faint); }
.log-sep { width: 1px; height: 26px; background: var(--hairline); }
.log-empty {
  font-size: 13px;
  color: var(--color-muted);
  line-height: 1.7;
  padding: 14px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px dashed var(--hairline-strong);
}
.log-empty .lnk { color: var(--color-accent-ink); font-weight: 700; }

.reminders { display: flex; flex-direction: column; gap: 10px; }
.reminder {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
  border: 1px solid var(--hairline);
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
.rem-ic.coral { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.rem-ic.sand { background: var(--color-surface-2); color: var(--color-muted); }
.rem-ic.peach { background: var(--color-sage-soft); color: var(--color-watch); }
.rem-ic.ink { background: var(--color-surface-2); color: var(--color-ink-2); }
.reminder.watch { border-color: rgba(200, 67, 31, 0.22); }
.rem-body { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.rem-label { font-weight: 700; font-size: 15px; }
.rem-date { font-size: 12px; color: var(--color-muted); margin-top: 2px; }
.rem-done {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-accent-ink);
  padding: 8px 4px 8px 12px;
  flex-shrink: 0;
}

/* ---------- 快捷工具条：弱化为单行小入口 ---------- */
.tool-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.tool {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  padding: 14px 4px 12px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  transition: transform var(--dur-fast) var(--ease-out);
}
.tool:active { transform: scale(0.95); }
.tool-ic {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: var(--color-sage-soft);
  color: var(--color-ink);
}
.tool.accent .tool-ic {
  background: var(--grad-coral);
  color: #fff;
  box-shadow: 0 6px 14px rgba(214, 80, 42, 0.24);
}
.tool-label { font-size: 12px; font-weight: 700; }

/* ---------- 本周趋势 ---------- */
.trend {
  display: flex;
  align-items: stretch;
  gap: 18px;
  padding: 20px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
  border: 1px solid var(--hairline);
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

/* ---------- 贴士：一行轻量提示条 ---------- */
.tip-line {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  margin-top: 12px;
  padding: 11px 14px;
  border-radius: var(--radius-md);
  background: var(--color-sage-soft);
  border: 1px solid var(--hairline);
  text-align: left;
  transition: transform var(--dur-fast) var(--ease-out);
}
.tip-line:active { transform: scale(0.978); }
.tl-ic {
  display: grid;
  place-items: center;
  color: var(--color-good);
  flex-shrink: 0;
}
.tl-text {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  color: var(--color-ink-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tl-text b { color: var(--color-ink); font-weight: 700; }
.tl-arrow { color: var(--color-faint); transform: rotate(180deg); flex-shrink: 0; }

/* ---------- 社区引流：描边卡，克制处理 ---------- */
.discover {
  margin-top: 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
  color: var(--color-ink);
  transition: transform var(--dur-fast) var(--ease-out);
}
.discover:active { transform: scale(0.978); }
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
