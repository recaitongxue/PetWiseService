<template>
  <section class="screen pet">
    <header class="pet-head">
      <button class="back" type="button" @click="goBack" aria-label="返回">
        <AppIcon name="back" :size="22" />
      </button>
      <span class="pet-head-title">{{ pet?.name || '宠物' }}的档案</span>
      <span class="back"></span>
    </header>

    <template v-if="pet">
      <!-- 头像 + 基本信息 -->
      <div class="pet-hero" v-reveal>
        <PetAvatar :species="pet.species" :name="pet.name" :size="84" :ring="false" />
        <div class="pet-hero-info">
          <h2 class="pet-hero-name">{{ pet.name }}</h2>
          <p class="pet-hero-breed">{{ pet.breed }} · {{ pet.gender }}</p>
          <span class="pet-hero-pill">{{ pet.tagline }}</span>
        </div>
        <span class="pet-hero-ring">
          <HealthRing :value="pet.healthScore" label="健康分" :size="92" />
        </span>
      </div>

      <!-- 数据块 -->
      <div class="pet-stats" v-reveal="{ delay: 80 }">
        <div class="pstat">
          <b class="num">{{ pet.weight }}</b><span>kg 体重</span>
        </div>
        <div class="pstat">
          <b class="num">{{ pet.age }}</b><span>岁 年龄</span>
        </div>
        <div class="pstat">
          <b>{{ pet.nextVaccine.slice(5) }}</b><span>下次疫苗</span>
        </div>
      </div>

      <!-- 快捷 -->
      <div class="pet-actions" v-reveal="{ delay: 120 }">
        <router-link
          :to="{ path: '/consult/ai', query: { pet: pet.name, note: `${pet.breed} · ${pet.age}岁 · ${pet.weight}kg` } }"
          class="pact ink"
        >
          <AppIcon name="stethoscope" :size="20" /> 智能问诊
        </router-link>
        <router-link to="/recognize" class="pact accent">
          <AppIcon name="camera" :size="20" /> 拍照识别
        </router-link>
      </div>

      <!-- 体重趋势 -->
      <section class="block" v-reveal="{ delay: 160 }">
        <div class="block-head">
          <h3 class="block-title">体重趋势</h3>
          <button class="block-act" type="button" @click="openRecord('weight')">＋ 记录体重</button>
        </div>
        <div class="weight-chart">
          <div v-for="w in weightHistory" :key="w.m" class="wc-col">
            <span class="wc-val num">{{ w.w }}</span>
            <div class="wc-bar-wrap">
              <span class="wc-bar" :style="{ height: barH(w.w) }"></span>
            </div>
            <span class="wc-month num">{{ w.m }}</span>
          </div>
        </div>
        <p class="wc-foot">
          当前 {{ pet.weight }}kg ·
          <span :class="trendState">{{ trendText }}</span>
        </p>
      </section>

      <!-- 免疫与护理日程 -->
      <section class="block" v-reveal="{ delay: 200 }">
        <div class="block-head">
          <h3 class="block-title">免疫与护理日程</h3>
          <span class="block-hint">近期</span>
        </div>
        <ul class="timeline">
          <li v-for="s in schedule" :key="s.date" class="tl-item">
            <span class="tl-dot" :class="s.state"></span>
            <div class="tl-body">
              <div class="tl-row">
                <span class="tl-title">{{ s.title }}</span>
                <span class="tl-date num">{{ s.date.slice(5) }}</span>
              </div>
              <span class="tl-type" :class="s.type">{{ typeLabel(s.type) }}</span>
            </div>
          </li>
        </ul>
      </section>

      <!-- 健康记录 -->
      <section class="block" v-reveal="{ delay: 240 }">
        <div class="block-head">
          <h3 class="block-title">健康记录</h3>
          <button class="block-act" type="button" @click="openRecord('care')">＋ 添加</button>
        </div>
        <ul class="timeline">
          <li v-for="r in records" :key="r.id || r.date" class="tl-item">
            <span class="tl-dot" :class="r.state"></span>
            <div class="tl-body">
              <div class="tl-row">
                <span class="tl-title">{{ r.title }}</span>
                <span class="tl-date num">{{ r.date }}</span>
              </div>
              <p class="tl-desc">{{ r.desc }}</p>
            </div>
            <button
              v-if="r.custom"
              class="tl-del"
              type="button"
              aria-label="删除记录"
              @click="del(r.id)"
            >
              <AppIcon name="x" :size="14" />
            </button>
          </li>
        </ul>
      </section>
    </template>

    <p v-else class="empty">未找到该宠物档案。</p>

    <!-- 录入健康记录（置于 v-if/v-else 之后，避免打断条件链） -->
    <transition name="sheet">
      <div v-if="recOpen" class="sheet-mask" @click.self="recOpen = false">
        <div class="sheet">
          <div class="sheet-grip" aria-hidden="true"></div>
          <h3 class="sheet-title">添加健康记录</h3>
          <p class="sheet-sub">为 {{ pet?.name }} 记一笔，数据会同步到趋势图</p>

          <div class="type-chips">
            <button
              v-for="k in kinds"
              :key="k.key"
              type="button"
              class="type-chip"
              :class="{ on: form.kind === k.key }"
              @click="form.kind = k.key"
            >{{ k.label }}</button>
          </div>

          <div class="f-row">
            <label class="f-field">
              <span>日期</span>
              <input v-model="form.date" class="f-input" type="date" />
            </label>
            <label v-if="form.kind === 'weight'" class="f-field">
              <span>体重 (kg)</span>
              <input v-model="form.value" class="f-input" type="number" step="0.1" placeholder="4.6" />
            </label>
          </div>

          <textarea
            v-model="form.note"
            class="f-input f-area"
            rows="3"
            :placeholder="form.kind === 'weight' ? '备注，如：饭后称重' : '记录具体情况…'"
          ></textarea>

          <button class="f-submit" type="button" :disabled="!canSave" @click="save">保存记录</button>
        </div>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { computed, ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import HealthRing from '@/components/HealthRing.vue'
import {
  fetchPet, fetchWeights, fetchPetSchedule,
  fetchHealthRecords, addHealthRecord, removeHealthRecord
} from '@/api/data'
import { showToast } from '@shared/toast'

const route = useRoute()
const router = useRouter()
const petId = route.params.id

const pet = ref(null)
const weightBase = ref([])
const schedMap = ref({})
// 用户录入的健康记录（后端 GET /pets/{id}/records）
const customRecs = ref([])

function goBack() {
  router.back()
}

async function loadRecords(id) {
  customRecs.value = await fetchHealthRecords(id)
}

// 体重趋势 = 后端月度体重 + 用户录入的体重（同月取最新一条，图表随之更新）
const weightHistory = computed(() => {
  const base = (weightBase.value || []).map((x) => ({ ...x }))
  const mine = customRecs.value
    .filter((r) => r.petId === pet.value?.id && r.kind === 'weight' && r.value)
    .slice()
    .sort((a, b) => (a.date < b.date ? -1 : 1))

  const byMonth = {}
  mine.forEach((r) => {
    byMonth[`${Number(r.date.slice(5, 7))}月`] = Number(r.value)
  })
  Object.entries(byMonth).forEach(([m, w]) => {
    const hit = base.find((x) => x.m === m)
    if (hit) hit.w = w
    else base.push({ m, w })
  })
  return base.sort((a, b) => parseInt(a.m) - parseInt(b.m))
})
// 日程按 petId 分组返回
const schedule = computed(() => (pet.value && schedMap.value[pet.value.id]) || [])

const maxW = computed(() => Math.max(...weightHistory.value.map((w) => w.w), 1))
function barH(w) {
  return Math.round((w / maxW.value) * 100) + '%'
}
const trendText = computed(() => {
  const list = weightHistory.value
  if (list.length < 2) return '数据不足'
  const diff = list[list.length - 1].w - list[list.length - 2].w
  if (diff > 0.05) return '较上月略增'
  if (diff < -0.05) return '较上月略减'
  return '保持稳定'
})
const trendState = computed(() =>
  trendText.value.includes('增') || trendText.value.includes('减') ? 'watch' : 'good'
)

function typeLabel(t) {
  return {
    vaccine: '疫苗', deworm: '驱虫', check: '体检', weight: '体重',
    groom: '洗护', feed: '喂食', medication: '喂药'
  }[t] || '护理'
}

// 内置记录 + 用户记录，用户记录排在前（按录入顺序，最新的在上）
const records = computed(() => {
  const mine = customRecs.value
    .filter((r) => r.petId === pet.value?.id)
    .map((r) => ({
      id: r.id,
      custom: true,
      date: r.date,
      title: kindLabel(r.kind),
      desc: r.kind === 'weight' ? `体重 ${r.value} kg${r.note ? ' · ' + r.note : ''}` : r.note || '—',
      state: r.kind === 'symptom' ? 'watch' : 'good'
    }))
  return [
    ...mine,
    {
      date: pet.value?.nextVaccine || '2026-11-02',
      title: '年度疫苗提醒',
      desc: '距离下次免疫还有一段时间，建议提前一周预约。',
      state: 'watch'
    },
    {
      date: '2026-09-12',
      title: '体态评估',
      desc: pet.value?.species === 'dog' ? '体重略偏高，建议增加日常运动量。' : '体态标准，被毛光亮。',
      state: 'good'
    },
    {
      date: '2026-08-03',
      title: '驱虫完成',
      desc: '体内外驱虫已按计划完成，下次驱虫 3 个月后。',
      state: 'good'
    }
  ]
})

/* ---------------- 录入 ---------------- */
const kinds = [
  { key: 'weight', label: '体重' },
  { key: 'diet', label: '饮食' },
  { key: 'symptom', label: '症状' },
  { key: 'care', label: '护理' }
]

const recOpen = ref(false)
const form = reactive({
  kind: 'weight',
  date: new Date().toISOString().slice(0, 10),
  value: '',
  note: ''
})

const canSave = computed(() => {
  if (!form.date) return false
  return form.kind === 'weight' ? Boolean(form.value) : Boolean(form.note.trim())
})

function kindLabel(k) {
  return { weight: '体重记录', diet: '饮食记录', symptom: '症状记录', care: '护理记录' }[k] || '记录'
}

function openRecord(kind) {
  form.kind = kind
  form.note = ''
  form.value = kind === 'weight' ? String(pet.value?.weight ?? '') : ''
  recOpen.value = true
}

async function save() {
  if (!pet.value?.id) return
  try {
    await addHealthRecord(pet.value.id, {
      kind: form.kind,
      record_date: form.date,
      weight: form.kind === 'weight' ? Number(form.value) : null,
      note: form.note.trim() || null
    })
    recOpen.value = false
    await loadRecords(pet.value.id)
    showToast(form.kind === 'weight' ? '体重已记录，趋势图已更新' : '记录已保存', { type: 'success' })
  } catch (e) {
    showToast(e?.message || '保存失败', { type: 'error' })
  }
}

async function del(id) {
  try {
    await removeHealthRecord(id)
    await loadRecords(pet.value.id)
    showToast('记录已删除')
  } catch (e) {
    showToast(e?.message || '删除失败', { type: 'error' })
  }
}

onMounted(async () => {
  try {
    const [p, ws, sm] = await Promise.all([
      fetchPet(petId).catch(() => null),
      fetchWeights(petId).catch(() => []),
      fetchPetSchedule().catch(() => ({}))
    ])
    // nextVaccine 后端可为空，模板直接 slice(5) → 兜成空串避免报错
    pet.value = p ? { ...p, nextVaccine: p.nextVaccine || '' } : null
    weightBase.value = ws || []
    schedMap.value = sm || {}
    if (pet.value) await loadRecords(petId)
  } catch (e) {
    showToast(e?.message || '档案加载失败', { type: 'error' })
  }
})
</script>

<style scoped>
.pet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 4px 12px;
}
.back {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--color-ink);
}
.pet-head-title { font-family: var(--font-display); font-weight: 700; font-size: var(--fs-lg); }

.pet-hero {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  background: linear-gradient(150deg, var(--color-sage-soft), #eef3e8);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-1);
}
.pet-hero-info { flex: 1; }
.pet-hero-name { font-family: var(--font-display); font-weight: 700; font-size: var(--fs-xl); line-height: 1; }
.pet-hero-breed { font-size: 14px; color: var(--color-ink-2); margin-top: 4px; }
.pet-hero-pill {
  display: inline-block;
  margin-top: 10px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-sage);
  background: rgba(255, 255, 255, 0.6);
  padding: 4px 12px;
  border-radius: var(--radius-pill);
}
.pet-hero-ring { flex-shrink: 0; }

.pet-stats {
  display: flex;
  gap: 10px;
  margin: 16px 0;
}
.pstat {
  flex: 1;
  text-align: center;
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  border-radius: var(--radius-md);
  padding: 14px 0;
}
.pstat b { display: block; font-family: var(--font-display); font-size: var(--fs-lg); line-height: 1; }
.pstat span { font-size: 12px; color: var(--color-muted); }

.pet-actions { display: flex; gap: 12px; }
.pact {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  border-radius: var(--radius-pill);
  font-weight: 700;
  font-size: 15px;
  color: #fff;
  transition: transform var(--dur-fast) var(--ease-out);
}
.pact:active { transform: scale(0.97); }
.pact.ink { background: var(--color-ink); }
.pact.accent { background: linear-gradient(140deg, var(--color-accent), var(--color-accent-ink)); }

.block { margin-top: 28px; }
.block-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14px;
}
.block-title { font-family: var(--font-display); font-weight: 700; font-size: var(--fs-lg); }
.block-hint { font-size: 12px; font-weight: 700; letter-spacing: 0.08em; color: var(--color-accent-ink); text-transform: uppercase; }

/* 体重趋势 */
.weight-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 6px;
  height: 150px;
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  border-radius: var(--radius-lg);
  padding: 16px 12px 12px;
}
.wc-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  height: 100%;
  justify-content: flex-end;
}
.wc-val { font-size: 11px; color: var(--color-muted); font-weight: 700; }
.wc-bar-wrap { flex: 1; width: 100%; display: flex; align-items: flex-end; justify-content: center; }
.wc-bar {
  width: 56%;
  max-width: 18px;
  border-radius: 8px 8px 4px 4px;
  background: linear-gradient(180deg, var(--color-sage), #6c8a66);
  transition: height 0.9s var(--ease-out);
}
.wc-month { font-size: 11px; color: var(--color-muted); }
.wc-foot {
  font-size: 13px;
  color: var(--color-ink-2);
  margin-top: 10px;
}
.wc-foot .good { color: var(--color-good); font-weight: 700; }
.wc-foot .watch { color: var(--color-watch); font-weight: 700; }

/* 时间线 */
.timeline { position: relative; padding-left: 8px; }
.tl-item {
  position: relative;
  display: flex;
  gap: 16px;
  padding-bottom: 20px;
}
.tl-item::before {
  content: '';
  position: absolute;
  left: 16px;
  top: 22px;
  bottom: -2px;
  width: 2px;
  background: var(--color-border);
}
.tl-item:last-child::before { display: none; }
.tl-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  margin-top: 4px;
  flex-shrink: 0;
  border: 3px solid var(--color-bg);
  background: var(--color-sage);
  z-index: 1;
}
.tl-dot.good { background: var(--color-good); }
.tl-dot.watch { background: var(--color-watch); }
.tl-body { flex: 1; }
.tl-row { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
.tl-title { font-weight: 700; font-size: 15px; }
.tl-date { font-size: 12px; color: var(--color-muted); }
.tl-desc { font-size: 13px; color: var(--color-ink-2); margin-top: 3px; line-height: 1.55; }
.tl-type {
  display: inline-block;
  margin-top: 6px;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  color: var(--color-sage);
  background: var(--color-sage-soft);
}
.tl-type.vaccine { color: var(--color-accent-ink); background: var(--color-accent-soft); }
.tl-type.deworm { color: var(--color-good); background: var(--color-sage-soft); }
.tl-type.weight { color: var(--color-watch); background: #fbe7d2; }

.empty { text-align: center; color: var(--color-muted); margin-top: 60px; }

/* ---------- 区块「新增」操作 ---------- */
.block-act {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-accent-ink);
  padding: 4px 2px;
}
.block-act:active { opacity: 0.6; }

/* 删除自定义记录 */
.tl-del {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--color-faint);
  transition: all var(--dur-fast) var(--ease-out);
}
.tl-del:active { background: var(--color-accent-soft); color: var(--color-accent-ink); }

/* ---------- 录入面板 ---------- */
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
.sheet-title { font-family: var(--font-display); font-size: 19px; font-weight: 700; }
.sheet-sub { font-size: 13px; color: var(--color-muted); margin: 4px 0 16px; }

.type-chips { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }
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
.f-area { margin-top: 10px; resize: none; line-height: 1.5; }

.f-row { display: flex; gap: 10px; }
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
