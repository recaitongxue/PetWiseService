<template>
  <section class="splash">
    <div class="splash-orbit" aria-hidden="true">
      <span class="orb o1 tone-sage"></span>
      <span class="orb o2 tone-peach"></span>
      <span class="orb o3 tone-coral"></span>
      <span class="orb o4 tone-sand"></span>
    </div>

    <div class="splash-core">
      <div class="splash-mark" v-reveal>
        <BrandMark :show-text="false" />
      </div>
      <h1 class="splash-word" v-reveal="{ delay: 90 }">Petwise</h1>
      <p class="splash-tag" v-reveal="{ delay: 180 }">
        用计算机视觉与大模型，<br />读懂它不会说出口的事。
      </p>
    </div>

    <div class="splash-foot" v-reveal="{ delay: 300 }">
      <button class="enter-btn" type="button" @click="enter">{{ authed ? '进入 Petwise' : '开始使用' }}</button>
      <span class="enter-sub">拍照识别 · 智能问诊 · 宠物社区</span>
    </div>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router'
import BrandMark from '@/components/BrandMark.vue'
import { isAuthed } from '@/data/ops'

const router = useRouter()
// 已登录直接进首页，未登录先引导登录（主流 App 的冷启动分流）
const authed = isAuthed()

function enter() {
  router.replace(authed ? '/home' : '/login')
}
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
.splash-mark {
  width: 92px;
  height: 92px;
  margin-bottom: 14px;
  animation: pop 0.7s var(--ease-out) both;
}
@keyframes pop {
  0% { transform: scale(0.6) rotate(-12deg); opacity: 0; }
  100% { transform: scale(1) rotate(0); opacity: 1; }
}
.splash-word {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-3xl);
  letter-spacing: -0.03em;
  color: var(--color-ink);
  line-height: 1;
}
.splash-tag {
  font-family: var(--font-display);
  font-style: italic;
  font-size: var(--fs-md);
  color: var(--color-ink-2);
  line-height: 1.5;
  margin-top: 8px;
}
.splash-foot {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
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
@media (prefers-reduced-motion: reduce) {
  .splash-orbit .orb, .splash-mark { animation: none; }
}
</style>
