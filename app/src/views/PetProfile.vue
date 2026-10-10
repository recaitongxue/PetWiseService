<template>
  <section class="screen pet">
    <header class="pet-head">
      <button class="back" type="button" @click="goBack" aria-label="返回">
        <AppIcon name="back" :size="22" />
      </button>
      <span class="pet-head-title">{{ pet?.name || '宠物' }}的档案</span>
      <span class="back"></span>
    </header>

    <template v-if="pet">
      <!-- 头像 + 基本信息 -->
      <div class="pet-hero" v-reveal>
        <PetAvatar :species="pet.species" :name="pet.name" :size="84" :ring="false" />
        <div class="pet-hero-info">
          <h2 class="pet-hero-name">{{ pet.name }}</h2>
          <p class="pet-hero-breed">{{ pet.breed }} · {{ pet.gender }}</p>
          <span class="pet-hero-pill">{{ pet.tagline }}</span>
        </div>
        <span class="pet-hero-ring">
          <HealthRing :value="pet.healthScore" label="健康分" :size="92" />
        </span>
      </div>

      <!-- 数据块 -->
      <div class="pet-stats" v-reveal="{ delay: 80 }">
        <div class="pstat">
          <b class="num">{{ pet.weight }}</b><span>kg 体重</span>
        </div>
        <div class="pstat">
          <b class="num">{{ pet.age }}</b><span>岁 年龄</span>
        </div>
        <div class="pstat">
          <b>{{ pet.nextVaccine.slice(5) }}</b><span>下次疫苗</span>
        </div>
      </div>

      <!-- 快捷 -->
      <div class="pet-actions" v-reveal="{ delay: 120 }">
        <router-link to="/consult" class="pact ink">
          <AppIcon name="stethoscope" :size="20" /> 智能问诊
        </router-link>
        <router-link to="/recognize" class="pact accent">
          <AppIcon name="camera" :size="20" /> 拍照识别
        </router-link>
      </div>

      <!-- 体重趋势 -->
      <section class="block" v-reveal="{ delay: 160 }">
        <div class="block-head">
          <h3 class="block-title">体重趋势</h3>
          <span class="block-hint">近 6 月</span>
        </div>
        <div class="weight-chart">
          <div v-for="w in weightHistory" :key="w.m" class="wc-col">
            <span class="wc-val num">{{ w.w }}</span>
            <div class="wc-bar-wrap">
              <span class="wc-bar" :style="{ height: barH(w.w) }"></span>
            </div>
            <span class="wc-month num">{{ w.m }}</span>
          </div>
        </div>
        <p class="wc-foot">
          当前 {{ pet.weight }}kg ·
          <span :class="trendState">{{ trendText }}</span>
        </p>
      </section>

      <!-- 免疫与护理日程 -->
      <section class="block" v-reveal="{ delay: 200 }">
        <div class="block-head">
          <h3 class="block-title">免疫与护理日程</h3>
          <span class="block-hint">近期</span>
        </div>
        <ul class="timeline">
          <li v-for="s in schedule" :key="s.date" class="tl-item">
            <span class="tl-dot" :class="s.state"></span>
            <div class="tl-body">
              <div class="tl-row">
                <span class="tl-title">{{ s.title }}</span>
                <span class="tl-date num">{{ s.date.slice(5) }}</span>
              </div>
              <span class="tl-type" :class="s.type">{{ typeLabel(s.type) }}</span>
            </div>
          </li>
        </ul>
      </section>

      <!-- 健康记录 -->
      <section class="block" v-reveal="{ delay: 240 }">
        <div class="block-head">
          <h3 class="block-title">健康记录</h3>
          <span class="block-hint">日志</span>
        </div>
        <ul class="timeline">
          <li v-for="r in records" :key="r.date" class="tl-item">
            <span class="tl-dot" :class="r.state"></span>
            <div class="tl-body">
              <div class="tl-row">
                <span class="tl-title">{{ r.title }}</span>
                <span class="tl-date num">{{ r.date }}</span>
              </div>
              <p class="tl-desc">{{ r.desc }}</p>
            </div>
          </li>
        </ul>
      </section>
    </template>

    <p v-else class="empty">未找到该宠物档案。</p>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import HealthRing from '@/components/HealthRing.vue'
import { pets, petWeightHistory, petSchedule } from '@/data/mock'

const route = useRoute()
const router = useRouter()
const pet = computed(() => pets.find((p) => p.id === route.params.id))

function goBack() {
  router.back()
}

const weightHistory = computed(() => petWeightHistory[pet.value?.id] || [])
const schedule = computed(() => petSchedule[pet.value?.id] || [])

const maxW = computed(() => Math.max(...weightHistory.value.map((w) => w.w), 1))
function barH(w) {
  return Math.round((w / maxW.value) * 100) + '%'
}
const trendText = computed(() => {
  const list = weightHistory.value
  if (list.length < 2) return '数据不足'
  const diff = list[list.length - 1].w - list[list.length - 2].w
  if (diff > 0.05) return '较上月略增'
  if (diff < -0.05) return '较上月略减'
  return '保持稳定'
})
const trendState = computed(() =>
  trendText.value.includes('增') || trendText.value.includes('减') ? 'watch' : 'good'
)

function typeLabel(t) {
  return { vaccine: '疫苗', deworm: '驱虫', check: '体检', weight: '体重' }[t] || '护理'
}

const records = computed(() => [
  {
    date: pet.value?.nextVaccine || '2026-11-02',
    title: '年度疫苗提醒',
    desc: '距离下次免疫还有一段时间，建议提前一周预约。',
    state: 'watch'
  },
  {
    date: '2026-09-12',
    title: '体态评估',
    desc: pet.value?.species === 'dog' ? '体重略偏高，建议增加日常运动量。' : '体态标准，被毛光亮。',
    state: 'good'
  },
  {
    date: '2026-08-03',
    title: '驱虫完成',
    desc: '体内外驱虫已按计划完成，下次驱虫 3 个月后。',
    state: 'good'
  }
])
</script>

<style scoped>
.pet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 4px 12px;
}
.back {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--color-ink);
}
.pet-head-title { font-family: var(--font-display); font-weight: 700; font-size: var(--fs-lg); }

.pet-hero {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  background: linear-gradient(150deg, var(--color-sage-soft), #eef3e8);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-1);
}
.pet-hero-info { flex: 1; }
.pet-hero-name { font-family: var(--font-display); font-weight: 700; font-size: var(--fs-xl); line-height: 1; }
.pet-hero-breed { font-size: 14px; color: var(--color-ink-2); margin-top: 4px; }
.pet-hero-pill {
  display: inline-block;
  margin-top: 10px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-sage);
  background: rgba(255, 255, 255, 0.6);
  padding: 4px 12px;
  border-radius: var(--radius-pill);
}
.pet-hero-ring { flex-shrink: 0; }

.pet-stats {
  display: flex;
  gap: 10px;
  margin: 16px 0;
}
.pstat {
  flex: 1;
  text-align: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 14px 0;
}
.pstat b { display: block; font-family: var(--font-display); font-size: var(--fs-lg); line-height: 1; }
.pstat span { font-size: 12px; color: var(--color-muted); }

.pet-actions { display: flex; gap: 12px; }
.pact {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  border-radius: var(--radius-pill);
  font-weight: 700;
  font-size: 15px;
  color: #fff;
  transition: transform var(--dur-fast) var(--ease-out);
}
.pact:active { transform: scale(0.97); }
.pact.ink { background: var(--color-ink); }
.pact.accent { background: linear-gradient(140deg, var(--color-accent), var(--color-accent-ink)); }

.block { margin-top: 28px; }
.block-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14px;
}
.block-title { font-family: var(--font-display); font-weight: 700; font-size: var(--fs-lg); }
.block-hint { font-size: 12px; font-weight: 700; letter-spacing: 0.08em; color: var(--color-accent-ink); text-transform: uppercase; }

/* 体重趋势 */
.weight-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 6px;
  height: 150px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 16px 12px 12px;
}
.wc-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  height: 100%;
  justify-content: flex-end;
}
.wc-val { font-size: 11px; color: var(--color-muted); font-weight: 700; }
.wc-bar-wrap { flex: 1; width: 100%; display: flex; align-items: flex-end; justify-content: center; }
.wc-bar {
  width: 56%;
  max-width: 18px;
  border-radius: 8px 8px 4px 4px;
  background: linear-gradient(180deg, var(--color-sage), #6c8a66);
  transition: height 0.9s var(--ease-out);
}
.wc-month { font-size: 11px; color: var(--color-muted); }
.wc-foot {
  font-size: 13px;
  color: var(--color-ink-2);
  margin-top: 10px;
}
.wc-foot .good { color: var(--color-good); font-weight: 700; }
.wc-foot .watch { color: var(--color-watch); font-weight: 700; }

/* 时间线 */
.timeline { position: relative; padding-left: 8px; }
.tl-item {
  position: relative;
  display: flex;
  gap: 16px;
  padding-bottom: 20px;
}
.tl-item::before {
  content: '';
  position: absolute;
  left: 16px;
  top: 22px;
  bottom: -2px;
  width: 2px;
  background: var(--color-border);
}
.tl-item:last-child::before { display: none; }
.tl-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  margin-top: 4px;
  flex-shrink: 0;
  border: 3px solid var(--color-bg);
  background: var(--color-sage);
  z-index: 1;
}
.tl-dot.good { background: var(--color-good); }
.tl-dot.watch { background: var(--color-watch); }
.tl-body { flex: 1; }
.tl-row { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
.tl-title { font-weight: 700; font-size: 15px; }
.tl-date { font-size: 12px; color: var(--color-muted); }
.tl-desc { font-size: 13px; color: var(--color-ink-2); margin-top: 3px; line-height: 1.55; }
.tl-type {
  display: inline-block;
  margin-top: 6px;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  color: var(--color-sage);
  background: var(--color-sage-soft);
}
.tl-type.vaccine { color: var(--color-accent-ink); background: var(--color-accent-soft); }
.tl-type.deworm { color: var(--color-good); background: var(--color-sage-soft); }
.tl-type.weight { color: var(--color-watch); background: #fbe7d2; }

.empty { text-align: center; color: var(--color-muted); margin-top: 60px; }
</style>
