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

          <div class="sheet-gallery-label">添加图片（最多 3 张，真实上传）</div>
          <div class="sheet-gallery">
            <template v-if="draftImages.length">
              <div v-for="(url, i) in draftImages" :key="i" class="g-item url" :style="{ backgroundImage: `url(${url})` }">
                <button class="g-remove" type="button" aria-label="移除图片" @click="draftImages.splice(i, 1)">×</button>
              </div>
            </template>
            <button v-if="draftImages.length < 3" class="g-item g-add" type="button" @click="pickPostImages">
              <AppIcon name="plus" :size="22" />
            </button>
          </div>
          <input
            ref="postImgInput"
            class="file-input"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            multiple
            @change="onPostImagesPicked"
          />

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
import { ref, computed, onMounted } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import PostCard from '@/components/PostCard.vue'
import {
  fetchFeed, fetchUser, fetchPostComments, publishPost,
  commentPost as sendPostComment, reportPost as submitPostReport, addFavorite
} from '@/api/data'
import { fileApi } from '@/api'
import { showToast } from '@shared/toast'

const topics = ['成长记录', '健康管理', '柯基', '英短', '换季护理', '线下撸猫']
const activeTopic = ref(null)
const posts = ref([])
const hidden = ref([])
const me = ref({ name: '' })

const emojis = ['🐱', '🐶', '😻', '🥺', '😭', '🤤', '👍', '🎉', '🐾', '❤️', '😴', '✨']

const visiblePosts = computed(() => {
  let list = posts.value.filter((p) => !hidden.value.includes(p.id))
  if (activeTopic.value) {
    // 后端 tags 不带 '#' 前缀（mock 时代带），比较时统一去掉
    const tag = activeTopic.value.replace(/^#/, '')
    list = list.filter((p) => (p.tags || []).some((t) => String(t).replace(/^#/, '') === tag))
  }
  return list
})

/* ---------- 加载 / 分页 ---------- */

const page = ref(1)
const hasMore = ref(true)
const loading = ref(false)

async function load(reset = true) {
  if (loading.value) return
  loading.value = true
  try {
    const next = reset ? 1 : page.value + 1
    const list = await fetchFeed({ page: next, page_size: 20 })
    posts.value = reset ? list : [...posts.value, ...list]
    page.value = next
    hasMore.value = (list || []).length >= 20
  } catch (e) {
    showToast(e?.message || '动态加载失败', { type: 'error' })
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (!hasMore.value) return showToast('没有更多动态了', { type: 'info' })
  await load(false)
}

/* ---------- 发布 ---------- */

const composing = ref(false)
const draft = ref('')
const draftImages = ref([]) // 真实上传后的 URL 列表（最多 3 张）
const draftTopic = ref('')
const postImgInput = ref(null)
const uploading = ref(false)
const MAX_POST_IMAGES = 3
const MAX_IMAGE_MB = 8

function openCompose() {
  composing.value = true
}
function closeCompose() {
  composing.value = false
}
function pickPostImages() {
  postImgInput.value?.click()
}
async function onPostImagesPicked(e) {
  const files = Array.from(e.target.files || [])
  e.target.value = ''
  if (!files.length) return
  const room = MAX_POST_IMAGES - draftImages.value.length
  const picked = files.slice(0, room)
  uploading.value = true
  try {
    for (const f of picked) {
      if (!f.type.startsWith('image/')) {
        showToast('只能选择图片文件', { type: 'warn' })
        continue
      }
      if (f.size > MAX_IMAGE_MB * 1024 * 1024) {
        showToast(`「${f.name}」超过 ${MAX_IMAGE_MB}MB，已跳过`, { type: 'warn' })
        continue
      }
      const fd = new FormData()
      fd.append('file', f)
      const up = await fileApi.upload(fd, 'post')
      if (up?.url) draftImages.value.push(up.url)
    }
  } catch (err) {
    showToast(err?.message || '图片上传失败', { type: 'error' })
  } finally {
    uploading.value = false
  }
}
async function publish() {
  if (!draft.value.trim()) return
  const tags = ['我的日常']
  if (draftTopic.value) tags.unshift(draftTopic.value)
  try {
    const created = await publishPost({
      text: draft.value.trim(),
      images: [...draftImages.value],
      tags
    })
    posts.value.unshift(created)
    showToast('已发布到社区', { type: 'success' })
  } catch (e) {
    showToast(e?.message || '发布失败', { type: 'error' })
    return
  }
  draft.value = ''
  draftImages.value = []
  draftTopic.value = ''
  composing.value = false
  activeTopic.value = null
}

/* ---------- 评论 ---------- */

const commentPost = ref(null)
const commentList = ref([])
const commentDraft = ref('')

async function openComments(post) {
  commentPost.value = post
  commentList.value = []
  try {
    commentList.value = await fetchPostComments(post.id)
  } catch (e) {
    showToast(e?.message || '评论加载失败', { type: 'error' })
  }
}
function closeComments() {
  commentPost.value = null
  commentDraft.value = ''
}
function toggleCommentLike(i) {
  const c = commentList.value[i]
  if (c) c.liked = !c.liked
}
async function sendComment() {
  const text = commentDraft.value.trim()
  if (!text || !commentPost.value) return
  const post = commentPost.value
  try {
    const created = await sendPostComment(post.id, text)
    commentList.value.push(created || { name: me.value.name, text, time: '刚刚', liked: false })
    commentDraft.value = ''
    post.comments = (post.comments || 0) + 1
  } catch (e) {
    showToast(e?.message || '评论发送失败', { type: 'error' })
  }
}

/* ---------- 更多操作 / 举报 / 收藏 ---------- */

const morePost = ref(null)
const reportPost = ref(null)
const reportReasons = ['广告或垃圾信息', '辱骂攻击', '血腥暴力', '违法违规', '侵犯权益', '其他']

function openMore(post) {
  morePost.value = post
}

async function favorite(post) {
  morePost.value = null
  try {
    await addFavorite('post', post.id, {
      title: post.author + '的动态',
      desc: (post.text || '').slice(0, 30),
      route: '/community'
    })
    showToast('已收藏，可在「我的-收藏」查看', { type: 'success' })
  } catch (e) {
    showToast(e?.message || '收藏失败', { type: 'error' })
  }
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

async function submitReport(reason) {
  const p = reportPost.value
  if (!p) return
  try {
    await submitPostReport(p.id, { reason })
    showToast('已提交举报，平台会尽快审核', { type: 'success' })
  } catch (e) {
    showToast(e?.message || '举报提交失败', { type: 'error' })
  }
  reportPost.value = null
}

function initial(name) {
  return (name || '?').slice(0, 1)
}

onMounted(async () => {
  try {
    me.value = (await fetchUser()) || { name: '' }
  } catch {
    me.value = { name: '' }
  }
  load(true)
})
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
  grid-template-columns: repeat(3, 1fr);
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
  background-size: cover;
  background-position: center;
  transition: transform var(--dur-fast) var(--ease-out), border-color var(--dur-fast);
}
.g-item:active { transform: scale(0.9); }
.g-add {
  display: grid;
  place-items: center;
  color: var(--color-muted);
  border-style: dashed;
  border-color: var(--hairline-strong);
  cursor: pointer;
}
.g-remove {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 13px;
  line-height: 1;
  cursor: pointer;
}
.file-input { display: none; }

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
