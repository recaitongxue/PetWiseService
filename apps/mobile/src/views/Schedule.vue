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

    <!-- AI 一键设置：按档案生成整套养护周期，是日程模块的核心入口 -->
    <button class="ai-card" type="button" v-reveal="{ delay: 30 }" @click="openAI">
      <span class="ai-ic"><AppIcon name="sparkle" :size="18" /></span>
      <span class="ai-body">
        <span class="ai-t">AI 一键设置日程</span>
        <span class="ai-s">读取宠物档案，自动生成疫苗 / 驱虫 / 体检 / 喂养整套计划</span>
      </span>
      <span class="ai-go">立即生成</span>
    </button>

    <!-- 宠物筛选 -->
    <div class="filters" v-reveal="{ delay: 50 }">
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

    <!-- 类型筛选 -->
    <div class="filters type-filters" v-reveal="{ delay: 70 }">
      <button
        v-for="t in typeTabs"
        :key="t.key"
        class="f-chip sm"
        :class="{ on: typeFilter === t.key }"
        type="button"
        @click="typeFilter = t.key"
      >{{ t.label }}</button>
    </div>

    <!-- 概览 -->
    <div class="summary" v-reveal="{ delay: 90 }">
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
      <span class="sm-sep" aria-hidden="true"></span>
      <div class="sm-cell">
        <b class="num">{{ memos.length }}</b>
        <span>备忘</span>
      </div>
    </div>

    <!-- 待办时间轴 -->
    <section v-if="pending.length" class="group" v-reveal="{ delay: 110 }">
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
              <span v-else-if="it.days === 0" class="tl-flag today">今天</span>
            </div>
            <div class="tl-meta">
              <span class="num">{{ it.dateText }}</span>
              <span v-if="it.time" class="tl-time num">
                <AppIcon name="bell" :size="11" /> {{ it.time }}
              </span>
              <span class="tl-dot-sep">·</span>
              <span>{{ it.petName }}</span>
              <span v-if="it.cycle" class="tl-cycle">{{ it.cycle }}</span>
            </div>
            <p v-if="it.note" class="tl-note">{{ it.note }}</p>
          </div>
          <button class="tl-check" type="button" aria-label="标记完成" @click="toggle(it)">
            <AppIcon name="check" :size="15" />
          </button>
        </article>
      </div>
    </section>

    <!-- 已完成 -->
    <section v-if="done.length" class="group" v-reveal="{ delay: 140 }">
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
          <div class="tl-ops">
            <button v-if="it.custom" class="tl-del" type="button" aria-label="删除" @click="remove(it)">
              <AppIcon name="x" :size="13" />
            </button>
            <button class="tl-undo" type="button" @click="toggle(it)">撤销</button>
          </div>
        </article>
      </div>
    </section>

    <p v-if="!rows.length && !memos.length" class="empty">
      暂无日程。点右上角 + 手动添加，或用 AI 一键生成整套计划。
    </p>

    <!-- 备忘录 -->
    <section class="group" v-reveal="{ delay: 160 }">
      <h3 class="g-title">
        备忘录
        <span class="g-count num">{{ memos.length }}</span>
      </h3>
      <div class="memo-add">
        <input
          v-model="memoText"
          class="memo-input"
          type="text"
          placeholder="记一笔：零食柜在阳台 / 周末寄养联系…"
          @keyup.enter="submitMemo"
        />
        <button class="memo-btn" type="button" :disabled="!memoText.trim()" @click="submitMemo">
          保存
        </button>
      </div>
      <div v-if="memos.length" class="memo-list">
        <article v-for="m in memos" :key="m.id" class="memo-item" :class="{ pinned: m.pinned }">
          <button class="memo-pin" type="button" :aria-label="m.pinned ? '取消置顶' : '置顶'" @click="pin(m)">
            <AppIcon name="bookmark" :size="14" />
          </button>
          <p class="memo-text">{{ m.text }}</p>
          <span class="memo-time num">{{ memoTime(m.createdAt) }}</span>
          <button class="memo-del" type="button" aria-label="删除备忘" @click="del(m)">
            <AppIcon name="x" :size="13" />
          </button>
        </article>
      </div>
    </section>

    <!-- AI 一键设置面板 -->
    <transition name="sheet">
      <div v-if="aiOpen" class="sheet-mask" @click.self="aiOpen = false">
        <div class="sheet tall">
          <div class="sheet-grip" aria-hidden="true"></div>
          <h3 class="sheet-title">
            <AppIcon name="sparkle" :size="16" /> AI 一键设置日程
          </h3>
          <p class="sheet-sub">为哪只宠物生成计划？</p>

          <div class="type-chips">
            <button
              v-for="p in pets"
              :key="p.id"
              type="button"
              class="type-chip"
              :class="{ on: aiPetId === p.id }"
              @click="aiPetId = p.id"
            >
              <PetAvatar :species="p.species" :name="p.name" :size="16" :ring="false" />
              {{ p.name }}
            </button>
          </div>

          <!-- 生成中：分步提示，比单纯转圈更可信 -->
          <div v-if="aiPhase === 'thinking'" class="ai-thinking">
            <span class="ai-dots"><i></i><i></i><i></i></span>
            <p class="ai-step">{{ aiStep }}</p>
          </div>

          <!-- 生成结果：可勾选 -->
          <template v-else-if="aiPhase === 'done'">
            <p class="ai-result-t">
              已生成 <b class="num">{{ plan.length }}</b> 条计划，勾选后一键添加：
            </p>
            <ul class="plan-list">
              <li v-for="(p, i) in plan" :key="i" :class="{ off: !picked[i] }">
                <button class="plan-check" type="button" :aria-label="picked[i] ? '取消勾选' : '勾选'" @click="picked[i] = !picked[i]">
                  <AppIcon :name="picked[i] ? 'check' : 'plus'" :size="13" />
                </button>
                <span class="plan-dot" :class="typeOf(p.type).tone">
                  <AppIcon :name="typeOf(p.type).icon" :size="14" />
                </span>
                <span class="plan-body">
                  <span class="plan-name">{{ p.title }}</span>
                  <span class="plan-meta num">{{ fmtDate(p.date, daysOf(p.date)) }}<template v-if="p.time"> · {{ p.time }}</template> · {{ p.cycle }}</span>
                  <span class="plan-note">{{ p.note }}</span>
                </span>
              </li>
            </ul>
          </template>

          <button
            v-if="aiPhase === 'idle'"
            class="f-submit"
            type="button"
            @click="generate"
          >开始生成</button>
          <button
            v-else-if="aiPhase === 'done'"
            class="f-submit"
            type="button"
            :disabled="!pickedCount"
            @click="applyPlan"
          >一键添加 {{ pickedCount }} 条日程</button>
        </div>
      </div>
    </transition>

    <!-- 添加日程 -->
    <transition name="sheet">
      <div v-if="addOpen" class="sheet-mask" @click.self="addOpen = false">
        <div class="sheet">
          <div class="sheet-grip" aria-hidden="true"></div>
          <h3 class="sheet-title">添加日程</h3>
          <p class="sheet-sub">为宠物建立疫苗、驱虫、体检或喂养提醒</p>

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
              <span>提醒时间</span>
              <input v-model="form.time" class="f-input" type="time" />
            </label>
          </div>
          <div class="f-row">
            <label class="f-field">
              <span>重复周期</span>
              <select v-model="form.cycle" class="f-input">
                <option value="">不重复</option>
                <option value="每天">每天</option>
                <option value="每周一次">每周一次</option>
                <option value="每月一次">每月一次</option>
                <option value="每季度一次">每季度一次</option>
                <option value="每半年一次">每半年一次</option>
                <option value="每年一次">每年一次</option>
              </select>
            </label>
            <label class="f-field">
              <span>归属宠物</span>
              <select v-model="form.petId" class="f-input">
                <option v-for="p in pets" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </label>
          </div>
          <input v-model="form.note" class="f-input mt" type="text" placeholder="备注（可选），如：接种前一周完成驱虫" />

          <button class="f-submit" type="button" :disabled="!canSubmit" @click="submit">保存日程</button>
        </div>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import {
  fetchPets, fetchPetSchedule, fetchScheduleTypes, aiSchedulePlan, batchSchedule,
  createSchedule, toggleScheduleDone, removeSchedule,
  fetchMemos, addMemo, pinMemo, removeMemo
} from '@/api/data'
import { showToast } from '@shared/toast'

const filter = ref('all')
const typeFilter = ref('all')
const addOpen = ref(false)
const memos = ref([])
const memoText = ref('')

const pets = ref([])
// 后端按 petId 分组的日程（系统周期条目 + 自建条目已合并）
const schedMap = ref({})
const scheduleTypes = ref({})

// 后端类型字典比 mock 多了 medication / feed：未知类型退到 other，图标与色调不落空
const NEUTRAL_TYPE = { label: '日程', icon: 'calendar', tone: 'ink' }
function typeOf(t) {
  return scheduleTypes.value[t] || scheduleTypes.value.other || NEUTRAL_TYPE
}

const typeList = [
  { key: 'vaccine', label: '疫苗' },
  { key: 'deworm', label: '驱虫' },
  { key: 'check', label: '体检' },
  { key: 'weight', label: '称重' },
  { key: 'groom', label: '洗护' },
  { key: 'feed', label: '喂养' },
  { key: 'other', label: '自定义' }
]

const typeTabs = [
  { key: 'all', label: '全部' },
  ...typeList
]

/* ---------- AI 一键设置 ---------- */

const aiOpen = ref(false)
const aiPetId = ref(null)
const aiPhase = ref('idle') // idle → thinking → done
const aiStep = ref('')
const plan = ref([])
const picked = ref([])

const AI_STEPS = ['正在读取宠物档案…', '匹配品种养护周期…', '核对疫苗与驱虫时间…', '生成计划中…']

function aiPet() {
  return pets.value.find((p) => p.id === aiPetId.value) || pets.value[0] || null
}

function openAI() {
  aiPetId.value = filter.value === 'all' ? (pets.value[0]?.id ?? null) : filter.value
  aiPhase.value = 'idle'
  plan.value = []
  picked.value = []
  aiOpen.value = true
}

async function generate() {
  const pet = aiPet()
  if (!pet) {
    showToast('暂无宠物档案', { type: 'error' })
    return
  }
  aiPhase.value = 'thinking'
  let i = 0
  aiStep.value = AI_STEPS[0]
  const timer = setInterval(() => {
    i += 1
    if (i < AI_STEPS.length) aiStep.value = AI_STEPS[i]
  }, 520)
  try {
    const res = await aiSchedulePlan(pet.id)
    clearInterval(timer)
    // 已存在的同名日程不再重复推荐
    const existing = new Set((schedMap.value[pet.id] || []).map((x) => x.title))
    plan.value = ((res && res.items) || []).filter((x) => !existing.has(x.title))
    picked.value = plan.value.map(() => true)
    aiPhase.value = 'done'
  } catch (e) {
    clearInterval(timer)
    aiPhase.value = 'idle'
    showToast(e?.message || '生成失败，请稍后重试', { type: 'error' })
  }
}

const pickedCount = computed(() => picked.value.filter(Boolean).length)

async function applyPlan() {
  const pet = aiPet()
  if (!pet) return
  const items = plan.value.filter((_, i) => picked.value[i])
  try {
    const res = await batchSchedule(pet.id, items)
    const n = (res && res.created && res.created.length) || items.length
    schedMap.value = await fetchPetSchedule()
    aiOpen.value = false
    showToast(`已为「${pet.name}」添加 ${n} 条日程`, { type: 'success' })
  } catch (e) {
    showToast(e?.message || '添加失败', { type: 'error' })
  }
}

/* ---------- 列表数据 ---------- */

const today = new Date()
const todayISO = toISO(today)

function toISO(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function daysOf(iso) {
  return Math.round((new Date(iso) - today) / 86400000)
}

// 后端已合并「系统周期条目 + 自建条目」，完成态直接取 item.done
const rows = computed(() => {
  const out = []
  Object.keys(schedMap.value || {}).forEach((pid) => {
    ;(schedMap.value[pid] || []).forEach((s) => {
      const meta = typeOf(s.type)
      const petId = s.petId ?? Number(pid)
      const pet = pets.value.find((p) => p.id === petId)
      out.push({
        ...s,
        petId,
        petName: s.petName || (pet ? pet.name : '未指定'),
        icon: meta.icon,
        tone: meta.tone,
        typeLabel: meta.label
      })
    })
  })

  return out
    .filter((x) => filter.value === 'all' || x.petId === filter.value)
    .filter((x) => typeFilter.value === 'all' || x.type === typeFilter.value)
    .map((x) => {
      const diff = daysOf(x.date)
      return {
        ...x,
        overdue: diff < 0,
        days: diff,
        dateText: fmtDate(x.date, diff)
      }
    })
    .sort((a, b) => {
      if (a.done !== b.done) return a.done ? 1 : -1
      return a.date < b.date ? -1 : 1
    })
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

async function toggle(it) {
  const next = !it.done
  try {
    await toggleScheduleDone(it.id, next)
    schedMap.value = await fetchPetSchedule()
    showToast(next ? `已完成「${it.title}」` : `已撤销「${it.title}」`, {
      type: next ? 'success' : 'info'
    })
  } catch (e) {
    showToast(e?.message || '操作失败', { type: 'error' })
  }
}

async function remove(it) {
  try {
    await removeSchedule(it.id)
    schedMap.value = await fetchPetSchedule()
    showToast('日程已删除', { type: 'info' })
  } catch (e) {
    showToast(e?.message || '删除失败', { type: 'error' })
  }
}

/* ---------- 备忘录 ---------- */

async function loadMemos() {
  const list = await fetchMemos()
  // 后端只返回 time（'YYYY-MM-DD HH:mm'），补 createdAt 供模板时间格式化使用
  memos.value = (list || []).map((m) => ({
    ...m,
    createdAt: m.createdAt || Date.parse(String(m.time || '').replace(' ', 'T')) || Date.now()
  }))
}

async function submitMemo() {
  const text = memoText.value.trim()
  if (!text) return
  try {
    await addMemo({ text, petId: filter.value === 'all' ? null : filter.value })
    await loadMemos()
    memoText.value = ''
    showToast('已记到备忘录', { type: 'success' })
  } catch (e) {
    showToast(e?.message || '保存失败', { type: 'error' })
  }
}

async function del(m) {
  try {
    await removeMemo(m.id)
    await loadMemos()
  } catch (e) {
    showToast(e?.message || '删除失败', { type: 'error' })
  }
}

async function pin(m) {
  try {
    await pinMemo(m.id, !m.pinned)
    await loadMemos()
  } catch (e) {
    showToast(e?.message || '操作失败', { type: 'error' })
  }
}

function memoTime(ts) {
  const d = new Date(ts)
  return `${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
}

/* ---------- 手动添加 ---------- */

const form = reactive({
  type: 'vaccine',
  title: '',
  date: todayISO,
  time: '',
  cycle: '',
  note: '',
  petId: ''
})

const canSubmit = computed(() => form.title.trim() && form.date)

function openAdd() {
  form.petId = filter.value === 'all' ? (pets.value[0]?.id ?? '') : filter.value
  addOpen.value = true
}

async function submit() {
  try {
    await createSchedule({
      type: form.type,
      title: form.title.trim(),
      date: form.date,
      time: form.time || '',
      cycle: form.cycle || '',
      note: form.note.trim(),
      petId: form.petId
    })
    schedMap.value = await fetchPetSchedule()
    addOpen.value = false
    form.title = ''
    form.note = ''
    form.time = ''
    form.cycle = ''
    showToast('日程已保存', { type: 'success' })
  } catch (e) {
    showToast(e?.message || '保存失败', { type: 'error' })
  }
}

onMounted(async () => {
  try {
    const [ps, sm, tm] = await Promise.all([
      fetchPets(),
      fetchPetSchedule(),
      fetchScheduleTypes()
    ])
    pets.value = ps || []
    schedMap.value = sm || {}
    scheduleTypes.value = tm || {}
    if (pets.value.length) {
      form.petId = pets.value[0].id
      aiPetId.value = pets.value[0].id
    }
  } catch (e) {
    showToast(e?.message || '日程加载失败', { type: 'error' })
  }
  try {
    await loadMemos()
  } catch {
    memos.value = []
  }
})
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

/* ---------- AI 一键设置入口 ---------- */
.ai-card {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  text-align: left;
  padding: 14px 15px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--color-sage-soft), var(--color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--color-accent) 18%, transparent);
  margin-bottom: 16px;
  transition: transform var(--dur-fast) var(--ease-out);
}
.ai-card:active { transform: scale(0.985); }
.ai-ic {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 13px;
  display: grid;
  place-items: center;
  background: var(--color-surface);
  color: var(--color-accent-ink);
  box-shadow: var(--shadow-soft);
}
.ai-body { flex: 1; display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.ai-t { font-family: var(--font-display); font-weight: 700; font-size: 15px; }
.ai-s { font-size: 11.5px; color: var(--color-ink-2); line-height: 1.5; }
.ai-go {
  flex-shrink: 0;
  font-size: 12.5px;
  font-weight: 700;
  color: #fff;
  background: var(--color-accent);
  padding: 8px 13px;
  border-radius: var(--radius-pill);
}

/* ---------- 筛选 ---------- */
.filters {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  overflow-x: auto;
  scrollbar-width: none;
}
.filters::-webkit-scrollbar { display: none; }
.type-filters { margin-bottom: 16px; }
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
.f-chip.sm { padding: 5px 12px; font-size: 12px; }
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
  display: flex;
  align-items: center;
  gap: 6px;
}
.g-count {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-faint);
  background: var(--color-surface-2);
  border-radius: var(--radius-pill);
  padding: 1px 7px;
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
.tl-dot.ink { background: var(--color-surface-2); color: var(--color-ink-2); }
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
.tl-flag.today { background: var(--color-sage-soft); color: var(--color-good); }
.tl-meta {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 3px;
  font-size: 12px;
  color: var(--color-muted);
}
.tl-time {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-weight: 700;
  color: var(--color-ink-2);
}
.tl-dot-sep { color: var(--color-faint); }
.tl-cycle {
  margin-left: 2px;
  padding: 1px 7px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-2);
  font-size: 11px;
}
.tl-note {
  margin-top: 5px;
  font-size: 12px;
  line-height: 1.55;
  color: var(--color-faint);
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
.tl-ops { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
.tl-del {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--color-faint);
}
.tl-del:active { background: var(--color-surface-2); color: var(--color-accent-ink); }
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
  line-height: 1.7;
  color: var(--color-faint);
}

/* ---------- 备忘录 ---------- */
.memo-add {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.memo-input {
  flex: 1;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  border: 1px dashed var(--hairline-strong);
  background: var(--color-surface);
  font: inherit;
  font-size: 14px;
  color: var(--color-ink);
  outline: none;
}
.memo-input:focus { border-color: var(--color-accent); border-style: solid; }
.memo-btn {
  flex-shrink: 0;
  padding: 0 16px;
  border-radius: var(--radius-md);
  background: var(--color-ink);
  color: var(--color-surface);
  font-size: 13.5px;
  font-weight: 700;
}
.memo-btn:disabled { opacity: 0.4; }
.memo-list { display: flex; flex-direction: column; gap: 8px; }
.memo-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 11px 12px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
}
.memo-item.pinned { border-color: color-mix(in srgb, var(--color-watch) 40%, transparent); }
.memo-pin {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--color-faint);
}
.memo-item.pinned .memo-pin { color: var(--color-watch); }
.memo-pin:active { background: var(--color-surface-2); }
.memo-text {
  flex: 1;
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--color-ink-2);
  word-break: break-all;
}
.memo-time { flex-shrink: 0; font-size: 11px; color: var(--color-faint); }
.memo-del {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--color-faint);
}
.memo-del:active { background: var(--color-surface-2); color: var(--color-accent-ink); }

/* ---------- 底部面板 ---------- */
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
  max-height: 86dvh;
  overflow-y: auto;
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
  display: flex;
  align-items: center;
  gap: 7px;
}
.sheet-sub {
  font-size: 13px;
  color: var(--color-muted);
  margin: 4px 0 16px;
}

/* AI 生成动效 */
.ai-thinking {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 34px 0 26px;
}
.ai-dots { display: inline-flex; gap: 6px; }
.ai-dots i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--color-accent);
  animation: bounce 1.2s var(--ease-in-out) infinite;
}
.ai-dots i:nth-child(2) { animation-delay: 0.18s; }
.ai-dots i:nth-child(3) { animation-delay: 0.36s; }
@keyframes bounce { 0%,100%{transform:translateY(0);opacity:0.4} 50%{transform:translateY(-6px);opacity:1} }
.ai-step { font-size: 13.5px; font-weight: 600; color: var(--color-muted); }

.ai-result-t { font-size: 13px; color: var(--color-muted); margin-bottom: 12px; }
.ai-result-t b { color: var(--color-accent-ink); }
.plan-list { list-style: none; display: flex; flex-direction: column; gap: 9px; }
.plan-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--hairline);
  background: var(--color-bg);
  transition: opacity var(--dur-fast);
}
.plan-list li.off { opacity: 0.45; }
.plan-check {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  margin-top: 1px;
  border: 1px solid var(--hairline-strong);
  color: var(--color-muted);
  background: var(--color-surface);
}
.plan-list li:not(.off) .plan-check {
  background: var(--color-good);
  border-color: var(--color-good);
  color: #fff;
}
.plan-dot {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  background: var(--color-sage-soft);
  color: var(--color-good);
}
.plan-dot.coral { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.plan-dot.sand { background: var(--color-surface-2); color: var(--color-muted); }
.plan-dot.peach { background: var(--color-sage-soft); color: var(--color-watch); }
.plan-dot.ink { background: var(--color-surface-2); color: var(--color-ink-2); }
.plan-body { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.plan-name { font-size: 14px; font-weight: 700; }
.plan-meta { font-size: 11.5px; font-weight: 700; color: var(--color-accent-ink); }
.plan-note { font-size: 11.5px; color: var(--color-faint); line-height: 1.5; }

.type-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.type-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
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
.f-input.mt { margin-top: 10px; }
.f-input:focus { outline: 2px solid var(--color-accent); outline-offset: -1px; }
.f-row {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}
.f-field { flex: 1; display: flex; flex-direction: column; gap: 5px; min-width: 0; }
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

@media (prefers-reduced-motion: reduce) {
  .ai-dots i { animation: none; }
}
</style>
