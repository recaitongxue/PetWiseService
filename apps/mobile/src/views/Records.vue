<template>
  <section class="screen">
    <header class="r-head">
      <button class="back" type="button" @click="goBack" aria-label="返回">
        <AppIcon name="back" :size="22" />
      </button>
      <span class="r-title">问诊记录</span>
      <span class="back"></span>
    </header>

    <!-- 类型筛选 -->
    <div class="tabs">
      <button
        v-for="t in tabs"
        :key="t.id"
        class="tab"
        :class="{ on: tab === t.id }"
        type="button"
        @click="tab = t.id"
      >
        {{ t.label }}
        <span class="tab-n num">{{ countOf(t.id) }}</span>
      </button>
    </div>

    <p class="lede" v-reveal>智能问诊与真人医生的完整记录，可随时回看建议与处方。</p>

    <div v-if="rows.length" class="list" v-reveal="{ delay: 60 }">
      <article
        v-for="r in rows"
        :key="r.id"
        class="rec"
        :class="{ clickable: r.orderId || r.reportId }"
        @click="open(r)"
      >
        <span class="rec-ic" :class="r.type">
          <AppIcon :name="r.type === 'ai' ? 'sparkle' : 'stethoscope'" :size="17" />
        </span>
        <div class="rec-body">
          <div class="rec-top">
            <span class="rec-title">{{ r.title }}</span>
            <span class="rec-date num">{{ r.date.slice(5) }}</span>
          </div>
          <p class="rec-preview">{{ r.preview }}</p>
          <div class="rec-foot">
            <span class="rec-pet">
              <PetAvatar :species="r.species" :name="r.petName" :size="16" :ring="false" />
              {{ r.petName }}
            </span>
            <span v-if="r.type === 'human'" class="rec-doc">{{ r.doctorName }} · {{ r.modeLabel }}</span>
            <span class="rec-state" :class="r.state">{{ stateText(r) }}</span>
          </div>
        </div>
        <AppIcon v-if="r.orderId || r.reportId" name="back" :size="15" class="rec-arrow" />
      </article>
    </div>

    <p v-else class="empty">还没有这类问诊记录。</p>

    <router-link to="/preconsult" class="guide" v-reveal="{ delay: 90 }">
      <span class="g-ic"><AppIcon name="notes" :size="17" /></span>
      <span class="g-body">
        <span class="g-t">结构化问诊 · 判断更准</span>
        <span class="g-s">7 步引导收集症状，生成可带给医生的完整报告</span>
      </span>
      <AppIcon name="back" :size="15" class="g-arrow" />
    </router-link>

    <div class="cta-row">
      <router-link to="/consult/ai" class="cta" v-reveal="{ delay: 100 }">
        <AppIcon name="sparkle" :size="17" />
        AI 智能问诊
      </router-link>
      <router-link to="/doctors" class="cta solid" v-reveal="{ delay: 120 }">
        <AppIcon name="stethoscope" :size="17" />
        找真人医生
      </router-link>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import { consultModes } from '@/data/static'
import {
  fetchConsultRecords, fetchPets, fetchDoctors, fetchConsultOrders, fetchReports
} from '@/api/data'
import { showToast } from '@shared/toast'

const router = useRouter()
function goBack() {
  router.back()
}

const tabs = [
  { id: 'all', label: '全部' },
  { id: 'ai', label: '智能问诊' },
  { id: 'human', label: '真人医生' }
]
const tab = ref('all')

const modeLabel = (id) => (consultModes.find((m) => m.id === id) || {}).label || '图文'

const pets = ref([])
const doctors = ref([])
const records = ref([])
const orders = ref([])
const reports = ref([])

const idEq = (a, b) => String(a) === String(b)

// 问诊单 → 记录卡片（只保留列表需要的字段）
function fromOrder(o) {
  const pet = pets.value.find((p) => idEq(p.id, o.petId))
  const doc = doctors.value.find((d) => idEq(d.id, o.doctorId))
  const first =
    o.summary?.note || o.summary?.complaints?.[0] || o.summary?.symptoms?.[0] || '健康咨询'
  return {
    id: o.id,
    orderId: o.id,
    reportId: o.reportId || null,
    date: (o.createdAt || '').slice(0, 10),
    petId: o.petId,
    petName: pet ? pet.name : o.summary?.petName || '未指定',
    species: pet ? pet.species : 'cat',
    title: `${doc ? doc.name : ''}医生 · ${first}`.slice(0, 40),
    preview: o.summary?.note || '等待医生回复中，可在问诊室补充照片与描述。',
    state: o.state === 'closed' ? 'closed' : o.state === 'replied' ? 'replied' : 'pending',
    type: 'human',
    doctorName: doc ? doc.name : '',
    modeLabel: modeLabel(o.mode)
  }
}

// 问诊报告 → 记录卡片（结构化预问诊与真人问诊的最终产出物）
function fromReport(r) {
  const pet = pets.value.find((p) => idEq(p.id, r.petId))
  return {
    id: r.id,
    reportId: r.id,
    orderId: r.orderId || null,
    date: r.date || '',
    petId: r.petId,
    petName: pet ? pet.name : r.petName || '未指定',
    species: pet ? pet.species : 'cat',
    title: r.title || '问诊报告',
    preview: r.preview || '点击查看完整问诊报告',
    state: 'closed',
    type: r.type || 'ai',
    doctorName: r.doctor ? r.doctor.name : '',
    modeLabel: r.type === 'human' ? '问诊报告' : '预问诊报告'
  }
}

// 问诊记录：三个来源按「报告 → 问诊单 → 合并记录」排优先级，按 id 去重避免重复卡片
const all = computed(() => {
  const builtin = records.value.map((r) => {
    const pet = pets.value.find((p) => idEq(p.id, r.petId))
    const doc = doctors.value.find((d) => idEq(d.id, r.doctorId))
    return {
      ...r,
      date: r.date || '',
      petName: r.petName || (pet ? pet.name : '未指定'),
      species: pet ? pet.species : 'cat',
      doctorName: doc ? doc.name : '',
      modeLabel: modeLabel(r.mode),
      orderId: r.orderId || null,
      reportId: r.reportId || null
    }
  })

  const seen = new Set()
  return [...reports.value.map(fromReport), ...orders.value.map(fromOrder), ...builtin].filter(
    (r) => !seen.has(r.id) && seen.add(r.id)
  )
})

onMounted(async () => {
  try {
    const [ps, docs, recs, os, rs] = await Promise.all([
      fetchPets(),
      fetchDoctors(),
      fetchConsultRecords(),
      fetchConsultOrders(),
      fetchReports()
    ])
    pets.value = ps || []
    doctors.value = docs || []
    records.value = recs || []
    orders.value = os || []
    reports.value = rs || []
  } catch (e) {
    showToast(e?.message || '问诊记录加载失败', { type: 'error' })
  }
})

const rows = computed(() => (tab.value === 'all' ? all.value : all.value.filter((r) => r.type === tab.value)))

function countOf(id) {
  return id === 'all' ? all.value.length : all.value.filter((r) => r.type === id).length
}

function stateText(r) {
  if (r.type === 'ai') return '已完成'
  if (r.state === 'pending') return '待接诊'
  if (r.state === 'replied') return '医生已回复'
  return '已完成'
}

function open(r) {
  if (r.reportId) router.push(`/report/${r.reportId}`)
  else if (r.orderId) router.push(`/consultation/${r.orderId}`)
}
</script>

<style scoped>
.r-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0 12px;
}
.back { width: 40px; height: 40px; display: grid; place-items: center; border-radius: 50%; }
.r-title { font-family: var(--font-display); font-weight: 700; font-size: var(--fs-lg); }

/* ---------- 筛选 ---------- */
.tabs { display: flex; gap: 7px; }
.tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-muted);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  padding: 7px 13px;
  border-radius: var(--radius-pill);
  transition: color var(--dur-fast), border-color var(--dur-fast), background var(--dur-fast);
}
.tab.on {
  color: var(--color-ink);
  background: var(--color-surface-2);
  border-color: var(--hairline-strong);
  font-weight: 700;
}
.tab-n { font-size: 11px; color: var(--color-faint); font-weight: 700; }

.lede {
  font-size: 14px;
  color: var(--color-muted);
  line-height: 1.6;
  margin: 14px 0 18px;
}

.list { display: flex; flex-direction: column; gap: 10px; }
.rec {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
  transition: transform var(--dur-fast) var(--ease-out);
}
.rec.clickable:active { transform: scale(0.988); }
.rec-ic {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  flex-shrink: 0;
  background: var(--color-sage-soft);
  color: var(--color-good);
}
.rec-ic.ai { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.rec-body { flex: 1; min-width: 0; }
.rec-top { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
.rec-title { font-weight: 700; font-size: 15px; }
.rec-date { font-size: 12px; color: var(--color-faint); flex-shrink: 0; }
.rec-preview {
  font-size: 13px;
  color: var(--color-ink-2);
  line-height: 1.6;
  margin-top: 5px;
}
.rec-foot {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  padding-top: 9px;
  border-top: 1px solid var(--hairline);
  flex-wrap: wrap;
}
.rec-pet {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-muted);
}
.rec-doc { font-size: 11.5px; color: var(--color-faint); }
.rec-state {
  margin-left: auto;
  font-size: 11px;
  font-weight: 700;
  color: var(--color-good);
  background: var(--color-sage-soft);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}
.rec-state.pending { color: var(--color-watch); background: color-mix(in srgb, var(--color-watch) 14%, white); }
.rec-state.replied { color: var(--color-accent-ink); background: var(--color-accent-soft); }
.rec-arrow { color: var(--color-faint); transform: rotate(180deg); flex-shrink: 0; margin-top: 4px; }

.empty { text-align: center; color: var(--color-muted); font-size: 14px; margin-top: 48px; }

.guide {
  display: flex;
  align-items: center;
  gap: 11px;
  margin-top: 20px;
  padding: 13px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--hairline-strong);
  background: var(--color-surface);
  transition: transform var(--dur-fast) var(--ease-out);
}
.guide:active { transform: scale(0.988); }
.g-ic {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  background: var(--color-sage-soft);
  color: var(--color-good);
  flex-shrink: 0;
}
.g-body { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.g-t { font-size: 14px; font-weight: 700; }
.g-s { font-size: 11.5px; color: var(--color-muted); line-height: 1.45; }
.g-arrow { color: var(--color-faint); transform: rotate(180deg); flex-shrink: 0; }

.cta-row { display: flex; gap: 9px; margin-top: 12px; }
.cta {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 14px;
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  border: 1px solid var(--hairline-strong);
  font-weight: 700;
  font-size: 14px;
  transition: transform var(--dur-fast) var(--ease-out);
}
.cta:active { transform: scale(0.978); }
.cta.solid { background: var(--color-accent); color: #fff; border-color: transparent; }
</style>
