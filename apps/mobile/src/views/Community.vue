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
        @more="openMore(p)"
        @share="share(p)"
      />
    </div>

    <p v-if="!visiblePosts.length" class="empty">这个话题下还没有动态，换个看看？</p>

    <button class="load-more" type="button" @click="loadMore">加载更多动态</button>

    <!-- 发布 FAB -->
    <button class="fab" type="button" @click="openCompose" aria-label="发布动态">
      <AppIcon name="plus" :size="26" />
    </button>

    <!-- 发布底部弹层：文字 + 图片 + 视频 + 表情 + 话题 -->
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

          <!-- 表情包 -->
          <div class="emoji-bar">
            <button
              v-for="e in emojis"
              :key="e"
              class="emoji"
              type="button"
              @click="draft += e"
            >{{ e }}</button>
          </div>

          <div class="sheet-gallery-label">添加图片（最多 3 张）</div>
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

          <div class="sheet-gallery-label">添加视频</div>
          <div class="video-row">
            <button
              class="v-pick"
              :class="{ on: draftVideo }"
              type="button"
              @click="draftVideo = !draftVideo"
            >
              <AppIcon name="video" :size="18" />
              {{ draftVideo ? '已选择 1 段视频' : '从相册选择视频' }}
            </button>
            <span class="v-tip">视频将作为动态首图，带时长标识</span>
          </div>

          <div class="sheet-gallery-label">参与话题</div>
          <div class="topic-picks">
            <button
              v-for="t in topics"
              :key="t"
              class="topic-pick"
              :class="{ on: draftTopic === t }"
              type="button"
              @click="draftTopic = draftTopic === t ? '' : t"
            >#{{ t }}</button>
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
          <div class="emoji-bar compact">
            <button
              v-for="e in emojis"
              :key="e"
              class="emoji"
              type="button"
              @click="commentDraft += e"
            >{{ e }}</button>
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

    <!-- 帖子更多操作 -->
    <transition name="sheet">
      <div v-if="morePost" class="sheet-mask" @click.self="morePost = null">
        <div class="sheet actions">
          <div class="sheet-grip" aria-hidden="true"></div>
          <p class="act-title">{{ morePost.author }} 的动态</p>
          <button class="act-row" type="button" @click="favorite(morePost)">
            <AppIcon name="bookmark" :size="17" />
            收藏这条动态
          </button>
          <button class="act-row" type="button" @click="share(morePost); morePost = null">
            <AppIcon name="share" :size="17" />
            分享给朋友
          </button>
          <button class="act-row" type="button" @click="notInterested(morePost)">
            <AppIcon name="x" :size="17" />
            不感兴趣，减少此类推荐
          </button>
          <button class="act-row danger" type="button" @click="openReport(morePost)">
            <AppIcon name="alert" :size="17" />
            举报
          </button>
        </div>
      </div>
    </transition>

    <!-- 举报理由 -->
    <transition name="sheet">
      <div v-if="reportPost" class="sheet-mask" @click.self="reportPost = null">
        <div class="sheet actions">
          <div class="sheet-grip" aria-hidden="true"></div>
          <p class="act-title">举报理由（提交后由平台审核）</p>
          <button
            v-for="r in reportReasons"
            :key="r"
            class="act-row"
            type="button"
            @click="submitReport(r)"
          >{{ r }}</button>
          <button class="act-row ghost" type="button" @click="reportPost = null">取消</button>
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
import { reportPost as saveReport, addFavorite } from '@/data/ops'
import { showToast } from '@/composables/toast'

const tab = ref('recommend')
const topics = ['成长记录', '健康管理', '柯基', '英短', '换季护理', '线下撸猫']
const activeTopic = ref(null)
const posts = ref([...feed])
const hidden = ref([])

const emojis = ['🐱', '🐶', '😻', '🥺', '😭', '🤤', '👍', '🎉', '🐾', '❤️', '😴', '✨']

const visiblePosts = computed(() => {
  let list = posts.value.filter((p) => !hidden.value.includes(p.id))
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

/* ---------- 发布 ---------- */

const composing = ref(false)
const draft = ref('')
const draftImages = ref([])
const draftVideo = ref(false)
const draftTopic = ref('')

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
  const hasVideo = draftVideo.value
  const tags = ['#我的日常']
  if (draftTopic.value) tags.unshift('#' + draftTopic.value)
  posts.value.unshift({
    id: 'mine' + Date.now(),
    author: user.name,
    species: 'cat',
    time: '刚刚',
    text: draft.value.trim(),
    images: [...draftImages.value],
    videos: hasVideo ? 1 : 0,
    videoDuration: '00:12',
    tags,
    likes: 0,
    comments: 0,
    liked: false
  })
  draft.value = ''
  draftImages.value = []
  draftVideo.value = false
  draftTopic.value = ''
  composing.value = false
  tab.value = 'recommend'
  activeTopic.value = null
  showToast(hasVideo ? '已发布（含 1 段视频）' : '已发布到社区', { type: 'success' })
}

/* ---------- 评论 ---------- */

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

/* ---------- 更多操作 / 举报 / 收藏 ---------- */

const morePost = ref(null)
const reportPost = ref(null)
const reportReasons = ['广告或垃圾信息', '辱骂攻击', '血腥暴力', '违法违规', '侵犯权益', '其他']

function openMore(post) {
  morePost.value = post
}

function favorite(post) {
  morePost.value = null
  const ok = addFavorite({
    id: 'post-' + post.id,
    kind: 'post',
    title: post.author + '的动态',
    desc: post.text.slice(0, 30),
    to: '/community'
  })
  showToast(ok ? '已收藏，可在「我的-收藏」查看' : '这条动态已在收藏里', {
    type: ok ? 'success' : 'info'
  })
}

function share(post) {
  showToast('链接已复制，去微信粘贴给朋友', { type: 'success' })
}

function notInterested(post) {
  hidden.value.push(post.id)
  morePost.value = null
  showToast('将减少此类推荐', { type: 'info' })
}

function openReport(post) {
  morePost.value = null
  reportPost.value = post
}

function submitReport(reason) {
  const p = reportPost.value
  saveReport({ postId: p.id, author: p.author, reason })
  reportPost.value = null
  showToast('已提交举报，平台会尽快审核', { type: 'success' })
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
  bottom: calc(var(--dock-h) + 16px + env(safe-area-inset-bottom, 0px));
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

/* 弹层通用 */
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
.sheet.actions { padding-top: 10px; }
.sheet-grip {
  width: 38px;
  height: 4px;
  border-radius: 999px;
  background: var(--color-border-strong);
  margin: 0 auto 14px;
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

/* 表情包 */
.emoji-bar {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  scrollbar-width: none;
  margin: 12px 0 4px;
  padding-bottom: 2px;
}
.emoji-bar::-webkit-scrollbar { display: none; }
.emoji-bar.compact { margin: 0 0 10px; }
.emoji {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  font-size: 19px;
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  transition: transform var(--dur-fast) var(--ease-out);
}
.emoji:active { transform: scale(0.85); }

.sheet-gallery-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-muted);
  margin: 14px 0 10px;
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

.video-row { display: flex; align-items: center; gap: 10px; }
.v-pick {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 11px 16px;
  border-radius: var(--radius-md);
  border: 1px dashed var(--hairline-strong);
  background: var(--color-surface);
  font-size: 13.5px;
  font-weight: 700;
  color: var(--color-ink-2);
}
.v-pick.on {
  border-style: solid;
  border-color: var(--color-accent);
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
}
.v-tip { font-size: 11px; color: var(--color-faint); }

.topic-picks { display: flex; flex-wrap: wrap; gap: 8px; }
.topic-pick {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-sage);
  background: var(--color-sage-soft);
  padding: 7px 13px;
  border-radius: var(--radius-pill);
}
.topic-pick.on { background: var(--color-sage); color: var(--color-surface); font-weight: 700; }

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

/* 更多操作 / 举报 */
.act-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-muted);
  text-align: center;
  margin-bottom: 12px;
}
.act-row {
  display: flex;
  align-items: center;
  gap: 11px;
  width: 100%;
  padding: 15px 14px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 8px;
  text-align: left;
  transition: transform var(--dur-fast) var(--ease-out);
}
.act-row:active { transform: scale(0.985); }
.act-row.danger { color: var(--color-alert); }
.act-row.ghost {
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--color-muted);
  font-weight: 700;
}

.sheet-enter-active, .sheet-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.sheet-enter-from, .sheet-leave-to { opacity: 0; }
.sheet-enter-active .sheet, .sheet-leave-active .sheet { transition: transform var(--dur-base) var(--ease-out); }
.sheet-enter-from .sheet, .sheet-leave-to .sheet { transform: translateY(100%); }
</style>
