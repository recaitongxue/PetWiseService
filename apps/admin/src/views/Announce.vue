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
        <button class="btn sm primary" :disabled="!form.title || !form.body" @click="save">发布公告</button>
      </div>
    </div>

    <div class="ann-list">
      <article v-for="a in rows" :key="a.id" class="card ann" v-reveal>
        <span class="level-dot" :class="a.level"></span>
        <div class="ann-main">
          <div class="ann-head">
            <b>{{ a.title }}</b>
            <span class="badge" :class="levelBadge(a.level)">{{ levelLabel(a.level) }}</span>
            <span class="date num">{{ a.date }}</span>
          </div>
          <p class="ann-text">{{ a.body }}</p>
        </div>
        <div class="ann-actions">
          <button class="btn sm" :class="a.active ? 'ghost' : 'primary'" @click="toggle(a)">
            {{ a.active ? '下线' : '上线' }}
          </button>
          <button class="btn sm danger" @click="remove(a)"><AppIcon name="x" :size="13" /></button>
        </div>
      </article>
      <p v-if="!rows.length" class="empty">还没有公告，点击右上角新建</p>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { loadAnnouncements, saveAnnouncements } from '@/data/ops'
import { showToast } from '@/composables/toast'

const rows = ref(loadAnnouncements())
const editing = ref(false)
const form = reactive({ id: '', title: '', body: '', level: 'event', date: '', active: true })

const activeCount = computed(() => rows.value.filter((a) => a.active).length)

function persist() {
  saveAnnouncements(rows.value.map((a) => ({ ...a })))
}

function openForm() {
  Object.assign(form, { id: '', title: '', body: '', level: 'event', date: '', active: true })
  editing.value = true
}

function save() {
  const today = new Date().toISOString().slice(0, 10)
  if (form.id) {
    const hit = rows.value.find((a) => a.id === form.id)
    Object.assign(hit, { title: form.title, body: form.body, level: form.level })
  } else {
    rows.value.unshift({ id: 'a' + Date.now(), title: form.title, body: form.body, level: form.level, date: today, active: true })
  }
  persist()
  editing.value = false
  showToast('公告已发布，App 首页将同步展示', { type: 'success' })
}

function toggle(a) {
  a.active = !a.active
  persist()
  showToast(a.active ? '公告已上线' : '公告已下线，App 端不再展示')
}

function remove(a) {
  rows.value = rows.value.filter((x) => x.id !== a.id)
  persist()
  showToast('公告已删除')
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
