<template>
  <section class="screen consult">
    <header class="screen-head" v-reveal>
      <div>
        <p class="eyebrow">AI TRIAGE · 智能分诊</p>
        <h1 class="title">智能问诊</h1>
      </div>
      <button class="find-doc" type="button" @click="goDoctors()">
        <AppIcon name="stethoscope" :size="15" />
        找医生
      </button>
    </header>

    <!-- 问诊对象：多宠切换（AI 判断需要品种/年龄/体重上下文） -->
    <div class="pet-bar" v-reveal="{ delay: 40 }">
      <button
        v-for="p in pets"
        :key="p.id"
        class="pet-chip"
        :class="{ on: p.id === petId }"
        type="button"
        @click="petId = p.id"
      >
        <PetAvatar :species="p.species" :name="p.name" :size="18" :ring="false" />
        {{ p.name }}
      </button>
      <button class="import-btn" type="button" @click="openImport">
        <AppIcon name="notes" :size="13" />
        档案导入
      </button>
    </div>

    <!-- 免费额度 -->
    <div class="quota" v-reveal="{ delay: 60 }">
      <AppIcon name="sparkle" :size="13" />
      <span>今日 AI 免费问诊剩余 <b class="num">{{ quota.left }}/{{ quota.free }}</b> 次</span>
      <button class="quota-doc" type="button" @click="goDoctors()">升级真人</button>
    </div>

    <!-- 识别上下文横幅（从拍照识别带入） -->
    <transition name="ctx">
      <div v-if="ctx.pet" class="ctx-banner">
        <span class="ctx-ic"><AppIcon name="camera" :size="16" /></span>
        <div class="ctx-body">
          <span class="ctx-title">已关联识别结果：{{ ctx.pet }}</span>
          <span class="ctx-note" v-if="ctx.note">{{ ctx.note }}</span>
        </div>
        <button class="ctx-x" type="button" @click="ctx = { pet: '', note: '' }" aria-label="清除上下文">
          <AppIcon name="x" :size="16" />
        </button>
      </div>
    </transition>

    <!-- 急诊告警条：命中高危症状时置顶（线上问诊会延误，必须优先提示线下） -->
    <transition name="ctx">
      <div v-if="lastTriage && lastTriage.level === 'emergency'" class="er-bar">
        <span class="er-ic"><AppIcon name="alert" :size="18" /></span>
        <div class="er-body">
          <p class="er-t">检测到疑似急症信号</p>
          <p class="er-s">{{ lastTriage.short }} · 线上问诊会延误治疗</p>
        </div>
        <button class="er-btn" type="button" @click="goDoctors('er')">急诊医生</button>
      </div>
    </transition>

    <!-- 结构化问诊入口：比自由输入判断更准，且会产出可带走的报告 -->
    <router-link to="/preconsult" class="guide-cta" v-reveal="{ delay: 70 }">
      <span class="gc-ic"><AppIcon name="notes" :size="18" /></span>
      <span class="gc-body">
        <span class="gc-t">结构化问诊 · 判断更准</span>
        <span class="gc-s">7 步引导收集症状，生成可带给医生的完整报告</span>
      </span>
      <AppIcon name="back" :size="15" class="gc-arrow" />
    </router-link>

    <!-- 症状快捷标签 -->
    <div class="symptoms" v-reveal="{ delay: 80 }">
      <div v-for="g in symptomGroups" :key="g.group" class="sym-row">
        <span class="sym-g">{{ g.group }}</span>
        <div class="sym-items">
          <button
            v-for="s in g.items"
            :key="s"
            class="sym-chip"
            :class="{ on: picked.includes(s) }"
            type="button"
            @click="toggleSymptom(s)"
          >
            {{ s }}
          </button>
        </div>
      </div>
    </div>

    <!-- 推荐问题 -->
    <div class="suggest" v-reveal="{ delay: 100 }">
      <button v-for="q in consultSuggestions" :key="q" class="suggest-chip" type="button" @click="send(q)">
        {{ q }}
      </button>
    </div>

    <!-- 对话区 -->
    <div class="chat-list" ref="listEl">
      <template v-for="(m, i) in messages" :key="i">
        <!-- 档案导入卡片：AI 读取的结构化上下文 -->
        <div v-if="m.kind === 'context'" class="ctx-card">
          <header class="cc-head">
            <AppIcon name="notes" :size="14" />
            已导入宠物档案
            <span class="cc-time num">{{ m.time }}</span>
          </header>
          <ul class="cc-list">
            <li v-for="(c, j) in m.context" :key="j">{{ c }}</li>
          </ul>
        </div>
        <template v-else-if="m.kind === 'triage'">
          <TriageCard
            :level="m.triage.level"
            :label="m.triage.label"
            :short="m.triage.short"
            :advice="m.triage.advice"
            :causes="m.triage.causes"
            :actions="m.triage.actions"
            :confidence="m.triage.confidence"
            @escalate="goDoctors(m.triage.dept)"
          />
          <!-- RAG 引用：结论挂上知识库出处，可点进品种档案核实 -->
          <p v-if="m.cite" class="rag-cite">
            <AppIcon name="notes" :size="12" />
            参考知识库：{{ m.cite }}
            <router-link v-if="m.citeBreedId" :to="`/breed/${m.citeBreedId}`" class="cite-link">查看品种档案 →</router-link>
          </p>
        </template>
        <div v-else-if="m.kind === 'photo'" class="photo-bubble">
          <img :src="m.image" alt="问诊照片" @click="openPhoto(m.image)" />
          <span class="pb-time num">{{ m.time }}</span>
        </div>
        <ChatBubble
          v-else
          :role="m.role === 'me' ? 'me' : 'them'"
          :text="m.text"
          :time="m.time"
          :name="m.role === 'ai' ? 'AI' : '我'"
        />
      </template>
      <div v-if="typing" class="typing">
        <span></span><span></span><span></span>
      </div>
    </div>

    <!-- 随访建议（AI 回复后给出，自然延续对话） -->
    <transition name="ctx">
      <div v-if="followups.length" class="followups">
        <button v-for="f in followups" :key="f" class="fu-chip" type="button" @click="send(f)">
          {{ f }}
        </button>
      </div>
    </transition>

    <!-- 档案导入面板：把结构化档案/记录/识别/报告带入对话 -->
    <transition name="sheet">
      <div v-if="importOpen" class="sheet-mask" @click.self="importOpen = false">
        <div class="sheet">
          <div class="sheet-grip" aria-hidden="true"></div>
          <h3 class="sheet-title">导入宠物档案</h3>
          <p class="sheet-sub">勾选要带入对话的内容，AI 会结合这些背景判断</p>

          <div class="imp-group">
            <h4 class="imp-h">基础档案</h4>
            <label class="imp-row locked">
              <input type="checkbox" checked disabled />
              <span class="imp-body">
                <b>{{ curPet.name }} · {{ curPet.breed }}</b>
                <span>{{ curPet.age }}岁 · {{ curPet.weight }}kg · {{ curPet.gender }} · 健康分 {{ curPet.healthScore }}</span>
              </span>
            </label>
          </div>

          <div v-if="impRecords.length" class="imp-group">
            <h4 class="imp-h">近期健康记录</h4>
            <label v-for="r in impRecords" :key="r.id" class="imp-row">
              <input v-model="impPicked" type="checkbox" :value="`rec:${r.id}`" />
              <span class="imp-body">
                <b>{{ recordLabel(r.kind) }} · {{ r.value }}</b>
                <span>{{ r.date }}<template v-if="r.note"> · {{ r.note }}</template></span>
              </span>
            </label>
          </div>

          <div v-if="impRecognitions.length" class="imp-group">
            <h4 class="imp-h">最近识别</h4>
            <label v-for="r in impRecognitions" :key="r.id" class="imp-row">
              <input v-model="impPicked" type="checkbox" :value="`recog:${r.id}`" />
              <span class="imp-body">
                <b>识别为 {{ r.predicted }}（{{ Math.round(r.confidence * 100) }}%）</b>
                <span>{{ r.date }}{{ r.corrected ? ' · 已手动纠正' : '' }}</span>
              </span>
            </label>
          </div>

          <div v-if="impReports.length" class="imp-group">
            <h4 class="imp-h">最近问诊报告</h4>
            <label v-for="r in impReports" :key="r.id" class="imp-row">
              <input v-model="impPicked" type="checkbox" :value="`report:${r.id}`" />
              <span class="imp-body">
                <b>{{ r.title }}</b>
                <span>{{ r.date }} · {{ r.triage?.label || '已完成' }}</span>
              </span>
            </label>
          </div>

          <button class="f-submit" type="button" :disabled="!impPicked.length" @click="applyImport">
            带入对话（{{ impPicked.length }}）
          </button>
        </div>
      </div>
    </transition>

    <!-- 输入栏（固定底部，独立于滚动区） -->
    <div class="composer">
      <button class="composer-icon" type="button" @click="pickPhoto" aria-label="上传照片">
        <AppIcon name="image" :size="22" />
      </button>
      <!-- 真实选图：上传后随主诉一起转交医生（规则分诊不识别图片，不做假装分析） -->
      <input
        ref="photoInput"
        class="file-input"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        @change="onPhotoPicked"
      />
      <input
        v-model="input"
        class="composer-input"
        type="text"
        :placeholder="placeholder"
        @keyup.enter="send()"
      />
      <button class="composer-send" type="button" :disabled="!canSend" @click="send()" aria-label="发送">
        <AppIcon name="send" :size="20" />
      </button>
    </div>

    <!-- 医疗免责声明 -->
    <p class="disclaimer">AI 建议仅供参考，不能替代执业兽医的当面诊断。紧急情况请立即就医。</p>
  </section>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import ChatBubble from '@/components/ChatBubble.vue'
import TriageCard from '@/components/TriageCard.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import { consultSeed, consultSuggestions, symptomGroups } from '@/data/static'
import {
  fetchPets, fetchBreedLibrary, fetchAiQuota, triageFree,
  fetchHealthRecords, fetchRecognitionHistory, fetchReports
} from '@/api/data'
import { fileApi } from '@/api'
import { showToast } from '@shared/toast'

const route = useRoute()
const router = useRouter()

// 数据加载前给一个安全的空形状，避免模板在数据到达前取不到字段
const EMPTY_PET = { id: null, name: '', species: '', breed: '', breedId: null, age: '', gender: '', weight: '', healthScore: 0 }

const pets = ref([])
const petId = ref(null)
const curPet = computed(() => pets.value.find((p) => p.id === petId.value) || pets.value[0] || EMPTY_PET)
// RAG：当前品种的知识档案（没有则退化为通用建议）
const breeds = ref([])
const breedDoc = computed(
  () => breeds.value.find((b) => b.id === curPet.value.breedId || b.name === curPet.value.breed) || null
)

const messages = ref([...consultSeed])
const input = ref('')
const typing = ref(false)
const followups = ref([])
const listEl = ref(null)
const picked = ref([])
const quota = ref({ free: 3, used: 0, left: 3 })
const lastTriage = ref(null)
const attachedPhoto = ref(null)

// 档案导入面板的数据源（原为同步 ops 读取，改为接口加载）
const records = ref([])
const recognitions = ref([])
const reports = ref([])

// 用户提到过的主诉，用于生成转诊病例摘要
const complaints = ref([])

const canSend = computed(() => input.value.trim().length > 0 && !typing.value)
const placeholder = computed(() =>
  picked.value.length ? `补充「${picked.value.join('、')}」的持续时间…` : '描述宠物的情况…'
)

// 从拍照识别带入的上下文
const ctx = reactive({ pet: route.query.pet || '', note: route.query.note || '' })
function greetWithCtx() {
  if (!ctx.pet) return
  messages.value.push({
    role: 'ai',
    text: `我已了解你刚识别的是「${ctx.pet}」。${
      ctx.note ? '结合识别提示：' + ctx.note : ''
    }你想进一步确认哪方面？我帮你分析。`,
    time: now()
  })
}
greetWithCtx()

// 停留在问诊页时再次从识别页带参进入（组件复用，setup 不会重跑），需同步上下文
watch(
  () => route.query.pet,
  (pet) => {
    if (!pet || pet === ctx.pet) return
    ctx.pet = pet
    ctx.note = route.query.note || ''
    greetWithCtx()
  }
)

// 从问诊中心知识库带问题直达：自动发送该问题
watch(
  () => route.query.q,
  (q) => {
    if (!q) return
    router.replace({ path: '/consult/ai' })
    send(q)
  },
  { immediate: true }
)

function now() {
  const d = new Date()
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function scrollToEnd() {
  nextTick(() => {
    if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
  })
}

function toggleSymptom(s) {
  const i = picked.value.indexOf(s)
  if (i >= 0) picked.value.splice(i, 1)
  else picked.value.push(s)
  // 选中症状自动带入输入框，减少打字
  input.value = picked.value.join('、')
}

/* ---------- 档案导入：结构化上下文带入对话 ---------- */

const importOpen = ref(false)
const impPicked = ref([])

const impRecords = computed(() =>
  records.value
    .slice()
    .sort((a, b) => (a.date < b.date ? 1 : -1))
    .slice(0, 4)
)
const impRecognitions = computed(() => recognitions.value.slice(0, 2))
const impReports = computed(() =>
  reports.value
    .filter((r) => r.petId === petId.value)
    .slice(0, 2)
)

function recordLabel(kind) {
  return { weight: '体重', diet: '饮食', symptom: '症状', care: '护理' }[kind] || '记录'
}

function openImport() {
  impPicked.value = []
  importOpen.value = true
}

function applyImport() {
  const lines = [`${curPet.value.name}：${curPet.value.breed} · ${curPet.value.age}岁 · ${curPet.value.weight}kg · 健康分 ${curPet.value.healthScore}`]
  impPicked.value.forEach((key) => {
    const [kind, id] = key.split(':')
    if (kind === 'rec') {
      const r = records.value.find((x) => x.id === id)
      if (r) lines.push(`${r.date} ${recordLabel(r.kind)}：${r.value}${r.note ? '（' + r.note + '）' : ''}`)
    } else if (kind === 'recog') {
      const r = recognitions.value.find((x) => x.id === id)
      if (r) lines.push(`${r.date} 拍照识别：${r.predicted}（置信度 ${Math.round(r.confidence * 100)}%）${r.corrected ? '，用户已手动纠正' : ''}`)
    } else if (kind === 'report') {
      const r = reports.value.find((x) => x.id === id)
      if (r) lines.push(`${r.date} 问诊报告：${r.title}，分诊「${r.triage?.label || '已完成'}」`)
    }
  })
  if (lines.length < 2) {
    showToast('请至少勾选一项档案内容', { type: 'info' })
    return
  }

  importOpen.value = false
  messages.value.push({ role: 'me', kind: 'context', time: now(), context: lines })

  typing.value = true
  scrollToEnd()
  setTimeout(() => {
    typing.value = false
    const breedTip = breedDoc.value
      ? `结合品种档案：${breedDoc.value.name}${breedDoc.value.issues?.length ? '易患「' + breedDoc.value.issues.slice(0, 2).join('、') + '」' : ''}，日常${breedDoc.value.care ? breedDoc.value.care.slice(0, 42) + '…' : '注意定期体检'}。`
      : ''
    messages.value.push({
      role: 'ai',
      text: `已读取 ${lines.length - 1} 项档案背景。${breedTip}请描述它现在最明显的异常，以及什么时候开始的，我来判断。`,
      time: now()
    })
    followups.value = ['它最近精神不太好', '排便有点异常', '食欲下降了']
    scrollToEnd()
  }, 1100)
}

async function send(preset) {
  const text = (preset ?? input.value).trim()
  if (!text || typing.value) return

  // 免费额度耗尽后引导转真人，而不是直接拒绝服务
  if (quota.value.left <= 0) {
    showToast('今日 AI 免费次数已用完，可转真人医生继续问诊', { type: 'info' })
    goDoctors()
    return
  }

  messages.value.push({ role: 'me', text, time: now() })
  complaints.value.push(text)
  input.value = ''
  followups.value = []
  scrollToEnd()

  typing.value = true
  try {
    // 分诊完全由服务端规则引擎产出（分级/病因/动作/科室/置信度/随访），前端只渲染
    const res = await triageFree(text)
    const bt = res?.triage || {}
    if (bt.level) {
      lastTriage.value = bt
      messages.value.push({
        role: 'ai',
        kind: 'triage',
        time: now(),
        triage: bt,
        // RAG 引用：结论可溯源到品种档案
        cite: breedDoc.value ? `${breedDoc.value.name}品种档案 · 易患 ${breedDoc.value.issues?.slice(0, 2).join('、') || '—'}` : '',
        citeBreedId: breedDoc.value ? breedDoc.value.id : ''
      })
      followups.value = ['这种情况要立刻去医院吗', '现在能做些什么', '转真人医生看看']
    } else {
      messages.value.push({
        role: 'ai',
        text: res?.reply || '请补充更具体的症状描述（部位、持续时间、精神状态），我来帮你初步判断。',
        time: now()
      })
      followups.value = ['帮我记录症状', '这种情况要去医院吗', '日常怎么护理']
    }

    // 后端分诊后已扣减当日额度，用返回值覆盖本地
    quota.value = res?.quota || quota.value
  } catch (e) {
    showToast(e?.message || 'AI 问诊失败，请重试', { type: 'error' })
  } finally {
    typing.value = false
    scrollToEnd()
  }
}

/* ---------- 照片：真实选图上传（规则分诊不识别图片，转交医生时随附） ---------- */

const photoInput = ref(null)
const MAX_PHOTO_MB = 8

function pickPhoto() {
  if (typing.value) return
  photoInput.value?.click()
}

function openPhoto(url) {
  window.open(url, '_blank')
}

async function onPhotoPicked(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) {
    showToast('请选择图片文件', { type: 'warn' })
    return
  }
  if (file.size > MAX_PHOTO_MB * 1024 * 1024) {
    showToast(`图片不能超过 ${MAX_PHOTO_MB}MB`, { type: 'warn' })
    return
  }
  typing.value = true
  scrollToEnd()
  try {
    const fd = new FormData()
    fd.append('file', file)
    const up = await fileApi.upload(fd, 'consult')
    if (!up?.url) throw new Error('上传失败')
    attachedPhoto.value = up.url
    messages.value.push({ role: 'me', kind: 'photo', image: up.url, time: now() })
    messages.value.push({
      role: 'ai',
      text: '照片已存档，转真人医生时会随病历一起发送。请用文字描述你最担心的部位和持续时间，我来做初步分诊。',
      time: now()
    })
    followups.value = ['患处发红脱毛', '频繁挠抓或蹭蹭', '精神状态正常']
    scrollToEnd()
  } catch (err) {
    showToast(err?.message || '照片上传失败', { type: 'error' })
  } finally {
    typing.value = false
    scrollToEnd()
  }
}

/**
 * 转真人医生：把宠物档案 + 主诉 + AI 分诊结论打包成结构化病例摘要，
 * 医生接诊时可直接看到，不必重复追问（主流平台的核心效率点）。
 */
function buildCaseSummary() {
  return {
    petId: curPet.value.id,
    petName: curPet.value.name,
    species: curPet.value.species,
    breed: curPet.value.breed,
    age: curPet.value.age,
    weight: curPet.value.weight,
    gender: curPet.value.gender,
    complaints: complaints.value.slice(),
    symptoms: picked.value.slice(),
    photo: attachedPhoto.value || null,
    triage: lastTriage.value
      ? {
          level: lastTriage.value.level,
          label: lastTriage.value.label,
          advice: lastTriage.value.advice
        }
      : null
  }
}

function goDoctors(dept) {
  try {
    sessionStorage.setItem('petwise_case_summary', JSON.stringify(buildCaseSummary()))
  } catch {
    /* 会话存储不可用时降级：医生页会退回手动填写 */
  }
  router.push(dept ? { path: '/doctors', query: { dept } } : '/doctors')
}

async function loadRecords() {
  if (petId.value === null) return
  try {
    records.value = await fetchHealthRecords(petId.value)
  } catch {
    records.value = []
  }
}

async function loadSideData() {
  try {
    recognitions.value = await fetchRecognitionHistory()
  } catch {
    recognitions.value = []
  }
  try {
    reports.value = await fetchReports()
  } catch {
    reports.value = []
  }
}

watch(petId, loadRecords)

onMounted(async () => {
  scrollToEnd()
  try {
    const [ps, bs, qs] = await Promise.all([fetchPets(), fetchBreedLibrary(), fetchAiQuota()])
    pets.value = ps || []
    breeds.value = bs || []
    quota.value = qs || quota.value
    if (pets.value.length && petId.value === null) petId.value = pets.value[0].id
    await Promise.all([loadRecords(), loadSideData()])
  } catch (e) {
    showToast(e?.message || '问诊上下文加载失败', { type: 'error' })
  }
})
</script>

<style scoped>
.title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-2xl);
  letter-spacing: -0.02em;
  line-height: 1;
}

.find-doc {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-ink);
  background: var(--color-surface);
  border: 1px solid var(--hairline-strong);
  padding: 8px 13px;
  border-radius: var(--radius-pill);
  transition: transform var(--dur-fast) var(--ease-out);
}
.find-doc:active { transform: scale(0.96); }

/* ---------- 问诊对象 ---------- */
.pet-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
}
.pet-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-muted);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  padding: 6px 12px 6px 7px;
  border-radius: var(--radius-pill);
  transition: border-color var(--dur-fast), color var(--dur-fast), background var(--dur-fast);
}
.pet-chip.on {
  color: var(--color-ink);
  border-color: var(--color-accent);
  background: var(--color-accent-soft);
}
.pet-meta {
  margin-left: auto;
  font-size: 11px;
  color: var(--color-faint);
}

/* ---------- 免费额度 ---------- */
.quota {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 12px;
  padding: 9px 12px;
  border-radius: var(--radius-md);
  background: var(--color-sage-soft);
  font-size: 12px;
  color: var(--color-ink-2);
}
.quota b { color: var(--color-good); font-weight: 700; }
.quota-doc {
  margin-left: auto;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-good);
  text-decoration: underline;
  text-underline-offset: 2px;
}

/* ---------- 急诊告警条 ---------- */
.er-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--color-alert) 10%, white);
  border: 1px solid color-mix(in srgb, var(--color-alert) 40%, transparent);
}
.er-ic {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  background: var(--color-alert);
  color: #fff;
  flex-shrink: 0;
}
.er-body { flex: 1; min-width: 0; }
.er-t { font-size: 14px; font-weight: 700; color: var(--color-alert); }
.er-s { font-size: 12px; color: var(--color-ink-2); margin-top: 2px; line-height: 1.45; }
.er-btn {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  background: var(--color-alert);
  padding: 8px 13px;
  border-radius: var(--radius-pill);
  transition: transform var(--dur-fast) var(--ease-out);
}
.er-btn:active { transform: scale(0.96); }

/* ---------- 结构化问诊入口 ---------- */
.guide-cta {
  display: flex;
  align-items: center;
  gap: 11px;
  margin-top: 14px;
  padding: 13px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--hairline-strong);
  background: var(--color-surface);
  transition: transform var(--dur-fast) var(--ease-out);
}
.guide-cta:active { transform: scale(0.988); }
.gc-ic {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  background: var(--color-sage-soft);
  color: var(--color-good);
  flex-shrink: 0;
}
.gc-body { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.gc-t { font-size: 14px; font-weight: 700; }
.gc-s { font-size: 11.5px; color: var(--color-muted); line-height: 1.45; }
.gc-arrow { color: var(--color-faint); transform: rotate(180deg); flex-shrink: 0; }

/* ---------- 症状标签 ---------- */
.symptoms { margin-top: 16px; display: flex; flex-direction: column; gap: 9px; }
.sym-row { display: flex; align-items: flex-start; gap: 10px; }
.sym-g {
  flex-shrink: 0;
  width: 34px;
  padding-top: 7px;
  font-size: 11px;
  font-weight: 700;
  color: var(--color-faint);
}
.sym-items { flex: 1; display: flex; flex-wrap: wrap; gap: 6px; }
.sym-chip {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink-2);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  padding: 6px 12px;
  border-radius: var(--radius-pill);
  transition: transform var(--dur-fast) var(--ease-out), border-color var(--dur-fast),
    background var(--dur-fast), color var(--dur-fast);
}
.sym-chip.on {
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  border-color: color-mix(in srgb, var(--color-accent) 40%, transparent);
}
.sym-chip:active { transform: scale(0.95); }

/* 识别上下文横幅 */
.ctx-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: var(--color-accent-soft);
  border: 1px solid color-mix(in srgb, var(--color-accent) 30%, transparent);
  margin: 12px 0 0;
}
.ctx-ic {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: var(--color-surface);
  color: var(--color-accent-ink);
  flex-shrink: 0;
}
.ctx-body { flex: 1; display: flex; flex-direction: column; }
.ctx-title { font-weight: 700; font-size: 14px; color: var(--color-accent-ink); }
.ctx-note { font-size: 12px; color: var(--color-ink-2); line-height: 1.5; margin-top: 2px; }
.ctx-x {
  color: var(--color-muted);
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 50%;
}
.ctx-x:active { background: rgba(0, 0, 0, 0.06); }

.suggest {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 16px 0 18px;
}
.suggest-chip {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  padding: 8px 14px;
  border-radius: var(--radius-pill);
  transition: transform var(--dur-fast) var(--ease-out), border-color var(--dur-fast);
}
.suggest-chip:active { transform: scale(0.95); border-color: var(--color-accent); }

.chat-list {
  display: flex;
  flex-direction: column;
  padding-bottom: 128px; /* 清空固定输入栏 + 底部导航 */
}
/* 短对话贴底对齐；首个子元素上推，避免 flex-end 溢出陷阱 */
.chat-list > :first-child { margin-top: auto; }

/* 随访建议 */
.followups {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(var(--dock-h) + 62px + env(safe-area-inset-bottom, 0px));
  width: min(var(--shell-max), 100%);
  display: flex;
  gap: 8px;
  padding: 8px 14px;
  overflow-x: auto;
  z-index: 20;
}
.fu-chip {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-accent-ink);
  background: color-mix(in srgb, var(--color-accent-soft) 85%, white);
  border: 1px solid color-mix(in srgb, var(--color-accent) 25%, transparent);
  padding: 8px 14px;
  border-radius: var(--radius-pill);
  transition: transform var(--dur-fast) var(--ease-out);
}
.fu-chip:active { transform: scale(0.95); }

.typing {
  display: inline-flex;
  gap: 5px;
  padding: 12px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 18px;
  border-bottom-left-radius: 6px;
  width: fit-content;
  margin-bottom: 16px;
}
.typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-muted);
  animation: bounce 1.2s var(--ease-in-out) infinite;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%,100%{transform:translateY(0);opacity:0.4} 50%{transform:translateY(-5px);opacity:1} }

/* 输入栏：固定底部，停靠在底部导航正上方 */
.composer {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(var(--dock-h) + env(safe-area-inset-bottom, 0px));
  width: min(var(--shell-max), 100%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: color-mix(in srgb, var(--color-surface) 92%, transparent);
  backdrop-filter: blur(14px);
  border-top: 1px solid var(--color-border);
}
.file-input {
  display: none;
}
.photo-bubble {
  align-self: flex-end;
  max-width: 72%;
  margin: 6px 0;
  position: relative;
}
.photo-bubble img {
  display: block;
  width: 100%;
  border-radius: var(--radius-md, 14px);
  border: 1px solid var(--color-border);
  cursor: zoom-in;
}
.photo-bubble .pb-time {
  position: absolute;
  right: 8px;
  bottom: 6px;
  font-size: 10px;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}
.composer-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--color-muted);
  background: var(--color-surface-2);
  flex-shrink: 0;
}
.composer-input {
  flex: 1;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  border-radius: var(--radius-pill);
  padding: 11px 16px;
  font-size: 15px;
  color: var(--color-ink);
  outline: none;
}
.composer-input:focus-visible { border-color: var(--color-accent); }
.composer-send {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--color-accent);
  flex-shrink: 0;
  transition: transform var(--dur-fast) var(--ease-out), opacity var(--dur-fast);
}
.composer-send:active { transform: scale(0.9); }
.composer-send:disabled { opacity: 0.4; }

.disclaimer {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(var(--dock-h) + 106px + env(safe-area-inset-bottom, 0px));
  width: min(var(--shell-max), 100%);
  text-align: center;
  font-size: 11px;
  color: var(--color-faint);
  padding: 2px 16px 0;
  z-index: 19;
  line-height: 1.4;
}

.ctx-enter-active, .ctx-leave-active { transition: opacity var(--dur-base) var(--ease-out), transform var(--dur-base) var(--ease-out); }
.ctx-enter-from, .ctx-leave-to { opacity: 0; transform: translateY(-6px); }

/* ---------- 档案导入 ---------- */
.import-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-left: auto;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  border: 1px solid color-mix(in srgb, var(--color-accent) 25%, transparent);
  padding: 6px 11px;
  border-radius: var(--radius-pill);
  transition: transform var(--dur-fast) var(--ease-out);
}
.import-btn:active { transform: scale(0.95); }

/* RAG 引用 */
.rag-cite {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
  margin: -8px 0 16px 4px;
  font-size: 11px;
  color: var(--color-faint);
  line-height: 1.5;
}
.rag-cite svg { flex-shrink: 0; }
.cite-link { color: var(--color-accent-ink); font-weight: 700; }

/* 档案导入卡片（对话内） */
.ctx-card {
  align-self: stretch;
  border-radius: var(--radius-md);
  border: 1px dashed color-mix(in srgb, var(--color-accent) 35%, transparent);
  background: color-mix(in srgb, var(--color-accent-soft) 55%, white);
  padding: 12px 14px;
  margin-bottom: 16px;
}
.cc-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  font-weight: 700;
  color: var(--color-accent-ink);
}
.cc-time { margin-left: auto; font-weight: 400; color: var(--color-faint); }
.cc-list {
  list-style: none;
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.cc-list li {
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--color-ink-2);
  padding-left: 12px;
  position: relative;
}
.cc-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--color-accent);
}

/* ---------- 档案导入面板 ---------- */
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
  max-height: 84dvh;
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
}
.sheet-sub {
  font-size: 13px;
  color: var(--color-muted);
  margin: 4px 0 14px;
}
.imp-group { margin-bottom: 16px; }
.imp-h {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-faint);
  letter-spacing: 0.06em;
  margin-bottom: 8px;
}
.imp-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 11px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--hairline);
  background: var(--color-bg);
  margin-bottom: 8px;
  cursor: pointer;
}
.imp-row.locked { opacity: 0.75; cursor: default; }
.imp-row input {
  width: 18px;
  height: 18px;
  margin-top: 2px;
  accent-color: var(--color-accent);
  flex-shrink: 0;
}
.imp-body { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.imp-body b { font-size: 13.5px; }
.imp-body span { font-size: 11.5px; color: var(--color-muted); line-height: 1.5; }
.f-submit {
  width: 100%;
  margin-top: 4px;
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
  .typing span { animation: none; }
}
</style>
