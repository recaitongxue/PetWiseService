<template>
  <section>
    <div class="toolbar" v-reveal>
      <label class="search">
        <AppIcon name="search" :size="16" />
        <input v-model.trim="kw" type="search" placeholder="搜索用户 / 品种…" />
      </label>
      <span class="tip-chip">
        <AppIcon name="eye" :size="13" /> 置信度低于 0.60 自动标记复核
      </span>
    </div>

    <article class="card" v-reveal="{ delay: 60 }">
      <table class="table">
        <thead>
          <tr>
            <th>编号</th><th>用户</th><th>宠物</th><th>识别结果</th><th>置信度</th><th>时间</th><th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in list" :key="r.id">
            <td class="num muted">{{ r.id }}</td>
            <td>{{ r.user }}</td>
            <td>{{ r.pet }}</td>
            <td><b>{{ r.breed }}</b></td>
            <td>
              <span class="conf-track">
                <span class="conf-bar" :style="{ width: r.conf * 100 + '%' }" :class="confState(r.conf)"></span>
              </span>
              <b class="num conf-num">{{ Math.round(r.conf * 100) }}%</b>
            </td>
            <td class="num muted">{{ r.time }}</td>
            <td>
              <span class="badge" :class="badgeOf(r.state)">{{ stateLabel(r.state) }}</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!list.length" class="empty">没有匹配的记录</p>
    </article>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { recognitions } from '@/data/admin'

const kw = ref('')
const list = computed(() =>
  recognitions.filter((r) => !kw.value || r.user.includes(kw.value) || r.breed.includes(kw.value))
)

function confState(c) {
  if (c >= 0.85) return 'good'
  if (c >= 0.6) return 'mid'
  return 'low'
}
function badgeOf(s) {
  return { done: 'good', review: 'watch', failed: 'alert' }[s] || 'neutral'
}
function stateLabel(s) {
  return { done: '已完成', review: '待复核', failed: '识别失败' }[s] || s
}
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
  color: var(--color-muted);
  background: var(--color-surface-2);
  padding: 7px 13px;
  border-radius: var(--radius-pill);
}
.muted { color: var(--color-faint); }
.conf-track {
  display: inline-block;
  width: 90px;
  height: 8px;
  border-radius: 999px;
  background: var(--color-surface-2);
  overflow: hidden;
  vertical-align: middle;
  margin-right: 8px;
}
.conf-bar { display: block; height: 100%; border-radius: 999px; }
.conf-bar.good { background: var(--color-good); }
.conf-bar.mid { background: var(--color-sage); }
.conf-bar.low { background: var(--color-alert); }
.conf-num { font-size: 13px; }
.empty { text-align: center; color: var(--color-muted); padding: 26px 0; font-size: 14px; }
</style>
