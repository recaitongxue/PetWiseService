<template>
  <section>
    <div class="toolbar" v-reveal>
      <span class="count-chip">已上线 {{ activeCount }} 条公告</span>
      <button class="btn sm primary" @click="openForm"><AppIcon name="plus" :size="14" /> 新建公告</button>
    </div>

    <!-- 新建/编辑表单 -->
    <div v-if="editing" class="card form" v-reveal>
      <h3 class="form-title">{{ form.id ? '编辑公告' : '新建公告' }}</h3>
      <div class="field-row">
        <label class="field">
          <span class="field-label">标题</span>
          <input v-model="form.title" type="text" placeholder="一句话说清这条公告" />
        </label>
        <label class="field narrow">
          <span class="field-label">级别</span>
          <select v-model="form.level">
            <option value="event">活动</option>
            <option value="info">通知</option>
            <option value="warn">提醒</option>
          </select>
        </label>
      </div>
      <label class="field">
        <span class="field-label">正文</span>
        <textarea v-model="form.body" rows="3" placeholder="公告正文，将在 App 首页展示"></textarea>
      </label>
      <div class="form-actions">
        <button class="btn sm ghost" @click="editing = false">取消</button>
        <button class="btn sm primary" :disabled="saving || !form.title || !form.body" @click="save">发布公告</button>
      </div>
    </div>

    <div class="ann-list">
      <article v-for="a in rows" :key="a.id" class="card ann" v-reveal>
        <span class="level-dot" :class="a.level"></span>
        <div class="ann-main">
          <div class="ann-head">
            <b>{{ a.title }}</b>
            <span class="badge" :class="levelBadge(a.level)">{{ levelLabel(a.level) }}</span>
            <span v-if="a.pinned" class="badge neutral">置顶</span>
            <span class="date num">{{ a.date }}</span>
          </div>
          <p class="ann-text">{{ a.content }}</p>
        </div>
        <div class="ann-actions">
          <button class="btn sm" :class="a.pinned ? 'ghost' : 'primary'" @click="toggle(a)">
            {{ a.pinned ? '取消置顶' : '置顶' }}
          </button>
          <button class="btn sm danger" @click="remove(a)"><AppIcon name="x" :size="13" /></button>
        </div>
      </article>
      <p v-if="!rows.length" class="empty">还没有公告，点击右上角新建</p>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { adminApi } from '@/api'
import { showToast } from '@shared/toast'

const rows = ref([])
const editing = ref(false)
const saving = ref(false)
const form = reactive({ id: '', title: '', body: '', level: 'event', pinned: false })

// 后端公告没有「下线」标志，列表返回的都是已发布公告
const activeCount = computed(() => rows.value.length)

async function load() {
  try {
    // 分页信封：数组在 res.list
    const res = await adminApi.announcements({ page: 1, page_size: 50 })
    rows.value = res?.list ?? []
  } catch (e) {
    showToast(e?.message || '公告加载失败', { type: 'warn' })
  }
}
onMounted(load)

function openForm() {
  Object.assign(form, { id: '', title: '', body: '', level: 'event', pinned: false })
  editing.value = true
}

async function save() {
  if (!form.title.trim() || !form.body.trim()) return
  saving.value = true
  try {
    const payload = {
      title: form.title.trim(),
      content: form.body.trim(),
      level: form.level,
      pinned: form.pinned
    }
    if (form.id) {
      await adminApi.updateAnnouncement(form.id, payload)
    } else {
      await adminApi.createAnnouncement(payload)
    }
    editing.value = false
    showToast('公告已发布，App 首页将同步展示', { type: 'success' })
    await load()
  } catch (e) {
    showToast(e?.message || '公告保存失败', { type: 'warn' })
  } finally {
    saving.value = false
  }
}

async function toggle(a) {
  const pinned = !a.pinned
  try {
    await adminApi.updateAnnouncement(a.id, { pinned })
    showToast(pinned ? '公告已置顶' : '公告已取消置顶')
    await load()
  } catch (e) {
    showToast(e?.message || '操作失败', { type: 'warn' })
  }
}

async function remove(a) {
  try {
    await adminApi.removeAnnouncement(a.id)
    showToast('公告已删除')
    await load()
  } catch (e) {
    showToast(e?.message || '删除失败', { type: 'warn' })
  }
}

function levelBadge(l) {
  return { event: 'good', info: 'neutral', warn: 'watch' }[l] || 'neutral'
}
function levelLabel(l) {
  return { event: '活动', info: '通知', warn: '提醒' }[l] || l
}
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.count-chip {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-muted);
}
.form { margin-bottom: 16px; }
.form-title {
  font-family: var(--font-display);
  font-size: 16px;
  margin-bottom: 14px;
}
.field-row { display: flex; gap: 12px; }
.field { display: flex; flex-direction: column; gap: 6px; flex: 1; margin-bottom: 12px; }
.field.narrow { flex: 0 0 140px; }
.field-label { font-size: 12px; font-weight: 700; color: var(--color-faint); }
.field input,
.field textarea,
.field select {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  font-size: 14px;
  font-family: inherit;
  background: var(--color-surface);
  color: var(--color-ink);
  resize: vertical;
}
.form-actions { display: flex; justify-content: flex-end; gap: 8px; }
.ann-list { display: flex; flex-direction: column; gap: 12px; }
.ann { display: flex; align-items: flex-start; gap: 14px; }
.level-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  margin-top: 8px;
  flex-shrink: 0;
  background: var(--color-accent);
}
.level-dot.event { background: var(--color-good); }
.level-dot.info { background: var(--color-muted); }
.level-dot.warn { background: #d9922f; }
.ann-main { flex: 1; min-width: 0; }
.ann-head { display: flex; align-items: center; gap: 9px; }
.ann-head b { font-size: 14.5px; }
.date { font-size: 12px; color: var(--color-faint); margin-left: auto; }
.ann-text {
  margin-top: 6px;
  font-size: 13.5px;
  line-height: 1.6;
  color: var(--color-ink-2);
}
.ann-actions { display: flex; gap: 8px; flex-shrink: 0; }
.empty { text-align: center; color: var(--color-muted); padding: 26px 0; font-size: 14px; }
</style>
