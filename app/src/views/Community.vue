<template>
  <section class="screen community">
    <header class="screen-head" v-reveal>
      <div>
        <p class="eyebrow">PET COMMUNITY</p>
        <h1 class="title">宠物社区</h1>
      </div>
      <button class="post-btn-top" type="button" @click="openCompose" aria-label="发布">
        <AppIcon name="plus" :size="20" />
      </button>
    </header>

    <!-- 分段标签 -->
    <div class="tabs" v-reveal="{ delay: 80 }">
      <button
        class="tab"
        :class="{ on: tab === 'recommend' }"
        type="button"
        @click="tab = 'recommend'"
      >
        推荐
      </button>
      <button class="tab" :class="{ on: tab === 'follow' }" type="button" @click="tab = 'follow'">
        关注
      </button>
      <span class="tab-glider" :class="tab"></span>
    </div>

    <!-- 话题条（可点击筛选） -->
    <div class="topics" v-reveal="{ delay: 120 }">
      <button
        class="topic"
        :class="{ on: activeTopic === null }"
        type="button"
        @click="activeTopic = null"
      >
        全部
      </button>
      <button
        v-for="t in topics"
        :key="t"
        class="topic"
        :class="{ on: activeTopic === t }"
        type="button"
        @click="activeTopic = activeTopic === t ? null : t"
      >
        #{{ t }}
      </button>
    </div>

    <!-- 信息流 -->
    <div class="feed">
      <PostCard
        v-for="p in visiblePosts"
        :key="p.id"
        :post="p"
        @comment="openComments(p)"
      />
    </div>

    <p v-if="!visiblePosts.length" class="empty">这个话题下还没有动态，换个看看？</p>

    <button class="load-more" type="button" @click="loadMore">加载更多动态</button>

    <!-- 发布 FAB -->
    <button class="fab" type="button" @click="openCompose" aria-label="发布动态">
      <AppIcon name="plus" :size="26" />
    </button>

    <!-- 发布底部弹层 -->
    <transition name="sheet">
      <div v-if="composing" class="sheet-mask" @click.self="closeCompose">
        <div class="sheet">
          <div class="sheet-head">
            <span>发布动态</span>
            <button class="sheet-close" type="button" @click="closeCompose">取消</button>
          </div>
          <textarea
            v-model="draft"
            class="sheet-input"
            rows="4"
            placeholder="分享你和毛孩子的故事…"
          ></textarea>
          <div class="sheet-gallery-label">添加图片</div>
          <div class="sheet-gallery">
            <button
              v-for="e in galleryPool"
              :key="e"
              type="button"
              class="g-item"
              :class="['tone-' + e, { on: draftImages.includes(e) }]"
              @click="toggleTone(e)"
            ></button>
          </div>
          <button class="sheet-publish" type="button" :disabled="!draft.trim()" @click="publish">
            发布
          </button>
        </div>
      </div>
    </transition>

    <!-- 评论底部弹层 -->
    <transition name="sheet">
      <div v-if="commentPost" class="sheet-mask" @click.self="closeComments">
        <div class="sheet comments">
          <div class="sheet-head">
            <span>评论 · {{ commentList.length }}</span>
            <button class="sheet-close" type="button" @click="closeComments">关闭</button>
          </div>
          <div class="comment-list">
            <div v-for="(c, i) in commentList" :key="i" class="comment">
              <span class="c-avatar">{{ initial(c.name) }}</span>
              <div class="c-body">
                <span class="c-name">{{ c.name }}</span>
                <p class="c-text">{{ c.text }}</p>
                <span class="c-time">{{ c.time }}</span>
              </div>
              <button class="c-like" :class="{ on: c.liked }" type="button" @click="toggleCommentLike(i)">
                <AppIcon :name="c.liked ? 'heart' : 'heart-o'" :size="16" />
              </button>
            </div>
          </div>
          <div class="comment-compose">
            <input
              v-model="commentDraft"
              class="cc-input"
              type="text"
              placeholder="说点什么…"
              @keyup.enter="sendComment"
            />
            <button class="cc-send" type="button" :disabled="!commentDraft.trim()" @click="sendComment">发送</button>
          </div>
        </div>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import PostCard from '@/components/PostCard.vue'
import { feed, user, commentsByPost, galleryPool } from '@/data/mock'
import { showToast } from '@/composables/toast'

const tab = ref('recommend')
const topics = ['成长记录', '健康管理', '柯基', '英短', '换季护理', '线下撸猫']
const activeTopic = ref(null)
const posts = ref([...feed])

const visiblePosts = computed(() => {
  let list = posts.value
  if (tab.value === 'follow') list = list.filter((_, i) => i % 2 === 1)
  if (activeTopic.value) {
    const tag = '#' + activeTopic.value
    list = list.filter((p) => p.tags.includes(tag))
  }
  return list
})

let moreCount = 0
function loadMore() {
  moreCount++
  posts.value.push({
    id: 'more' + moreCount,
    author: '橘座铲屎团',
    species: 'cat',
    time: '刚刚',
    text: '又是被主子统治的一天，分享一张今天的窗台晒太阳。',
    images: ['peach', 'coral'],
    tags: ['#日常', '#晒太阳'],
    likes: 12,
    comments: 3,
    liked: false
  })
}

// 发布
const composing = ref(false)
const draft = ref('')
const draftImages = ref([])

function openCompose() {
  composing.value = true
}
function closeCompose() {
  composing.value = false
}
function toggleTone(e) {
  const i = draftImages.value.indexOf(e)
  if (i >= 0) draftImages.value.splice(i, 1)
  else if (draftImages.value.length < 3) draftImages.value.push(e)
}
function publish() {
  if (!draft.value.trim()) return
  posts.value.unshift({
    id: 'mine' + Date.now(),
    author: user.name,
    time: '刚刚',
    text: draft.value.trim(),
    images: [...draftImages.value],
    tags: ['#我的日常'],
    likes: 0,
    comments: 0,
    liked: false
  })
  draft.value = ''
  draftImages.value = []
  composing.value = false
  tab.value = 'recommend'
  activeTopic.value = null
  showToast('已发布到社区', { type: 'success' })
}

// 评论
const commentPost = ref(null)
const commentList = ref([])
const commentDraft = ref('')

function openComments(post) {
  commentPost.value = post
  commentList.value = [...(commentsByPost[post.id] || [])]
}
function closeComments() {
  commentPost.value = null
  commentDraft.value = ''
}
function toggleCommentLike(i) {
  const c = commentList.value[i]
  c.liked = !c.liked
}
function sendComment() {
  const text = commentDraft.value.trim()
  if (!text) return
  commentList.value.push({
    name: user.name,
    text,
    time: '刚刚',
    liked: false
  })
  commentDraft.value = ''
  if (commentPost.value) commentPost.value.comments++
}

function initial(name) {
  return (name || '?').slice(0, 1)
}
</script>

<style scoped>
.title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-2xl);
  letter-spacing: -0.02em;
  line-height: 1;
}
.post-btn-top {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-ink);
}

.tabs {
  position: relative;
  display: inline-flex;
  background: var(--color-surface-2);
  border-radius: var(--radius-pill);
  padding: 4px;
  margin: 8px 0 14px;
}
.tab {
  position: relative;
  z-index: 1;
  padding: 8px 22px;
  font-weight: 700;
  font-size: 14px;
  color: var(--color-muted);
  transition: color var(--dur-base) var(--ease-out);
}
.tab.on { color: var(--color-ink); }
.tab-glider {
  position: absolute;
  top: 4px;
  bottom: 4px;
  width: calc(50% - 4px);
  background: var(--color-surface);
  border-radius: var(--radius-pill);
  box-shadow: var(--shadow-1);
  transition: transform var(--dur-base) var(--ease-out);
}
.tab-glider.recommend { transform: translateX(0); }
.tab-glider.follow { transform: translateX(100%); }

.topics {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 6px;
  margin-bottom: 8px;
}
.topic {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-sage);
  background: var(--color-sage-soft);
  padding: 6px 14px;
  border-radius: var(--radius-pill);
  transition: all var(--dur-fast) var(--ease-out);
}
.topic.on {
  background: var(--color-sage);
  color: var(--color-surface);
}
.topic:active { transform: scale(0.95); }

.empty {
  text-align: center;
  color: var(--color-muted);
  font-size: 14px;
  padding: 30px 0;
}
.load-more {
  width: 100%;
  padding: 13px;
  border-radius: var(--radius-pill);
  border: 1px dashed var(--color-border-strong);
  color: var(--color-muted);
  font-weight: 700;
  font-size: 14px;
  margin-top: 4px;
}

.fab {
  position: fixed;
  right: max(16px, calc(50% - var(--shell-max) / 2 + 16px));
  bottom: calc(92px + env(safe-area-inset-bottom, 0px));
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #fff;
  background: linear-gradient(150deg, var(--color-accent), var(--color-accent-ink));
  box-shadow: 0 8px 20px rgba(232, 85, 43, 0.32);
  transition: transform var(--dur-fast) var(--ease-out);
}
.fab:active { transform: scale(0.92); }

/* 发布弹层 */
.sheet-mask {
  position: fixed;
  inset: 0;
  background: rgba(27, 42, 34, 0.4);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 50;
}
.sheet {
  width: min(var(--shell-max), 100%);
  background: var(--color-bg);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  padding: 20px 22px calc(28px + env(safe-area-inset-bottom, 0px));
  box-shadow: var(--shadow-3);
  max-height: 86vh;
  display: flex;
  flex-direction: column;
}
.sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-lg);
  margin-bottom: 14px;
}
.sheet-close {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-muted);
}
.sheet-input {
  width: 100%;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: 14px;
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.6;
  color: var(--color-ink);
  resize: none;
  outline: none;
}
.sheet-input:focus-visible { border-color: var(--color-accent); }
.sheet-gallery-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-muted);
  margin: 16px 0 10px;
}
.sheet-gallery {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
}
.g-item {
  aspect-ratio: 1;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.22);
  transition: transform var(--dur-fast) var(--ease-out), border-color var(--dur-fast);
}
.g-item.tone-sage { background: var(--grad-sage); }
.g-item.tone-peach { background: var(--grad-peach); }
.g-item.tone-ink { background: var(--grad-ink); }
.g-item.tone-coral { background: var(--grad-coral); }
.g-item.tone-sand { background: var(--grad-sand); }
.g-item.on { border-color: var(--color-accent); box-shadow: 0 0 0 2px var(--color-accent); }
.g-item:active { transform: scale(0.9); }
.sheet-publish {
  width: 100%;
  padding: 15px;
  border-radius: var(--radius-pill);
  background: var(--color-ink);
  color: var(--color-surface);
  font-weight: 700;
  font-size: 16px;
  transition: opacity var(--dur-fast);
  margin-top: 18px;
}
.sheet-publish:disabled { opacity: 0.4; }

/* 评论弹层 */
.comments { padding-bottom: calc(20px + env(safe-area-inset-bottom, 0px)); }
.comment-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
  margin-bottom: 12px;
}
.comment {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border);
}
.c-avatar {
  width: 38px;
  height: 38px;
  border-radius: 30%;
  display: grid;
  place-items: center;
  font-size: 20px;
  background: var(--color-sage-soft);
  flex-shrink: 0;
}
.c-body { flex: 1; }
.c-name { font-weight: 700; font-size: 14px; }
.c-text { font-size: 14px; color: var(--color-ink-2); line-height: 1.55; margin: 2px 0; }
.c-time { font-size: 11px; color: var(--color-faint); }
.c-like {
  color: var(--color-muted);
  align-self: center;
  transition: color var(--dur-fast), transform var(--dur-fast) var(--ease-out);
}
.c-like.on { color: var(--color-accent); }
.c-like:active { transform: scale(0.85); }

.comment-compose {
  display: flex;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}
.cc-input {
  flex: 1;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  border-radius: var(--radius-pill);
  padding: 11px 16px;
  font-size: 15px;
  color: var(--color-ink);
  outline: none;
}
.cc-input:focus-visible { border-color: var(--color-accent); }
.cc-send {
  padding: 0 18px;
  border-radius: var(--radius-pill);
  background: var(--color-ink);
  color: var(--color-surface);
  font-weight: 700;
  font-size: 14px;
  transition: opacity var(--dur-fast);
}
.cc-send:disabled { opacity: 0.4; }

.sheet-enter-active, .sheet-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.sheet-enter-from, .sheet-leave-to { opacity: 0; }
.sheet-enter-active .sheet, .sheet-leave-active .sheet { transition: transform var(--dur-base) var(--ease-out); }
.sheet-enter-from .sheet, .sheet-leave-to .sheet { transform: translateY(100%); }
</style>
