<template>
  <section class="screen">
    <header class="r-head">
      <button class="back" type="button" @click="goBack" aria-label="返回">
        <AppIcon name="back" :size="22" />
      </button>
      <span class="r-title">找医生</span>
      <span class="back"></span>
    </header>

    <!-- AI 病例摘要：从智能问诊转诊过来时带上，医生接诊前就能看到 -->
    <transition name="ctx">
      <article v-if="summary" class="case-card">
        <header class="case-head">
          <span class="case-ic"><AppIcon name="sparkle" :size="15" /></span>
          <div>
            <p class="case-t">AI 已为 {{ summary.petName }} 生成初步判断</p>
            <p class="case-s" v-if="summary.triage">
              {{ summary.triage.label }} · 医生接诊时可直接看到
            </p>
            <p class="case-s" v-else>已完成档案整理，医生接诊时可直接看到</p>
          </div>
          <button class="case-toggle" type="button" @click="caseOpen = !caseOpen">
            {{ caseOpen ? '收起' : '查看' }}
          </button>
        </header>
        <div v-if="caseOpen" class="case-body">
          <dl class="case-dl">
            <div><dt>宠物</dt><dd>{{ summary.petName }} · {{ summary.breed }} · {{ summary.age }}岁 · {{ summary.weight }}kg</dd></div>
            <div v-if="summary.symptoms.length"><dt>症状标签</dt><dd>{{ summary.symptoms.join('、') }}</dd></div>
            <div v-if="summary.complaints.length"><dt>主诉</dt><dd>{{ summary.complaints.join('；') }}</dd></div>
            <div v-if="summary.triage"><dt>AI 判断</dt><dd>{{ summary.triage.label }} — {{ summary.triage.advice }}</dd></div>
          </dl>
        </div>
      </article>
    </transition>

    <!-- 科室筛选 -->
    <div class="depts">
      <button
        v-for="d in departments"
        :key="d.id"
        class="dept-chip"
        :class="{ on: dept === d.id }"
        type="button"
        @click="dept = d.id"
      >
        <AppIcon :name="d.icon" :size="13" />
        {{ d.label }}
      </button>
    </div>

    <div class="tool-row">
      <span class="count">{{ list.length }} 位医生</span>
      <button class="online-only" :class="{ on: onlyOnline }" type="button" @click="onlyOnline = !onlyOnline">
        <span class="dot" :class="{ live: onlyOnline }"></span>
        仅看在线
      </button>
    </div>

    <!-- 医生列表 -->
    <div class="docs">
      <router-link
        v-for="d in list"
        :key="d.id"
        :to="`/doctor/${d.id}`"
        class="doc"
        v-reveal="{ delay: 40 }"
      >
        <span class="doc-av" :class="d.dept">{{ d.name.slice(0, 1) }}</span>
        <div class="doc-body">
          <div class="doc-top">
            <span class="doc-name">{{ d.name }}</span>
            <span class="doc-title">{{ d.title }}</span>
            <span class="doc-state" :class="{ on: d.online }">
              <span class="s-dot"></span>{{ d.online ? '在线' : '离线' }}
            </span>
          </div>
          <p class="doc-hosp">{{ d.hospital }}</p>
          <div class="doc-tags">
            <span v-for="t in d.tags" :key="t" class="doc-tag">{{ t }}</span>
          </div>
          <div class="doc-foot">
            <span class="doc-rate"><AppIcon name="star" :size="12" /> {{ d.rating }}</span>
            <span class="doc-num num">{{ d.consults }}+ 接诊</span>
            <span class="doc-eta">{{ d.online ? `${d.responseMin} 分钟响应` : d.slot }}</span>
            <span class="doc-price">¥{{ minPrice }} 起</span>
          </div>
        </div>
      </router-link>
    </div>

    <p v-if="!list.length" class="empty">该科室暂无在线医生，试试切换科室或取消「仅看在线」。</p>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import { departments, consultModes } from '@/data/static'
import { fetchDoctors } from '@/api/data'
import { showToast } from '@shared/toast'

const route = useRoute()
const router = useRouter()
function goBack() {
  router.back()
}

const dept = ref(route.query.dept || 'all')
const onlyOnline = ref(false)
const caseOpen = ref(false)
const summary = ref(null)
const doctors = ref([])

async function loadDoctors() {
  try {
    doctors.value = (await fetchDoctors({ department: dept.value })) || []
  } catch (e) {
    doctors.value = []
    showToast(e?.message || '医生列表加载失败', { type: 'error' })
  }
}

// 读取问诊页写入的病例摘要（一次性传递，读完即保留在内存）
onMounted(async () => {
  try {
    const raw = sessionStorage.getItem('petwise_case_summary')
    if (raw) summary.value = JSON.parse(raw)
  } catch {
    summary.value = null
  }
  await loadDoctors()
})

// 切换科室时向后端重新拉取该科室医生
watch(dept, loadDoctors)

const minPrice = Math.min(...consultModes.map((m) => m.price))

const list = computed(() => {
  let out = doctors.value
  if (dept.value !== 'all') out = out.filter((d) => d.dept === dept.value)
  if (onlyOnline.value) out = out.filter((d) => d.online)
  // 在线优先，其次评分高、响应快
  return [...out].sort((a, b) => {
    if (a.online !== b.online) return a.online ? -1 : 1
    if (b.rating !== a.rating) return b.rating - a.rating
    return a.responseMin - b.responseMin
  })
})
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

/* ---------- AI 病例摘要卡 ---------- */
.case-card {
  border-radius: var(--radius-lg);
  border: 1px solid color-mix(in srgb, var(--color-accent) 30%, transparent);
  background: var(--color-accent-soft);
  padding: 13px 14px;
  margin-bottom: 16px;
}
.case-head { display: flex; align-items: flex-start; gap: 10px; }
.case-ic {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  background: var(--color-surface);
  color: var(--color-accent-ink);
  flex-shrink: 0;
}
.case-t { font-size: 14px; font-weight: 700; color: var(--color-accent-ink); }
.case-s { font-size: 12px; color: var(--color-ink-2); margin-top: 2px; }
.case-toggle {
  margin-left: auto;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-accent-ink);
  text-decoration: underline;
  text-underline-offset: 2px;
}
.case-body { margin-top: 12px; padding-top: 11px; border-top: 1px solid color-mix(in srgb, var(--color-accent) 20%, transparent); }
.case-dl { display: flex; flex-direction: column; gap: 8px; margin: 0; }
.case-dl > div { display: flex; gap: 10px; }
.case-dl dt {
  flex-shrink: 0;
  width: 56px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-faint);
}
.case-dl dd { margin: 0; font-size: 13px; line-height: 1.55; color: var(--color-ink-2); }

/* ---------- 科室 ---------- */
.depts {
  display: flex;
  gap: 7px;
  overflow-x: auto;
  padding-bottom: 4px;
  margin-bottom: 12px;
}
.dept-chip {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-muted);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  padding: 7px 13px;
  border-radius: var(--radius-pill);
  transition: color var(--dur-fast), border-color var(--dur-fast), background var(--dur-fast);
}
.dept-chip.on {
  color: var(--color-ink);
  border-color: var(--hairline-strong);
  background: var(--color-surface-2);
  font-weight: 700;
}

.tool-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.count { font-size: 12px; color: var(--color-faint); }
.online-only {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-muted);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  padding: 6px 12px;
  border-radius: var(--radius-pill);
}
.online-only.on { color: var(--color-good); border-color: color-mix(in srgb, var(--color-good) 35%, transparent); }
.dot { width: 7px; height: 7px; border-radius: 50%; background: var(--color-faint); }
.dot.live { background: var(--color-good); }

/* ---------- 医生卡 ---------- */
.docs { display: flex; flex-direction: column; gap: 10px; }
.doc {
  display: flex;
  gap: 12px;
  padding: 14px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
  transition: transform var(--dur-fast) var(--ease-out);
}
.doc:active { transform: scale(0.988); }
.doc-av {
  width: 46px;
  height: 46px;
  border-radius: 32%;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 20px;
  color: var(--color-ink);
  flex-shrink: 0;
  background: var(--grad-sand);
}
.doc-av.internal { background: var(--grad-sage); }
.doc-av.er { background: var(--grad-peach); }
.doc-av.derma { background: var(--grad-sage); }
.doc-av.exotic { background: var(--grad-sand); }
.doc-av.nutrition { background: var(--grad-peach); }

.doc-body { flex: 1; min-width: 0; }
.doc-top { display: flex; align-items: center; gap: 7px; }
.doc-name { font-weight: 700; font-size: 16px; letter-spacing: -0.01em; }
.doc-title { font-size: 12px; color: var(--color-muted); font-weight: 600; }
.doc-state {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  color: var(--color-faint);
  flex-shrink: 0;
}
.doc-state.on { color: var(--color-good); }
.s-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

.doc-hosp {
  font-size: 12px;
  color: var(--color-muted);
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.doc-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 9px; }
.doc-tag {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--color-ink-2);
  background: var(--color-surface-2);
  border: 1px solid var(--hairline);
  padding: 3px 9px;
  border-radius: var(--radius-pill);
}
.doc-foot {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 11px;
  padding-top: 9px;
  border-top: 1px solid var(--hairline);
  font-size: 11.5px;
  color: var(--color-muted);
  flex-wrap: wrap;
}
.doc-rate {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-weight: 700;
  color: var(--color-watch);
}
.doc-eta { color: var(--color-faint); }
.doc-price {
  margin-left: auto;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-accent-ink);
}

.empty { text-align: center; color: var(--color-muted); font-size: 14px; margin-top: 40px; }

.ctx-enter-active, .ctx-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.ctx-enter-from, .ctx-leave-to { opacity: 0; }
</style>
