<template>
  <section class="screen hub">
    <header class="screen-head" v-reveal>
      <div>
        <p class="eyebrow">CONSULT · 问诊中心</p>
        <h1 class="title">问诊</h1>
      </div>
      <router-link to="/records" class="head-link">
        <AppIcon name="file" :size="15" />
        记录
      </router-link>
    </header>

    <!-- 限时免费条：前期全功能免费，不做付费墙 -->
    <div class="quota" v-reveal="{ delay: 30 }">
      <AppIcon name="sparkle" :size="13" />
      <span>AI 问诊<b class="num">限时免费</b>中，今日剩余 {{ quota.left }} 次</span>
      <span class="quota-note">用不完转真人，病例自动带过去</span>
    </div>

    <!-- 三大入口：结构化预问诊 → AI 问诊 → 真人 -->
    <div class="entries">
      <router-link to="/preconsult" class="entry primary" v-reveal="{ delay: 60 }">
        <span class="entry-ic"><AppIcon name="firstaid" :size="20" /></span>
        <span class="entry-body">
          <span class="entry-t">
            结构化预问诊
            <span class="entry-badge">推荐</span>
          </span>
          <span class="entry-d">7 步向导收集病情，生成可带去医院的问诊报告</span>
        </span>
        <AppIcon name="back" :size="16" class="entry-go" />
      </router-link>

      <router-link to="/consult/ai" class="entry" v-reveal="{ delay: 90 }">
        <span class="entry-ic"><AppIcon name="stethoscope" :size="20" /></span>
        <span class="entry-body">
          <span class="entry-t">AI 智能问诊</span>
          <span class="entry-d">直接描述症状，结合品种知识库即时分诊</span>
        </span>
        <AppIcon name="back" :size="16" class="entry-go" />
      </router-link>

      <router-link to="/doctors" class="entry" v-reveal="{ delay: 120 }">
        <span class="entry-ic"><AppIcon name="verified" :size="20" /></span>
        <span class="entry-body">
          <span class="entry-t">找真人兽医</span>
          <span class="entry-d">
            <span class="dot-on"></span>{{ onlineCount }} 位在线 · 图文 / 电话 / 视频
          </span>
        </span>
        <AppIcon name="back" :size="16" class="entry-go" />
      </router-link>
    </div>

    <!-- 宠物档案速览：问诊前先给 AI 完整上下文 -->
    <div class="sec-head" v-reveal="{ delay: 140 }">
      <h3 class="sec-t">问诊对象</h3>
      <span class="sec-hint">档案自动带入问诊</span>
    </div>
    <div class="pet-strip">
      <router-link
        v-for="p in pets"
        :key="p.id"
        :to="`/pet/${p.id}`"
        class="pet-cell"
        v-reveal="{ delay: 150 }"
      >
        <PetAvatar :species="p.species" :name="p.name" :size="38" />
        <span class="pc-body">
          <b class="pc-name">{{ p.name }}</b>
          <span class="pc-meta">{{ p.breed }} · {{ p.age }}岁 · {{ p.weight }}kg</span>
          <span class="pc-score" :class="p.healthScore >= 85 ? 'good' : 'watch'">
            健康分 {{ p.healthScore }}
            <template v-if="p.nextVaccine"> · 疫苗 {{ shortDate(p.nextVaccine) }}</template>
          </span>
        </span>
      </router-link>
    </div>

    <!-- RAG 知识库：高频问题直达，答案有品种/病程出处 -->
    <div class="sec-head" v-reveal="{ delay: 180 }">
      <h3 class="sec-t">知识库高频问题</h3>
      <span class="sec-hint">基于品种档案与兽医指南</span>
    </div>
    <div class="rag">
      <button
        v-for="q in ragQuestions"
        :key="q.text"
        class="rag-chip"
        type="button"
        @click="askAI(q.text)"
      >
        <AppIcon name="search" :size="13" />
        {{ q.text }}
      </button>
    </div>

    <!-- 科室直达 -->
    <div class="sec-head" v-reveal="{ delay: 200 }">
      <h3 class="sec-t">按症状找科室</h3>
    </div>
    <div class="depts">
      <router-link
        v-for="d in deptList"
        :key="d.key"
        :to="{ path: '/doctors', query: { dept: d.key } }"
        class="dept-cell"
        v-reveal="{ delay: 210 }"
      >
        <span class="dept-ic" :class="d.tone"><AppIcon :name="d.icon" :size="16" /></span>
        <span class="dept-label">{{ d.label }}</span>
      </router-link>
    </div>

    <!-- 进行中的问诊单 -->
    <template v-if="ongoing.length">
      <div class="sec-head" v-reveal="{ delay: 220 }">
        <h3 class="sec-t">进行中的问诊</h3>
        <span class="sec-hint num">{{ ongoing.length }}</span>
      </div>
      <router-link
        v-for="o in ongoing"
        :key="o.id"
        :to="`/consultation/${o.id}`"
        class="order card"
        v-reveal="{ delay: 230 }"
      >
        <span class="order-ic"><AppIcon name="user" :size="18" /></span>
        <span class="order-body">
          <span class="order-row">
            <b class="order-name">{{ doctorOf(o).name }}</b>
            <span class="order-pill" :class="o.state">{{ stateText(o) }}</span>
          </span>
          <span class="order-sub">
            {{ doctorOf(o).deptLabel }} · {{ modeLabel(o.mode) }} · {{ petName(o.petId) }}
          </span>
          <span class="order-last">{{ lastMsg(o) }}</span>
        </span>
        <AppIcon name="back" :size="15" class="entry-go" />
      </router-link>
    </template>

    <!-- 最近报告 -->
    <template v-if="latestReports.length">
      <div class="sec-head" v-reveal="{ delay: 240 }">
        <h3 class="sec-t">最近问诊报告</h3>
        <router-link to="/records" class="sec-more">全部</router-link>
      </div>
      <router-link
        v-for="r in latestReports"
        :key="r.id"
        :to="`/report/${r.id}`"
        class="order card"
        v-reveal="{ delay: 250 }"
      >
        <span class="order-ic" :class="r.type"><AppIcon :name="r.type === 'ai' ? 'sparkle' : 'stethoscope'" :size="17" /></span>
        <span class="order-body">
          <span class="order-row">
            <b class="order-name">{{ r.title }}</b>
            <span class="order-pill">{{ r.type === 'ai' ? 'AI 预问诊' : '医生问诊' }}</span>
          </span>
          <span class="order-sub">{{ r.petName }} · {{ r.date }}</span>
          <span class="order-last">{{ reportBrief(r) }}</span>
        </span>
        <AppIcon name="back" :size="15" class="entry-go" />
      </router-link>
    </template>

    <!-- 辅助能力 -->
    <div class="sec-head" v-reveal="{ delay: 260 }">
      <h3 class="sec-t">辅助工具</h3>
    </div>
    <div class="minor">
      <router-link to="/recognize" class="minor-row" v-reveal="{ delay: 270 }">
        <span class="minor-ic"><AppIcon name="camera" :size="18" /></span>
        <span class="minor-body">
          <b>拍照看品种</b>
          <span>识别猫狗品种，识别结果可带入问诊继续追问</span>
        </span>
        <AppIcon name="back" :size="15" class="entry-go" />
      </router-link>
      <router-link to="/schedule" class="minor-row" v-reveal="{ delay: 280 }">
        <span class="minor-ic"><AppIcon name="calendar-check" :size="18" /></span>
        <span class="minor-body">
          <b>疫苗驱虫日程</b>
          <span>AI 一键生成养护计划，到期自动提醒</span>
        </span>
        <AppIcon name="back" :size="15" class="entry-go" />
      </router-link>
      <router-link to="/records" class="minor-row" v-reveal="{ delay: 290 }">
        <span class="minor-ic"><AppIcon name="notes" :size="18" /></span>
        <span class="minor-body">
          <b>问诊记录与报告</b>
          <span>{{ recordCount }} 条历史记录，支持回看完整报告</span>
        </span>
        <AppIcon name="back" :size="15" class="entry-go" />
      </router-link>
    </div>

    <p class="disclaimer">
      线上问诊不能替代线下检查。若宠物出现呼吸困难、抽搐、大出血等情况，请立即前往急诊。
    </p>
  </section>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import { consultModes } from '@/data/static'
import {
  fetchDoctors, fetchPets, fetchConsultRecords, fetchConsultOrders, fetchReports, fetchAiQuota
} from '@/api/data'
import { showToast } from '@shared/toast'

const router = useRouter()

const doctors = ref([])
const pets = ref([])
const quota = ref({ free: 3, used: 0, left: 3 })
const orders = ref([])
const myReports = ref([])
const myRecords = ref([])

// 报告与订单在页面每次进入时刷新（下单 / 结束问诊后返回此处可见）
onMounted(async () => {
  try {
    const [docs, ps, q, os, rs, recs] = await Promise.all([
      fetchDoctors(),
      fetchPets(),
      fetchAiQuota(),
      fetchConsultOrders(),
      fetchReports(),
      fetchConsultRecords()
    ])
    doctors.value = docs || []
    pets.value = ps || []
    quota.value = q || quota.value
    orders.value = os || []
    myReports.value = rs || []
    myRecords.value = recs || []
  } catch (e) {
    showToast(e?.message || '问诊中心加载失败', { type: 'error' })
  }
})

const onlineCount = computed(() => doctors.value.filter((d) => d.online).length)
const recordCount = computed(() => myRecords.value.length)
const ongoing = computed(() => orders.value.filter((o) => o.state !== 'closed'))
const latestReports = computed(() => myReports.value.slice(0, 2))

function shortDate(iso) {
  const [, m, d] = String(iso).split('-')
  return `${Number(m)}.${Number(d)}`
}

function doctorOf(o) {
  return o.doctor || doctors.value.find((d) => d.id === o.doctorId) || { name: '兽医', deptLabel: '在线问诊' }
}
function petName(id) {
  return (pets.value.find((p) => p.id === id) || {}).name || '宠物'
}
function modeLabel(id) {
  return (consultModes.find((m) => m.id === id) || {}).label || '图文问诊'
}
function stateText(o) {
  return { pending: '待接诊', replied: '医生已回复', closed: '已完成' }[o.state] || '进行中'
}
function lastMsg(o) {
  const msgs = o.messages || []
  const m = msgs.filter((x) => x.type !== 'system').slice(-1)[0]
  if (m) return m.text
  if (o.lastMessage && o.lastMessage.text) return o.lastMessage.text
  return o.summary || '医生正在查看你的病例摘要…'
}
function reportBrief(r) {
  return r.triage?.short || r.chief?.note || '查看完整分诊结论与建议'
}

/* ---------- RAG 知识库高频问题 ---------- */

const ragQuestions = [
  { text: '幼猫疫苗时间表怎么排？', pet: 'mochi' },
  { text: '驱虫和疫苗可以同一天做吗？', pet: 'mochi' },
  { text: '柯基为什么不能频繁上下楼？', pet: 'doudou' },
  { text: '换粮腹泻要怎么过渡？', pet: 'mochi' },
  { text: '狗狗夏天食欲下降正常吗？', pet: 'doudou' },
  { text: '猫频繁挠耳朵是什么原因？', pet: 'mochi' }
]

function askAI(text) {
  router.push({ path: '/consult/ai', query: { q: text } })
}

/* ---------- 科室直达 ---------- */

const deptList = [
  { key: 'internal', label: '内科', icon: 'stethoscope', tone: 'sage' },
  { key: 'derma', label: '皮肤科', icon: 'sparkle', tone: 'peach' },
  { key: 'surgery', label: '外科', icon: 'firstaid', tone: 'coral' },
  { key: 'eye', label: '眼科', icon: 'eye', tone: 'sand' },
  { key: 'nutrition', label: '营养科', icon: 'scale', tone: 'sage' },
  { key: 'er', label: '急诊', icon: 'alert', tone: 'coral' }
]
</script>

<style scoped>
.hub { padding-bottom: 8px; }

.head-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: var(--fs-xs);
  font-weight: 700;
  color: var(--color-muted);
  padding: 7px 12px;
  border-radius: 999px;
  border: 1px solid var(--hairline);
  background: var(--color-surface);
}

/* 限免条 */
.quota {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 18px;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  background: var(--color-sage-soft);
  font-size: var(--fs-xs);
  color: var(--color-ink-2);
}
.quota b {
  color: var(--color-accent-ink);
  font-weight: 800;
  padding: 0 2px;
}
.quota-note { margin-left: auto; color: var(--color-faint); }

/* 主入口 */
.entries { display: flex; flex-direction: column; gap: 10px; }

.entry {
  display: flex;
  align-items: center;
  gap: 13px;
  padding: 15px 15px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  transition: transform var(--dur-fast) var(--ease-out);
}
.entry:active { transform: scale(0.985); }
/* 唯一强调面：主推结构化预问诊 */
.entry.primary {
  background: var(--color-accent-soft);
  border-color: color-mix(in srgb, var(--color-accent) 22%, transparent);
}
.entry-ic {
  flex: 0 0 auto;
  width: 40px;
  height: 40px;
  border-radius: 13px;
  display: grid;
  place-items: center;
  background: var(--color-sage-soft);
  color: var(--color-ink);
}
.entry.primary .entry-ic {
  background: color-mix(in srgb, var(--color-accent) 16%, transparent);
  color: var(--color-accent-ink);
}
.entry-body { flex: 1; display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.entry-t {
  display: flex;
  align-items: center;
  gap: 7px;
  font-family: var(--font-display);
  font-weight: 600;
  font-size: var(--fs-sm);
}
.entry-badge {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  padding: 2px 6px;
  border-radius: 999px;
  background: var(--color-accent);
  color: #fff;
}
.entry-d {
  font-size: var(--fs-xs);
  color: var(--color-muted);
  line-height: 1.5;
  display: flex;
  align-items: center;
  gap: 5px;
}
.dot-on {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-sage);
  display: inline-block;
}
.entry-go { color: var(--color-faint); transform: rotate(180deg); flex: 0 0 auto; }

/* 区块标题 */
.sec-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 26px 0 12px;
}
.sec-t {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: var(--fs-md);
}
.sec-hint { margin-left: auto; font-size: var(--fs-xs); color: var(--color-faint); }
.sec-more {
  margin-left: auto;
  font-size: var(--fs-xs);
  font-weight: 700;
  color: var(--color-accent-ink);
}

/* 宠物档案速览 */
.pet-strip { display: flex; flex-direction: column; gap: 9px; }
.pet-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  transition: transform var(--dur-fast) var(--ease-out);
}
.pet-cell:active { transform: scale(0.985); }
.pc-body { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.pc-name { font-size: var(--fs-sm); font-weight: 700; }
.pc-meta { font-size: 11.5px; color: var(--color-muted); }
.pc-score { font-size: 11px; font-weight: 700; color: var(--color-good); }
.pc-score.watch { color: var(--color-watch); }

/* RAG 知识库 */
.rag { display: flex; flex-wrap: wrap; gap: 8px; }
.rag-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink-2);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  padding: 9px 13px;
  border-radius: var(--radius-pill);
  transition: transform var(--dur-fast) var(--ease-out), border-color var(--dur-fast);
}
.rag-chip svg { color: var(--color-faint); flex-shrink: 0; }
.rag-chip:active { transform: scale(0.95); border-color: var(--color-accent); }

/* 科室直达 */
.depts {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 9px;
}
.dept-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  padding: 14px 6px 12px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  transition: transform var(--dur-fast) var(--ease-out);
}
.dept-cell:active { transform: scale(0.96); }
.dept-ic {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: var(--color-sage-soft);
  color: var(--color-good);
}
.dept-ic.coral { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.dept-ic.peach { background: var(--color-sage-soft); color: var(--color-watch); }
.dept-ic.sand { background: var(--color-surface-2); color: var(--color-muted); }
.dept-label { font-size: 12.5px; font-weight: 700; }

/* 进行中的订单 / 最近报告 */
.order {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  margin-bottom: 9px;
}
.order-ic {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-sage-soft);
  color: var(--color-ink);
  flex-shrink: 0;
}
.order-ic.ai { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.order-body { flex: 1; display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.order-row { display: flex; align-items: center; gap: 7px; }
.order-name { font-weight: 700; font-size: var(--fs-sm); }
.order-pill {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--color-sage-soft);
  color: var(--color-ink-2);
  flex-shrink: 0;
}
.order-pill.pending { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.order-sub { font-size: 11px; color: var(--color-faint); }
.order-last {
  font-size: var(--fs-xs);
  color: var(--color-muted);
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 辅助工具 */
.minor { display: flex; flex-direction: column; gap: 9px; }
.minor-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
}
.minor-ic {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: var(--color-surface-2);
  color: var(--color-ink-2);
  flex-shrink: 0;
}
.minor-body { flex: 1; display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.minor-body b { font-size: var(--fs-sm); font-weight: 700; }
.minor-body span { font-size: var(--fs-xs); color: var(--color-muted); line-height: 1.5; }

.disclaimer {
  margin-top: 22px;
  font-size: 11px;
  line-height: 1.6;
  color: var(--color-faint);
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--color-surface-2) 60%, transparent);
}
</style>
