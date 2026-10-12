<template>
  <section class="screen pre">
    <header class="r-head">
      <button class="back" type="button" @click="prevOrBack" aria-label="返回">
        <AppIcon name="back" :size="22" />
      </button>
      <div class="h-mid">
        <span class="r-title">结构化问诊</span>
        <span class="h-step num">{{ stepIndex + 1 }}/{{ steps.length }}</span>
      </div>
      <span class="back"></span>
    </header>

    <div class="prog">
      <span class="prog-bar" :style="{ width: ((stepIndex + 1) / steps.length) * 100 + '%' }"></span>
    </div>

    <!-- 高危信号即时提示：不打断问卷，但明确告知需线下急诊 -->
    <transition name="rise">
      <div v-if="redFlags.length" class="rf">
        <span class="rf-ic"><AppIcon name="alert" :size="17" /></span>
        <div class="rf-body">
          <p class="rf-t">{{ redFlags[0].label }} 属于高危信号</p>
          <p class="rf-s">建议立即线下急诊，问卷可继续填完，报告可带给医生看</p>
        </div>
        <button class="rf-btn" type="button" @click="toER">急诊医生</button>
      </div>
    </transition>

    <!-- 步骤内容 -->
    <div class="stage">
      <p class="q-eyebrow">{{ steps[stepIndex].eyebrow }}</p>
      <h2 class="q-title">{{ steps[stepIndex].title }}</h2>
      <p class="q-sub" v-if="steps[stepIndex].sub">{{ steps[stepIndex].sub }}</p>

      <!-- 0 · 选择宠物 -->
      <div v-if="stepIndex === 0" class="opts">
        <button
          v-for="p in pets"
          :key="p.id"
          class="opt pet"
          :class="{ on: petId === p.id }"
          type="button"
          @click="petId = p.id"
        >
          <PetAvatar :species="p.species" :name="p.name" :size="32" :ring="false" />
          <span class="opt-body">
            <span class="opt-t">{{ p.name }}</span>
            <span class="opt-d">{{ p.breed }} · {{ p.age }}岁 · {{ p.weight }}kg</span>
          </span>
          <span class="tick"><AppIcon name="check" :size="14" /></span>
        </button>
      </div>

      <!-- 1 · 部位 -->
      <div v-else-if="stepIndex === 1" class="chips">
        <button
          v-for="b in bodyParts"
          :key="b.id"
          class="chip"
          :class="{ on: partId === b.id }"
          type="button"
          @click="pickPart(b.id)"
        >
          <AppIcon :name="b.icon" :size="14" />
          {{ b.label }}
        </button>
      </div>

      <!-- 2 · 症状 -->
      <div v-else-if="stepIndex === 2" class="opts">
        <button
          v-for="s in curPart.symptoms"
          :key="s.id"
          class="opt"
          :class="{ on: symptomIds.includes(s.id), danger: s.redFlag }"
          type="button"
          @click="toggleSymptom(s.id)"
        >
          <span class="opt-body">
            <span class="opt-t">{{ s.label }}</span>
            <span v-if="s.redFlag" class="opt-flag">高危信号</span>
          </span>
          <span class="tick"><AppIcon name="check" :size="14" /></span>
        </button>
      </div>

      <!-- 3 · 持续时间 -->
      <div v-else-if="stepIndex === 3" class="opts">
        <button
          v-for="d in durations"
          :key="d.id"
          class="opt"
          :class="{ on: durationId === d.id }"
          type="button"
          @click="durationId = d.id"
        >
          <span class="opt-body"><span class="opt-t">{{ d.label }}</span></span>
          <span class="tick"><AppIcon name="check" :size="14" /></span>
        </button>
      </div>

      <!-- 4 · 严重程度 -->
      <div v-else-if="stepIndex === 4" class="opts">
        <button
          v-for="s in severities"
          :key="s.id"
          class="opt"
          :class="{ on: severityId === s.id }"
          type="button"
          @click="severityId = s.id"
        >
          <span class="opt-body"><span class="opt-t">{{ s.label }}</span></span>
          <span class="tick"><AppIcon name="check" :size="14" /></span>
        </button>
      </div>

      <!-- 5 · 伴随症状 -->
      <div v-else-if="stepIndex === 5" class="opts">
        <button
          v-for="a in accompanyOptions"
          :key="a.id"
          class="opt"
          :class="{ on: accompanyIds.includes(a.id) }"
          type="button"
          @click="toggleAccompany(a.id)"
        >
          <span class="opt-body"><span class="opt-t">{{ a.label }}</span></span>
          <span class="tick"><AppIcon name="check" :size="14" /></span>
        </button>
      </div>

      <!-- 6 · 补充 -->
      <div v-else class="extra">
        <textarea
          v-model="note"
          class="note"
          rows="4"
          placeholder="补充症状细节，例如：挠右耳 3 天，耳道有褐色分泌物，精神食欲正常。"
        ></textarea>
        <button class="attach" type="button" @click="attach">
          <AppIcon name="image" :size="18" />
          {{ photos ? '已添加 1 张患处照片' : '添加患处照片' }}
        </button>
        <p class="extra-tip">清晰照片能显著提升判断准确度（光线充足、对焦在患处）</p>
      </div>
    </div>

    <!-- 底部导航 -->
    <div class="nav">
      <button v-if="stepIndex > 0" class="nav-prev" type="button" @click="stepIndex--">上一步</button>
      <button class="nav-next" :class="{ full: stepIndex === 0 }" type="button" :disabled="!canNext" @click="next">
        {{ stepIndex === steps.length - 1 ? '生成问诊报告' : '下一步' }}
        <AppIcon name="back" :size="15" class="nav-arrow" />
      </button>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import { pets, bodyParts, durations, severities, accompanyOptions } from '@/data/mock'
import { scoreTriage } from '@/data/triage'
import { saveReport } from '@/data/ops'
import { showToast } from '@/composables/toast'

const router = useRouter()

const steps = [
  { eyebrow: 'STEP 1', title: '是哪只宠物不舒服？', sub: '品种、年龄与体重会影响判断' },
  { eyebrow: 'STEP 2', title: '主要不舒服在哪个部位？', sub: '选最接近的一项' },
  { eyebrow: 'STEP 3', title: '具体有哪些表现？', sub: '可多选，越具体判断越准' },
  { eyebrow: 'STEP 4', title: '这种情况持续多久了？', sub: '' },
  { eyebrow: 'STEP 5', title: '目前的精神与进食状态？', sub: '' },
  { eyebrow: 'STEP 6', title: '还有以下伴随情况吗？', sub: '可多选，没有可跳过' },
  { eyebrow: 'STEP 7', title: '还有什么想补充的？', sub: '选填' }
]

const stepIndex = ref(0)
const petId = ref(pets[0].id)
const partId = ref('')
const symptomIds = ref([])
const durationId = ref('')
const severityId = ref('')
const accompanyIds = ref([])
const note = ref('')
const photos = ref(0)

const curPart = computed(() => bodyParts.find((b) => b.id === partId.value) || { symptoms: [] })
const redFlags = computed(() => curPart.value.symptoms.filter((s) => s.redFlag && symptomIds.value.includes(s.id)))

const canNext = computed(() => {
  switch (stepIndex.value) {
    case 0: return !!petId.value
    case 1: return !!partId.value
    case 2: return symptomIds.value.length > 0
    case 3: return !!durationId.value
    case 4: return !!severityId.value
    default: return true
  }
})

// 注意：模板中 ref 会自动解包，因此这里直接操作 ref.value，不接收模板传入的数组
function toggleSymptom(id) {
  const i = symptomIds.value.indexOf(id)
  if (i >= 0) symptomIds.value.splice(i, 1)
  else symptomIds.value.push(id)
}

function toggleAccompany(id) {
  const i = accompanyIds.value.indexOf(id)
  if (i >= 0) accompanyIds.value.splice(i, 1)
  else accompanyIds.value.push(id)
}

function pickPart(id) {
  if (partId.value !== id) symptomIds.value = []
  partId.value = id
}

function attach() {
  photos.value = 1
  showToast('演示环境已模拟添加一张患处照片', { type: 'info' })
}

function prevOrBack() {
  if (stepIndex.value > 0) stepIndex.value--
  else router.back()
}

function next() {
  if (!canNext.value) return
  if (stepIndex.value < steps.length - 1) {
    stepIndex.value++
    return
  }

  // 最后一步：跑分诊引擎 → 生成报告
  const answers = {
    petId: petId.value,
    partId: partId.value,
    symptomIds: symptomIds.value.slice(),
    durationId: durationId.value,
    severityId: severityId.value,
    accompanyIds: accompanyIds.value.slice()
  }
  const triage = scoreTriage(answers)
  const pet = pets.find((p) => p.id === petId.value)
  const partLabel = (bodyParts.find((b) => b.id === partId.value) || {}).label || ''
  const symptomLabels = curPart.value.symptoms
    .filter((s) => symptomIds.value.includes(s.id))
    .map((s) => s.label)

  const report = saveReport({
    type: 'ai',
    petId: petId.value,
    petName: pet ? pet.name : '',
    title: `${pet ? pet.name : ''} · ${symptomLabels[0] || partLabel}`,
    preview: `${triage.label} — ${triage.short}`,
    chief: {
      partLabel,
      symptomLabels,
      durationLabel: (durations.find((d) => d.id === durationId.value) || {}).label || '',
      severityLabel: (severities.find((s) => s.id === severityId.value) || {}).label || '',
      accompanyLabels: accompanyOptions
        .filter((a) => accompanyIds.value.includes(a.id))
        .map((a) => a.label),
      note: note.value.trim(),
      photos: photos.value
    },
    triage
  })

  router.replace(`/report/${report.id}`)
}

function toER() {
  router.push({ path: '/doctors', query: { dept: 'er' } })
}
</script>

<style scoped>
.r-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0 10px;
}
.back { width: 40px; height: 40px; display: grid; place-items: center; border-radius: 50%; flex-shrink: 0; }
.h-mid { display: flex; flex-direction: column; align-items: center; }
.r-title { font-family: var(--font-display); font-weight: 700; font-size: var(--fs-lg); }
.h-step { font-size: 11px; color: var(--color-faint); font-weight: 700; margin-top: 1px; }

.prog {
  height: 3px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-2);
  overflow: hidden;
}
.prog-bar {
  display: block;
  height: 100%;
  border-radius: var(--radius-pill);
  background: var(--color-accent);
  transition: width var(--dur-base) var(--ease-out);
}

/* ---------- 高危提示 ---------- */
.rf {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
  padding: 12px 13px;
  border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--color-alert) 10%, white);
  border: 1px solid color-mix(in srgb, var(--color-alert) 40%, transparent);
}
.rf-ic {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  background: var(--color-alert);
  color: #fff;
  flex-shrink: 0;
}
.rf-body { flex: 1; min-width: 0; }
.rf-t { font-size: 13.5px; font-weight: 700; color: var(--color-alert); }
.rf-s { font-size: 11.5px; color: var(--color-ink-2); margin-top: 2px; line-height: 1.45; }
.rf-btn {
  flex-shrink: 0;
  font-size: 12.5px;
  font-weight: 700;
  color: #fff;
  background: var(--color-alert);
  padding: 7px 12px;
  border-radius: var(--radius-pill);
}

/* ---------- 题目区 ---------- */
.stage { margin-top: 26px; }
.q-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: var(--color-accent-ink);
}
.q-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 22px;
  line-height: 1.3;
  letter-spacing: -0.02em;
  margin-top: 7px;
}
.q-sub { font-size: 13px; color: var(--color-muted); margin-top: 6px; }

/* 选项列表 */
.opts { display: flex; flex-direction: column; gap: 8px; margin-top: 20px; }
.opt {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 13px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--hairline);
  background: var(--color-surface);
  text-align: left;
  transition: border-color var(--dur-fast), background var(--dur-fast);
}
.opt.on {
  border-color: var(--color-accent);
  background: var(--color-accent-soft);
}
.opt.danger.on {
  border-color: var(--color-alert);
  background: color-mix(in srgb, var(--color-alert) 8%, white);
}
.opt-body { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.opt-t { font-size: 14.5px; font-weight: 600; }
.opt-d { font-size: 12px; color: var(--color-muted); }
.opt-flag {
  align-self: flex-start;
  margin-top: 3px;
  font-size: 10.5px;
  font-weight: 700;
  color: var(--color-alert);
  background: color-mix(in srgb, var(--color-alert) 12%, white);
  padding: 2px 7px;
  border-radius: var(--radius-pill);
}
.tick {
  width: 21px;
  height: 21px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  border: 1px solid var(--hairline-strong);
  color: transparent;
  flex-shrink: 0;
  transition: background var(--dur-fast), color var(--dur-fast), border-color var(--dur-fast);
}
.opt.on .tick {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}
.opt.danger.on .tick { background: var(--color-alert); border-color: var(--color-alert); }

/* 部位 chips */
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 20px; }
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--color-ink-2);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  padding: 10px 15px;
  border-radius: var(--radius-pill);
  transition: color var(--dur-fast), border-color var(--dur-fast), background var(--dur-fast);
}
.chip.on {
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  border-color: var(--color-accent);
  font-weight: 700;
}

/* 补充 */
.extra { margin-top: 20px; }
.note {
  width: 100%;
  border: 1px solid var(--hairline-strong);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: 13px 14px;
  font-size: 14px;
  line-height: 1.65;
  color: var(--color-ink);
  font-family: inherit;
  resize: vertical;
  outline: none;
}
.note:focus-visible { border-color: var(--color-accent); }
.attach {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-top: 10px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--color-ink-2);
  background: var(--color-surface);
  border: 1px dashed var(--hairline-strong);
  padding: 11px 15px;
  border-radius: var(--radius-md);
}
.extra-tip { font-size: 11.5px; color: var(--color-faint); margin-top: 9px; line-height: 1.5; }

/* ---------- 底部导航 ---------- */
.nav {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(78px + env(safe-area-inset-bottom, 0px));
  width: min(var(--shell-max), 100%);
  display: flex;
  gap: 9px;
  padding: 11px 14px;
  background: color-mix(in srgb, var(--color-surface) 94%, transparent);
  backdrop-filter: blur(14px);
  border-top: 1px solid var(--color-border);
}
.nav-prev {
  flex-shrink: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-ink);
  background: var(--color-surface);
  border: 1px solid var(--hairline-strong);
  padding: 14px 18px;
  border-radius: var(--radius-pill);
}
.nav-next {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  background: var(--color-accent);
  padding: 14px;
  border-radius: var(--radius-pill);
  transition: transform var(--dur-fast) var(--ease-out), opacity var(--dur-fast);
}
.nav-next.full { flex: 1; }
.nav-next:active { transform: scale(0.978); }
.nav-next:disabled { opacity: 0.4; }
.nav-arrow { transform: rotate(180deg); }

.rise-enter-active, .rise-leave-active { transition: opacity var(--dur-base) var(--ease-out), transform var(--dur-base) var(--ease-out); }
.rise-enter-from, .rise-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
