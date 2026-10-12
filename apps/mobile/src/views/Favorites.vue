<template>
  <section class="screen">
    <header class="f-head">
      <button class="back" type="button" @click="goBack" aria-label="返回">
        <AppIcon name="back" :size="22" />
      </button>
      <span class="f-title">我的收藏</span>
      <span class="back"></span>
    </header>

    <div class="filters" v-reveal>
      <button
        v-for="t in tabs"
        :key="t.key"
        class="f-chip"
        :class="{ on: tab === t.key }"
        type="button"
        @click="tab = t.key"
      >{{ t.label }}</button>
    </div>

    <div v-if="rows.length" class="list" v-reveal="{ delay: 60 }">
      <router-link v-for="f in rows" :key="f.id" :to="f.to" class="fav">
        <span class="fav-ic" :class="f.kind"><AppIcon :name="iconOf(f.kind)" :size="17" /></span>
        <div class="fav-body">
          <span class="fav-title">{{ f.title }}</span>
          <span class="fav-desc">{{ f.desc }}</span>
        </div>
        <button
          class="fav-remove"
          type="button"
          aria-label="取消收藏"
          @click.prevent="remove(f.id)"
        >
          <AppIcon name="x" :size="15" />
        </button>
      </router-link>
    </div>

    <p v-else class="empty">这个分类下还没有收藏。</p>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import { favorites } from '@/data/mock'
import { showToast } from '@/composables/toast'

const router = useRouter()
function goBack() {
  router.back()
}

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'breed', label: '品种百科' },
  { key: 'post', label: '社区帖子' },
  { key: 'tip', label: '护理贴士' }
]
const tab = ref('all')
const removed = ref([])

const rows = computed(() => {
  const list = favorites.filter((f) => !removed.value.includes(f.id))
  return tab.value === 'all' ? list : list.filter((f) => f.kind === tab.value)
})

function iconOf(kind) {
  return { breed: 'search', post: 'paw', tip: 'sparkle' }[kind] || 'bookmark'
}

function remove(id) {
  removed.value.push(id)
  showToast('已取消收藏')
}
</script>

<style scoped>
.f-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0 12px;
}
.back { width: 40px; height: 40px; display: grid; place-items: center; border-radius: 50%; }
.f-title { font-family: var(--font-display); font-weight: 700; font-size: var(--fs-lg); }

.filters { display: flex; gap: 8px; margin-bottom: 18px; }
.f-chip {
  padding: 7px 14px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--hairline);
  font-size: 13px;
  font-weight: 700;
  color: var(--color-muted);
  transition: all var(--dur-fast) var(--ease-out);
}
.f-chip.on {
  color: var(--color-ink);
  background: var(--color-surface);
  border-color: var(--hairline-strong);
  box-shadow: var(--shadow-soft);
}

.list { display: flex; flex-direction: column; gap: 10px; }
.fav {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
  transition: transform var(--dur-fast) var(--ease-out);
}
.fav:active { transform: scale(0.978); }
.fav-ic {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  flex-shrink: 0;
  background: var(--color-sage-soft);
  color: var(--color-good);
}
.fav-ic.breed { background: var(--color-surface-2); color: var(--color-muted); }
.fav-ic.tip { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.fav-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.fav-title { font-weight: 700; font-size: 15px; }
.fav-desc {
  font-size: 12px;
  color: var(--color-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.fav-remove {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--color-faint);
}
.fav-remove:active { background: var(--color-accent-soft); color: var(--color-accent-ink); }

.empty { text-align: center; color: var(--color-muted); font-size: 14px; margin-top: 48px; }
</style>
