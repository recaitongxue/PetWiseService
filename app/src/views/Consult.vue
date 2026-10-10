<template>
  <section class="screen consult">
    <header class="screen-head" v-reveal>
      <div>
        <p class="eyebrow">LARGE LANGUAGE MODEL</p>
        <h1 class="title">智能问诊</h1>
      </div>
      <span class="ai-badge"><span class="ai-dot"></span> 智能兽医在线</span>
    </header>

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

    <!-- 推荐问题 -->
    <div class="suggest" v-reveal="{ delay: 80 }">
      <button
        v-for="q in consultSuggestions"
        :key="q"
        class="suggest-chip"
        type="button"
        @click="send(q)"
      >
        {{ q }}
      </button>
    </div>

    <!-- 对话区 -->
    <div class="chat-list" ref="listEl">
      <ChatBubble
        v-for="(m, i) in messages"
        :key="i"
        :role="m.role"
        :text="m.text"
        :time="m.time"
        :avatar="petAvatar"
      />
      <div v-if="typing" class="typing">
        <span></span><span></span><span></span>
      </div>
    </div>

    <!-- 随访建议（AI 回复后给出，自然延续对话） -->
    <transition name="ctx">
      <div v-if="followups.length" class="followups">
        <button
          v-for="f in followups"
          :key="f"
          class="fu-chip"
          type="button"
          @click="send(f)"
        >
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
        placeholder="描述宠物的情况…"
        @keyup.enter="send()"
      />
      <button class="composer-send" type="button" :disabled="!input.trim()" @click="send()" aria-label="发送">
        <AppIcon name="send" :size="20" />
      </button>
    </div>

    <!-- 医疗免责声明 -->
    <p class="disclaimer">AI 建议仅供参考，不能替代执业兽医的当面诊断。紧急情况请立即就医。</p>
  </section>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import ChatBubble from '@/components/ChatBubble.vue'
import { consultSeed, consultSuggestions, pets } from '@/data/mock'

const route = useRoute()
const petAvatar = pets[0].avatar
const messages = ref([...consultSeed])
const input = ref('')
const typing = ref(false)
const followups = ref([])
const listEl = ref(null)

// 从拍照识别带入的上下文
const ctx = reactive({ pet: route.query.pet || '', note: route.query.note || '' })
if (ctx.pet) {
  messages.value.push({
    role: 'ai',
    text: `我已了解你刚识别的是「${ctx.pet}」。${
      ctx.note ? '结合识别提示：' + ctx.note : ''
    }你想进一步确认哪方面？我帮你分析。`,
    time: now()
  })
}

function now() {
  const d = new Date()
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function scrollToEnd() {
  nextTick(() => {
    if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
  })
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
    return '幼猫/幼犬基础免疫通常在 6–8 周开始，每 2–4 周一针，完成基础免疫后每年加强。接种前需确保宠物健康、无寄生虫。具体时间表我可结合麻薯的档案帮你排。'
  }
  if (t.includes('皮肤') || t.includes('照片')) {
    return '已收到照片区域描述。皮肤问题需关注红斑、脱毛、皮屑与抓挠频率。请保持患处干燥清洁，避免舔舐；若范围扩大或出现渗液，建议拍照后线下面诊。以上仅供参考。'
  }
  return '我理解你的情况了。请补充一下宠物的年龄、品种、症状持续时间和精神状态，我会给出更有针对性的初步判断。注意：我的建议仅作参考，紧急情况请立即就医。'
}

// 根据对话生成相关随访建议，让对话自然延续
function genFollowups(text) {
  const t = text.toLowerCase()
  if (t.includes('耳朵')) return ['耳道怎么清洁？', '需要买耳药吗？', '多久能好？']
  if (t.includes('吃饭') || t.includes('食欲')) return ['能喂什么开胃？', '要去医院吗？', '精神差怎么判断？']
  if (t.includes('疫苗')) return ['麻薯的接种记录', '接种后注意什么', '能洗澡吗？']
  if (t.includes('皮肤')) return ['居家怎么护理', '要忌口吗', '什么时候必须面诊']
  return ['帮我记录症状', '这种情况要去医院吗', '日常怎么护理']
}

function send(preset) {
  const text = (preset ?? input.value).trim()
  if (!text || typing.value) return
  messages.value.push({ role: 'me', text, time: now() })
  input.value = ''
  followups.value = []
  scrollToEnd()

  typing.value = true
  scrollToEnd()
  setTimeout(() => {
    typing.value = false
    const reply = aiReply(text)
    messages.value.push({ role: 'ai', text: reply, time: now() })
    followups.value = genFollowups(text)
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
.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-good);
  background: var(--color-sage-soft);
  padding: 6px 12px;
  border-radius: var(--radius-pill);
}
.ai-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-good);
  animation: blink 1.6s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* 识别上下文横幅 */
.ctx-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: var(--color-accent-soft);
  border: 1px solid color-mix(in srgb, var(--color-accent) 30%, transparent);
  margin: 8px 0 14px;
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
  margin: 14px 0 18px;
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
  .ai-dot, .typing span { animation: none; }
}
</style>
