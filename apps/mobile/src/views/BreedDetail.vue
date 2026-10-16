<template>
  <div v-if="breed" class="breed-page">
    <header class="bd-head">
      <RouterLink to="/recognize" class="bd-back" aria-label="返回">
        <AppIcon name="back" />
      </RouterLink>
      <span class="bd-kicker num">Breed Library · 品种百科</span>
    </header>

    <section class="bd-hero">
      <PetIllustration :species="breed.species" class="bd-illu" />
      <h1 class="bd-name">{{ breed.name }}</h1>
      <p class="bd-sci num">{{ breed.sci }}</p>
      <div class="bd-tags">
        <span class="bd-tag">{{ breed.species === 'cat' ? '猫科' : '犬科' }}</span>
        <span class="bd-tag">原产地 · {{ breed.origin }}</span>
      </div>
    </section>

    <section class="bd-facts">
      <div class="fact">
        <span class="fact-label">体重区间</span>
        <span class="fact-value num">{{ breed.weight }}</span>
      </div>
      <div class="fact">
        <span class="fact-label">预期寿命</span>
        <span class="fact-value num">{{ breed.life }}</span>
      </div>
    </section>

    <section class="bd-sec">
      <span class="sec-idx num">01</span>
      <h2 class="sec-title">性格特质</h2>
      <div class="temp-chips">
        <span v-for="t in breed.temperament" :key="t" class="temp-chip">{{ t }}</span>
      </div>
    </section>

    <section class="bd-sec">
      <span class="sec-idx num">02</span>
      <h2 class="sec-title">易患问题</h2>
      <ul class="issue-list">
        <li v-for="it in breed.issues" :key="it" class="issue-item">
          <AppIcon name="paw" class="issue-dot" />
          <span>{{ it }}</span>
        </li>
      </ul>
    </section>

    <section class="bd-sec">
      <span class="sec-idx num">03</span>
      <h2 class="sec-title">护理要点</h2>
      <p class="care-text">{{ breed.care }}</p>
    </section>

    <section class="bd-sec">
      <span class="sec-idx num">04</span>
      <h2 class="sec-title">喂食建议</h2>
      <ul class="feed-list">
        <li v-for="(f, i) in breed.feeding" :key="i" class="feed-item">
          <span class="feed-idx num">{{ String(i + 1).padStart(2, '0') }}</span>
          <span>{{ f }}</span>
        </li>
      </ul>
    </section>

    <!-- AI 快捷提问：携带具体问题进入问诊 -->
    <section class="bd-ai">
      <div class="ai-head"><AppIcon name="sparkle" :size="15" /> 问问 AI 关于{{ breed.name }}</div>
      <button v-for="(q, i) in breed.aiPrompts" :key="i" class="ai-q" type="button" @click="askAi(q)">
        <span>{{ q }}</span>
        <AppIcon name="back" :size="14" class="ai-arrow" />
      </button>
    </section>

    <div class="bd-actions">
      <RouterLink
        :to="{ path: '/consult/ai', query: { pet: breed.name, note: `${breed.name}饲养与健康管理咨询` } }"
        class="bd-cta"
      >就这个品种问一问</RouterLink>
      <RouterLink to="/recognize" class="bd-cta ghost">拍一张识别看看</RouterLink>
    </div>
  </div>

  <div v-else class="breed-page">
    <p class="bd-missing">没有找到这个品种，<RouterLink to="/recognize" class="link">去识别看看</RouterLink></p>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import PetIllustration from '@/components/PetIllustration.vue'
import { fetchBreed, fetchBreedLibrary } from '@/api/data'

const route = useRoute()
const router = useRouter()
const breed = ref(null)

// 路由参数可能是后端数字 id，也可能是旧演示的 slug / 品种名，两种都兼容
async function load(id) {
  breed.value = null
  try {
    if (/^\d+$/.test(String(id))) {
      breed.value = await fetchBreed(Number(id))
      return
    }
    const list = await fetchBreedLibrary()
    breed.value =
      list.find((b) => String(b.id) === String(id)) ||
      list.find((b) => b.name === id) ||
      null
  } catch {
    breed.value = null
  }
}

onMounted(() => load(route.params.id))
watch(() => route.params.id, load)

// 带具体问题进入 AI 问诊（RAG 检索的知识库上下文由后端补充）
function askAi(question) {
  router.push({ path: '/consult/ai', query: { pet: breed.value?.name || '', note: question } })
}
</script>

<style scoped>
.breed-page {
  max-width: 560px;
  margin: 0 auto;
  padding: 24px 20px 48px;
}
.bd-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}
.bd-back {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: var(--color-paper, #f2ebdc);
  box-shadow: var(--shadow-soft);
  color: var(--color-ink, #1b2a22);
}
.bd-kicker {
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-ink-3, #7a776c);
}
.bd-hero {
  text-align: center;
  padding: 8px 0 4px;
}
.bd-illu {
  width: 132px;
  margin-bottom: 10px;
}
.bd-name {
  font-family: var(--font-display, 'Fraunces', 'Noto Serif SC', serif);
  font-size: 34px;
  font-weight: 600;
  line-height: 1.15;
  color: var(--color-ink, #1b2a22);
}
.bd-sci {
  margin-top: 4px;
  font-style: italic;
  font-size: 14px;
  color: var(--color-ink-3, #7a776c);
}
.bd-tags {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 14px;
}
.bd-tag {
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--color-paper, #f2ebdc);
  color: var(--color-ink-2, #4a5248);
}
.bd-facts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 26px 0 8px;
}
.fact {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 18px;
  border-radius: 20px;
  background: var(--color-paper, #f2ebdc);
}
.fact-label {
  font-size: 12px;
  color: var(--color-ink-3, #7a776c);
}
.fact-value {
  font-family: var(--font-display, 'Fraunces', 'Noto Serif SC', serif);
  font-size: 21px;
  font-weight: 600;
  color: var(--color-ink, #1b2a22);
}
.bd-sec {
  position: relative;
  padding: 26px 0 6px;
}
.sec-idx {
  position: absolute;
  top: 22px;
  right: 0;
  font-family: var(--font-display, 'Fraunces', serif);
  font-size: 15px;
  color: var(--color-ink-4, #b6b0a0);
  letter-spacing: 0.08em;
}
.sec-title {
  font-family: var(--font-display, 'Fraunces', 'Noto Serif SC', serif);
  font-size: 19px;
  font-weight: 600;
  margin-bottom: 14px;
  color: var(--color-ink, #1b2a22);
}
.temp-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.temp-chip {
  font-size: 13px;
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--grad-sage, #e4e9df);
  color: var(--color-ink, #1b2a22);
}
.temp-chip:nth-child(2) { background: var(--grad-peach, #f6e3d3); }
.temp-chip:nth-child(3) { background: var(--grad-sand, #efe6d2); }
.issue-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.issue-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: var(--color-ink-2, #4a5248);
}
.issue-dot {
  width: 14px;
  height: 14px;
  color: var(--color-accent, #e8552b);
  flex-shrink: 0;
}
.care-text {
  font-size: 14.5px;
  line-height: 1.85;
  color: var(--color-ink-2, #4a5248);
  text-align: justify;
}

/* 喂食建议 */
.feed-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.feed-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--color-surface-2, #f6f2e8);
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-ink-2, #4a5248);
}
.feed-idx {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-accent, #e8552b);
  padding-top: 2px;
}

/* AI 快捷提问卡 */
.bd-ai {
  margin-top: 28px;
  padding: 16px;
  border-radius: 18px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, rgba(27, 42, 34, 0.08));
  box-shadow: var(--shadow-soft, 0 6px 18px rgba(27, 42, 34, 0.05));
}
.ai-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13.5px;
  font-weight: 700;
  color: var(--color-accent-ink, #b03a17);
  margin-bottom: 12px;
}
.ai-q {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
  margin-bottom: 8px;
  border-radius: 14px;
  border: 1px solid var(--color-border, rgba(27, 42, 34, 0.08));
  background: var(--color-surface-2, #f6f2e8);
  font-size: 13.5px;
  line-height: 1.5;
  text-align: left;
  color: var(--color-ink, #1b2a22);
  transition: transform var(--dur-fast, 0.15s) var(--ease-out, ease-out);
}
.ai-q:last-of-type { margin-bottom: 0; }
.ai-q:active { transform: scale(0.98); }
.ai-arrow { transform: rotate(180deg); color: var(--color-ink-3, #7a776c); flex-shrink: 0; }

.bd-actions {
  margin-top: 32px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.bd-cta {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 52px;
  border-radius: 18px;
  background: var(--color-accent, #e8552b);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.04em;
  box-shadow: 0 10px 24px rgba(232, 85, 43, 0.28);
}
.bd-cta.ghost {
  background: transparent;
  color: var(--color-ink, #1b2a22);
  border: 1px solid var(--color-border, rgba(27, 42, 34, 0.14));
  box-shadow: none;
}
.bd-missing {
  text-align: center;
  margin-top: 40vh;
  font-size: 14px;
  color: var(--color-ink-3, #7a776c);
}
.link { color: var(--color-accent, #e8552b); }
</style>
