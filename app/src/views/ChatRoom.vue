<template>
  <section class="screen room">
    <!-- 顶部会话栏 -->
    <header class="room-head">
      <button class="back" type="button" @click="goBack" aria-label="返回">
        <AppIcon name="back" :size="22" />
      </button>
      <div class="room-id">
        <span class="room-name">{{ conv?.name }}</span>
        <span class="room-status">{{ conv?.online ? '在线' : '离线' }}</span>
      </div>
      <button class="back" type="button" aria-label="更多">
        <AppIcon name="share" :size="20" />
      </button>
    </header>

    <div class="chat-list" ref="listEl">
      <ChatBubble
        v-for="(m, i) in msgs"
        :key="i"
        :role="m.role"
        :text="m.text"
        :time="m.time"
        :name="conv?.name"
      />
      <div v-if="typing" class="typing">
        <span></span><span></span><span></span>
      </div>
    </div>

    <div class="composer">
      <button class="composer-icon" type="button" aria-label="表情">
        <AppIcon name="sparkle" :size="20" />
      </button>
      <input
        v-model="input"
        class="composer-input"
        type="text"
        placeholder="发条消息…"
        @keyup.enter="send()"
      />
      <button class="composer-send" type="button" :disabled="!input.trim()" @click="send()" aria-label="发送">
        <AppIcon name="send" :size="20" />
      </button>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import ChatBubble from '@/components/ChatBubble.vue'
import { conversations, chatRooms } from '@/data/mock'

const route = useRoute()
const router = useRouter()

const conv = computed(() => conversations.find((c) => c.id === route.params.id))
const msgs = ref([...(chatRooms[route.params.id] || [])])
const input = ref('')
const typing = ref(false)
const listEl = ref(null)

function scrollToEnd() {
  nextTick(() => {
    if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
  })
}
function now() {
  const d = new Date()
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
function goBack() {
  router.back()
}

function send() {
  const text = input.value.trim()
  if (!text || typing.value) return
  msgs.value.push({ role: 'me', text, time: now() })
  input.value = ''
  scrollToEnd()
  typing.value = true
  scrollToEnd()
  setTimeout(() => {
    typing.value = false
    msgs.value.push({ role: 'them', text: '收到～ 我看看', time: now() })
    scrollToEnd()
  }, 1100)
}

onMounted(scrollToEnd)
</script>

<style scoped>
.room {
  padding: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.room-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  background: color-mix(in srgb, var(--color-surface) 90%, transparent);
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 10;
}
.back {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--color-ink);
}
.room-id { flex: 1; display: flex; flex-direction: column; align-items: center; }
.room-name { font-weight: 700; font-size: 16px; }
.room-status { font-size: 12px; color: var(--color-muted); }

.chat-list {
  flex: 1;
  overflow-y: auto;
  padding: 18px 18px 96px;
}
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

@media (prefers-reduced-motion: reduce) {
  .typing span { animation: none; }
}
</style>
