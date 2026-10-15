<template>
  <section class="screen">
    <header class="screen-head" v-reveal>
      <div>
        <p class="eyebrow">COMPUTER VISION</p>
        <h1 class="title">拍照识别</h1>
      </div>
      <span class="cv-badge"><AppIcon name="sparkle" :size="14" /> 品种识别</span>
    </header>

    <p class="lede" v-reveal="{ delay: 80 }">
      对准宠物拍一张，模型识别猫狗品种，并给出该品种的档案介绍与饲养建议。
    </p>

    <!-- 取景框 -->
    <div class="viewfinder" :class="{ scanning }" v-reveal="{ delay: 120 }">
      <div class="vf-deco" aria-hidden="true"><AppIcon name="paw" :size="120" /></div>
      <span class="vf-corner tl"></span>
      <span class="vf-corner tr"></span>
      <span class="vf-corner bl"></span>
      <span class="vf-corner br"></span>
      <span class="vf-scan"></span>

      <div class="vf-state">
        <template v-if="picked">
          <img :src="picked" class="vf-photo" alt="待识别照片" />
        </template>
        <template v-else-if="!scanning && !result">
          <p class="vf-tip">将宠物放入框内</p>
        </template>
        <template v-else-if="scanning">
          <p class="vf-tip scanning-text">品种识别中…</p>
        </template>
        <template v-else>
          <PetIllustration :species="result.species" class="vf-illu" />
        </template>
      </div>

      <button class="shutter" type="button" :disabled="scanning" @click="capture" aria-label="拍照识别">
        <AppIcon name="camera" :size="28" />
      </button>
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        class="file-hidden"
        @change="onFile"
      />
    </div>

    <div class="vf-actions" v-reveal="{ delay: 160 }">
      <button class="vf-btn" type="button" @click="capture" :disabled="scanning">拍摄识别</button>
      <button class="vf-btn ghost" type="button" @click="openAlbum" :disabled="scanning">从相册选择</button>
    </div>

    <!-- 识别结果 -->
    <transition name="result">
      <article v-if="result && !scanning" class="result-card">
        <div class="result-top">
          <PetIllustration :species="result.species" class="result-illu" />
          <div class="result-id">
            <h2 class="result-name">{{ result.title }}</h2>
            <p class="result-sci">{{ result.sci }}</p>
          </div>
          <span class="result-conf">
            <b class="num">{{ Math.round(result.confidence * 100) }}</b
            ><i>%</i>
            <small>置信度</small>
          </span>
        </div>

        <div class="conf-bar">
          <span :style="{ width: result.confidence * 100 + '%' }"></span>
        </div>

        <!-- 模型 top-3 备选 -->
        <div class="alts">
          <span class="alts-label">模型备选</span>
          <span v-for="a in result.alternatives" :key="a.title" class="alt-chip">
            {{ a.title }} <i class="num">{{ Math.round(a.confidence * 100) }}%</i>
          </span>
        </div>

        <!-- top1 品种档案（与百科联动） -->
        <div v-if="breedOf" class="breed-intro">
          <div class="bi-head">
            <span class="bi-origin"><AppIcon name="location" :size="13" /> 原产地 · {{ breedOf.origin }}</span>
            <span class="bi-life">寿命 {{ breedOf.life }} · 体重 {{ breedOf.weight }}</span>
          </div>
          <div class="bi-temper">
            <span v-for="t in breedOf.temperament" :key="t" class="temper-chip">{{ t }}</span>
          </div>
          <div class="bi-feeding">
            <p class="bi-sub">喂食建议</p>
            <p v-for="(f, i) in breedOf.feeding.slice(0, 2)" :key="i" class="bi-line">{{ f }}</p>
          </div>
        </div>
        <p v-else class="breed-missing">该品种的百科资料完善中，可先查看其它内容或手动纠正品种。</p>

        <div class="result-foot">
          <button class="rf-btn" type="button" @click="capture">重新识别</button>
          <button class="rf-btn" type="button" @click="saveRecord">保存记录</button>
          <router-link :to="`/breed/${breedPath}`" class="rf-btn">品种百科</router-link>
          <router-link
            :to="{ path: '/consult/ai', query: { pet: result.title, note: `我拍到的宠物识别为${result.title}，想了解这个品种的饲养与健康管理` } }"
            class="rf-btn accent"
          >问问 AI →</router-link>
        </div>

        <button class="fix-btn" type="button" @click="openFix">
          <AppIcon name="edit" :size="14" /> 识别不准？手动纠正品种
        </button>
      </article>
    </transition>

    <!-- 识别记录（持久化，管理端审核后状态同步） -->
    <section class="block" v-if="history.length" v-reveal>
      <div class="block-head">
        <h3 class="block-title">识别记录</h3>
        <span class="block-hint">{{ history.length }} 条</span>
      </div>
      <div class="records">
        <div v-for="h in history" :key="h.id" class="rec">
          <span class="rec-illu"><PetIllustration :species="h.species" /></span>
          <div class="rec-body">
            <span class="rec-name">
              {{ h.corrected || h.predicted }}
              <em v-if="h.corrected" class="rec-from">纠正自「{{ h.predicted }}」</em>
            </span>
            <span class="rec-time num">{{ formatTime(h.time) }}</span>
          </div>
          <span class="rec-badge num" :class="badgeOf(h.status).c">{{ badgeOf(h.status).t }}</span>
        </div>
      </div>
      <p class="rec-note">手动纠正的记录将进入管理端审核，通过后可作为训练数据回流模型。</p>
    </section>

    <!-- 示例库（演示数据集） -->
    <section class="block" v-reveal>
      <div class="block-head">
        <h3 class="block-title">识别示例库</h3>
        <span class="block-hint">数据集</span>
      </div>
      <div class="samples">
        <button
          v-for="(s, i) in recognitionSamples"
          :key="s.id"
          class="sample"
          type="button"
          :class="{ on: result && result.id === s.id }"
          @click="loadSample(i)"
        >
          <span class="sample-illu"><PetIllustration :species="s.species" /></span>
          <span class="sample-name">{{ s.title }}</span>
        </button>
      </div>
    </section>

    <!-- 手动纠正：底部弹层 -->
    <teleport to="body">
      <div v-if="correcting" class="sheet-mask" @click.self="correcting = false">
        <div class="sheet">
          <div class="sheet-head">
            <h3>纠正识别品种</h3>
            <button class="sheet-close" type="button" @click="correcting = false">取消</button>
          </div>
          <p class="sheet-tip">模型预测为「{{ result?.title }}」。请选择正确品种（仅支持{{ result?.species === 'dog' ? '犬' : '猫' }}种）：</p>
          <input v-model="fixKw" class="sheet-search" type="search" placeholder="搜索品种名" />
          <div class="sheet-list">
            <button
              v-for="b in fixCandidates"
              :key="b.id"
              class="sheet-item"
              type="button"
              @click="applyFix(b.name)"
            >
              <span class="si-illu"><PetIllustration :species="b.species" /></span>
              <span class="si-body">
                <span class="si-name">{{ b.name }}</span>
                <span class="si-origin">{{ b.origin }} · {{ b.weight }}</span>
              </span>
            </button>
            <p v-if="!fixCandidates.length" class="sheet-empty">没有匹配的品种</p>
          </div>
        </div>
      </div>
    </teleport>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import PetIllustration from '@/components/PetIllustration.vue'
import { recognitionSamples, breedLibrary } from '@/data/mock'
import { recognitionHistory, saveRecognition, correctRecognition } from '@/data/ops'
import { showToast } from '@/composables/toast'

const scanning = ref(false)
const result = ref(null)
const cursor = ref(0)
const picked = ref(null)
const fileInput = ref(null)
const history = ref(recognitionHistory())
const correcting = ref(false)
const fixKw = ref('')
const savedId = ref(null) // 本次结果对应的记录 id（未保存时为 null）

// 识别标题 → 品种库 id（识别结果一键跳转百科）
const breedPath = computed(() => {
  if (!result.value) return ''
  const hit = breedLibrary.find((b) => b.name === result.value.title)
  return hit ? hit.id : result.value.title
})

// top1 品种档案（识别结果与百科联动的数据基础）
const breedOf = computed(() => {
  if (!result.value) return null
  return breedLibrary.find((b) => b.name === result.value.title) || null
})

// 手动纠正候选：同物种品种库 + 搜索
const fixCandidates = computed(() => {
  if (!result.value) return []
  const kw = fixKw.value.trim()
  return breedLibrary.filter(
    (b) => b.species === result.value.species && (!kw || b.name.includes(kw) || b.origin.includes(kw))
  )
})

function formatTime(iso) {
  const d = new Date(iso)
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function badgeOf(status) {
  return (
    { review: { t: '纠正待审核', c: 'watch' }, approved: { t: '已采纳', c: 'good' }, rejected: { t: '维持原结果', c: 'muted' } }[status] ||
    { t: '已完成', c: 'good' }
  )
}

function finishWith(index) {
  result.value = { ...recognitionSamples[index], source: 'demo' }
  savedId.value = null
}

function runScan() {
  if (scanning.value) return
  scanning.value = true
  result.value = null
  setTimeout(() => {
    finishWith(cursor.value % recognitionSamples.length)
    cursor.value++
    scanning.value = false
  }, 1600)
}

// 模拟拍摄：无真实图像，直接走识别
function capture() {
  if (scanning.value) return
  picked.value = null
  runScan()
}

// 从相册选择：真实文件预览 + 识别
function openAlbum() {
  if (scanning.value) return
  fileInput.value?.click()
}
function onFile(e) {
  const f = e.target.files?.[0]
  if (!f) return
  if (picked.value) URL.revokeObjectURL(picked.value)
  picked.value = URL.createObjectURL(f)
  runScan()
  e.target.value = ''
}

function loadSample(i) {
  if (scanning.value) return
  picked.value = null
  finishWith(i)
}

// 保存识别记录（持久化）
function saveRecord() {
  if (!result.value) return
  const rec = saveRecognition({
    species: result.value.species,
    predicted: result.value.title,
    confidence: result.value.confidence,
    alternatives: result.value.alternatives,
    imageRef: result.value.source
  })
  savedId.value = rec.id
  history.value = recognitionHistory()
  showToast('已保存到识别记录', { type: 'success' })
}

// 打开纠正弹层：未保存过的结果先自动保存
function openFix() {
  if (!result.value) return
  if (!savedId.value) saveRecord()
  fixKw.value = ''
  correcting.value = true
}

// 提交纠正 → 进入管理端审核队列
function applyFix(breedName) {
  if (!savedId.value) return
  correctRecognition(savedId.value, breedName)
  history.value = recognitionHistory()
  correcting.value = false
  showToast(`已提交「${breedName}」，等待管理端审核`, { type: 'success' })
}
</script>

<style scoped>
.title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-2xl);
  letter-spacing: -0.02em;
  line-height: 1;
}
.cv-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  padding: 6px 12px;
  border-radius: var(--radius-pill);
}
.lede {
  font-size: 15px;
  color: var(--color-ink-2);
  line-height: 1.6;
  margin: 14px 0 18px;
}

/* 取景框 */
.viewfinder {
  position: relative;
  aspect-ratio: 4 / 3;
  border-radius: var(--radius-lg);
  background:
    radial-gradient(60% 60% at 50% 40%, rgba(126, 155, 120, 0.18), transparent 70%),
    linear-gradient(160deg, #2c3a31, #1b2a22);
  overflow: hidden;
  box-shadow: var(--shadow-2);
}
.file-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}
.vf-deco {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: #ffffff;
  opacity: 0.14;
}
.vf-corner {
  position: absolute;
  width: 26px;
  height: 26px;
  border: 3px solid var(--color-accent);
  opacity: 0.9;
}
.vf-corner.tl { top: 16px; left: 16px; border-right: none; border-bottom: none; border-radius: 8px 0 0 0; }
.vf-corner.tr { top: 16px; right: 16px; border-left: none; border-bottom: none; border-radius: 0 8px 0 0; }
.vf-corner.bl { bottom: 16px; left: 16px; border-right: none; border-top: none; border-radius: 0 0 0 8px; }
.vf-corner.br { bottom: 16px; right: 16px; border-left: none; border-top: none; border-radius: 0 0 8px 0; }
.vf-scan {
  position: absolute;
  left: 8%;
  right: 8%;
  height: 3px;
  top: 12%;
  background: linear-gradient(90deg, transparent, var(--color-accent), transparent);
  opacity: 0;
}
.viewfinder.scanning .vf-scan {
  opacity: 1;
  animation: scan 1.4s var(--ease-in-out) infinite;
}
@keyframes scan {
  0% { top: 10%; }
  100% { top: 86%; }
}
.vf-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
}
.vf-photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.92;
}
.vf-tip {
  color: rgba(251, 246, 236, 0.85);
  font-size: 15px;
  letter-spacing: 0.04em;
}
.scanning-text {
  color: var(--color-peach);
  font-weight: 700;
  animation: pulse 1s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
.vf-illu {
  width: 96px;
  height: 96px;
  animation: pop 0.5s var(--ease-out) both;
  filter: drop-shadow(0 10px 22px rgba(0, 0, 0, 0.28));
}
@keyframes pop { 0%{transform:scale(0.5);opacity:0} 100%{transform:scale(1);opacity:1} }
.shutter {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  width: 62px;
  height: 62px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--color-accent);
  box-shadow: 0 8px 22px rgba(232, 85, 43, 0.5);
  border: 4px solid rgba(255, 255, 255, 0.85);
  transition: transform var(--dur-fast) var(--ease-out);
}
.shutter:active { transform: translateX(-50%) scale(0.92); }
.shutter:disabled { opacity: 0.6; }

.vf-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}
.vf-btn {
  flex: 1;
  padding: 14px;
  border-radius: var(--radius-pill);
  background: var(--color-ink);
  color: var(--color-surface);
  font-weight: 700;
  font-size: 15px;
  transition: transform var(--dur-fast) var(--ease-out);
}
.vf-btn:active { transform: scale(0.97); }
.vf-btn.ghost {
  background: var(--color-surface);
  color: var(--color-ink);
  border: 1px solid var(--color-border);
}

/* 结果卡 */
.result-enter-active, .result-leave-active { transition: all var(--dur-base) var(--ease-out); }
.result-enter-from, .result-leave-to { opacity: 0; transform: translateY(16px); }
.result-card {
  margin-top: 22px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-2);
}
.result-top {
  display: flex;
  align-items: center;
  gap: 14px;
}
.result-illu { width: 58px; height: 58px; flex-shrink: 0; }
.result-id { flex: 1; }
.result-name {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-xl);
  letter-spacing: -0.01em;
  line-height: 1;
}
.result-sci {
  font-style: italic;
  font-size: 13px;
  color: var(--color-muted);
  margin-top: 3px;
}
.result-conf {
  text-align: right;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  color: var(--color-accent-ink);
}
.result-conf b { font-size: 30px; font-family: var(--font-display); line-height: 1; }
.result-conf i { font-style: normal; font-size: 14px; }
.result-conf small { font-size: 11px; color: var(--color-muted); }

.conf-bar {
  height: 8px;
  border-radius: 999px;
  background: var(--color-border);
  margin: 16px 0;
  overflow: hidden;
}
.conf-bar span {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--color-accent), var(--color-peach));
  transition: width 0.9s var(--ease-out);
}

/* 模型备选 */
.alts {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.alts-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-muted);
  letter-spacing: 0.06em;
}
.alt-chip {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  color: var(--color-ink-2);
}
.alt-chip i {
  font-style: normal;
  color: var(--color-muted);
  margin-left: 3px;
  font-size: 11px;
}

/* top1 品种档案 */
.breed-intro {
  margin-top: 16px;
  padding: 14px;
  border-radius: var(--radius-md);
  background: var(--color-bg-2);
  border: 1px solid var(--color-border);
}
.bi-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}
.bi-origin {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-pine-ink, #2d4a3e);
}
.bi-life { font-size: 11.5px; color: var(--color-muted); }
.bi-temper {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 10px 0;
}
.temper-chip {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-sage-soft);
  color: #2d4a3e;
  font-weight: 600;
}
.bi-sub {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-accent-ink);
  margin-bottom: 4px;
}
.bi-line {
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-ink-2);
  padding-left: 12px;
  position: relative;
}
.bi-line::before {
  content: '';
  position: absolute;
  left: 0;
  top: 9px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--color-accent);
}
.breed-missing {
  margin-top: 14px;
  font-size: 13px;
  color: var(--color-muted);
  line-height: 1.6;
}

.result-foot {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}
.rf-btn {
  flex: 1;
  padding: 13px 8px;
  border-radius: var(--radius-pill);
  font-weight: 700;
  font-size: 13px;
  text-align: center;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  color: var(--color-ink);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.rf-btn.accent {
  background: var(--color-ink);
  color: var(--color-surface);
  border-color: transparent;
  flex: 1.3;
}
.fix-btn {
  margin-top: 12px;
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-muted);
  font-size: 12.5px;
  font-weight: 600;
}
.fix-btn:active { transform: scale(0.98); }

/* 识别历史 */
.block { margin-top: 28px; }
.block-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14px;
}
.block-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-lg);
}
.block-hint {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--color-accent-ink);
  text-transform: uppercase;
}
.records {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.rec {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}
.rec-illu { width: 42px; height: 42px; flex-shrink: 0; }
.rec-body { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.rec-name { font-weight: 700; font-size: 15px; }
.rec-from {
  font-style: normal;
  font-size: 11px;
  font-weight: 400;
  color: var(--color-muted);
  margin-left: 6px;
}
.rec-time { font-size: 12px; color: var(--color-muted); }
.rec-badge {
  font-weight: 700;
  font-size: 11px;
  padding: 4px 9px;
  border-radius: var(--radius-pill);
  flex-shrink: 0;
}
.rec-badge.good { color: #2d4a3e; background: var(--color-sage-soft); }
.rec-badge.watch { color: #8a5a12; background: #fbe7d2; }
.rec-badge.muted { color: var(--color-muted); background: var(--color-surface-2); }
.rec-note {
  margin-top: 10px;
  font-size: 11.5px;
  color: var(--color-muted);
  line-height: 1.5;
}

/* 示例库 */
.samples {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 6px;
}
.sample {
  flex-shrink: 0;
  width: 92px;
  padding: 14px 8px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  transition: border-color var(--dur-fast), transform var(--dur-fast) var(--ease-out);
}
.sample:active { transform: scale(0.95); }
.sample.on { border-color: var(--color-accent); box-shadow: 0 0 0 2px var(--color-accent-soft); }
.sample-illu { width: 50px; height: 50px; }
.sample-name { font-size: 12px; font-weight: 600; }

/* 手动纠正弹层 */
.sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 90;
  background: rgba(27, 42, 34, 0.45);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  animation: fade 0.2s var(--ease-out);
}
@keyframes fade { from { opacity: 0; } }
.sheet {
  width: min(440px, 100%);
  max-height: 76vh;
  overflow: auto;
  background: var(--color-surface);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  padding: 20px 20px 32px;
  animation: up 0.28s var(--ease-out);
}
@keyframes up { from { transform: translateY(40px); opacity: 0; } }
.sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.sheet-head h3 {
  font-family: var(--font-display);
  font-size: var(--fs-lg);
  font-weight: 700;
}
.sheet-close {
  font-size: 13px;
  color: var(--color-muted);
  background: none;
  border: none;
  padding: 6px;
}
.sheet-tip {
  font-size: 13px;
  color: var(--color-ink-2);
  line-height: 1.6;
  margin: 10px 0 12px;
}
.sheet-search {
  width: 100%;
  padding: 11px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-bg-2);
  font-size: 14px;
  outline: none;
}
.sheet-search:focus { border-color: var(--color-accent); }
.sheet-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}
.sheet-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  text-align: left;
}
.sheet-item:active { transform: scale(0.98); }
.si-illu { width: 38px; height: 38px; flex-shrink: 0; }
.si-body { display: flex; flex-direction: column; }
.si-name { font-weight: 700; font-size: 14.5px; }
.si-origin { font-size: 12px; color: var(--color-muted); }
.sheet-empty {
  text-align: center;
  font-size: 13px;
  color: var(--color-muted);
  padding: 20px 0;
}

@media (prefers-reduced-motion: reduce) {
  .vf-scan, .scanning-text, .vf-illu, .sheet, .sheet-mask { animation: none; }
}
</style>
