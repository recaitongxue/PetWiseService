<template>
  <section class="splash">
    <!-- 环境光斑 -->
    <div class="splash-orbit" aria-hidden="true">
      <span class="orb o1 tone-sage"></span>
      <span class="orb o2 tone-peach"></span>
      <span class="orb o3 tone-coral"></span>
      <span class="orb o4 tone-sand"></span>
    </div>

    <div class="splash-core">
      <!-- 品牌标识：呼吸缩放 + 双圈爪印涟漪 -->
      <div class="splash-mark">
        <span class="ripple r1" aria-hidden="true"></span>
        <span class="ripple r2" aria-hidden="true"></span>
        <span class="mark-inner"><BrandMark :show-text="false" /></span>
      </div>
      <h1 class="splash-word">
        <span v-for="(ch, i) in 'Petwise'" :key="i" :style="{ animationDelay: i * 0.07 + 's' }">{{ ch }}</span>
      </h1>
      <!-- 标语轮播：三句渐隐切换 -->
      <div class="tag-stage">
        <p v-for="(t, i) in taglines" :key="i" class="splash-tag" :class="{ on: tagIndex === i }">
          {{ t }}
        </p>
      </div>
    </div>

    <div class="splash-foot">
      <button class="enter-btn" type="button" @click="enter">{{ authed ? '进入 Petwise' : '开始使用' }}</button>
      <span class="enter-sub">拍照识别 · 智能问诊 · 宠物社区</span>
      <!-- 启动进度：满格后自动进入（主流 App 冷启动行为） -->
      <div class="boot-bar" aria-hidden="true"><span class="boot-fill" :style="{ animationDuration: bootMs + 'ms' }"></span></div>
      <span class="boot-note num">{{ bootPct }}% · 正在同步宠物档案</span>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import BrandMark from '@/components/BrandMark.vue'
import { isAuthed } from '@/api/client'

const router = useRouter()
// 已登录直接进首页，未登录先引导登录（主流 App 的冷启动分流）
const authed = isAuthed()

const taglines = [
  '用计算机视觉与大模型，\n读懂它不会说出口的事。',
  '识别品种 · 问诊分诊 · 养护提醒，\n一只APP照顾好它的一生。',
  '每一次喵呜与摇尾，\n都值得被认真记录。'
]
const tagIndex = ref(0)
let tagTimer = null

// 启动进度：与 CSS 动画同长（2.6s），到 100% 自动进入
const bootMs = 2600
const bootPct = ref(0)
let bootTimer = null
let entered = false

function enter() {
  if (entered) return
  entered = true
  clearInterval(bootTimer)
  clearInterval(tagTimer)
  router.replace(authed ? '/home' : '/login')
}

onMounted(() => {
  tagTimer = setInterval(() => {
    tagIndex.value = (tagIndex.value + 1) % taglines.length
  }, bootMs / taglines.length)

  const t0 = Date.now()
  bootTimer = setInterval(() => {
    const pct = Math.min(100, Math.round(((Date.now() - t0) / bootMs) * 100))
    bootPct.value = pct
    if (pct >= 100) {
      clearInterval(bootTimer)
      setTimeout(enter, 240)
    }
  }, 80)
})

onUnmounted(() => {
  clearInterval(bootTimer)
  clearInterval(tagTimer)
})
</script>

<style scoped>
.splash {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: 80px 28px 56px;
  position: relative;
  overflow: hidden;
}
.splash-orbit .orb {
  position: absolute;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  opacity: 0.65;
  filter: blur(0.2px) drop-shadow(0 6px 14px rgba(27, 42, 34, 0.12));
  animation: float 7s var(--ease-in-out) infinite;
}
.orb.tone-sage { background: var(--grad-sage); }
.orb.tone-peach { background: var(--grad-peach); }
.orb.tone-coral { background: var(--grad-coral); }
.orb.tone-sand { background: var(--grad-sand); }
.o1 { top: 14%; left: 12%; animation-delay: 0s; }
.o2 { top: 22%; right: 14%; animation-delay: 1.2s; width: 20px; height: 20px; }
.o3 { bottom: 26%; left: 16%; animation-delay: 2s; width: 30px; height: 30px; }
.o4 { bottom: 18%; right: 12%; animation-delay: 0.6s; }
@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0); }
  50% { transform: translateY(-14px) rotate(8deg); }
}

.splash-core {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 8px;
}

/* 品牌标识：呼吸 + 涟漪 */
.splash-mark {
  position: relative;
  width: 92px;
  height: 92px;
  margin-bottom: 14px;
  display: grid;
  place-items: center;
}
.mark-inner {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  animation: breathe 3.2s var(--ease-in-out) infinite;
}
@keyframes breathe {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.06); }
}
.ripple {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1.5px solid color-mix(in srgb, var(--color-accent) 40%, transparent);
  animation: ripple 2.8s var(--ease-out) infinite;
}
.ripple.r2 { animation-delay: 1.4s; }
@keyframes ripple {
  0% { transform: scale(0.72); opacity: 0; }
  18% { opacity: 0.85; }
  100% { transform: scale(1.7); opacity: 0; }
}

/* 品牌名逐字浮现 */
.splash-word {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-3xl);
  letter-spacing: -0.03em;
  color: var(--color-ink);
  line-height: 1;
  display: flex;
}
.splash-word span {
  display: inline-block;
  animation: letter-in 0.55s var(--ease-out) both;
}
@keyframes letter-in {
  0% { transform: translateY(14px); opacity: 0; }
  100% { transform: translateY(0); opacity: 1; }
}

/* 标语轮播 */
.tag-stage {
  position: relative;
  height: 48px;
  margin-top: 10px;
  width: 100%;
}
.splash-tag {
  position: absolute;
  inset: 0;
  font-family: var(--font-display);
  font-style: italic;
  font-size: var(--fs-md);
  color: var(--color-ink-2);
  line-height: 1.5;
  white-space: pre-line;
  opacity: 0;
  transform: translateY(8px);
  transition: opacity 0.6s var(--ease-out), transform 0.6s var(--ease-out);
}
.splash-tag.on {
  opacity: 1;
  transform: translateY(0);
}

.splash-foot {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.enter-btn {
  width: 100%;
  max-width: 320px;
  padding: 16px;
  border-radius: var(--radius-pill);
  background: var(--color-ink);
  color: var(--color-surface);
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.02em;
  box-shadow: var(--shadow-2);
  transition: transform var(--dur-fast) var(--ease-out), box-shadow var(--dur-base);
}
.enter-btn:active {
  transform: translateY(2px) scale(0.99);
  box-shadow: var(--shadow-1);
}
.enter-sub {
  font-size: 13px;
  color: var(--color-muted);
  letter-spacing: 0.04em;
}
.boot-bar {
  width: min(320px, 100%);
  height: 3px;
  border-radius: 999px;
  background: var(--color-surface-2);
  overflow: hidden;
  margin-top: 6px;
}
.boot-fill {
  display: block;
  height: 100%;
  width: 0;
  border-radius: 999px;
  background: var(--grad-coral);
  animation: boot linear both;
}
@keyframes boot {
  0% { width: 0; }
  100% { width: 100%; }
}
.boot-note {
  font-size: 11px;
  color: var(--color-faint);
  letter-spacing: 0.04em;
}

@media (prefers-reduced-motion: reduce) {
  .splash-orbit .orb, .mark-inner, .ripple, .splash-word span { animation: none; }
  .boot-fill { animation: none; width: 100%; }
}
</style>
