<template>
  <section>
    <div class="toolbar" v-reveal>
      <label class="search">
        <AppIcon name="search" :size="16" />
        <input v-model.trim="kw" type="search" placeholder="搜索用户 / 主题…" />
      </label>
      <span class="tip-chip">
        <AppIcon name="stethoscope" :size="13" /> 转人工 1 条待跟进
      </span>
    </div>

    <article class="card" v-reveal="{ delay: 60 }">
      <table class="table">
        <thead>
          <tr>
            <th>编号</th><th>用户</th><th>宠物</th><th>问诊主题</th><th>对话轮次</th><th>模型</th><th>时间</th><th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in list" :key="c.id">
            <td class="num muted">{{ c.id }}</td>
            <td>{{ c.user }}</td>
            <td>{{ c.pet }}</td>
            <td><b>{{ c.topic }}</b></td>
            <td class="num">{{ c.turns }}</td>
            <td><span class="model">{{ c.model }}</span></td>
            <td class="num muted">{{ c.time }}</td>
            <td>
              <span class="badge" :class="c.state === 'transferred' ? 'watch' : 'good'">
                {{ c.state === 'transferred' ? '已转人工' : '已完成' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!list.length" class="empty">没有匹配的问诊记录</p>
    </article>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { consults } from '@/data/admin'

const kw = ref('')
const list = computed(() =>
  consults.filter((c) => !kw.value || c.user.includes(kw.value) || c.topic.includes(kw.value))
)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.tip-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #a66e14;
  background: #f7e8cb;
  padding: 7px 13px;
  border-radius: var(--radius-pill);
}
.muted { color: var(--color-faint); }
.model {
  font-size: 12px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-2);
  color: var(--color-ink-2);
}
.empty { text-align: center; color: var(--color-muted); padding: 26px 0; font-size: 14px; }
</style>
