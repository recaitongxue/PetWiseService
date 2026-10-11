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
      <span class="pet-meta">{{ curPet.breed }} · {{ curPet.age }}岁 · {{ curPet.weight }}kg</span>
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
        <ChatBubble
          v-if="m.kind !== 'triage'"
          :role="m.role === 'me' ? 'me' : 'them'"
          :text="m.text"
          :time="m.time"
          :name="m.role === 'ai' ? 'AI' : '我'"
        />
        <TriageCard
          v-else
          :level="m.triage.level"
          :label="m.triage.label"
          :short="m.triage.short"
          :advice="m.triage.advice"
          :causes="m.triage.causes"
          :actions="m.triage.actions"
          :confidence="m.triage.confidence"
          @escalate="goDoctors(m.triage.dept)"
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

    <!-- 输入栏（固定底部，独立于滚动区） -->
    <div class="composer">
      <button class="composer-icon" type="button" @click="attach" aria-label="上传照片">
        <AppIcon name="image" :size="22" />
      </button>
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
import { consultSeed, consultSuggestions, pets, symptomGroups, triageRules } from '@/data/mock'
import { aiQuota, consumeAiQuota } from '@/data/ops'
import { showToast } from '@/composables/toast'

const route = useRoute()
const router = useRouter()

const petId = ref(pets[0].id)
const curPet = computed(() => pets.find((p) => p.id === petId.value) || pets[0])

const messages = ref([...consultSeed])
const input = ref('')
const typing = ref(false)
const followups = ref([])
const listEl = ref(null)
const picked = ref([])
const quota = ref(aiQuota())
const lastTriage = ref(null)

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

/* ---------- AI 分诊：关键词 → 分级 + 可能原因 + 建议动作 ---------- */

function matchRule(text) {
  const t = text.toLowerCase()
  for (const r of triageRules) {
    if (r.keywords.some((k) => t.includes(k))) return r
  }
  return null
}

function causesOf(text) {
  const t = text.toLowerCase()
  if (t.includes('耳朵') || t.includes('挠耳')) return ['耳螨', '真菌感染', '外耳道炎', '食物或环境过敏']
  if (t.includes('呕吐') || t.includes('吐'))
    return ['进食过快或饮食不当', '毛球症', '胃肠炎', '异物梗阻']
  if (t.includes('软便') || t.includes('腹泻') || t.includes('拉稀'))
    return ['换粮应激', '肠道寄生虫', '菌群失调', '食物不耐受']
  if (t.includes('皮肤') || t.includes('红疹') || t.includes('脱毛') || t.includes('斑秃'))
    return ['过敏性皮炎', '真菌感染', '跳蚤叮咬', '蠕形螨']
  if (t.includes('食欲') || t.includes('不吃') || t.includes('挑食'))
    return ['环境应激', '口腔或牙齿问题', '消化不适', '潜在发热性疾病']
  if (t.includes('呼吸') || t.includes('咳嗽') || t.includes('喘'))
    return ['上呼吸道感染', '过敏反应', '心脏问题', '气管异物']
  if (t.includes('体重') || t.includes('胖') || t.includes('瘦'))
    return ['喂食过量', '运动量不足', '内分泌异常', '年龄相关代谢变化']
  if (t.includes('掉毛') || t.includes('皮屑'))
    return ['季节性换毛', '营养不均衡', '皮肤疾病', '长期应激']
  if (t.includes('眼') || t.includes('泪'))
    return ['结膜炎', '角膜损伤', '鼻泪管阻塞', '异物刺激']
  if (t.includes('跛') || t.includes('腿') || t.includes('瘸'))
    return ['软组织挫伤', '关节问题', '骨折', '趾间炎']
  return ['饮食与环境因素', '轻度感染', '应激反应', '品种相关易感问题']
}

function deptOf(text) {
  const t = text.toLowerCase()
  if (
    t.includes('呼吸困难') || t.includes('抽搐') || t.includes('中毒') ||
    t.includes('误食') || t.includes('骨折') || t.includes('大出血')
  ) return 'er'
  if (t.includes('皮肤') || t.includes('耳朵') || t.includes('掉毛') || t.includes('红疹') || t.includes('脱毛'))
    return 'derma'
  if (t.includes('跛') || t.includes('腿') || t.includes('伤口')) return 'surgery'
  if (t.includes('眼') || t.includes('泪')) return 'eye'
  if (t.includes('体重') || t.includes('胖') || t.includes('喂')) return 'nutrition'
  if (t.includes('鸟') || t.includes('兔') || t.includes('龟')) return 'exotic'
  return 'internal'
}

// 演示用：根据关键词生成贴合的问诊回复（接入大模型后由后端流式返回）
function aiReply(text) {
  const t = text.toLowerCase()
  if (t.includes('耳朵')) {
    return '频繁挠耳朵常见原因有耳螨、外耳道炎或过敏。建议先观察耳道是否有黑褐色分泌物或异味，避免自行掏挖。若持续 2 天以上或宠物表现出疼痛，请预约线下检查。'
  }
  if (t.includes('吃饭') || t.includes('食欲') || t.includes('不爱吃')) {
    return '短期食欲下降可能与天气、应激或食物变更有关。可尝试少量多餐、温热食物。若超过 24 小时拒食、伴随呕吐或精神萎靡，请尽快问诊。'
  }
  if (t.includes('疫苗')) {
    return '幼猫/幼犬基础免疫通常在 6–8 周开始，每 2–4 周一针，完成基础免疫后每年加强。接种前需确保宠物健康、无寄生虫。'
  }
  if (t.includes('皮肤') || t.includes('照片')) {
    return '已收到照片区域描述。皮肤问题需关注红斑、脱毛、皮屑与抓挠频率。请保持患处干燥清洁，避免舔舐；若范围扩大或出现渗液，建议拍照后线下面诊。'
  }
  return '我理解你的情况了。请补充一下宠物的年龄、品种、症状持续时间和精神状态，我会给出更有针对性的初步判断。注意：我的建议仅作参考，紧急情况请立即就医。'
}

// 根据对话生成相关随访建议，让对话自然延续
function genFollowups(text) {
  const t = text.toLowerCase()
  if (t.includes('耳朵')) return ['耳道怎么清洁？', '需要买耳药吗？', '多久能好？']
  if (t.includes('吃饭') || t.includes('食欲')) return ['能喂什么开胃？', '要去医院吗？', '精神差怎么判断？']
  if (t.includes('疫苗')) return ['接种记录怎么看', '接种后注意什么', '能洗澡吗？']
  if (t.includes('皮肤')) return ['居家怎么护理', '要忌口吗', '什么时候必须面诊']
  return ['帮我记录症状', '这种情况要去医院吗', '日常怎么护理']
}

function send(preset) {
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
  scrollToEnd()
  setTimeout(() => {
    typing.value = false

    const rule = matchRule(text)
    if (rule) {
      // 命中分诊规则 → 输出结构化分诊卡，而不是一段散文本
      const triage = {
        level: rule.level,
        label: rule.label,
        short: rule.short,
        advice: rule.advice,
        causes: causesOf(text),
        actions: rule.actions,
        confidence: rule.level === 'emergency' ? '高' : '中',
        dept: deptOf(text)
      }
      lastTriage.value = triage
      messages.value.push({ role: 'ai', kind: 'triage', time: now(), triage })
      followups.value = ['这种情况要立刻去医院吗', '现在能做些什么', '转真人医生看看']
    } else {
      messages.value.push({ role: 'ai', text: aiReply(text), time: now() })
      followups.value = genFollowups(text)
    }

    quota.value = consumeAiQuota()
    scrollToEnd()
  }, 1300)
}

function attach() {
  if (typing.value) return
  messages.value.push({ role: 'me', text: '📷 已上传一张宠物照片', time: now() })
  followups.value = []
  scrollToEnd()
  typing.value = true
  setTimeout(() => {
    typing.value = false
    messages.value.push({
      role: 'ai',
      text: '收到照片。从画面看毛发状态尚可，请告诉我你最担心的部位，我帮你重点看看。',
      time: now()
    })
    followups.value = genFollowups('照片')
    scrollToEnd()
  }, 1200)
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

onMounted(scrollToEnd)
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
  padding-bottom: 96px;
}

/* 随访建议 */
.followups {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(78px + 56px + env(safe-area-inset-bottom, 0px));
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

/* 输入栏：固定底部，独立于滚动区 */
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

.disclaimer {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(78px + 56px + 44px + env(safe-area-inset-bottom, 0px));
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

@media (prefers-reduced-motion: reduce) {
  .typing span { animation: none; }
}
</style>
