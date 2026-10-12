<template>
  <section class="screen" v-if="r">
    <header class="r-head">
      <button class="back" type="button" @click="goBack" aria-label="返回">
        <AppIcon name="back" :size="22" />
      </button>
      <span class="r-title">问诊报告</span>
      <button class="share" type="button" @click="exportReport" aria-label="导出报告">
        <AppIcon name="share" :size="19" />
      </button>
    </header>

    <!-- 报告封面 -->
    <article class="cover" v-reveal>
      <div class="cover-top">
        <span class="cover-kind" :class="r.type">
          <AppIcon :name="r.type === 'ai' ? 'sparkle' : 'stethoscope'" :size="12" />
          {{ r.type === 'ai' ? 'AI 预问诊报告' : '真人医生问诊报告' }}
        </span>
        <span class="cover-date num">{{ r.date }}</span>
      </div>
      <h2 class="cover-title">{{ r.title }}</h2>
      <p class="cover-sub">
        {{ r.petName }}<span v-if="r.chief?.partLabel"> · {{ r.chief.partLabel }}</span>
        <span v-if="r.doctor"> · {{ r.doctor.name }}{{ r.doctor.title }}</span>
      </p>
    </article>

    <!-- 主诉（结构化） -->
    <section class="blk" v-reveal="{ delay: 40 }">
      <h3 class="blk-h">主诉</h3>
      <div class="chief">
        <div v-if="r.chief?.symptomLabels?.length" class="chief-row">
          <span class="chief-k">表现</span>
          <div class="chief-v">
            <span v-for="s in r.chief.symptomLabels" :key="s" class="cv-chip">{{ s }}</span>
          </div>
        </div>
        <div v-if="r.chief?.durationLabel" class="chief-row">
          <span class="chief-k">持续</span>
          <span class="chief-v">{{ r.chief.durationLabel }}</span>
        </div>
        <div v-if="r.chief?.severityLabel" class="chief-row">
          <span class="chief-k">状态</span>
          <span class="chief-v">{{ r.chief.severityLabel }}</span>
        </div>
        <div v-if="r.chief?.accompanyLabels?.length" class="chief-row">
          <span class="chief-k">伴随</span>
          <div class="chief-v">
            <span v-for="a in r.chief.accompanyLabels" :key="a" class="cv-chip soft">{{ a }}</span>
          </div>
        </div>
        <div v-if="r.chief?.note" class="chief-row col">
          <span class="chief-k">补充</span>
          <span class="chief-v">{{ r.chief.note }}</span>
        </div>
        <div v-if="r.chief?.photos" class="chief-row">
          <span class="chief-k">附件</span>
          <span class="chief-v">患处照片 {{ r.chief.photos }} 张</span>
        </div>
      </div>
    </section>

    <!-- 分诊结论 -->
    <section class="blk" v-reveal="{ delay: 60 }">
      <h3 class="blk-h">分诊结论</h3>
      <TriageCard
        :level="r.triage.level"
        :label="r.triage.label"
        :short="r.triage.short"
        :advice="r.triage.advice"
        :causes="r.triage.causes || []"
        :actions="r.triage.actions || []"
        :confidence="r.triage.level === 'emergency' ? '高' : '中'"
        @escalate="toDoctors"
      />

      <!-- 评分依据：让分级可解释，而不是黑盒结论 -->
      <div class="score">
        <header class="score-h" @click="scoreOpen = !scoreOpen">
          <span class="score-t">评分依据</span>
          <span class="score-n num">{{ r.triage.score }} 分</span>
          <AppIcon name="back" :size="14" class="score-arrow" :class="{ up: scoreOpen }" />
        </header>
        <ul v-if="scoreOpen" class="factors">
          <li v-for="(f, i) in r.triage.factors || []" :key="i" :class="{ danger: f.danger }">
            <span class="f-text">{{ f.text }}</span>
            <span v-if="f.danger" class="f-w danger">急诊</span>
            <span v-else class="f-w num">+{{ f.w }}</span>
          </li>
          <li v-if="!(r.triage.factors || []).length" class="f-empty">
            未记录到加分项，按最低风险处理
          </li>
        </ul>
      </div>
    </section>

    <!-- 医生建议（真人问诊） -->
    <section class="blk" v-if="r.doctorAdvice?.length" v-reveal="{ delay: 80 }">
      <h3 class="blk-h">医生建议</h3>
      <ul class="advice">
        <li v-for="(a, i) in r.doctorAdvice" :key="i">
          <span class="adv-n num">{{ i + 1 }}</span>
          <span>{{ a }}</span>
        </li>
      </ul>
    </section>

    <!-- 处方 -->
    <section class="blk" v-if="r.rx?.drugs?.length" v-reveal="{ delay: 90 }">
      <h3 class="blk-h">用药方案</h3>
      <article class="rx">
        <ul class="rx-list">
          <li v-for="d in r.rx.drugs" :key="d.name">
            <div class="rx-d-top">
              <span class="rx-name">{{ d.name }}</span>
              <span class="rx-dose">{{ d.dose }}</span>
            </div>
            <p class="rx-use">{{ d.use }}</p>
          </li>
        </ul>
        <p class="rx-note" v-if="r.rx.note">{{ r.rx.note }}</p>
      </article>
    </section>

    <!-- 复查计划 -->
    <section class="blk" v-reveal="{ delay: 100 }">
      <h3 class="blk-h">复查计划</h3>
      <p class="follow">{{ r.triage.followUp }}</p>
    </section>

    <p class="disclaim">
      本报告由 AI 结合结构化问诊生成<span v-if="r.type === 'human'">，并经由执业兽医确认</span>，
      仅供参考，不能替代执业兽医的当面诊断与处方。紧急情况请立即就医。
    </p>

    <!-- 底部闭环操作 -->
    <div class="bar">
      <button class="bar-ic" type="button" :disabled="r.archived" @click="archive">
        <AppIcon :name="r.archived ? 'check' : 'notes'" :size="18" />
        <span>{{ r.archived ? '已存档' : '存入档案' }}</span>
      </button>
      <button class="bar-ic" type="button" :disabled="r.reminded" @click="remind">
        <AppIcon :name="r.reminded ? 'check' : 'calendar'" :size="18" />
        <span>{{ r.reminded ? '已设提醒' : '用药提醒' }}</span>
      </button>
      <button class="bar-main" type="button" @click="toDoctors">转真人医生</button>
    </div>
  </section>

  <p v-else class="empty">报告不存在或已被清除。</p>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import TriageCard from '@/components/TriageCard.vue'
import { reportById, archiveReport, remindFromReport } from '@/data/ops'
import { showToast } from '@/composables/toast'

const route = useRoute()
const router = useRouter()
function goBack() {
  router.push('/records')
}

const r = ref(reportById(route.params.id))
const scoreOpen = ref(true)

const reload = () => (r.value = reportById(route.params.id))

function archive() {
  if (archiveReport(r.value, r.value.petId)) {
    reload()
    showToast('已写入健康档案，可在宠物档案页查看', { type: 'success' })
  }
}

function remind() {
  const n = remindFromReport(r.value, r.value.petId)
  if (n) {
    reload()
    showToast(`已生成 ${n} 条提醒，可在日程页查看`, { type: 'success' })
  }
}

function exportReport() {
  showToast('演示环境暂不支持导出图片，可截图分享给线下医生', { type: 'info' })
}

function toDoctors() {
  router.push({ path: '/doctors', query: { dept: deptOf() } })
}

// 报告 → 医生科室推荐（与问诊页共用同一套映射意图）
function deptOf() {
  const part = r.value?.chief?.partLabel || ''
  if (r.value?.triage?.level === 'emergency') return 'er'
  if (part.includes('皮肤')) return 'derma'
  if (part.includes('四肢')) return 'surgery'
  if (part.includes('头颈')) return 'eye'
  return 'internal'
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
.share { width: 40px; height: 40px; display: grid; place-items: center; border-radius: 50%; color: var(--color-muted); }

/* ---------- 封面 ---------- */
.cover {
  padding: 16px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
}
.cover-top { display: flex; align-items: center; justify-content: space-between; }
.cover-kind {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  font-weight: 700;
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  padding: 5px 10px;
  border-radius: var(--radius-pill);
}
.cover-kind.human { color: var(--color-good); background: var(--color-sage-soft); }
.cover-date { font-size: 12px; color: var(--color-faint); }
.cover-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 20px;
  letter-spacing: -0.02em;
  line-height: 1.35;
  margin-top: 11px;
}
.cover-sub { font-size: 12.5px; color: var(--color-muted); margin-top: 5px; }

/* ---------- 区块 ---------- */
.blk { margin-top: 22px; }
.blk-h {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 16px;
  letter-spacing: -0.01em;
  margin-bottom: 11px;
}

.chief {
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  padding: 13px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.chief-row { display: flex; align-items: flex-start; gap: 10px; }
.chief-row.col { flex-direction: column; gap: 5px; }
.chief-k {
  flex-shrink: 0;
  width: 32px;
  font-size: 11px;
  font-weight: 700;
  color: var(--color-faint);
  padding-top: 3px;
}
.chief-v { flex: 1; display: flex; flex-wrap: wrap; gap: 6px; font-size: 13.5px; color: var(--color-ink-2); line-height: 1.6; }
.cv-chip {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  padding: 4px 10px;
  border-radius: var(--radius-pill);
}
.cv-chip.soft { color: var(--color-ink-2); background: var(--color-surface-2); }

/* ---------- 评分依据 ---------- */
.score {
  margin-top: 10px;
  border-radius: var(--radius-md);
  border: 1px solid var(--hairline);
  background: var(--color-surface);
  overflow: hidden;
}
.score-h {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
}
.score-t { font-size: 13px; font-weight: 700; }
.score-n { margin-left: auto; font-size: 13px; font-weight: 700; color: var(--color-accent-ink); }
.score-arrow { color: var(--color-faint); transform: rotate(-90deg); transition: transform var(--dur-fast); }
.score-arrow.up { transform: rotate(90deg); }
.factors { list-style: none; padding: 0 14px 12px; display: flex; flex-direction: column; gap: 8px; }
.factors li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 13px;
  color: var(--color-ink-2);
}
.f-text { flex: 1; }
.f-w {
  flex-shrink: 0;
  font-size: 11.5px;
  font-weight: 700;
  color: var(--color-watch);
  background: color-mix(in srgb, var(--color-watch) 14%, white);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}
.f-w.danger { color: var(--color-alert); background: color-mix(in srgb, var(--color-alert) 12%, white); }
.factors li.danger .f-text { color: var(--color-alert); font-weight: 600; }
.f-empty { color: var(--color-faint); }

/* ---------- 建议 / 处方 ---------- */
.advice { list-style: none; display: flex; flex-direction: column; gap: 10px; }
.advice li {
  display: flex;
  gap: 10px;
  font-size: 13.5px;
  line-height: 1.65;
  color: var(--color-ink-2);
}
.adv-n {
  flex-shrink: 0;
  width: 19px;
  height: 19px;
  margin-top: 2px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--color-good);
  background: var(--color-sage-soft);
}

.rx {
  border-radius: var(--radius-lg);
  border: 1px solid color-mix(in srgb, var(--color-good) 30%, transparent);
  background: var(--color-surface);
  padding: 14px;
}
.rx-list { list-style: none; display: flex; flex-direction: column; gap: 10px; }
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

.follow {
  font-size: 13.5px;
  line-height: 1.7;
  color: var(--color-ink-2);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  border-radius: var(--radius-md);
  padding: 13px 14px;
}

.disclaim {
  margin: 22px 0 8px;
  font-size: 11.5px;
  line-height: 1.6;
  color: var(--color-faint);
  text-align: center;
}

/* ---------- 底部闭环 ---------- */
.bar {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(78px + env(safe-area-inset-bottom, 0px));
  width: min(var(--shell-max), 100%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 14px;
  background: color-mix(in srgb, var(--color-surface) 94%, transparent);
  backdrop-filter: blur(14px);
  border-top: 1px solid var(--color-border);
}
.bar-ic {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  font-size: 10.5px;
  font-weight: 700;
  color: var(--color-muted);
  flex-shrink: 0;
  padding: 3px 8px;
}
.bar-ic:disabled { color: var(--color-good); }
.bar-main {
  margin-left: auto;
  font-size: 14.5px;
  font-weight: 700;
  color: #fff;
  background: var(--color-accent);
  padding: 13px 20px;
  border-radius: var(--radius-pill);
  transition: transform var(--dur-fast) var(--ease-out);
}
.bar-main:active { transform: scale(0.97); }

.empty { text-align: center; color: var(--color-muted); margin-top: 60px; }
</style>
