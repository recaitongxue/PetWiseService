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

    <!-- AI 免费额度 -->
    <div class="quota" v-reveal="{ delay: 30 }">
      <AppIcon name="sparkle" :size="13" />
      <span>今日 AI 免费问诊剩余 <b class="num">{{ quota.left }}/{{ quota.free }}</b> 次</span>
      <span class="quota-note">超出后可转真人兽医</span>
    </div>

    <!-- 三大入口：AI 分诊 → 结构化 → 真人 -->
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
          <span class="entry-d">直接描述症状，即时分诊并给出处理建议</span>
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

    <!-- 进行中的问诊单（下单后从这里回到问诊室） -->
    <template v-if="ongoing.length">
      <div class="sec-head" v-reveal="{ delay: 150 }">
        <h3 class="sec-t">进行中的问诊</h3>
        <span class="sec-hint num">{{ ongoing.length }}</span>
      </div>
      <router-link
        v-for="o in ongoing"
        :key="o.id"
        :to="`/consultation/${o.id}`"
        class="order card"
        v-reveal="{ delay: 170 }"
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

    <!-- 辅助能力 -->
    <div class="sec-head" v-reveal="{ delay: 200 }">
      <h3 class="sec-t">辅助工具</h3>
    </div>
    <div class="minor">
      <router-link to="/recognize" class="minor-row" v-reveal="{ delay: 220 }">
        <span class="minor-ic"><AppIcon name="camera" :size="18" /></span>
        <span class="minor-body">
          <b>拍照看症状</b>
          <span>识别品种、体态与皮肤状态，结果可直接带入问诊</span>
        </span>
        <AppIcon name="back" :size="15" class="entry-go" />
      </router-link>
      <router-link to="/records" class="minor-row" v-reveal="{ delay: 240 }">
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
import { computed, ref } from 'vue'
import { onMounted } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { doctors, pets, consultModes, consultRecords } from '@/data/mock'
import { aiQuota, consultOrders, reports } from '@/data/ops'

const quota = ref(aiQuota())
const orders = ref(consultOrders())
const builtin = consultRecords.length
const myReports = ref(reports())

// 报告与订单在页面每次进入时刷新（下单 / 结束问诊后返回此处可见）
onMounted(() => {
  quota.value = aiQuota()
  orders.value = consultOrders()
  myReports.value = reports()
})

const onlineCount = computed(() => doctors.filter((d) => d.online).length)
const recordCount = computed(() => builtin + myReports.value.length + orders.value.length)
const ongoing = computed(() => orders.value.filter((o) => o.state !== 'closed'))

function doctorOf(o) {
  return doctors.find((d) => d.id === o.doctorId) || { name: '兽医', deptLabel: '在线问诊' }
}
function petName(id) {
  return (pets.find((p) => p.id === id) || {}).name || '宠物'
}
function modeLabel(id) {
  return (consultModes.find((m) => m.id === id) || {}).label || '图文问诊'
}
function stateText(o) {
  return { pending: '待接诊', replied: '医生已回复', closed: '已完成' }[o.state] || '进行中'
}
function lastMsg(o) {
  const m = o.messages?.filter((x) => x.type !== 'system').slice(-1)[0]
  if (!m) return o.summary || '医生正在查看你的病例摘要…'
  return m.text
}
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

/* 额度条 */
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
.quota b { color: var(--color-accent-ink); }
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

/* 进行中的订单 */
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
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-sage-soft);
  color: var(--color-ink);
}
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
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: var(--color-surface-2);
  color: var(--color-ink-2);
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
