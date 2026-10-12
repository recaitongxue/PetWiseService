<template>
  <section class="screen">
    <header class="screen-head" v-reveal>
      <div>
        <p class="eyebrow">SCHEDULE</p>
        <h1 class="title">日程与提醒</h1>
      </div>
      <button class="add-btn" type="button" aria-label="添加日程" @click="openAdd">
        <AppIcon name="plus" :size="20" />
      </button>
    </header>

    <!-- 宠物筛选 -->
    <div class="filters" v-reveal="{ delay: 40 }">
      <button
        class="f-chip"
        :class="{ on: filter === 'all' }"
        type="button"
        @click="filter = 'all'"
      >全部</button>
      <button
        v-for="p in pets"
        :key="p.id"
        class="f-chip"
        :class="{ on: filter === p.id }"
        type="button"
        @click="filter = p.id"
      >
        <PetAvatar :species="p.species" :name="p.name" :size="18" :ring="false" />
        {{ p.name }}
      </button>
    </div>

    <!-- 概览 -->
    <div class="summary" v-reveal="{ delay: 80 }">
      <div class="sm-cell">
        <b class="num">{{ pending.length }}</b>
        <span>待办</span>
      </div>
      <span class="sm-sep" aria-hidden="true"></span>
      <div class="sm-cell">
        <b class="num" :class="{ warn: overdue.length > 0 }">{{ overdue.length }}</b>
        <span>已逾期</span>
      </div>
      <span class="sm-sep" aria-hidden="true"></span>
      <div class="sm-cell">
        <b class="num">{{ done.length }}</b>
        <span>已完成</span>
      </div>
    </div>

    <!-- 待办时间轴 -->
    <section v-if="pending.length" class="group" v-reveal="{ delay: 120 }">
      <h3 class="g-title">待办</h3>
      <div class="timeline">
        <article
          v-for="it in pending"
          :key="it.id"
          class="tl-item"
          :class="{ overdue: it.overdue }"
        >
          <span class="tl-dot" :class="it.tone"><AppIcon :name="it.icon" :size="16" /></span>
          <div class="tl-body">
            <div class="tl-top">
              <span class="tl-name">{{ it.title }}</span>
              <span v-if="it.overdue" class="tl-flag">逾期</span>
            </div>
            <div class="tl-meta">
              <span class="num">{{ it.dateText }}</span>
              <span class="tl-dot-sep">·</span>
              <span>{{ it.petName }}</span>
              <span v-if="it.cycle" class="tl-cycle">{{ it.cycle }}</span>
            </div>
          </div>
          <button class="tl-check" type="button" aria-label="标记完成" @click="toggle(it)">
            <AppIcon name="check" :size="15" />
          </button>
        </article>
      </div>
    </section>

    <!-- 已完成 -->
    <section v-if="done.length" class="group" v-reveal="{ delay: 160 }">
      <h3 class="g-title">已完成</h3>
      <div class="timeline">
        <article v-for="it in done" :key="it.id" class="tl-item is-done">
          <span class="tl-dot done"><AppIcon name="check" :size="15" /></span>
          <div class="tl-body">
            <span class="tl-name">{{ it.title }}</span>
            <div class="tl-meta">
              <span class="num">{{ it.dateText }}</span>
              <span class="tl-dot-sep">·</span>
              <span>{{ it.petName }}</span>
            </div>
          </div>
          <button class="tl-undo" type="button" aria-label="撤销完成" @click="toggle(it)">
            撤销
          </button>
        </article>
      </div>
    </section>

    <p v-if="!rows.length" class="empty">这只宠物暂无日程，点右上角 + 添加一条。</p>

    <!-- 添加日程 -->
    <transition name="sheet">
      <div v-if="addOpen" class="sheet-mask" @click.self="addOpen = false">
        <div class="sheet">
          <div class="sheet-grip" aria-hidden="true"></div>
          <h3 class="sheet-title">添加日程</h3>
          <p class="sheet-sub">为宠物建立疫苗、驱虫或体检提醒</p>

          <div class="type-chips">
            <button
              v-for="t in typeList"
              :key="t.key"
              type="button"
              class="type-chip"
              :class="{ on: form.type === t.key }"
              @click="form.type = t.key"
            >{{ t.label }}</button>
          </div>

          <input v-model="form.title" class="f-input" type="text" placeholder="日程名称，如：年度疫苗" />
          <div class="f-row">
            <label class="f-field">
              <span>日期</span>
              <input v-model="form.date" class="f-input" type="date" />
            </label>
            <label class="f-field">
              <span>归属宠物</span>
              <select v-model="form.petId" class="f-input">
                <option v-for="p in pets" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </label>
          </div>

          <button class="f-submit" type="button" :disabled="!canSubmit" @click="submit">保存日程</button>
        </div>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import { pets, petSchedule, scheduleTypes } from '@/data/mock'
import {
  doneScheduleIds,
  toggleScheduleDone,
  customScheduleItems,
  addScheduleItem
} from '@/data/ops'
import { showToast } from '@/composables/toast'

const filter = ref('all')
const addOpen = ref(false)
const doneIds = ref(doneScheduleIds())
const custom = ref(customScheduleItems())

const typeList = [
  { key: 'vaccine', label: '疫苗' },
  { key: 'deworm', label: '驱虫' },
  { key: 'check', label: '体检' },
  { key: 'weight', label: '称重' },
  { key: 'groom', label: '洗护' },
  { key: 'other', label: '自定义' }
]

const today = new Date()
const todayISO = toISO(today)

function toISO(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// 合并内置日程与用户自定义日程
const rows = computed(() => {
  const out = []
  const push = (petId, s) => {
    const meta = scheduleTypes[s.type] || scheduleTypes.other
    const pet = pets.find((p) => p.id === petId)
    out.push({
      ...s,
      petId,
      petName: pet ? pet.name : '未指定',
      icon: meta.icon,
      tone: meta.tone,
      typeLabel: meta.label
    })
  }
  Object.keys(petSchedule).forEach((pid) => {
    petSchedule[pid].forEach((s) => push(pid, s))
  })
  custom.value.forEach((s) => push(s.petId, s))

  return out
    .filter((x) => filter.value === 'all' || x.petId === filter.value)
    .map((x) => {
      const d = new Date(x.date)
      const diff = Math.round((d - today) / 86400000)
      return {
        ...x,
        overdue: diff < 0,
        days: diff,
        dateText: fmtDate(x.date, diff),
        done: doneIds.value.includes(x.id)
      }
    })
    .sort((a, b) => (a.date < b.date ? -1 : 1))
})

function fmtDate(iso, diff) {
  const [, m, d] = iso.split('-')
  const label = `${Number(m)}.${d}`
  if (diff === 0) return `今天 ${label}`
  if (diff === 1) return `明天 ${label}`
  if (diff === 2) return `后天 ${label}`
  if (diff < 0) return `${label}（${Math.abs(diff)} 天前）`
  if (diff <= 7) return `${label}（${diff} 天后）`
  return label
}

const pending = computed(() => rows.value.filter((x) => !x.done))
const done = computed(() => rows.value.filter((x) => x.done))
const overdue = computed(() => pending.value.filter((x) => x.overdue))

function toggle(it) {
  const nowDone = toggleScheduleDone(it.id)
  doneIds.value = doneScheduleIds()
  showToast(nowDone ? `已完成「${it.title}」` : `已撤销「${it.title}」`, {
    type: nowDone ? 'success' : 'info'
  })
}

const form = reactive({
  type: 'vaccine',
  title: '',
  date: todayISO,
  petId: pets[0].id
})

const canSubmit = computed(() => form.title.trim() && form.date)

function openAdd() {
  form.petId = filter.value === 'all' ? pets[0].id : filter.value
  addOpen.value = true
}

function submit() {
  addScheduleItem({
    type: form.type,
    title: form.title.trim(),
    date: form.date,
    petId: form.petId
  })
  custom.value = customScheduleItems()
  addOpen.value = false
  form.title = ''
  showToast('日程已保存', { type: 'success' })
}
</script>

<style scoped>
.title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-xl);
  letter-spacing: -0.02em;
  margin-top: 4px;
}

.add-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
  color: var(--color-ink);
  transition: transform var(--dur-fast) var(--ease-out);
}
.add-btn:active { transform: scale(0.94); }

/* ---------- 筛选 ---------- */
.filters {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  overflow-x: auto;
  scrollbar-width: none;
}
.filters::-webkit-scrollbar { display: none; }
.f-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 7px 14px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--hairline);
  font-size: 13px;
  font-weight: 700;
  color: var(--color-muted);
  background: transparent;
  transition: all var(--dur-fast) var(--ease-out);
}
.f-chip.on {
  color: var(--color-ink);
  background: var(--color-surface);
  border-color: var(--hairline-strong);
  box-shadow: var(--shadow-soft);
}

/* ---------- 概览 ---------- */
.summary {
  display: flex;
  align-items: center;
  padding: 16px 18px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
  margin-bottom: 24px;
}
.sm-cell {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.sm-cell b {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.02em;
}
.sm-cell b.warn { color: var(--color-accent-ink); }
.sm-cell span {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--color-faint);
}
.sm-sep {
  width: 1px;
  height: 30px;
  background: var(--hairline);
}

/* ---------- 分组 ---------- */
.group { margin-bottom: 26px; }
.g-title {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  color: var(--color-muted);
  margin-bottom: 12px;
  padding-left: 2px;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.tl-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
}
.tl-item.overdue { border-color: rgba(200, 67, 31, 0.22); }
.tl-item.is-done { opacity: 0.58; }

.tl-dot {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  flex-shrink: 0;
  background: var(--color-sage-soft);
  color: var(--color-good);
}
.tl-dot.coral { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.tl-dot.sand { background: var(--color-surface-2); color: var(--color-muted); }
.tl-dot.peach { background: var(--color-sage-soft); color: var(--color-watch); }
.tl-dot.done { background: var(--color-sage-soft); color: var(--color-good); }

.tl-body { flex: 1; min-width: 0; }
.tl-top { display: flex; align-items: center; gap: 6px; }
.tl-name {
  font-weight: 700;
  font-size: 15px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tl-flag {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: var(--radius-pill);
  background: var(--color-accent-soft);
  color: var(--color-accent-ink);
}
.tl-meta {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 3px;
  font-size: 12px;
  color: var(--color-muted);
}
.tl-dot-sep { color: var(--color-faint); }
.tl-cycle {
  margin-left: 2px;
  padding: 1px 7px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-2);
  font-size: 11px;
}

.tl-check {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border: 1px solid var(--hairline-strong);
  color: var(--color-muted);
  transition: all var(--dur-fast) var(--ease-out);
}
.tl-check:active {
  background: var(--color-good);
  border-color: var(--color-good);
  color: #fff;
  transform: scale(0.9);
}
.tl-undo {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-muted);
  padding: 8px 4px;
}

.empty {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: var(--color-faint);
}

/* ---------- 添加面板 ---------- */
.sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: rgba(27, 42, 34, 0.36);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.sheet {
  width: 100%;
  max-width: var(--shell-max);
  background: var(--color-surface);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  padding: 10px 20px 28px;
}
.sheet-grip {
  width: 38px;
  height: 4px;
  border-radius: 999px;
  background: var(--color-border-strong);
  margin: 0 auto 16px;
}
.sheet-title {
  font-family: var(--font-display);
  font-size: 19px;
  font-weight: 700;
}
.sheet-sub {
  font-size: 13px;
  color: var(--color-muted);
  margin: 4px 0 16px;
}
.type-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.type-chip {
  padding: 7px 13px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--hairline);
  font-size: 13px;
  font-weight: 700;
  color: var(--color-muted);
  transition: all var(--dur-fast) var(--ease-out);
}
.type-chip.on {
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  border-color: transparent;
}
.f-input {
  width: 100%;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--hairline-strong);
  background: var(--color-bg);
  font: inherit;
  font-size: 15px;
  color: var(--color-ink);
}
.f-input:focus { outline: 2px solid var(--color-accent); outline-offset: -1px; }
.f-row {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}
.f-field { flex: 1; display: flex; flex-direction: column; gap: 5px; }
.f-field span { font-size: 12px; font-weight: 700; color: var(--color-muted); }
.f-submit {
  width: 100%;
  margin-top: 18px;
  padding: 15px;
  border-radius: var(--radius-pill);
  background: var(--color-ink);
  color: var(--color-surface);
  font-size: 16px;
  font-weight: 700;
  transition: opacity var(--dur-fast);
}
.f-submit:disabled { opacity: 0.4; }

.sheet-enter-active,
.sheet-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.sheet-enter-from,
.sheet-leave-to { opacity: 0; }
.sheet-enter-active .sheet,
.sheet-leave-active .sheet { transition: transform var(--dur-base) var(--ease-out); }
.sheet-enter-from .sheet,
.sheet-leave-to .sheet { transform: translateY(100%); }
</style>
