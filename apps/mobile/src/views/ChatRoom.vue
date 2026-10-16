<template>
  <section class="screen room">
    <!-- 顶部会话栏：点击名字查看对方信息 -->
    <header class="room-head">
      <button class="back" type="button" @click="goBack" aria-label="返回">
        <AppIcon name="back" :size="22" />
      </button>
      <button class="room-id" type="button" @click="infoOpen = true">
        <span class="room-ava" :class="{ on: conv?.online }">{{ initial(conv?.name) }}</span>
        <span class="room-id-text">
          <span class="room-name">{{ conv?.name }}</span>
          <span class="room-status">{{ conv?.online ? '在线' : '离线' }}<template v-if="conv?.kind === 'vet'"> · 执业兽医</template></span>
        </span>
      </button>
      <button class="back" type="button" aria-label="更多" @click="infoOpen = true">
        <AppIcon name="filter" :size="20" />
      </button>
    </header>

    <div class="chat-list" ref="listEl">
      <template v-for="(m, i) in msgs" :key="i">
        <!-- 图片消息 -->
        <div v-if="m.image" class="bubble-row" :class="m.role">
          <span v-if="m.role === 'them'" class="b-avatar">{{ initial(conv?.name) }}</span>
          <div
            class="img-bubble"
            :class="[isUrl(m.image) ? 'url' : 'tone-' + m.image, m.role]"
            :style="isUrl(m.image) ? { backgroundImage: `url(${m.image})` } : null"
          >
            <AppIcon name="image" :size="30" class="img-mark" />
            <span class="img-mask" @click="preview(m)">查看大图</span>
          </div>
        </div>
        <!-- 文本消息：长按 / 右键弹出操作 -->
        <div
          v-else
          class="bubble-row"
          :class="m.role"
          @contextmenu.prevent="openMsgMenu(m, i)"
          @touchstart.passive="startPress(m, i)"
          @touchend="cancelPress"
          @touchmove.passive="cancelPress"
        >
          <span v-if="m.role === 'them'" class="b-avatar">{{ initial(conv?.name) }}</span>
          <div class="bubble" :class="m.role">{{ m.text }}</div>
          <span v-if="m.time" class="b-time num">{{ m.time }}</span>
        </div>
      </template>
      <p v-if="!msgs.length && !typing" class="room-empty">打个招呼，开始你们的第一条消息吧</p>
      <div v-if="typing" class="typing">
        <span></span><span></span><span></span>
      </div>
    </div>

    <!-- 表情面板 -->
    <transition name="pop">
      <div v-if="emojiOpen" class="emoji-panel">
        <div class="emoji-grid">
          <button
            v-for="e in emojis"
            :key="e"
            class="emoji"
            type="button"
            @click="input += e"
          >{{ e }}</button>
        </div>
      </div>
    </transition>

    <div class="composer">
      <button class="composer-icon" type="button" aria-label="表情" @click="emojiOpen = !emojiOpen">
        <AppIcon name="sparkle" :size="20" />
      </button>
      <button class="composer-icon" type="button" aria-label="发送图片" @click="pickImage">
        <AppIcon name="image" :size="20" />
      </button>
      <!-- 真实选图：相册/相机选图后上传到服务端，消息携带可访问 URL -->
      <input
        ref="fileInput"
        class="file-input"
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif"
        @change="onImagePicked"
      />
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

    <!-- 消息长按操作 -->
    <transition name="pop">
      <div v-if="msgMenu" class="msg-menu-mask" @click.self="msgMenu = null">
        <div class="msg-menu">
          <button type="button" @click="copyMsg(msgMenu.m)">复制</button>
          <button type="button" @click="deleteMsg(msgMenu.i)">删除</button>
          <button type="button" class="danger" @click="msgMenu = null">取消</button>
        </div>
      </div>
    </transition>

    <!-- 对方信息卡 -->
    <transition name="sheet">
      <div v-if="infoOpen" class="sheet-mask" @click.self="infoOpen = false">
        <div class="sheet">
          <div class="sheet-grip" aria-hidden="true"></div>
          <div class="pf-head">
            <span class="pf-ava" :class="{ on: conv?.online }">{{ initial(conv?.name) }}</span>
            <div class="pf-id">
              <b class="pf-name">{{ conv?.name }}</b>
              <span class="pf-kind" :class="conv?.kind">{{ kindLabel(conv?.kind) }}</span>
              <span class="pf-status">{{ conv?.online ? '在线 · 通常几分钟内回复' : '离线 · 留言会尽快回复' }}</span>
            </div>
          </div>
          <p class="pf-bio">{{ conv?.profile?.bio || '这个人很懒，什么都没写' }}</p>

          <div v-if="conv?.profile?.pet" class="pf-pet">
            <PetAvatar :species="'dog'" :name="conv.profile.pet.name" :size="40" />
            <div class="pf-pet-body">
              <b>{{ conv.profile.pet.name }} · {{ conv.profile.pet.breed }}</b>
              <span>{{ conv.profile.pet.age }} 岁 · 已接种疫苗</span>
            </div>
            <router-link :to="`/pet/doudou`" class="pf-pet-link">看档案</router-link>
          </div>

          <div class="pf-stats">
            <div class="pf-stat">
              <b class="num">{{ conv?.profile?.posts || 0 }}</b>
              <span>社区动态</span>
            </div>
            <span class="pf-sep"></span>
            <div class="pf-stat">
              <b class="num">{{ conv?.profile?.fans || 0 }}</b>
              <span>粉丝</span>
            </div>
          </div>

          <div class="pf-actions">
            <button class="pf-btn ghost" type="button" @click="goCommunity">查看 TA 的社区</button>
          </div>
        </div>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import { fetchConversations, fetchContactGroups, fetchMessages, sendMessage } from '@/api/data'
import { fileApi } from '@/api'
import { showToast } from '@shared/toast'

const route = useRoute()
const router = useRouter()

const conversations = ref([])
const allContacts = ref([])

// 有会话记录的用会话；通讯录联系人（暂无会话）回退为临时会话，可直接发起聊天
const conv = computed(() => {
  const hit = conversations.value.find((c) => c.id === route.params.id)
  if (hit) return hit
  const c = allContacts.value.find((m) => m.id === route.params.id)
  if (!c) return null
  return {
    id: c.id,
    name: c.name,
    kind: c.kind,
    online: !!c.online,
    profile: {
      bio: c.bio,
      pet: c.pet && c.pet.name ? c.pet : null,
      posts: c.posts || 0,
      fans: c.fans || 0
    }
  }
})
const msgs = ref([])
const input = ref('')
const typing = ref(false)
const listEl = ref(null)
const emojiOpen = ref(false)
const infoOpen = ref(false)
const msgMenu = ref(null)

const emojis = ['🐱', '🐶', '😻', '🥺', '😭', '🤤', '👍', '🎉', '🐾', '❤️', '😴', '✨']
const fileInput = ref(null)
const MAX_IMAGE_MB = 8

function initial(name) {
  return (name || '?').slice(0, 1)
}
function kindLabel(k) {
  return { vet: '执业兽医', group: '群聊', friend: '好友' }[k] || ''
}
function isUrl(v) {
  return typeof v === 'string' && /^(https?:)?\/\/|^data:|^\/|^[\w.-]+\.(png|jpe?g|gif|webp|svg)/i.test(v)
}

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

async function send() {
  const text = input.value.trim()
  if (!text || typing.value) return
  input.value = ''
  emojiOpen.value = false
  typing.value = true
  scrollToEnd()
  try {
    // 后端返回「本条消息」+「对方回执」，两条都要进本地列表
    const { message, reply } = await sendMessage(route.params.id, { text })
    if (message) msgs.value.push(message)
    if (reply) msgs.value.push(reply)
    scrollToEnd()
  } catch (e) {
    showToast(e?.message || '发送失败', { type: 'error' })
  } finally {
    typing.value = false
  }
}

// 图片消息：真实选图 → 上传服务端 → 以可访问 URL 发送
function pickImage() {
  if (typing.value) return
  fileInput.value?.click()
}

async function onImagePicked(e) {
  const file = e.target.files?.[0]
  e.target.value = '' // 允许再次选择同一文件
  if (!file) return
  if (!file.type.startsWith('image/')) {
    showToast('请选择图片文件', { type: 'warn' })
    return
  }
  if (file.size > MAX_IMAGE_MB * 1024 * 1024) {
    showToast(`图片不能超过 ${MAX_IMAGE_MB}MB`, { type: 'warn' })
    return
  }
  typing.value = true
  scrollToEnd()
  try {
    const fd = new FormData()
    fd.append('file', file)
    const up = await fileApi.upload(fd, 'chat')
    const url = up?.url
    if (!url) throw new Error('上传失败')
    const { message, reply } = await sendMessage(route.params.id, { images: [url] })
    if (message) msgs.value.push(toViewMsg(message))
    if (reply) msgs.value.push(reply)
    scrollToEnd()
  } catch (err) {
    showToast(err?.message || '图片发送失败', { type: 'error' })
  } finally {
    typing.value = false
    scrollToEnd()
  }
}

function preview(m) {
  if (isUrl(m.image)) window.open(m.image, '_blank')
  else showToast('演示环境：真实设备上此处查看原图', { type: 'info' })
}

/* ---------- 长按操作 ---------- */

let pressTimer = null
function startPress(m, i) {
  cancelPress()
  pressTimer = setTimeout(() => {
    msgMenu.value = { m, i }
  }, 550)
}
function cancelPress() {
  if (pressTimer) {
    clearTimeout(pressTimer)
    pressTimer = null
  }
}
function openMsgMenu(m, i) {
  msgMenu.value = { m, i }
}
async function copyMsg(m) {
  msgMenu.value = null
  try {
    await navigator.clipboard.writeText(m.text)
    showToast('已复制', { type: 'success' })
  } catch {
    showToast('复制失败', { type: 'info' })
  }
}
function deleteMsg(i) {
  msgs.value.splice(i, 1)
  msgMenu.value = null
  showToast('消息已删除', { type: 'info' })
}

/* ---------- 对方信息卡 ---------- */

function goCommunity() {
  infoOpen.value = false
  router.push('/community')
}

onMounted(async () => {
  try {
    const [convs, contactRes] = await Promise.all([fetchConversations(), fetchContactGroups()])
    conversations.value = convs || []
    allContacts.value = (contactRes?.groups || []).flatMap((g) => g.members || [])
  } catch (e) {
    showToast(e?.message || '会话加载失败', { type: 'error' })
  }
  try {
    // 后端图片消息用 images[]（URL 数组），模板按 m.image 单图渲染，这里做一次映射
    const list = await fetchMessages(route.params.id)
    msgs.value = (list || []).map(toViewMsg)
  } catch {
    msgs.value = []
  }
  scrollToEnd()
})

/** 后端消息形状 → 视图消息形状（images[] 取首图映射为 image） */
function toViewMsg(m) {
  return {
    ...m,
    image: m.image || (m.images?.length && !m.text ? m.images[0] : undefined)
  }
}
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
  flex-shrink: 0;
}
.room-id {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
}
.room-ava {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 30%;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 16px;
  background: var(--grad-sand);
  flex-shrink: 0;
}
.room-ava.on::after {
  content: '';
  position: absolute;
  right: -1px;
  bottom: -1px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-good);
  border: 2px solid var(--color-surface);
}
.room-id-text { display: flex; flex-direction: column; align-items: flex-start; min-width: 0; }
.room-name { font-weight: 700; font-size: 16px; }
.room-status { font-size: 11.5px; color: var(--color-muted); }

.chat-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 18px 18px 24px;
}
/* 短对话时消息贴底对齐（与主流 IM 一致）；用首个子元素 margin-top:auto 实现，
   避免 justify-content:flex-end 在溢出时顶部不可滚动的经典 flex 陷阱 */
.chat-list > :first-child { margin-top: auto; }
.room-empty {
  text-align: center;
  font-size: 13px;
  color: var(--color-faint);
  padding: 26px 0 8px;
}

/* 消息行（与 ChatBubble 视觉一致，支持长按与图片） */
.bubble-row {
  display: flex;
  align-items: flex-end;
  gap: 9px;
  margin-bottom: 16px;
}
.bubble-row.me { flex-direction: row-reverse; }
.b-avatar {
  width: 34px;
  height: 34px;
  border-radius: 30%;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 15px;
  background: var(--grad-sand);
  flex-shrink: 0;
}
.bubble {
  max-width: 68%;
  padding: 11px 15px;
  border-radius: 18px;
  border-bottom-left-radius: 6px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  font-size: 15px;
  line-height: 1.55;
  color: var(--color-ink);
  word-break: break-word;
}
.bubble.me {
  background: var(--color-accent);
  border-color: transparent;
  color: #fff;
  border-bottom-left-radius: 18px;
  border-bottom-right-radius: 6px;
}
.b-time { font-size: 10.5px; color: var(--color-faint); flex-shrink: 0; }

/* 图片消息 */
.img-bubble {
  position: relative;
  width: 180px;
  height: 135px;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  color: rgba(255, 255, 255, 0.5);
  overflow: hidden;
  border-bottom-left-radius: 6px;
}
.img-bubble.me { border-bottom-left-radius: var(--radius-md); border-bottom-right-radius: 6px; }
.img-bubble.tone-sage { background: var(--grad-sage); }
.img-bubble.tone-peach { background: var(--grad-peach); }
.img-bubble.tone-coral { background: var(--grad-coral); }
.img-bubble.tone-sand { background: var(--grad-sand); }
/* 真实图片：URL 作为背景铺满，隐藏示意图标 */
.img-bubble.url {
  background-size: cover;
  background-position: center;
  background-color: var(--color-surface-2);
}
.img-bubble.url .img-mark { display: none; }
.img-mask {
  position: absolute;
  inset: auto 0 0 0;
  padding: 5px 0;
  text-align: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  background: rgba(27, 42, 34, 0.45);
  backdrop-filter: blur(4px);
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

/* 表情面板：房间内静态项，打开时聊天区自然让位（不再 fixed 计算底栏偏移） */
.emoji-panel {
  flex: 0 0 auto;
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  padding: 12px 14px;
  z-index: 18;
}
.emoji-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 6px;
}
.emoji {
  aspect-ratio: 1;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  font-size: 24px;
  transition: background var(--dur-fast);
}
.emoji:active { background: var(--color-surface-2); }

/* 输入栏：房间底部静态项，位于底部导航正上方 */
.composer {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px calc(10px + env(safe-area-inset-bottom, 0px));
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
  transition: transform var(--dur-fast) var(--ease-out);
}
.composer-icon:active { transform: scale(0.9); }
.file-input {
  display: none;
}
.composer-input {
  flex: 1;
  min-width: 0;
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

/* 长按菜单 */
.msg-menu-mask {
  position: fixed;
  inset: 0;
  z-index: 70;
  background: rgba(27, 42, 34, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}
.msg-menu {
  display: flex;
  flex-direction: column;
  width: 200px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-3);
}
.msg-menu button {
  padding: 15px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
  border-bottom: 1px solid var(--hairline);
}
.msg-menu button:last-child { border-bottom: none; }
.msg-menu button.danger { color: var(--color-alert); }
.msg-menu button:active { background: var(--color-surface-2); }

/* 对方信息卡 */
.sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: rgba(27, 42, 34, 0.36);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.sheet {
  width: 100%;
  max-width: var(--shell-max);
  background: var(--color-surface);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  padding: 10px 20px calc(28px + env(safe-area-inset-bottom, 0px));
}
.sheet-grip {
  width: 38px;
  height: 4px;
  border-radius: 999px;
  background: var(--color-border-strong);
  margin: 0 auto 16px;
}
.pf-head { display: flex; align-items: center; gap: 14px; }
.pf-ava {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 30%;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 26px;
  background: var(--grad-sand);
  flex-shrink: 0;
}
.pf-ava.on::after {
  content: '';
  position: absolute;
  right: 0;
  bottom: 2px;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: var(--color-good);
  border: 2.5px solid var(--color-surface);
}
.pf-id { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.pf-name { font-family: var(--font-display); font-size: 19px; font-weight: 700; }
.pf-kind {
  align-self: flex-start;
  font-size: 10.5px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-2);
  color: var(--color-muted);
}
.pf-kind.vet { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.pf-kind.friend { background: var(--color-sage-soft); color: var(--color-good); }
.pf-status { font-size: 11.5px; color: var(--color-faint); }
.pf-bio {
  margin-top: 14px;
  font-size: 13.5px;
  line-height: 1.7;
  color: var(--color-ink-2);
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: var(--color-bg);
  border: 1px solid var(--hairline);
}
.pf-pet {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: var(--color-bg);
  border: 1px solid var(--hairline);
}
.pf-pet-body { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.pf-pet-body b { font-size: 14px; }
.pf-pet-body span { font-size: 11.5px; color: var(--color-muted); }
.pf-pet-link { font-size: 12.5px; font-weight: 700; color: var(--color-accent-ink); }
.pf-stats {
  display: flex;
  align-items: center;
  margin-top: 16px;
  padding: 13px 14px;
  border-radius: var(--radius-md);
  background: var(--color-bg);
  border: 1px solid var(--hairline);
}
.pf-stat { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.pf-stat b { font-family: var(--font-display); font-size: 19px; font-weight: 700; }
.pf-stat span { font-size: 11px; color: var(--color-faint); }
.pf-sep { width: 1px; height: 26px; background: var(--hairline); }
.pf-actions { display: flex; gap: 10px; margin-top: 18px; }
.pf-btn {
  flex: 1;
  padding: 14px;
  border-radius: var(--radius-pill);
  background: var(--color-ink);
  color: var(--color-surface);
  font-size: 15px;
  font-weight: 700;
  transition: opacity var(--dur-fast), transform var(--dur-fast) var(--ease-out);
}
.pf-btn:active { transform: scale(0.97); }
.pf-btn.ghost {
  background: var(--color-surface);
  color: var(--color-ink);
  border: 1px solid var(--hairline-strong);
}

.pop-enter-active, .pop-leave-active { transition: opacity var(--dur-fast) var(--ease-out); }
.pop-enter-from, .pop-leave-to { opacity: 0; }

.sheet-enter-active, .sheet-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.sheet-enter-from, .sheet-leave-to { opacity: 0; }
.sheet-enter-active .sheet, .sheet-leave-active .sheet { transition: transform var(--dur-base) var(--ease-out); }
.sheet-enter-from .sheet, .sheet-leave-to .sheet { transform: translateY(100%); }

@media (prefers-reduced-motion: reduce) {
  .typing span { animation: none; }
}
</style>
