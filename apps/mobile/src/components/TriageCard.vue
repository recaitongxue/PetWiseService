<template>
  <article class="triage" :class="level">
    <header class="t-head">
      <span class="t-ic">
        <AppIcon :name="level === 'emergency' ? 'alert' : level === 'urgent' ? 'clock' : 'shield'" :size="18" />
      </span>
      <div class="t-head-txt">
        <span class="t-level">{{ label }}</span>
        <span class="t-short">{{ short }}</span>
      </div>
    </header>

    <p class="t-advice">{{ advice }}</p>

    <div v-if="causes.length" class="t-block">
      <p class="t-block-h">可能原因</p>
      <ul class="t-causes">
        <li v-for="c in causes" :key="c">{{ c }}</li>
      </ul>
    </div>

    <div v-if="actions.length" class="t-block">
      <p class="t-block-h">建议下一步</p>
      <ol class="t-actions">
        <li v-for="a in actions" :key="a">
          <span class="t-act-n"></span>
          <span>{{ a }}</span>
        </li>
      </ol>
    </div>

    <footer class="t-foot">
      <span class="t-conf">
        <AppIcon name="sparkle" :size="12" />
        AI 初步判断 · 置信度 {{ confidence }}
      </span>
      <button class="t-escalate" type="button" @click="$emit('escalate')">
        转真人医生
        <AppIcon name="back" :size="14" class="t-arrow" />
      </button>
    </footer>
  </article>
</template>

<script setup>
import AppIcon from '@/components/icons/AppIcon.vue'

defineProps({
  level: { type: String, default: 'home' }, // emergency | urgent | home
  label: { type: String, default: '' },
  short: { type: String, default: '' },
  advice: { type: String, default: '' },
  causes: { type: Array, default: () => [] },
  actions: { type: Array, default: () => [] },
  confidence: { type: String, default: '中' }
})

defineEmits(['escalate'])
</script>

<style scoped>
.triage {
  border-radius: var(--radius-lg);
  border: 1px solid var(--hairline-strong);
  background: var(--color-surface);
  padding: 16px;
  margin-bottom: 16px;
}

/* 紧急度只体现在顶部标签与左侧色条，卡片本体保持纸面，避免整屏告警色 */
.triage.emergency { border-color: color-mix(in srgb, var(--color-alert) 45%, transparent); }
.triage.urgent { border-color: color-mix(in srgb, var(--color-watch) 45%, transparent); }
.triage.home { border-color: color-mix(in srgb, var(--color-good) 35%, transparent); }

.t-head { display: flex; align-items: center; gap: 10px; }
.t-ic {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  flex-shrink: 0;
}
.triage.emergency .t-ic { background: color-mix(in srgb, var(--color-alert) 12%, white); color: var(--color-alert); }
.triage.urgent .t-ic { background: color-mix(in srgb, var(--color-watch) 14%, white); color: var(--color-watch); }
.triage.home .t-ic { background: var(--color-sage-soft); color: var(--color-good); }

.t-head-txt { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.t-level { font-weight: 700; font-size: 15px; letter-spacing: -0.01em; }
.triage.emergency .t-level { color: var(--color-alert); }
.triage.urgent .t-level { color: var(--color-watch); }
.triage.home .t-level { color: var(--color-good); }
.t-short { font-size: 12px; color: var(--color-muted); }

.t-advice {
  font-size: 14px;
  line-height: 1.65;
  color: var(--color-ink-2);
  margin-top: 12px;
}

.t-block { margin-top: 14px; }
.t-block-h {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-faint);
  margin-bottom: 8px;
}
.t-causes { list-style: none; display: flex; flex-wrap: wrap; gap: 6px; }
.t-causes li {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink-2);
  background: var(--color-surface-2);
  border: 1px solid var(--hairline);
  padding: 5px 11px;
  border-radius: var(--radius-pill);
}

.t-actions { list-style: none; display: flex; flex-direction: column; gap: 8px; counter-reset: act; }
.t-actions li {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--color-ink-2);
}
.t-act-n {
  flex-shrink: 0;
  width: 17px;
  height: 17px;
  margin-top: 2px;
  border-radius: 50%;
  background: var(--color-sage-soft);
  color: var(--color-good);
  font-size: 10px;
  font-weight: 700;
  display: grid;
  place-items: center;
  counter-increment: act;
}
.t-act-n::before { content: counter(act); }

.t-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--hairline);
}
.t-conf {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--color-faint);
}
.t-escalate {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  padding: 8px 12px;
  border-radius: var(--radius-pill);
  transition: transform var(--dur-fast) var(--ease-out);
  flex-shrink: 0;
}
.t-escalate:active { transform: scale(0.96); }
.t-arrow { transform: rotate(180deg); }
</style>
