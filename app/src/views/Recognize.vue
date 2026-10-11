<template>
  <section class="screen">
    <header class="screen-head" v-reveal>
      <div>
        <p class="eyebrow">COMPUTER VISION</p>
        <h1 class="title">拍照识别</h1>
      </div>
      <span class="cv-badge"><AppIcon name="sparkle" :size="14" /> 视觉模型</span>
    </header>

    <p class="lede" v-reveal="{ delay: 80 }">
      对准宠物拍一张，模型会识别品种、体态与精神状态，并给出健康提示。
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
          <p class="vf-tip scanning-text">视觉模型识别中…</p>
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

        <div class="metrics">
          <div v-for="m in result.metrics" :key="m.label" class="metric" :class="m.state">
            <span class="metric-val num">{{ m.value }}</span>
            <span class="metric-label">{{ m.label }}</span>
          </div>
        </div>

        <p class="result-note">{{ result.note }}</p>

        <div class="result-foot">
          <button class="rf-btn" type="button" @click="capture">重新识别</button>
          <button class="rf-btn" type="button" @click="saveRecord">保存记录</button>
          <router-link :to="`/breed/${breedPath}`" class="rf-btn">品种百科</router-link>
          <router-link
            :to="{ path: '/consult/ai', query: { pet: result.title, note: result.note } }"
            class="rf-btn accent"
          >就结果问医生 →</router-link>
        </div>
      </article>
    </transition>

    <!-- 识别历史 -->
    <section class="block" v-if="history.length" v-reveal>
      <div class="block-head">
        <h3 class="block-title">识别记录</h3>
        <span class="block-hint">{{ history.length }} 条</span>
      </div>
      <div class="records">
        <div v-for="(h, i) in history" :key="i" class="rec">
          <span class="rec-illu"><PetIllustration :species="h.species" /></span>
          <div class="rec-body">
            <span class="rec-name">{{ h.title }}</span>
            <span class="rec-time num">{{ h.time }}</span>
          </div>
          <span class="rec-conf num">{{ Math.round(h.confidence * 100) }}%</span>
        </div>
      </div>
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
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import PetIllustration from '@/components/PetIllustration.vue'
import { recognitionSamples, breedLibrary } from '@/data/mock'
import { showToast } from '@/composables/toast'

const scanning = ref(false)
const result = ref(null)
const cursor = ref(0)
const picked = ref(null)
const fileInput = ref(null)
const history = ref([])

// 识别标题 → 品种库 id（识别结果一键跳转百科）
const breedPath = computed(() => {
  if (!result.value) return ''
  const hit = breedLibrary.find((b) => b.name === result.value.title)
  return hit ? hit.id : result.value.title
})

function now() {
  const d = new Date()
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function finishWith(index) {
  result.value = recognitionSamples[index]
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

function saveRecord() {
  if (!result.value) return
  history.value.unshift({
    species: result.value.species,
    title: result.value.title,
    confidence: result.value.confidence,
    time: now()
  })
  showToast('已保存到识别记录', { type: 'success' })
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

.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.metric {
  text-align: center;
  padding: 12px 6px;
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
}
.metric.good { background: var(--color-sage-soft); }
.metric.watch { background: #fbe7d2; }
.metric-val {
  display: block;
  font-weight: 700;
  font-size: 16px;
  color: var(--color-ink);
}
.metric-label {
  display: block;
  font-size: 11px;
  color: var(--color-muted);
  margin-top: 3px;
}
.result-note {
  margin: 16px 0;
  font-size: 14px;
  line-height: 1.65;
  color: var(--color-ink-2);
  padding: 12px 14px;
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-accent);
}
.result-foot {
  display: flex;
  gap: 10px;
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
.rec-body { flex: 1; display: flex; flex-direction: column; }
.rec-name { font-weight: 700; font-size: 15px; }
.rec-time { font-size: 12px; color: var(--color-muted); }
.rec-conf {
  font-weight: 700;
  color: var(--color-accent-ink);
  font-size: 15px;
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

@media (prefers-reduced-motion: reduce) {
  .vf-scan, .scanning-text, .vf-illu { animation: none; }
}
</style>
