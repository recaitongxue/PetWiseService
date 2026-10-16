<template>
  <article class="post" v-reveal>
    <header class="post-head">
      <span v-if="post.species" class="post-avatar">
        <PetAvatar :species="post.species" :name="post.author" :size="44" />
      </span>
      <span v-else class="post-avatar mono">{{ initial }}</span>
      <div class="post-meta">
        <span class="post-name">{{ post.author }}</span>
        <span class="post-time">{{ post.time }}</span>
      </div>
      <button class="post-more" type="button" aria-label="更多操作" @click="$emit('more', post)">
        <AppIcon name="filter" :size="16" />
      </button>
    </header>

    <p class="post-text">{{ post.text }}</p>

    <div v-if="post.images.length" class="post-grid" :class="'g' + post.images.length">
      <div
        v-for="(img, i) in post.images"
        :key="i"
        class="post-img"
        :class="isUrl(img) ? 'url' : 'tone-' + img"
        :style="isUrl(img) ? { backgroundImage: `url(${img})` } : null"
      >
        <AppIcon name="paw" :size="post.images.length === 1 ? 64 : 36" class="img-mark" />
      </div>
    </div>

    <div v-if="post.tags.length" class="post-tags">
      <span v-for="t in post.tags" :key="t" class="tag-chip">{{ t }}</span>
    </div>

    <footer class="post-actions">
      <button
        class="act"
        :class="{ liked: localLiked }"
        type="button"
        @click="toggleLike"
        :aria-label="localLiked ? '取消点赞' : '点赞'"
      >
        <span class="like-ic" :class="{ pop: localLiked }">
          <AppIcon :name="localLiked ? 'heart' : 'heart-o'" :size="18" />
        </span>
        <span class="num">{{ localLikes }}</span>
      </button>
      <button class="act" type="button" aria-label="评论" @click="$emit('comment', post)">
        <AppIcon name="comment" :size="18" />
        <span class="num">{{ post.comments }}</span>
      </button>
      <button class="act" type="button" aria-label="分享" @click="$emit('share', post)">
        <AppIcon name="share" :size="18" />
      </button>
    </footer>
  </article>
</template>

<script setup>
import { ref, computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import { togglePostLike } from '@/api/data'

const props = defineProps({
  post: { type: Object, required: true }
})
defineEmits(['comment', 'more', 'share'])

const localLiked = ref(props.post.liked)
const localLikes = ref(props.post.likes)

// 图片项：后端返回真实 URL，兼容历史色调名
function isUrl(v) {
  return typeof v === 'string' && /^(https?:)?\/\/|^data:|^\/|^[\w.-]+\.(png|jpe?g|gif|webp|svg)/i.test(v)
}

// 点赞：单端点切换；先本地乐观更新，再用服务端返回的权威状态校正
async function toggleLike() {
  const prev = localLiked.value
  const prevLikes = localLikes.value
  localLiked.value = !prev
  localLikes.value = prevLikes + (localLiked.value ? 1 : -1)
  try {
    const res = await togglePostLike(props.post.id)
    if (res && typeof res.liked === 'boolean') localLiked.value = res.liked
    if (res && typeof res.likes === 'number') localLikes.value = res.likes
  } catch {
    localLiked.value = prev
    localLikes.value = prevLikes
  }
}

const initial = computed(() => (props.post.author || '?').slice(0, 1))
</script>

<style scoped>
.post {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 18px;
  box-shadow: var(--shadow-soft);
  margin-bottom: 18px;
}
.post-head {
  display: flex;
  align-items: center;
  gap: 12px;
}
.post-avatar {
  width: 44px;
  height: 44px;
  border-radius: 30%;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 19px;
  color: var(--color-ink);
  background: var(--grad-sand);
  flex-shrink: 0;
  overflow: hidden;
}
.post-meta {
  display: flex;
  flex-direction: column;
  flex: 1;
}
.post-name {
  font-weight: 700;
  font-size: 15px;
}
.post-time {
  font-size: 12px;
  color: var(--color-muted);
}
.post-more {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--color-faint);
  flex-shrink: 0;
}
.post-more:active { background: var(--color-surface-2); color: var(--color-ink); }
.post-text {
  margin: 12px 0;
  font-size: 15px;
  line-height: 1.65;
  color: var(--color-ink-2);
}
.post-grid {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
}
.post-grid.g1 {
  grid-template-columns: 1fr;
}
.post-grid.g1 .post-img {
  aspect-ratio: 4 / 3;
}
.post-grid.g2,
.post-grid.g3 {
  grid-template-columns: repeat(3, 1fr);
}
.post-img {
  aspect-ratio: 1;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  overflow: hidden;
  position: relative;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.25);
}
.post-img::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(120% 80% at 20% 0%, rgba(255, 255, 255, 0.35), transparent 55%);
  pointer-events: none;
}
.post-img.tone-sage { background: var(--grad-sage); }
.post-img.tone-peach { background: var(--grad-peach); }
.post-img.tone-ink { background: var(--grad-ink); }
.post-img.tone-coral { background: var(--grad-coral); }
.post-img.tone-sand { background: var(--grad-sand); }
/* 真实图片：以 URL 作为背景铺满，隐藏示意爪印 */
.post-img.url {
  background-size: cover;
  background-position: center;
  background-color: var(--color-surface-2);
}
.post-img.url .img-mark { display: none; }
.img-mark {
  color: rgba(255, 255, 255, 0.32);
  position: relative;
  z-index: 1;
}
.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
}
.tag-chip {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-sage);
  background: var(--color-sage-soft);
  padding: 4px 10px;
  border-radius: var(--radius-pill);
}
.post-actions {
  display: flex;
  gap: 22px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}
.act {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-muted);
  font-size: 13px;
  font-weight: 600;
  transition: color var(--dur-fast), transform var(--dur-fast) var(--ease-out);
}
.act:active {
  transform: scale(0.9);
}
.act.liked {
  color: var(--color-accent);
}
.like-ic {
  display: inline-grid;
  place-items: center;
}
.like-ic.pop {
  animation: like-pop 0.4s var(--ease-out);
}
@keyframes like-pop {
  0% { transform: scale(1); }
  35% { transform: scale(1.35); }
  60% { transform: scale(0.9); }
  100% { transform: scale(1); }
}
@media (prefers-reduced-motion: reduce) {
  .like-ic.pop { animation: none; }
}
</style>
