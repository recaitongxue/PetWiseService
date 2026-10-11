<template>
  <section class="screen room" v-if="order">
    <header class="r-head">
      <button class="back" type="button" @click="leave" aria-label="返回">
        <AppIcon name="back" :size="22" />
      </button>
      <div class="doc-mini">
        <span class="doc-mini-av" :class="doc.dept">{{ doc.name.slice(0, 1) }}</span>
        <div>
          <p class="doc-mini-n">{{ doc.name }} <span>{{ doc.title }}</span></p>
          <p class="doc-mini-s">
            <span class="live-dot" :class="{ on: doc.online }"></span>
            {{ doc.deptLabel }} · {{ doc.hospital.slice(0, 12) }}…
          </p>
        </div>
      </div>
      <button class="end-btn" type="button" @click="openRate" v-if="order.state !== 'closed'">结束</button>
      <span class="back" v-else></span>
    </header>

    <!-- 订单状态条 -->
    <div class="state-bar" :class="order.state">
      <AppIcon :name="stateIcon" :size="14" />
      <span>{{ stateText }}</span>
      <span class="state-mode">{{ modeLabel }}</span>
    </div>

    <!-- 通话入口（电话 / 视频问诊方式） -->
    <div v-if="order.mode !== 'text'" class="call-card">
      <span class="call-ic"><AppIcon :name="order.mode === 'video' ? 'video' : 'phone'" :size="20" /></span>
      <div class="call-body">
        <p class="call-t">{{ order.mode === 'video' ? '视频问诊 20 分钟' : '电话问诊 15 分钟' }}</p>
        <p class="call-s">医生将在预约时段主动接入，也可在此补充照片与描述</p>
      </div>
      <button class="call-btn" type="button" @click="startCall">
        {{ order.mode === 'video' ? '发起视频' : '呼叫' }}
      </button>
    </div>

    <!-- 病例摘要：医生已读 -->
    <article class="summary">
      <header class="sm-t">
        <AppIcon name="notes" :size="14" />
        病例摘要 · 医生已查看
      </header>
      <p class="sm-line">
        <b>{{ petName }}</b>
        <span v-if="order.summary.breed"> · {{ order.summary.breed }}</span>
        <span v-if="order.summary.age !== ''"> · {{ order.summary.age }}岁</span>
        <span v-if="order.summary.weight !== ''"> · {{ order.summary.weight }}kg</span>
      </p>
      <p class="sm-line" v-if="order.summary.symptoms?.length">
        症状标签：{{ order.summary.symptoms.join('、') }}
      </p>
      <p class="sm-line" v-if="order.summary.triage">
        AI 初步判断：{{ order.summary.triage.label }}
      </p>
      <p class="sm-line" v-if="order.summary.note">补充：{{ order.summary.note }}</p>
    </article>

    <!-- 对话区 -->
    <div class="chat-list" ref="listEl">
      <template v-for="(m, i) in msgs" :key="i">
        <div v-if="m.type === 'system'" class="sys">{{ m.text }}</div>
        <ChatBubble
          v-else-if="m.type !== 'rx'"
          :role="m.from === 'me' ? 'me' : 'them'"
          :text="m.text"
          :time="m.time"
          :name="m.from === 'me' ? '我' : doc.name"
        />
        <article v-else class="rx">
          <header class="rx-head">
            <AppIcon name="file" :size="15" />
            电子处方建议
            <span class="rx-by">{{ doc.name }} 医生</span>
          </header>
          <ul class="rx-list">
            <li v-for="d in m.drugs" :key="d.name">
              <div class="rx-d-top">
                <span class="rx-name">{{ d.name }}</span>
                <span class="rx-dose">{{ d.dose }}</span>
              </div>
              <p class="rx-use">{{ d.use }}</p>
            </li>
          </ul>
          <p class="rx-note">{{ m.note }}</p>
        </article>
      </template>
      <div v-if="typing" class="typing">
        <span></span><span></span><span></span>
      </div>
    </div>

    <!-- 输入栏 -->
    <div class="composer">
      <button class="composer-icon" type="button" @click="attach" aria-label="上传照片">
        <AppIcon name="image" :size="22" />
      </button>
      <input
        v-model="input"
        class="composer-input"
        type="text"
        placeholder="补充描述或追问…"
        @keyup.enter="send"
      />
      <button class="composer-send" type="button" :disabled="!input.trim() || typing" @click="send" aria-label="发送">
        <AppIcon name="send" :size="20" />
      </button>
    </div>

    <!-- 评价弹层 -->
    <transition name="sheet">
      <div v-if="rateOpen" class="sheet-mask" @click.self="rateOpen = false">
        <div class="sheet">
          <h3 class="sheet-t">本次问诊体验如何？</h3>
          <p class="sheet-s">你的评价会帮助其他宠主选择合适的医生</p>
          <div class="stars">
            <button
              v-for="n in 5"
              :key="n"
              class="star"
              :class="{ on: n <= score }"
              type="button"
              @click="score = n"
              :aria-label="`${n} 星`"
            >
              <AppIcon name="star" :size="26" />
            </button>
          </div>
          <div class="rate-tags">
            <button
              v-for="t in rateTags"
              :key="t"
              class="rate-tag"
              :class="{ on: tags.includes(t) }"
              type="button"
              @click="toggleTag(t)"
            >
              {{ t }}
            </button>
          </div>
          <button class="sheet-submit" type="button" @click="submitRate">提交并结束问诊</button>
        </div>
      </div>
    </transition>
  </section>

  <p v-else class="empty">问诊单不存在或已结束。</p>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import ChatBubble from '@/components/ChatBubble.vue'
import { doctors, pets, consultModes } from '@/data/mock'
import { orderById, appendOrderMessage, closeOrder, rateOrder, saveReport } from '@/data/ops'
import { showToast } from '@/composables/toast'

const route = useRoute()
const router = useRouter()

const order = ref(orderById(route.params.id))
const doc = computed(() => doctors.find((d) => d.id === order.value?.doctorId) || doctors[0])
const petName = computed(() => {
  const p = pets.find((x) => x.id === order.value?.petId)
  return p ? p.name : order.value?.summary?.petName || '宠物'
})
const modeLabel = computed(
  () => (consultModes.find((m) => m.id === order.value?.mode) || consultModes[0]).label
)

const msgs = ref(order.value ? [...order.value.messages] : [])
const input = ref('')
const typing = ref(false)
const listEl = ref(null)
const rateOpen = ref(false)
const score = ref(5)
const tags = ref([])
const rateTags = ['专业', '回复及时', '有耐心', '建议实用', '讲得清楚']

const stateText = computed(
  () =>
    ({ pending: '已提交，等待医生接诊', replied: '医生已回复，可继续追问', closed: '本次问诊已结束' }[
      order.value?.state
    ] || '问诊中')
)
const stateIcon = computed(
  () => ({ pending: 'clock', replied: 'check', closed: 'check' }[order.value?.state] || 'clock')
)

// 演示脚本：模拟医生接诊后的分轮回复（接入后端后由消息推送驱动）
const script = ref([
  '你好，我是' + (doctors.find((d) => d.id === order.value?.doctorId) || doctors[0]).name + '医生。已看过 AI 的初步判断和病例摘要，不用重复描述。',
  '从描述看倾向于是常见问题，先按下面的方案处理，注意观察 3 天。',
  '如果出现精神变差、拒食或症状加重，请立刻线下就诊，不要等。'
])
const step = ref(0)

function now() {
  const d = new Date()
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function scrollToEnd() {
  nextTick(() => {
    if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
  })
}

function push(msg) {
  msgs.value.push(msg)
  if (order.value) appendOrderMessage(order.value.id, msg)
  scrollToEnd()
}

function doctorReply() {
  typing.value = true
  scrollToEnd()
  setTimeout(() => {
    typing.value = false
    if (step.value < script.value.length) {
      push({ type: 'text', from: 'doc', text: script.value[step.value], time: now() })
      step.value += 1
    }
    // 第二轮后给出处方建议，让问诊闭环到用药方案
    if (step.value === 2) {
      setTimeout(() => {
        push({
          type: 'rx',
          from: 'doc',
          time: now(),
          drugs: [
            { name: '耳道清洁液', dose: '每日 1 次', use: '滴入耳道后轻揉耳根 30 秒，让宠物自行甩出' },
            { name: '复方制霉菌素软膏', dose: '每日 2 次', use: '薄涂于耳廓内侧，连续使用 7 天' }
          ],
          note: '用药 7 天后如未改善，需线下做耳道镜检与分泌物涂片，排除耐药菌感染。'
        })
      }, 900)
    }
    if (order.value && order.value.state === 'pending') {
      order.value.state = 'replied'
    }
  }, 1200)
}

function send() {
  const text = input.value.trim()
  if (!text || typing.value) return
  push({ type: 'text', from: 'me', text, time: now() })
  input.value = ''
  doctorReply()
}

function attach() {
  push({ type: 'text', from: 'me', text: '📷 已上传一张患处照片', time: now() })
  doctorReply()
}

function startCall() {
  showToast('演示环境暂不支持真实通话，已通知医生改以图文继续', { type: 'info' })
}

function toggleTag(t) {
  const i = tags.value.indexOf(t)
  if (i >= 0) tags.value.splice(i, 1)
  else tags.value.push(t)
}

function openRate() {
  rateOpen.value = true
}

function submitRate() {
  if (!order.value) return
  rateOrder(order.value.id, order.value.doctorId, score.value, tags.value.slice())
  closeOrder(order.value.id)
  const o = orderById(order.value.id)
  order.value = o
  rateOpen.value = false
  showToast('评价已提交，已生成问诊报告', { type: 'success' })

  // 结束即沉淀：把医生的文字建议与处方固化为一份报告
  const advice = msgs.value.filter((m) => m.type === 'text' && m.from === 'doc').map((m) => m.text)
  const rxMsg = [...msgs.value].reverse().find((m) => m.type === 'rx')
  const aiLevel = o?.summary?.triage?.level
  const report = saveReport({
    type: 'human',
    orderId: o?.id,
    petId: o?.petId,
    petName: petName.value,
    title: `${doc.value.name}医生 · ${o?.summary?.note || o?.summary?.symptoms?.[0] || '线上问诊'}`,
    preview: `${modeLabel.value} · ${doc.value.name}${doc.value.title} 已完成问诊`,
    chief: {
      partLabel: '',
      symptomLabels: o?.summary?.symptoms || [],
      durationLabel: '',
      severityLabel: '',
      accompanyLabels: [],
      note: o?.summary?.note || (o?.summary?.complaints || []).join('；'),
      photos: 0
    },
    triage: {
      level: aiLevel || 'urgent',
      label: '医生已接诊',
      short: '已完成线上问诊',
      advice: '医生已给出处理方案，请按医嘱执行并观察恢复情况。',
      causes: [],
      actions: ['按医嘱用药，不自行加减剂量', '观察 3 天并记录变化', '按时复查'],
      score: 0,
      factors: [],
      followUp: '如用药后无改善或症状加重，请及时复诊。'
    },
    doctor: { id: doc.value.id, name: doc.value.name, title: doc.value.title },
    doctorAdvice: advice,
    rx: rxMsg ? { drugs: rxMsg.drugs, note: rxMsg.note } : null
  })

  router.replace(`/report/${report.id}`)
}

function leave() {
  router.push('/records')
}

onMounted(() => {
  if (order.value && !order.value.messages.length) {
    push({ type: 'system', text: `已向 ${doc.value.name} 医生提交问诊单，${doc.value.responseMin} 分钟内接诊`, time: now() })
    setTimeout(doctorReply, 1500)
  } else {
    scrollToEnd()
  }
})
</script>

<style scoped>
.r-head {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 0 12px;
}
.back { width: 40px; height: 40px; display: grid; place-items: center; border-radius: 50%; flex-shrink: 0; }
.doc-mini { flex: 1; display: flex; align-items: center; gap: 9px; min-width: 0; }
.doc-mini-av {
  width: 36px;
  height: 36px;
  border-radius: 32%;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 16px;
  color: var(--color-ink);
  background: var(--grad-sand);
  flex-shrink: 0;
}
.doc-mini-av.internal { background: var(--grad-sage); }
.doc-mini-av.er { background: var(--grad-peach); }
.doc-mini-av.derma { background: var(--grad-sage); }
.doc-mini-n { font-size: 14px; font-weight: 700; line-height: 1.2; }
.doc-mini-n span { font-size: 11px; font-weight: 600; color: var(--color-muted); }
.doc-mini-s {
  font-size: 11px;
  color: var(--color-faint);
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.live-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--color-faint); }
.live-dot.on { background: var(--color-good); }
.end-btn {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-ink);
  background: var(--color-surface);
  border: 1px solid var(--hairline-strong);
  padding: 7px 14px;
  border-radius: var(--radius-pill);
}

/* ---------- 状态条 ---------- */
.state-bar {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 9px 13px;
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  font-size: 12.5px;
  color: var(--color-muted);
  margin-bottom: 12px;
}
.state-bar.replied { background: var(--color-sage-soft); color: var(--color-good); }
.state-bar.closed { background: var(--color-surface-2); }
.state-mode { margin-left: auto; font-weight: 700; font-size: 11.5px; }

/* ---------- 通话卡 ---------- */
.call-card {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 13px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  margin-bottom: 12px;
}
.call-ic {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  background: var(--color-accent-soft);
  color: var(--color-accent-ink);
  flex-shrink: 0;
}
.call-body { flex: 1; min-width: 0; }
.call-t { font-size: 14px; font-weight: 700; }
.call-s { font-size: 11.5px; color: var(--color-muted); margin-top: 2px; line-height: 1.5; }
.call-btn {
  flex-shrink: 0;
  font-size: 12.5px;
  font-weight: 700;
  color: #fff;
  background: var(--color-accent);
  padding: 9px 14px;
  border-radius: var(--radius-pill);
  transition: transform var(--dur-fast) var(--ease-out);
}
.call-btn:active { transform: scale(0.96); }

/* ---------- 病例摘要 ---------- */
.summary {
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  padding: 12px 13px;
  margin-bottom: 16px;
}
.sm-t {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-faint);
}
.sm-line { font-size: 12.5px; color: var(--color-ink-2); line-height: 1.6; margin-top: 6px; }

/* ---------- 对话 ---------- */
.chat-list {
  display: flex;
  flex-direction: column;
  padding-bottom: 96px;
}
.sys {
  align-self: center;
  font-size: 11.5px;
  color: var(--color-faint);
  background: var(--color-surface-2);
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  margin-bottom: 14px;
}

/* 处方卡 */
.rx {
  border-radius: var(--radius-lg);
  border: 1px solid color-mix(in srgb, var(--color-good) 30%, transparent);
  background: var(--color-surface);
  padding: 14px;
  margin-bottom: 16px;
}
.rx-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13.5px;
  font-weight: 700;
  color: var(--color-good);
}
.rx-by { margin-left: auto; font-size: 11px; font-weight: 600; color: var(--color-faint); }
.rx-list { list-style: none; margin-top: 11px; display: flex; flex-direction: column; gap: 10px; }
.rx-list li { padding-bottom: 10px; border-bottom: 1px solid var(--hairline); }
.rx-list li:last-child { border-bottom: none; padding-bottom: 0; }
.rx-d-top { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
.rx-name { font-size: 14px; font-weight: 700; }
.rx-dose { font-size: 12px; font-weight: 700; color: var(--color-accent-ink); flex-shrink: 0; }
.rx-use { font-size: 12.5px; color: var(--color-ink-2); line-height: 1.6; margin-top: 3px; }
.rx-note {
  font-size: 12px;
  color: var(--color-muted);
  line-height: 1.6;
  margin-top: 11px;
  padding-top: 10px;
  border-top: 1px solid var(--hairline);
}

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

/* ---------- 输入栏 ---------- */
.composer {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(78px + env(safe-area-inset-bottom, 0px));
  width: min(var(--shell-max), 100%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: color-mix(in srgb, var(--color-surface) 92%, transparent);
  backdrop-filter: blur(14px);
  border-top: 1px solid var(--color-border);
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

/* ---------- 评价弹层 ---------- */
.sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: rgba(20, 30, 24, 0.42);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.sheet {
  width: min(var(--shell-max), 100%);
  background: var(--color-surface);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  padding: 22px 20px calc(24px + env(safe-area-inset-bottom, 0px));
}
.sheet-t {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 19px;
  text-align: center;
  letter-spacing: -0.01em;
}
.sheet-s { font-size: 12.5px; color: var(--color-muted); text-align: center; margin-top: 5px; }
.stars { display: flex; justify-content: center; gap: 8px; margin: 18px 0 16px; }
.star { color: var(--color-sand); transition: transform var(--dur-fast) var(--ease-out); }
.star.on { color: var(--color-watch); }
.star:active { transform: scale(0.9); }
.rate-tags { display: flex; flex-wrap: wrap; gap: 7px; justify-content: center; }
.rate-tag {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink-2);
  background: var(--color-surface-2);
  border: 1px solid var(--hairline);
  padding: 7px 13px;
  border-radius: var(--radius-pill);
  transition: color var(--dur-fast), border-color var(--dur-fast), background var(--dur-fast);
}
.rate-tag.on {
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  border-color: color-mix(in srgb, var(--color-accent) 38%, transparent);
}
.sheet-submit {
  width: 100%;
  margin-top: 20px;
  padding: 15px;
  border-radius: var(--radius-pill);
  background: var(--color-accent);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  transition: transform var(--dur-fast) var(--ease-out);
}
.sheet-submit:active { transform: scale(0.978); }

.sheet-enter-active, .sheet-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.sheet-enter-active .sheet, .sheet-leave-active .sheet { transition: transform var(--dur-base) var(--ease-out); }
.sheet-enter-from, .sheet-leave-to { opacity: 0; }
.sheet-enter-from .sheet, .sheet-leave-to .sheet { transform: translateY(100%); }

.empty { text-align: center; color: var(--color-muted); margin-top: 60px; }

@media (prefers-reduced-motion: reduce) {
  .typing span { animation: none; }
}
</style>
