<template>
  <section class="screen" v-if="doc">
    <header class="r-head">
      <button class="back" type="button" @click="goBack" aria-label="返回">
        <AppIcon name="back" :size="22" />
      </button>
      <span class="r-title">医生详情</span>
      <span class="back"></span>
    </header>

    <!-- 医生信息 -->
    <article class="hero" v-reveal>
      <span class="hero-av" :class="doc.dept">{{ doc.name.slice(0, 1) }}</span>
      <div class="hero-body">
        <div class="hero-top">
          <span class="hero-name">{{ doc.name }}</span>
          <span class="hero-title">{{ doc.title }}</span>
        </div>
        <p class="hero-hosp">{{ doc.hospital }}</p>
        <div class="hero-stats">
          <div class="hs">
            <b class="num">{{ doc.rating }}</b>
            <span>评分</span>
          </div>
          <div class="hs">
            <b class="num">{{ doc.consults }}+</b>
            <span>接诊量</span>
          </div>
          <div class="hs">
            <b class="num">{{ doc.years }}</b>
            <span>执业年</span>
          </div>
        </div>
      </div>
    </article>

    <div class="sched" :class="{ on: doc.online }">
      <AppIcon name="clock" :size="14" />
      <span>{{ doc.slot }}</span>
      <span v-if="doc.online" class="sched-live">在线接诊中</span>
    </div>

    <div class="block" v-reveal="{ delay: 40 }">
      <h3 class="block-h">擅长领域</h3>
      <div class="tags">
        <span v-for="t in doc.tags" :key="t" class="tag">{{ t }}</span>
      </div>
      <p class="intro">{{ doc.intro }}</p>
    </div>

    <div class="block" v-reveal="{ delay: 60 }">
      <h3 class="block-h">资质认证</h3>
      <ul class="certs">
        <li v-for="c in doc.certs" :key="c">
          <AppIcon name="verified" :size="15" />
          <span>{{ c }}</span>
        </li>
      </ul>
    </div>

    <!-- 病例摘要：转诊的核心，医生接诊前先看这份，避免重复追问 -->
    <div class="block" v-reveal="{ delay: 80 }">
      <div class="block-h-row">
        <h3 class="block-h">病例摘要</h3>
        <span class="block-hint">医生接诊前可见</span>
      </div>
      <div class="summary" :class="{ ai: hasAI }">
        <header class="sm-head">
          <AppIcon :name="hasAI ? 'sparkle' : 'notes'" :size="14" />
          {{ hasAI ? 'AI 已自动生成，可补充修改' : '请描述宠物情况' }}
        </header>
        <div v-if="hasAI" class="sm-fixed">
          <p><b>{{ summary.petName }}</b> · {{ summary.breed }} · {{ summary.age }}岁 · {{ summary.weight }}kg · {{ summary.gender }}</p>
          <p v-if="summary.symptoms.length">症状标签：{{ summary.symptoms.join('、') }}</p>
          <p v-if="summary.triage">AI 初步判断：{{ summary.triage.label }}</p>
        </div>
        <textarea
          v-model="note"
          class="sm-input"
          rows="3"
          :placeholder="hasAI ? '补充症状持续时间、精神状态、已用药物等…' : '例如：麻薯，3岁英短，挠右耳 3 天，耳道有褐色分泌物，精神食欲正常。'"
        ></textarea>
      </div>
    </div>

    <!-- 问诊方式 -->
    <div class="block" v-reveal="{ delay: 100 }">
      <h3 class="block-h">选择问诊方式</h3>
      <div class="modes">
        <button
          v-for="m in consultModes"
          :key="m.id"
          class="mode"
          :class="{ on: mode === m.id }"
          type="button"
          @click="mode = m.id"
        >
          <span class="mode-ic"><AppIcon :name="m.icon" :size="18" /></span>
          <span class="mode-body">
            <span class="mode-t">{{ m.label }}</span>
            <span class="mode-d">{{ m.desc }}</span>
            <span class="mode-e">{{ m.eta }}</span>
          </span>
          <span class="mode-p">¥{{ m.price }}</span>
        </button>
      </div>
    </div>

    <!-- 用户评价 -->
    <div class="block" v-reveal="{ delay: 120 }">
      <div class="block-h-row">
        <h3 class="block-h">用户评价</h3>
        <span class="block-hint">{{ doc.reviews.length }} 条</span>
      </div>
      <ul class="reviews">
        <li v-for="(r, i) in doc.reviews" :key="i" class="rv">
          <div class="rv-top">
            <span class="rv-user">{{ r.user }}</span>
            <span class="rv-stars">
              <AppIcon v-for="n in r.rating" :key="n" name="star" :size="11" />
            </span>
            <span class="rv-time">{{ r.time }}</span>
          </div>
          <p class="rv-text">{{ r.text }}</p>
        </li>
      </ul>
    </div>

    <p class="tip">问诊费用用于医生诊疗服务，接诊前可随时取消并全额退款。</p>

    <!-- 底部下单栏 -->
    <div class="paybar">
      <div class="pay-price">
        <span class="pay-n num">¥{{ price }}</span>
        <span class="pay-l">{{ modeLabel }}</span>
      </div>
      <button class="pay-btn" type="button" @click="submit">
        立即问诊
        <AppIcon name="back" :size="15" class="pay-arrow" />
      </button>
    </div>
  </section>

  <p v-else class="empty">未找到该医生。</p>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import { doctors, consultModes } from '@/data/mock'
import { createConsultOrder } from '@/data/ops'
import { showToast } from '@/composables/toast'

const route = useRoute()
const router = useRouter()
function goBack() {
  router.back()
}

const doc = computed(() => doctors.find((d) => d.id === route.params.id) || null)

const mode = ref('text')
const note = ref('')
const summary = ref(null)
const hasAI = computed(() => !!summary.value)

onMounted(() => {
  try {
    const raw = sessionStorage.getItem('petwise_case_summary')
    if (raw) summary.value = JSON.parse(raw)
  } catch {
    summary.value = null
  }
})

const price = computed(() => (consultModes.find((m) => m.id === mode.value) || consultModes[0]).price)
const modeLabel = computed(() => (consultModes.find((m) => m.id === mode.value) || consultModes[0]).label)

function submit() {
  if (!doc.value) return
  const base = summary.value || {}
  const order = createConsultOrder({
    doctorId: doc.value.id,
    mode: mode.value,
    petId: base.petId || 'mochi',
    price: price.value,
    summary: {
      petName: base.petName || '未指定',
      breed: base.breed || '',
      age: base.age ?? '',
      weight: base.weight ?? '',
      gender: base.gender || '',
      symptoms: base.symptoms || [],
      complaints: base.complaints || [],
      triage: base.triage || null,
      note: note.value
    }
  })
  showToast(`已提交给 ${doc.value.name} 医生，请稍候`, { type: 'success' })
  router.replace(`/consultation/${order.id}`)
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

/* ---------- 医生头 ---------- */
.hero {
  display: flex;
  gap: 14px;
  padding: 16px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
}
.hero-av {
  width: 58px;
  height: 58px;
  border-radius: 32%;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 25px;
  color: var(--color-ink);
  flex-shrink: 0;
  background: var(--grad-sand);
}
.hero-av.internal { background: var(--grad-sage); }
.hero-av.er { background: var(--grad-peach); }
.hero-av.derma { background: var(--grad-sage); }
.hero-av.nutrition { background: var(--grad-peach); }
.hero-body { flex: 1; min-width: 0; }
.hero-top { display: flex; align-items: baseline; gap: 7px; }
.hero-name { font-family: var(--font-display); font-weight: 700; font-size: 20px; letter-spacing: -0.02em; }
.hero-title { font-size: 12px; font-weight: 600; color: var(--color-muted); }
.hero-hosp { font-size: 12.5px; color: var(--color-muted); margin-top: 5px; line-height: 1.5; }
.hero-stats { display: flex; gap: 18px; margin-top: 11px; }
.hs { display: flex; flex-direction: column; gap: 1px; }
.hs b { font-size: 16px; font-weight: 700; }
.hs span { font-size: 11px; color: var(--color-faint); }

.sched {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 10px;
  padding: 10px 13px;
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  font-size: 12.5px;
  color: var(--color-muted);
}
.sched.on { background: var(--color-sage-soft); color: var(--color-good); }
.sched-live { margin-left: auto; font-weight: 700; font-size: 12px; }

/* ---------- 区块 ---------- */
.block { margin-top: 22px; }
.block-h-row { display: flex; align-items: baseline; justify-content: space-between; }
.block-h {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 16px;
  letter-spacing: -0.01em;
}
.block-hint { font-size: 11px; color: var(--color-faint); }

.tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.tag {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--color-ink-2);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  padding: 5px 11px;
  border-radius: var(--radius-pill);
}
.intro {
  font-size: 13.5px;
  line-height: 1.7;
  color: var(--color-ink-2);
  margin-top: 11px;
}

.certs { list-style: none; margin-top: 10px; display: flex; flex-direction: column; gap: 8px; }
.certs li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  color: var(--color-ink-2);
}
.certs svg { color: var(--color-good); flex-shrink: 0; }

/* ---------- 病例摘要 ---------- */
.summary {
  margin-top: 10px;
  border-radius: var(--radius-md);
  border: 1px solid var(--hairline);
  background: var(--color-surface);
  padding: 13px;
}
.summary.ai {
  border-color: color-mix(in srgb, var(--color-accent) 28%, transparent);
  background: var(--color-accent-soft);
}
.sm-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-accent-ink);
}
.summary:not(.ai) .sm-head { color: var(--color-muted); }
.sm-fixed { margin-top: 9px; display: flex; flex-direction: column; gap: 4px; }
.sm-fixed p { font-size: 12.5px; color: var(--color-ink-2); line-height: 1.55; }
.sm-input {
  width: 100%;
  margin-top: 9px;
  border: 1px solid var(--hairline-strong);
  background: var(--color-surface);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  font-size: 13.5px;
  line-height: 1.6;
  color: var(--color-ink);
  font-family: inherit;
  resize: vertical;
  outline: none;
}
.sm-input:focus-visible { border-color: var(--color-accent); }

/* ---------- 问诊方式 ---------- */
.modes { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
.mode {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 13px;
  border-radius: var(--radius-md);
  border: 1px solid var(--hairline);
  background: var(--color-surface);
  text-align: left;
  transition: border-color var(--dur-fast), background var(--dur-fast);
}
.mode.on {
  border-color: var(--color-accent);
  background: var(--color-accent-soft);
}
.mode-ic {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  background: var(--color-surface-2);
  color: var(--color-ink-2);
  flex-shrink: 0;
}
.mode.on .mode-ic { background: var(--color-surface); color: var(--color-accent-ink); }
.mode-body { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.mode-t { font-size: 14.5px; font-weight: 700; }
.mode-d { font-size: 12px; color: var(--color-muted); line-height: 1.5; }
.mode-e { font-size: 11.5px; color: var(--color-faint); margin-top: 2px; }
.mode-p {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-accent-ink);
  flex-shrink: 0;
}

/* ---------- 评价 ---------- */
.reviews { list-style: none; margin-top: 10px; display: flex; flex-direction: column; gap: 10px; }
.rv {
  padding: 12px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
}
.rv-top { display: flex; align-items: center; gap: 8px; }
.rv-user { font-size: 13px; font-weight: 700; }
.rv-stars { display: inline-flex; gap: 1px; color: var(--color-watch); }
.rv-time { margin-left: auto; font-size: 11px; color: var(--color-faint); }
.rv-text { font-size: 13px; line-height: 1.6; color: var(--color-ink-2); margin-top: 6px; }

.tip {
  margin: 22px 0 8px;
  font-size: 11.5px;
  color: var(--color-faint);
  text-align: center;
  line-height: 1.5;
}

/* ---------- 下单栏 ---------- */
.paybar {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(78px + env(safe-area-inset-bottom, 0px));
  width: min(var(--shell-max), 100%);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  background: color-mix(in srgb, var(--color-surface) 94%, transparent);
  backdrop-filter: blur(14px);
  border-top: 1px solid var(--color-border);
  z-index: 20;
}
.pay-price { display: flex; flex-direction: column; }
.pay-n { font-size: 20px; font-weight: 700; color: var(--color-accent-ink); line-height: 1; }
.pay-l { font-size: 11px; color: var(--color-faint); margin-top: 3px; }
.pay-btn {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  background: var(--color-accent);
  padding: 13px 22px;
  border-radius: var(--radius-pill);
  transition: transform var(--dur-fast) var(--ease-out);
}
.pay-btn:active { transform: scale(0.97); }
.pay-arrow { transform: rotate(180deg); }

.empty { text-align: center; color: var(--color-muted); margin-top: 60px; }
</style>
